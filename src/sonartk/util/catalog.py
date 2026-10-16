from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Iterable, Optional, TypeVar

E = TypeVar("E", bound=Enum)


def resolve_name(
    catalog: type[E], name: Optional[str], label: str = "entry"
) -> Optional[E]:
    """Look up an enum member by the lower-case name used in data files.

    Data files such as map documents refer to sounds, music and terrain by
    plain names. A game keeps its assets in enums and uses this to bind the
    two: ``"ocean"`` finds ``Ambience.OCEAN``. ``None`` is passed through so
    optional fields need no special case.

    Args:
        catalog: Enum whose member names are the upper-case file names.
        name: Name from the data file, or ``None``.
        label: Description of the field, used in the error message.

    Raises:
        ValueError: If the catalog has no member with that name.
    """
    if name is None:
        return None
    try:
        return catalog[name.upper()]
    except KeyError:
        raise ValueError(
            f"Unknown {label} {name!r} in {catalog.__name__}."
        ) from None


class AssetCatalog:
    """Resolve logical asset keys to file paths under one root folder.

    The key for each file is its path relative to the root without extension,
    normalized to forward slashes. For example:
    ``audio/shared/sfx/ui/menu_click.wav`` -> ``shared/sfx/ui/menu_click``.
    """

    def __init__(self, root: Path, entries: dict[str, str]) -> None:
        self.root = root
        self._entries = entries

    @classmethod
    def from_directory(
        cls,
        root: Path | str,
        *,
        suffixes: tuple[str, ...] = (".wav",),
    ) -> "AssetCatalog":
        """Build a catalog by recursively scanning ``root`` for files."""
        base = Path(root).resolve()
        entries: dict[str, str] = {}
        allowed = {suffix.lower() for suffix in suffixes}
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() not in allowed:
                continue
            key = path.relative_to(base).with_suffix("").as_posix().lower()
            if key in entries:
                raise ValueError(
                    f"Duplicate catalog key {key!r} under {base}."
                )
            entries[key] = str(path)
        return cls(base, entries)

    @property
    def keys(self) -> tuple[str, ...]:
        """Catalog keys sorted alphabetically."""
        return tuple(sorted(self._entries))

    def keys_under(self, prefix: str) -> tuple[str, ...]:
        """Keys inside the folder ``prefix``, such as ``maps/beach``."""
        folder = prefix.lower().strip("/") + "/"
        return tuple(key for key in self.keys if key.startswith(folder))

    def paths_under(self, prefix: str) -> list[str]:
        """File paths inside the folder ``prefix``, sorted by key."""
        return [self._entries[key] for key in self.keys_under(prefix)]

    def require(self, key: str, label: str = "asset") -> str:
        """Return the file path for ``key`` or raise with context."""
        normalized = key.lower()
        path = self._entries.get(normalized)
        if path is None:
            raise ValueError(
                f"Unknown {label} {key!r} in {self.root.as_posix()}."
            )
        return path

    def get(self, key: Optional[str], label: str = "asset") -> Optional[str]:
        """Resolve an optional key to a path."""
        if key is None:
            return None
        return self.require(key, label)

    def many(self, keys: Iterable[str], label: str = "asset") -> list[str]:
        """Resolve several keys, preserving order."""
        return [self.require(key, label) for key in keys]
