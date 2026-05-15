from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class MapParser(ABC, Generic[T]):
    @abstractmethod
    def open(self, file_name: str) -> None:
        """Open the source file and initialize parser state."""

    @abstractmethod
    def read(self) -> list[T]:
        """Read and return the next map row; raise StopParsingException when exhausted."""

    @abstractmethod
    def close(self) -> None:
        """Release any file handles or parser resources."""
