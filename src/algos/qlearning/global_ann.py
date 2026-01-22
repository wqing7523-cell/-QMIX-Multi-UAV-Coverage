"""Global ANN policy network for UAV swarm Q-learning."""
from __future__ import annotations

import torch
from torch import nn


class GlobalPolicyNetwork(nn.Module):
    """Single network controlling all UAVs."""

    def __init__(
        self,
        input_dim: int,
        num_uavs: int,
        action_dim: int,
        hidden_dim: int = 167,
    ) -> None:
        super().__init__()
        self.num_uavs = num_uavs
        self.action_dim = action_dim

        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_uavs * action_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Return Q-values for each UAV and action."""
        out = self.net(x)
        return out.view(-1, self.num_uavs, self.action_dim)
