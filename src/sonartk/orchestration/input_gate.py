from dataclasses import dataclass


@dataclass
class InputGate:
    """Simple mutable gate for temporarily suppressing input callbacks."""

    is_locked: bool = False

    def lock(self) -> None:
        self.is_locked = True

    def unlock(self) -> None:
        self.is_locked = False

    def reset(self) -> None:
        self.is_locked = False
