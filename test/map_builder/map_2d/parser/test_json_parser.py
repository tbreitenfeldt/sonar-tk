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


def test_json_parser_close_is_safe_without_open() -> None:
    parser = JSONParser()

    parser.close()

    assert parser.file is None


def test_json_parser_context_manager_closes_file(tmp_path: Path) -> None:
    file_path = tmp_path / "map.json"
    file_path.write_text('[ [{"id": 1}] ]', encoding="utf-8")

    parser = JSONParser()
    with parser:
        parser.open(str(file_path))
        assert parser.file is not None

    assert parser.file is None


def test_json_parser_read_raises_if_not_opened() -> None:
    parser = JSONParser()

    with pytest.raises(RuntimeError, match="must be opened"):
        parser.read()
