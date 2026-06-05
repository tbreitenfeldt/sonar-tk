from __future__ import annotations

from typing import Optional, cast

from sonartk.orchestration.player_roles import recover_players_by_role
from sonartk.sound.openal_lite.openal import Player


def test_recover_players_by_role_reuses_recovered_and_allocates_missing() -> (
    None
):
    previous_players: dict[str, Player] = {
        "music": cast(Player, object()),
        "sfx": cast(Player, object()),
    }
    recovered_music: Player = cast(Player, object())
    allocated_sfx: Player = cast(Player, object())

    def take_recovered_player(player: Player) -> Optional[Player]:
        if player is previous_players["music"]:
            return recovered_music
        return None

    def allocate_players_by_role(roles: list[str]) -> dict[str, Player]:
        assert roles == ["sfx"]
        return {"sfx": allocated_sfx}

    result = recover_players_by_role(
        previous_players,
        take_recovered_player=take_recovered_player,
        allocate_players_by_role=allocate_players_by_role,
    )

    assert result == {
        "music": recovered_music,
        "sfx": allocated_sfx,
    }
