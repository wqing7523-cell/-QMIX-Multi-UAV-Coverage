"""Training script for ANN-based Q-Learning baseline."""
from __future__ import annotations

import argparse
import random
import time
from collections import deque, namedtuple
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from torch import nn
from torch.optim import RMSprop, Adam

from src.algos.qlearning.global_ann import GlobalPolicyNetwork
from src.algos.qlearning.per_uav_ann import PerUAVPolicyNetwork
from src.envs.grid_world import GridWorldEnv
from src.metrics.metrics import EpisodeStats, aggregate_episode_stats
from src.utils.config import load_config, merge_configs
from src.utils.logging import setup_logger
from src.utils.schedule import EpsilonSchedule
from src.utils.seeding import set_seed

Transition = namedtuple(
    "Transition", ["state", "action", "reward", "next_state", "done"]
)


class ReplayBuffer:
    def __init__(self, capacity: int) -> None:
        self.buffer = deque(maxlen=capacity)

    def push(
        self,
        state: np.ndarray,
        action: np.ndarray,
        reward: np.ndarray,
        next_state: np.ndarray,
        done: bool,
    ) -> None:
        self.buffer.append(Transition(state, action, reward, next_state, done))

    def sample(self, batch_size: int) -> Transition:
        batch = random.sample(self.buffer, batch_size)
        return Transition(*zip(*batch))

    def __len__(self) -> int:
        return len(self.buffer)


def to_device(array: np.ndarray, device: torch.device) -> torch.Tensor:
    return torch.tensor(array, dtype=torch.float32, device=device)


def select_actions(
    state: np.ndarray,
    policy_net,
    num_uavs: int,
    action_dim: int,
    epsilon: float,
    device: torch.device,
    network_type: str,
    per_uav_nets: List[nn.Module] | None = None,
) -> Tuple[np.ndarray, torch.Tensor]:
    if random.random() < epsilon:
        actions = np.array([random.randrange(action_dim) for _ in range(num_uavs)])
        return actions, None

    state_tensor = to_device(state, device).unsqueeze(0)
    if network_type == "global":
        with torch.no_grad():
            q_values = policy_net(state_tensor).cpu().numpy()[0]
        actions = q_values.argmax(axis=1)
        return actions, torch.tensor(q_values, dtype=torch.float32, device=device)

    # Per UAV networks
    actions = []
    q_values = []
    for net in per_uav_nets or []:
        with torch.no_grad():
            q_val = net(state_tensor).cpu().numpy()[0]
        q_values.append(q_val)
        actions.append(int(np.argmax(q_val)))
    q_values_tensor = torch.tensor(np.stack(q_values), dtype=torch.float32, device=device)
    return np.array(actions), q_values_tensor


def compute_loss_global(
    batch: Transition,
    policy_net: nn.Module,
    target_net: nn.Module,
    device: torch.device,
    gamma: float,
) -> torch.Tensor:
    states = torch.tensor(np.stack(batch.state), dtype=torch.float32, device=device)
    actions = torch.tensor(np.stack(batch.action), dtype=torch.long, device=device)
    rewards = torch.tensor(np.stack(batch.reward), dtype=torch.float32, device=device)
    next_states = torch.tensor(
        np.stack(batch.next_state), dtype=torch.float32, device=device
    )
    dones = torch.tensor(np.array(batch.done, dtype=np.float32), device=device).unsqueeze(-1)

    q_values = policy_net(states)
    state_action_values = q_values.gather(2, actions.unsqueeze(-1)).squeeze(-1)

    with torch.no_grad():
        next_q_values = target_net(next_states).max(dim=2).values
        target_values = rewards + gamma * (1 - dones) * next_q_values

    loss = nn.functional.mse_loss(state_action_values, target_values)
    return loss


def compute_loss_per_uav(
    batch: Transition,
    policy_nets: List[nn.Module],
    target_nets: List[nn.Module],
    device: torch.device,
    gamma: float,
) -> torch.Tensor:
    states = torch.tensor(np.stack(batch.state), dtype=torch.float32, device=device)
    actions = torch.tensor(np.stack(batch.action), dtype=torch.long, device=device)
    rewards = torch.tensor(np.stack(batch.reward), dtype=torch.float32, device=device)
    next_states = torch.tensor(
        np.stack(batch.next_state), dtype=torch.float32, device=device
    )
    dones = torch.tensor(np.array(batch.done, dtype=np.float32), device=device)

    losses = []
    for idx, (net, target_net) in enumerate(zip(policy_nets, target_nets)):
        q_values = net(states)
        state_action = q_values.gather(1, actions[:, idx].unsqueeze(-1)).squeeze(-1)

        with torch.no_grad():
            next_q = target_net(next_states).max(dim=1).values
            target = rewards[:, idx] + gamma * (1 - dones) * next_q
        losses.append(nn.functional.mse_loss(state_action, target))
    return torch.mean(torch.stack(losses))


def copy_weights(source: nn.Module, target: nn.Module) -> None:
    target.load_state_dict(source.state_dict())


def copy_weights_list(sources: List[nn.Module], targets: List[nn.Module]) -> None:
    for src, tgt in zip(sources, targets):
        copy_weights(src, tgt)


