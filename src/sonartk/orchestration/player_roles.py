from __future__ import annotations

from typing import Callable, Mapping, Optional

from sonartk.sound.openal_lite.openal import Player


def recover_players_by_role(
    previous_players: Mapping[str, Player],
    *,
    take_recovered_player: Callable[[Player], Optional[Player]],
    allocate_players_by_role: Callable[[list[str]], dict[str, Player]],
) -> dict[str, Player]:
    """Recover players by role and allocate replacements for missing roles."""
    recovered_players: dict[str, Player] = {}
    missing_roles: list[str] = []

    for role_name, previous_player in previous_players.items():
        recovered = take_recovered_player(previous_player)
        if recovered is None:
            missing_roles.append(role_name)
            continue
        recovered_players[role_name] = recovered

    if missing_roles:
        recovered_players.update(allocate_players_by_role(missing_roles))

    return recovered_players
