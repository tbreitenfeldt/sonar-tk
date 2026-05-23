from typing import Any, BinaryIO, Iterator, Optional

import ijson
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)


class JSONParser(MapParser[dict]):
    def __init__(self) -> None:
        self.file: Optional[BinaryIO] = None
        self.parser: Optional[Iterator[Any]] = None

    def open(self, file_name: str) -> None:
        """Open a JSON file and prepare an item iterator for top-level entries."""
        self.close()
        self.file = open(file_name, "rb")
        self.parser = ijson.items(self.file, "item")

    def read(self) -> list[dict]:
        """Read and return the next parsed JSON item, or raise StopParsingException at EOF."""
        if self.parser is None:
            raise RuntimeError("JSONParser must be opened before reading.")

        try:
            return next(self.parser)
        except StopIteration:
            raise StopParsingException

    def close(self) -> None:
        """Close the currently open JSON file handle."""
        if self.file is not None:
            self.file.close()
            self.file = None
        self.parser = None
