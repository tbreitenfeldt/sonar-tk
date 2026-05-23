from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from types import TracebackType

T = TypeVar("T")


class MapParser(ABC, Generic[T]):
    def __enter__(self) -> "MapParser[T]":
        """Enter context manager scope for parser lifecycle handling."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Ensure parser resources are released when leaving scope."""
        _ = exc_type, exc_value, traceback
        self.close()

    @abstractmethod
    def open(self, file_name: str) -> None:
        """Open the source file and initialize parser state."""

    @abstractmethod
    def read(self) -> list[T]:
        """Read and return the next map row; raise StopParsingException when exhausted."""

    @abstractmethod
    def close(self) -> None:
        """Release any file handles or parser resources."""