def build_optimizer(name: str, parameters, lr: float):
    name = name.lower()
    if name == "adam":
        return Adam(parameters, lr=lr)
    if name == "rmsprop":
        return RMSprop(parameters, lr=lr)
    raise ValueError(f"Unsupported optimizer: {name}")


def ensure_tuple_map_size(map_size_entry) -> Tuple[int, int]:
    if isinstance(map_size_entry, (list, tuple)):
        if len(map_size_entry) == 2:
            return int(map_size_entry[0]), int(map_size_entry[1])
        if len(map_size_entry) == 1:
            return int(map_size_entry[0]), int(map_size_entry[0])
    value = int(map_size_entry)
    return value, value


def train_single_setting(
    env_cfg: Dict,
    algo_cfg: Dict,
    base_cfg: Dict,
    map_size_entry,
    num_uavs: int,
    obstacle_density: float,
    logger,
) -> None:
    map_size = ensure_tuple_map_size(map_size_entry)

    device = torch.device(base_cfg.get("device", "cpu"))
    if device.type == "cuda" and not torch.cuda.is_available():
        device = torch.device("cpu")

    env = GridWorldEnv(
        map_size=map_size,
        num_uavs=num_uavs,
        obstacle_density=obstacle_density,
        obstacle_type=env_cfg.get("obstacle_type", "static"),
        max_steps=env_cfg.get("max_steps", 1000),
        energy_budget=env_cfg.get("energy_budget", 1800),
        seed=env_cfg.get("seed"),
    )

    obs_dim = int(env.observation_space.shape[0])
    action_dim = int(env.action_space.nvec[0])

    network_type = algo_cfg.get("network_type", "global").lower()
    hidden_dim = algo_cfg.get("hidden_dim", 167)

    if network_type == "global":
        policy_net = GlobalPolicyNetwork(obs_dim, num_uavs, action_dim, hidden_dim).to(device)
        target_net = GlobalPolicyNetwork(obs_dim, num_uavs, action_dim, hidden_dim).to(device)
        copy_weights(policy_net, target_net)
        optimizer = build_optimizer(algo_cfg.get("optimizer", "rmsprop"), policy_net.parameters(), algo_cfg.get("learning_rate", 1e-3))
        per_uav_nets = None
        per_uav_targets = None
    else:
        policy_list = [
            PerUAVPolicyNetwork(obs_dim, action_dim, hidden_dim).to(device)
            for _ in range(num_uavs)
        ]
        target_list = [
            PerUAVPolicyNetwork(obs_dim, action_dim, hidden_dim).to(device)
            for _ in range(num_uavs)
        ]
        copy_weights_list(policy_list, target_list)
        params = []
        for net in policy_list:
            params += list(net.parameters())
        optimizer = build_optimizer(algo_cfg.get("optimizer", "rmsprop"), params, algo_cfg.get("learning_rate", 1e-3))
        policy_net = None
        target_net = None
        per_uav_nets = policy_list
        per_uav_targets = target_list

    replay_buffer = ReplayBuffer(algo_cfg.get("memory_size", 200))
    epsilon_schedule = EpsilonSchedule(
        start=algo_cfg.get("epsilon_start", 1.0),
        end=algo_cfg.get("epsilon_end", 0.05),
        decay=algo_cfg.get("epsilon_decay", 0.99),
        min_epsilon=algo_cfg.get("epsilon_end", 0.05),
    )

    gamma = algo_cfg.get("gamma", 0.99)
    batch_size = algo_cfg.get("batch_size", 32)
    min_memory = algo_cfg.get("min_memory_size", batch_size)
    episodes = algo_cfg.get("episodes", 100)
    target_update_interval = algo_cfg.get("target_update_interval", 100)
    log_interval = algo_cfg.get("log_interval", 10)

    log_dir = Path(base_cfg.get("log_dir", "experiments/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)

    checkpoint_dir = Path(base_cfg.get("checkpoint_dir", "experiments/checkpoints"))
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    stats_all: List[EpisodeStats] = []

    logger.info(
        f"Training Q-Learning ({network_type}) on map={map_size}, num_uavs={num_uavs}, obstacle_density={obstacle_density}"
    )

    global_step = 0
    for episode in range(1, episodes + 1):
        obs, info = env.reset()
        episode_stats = EpisodeStats(
            start_time=time.time(),
            total_cells=info.get("valid_cells", env.total_cells),
            per_uav_new_cells=[0 for _ in range(num_uavs)],
        )
        done = False
        truncated = False
        prev_actions = np.zeros(num_uavs, dtype=int)

        while not (done or truncated):
            epsilon = epsilon_schedule.get()
            actions, _ = select_actions(
                obs,
                policy_net,
                num_uavs,
                action_dim,
                epsilon,
                device,
                network_type,
                per_uav_nets,
            )

            next_obs, rewards, done_flag, truncated_flag, step_info = env.step(actions)
            done = done_flag
            truncated = truncated_flag

            replay_buffer.push(obs, actions, rewards, next_obs, done or truncated)

            episode_stats.steps += 1
            episode_stats.total_actions += num_uavs
            episode_stats.energy_consumed += num_uavs
            episode_stats.collisions += step_info.get("collisions", 0)
            episode_stats.obstacle_hits += step_info.get("obstacle_hits", 0)
            episode_stats.visited_cells = step_info.get("visited_count", episode_stats.visited_cells)

            reward_vector = np.array(step_info.get("reward_vector", rewards))
            new_cell_threshold = env.reward_new_cell_base
            for idx, reward_value in enumerate(reward_vector):
                if reward_value >= new_cell_threshold * 0.8:
                    episode_stats.new_cell_actions += 1
                    episode_stats.per_uav_new_cells[idx] += 1

            if len(replay_buffer) >= min_memory:
                batch = replay_buffer.sample(batch_size)
                optimizer.zero_grad()
                if network_type == "global":
                    loss = compute_loss_global(batch, policy_net, target_net, device, gamma)
                else:
                    loss = compute_loss_per_uav(batch, per_uav_nets, per_uav_targets, device, gamma)
                loss.backward()
                nn.utils.clip_grad_norm_(
                    policy_net.parameters() if policy_net is not None else [p for net in per_uav_nets for p in net.parameters()],
                    max_norm=5.0,
                )
                optimizer.step()

                global_step += 1
                if global_step % target_update_interval == 0:
                    if network_type == "global":
                        copy_weights(policy_net, target_net)
                    else:
                        copy_weights_list(per_uav_nets, per_uav_targets)

            obs = next_obs
            prev_actions = actions

        episode_stats.end_time = time.time()
        episode_stats.success = bool(done and step_info.get("coverage", 0.0) >= 0.99)
        stats_all.append(episode_stats)

        epsilon_schedule.step()

        if episode % log_interval == 0:
            recent_stats = aggregate_episode_stats(stats_all[-log_interval:])
            logger.info(
                "Episode %d | coverage_mean=%.3f | pa_mean=%.3f | steps_mean=%.1f | epsilon=%.3f",
                episode,
                recent_stats.get("coverage_mean", 0.0),
                recent_stats.get("pa_mean", 0.0),
                recent_stats.get("steps_mean", 0.0),
                epsilon_schedule.get(),
            )

    summary = aggregate_episode_stats(stats_all)
    logger.info(
        "Training finished | coverage_mean=%.3f | pa_mean=%.3f | steps_mean=%.1f",
        summary.get("coverage_mean", 0.0),
        summary.get("pa_mean", 0.0),
        summary.get("steps_mean", 0.0),
    )

    # Save model checkpoint
    timestamp = int(time.time())
    if network_type == "global" and policy_net is not None:
        ckpt_path = checkpoint_dir / f"qlearning_global_map{map_size[0]}_uavs{num_uavs}_{timestamp}.pt"
        torch.save(policy_net.state_dict(), ckpt_path)
    elif per_uav_nets:
        ckpt_dir = checkpoint_dir / f"qlearning_peruav_map{map_size[0]}_uavs{num_uavs}_{timestamp}"
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        for idx, net in enumerate(per_uav_nets):
            torch.save(net.state_dict(), ckpt_dir / f"uav_{idx}.pt")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Q-Learning baseline")
    parser.add_argument("--base-config", default="configs/base.yaml")
    parser.add_argument("--env-config", default="configs/envs/grid_small.yaml")
    parser.add_argument("--algo-config", default="configs/algos/qlearning.yaml")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--map-index", type=int, default=0)
    parser.add_argument("--uav-index", type=int, default=0)
    parser.add_argument("--obstacle-index", type=int, default=0)
    args = parser.parse_args()

    base_cfg = load_config(args.base_config)
    env_cfg = load_config(args.env_config)
    algo_cfg = load_config(args.algo_config)

    config = merge_configs(base_cfg, algo_cfg)

    set_seed(args.seed)

    log_dir = Path(base_cfg.get("log_dir", "experiments/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger("qlearning", str(log_dir))

    map_sizes = env_cfg.get("map_size", [5])
    if not isinstance(map_sizes, list):
        map_sizes = [map_sizes]
    num_uavs_list = env_cfg.get("num_uavs", [1])
    if not isinstance(num_uavs_list, list):
        num_uavs_list = [num_uavs_list]

    obstacle_density = env_cfg.get("obstacle_density", 0.0)
    if isinstance(obstacle_density, list):
        obstacle_density_list = obstacle_density
    else:
        obstacle_density_list = [obstacle_density]

    map_idx = max(0, min(args.map_index, len(map_sizes) - 1))
    uav_idx = max(0, min(args.uav_index, len(num_uavs_list) - 1))
    if len(obstacle_density_list) == 1:
        od_idx = 0
    else:
        od_idx = max(0, min(args.obstacle_index, len(obstacle_density_list) - 1))

    train_single_setting(
        env_cfg,
        algo_cfg,
        base_cfg,
        map_sizes[map_idx],
        int(num_uavs_list[uav_idx]),
        float(obstacle_density_list[od_idx]),
        logger,
    )


if __name__ == "__main__":
    main()
