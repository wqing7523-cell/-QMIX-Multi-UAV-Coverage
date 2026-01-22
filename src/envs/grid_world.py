"""Multi-UAV grid world environment for path planning."""
from __future__ import annotations

from collections import deque
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from src.envs.obstacles import ObstacleManager


class CellType(IntEnum):
    UNVISITED = 0
    VISITED = 1
    OBSTACLE = 2
    UAV = 3


class Action(IntEnum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


class GridWorldEnv(gym.Env):
    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        map_size: Tuple[int, int] = (5, 5),
        num_uavs: int = 1,
        obstacle_density: float = 0.0,
        obstacle_type: str = "static",
        max_steps: int = 1000,
        energy_budget: int = 1800,
        reward_new_cell_base: float = 358.74,
        reward_visited_cell: float = -31.14,
        reward_obstacle: float = -225.17,
        reward_collision: float = -100.0,
        reward_complete: float = 1000.0,
        reward_no_progress: float = -2.0,
        no_progress_patience: int = 30,
        shaping_weight: float = 10.0,
        obstacle_shaping_weight: float = 2.0,
        seed: Optional[int] = None,
    ) -> None:
        super().__init__()

        self.map_size = map_size
        self.height, self.width = map_size
        self.num_uavs = num_uavs
        self.max_steps = max_steps
        self.energy_budget = energy_budget
        self.total_cells = self.height * self.width

        self.reward_new_cell_base = reward_new_cell_base
        self.reward_visited_cell = reward_visited_cell
        self.reward_obstacle = reward_obstacle
        self.reward_collision = reward_collision
        self.reward_complete = reward_complete
        self.reward_no_progress = reward_no_progress
        self.no_progress_patience = max(1, no_progress_patience)
        self.shaping_weight = shaping_weight
        self.obstacle_shaping_weight = obstacle_shaping_weight

        self.rng = np.random.default_rng(seed)

        self.obstacle_manager = ObstacleManager(
            map_size=map_size,
            obstacle_density=obstacle_density,
            obstacle_type=obstacle_type,
            seed=seed,
        )

        self.visited_map: np.ndarray = np.zeros((self.height, self.width), dtype=bool)
        self.uav_positions: List[Tuple[int, int]] = []
        self.uav_energy = np.zeros(self.num_uavs, dtype=int)
        self.step_count = 0
        self.visited_count = 0
        self.episode_reward = 0.0
        self.no_progress_steps = np.zeros(self.num_uavs, dtype=int)
        self.prev_potential = np.zeros(self.num_uavs, dtype=np.float32)

        self._build_spaces()

    def _build_spaces(self) -> None:
        self.action_space = spaces.MultiDiscrete([len(Action)] * self.num_uavs)
        map_obs_size = self.height * self.width * 3
        scalar_obs_size = 1 + self.num_uavs * 3
        obs_size = map_obs_size + scalar_obs_size
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=(obs_size,),
            dtype=np.float32,
        )

    def reset(
        self, *, seed: Optional[int] = None, options: Optional[Dict[str, Any]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        if seed is not None:
            self.rng = np.random.default_rng(seed)

        self.step_count = 0
        self.episode_reward = 0.0
        self.visited_map = np.zeros((self.height, self.width), dtype=bool)
        self.uav_energy = np.full(self.num_uavs, self.energy_budget, dtype=int)
        self.uav_positions = self._initial_positions()
        self.visited_count = 0
        self.no_progress_steps = np.zeros(self.num_uavs, dtype=int)

        for row, col in self.uav_positions:
            if not self.visited_map[row, col]:
                self.visited_map[row, col] = True
                self.visited_count += 1

        self.prev_potential = np.array([self._state_potential(pos) for pos in self.uav_positions], dtype=np.float32)

        self.obstacle_manager.ensure_connectivity(self.uav_positions)

        observation = self._get_observation()
        info = self._get_info()
        return observation, info

    def step(
        self, actions: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, bool, bool, Dict[str, Any]]:
        if len(actions) != self.num_uavs:
            raise ValueError(
                f"Expected {self.num_uavs} actions, received {len(actions)}"
            )

        rewards = np.zeros(self.num_uavs, dtype=np.float32)
        attempted_positions: List[Tuple[int, int]] = []
        final_positions = self.uav_positions.copy()
        progress_made = [False] * self.num_uavs
        penalty_registered = [False] * self.num_uavs
        collisions = 0
        obstacle_hits = 0

        for idx, action in enumerate(actions):
            row, col = self.uav_positions[idx]
            if self.uav_energy[idx] <= 0:
                attempted_positions.append((row, col))
                continue

            d_row, d_col = self._action_to_delta(Action(action))
            new_row, new_col = row + d_row, col + d_col

            if self._is_invalid_cell(new_row, new_col):
                rewards[idx] += self.reward_obstacle
                obstacle_hits += 1
                self._register_no_progress(idx, rewards)
                penalty_registered[idx] = True
                attempted_positions.append((row, col))
                continue

            attempted_positions.append((new_row, new_col))

        for idx, pos in enumerate(attempted_positions):
            if self.uav_energy[idx] <= 0:
                continue

            if attempted_positions.count(pos) > 1:
                rewards[idx] += self.reward_collision
                collisions += 1
                self._register_no_progress(idx, rewards)
                penalty_registered[idx] = True
                continue

            final_positions[idx] = pos
            self.uav_energy[idx] = max(0, self.uav_energy[idx] - 1)

            row, col = pos
            if not self.visited_map[row, col]:
                remaining = self._remaining_free_cells()
                scale = 1.0
                if remaining > 0:
                    scale += max(self.height, self.width) / remaining
                rewards[idx] += self.reward_new_cell_base * scale
                self.visited_map[row, col] = True
                self.visited_count += 1
                self.no_progress_steps[idx] = 0
                progress_made[idx] = True
            else:
                rewards[idx] += self.reward_visited_cell
                self._register_no_progress(idx, rewards)
                penalty_registered[idx] = True

        for idx in range(self.num_uavs):
            if self.uav_energy[idx] <= 0:
                continue
            if progress_made[idx]:
                continue
            if penalty_registered[idx]:
                continue
            self._register_no_progress(idx, rewards, gentle=True)

        self.uav_positions = final_positions

        # Potential-based shaping reward
        for idx, pos in enumerate(self.uav_positions):
            if self.uav_energy[idx] <= 0:
                continue
            potential_new = self._state_potential(pos)
            delta = potential_new - self.prev_potential[idx]
            rewards[idx] += self.shaping_weight * delta
            self.prev_potential[idx] = potential_new

        self.step_count += 1
        self.episode_reward += float(rewards.sum())

        terminated = self._is_covered()
        truncated = self.step_count >= self.max_steps or np.all(self.uav_energy <= 0)

        if terminated:
            rewards += self.reward_complete / self.num_uavs

        observation = self._get_observation()
        info = self._get_info()
        info.update(
            {
                "collisions": collisions,
                "obstacle_hits": obstacle_hits,
                "reward_vector": rewards.copy(),
            }
        )

        return observation, rewards, terminated, truncated, info

    def _state_potential(self, position: Tuple[int, int]) -> float:
        distance = self._nearest_unvisited_distance(position)
        clearance = self._nearest_obstacle_distance(position)
        potential = 0.0
        if distance is not None:
            potential -= float(distance)
        if clearance is not None:
            potential += self.obstacle_shaping_weight * float(min(clearance, 5))
        return potential

    def _nearest_obstacle_distance(self, position: Tuple[int, int]) -> Optional[int]:
        obstacle_map = self.obstacle_manager.get_obstacle_map()
        start_row, start_col = position
        if obstacle_map[start_row, start_col]:
            return 0

        visited = np.zeros((self.height, self.width), dtype=bool)
        queue = deque()
        queue.append((start_row, start_col, 0))
        visited[start_row, start_col] = True

        while queue:
            row, col, dist = queue.popleft()
            for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                n_row, n_col = row + d_row, col + d_col
                if n_row < 0 or n_row >= self.height or n_col < 0 or n_col >= self.width:
                    continue
                if visited[n_row, n_col]:
                    continue
                if obstacle_map[n_row, n_col]:
                    return dist + 1
                visited[n_row, n_col] = True
                queue.append((n_row, n_col, dist + 1))
        return None

    def _nearest_unvisited_distance(self, position: Tuple[int, int]) -> Optional[int]:
        obstacle_map = self.obstacle_manager.get_obstacle_map()
        start_row, start_col = position
        if not self.visited_map[start_row, start_col]:
            return 0

        visited = np.zeros((self.height, self.width), dtype=bool)
        queue = deque()
        queue.append((start_row, start_col, 0))
        visited[start_row, start_col] = True

        while queue:
            row, col, dist = queue.popleft()
            for d_row, d_col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                n_row, n_col = row + d_row, col + d_col
                if n_row < 0 or n_row >= self.height or n_col < 0 or n_col >= self.width:
                    continue
                if visited[n_row, n_col] or obstacle_map[n_row, n_col]:
                    continue
                if not self.visited_map[n_row, n_col]:
                    return dist + 1
                visited[n_row, n_col] = True
                queue.append((n_row, n_col, dist + 1))
        return None

    def _register_no_progress(
        self, idx: int, rewards: np.ndarray, gentle: bool = False
    ) -> None:
        self.no_progress_steps[idx] += 1
        if self.no_progress_steps[idx] >= self.no_progress_patience:
            penalty = self.reward_no_progress if not gentle else self.reward_no_progress * 0.5
            rewards[idx] += penalty
            self.no_progress_steps[idx] = 0

    def _initial_positions(self) -> List[Tuple[int, int]]:
        obstacle_map = self.obstacle_manager.get_obstacle_map()
        free_cells = np.argwhere(~obstacle_map)
        if len(free_cells) < self.num_uavs:
            raise RuntimeError("Not enough free cells for UAV initialisation")
        indices = self.rng.choice(len(free_cells), size=self.num_uavs, replace=False)
        positions = [tuple(free_cells[i]) for i in indices]
        return positions

    def _action_to_delta(self, action: Action) -> Tuple[int, int]:
        if action == Action.UP:
            return -1, 0
        if action == Action.DOWN:
            return 1, 0
        if action == Action.LEFT:
            return 0, -1
        if action == Action.RIGHT:
            return 0, 1
        raise ValueError(f"Unsupported action: {action}")

    def _is_invalid_cell(self, row: int, col: int) -> bool:
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return True
        return self.obstacle_manager.is_obstacle(row, col)

    def _remaining_free_cells(self) -> int:
        obstacle_map = self.obstacle_manager.get_obstacle_map()
        remaining = np.logical_not(np.logical_or(obstacle_map, self.visited_map))
        return int(remaining.sum())

    def _is_covered(self) -> bool:
        obstacle_map = self.obstacle_manager.get_obstacle_map()
        return np.all(np.logical_or(self.visited_map, obstacle_map))

    def _get_observation(self) -> np.ndarray:
        visited_layer = self.visited_map.astype(np.float32)
        obstacle_layer = self.obstacle_manager.get_obstacle_map().astype(np.float32)
        uav_layer = np.zeros((self.height, self.width), dtype=np.float32)
        for row, col in self.uav_positions:
            uav_layer[row, col] = 1.0
        maps = np.stack([visited_layer, obstacle_layer, uav_layer], axis=0).reshape(-1)

        coverage = self.visited_count / max(1, self.total_cells)
        scalars: List[float] = [coverage]
        for idx, (row, col) in enumerate(self.uav_positions):
            scalars.extend([
                row / (self.height - 1 + 1e-8),
                col / (self.width - 1 + 1e-8),
                self.uav_energy[idx] / max(1, self.energy_budget),
            ])
        return np.concatenate([maps, np.array(scalars, dtype=np.float32)], axis=0)

    def _get_info(self) -> Dict[str, Any]:
        coverage = self.visited_count / max(1, self.total_cells)
        return {
            "coverage": coverage,
            "steps": self.step_count,
            "energy": self.uav_energy.copy(),
            "visited_cells": self.visited_count,
            "visited_count": self.visited_count,
            "remaining_free_cells": self._remaining_free_cells(),
        }

    def render(self) -> None:
        grid = np.full((self.height, self.width), CellType.UNVISITED, dtype=int)
        grid[self.visited_map] = CellType.VISITED
        obstacle_map = self.obstacle_manager.get_obstacle_map()
        grid[obstacle_map] = CellType.OBSTACLE
        for row, col in self.uav_positions:
            grid[row, col] = CellType.UAV
        print(grid)

    def close(self) -> None:
        pass
