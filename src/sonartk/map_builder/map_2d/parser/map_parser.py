from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class MapParser(ABC, Generic[T]):
    @abstractmethod
    def open(self, file_name: str) -> None:
        """Opens a file using the provided file name."""

    @abstractmethod
    def read(self) -> list[T]:
        """Reads one row of a 2d map. This method is expected to be called from a loop."""

    @abstractmethod
    def close(self) -> None:
        """Close the file."""
