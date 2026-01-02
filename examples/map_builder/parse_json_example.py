import sys


sys.path.insert(0, "../src")


try:
    from sonartk.map_builder.map_2d.parser.json_parser import JSONParser  # type: ignore
    from sonartk.map_builder.map_2d.parser.stop_parsing_exception import StopParsingException  # type: ignore
except Exception:
    raise


def main() -> None:
    parser = JSONParser()
    parser.open("./test.json")

    while True:
        try:
            line = parser.read()
            print(line)
        except StopParsingException:
            break

    parser.close()


main()
