from __future__ import annotations

from enum import Enum
from typing import Optional, TypeVar

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
