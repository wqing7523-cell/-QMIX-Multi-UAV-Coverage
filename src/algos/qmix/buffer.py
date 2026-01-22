"""Replay buffer for QMIX."""
from __future__ import annotations

from collections import deque
from typing import Dict, List

import numpy as np


class EpisodeBatch:
    """Stores an episode worth of transitions for multi-agent training."""

    def __init__(self, max_seq_len: int, obs_dim: int, state_dim: int, num_agents: int, action_dim: int):
        self.max_seq_len = max_seq_len
        self.obs_dim = obs_dim
        self.state_dim = state_dim
        self.num_agents = num_agents
        self.action_dim = action_dim

        self.obs = np.zeros((max_seq_len + 1, num_agents, obs_dim), dtype=np.float32)
        self.state = np.zeros((max_seq_len + 1, state_dim), dtype=np.float32)
        self.actions = np.zeros((max_seq_len, num_agents), dtype=np.int64)
        self.rewards = np.zeros((max_seq_len, num_agents), dtype=np.float32)
        self.terminated = np.zeros((max_seq_len, 1), dtype=np.float32)
        self.mask = np.zeros((max_seq_len, 1), dtype=np.float32)
        self.available_actions = np.ones((max_seq_len + 1, num_agents, action_dim), dtype=np.float32)
        self.ptr = 0

    def insert(
        self,
        t: int,
        obs: np.ndarray,
        state: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        terminated: bool,
        avail_actions: np.ndarray | None = None,
    ) -> None:
        self.obs[t] = obs
        self.state[t] = state
        self.actions[t] = actions
        self.rewards[t] = rewards
        self.terminated[t] = float(terminated)
        self.mask[t] = 1.0
        if avail_actions is not None:
            self.available_actions[t] = avail_actions
        self.ptr = max(self.ptr, t + 1)

    def set_last(self, obs: np.ndarray, state: np.ndarray, avail_actions: np.ndarray | None = None) -> None:
        self.obs[self.ptr] = obs
        self.state[self.ptr] = state
        if avail_actions is not None:
            self.available_actions[self.ptr] = avail_actions


class ReplayBuffer:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.buffer: deque[Dict] = deque(maxlen=capacity)

    def push(self, episode: Dict) -> None:
        self.buffer.append(episode)

    def sample(self, batch_size: int) -> List[Dict]:
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        return [self.buffer[i] for i in indices]

    def __len__(self) -> int:
        return len(self.buffer)
