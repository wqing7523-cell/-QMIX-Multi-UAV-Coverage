"""Epsilon schedule for exploration."""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Plateau:
    start: int
    end: int
    value: float


class EpsilonSchedule:
    """Epsilon-greedy exploration schedule with optional plateaus."""

    def __init__(
        self,
        start: float,
        end: float,
        decay: float,
        min_epsilon: float = 0.05,
        plateaus: Optional[List[Plateau]] = None,
    ):
        """Initialize epsilon schedule.

        Args:
            start: Initial epsilon value.
            end: Final epsilon value (asymptotic floor).
            decay: Multiplicative decay applied when not on a plateau.
            min_epsilon: Hard lower bound for epsilon.
            plateaus: Optional list of Plateau segments (inclusive start/end) overriding epsilon.
        """
        self.start = start
        self.end = end
        self.decay = decay
        self.min_epsilon = min_epsilon
        self.current = start
        self.plateaus: List[Plateau] = sorted(plateaus or [], key=lambda p: p.start)

    def _active_plateau(self, episode: Optional[int]) -> Optional[Plateau]:
        if episode is None:
            return None
        for plateau in self.plateaus:
            if plateau.start <= episode <= plateau.end:
                return plateau
        return None

    def step(self, episode: Optional[int] = None):
        """Advance epsilon after processing a given episode."""
        plateau = self._active_plateau(episode + 1 if episode is not None else None)
        if plateau:
            self.current = max(self.min_epsilon, plateau.value)
            return

        decayed = self.current * self.decay
        floor = max(self.end, self.min_epsilon)
        self.current = max(floor, decayed)

    def get(self, episode: Optional[int] = None) -> float:
        """Get epsilon for the given episode index (1-based)."""
        plateau = self._active_plateau(episode)
        if plateau:
            return max(self.min_epsilon, plateau.value)
        return self.current

    def reset(self):
        """Reset epsilon to initial value."""
        self.current = self.start

    def set_value(self, value: float):
        """Force epsilon to a specific value (respecting minimum)."""
        self.current = max(self.min_epsilon, float(value))

    def decay_towards(self, target: float, factor: float):
        """Blend current epsilon towards a target with a decay factor in (0,1]."""
        target = max(self.min_epsilon, target)
        factor = min(max(factor, 0.0), 1.0)
        self.current = factor * self.current + (1.0 - factor) * target
