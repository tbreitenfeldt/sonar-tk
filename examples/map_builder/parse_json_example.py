import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
sys.path.insert(0, str(PROJECT_SRC))


try:
    from sonartk.map_builder.map_2d.parser.json_parser import JSONParser  # type: ignore
    from sonartk.map_builder.map_2d.parser.stop_parsing_exception import StopParsingException  # type: ignore
except Exception:
    raise


def main() -> None:
    parser = JSONParser()
    parser.open(str(EXAMPLE_DIR / "test.json"))

    while True:
        try:
            line = parser.read()
            print(line)
        except StopParsingException:
            break

    parser.close()


if __name__ == "__main__":
    main()
