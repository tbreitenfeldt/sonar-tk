from typing import Iterator, Optional
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
        self.csv_reader: Optional[Iterator[list[str]]] = None

    def open(self, file_name: str) -> None:
        """Open a CSV file and prepare a row iterator using the configured delimiter."""
        self.close()
        self.file = open(file_name)
        self.csv_reader = csv.reader(self.file, delimiter=self.delimiter)

    def read(self) -> list[str]:
        """Read and return the next CSV row, or raise StopParsingException at EOF."""
        if self.csv_reader is None:
            raise RuntimeError("CSVParser must be opened before reading.")

        try:
            return next(self.csv_reader)
        except StopIteration:
            raise StopParsingException

    def close(self) -> None:
        """Close the currently open CSV file handle."""
        if self.file is not None:
            self.file.close()
            self.file = None
        self.csv_reader = None
