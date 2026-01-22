"""QMIX training loop."""
from __future__ import annotations

import argparse
import random
import time
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import torch
from torch import nn
from torch.optim import RMSprop

from src.algos.qmix.agent_net import AgentNetwork
from src.algos.qmix.buffer import ReplayBuffer
from src.algos.qmix.mixer_net import MixingNetwork
from src.metrics.metrics import EpisodeStats, aggregate_episode_stats
from src.envs.grid_world import GridWorldEnv
from src.utils.config import load_config
from src.utils.logging import setup_logger
from src.utils.schedule import EpsilonSchedule, Plateau
from src.utils.seeding import set_seed


def ensure_tuple_map_size(map_size_entry) -> Tuple[int, int]:
    if isinstance(map_size_entry, (list, tuple)):
        if len(map_size_entry) == 2:
            return int(map_size_entry[0]), int(map_size_entry[1])
        if len(map_size_entry) == 1:
            value = int(map_size_entry[0])
            return value, value
    value = int(map_size_entry)
    return value, value


def build_agents(num_agents: int, obs_dim: int, action_dim: int, hidden_dim: int, device: torch.device) -> Tuple[List[AgentNetwork], List[AgentNetwork]]:
    agents = [AgentNetwork(obs_dim, action_dim, hidden_dim).to(device) for _ in range(num_agents)]
    target_agents = [AgentNetwork(obs_dim, action_dim, hidden_dim).to(device) for _ in range(num_agents)]
    for agent, target in zip(agents, target_agents):
        target.load_state_dict(agent.state_dict())
    return agents, target_agents


def build_mixer(num_agents: int, state_dim: int, mixing_hidden_dim: int, hyper_hidden_dim: int, device: torch.device) -> Tuple[MixingNetwork, MixingNetwork]:
    mixer = MixingNetwork(num_agents, state_dim, mixing_hidden_dim, hyper_hidden_dim).to(device)
    target_mixer = MixingNetwork(num_agents, state_dim, mixing_hidden_dim, hyper_hidden_dim).to(device)
    target_mixer.load_state_dict(mixer.state_dict())
    return mixer, target_mixer


def _decode_observations(data: np.ndarray, device: torch.device) -> torch.Tensor:
    tensor = torch.tensor(data, dtype=torch.float32, device=device)
    if data.dtype == np.uint8:
        tensor = tensor / 255.0
    return tensor



def select_actions(
    agents: List[AgentNetwork],
    obs: np.ndarray,
    hidden_states: torch.Tensor,
    epsilon: float,
    device: torch.device,
) -> Tuple[np.ndarray, torch.Tensor]:
    """Epsilon-greedy action selection for all agents."""
    batch_size = obs.shape[0]
    num_agents = len(agents)
    action_dim = agents[0].fc2.out_features

    obs_tensor = torch.tensor(obs, dtype=torch.float32, device=device)
    actions = np.zeros((batch_size, num_agents), dtype=np.int64)
    new_hidden_states = torch.zeros_like(hidden_states)

    for agent_idx, agent in enumerate(agents):
        agent_obs = obs_tensor[:, agent_idx, :]
        hidden = hidden_states[agent_idx]
        q_values, hidden_new = agent(agent_obs, hidden)
        new_hidden_states[agent_idx] = hidden_new

        if random.random() < epsilon:
            random_actions = np.random.randint(action_dim, size=batch_size)
            actions[:, agent_idx] = random_actions
        else:
            actions[:, agent_idx] = q_values.argmax(dim=1).cpu().numpy()

    return actions, new_hidden_states


