class MapTile:
    def __init__(
        self, name: str, is_passable: bool = True, is_one_way: bool = False
    ) -> None:
        self.name: str = name
        self.is_passable: bool = is_passable
        self.is_one_way: bool = is_one_way
        self.is_jumpable: bool = False

    def interact(self) -> None:
        """Interact."""
        pass

    def __str__(self) -> str:
        return f"(name: {self.name}, is_passable: {self.is_passable}, is_one_way: {self.is_one_way}, is_jumpable: {self.is_jumpable})"
