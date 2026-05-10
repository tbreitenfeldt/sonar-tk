from sonartk.map_builder.map_2d.parser.stop_parsing_exception import (
    StopParsingException,
)


def test_stop_parsing_exception_is_exception() -> None:
    error = StopParsingException("done")

    assert isinstance(error, Exception)
    assert str(error) == "done"
