from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TextHistory:
    """Maintain a bounded most-recent-first history of text entries."""

    limit: int = 50
    entries: list[str] = field(default_factory=list)
    index: int | None = None

    def record(self, value: str) -> None:
        """Store a non-empty value and reset navigation state."""
        entry = value.strip()
        if entry == "":
            return

        self.entries.insert(0, entry)
        self.entries = self.entries[: self.limit]
        self.index = None

    def previous_value(self) -> str | None:
        """Move to older history and return the selected entry."""
        if not self.entries:
            return None

        if self.index is None:
            self.index = 0
        elif self.index < len(self.entries) - 1:
            self.index += 1

        return self.entries[self.index]

    def next_value(self) -> str | None:
        """Move to newer history and return the selected entry."""
        if not self.entries or self.index is None:
            return None

        if self.index == 0:
            self.index = None
            return ""

        self.index -= 1
        return self.entries[self.index]

    def clear(self) -> None:
        """Reset the navigation cursor without clearing stored entries."""
        self.index = None