def compute_td_loss(
    batch: List[Dict],
    agents: List[AgentNetwork],
    target_agents: List[AgentNetwork],
    mixer: MixingNetwork,
    target_mixer: MixingNetwork,
    gamma: float,
    device: torch.device,
) -> torch.Tensor:
    batch_size = len(batch)
    episode_len = max(item["filled_steps"] for item in batch)
    num_agents = len(agents)
    obs_dim = agents[0].fc1.in_features
    state_dim = batch[0]["state"].shape[-1]

    obs = torch.zeros(batch_size, episode_len, num_agents, obs_dim, device=device)
    next_obs = torch.zeros_like(obs)
    state = torch.zeros(batch_size, episode_len, state_dim, device=device)
    next_state = torch.zeros_like(state)
    actions = torch.zeros(batch_size, episode_len, num_agents, device=device, dtype=torch.long)
    rewards = torch.zeros(batch_size, episode_len, num_agents, device=device)
    terminated = torch.zeros(batch_size, episode_len, 1, device=device)
    mask = torch.zeros(batch_size, episode_len, 1, device=device)

    for idx, episode in enumerate(batch):
        T = episode["filled_steps"]
        obs[idx, :T] = _decode_observations(episode["obs"][:T], device)
        next_obs[idx, :T] = _decode_observations(episode["next_obs"][:T], device)
        state[idx, :T] = _decode_observations(episode["state"][:T], device)
        next_state[idx, :T] = _decode_observations(episode["next_state"][:T], device)
        actions[idx, :T] = torch.tensor(episode["actions"][:T], dtype=torch.long, device=device)
        rewards[idx, :T] = torch.tensor(episode["rewards"][:T], dtype=torch.float32, device=device)
        terminated[idx, :T, 0] = torch.tensor(episode["terminated"][:T], dtype=torch.float32, device=device)
        mask[idx, :T, 0] = 1.0

    hidden_dim = agents[0].rnn.hidden_size
    hidden = torch.zeros(num_agents, batch_size, hidden_dim, device=device)
    target_hidden = torch.zeros_like(hidden)

    loss = 0.0
    mask_sum = mask.sum()

    for t in range(episode_len):
        step_mask = mask[:, t]
        if step_mask.sum() == 0:
            continue

        q_values_agents = []
        target_q_values_agents = []

        step_obs = obs[:, t]
        step_next_obs = next_obs[:, t]
        step_actions = actions[:, t]

        for agent_idx, agent in enumerate(agents):
            agent_obs = step_obs[:, agent_idx, :]
            agent_hidden = hidden[agent_idx]
            q, hidden_new = agent(agent_obs, agent_hidden)
            hidden[agent_idx] = hidden_new
            chosen = q.gather(1, step_actions[:, agent_idx].unsqueeze(-1)).squeeze(-1)
            q_values_agents.append(chosen)

            target_agent = target_agents[agent_idx]
            target_obs = step_next_obs[:, agent_idx, :]
            target_hidden_agent = target_hidden[agent_idx]
            target_q, target_hidden_new = target_agent(target_obs, target_hidden_agent)
            target_hidden[agent_idx] = target_hidden_new
            target_q_max = target_q.max(dim=1).values
            target_q_values_agents.append(target_q_max)

        agent_qs = torch.stack(q_values_agents, dim=1)
        target_agent_qs = torch.stack(target_q_values_agents, dim=1)

        q_tot = mixer(agent_qs, state[:, t])
        target_q_tot = target_mixer(target_agent_qs, next_state[:, t])

        reward_total = rewards[:, t].sum(dim=1, keepdim=True)
        target = reward_total + gamma * (1 - terminated[:, t]) * target_q_tot

        td_error = (q_tot - target) * step_mask
        loss = loss + (td_error ** 2).sum()

    loss = loss / mask_sum
    return loss


