from pathlib import Path

import pytest

from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)


def test_csv_parser_reads_rows(tmp_path: Path) -> None:
    file_path = tmp_path / "map.csv"
    file_path.write_text("a,b\nc,d\n", encoding="utf-8")

    parser = CSVParser()
    parser.open(str(file_path))

    first = parser.read()
    second = parser.read()

    assert first == ["a", "b"]
    assert second == ["c", "d"]

    parser.close()


def test_csv_parser_raises_stop_parsing_at_end(tmp_path: Path) -> None:
    file_path = tmp_path / "map.csv"
    file_path.write_text("a,b\n", encoding="utf-8")

    parser = CSVParser()
    parser.open(str(file_path))
    _ = parser.read()

    with pytest.raises(StopParsingException):
        parser.read()

    parser.close()


def test_csv_parser_custom_delimiter(tmp_path: Path) -> None:
    file_path = tmp_path / "map.csv"
    file_path.write_text("a|b\n", encoding="utf-8")

    parser = CSVParser()
    parser.delimiter = "|"
    parser.open(str(file_path))

    row = parser.read()

    assert row == ["a", "b"]

    parser.close()
