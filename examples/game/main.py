"""Audio-map gameplay example with terrain, collectibles, and scene states."""

import sys
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
PROJECT_SRC = EXAMPLE_DIR.parents[1] / "src"
sys.path.insert(0, str(PROJECT_SRC))
sys.path.insert(0, str(EXAMPLE_DIR))

from game_app import MapSoundsExampleGame  # noqa: E402


def main() -> None:
    """Run the map sounds game example."""
    MapSoundsExampleGame().run()


if __name__ == "__main__":
    main()
