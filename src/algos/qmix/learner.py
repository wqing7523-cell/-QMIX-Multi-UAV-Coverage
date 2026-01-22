"""QMIX learner implementation."""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import torch
from torch import nn

from src.algos.qmix.agent_net import AgentNetwork
from src.algos.qmix.mixer_net import MixingNetwork


def build_agent_networks(num_agents: int, obs_dim: int, action_dim: int, hidden_dim: int, device: torch.device) -> Tuple[List[AgentNetwork], List[AgentNetwork]]:
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


def init_hidden(num_agents: int, hidden_dim: int, batch_size: int, device: torch.device) -> torch.Tensor:
    return torch.zeros(batch_size * num_agents, hidden_dim, device=device)


def select_actions(
    agents: List[AgentNetwork],
    obs: np.ndarray,
    hidden_states: torch.Tensor,
    epsilon: float,
    avail_actions: np.ndarray | None,
    device: torch.device,
) -> Tuple[np.ndarray, torch.Tensor]:
    batch_size = obs.shape[0]
    num_agents = len(agents)
    action_dim = agents[0].fc2.out_features

    obs_tensor = torch.tensor(obs, dtype=torch.float32, device=device)
    actions = np.zeros((batch_size, num_agents), dtype=np.int64)
    new_hidden_states = torch.zeros_like(hidden_states)

    for agent_idx, agent in enumerate(agents):
        start = agent_idx * batch_size
        end = (agent_idx + 1) * batch_size
        agent_obs = obs_tensor[:, agent_idx, :]
        hidden = hidden_states[start:end]
        q_values, hidden_new = agent(agent_obs, hidden)
        new_hidden_states[start:end] = hidden_new

        if avail_actions is not None:
            mask = torch.tensor(avail_actions[:, agent_idx, :], dtype=torch.bool, device=device)
            q_values[~mask] = -1e9

        if np.random.rand() < epsilon:
            random_actions = []
            for b in range(batch_size):
                if avail_actions is not None:
                    valid = np.where(avail_actions[b, agent_idx])[0]
                    choice = np.random.choice(valid)
                else:
                    choice = np.random.randint(action_dim)
                random_actions.append(choice)
            actions[:, agent_idx] = np.array(random_actions)
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
    double_q: bool = True,
) -> torch.Tensor:
    batch_size = len(batch)
    episode_len = max(item["filled_steps"] for item in batch)

    num_agents = len(agents)
    action_dim = agents[0].fc2.out_features

    obs_dim = agents[0].fc1.in_features
    state_dim = batch[0]["state"].shape[-1]

    obs = torch.tensor(np.stack([item["obs"] for item in batch]), dtype=torch.float32, device=device)
    next_obs = torch.tensor(np.stack([item["next_obs"] for item in batch]), dtype=torch.float32, device=device)
    state = torch.tensor(np.stack([item["state"] for item in batch]), dtype=torch.float32, device=device)
    next_state = torch.tensor(np.stack([item["next_state"] for item in batch]), dtype=torch.float32, device=device)
    actions = torch.tensor(np.stack([item["actions"] for item in batch]), dtype=torch.int64, device=device)
    rewards = torch.tensor(np.stack([item["rewards"] for item in batch]), dtype=torch.float32, device=device)
    terminated = torch.tensor(np.stack([item["terminated"] for item in batch]), dtype=torch.float32, device=device)
    mask = torch.tensor(np.stack([item["mask"] for item in batch]), dtype=torch.float32, device=device)

    avail_actions = batch[0].get("avail_actions")
    if avail_actions is not None:
        avail_actions = torch.tensor(np.stack([item["avail_actions"] for item in batch]), dtype=torch.float32, device=device)

    hidden_dim = agents[0].rnn.hidden_size
    hidden_states = init_hidden(num_agents, hidden_dim, batch_size, device)
    target_hidden_states = init_hidden(num_agents, hidden_dim, batch_size, device)

    agent_qs = []
    target_agent_qs = []

    for t in range(episode_len):
        step_obs = obs[:, t]
        step_actions = actions[:, t]
        step_rewards = rewards[:, t]
        step_terminated = terminated[:, t]
        step_mask = mask[:, t]

        q_values = []
        target_q_values = []

        for agent_idx, agent in enumerate(agents):
            start = agent_idx * batch_size
            end = (agent_idx + 1) * batch_size

            agent_input = step_obs[:, agent_idx, :]
            hidden = hidden_states[start:end]
            q, hidden_new = agent(agent_input, hidden)
            hidden_states[start:end] = hidden_new

            chosen_action = step_actions[:, agent_idx]
            q_chosen = q.gather(1, chosen_action.unsqueeze(-1)).squeeze(-1)
            q_values.append(q_chosen)

            target_agent = target_agents[agent_idx]
            target_hidden = target_hidden_states[start:end]
            target_q, target_hidden_new = target_agent(agent_input, target_hidden)
            target_hidden_states[start:end] = target_hidden_new

            if avail_actions is not None:
                step_avail = avail_actions[:, t, agent_idx, :]
                target_q[step_avail == 0] = -1e9

            if double_q:
                q_detach = q.detach()
                if avail_actions is not None:
                    step_avail = avail_actions[:, t, agent_idx, :]
                    q_detach[step_avail == 0] = -1e9
                greedy_actions = q_detach.argmax(dim=1, keepdim=True)
                target_q_chosen = target_q.gather(1, greedy_actions).squeeze(-1)
            else:
                target_q_chosen = target_q.max(dim=1).values

            target_q_values.append(target_q_chosen)

        agent_qs.append(torch.stack(q_values, dim=1))
        target_agent_qs.append(torch.stack(target_q_values, dim=1))

    agent_qs = torch.stack(agent_qs, dim=1)
    target_agent_qs = torch.stack(target_agent_qs, dim=1)

    total_q = []
    total_target_q = []

    for t in range(episode_len):
        q_tot = mixer(agent_qs[:, t], state[:, t])
        target_q_tot = target_mixer(target_agent_qs[:, t], next_state[:, t])

        target_q_tot = rewards[:, t].sum(dim=1, keepdim=True) + gamma * (1 - terminated[:, t]) * target_q_tot

        total_q.append(q_tot)
        total_target_q.append(target_q_tot.detach())

    total_q = torch.stack(total_q, dim=1)
    total_target_q = torch.stack(total_target_q, dim=1)

    td_error = (total_q - total_target_q) * mask.sum(dim=2)
    loss = (td_error ** 2).sum() / mask.sum()
    return loss
