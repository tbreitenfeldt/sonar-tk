from pathlib import Path

import pytest

from sonartk.map_builder.map_2d.parser.json_parser import JSONParser
from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)


def test_json_parser_reads_items(tmp_path: Path) -> None:
    file_path = tmp_path / "map.json"
    file_path.write_text(
        '[ [{"id": 1}], [{"id": 2}] ]',
        encoding="utf-8",
    )

    parser = JSONParser()
    parser.open(str(file_path))

    first = parser.read()
    second = parser.read()

    assert first == [{"id": 1}]
    assert second == [{"id": 2}]

    parser.close()


def test_json_parser_raises_stop_parsing_at_end(tmp_path: Path) -> None:
    file_path = tmp_path / "map.json"
    file_path.write_text('[ [{"id": 1}] ]', encoding="utf-8")

    parser = JSONParser()
    parser.open(str(file_path))
    _ = parser.read()

    with pytest.raises(StopParsingException):
        parser.read()

    parser.close()
