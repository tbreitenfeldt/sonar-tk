import sys


sys.path.insert(0, "../src")


try:
    from sonartk.map_builder.map_2d.parser.csv_parser import CSVParser  # type: ignore
    from sonartk.map_builder.map_2d.parser.stop_parsing_exception import StopParsingException  # type: ignore
except Exception:
    raise


def main() -> None:
    parser = CSVParser()
    parser.open("./test.csv")

    while True:
        try:
            line: list[str] = parser.read()
            print(line)
        except StopParsingException:
            break

    parser.close()


main()
