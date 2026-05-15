from typing import Any, Optional
from io import TextIOWrapper

import ijson
from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)


class JSONParser(MapParser[dict]):
    def __init__(self) -> None:
        file: Optional[TextIOWrapper] = None  # NOQA
        parser: Any = None  # NOQA

    def open(self, file_name: str) -> None:
        """Open a JSON file and prepare an item iterator for top-level entries."""
        self.file = open(file_name, "rb")
        self.parser = ijson.items(self.file, "item")

    def read(self) -> list[dict]:
        """Read and return the next parsed JSON item, or raise StopParsingException at EOF."""
        try:
            return next(self.parser)
        except StopIteration:
            raise StopParsingException

    def close(self) -> None:
        """Close the currently open JSON file handle."""
        self.file.close()
