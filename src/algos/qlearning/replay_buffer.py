"""Replay buffer for Q-learning baselines."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Tuple

import numpy as np
import torch


@dataclass
class Transition:
    state: np.ndarray
    action: np.ndarray
    reward: np.ndarray
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.buffer: Deque[Transition] = deque(maxlen=capacity)

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
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        states = np.stack([self.buffer[i].state for i in indices])
        actions = np.stack([self.buffer[i].action for i in indices])
        rewards = np.stack([self.buffer[i].reward for i in indices])
        next_states = np.stack([self.buffer[i].next_state for i in indices])
        dones = np.stack([self.buffer[i].done for i in indices])

        return Transition(states, actions, rewards, next_states, dones)

    def __len__(self) -> int:
        return len(self.buffer)

    def is_full(self) -> bool:
        return len(self.buffer) >= self.capacity

    @staticmethod
    def to_tensors(transition: Transition, device: torch.device) -> Tuple[torch.Tensor, ...]:
        states = torch.from_numpy(transition.state).float().to(device)
        actions = torch.from_numpy(transition.action).long().to(device)
        rewards = torch.from_numpy(transition.reward).float().to(device)
        next_states = torch.from_numpy(transition.next_state).float().to(device)
        dones = torch.from_numpy(transition.done.astype(np.float32)).to(device)
        return states, actions, rewards, next_states, dones
