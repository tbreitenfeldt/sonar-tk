from typing import Any, Optional, cast
from io import TextIOWrapper
import csv

from sonartk.map_builder.map_2d.parser.map_parser import MapParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)


class CSVParser(MapParser[str]):
    def __init__(self) -> None:
        self.delimiter: str = ","
        self.file: Optional[TextIOWrapper] = None
        self.csv_reader: Any = None

    def open(self, file_name: str) -> None:
        self.file = open(file_name)
        self.csv_reader = csv.reader(self.file, delimiter=self.delimiter)

    def read(self) -> list[str]:
        try:
            return next(self.csv_reader)
        except StopIteration:
            raise StopParsingException

    def close(self) -> None:
        cast(TextIOWrapper, self.file).close()
