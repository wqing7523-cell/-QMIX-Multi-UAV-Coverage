"""Obstacle generation and management for grid world."""
from typing import List, Optional, Tuple

import numpy as np


class ObstacleManager:
    """Manages obstacles in the grid world."""

    def __init__(
        self,
        map_size: Tuple[int, int],
        obstacle_density: float = 0.0,
        obstacle_type: str = "static",
        seed: Optional[int] = None,
    ) -> None:
        """Initialise obstacle manager."""
        self.map_size = map_size
        self.obstacle_density = obstacle_density
        self.obstacle_type = obstacle_type
        self.height, self.width = map_size

        if seed is not None:
            np.random.seed(seed)

        self.obstacle_map = np.zeros((self.height, self.width), dtype=bool)
        self.obstacle_positions: List[Tuple[int, int]] = []
        self._generate_obstacles()

    def _generate_obstacles(self) -> None:
        """Generate obstacles on the map."""
        if self.obstacle_density <= 0:
            return

        num_obstacles = int(self.height * self.width * self.obstacle_density)
        attempts = num_obstacles * 10 if num_obstacles > 0 else 0

        while len(self.obstacle_positions) < num_obstacles and attempts > 0:
            attempts -= 1
            row = np.random.randint(0, self.height)
            col = np.random.randint(0, self.width)
            if not self.obstacle_map[row, col]:
                self.obstacle_map[row, col] = True
                self.obstacle_positions.append((row, col))

    def is_obstacle(self, row: int, col: int) -> bool:
        """Check if a cell is an obstacle or out-of-bounds."""
        if row < 0 or row >= self.height or col < 0 or col >= self.width:
            return True
        return bool(self.obstacle_map[row, col])

    def ensure_connectivity(self, start_positions: List[Tuple[int, int]]) -> None:
        """Ensure starting cells are obstacle-free."""
        for row, col in start_positions:
            if self.is_obstacle(row, col):
                self.obstacle_map[row, col] = False
                if (row, col) in self.obstacle_positions:
                    self.obstacle_positions.remove((row, col))

    def get_obstacle_map(self) -> np.ndarray:
        """Return a copy of the obstacle map."""
        return self.obstacle_map.copy()

    def update_dynamic(self) -> None:
        """Update dynamic obstacles (placeholder)."""
        if self.obstacle_type == "dynamic":
            # TODO: Implement dynamic obstacle behaviour
            pass