def train_single_setting(
    env_cfg: Dict,
    algo_cfg: Dict,
    base_cfg: Dict,
    map_size_entry,
    num_uavs: int,
    obstacle_density: float,
    logger,
    init_checkpoint: Optional[str] = None,
) -> None:
    map_size = ensure_tuple_map_size(map_size_entry)

    device = torch.device(base_cfg.get("device", "cpu"))
    if device.type == "cuda" and not torch.cuda.is_available():
        device = torch.device("cpu")

    # Dynamic obstacle_shaping_weight based on obstacle_density
    obstacle_shaping_weights = env_cfg.get("obstacle_shaping_weights", {})
    base_obstacle_shaping_weight = env_cfg.get("obstacle_shaping_weight", 2.0)
    
    if obstacle_density > 0.0 and obstacle_shaping_weights:
        # Use dynamic weight if available
        obstacle_shaping_weight = obstacle_shaping_weights.get(
            float(obstacle_density), 
            base_obstacle_shaping_weight
        )
        logger.info(
            "Using dynamic obstacle_shaping_weight: %.1f for obstacle_density: %.2f",
            obstacle_shaping_weight,
            obstacle_density,
        )
    else:
        obstacle_shaping_weight = base_obstacle_shaping_weight
    
    # 消融实验：根据配置控制势能奖励
    enable_potential = algo_cfg.get("enable_potential_reward", True)
    if enable_potential:
        shaping_weight = env_cfg.get("shaping_weight", 10.0)
        final_obstacle_shaping_weight = obstacle_shaping_weight
    else:
        shaping_weight = 0.0
        final_obstacle_shaping_weight = 0.0
        logger.info("消融实验：势能奖励已关闭")
    
    env = GridWorldEnv(
        map_size=map_size,
        num_uavs=num_uavs,
        obstacle_density=obstacle_density,
        obstacle_type=env_cfg.get("obstacle_type", "static"),
        max_steps=env_cfg.get("max_steps", 2000),
        energy_budget=env_cfg.get("energy_budget", 2400),
        shaping_weight=shaping_weight,
        obstacle_shaping_weight=final_obstacle_shaping_weight,
        seed=env_cfg.get("seed"),
    )

    obs_dim = int(env.observation_space.shape[0])
    state_dim = obs_dim
    action_dim = int(env.action_space.nvec[0])

    hidden_dim = algo_cfg.get("agent_hidden_dim", 64)
    mixing_hidden_dim = algo_cfg.get("mixing_hidden_dim", 32)
    hyper_hidden_dim = algo_cfg.get("hyper_hidden_dim", 64)

    agents, target_agents = build_agents(num_uavs, obs_dim, action_dim, hidden_dim, device)
    mixer, target_mixer = build_mixer(num_uavs, state_dim, mixing_hidden_dim, hyper_hidden_dim, device)

    if init_checkpoint:
        ckpt_path = Path(init_checkpoint)
        if ckpt_path.exists():
            logger.info("Loading initial checkpoint from %s", ckpt_path)
            checkpoint = torch.load(ckpt_path, map_location=device)
            agent_states = checkpoint.get("agents", [])
            if len(agent_states) == num_uavs:
                for agent, state in zip(agents, agent_states):
                    agent.load_state_dict(state)
            else:
                logger.warning(
                    "Checkpoint agent count (%d) does not match num_uavs (%d); skipping agent load",
                    len(agent_states),
                    num_uavs,
                )
            mixer_state = checkpoint.get("mixer")
            if mixer_state:
                mixer.load_state_dict(mixer_state)
            for agent, target in zip(agents, target_agents):
                target.load_state_dict(agent.state_dict())
            target_mixer.load_state_dict(mixer.state_dict())
        else:
            logger.warning("Init checkpoint %s not found, proceeding without warm start", ckpt_path)

    params = []
    for agent in agents:
        params += list(agent.parameters())
    params += list(mixer.parameters())
    optimizer = RMSprop(params, lr=algo_cfg.get("learning_rate", 5e-4))

    replay_buffer = ReplayBuffer(algo_cfg.get("buffer_size", 5000))
    batch_size = algo_cfg.get("batch_size", 32)
    min_buffer = algo_cfg.get("min_buffer", 200)
    episodes = algo_cfg.get("episodes", 100)
    target_update_interval = algo_cfg.get("target_update_interval", 200)
    gamma = algo_cfg.get("gamma", 0.99)

    plateau_configs = algo_cfg.get("epsilon_plateaus", [])
    plateaus: List[Plateau] = []
    for plateau_cfg in plateau_configs:
        if not isinstance(plateau_cfg, dict):
            continue
        start = int(plateau_cfg.get("start", 0))
        end = int(plateau_cfg.get("end", start))
        value = float(plateau_cfg.get("value", algo_cfg.get("epsilon_end", 0.05)))
        if end < start:
            start, end = end, start
        plateaus.append(Plateau(start=max(1, start), end=max(1, end), value=value))

    # Dynamic epsilon settings based on obstacle_density
    # Higher obstacle density needs more exploration
    base_epsilon_end = algo_cfg.get("epsilon_end", 0.05)
    base_epsilon_decay = algo_cfg.get("epsilon_decay", 0.995)
    
    # Adjust epsilon for high obstacle density scenarios
    if obstacle_density >= 0.20:
        # High obstacle density: use higher epsilon_end and slower decay
        epsilon_end = algo_cfg.get("epsilon_end_high_density", 0.12)
        epsilon_decay = algo_cfg.get("epsilon_decay_high_density", 0.9995)
        logger.info(
            "Using high-density exploration settings: epsilon_end=%.2f, epsilon_decay=%.5f",
            epsilon_end,
            epsilon_decay,
        )
    elif obstacle_density >= 0.10:
        # Medium obstacle density: moderate exploration
        epsilon_end = algo_cfg.get("epsilon_end_medium_density", 0.10)
        epsilon_decay = algo_cfg.get("epsilon_decay_medium_density", 0.9997)
        logger.info(
            "Using medium-density exploration settings: epsilon_end=%.2f, epsilon_decay=%.5f",
            epsilon_end,
            epsilon_decay,
        )
    else:
        # Low obstacle density or no obstacles: use base settings
        epsilon_end = base_epsilon_end
        epsilon_decay = base_epsilon_decay
    
    epsilon_schedule = EpsilonSchedule(
        start=algo_cfg.get("epsilon_start", 1.0),
        end=epsilon_end,
        decay=epsilon_decay,
        min_epsilon=algo_cfg.get("epsilon_min", epsilon_end),
        plateaus=plateaus,
    )

    epsilon_accel_episode = algo_cfg.get("epsilon_accel_episode", None)
    epsilon_accel_decay = algo_cfg.get("epsilon_accel_decay", None)
    epsilon_accel_applied = False
    epsilon_accel2_episode = algo_cfg.get("epsilon_accel2_episode", None)
    epsilon_accel2_decay = algo_cfg.get("epsilon_accel2_decay", None)
    epsilon_accel2_applied = False

    log_interval = algo_cfg.get("log_interval", 10)

    recovery_cfg = algo_cfg.get("recovery", {})
    recovery_enabled = bool(recovery_cfg.get("enabled", False))
    
    # Dynamic recovery threshold based on obstacle_density
    base_recovery_threshold = float(recovery_cfg.get("coverage_threshold", 0.9))
    if obstacle_density >= 0.20:
        # High obstacle density: lower threshold (0.85-0.90)
        recovery_threshold = recovery_cfg.get("coverage_threshold_high_density", 0.90)
        recovery_drop_tolerance = recovery_cfg.get("drop_tolerance_high_density", 0.05)
        logger.info(
            "Using high-density recovery settings: threshold=%.2f, drop_tolerance=%.2f",
            recovery_threshold,
            recovery_drop_tolerance,
        )
    elif obstacle_density >= 0.10:
        # Medium obstacle density: moderate threshold (0.90-0.95)
        recovery_threshold = recovery_cfg.get("coverage_threshold_medium_density", 0.95)
        recovery_drop_tolerance = recovery_cfg.get("drop_tolerance_medium_density", 0.04)
    else:
        # Low obstacle density or no obstacles: use base threshold
        recovery_threshold = base_recovery_threshold
        recovery_drop_tolerance = float(recovery_cfg.get("drop_tolerance", 0.02))
    
    recovery_patience = int(recovery_cfg.get("patience", 3))
    recovery_reset_epsilon = float(recovery_cfg.get("reset_epsilon", 0.4))
    recovery_epsilon_boost = float(recovery_cfg.get("epsilon_boost", 0.05))
    recovery_min_improvement = float(recovery_cfg.get("min_improvement", 0.01))
    recovery_start_episode = max(int(recovery_cfg.get("start_episode", 150)), log_interval)
    recovery_cooldown = int(recovery_cfg.get("cooldown", 0))

    stats_all: List[EpisodeStats] = []

    logger.info(
        f"Training QMIX on map={map_size}, num_uavs={num_uavs}, obstacle_density={obstacle_density}"
    )

    best_snapshot = None
    best_coverage = float("-inf")
    degrade_counter = 0
    last_recovery_episode = -recovery_cooldown

    global_step = 0
    for episode in range(1, episodes + 1):
        obs, info = env.reset()
        episode_stats = EpisodeStats(
            start_time=time.time(),
            total_cells=info.get("valid_cells", env.total_cells),
            per_uav_new_cells=[0 for _ in range(num_uavs)],
        )

        episode_data = {
            "obs": [],
            "next_obs": [],
            "actions": [],
            "rewards": [],
            "state": [],
            "next_state": [],
            "terminated": [],
        }

        state = obs.copy()
        hidden_states = torch.zeros(len(agents), 1, hidden_dim, device=device)

        done = False
        truncated = False

        while not (done or truncated):
            epsilon = epsilon_schedule.get(episode)
            agent_obs = np.tile(obs, (num_uavs, 1))
            agent_obs = agent_obs.reshape(1, num_uavs, obs_dim)
            actions, hidden_states = select_actions(agents, agent_obs, hidden_states, epsilon, device)
            actions = actions[0]

            next_obs, rewards, done_flag, truncated_flag, step_info = env.step(actions)
            done = done_flag
            truncated = truncated_flag

            episode_data["obs"].append(agent_obs[0].copy())
            episode_data["actions"].append(actions.copy())
            episode_data["rewards"].append(rewards.copy())
            episode_data["state"].append(state.copy())
            episode_data["terminated"].append(float(done or truncated))

            next_agent_obs = np.tile(next_obs, (num_uavs, 1)).reshape(1, num_uavs, obs_dim)
            episode_data["next_obs"].append(next_agent_obs[0].copy())
            episode_data["next_state"].append(next_obs.copy())

            episode_stats.steps += 1
            episode_stats.total_actions += num_uavs
            episode_stats.energy_consumed += num_uavs
            episode_stats.collisions += step_info.get("collisions", 0)
            episode_stats.obstacle_hits += step_info.get("obstacle_hits", 0)
            episode_stats.visited_cells = step_info.get("visited_count", episode_stats.visited_cells)

            for idx, reward_value in enumerate(rewards):
                if reward_value >= env.reward_new_cell_base * 0.8:
                    episode_stats.new_cell_actions += 1
                    episode_stats.per_uav_new_cells[idx] += 1

            state = next_obs.copy()
            obs = next_obs

        episode_stats.end_time = time.time()
        episode_stats.success = bool(done and step_info.get("coverage", 0.0) >= 0.99)
        stats_all.append(episode_stats)

        obs_array = np.array(episode_data["obs"], dtype=np.float32)
        next_obs_array = np.array(episode_data["next_obs"], dtype=np.float32)
        state_array = np.array(episode_data["state"], dtype=np.float32)
        next_state_array = np.array(episode_data["next_state"], dtype=np.float32)

        obs_encoded = np.clip(np.rint(obs_array * 255.0), 0, 255).astype(np.uint8)
        next_obs_encoded = np.clip(np.rint(next_obs_array * 255.0), 0, 255).astype(np.uint8)
        state_encoded = np.clip(np.rint(state_array * 255.0), 0, 255).astype(np.uint8)
        next_state_encoded = np.clip(np.rint(next_state_array * 255.0), 0, 255).astype(np.uint8)

        episode_array = {
            "obs": obs_encoded,
            "next_obs": next_obs_encoded,
            "actions": np.array(episode_data["actions"], dtype=np.int64),
            "rewards": np.array(episode_data["rewards"], dtype=np.float16),
            "state": state_encoded,
            "next_state": next_state_encoded,
            "terminated": np.array(episode_data["terminated"], dtype=np.uint8),
            "filled_steps": len(episode_data["actions"]),
        }

        replay_buffer.push(episode_array)

        if len(replay_buffer) >= min_buffer:
            batch = replay_buffer.sample(batch_size)
            optimizer.zero_grad()
            loss = compute_td_loss(batch, agents, target_agents, mixer, target_mixer, gamma, device)
            loss.backward()
            nn.utils.clip_grad_norm_(params, max_norm=algo_cfg.get("grad_clip", 10.0))
            optimizer.step()

            global_step += 1
            if global_step % target_update_interval == 0:
                for agent, target in zip(agents, target_agents):
                    target.load_state_dict(agent.state_dict())
                target_mixer.load_state_dict(mixer.state_dict())

        if (
            not epsilon_accel_applied
            and epsilon_accel_episode is not None
            and epsilon_accel_decay is not None
            and episode >= epsilon_accel_episode
        ):
            epsilon_schedule.decay = epsilon_accel_decay
            epsilon_accel_applied = True
            logger.info(
                "Epsilon decay accelerated to %.5f at episode %d",
                epsilon_accel_decay,
                episode,
            )

        if (
            not epsilon_accel2_applied
            and epsilon_accel2_episode is not None
            and epsilon_accel2_decay is not None
            and episode >= epsilon_accel2_episode
        ):
            epsilon_schedule.decay = epsilon_accel2_decay
            epsilon_accel2_applied = True
            logger.info(
                "Epsilon decay second acceleration to %.5f at episode %d",
                epsilon_accel2_decay,
                episode,
            )

        epsilon_schedule.step(episode)

        if episode % log_interval == 0:
            recent_stats = aggregate_episode_stats(stats_all[-log_interval:])
            epsilon_value = epsilon_schedule.get(episode)
            logger.info(
                "Episode %d | coverage_mean=%.3f | pa_mean=%.3f | steps_mean=%.1f | epsilon=%.3f",
                episode,
                recent_stats.get("coverage_mean", 0.0),
                recent_stats.get("pa_mean", 0.0),
                recent_stats.get("steps_mean", 0.0),
                epsilon_value,
            )

            if recovery_enabled and episode >= recovery_start_episode:
                coverage = recent_stats.get("coverage_mean", 0.0)
                if coverage >= recovery_threshold and coverage > best_coverage + recovery_min_improvement:
                    best_snapshot = {
                        "agents": [deepcopy(agent.state_dict()) for agent in agents],
                        "mixer": deepcopy(mixer.state_dict()),
                    }
                    best_coverage = coverage
                    degrade_counter = 0
                    logger.info(
                        "New best coverage %.3f at episode %d; snapshot saved for recovery.",
                        coverage,
                        episode,
                    )
                elif coverage >= recovery_threshold:
                    degrade_counter = 0
                elif (
                    best_snapshot is not None
                    and best_coverage >= recovery_threshold
                    and coverage <= best_coverage - recovery_drop_tolerance
                ):
                    degrade_counter += 1
                    if (
                        degrade_counter >= recovery_patience
                        and episode - last_recovery_episode >= recovery_cooldown
                    ):
                        for agent, state in zip(agents, best_snapshot["agents"]):
                            agent.load_state_dict(state)
                        mixer.load_state_dict(best_snapshot["mixer"])
                        for agent, target in zip(agents, target_agents):
                            target.load_state_dict(agent.state_dict())
                        target_mixer.load_state_dict(mixer.state_dict())
                        previous_epsilon = epsilon_value
                        if previous_epsilon < recovery_reset_epsilon:
                            new_epsilon = min(
                                previous_epsilon + recovery_epsilon_boost,
                                recovery_reset_epsilon,
                            )
                        else:
                            new_epsilon = recovery_reset_epsilon
                        epsilon_schedule.set_value(new_epsilon)
                        last_recovery_episode = episode
                        degrade_counter = 0
                        logger.warning(
                            "Coverage collapsed to %.3f at episode %d; restored best model (%.3f) and adjusted epsilon from %.3f -> %.3f.",
                            coverage,
                            episode,
                            best_coverage,
                            previous_epsilon,
                            new_epsilon,
                        )
                    elif degrade_counter >= recovery_patience:
                        logger.info(
                            "Recovery skipped at episode %d due to cooldown (%d episodes remaining).",
                            episode,
                            recovery_cooldown - (episode - last_recovery_episode),
                        )
                else:
                    degrade_counter = 0

    summary = aggregate_episode_stats(stats_all)
    logger.info(
        "Training finished | coverage_mean=%.3f | pa_mean=%.3f | steps_mean=%.1f",
        summary.get("coverage_mean", 0.0),
        summary.get("pa_mean", 0.0),
        summary.get("steps_mean", 0.0),
    )

    if best_snapshot is not None:
        logger.info("Best coverage snapshot=%.3f", best_coverage)
        logger.info(
            "Applying best snapshot (coverage=%.3f) before saving checkpoint.",
            best_coverage,
        )
        for agent, state in zip(agents, best_snapshot["agents"]):
            agent.load_state_dict(state)
        mixer.load_state_dict(best_snapshot["mixer"])

    checkpoint_dir = Path(base_cfg.get("checkpoint_dir", "experiments/checkpoints"))
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    # Include obstacle_density in checkpoint filename for curriculum learning
    obs_density_str = f"obs{obstacle_density:.2f}".replace(".", "")
    ckpt_path = checkpoint_dir / f"qmix_map{map_size[0]}_uavs{num_uavs}_{obs_density_str}_{int(time.time())}.pt"
    checkpoint = {
        "agents": [agent.state_dict() for agent in agents],
        "mixer": mixer.state_dict(),
        "map_size": map_size,
        "num_uavs": num_uavs,
        "obstacle_density": obstacle_density,
    }
    torch.save(checkpoint, ckpt_path)
    logger.info("Checkpoint saved to %s", ckpt_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train QMIX")
    parser.add_argument("--base-config", default="configs/base.yaml")
    parser.add_argument("--env-config", default="configs/envs/grid_small.yaml")
    parser.add_argument("--algo-config", default="configs/algos/qmix.yaml")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--map-index", type=int, default=0)
    parser.add_argument("--uav-index", type=int, default=0)
    parser.add_argument("--obstacle-index", type=int, default=0)
    parser.add_argument("--init-checkpoint", type=str, default=None)
    args = parser.parse_args()

    base_cfg = load_config(args.base_config)
    env_cfg = load_config(args.env_config)
    algo_cfg = load_config(args.algo_config)

    set_seed(args.seed)

    log_dir = Path(base_cfg.get("log_dir", "experiments/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger("qmix", str(log_dir))

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
        init_checkpoint=args.init_checkpoint,
    )


if __name__ == "__main__":
    main()
