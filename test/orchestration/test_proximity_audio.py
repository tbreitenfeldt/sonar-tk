from typing import cast

from sonartk.orchestration.proximity_audio import (
    ProximityAudioController,
    ProximityAudioEmitter,
)
from sonartk.sound.openal_lite.openal import Player


class _FakePlayer:
    def __init__(self) -> None:
        self.stop_calls = 0
        self.remove_calls = 0

    def stop(self) -> None:
        self.stop_calls += 1

    def remove(self) -> None:
        self.remove_calls += 1


class _FakeSoundService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def play_sound(
        self,
        sound: str,
        player: _FakePlayer | None = None,
        position: tuple[int, int, int] | None = None,
        volume: float = 1.0,
        rolloff: float = 0.01,
        loop: bool = False,
        retrigger_if_same: bool = True,
    ) -> _FakePlayer:
        self.calls.append(
            {
                "sound": sound,
                "player": player,
                "position": position,
                "volume": volume,
                "rolloff": rolloff,
                "loop": loop,
                "retrigger_if_same": retrigger_if_same,
            }
        )
        return player if player is not None else _FakePlayer()


def _build_controller(
    *,
    sound_service: _FakeSoundService,
    player: _FakePlayer,
) -> ProximityAudioController:
    emitter = ProximityAudioEmitter(
        sound_path="hum.wav",
        source_coordinates=(5, 5),
        max_distance_tiles=4,
        base_volume=0.8,
        min_volume_at_max_distance=0.25,
        distance_curve_exponent=2.0,
        rolloff=1.5,
        loop=True,
    )
    return ProximityAudioController(
        emitters={"hum": emitter},
        players={"hum": cast(Player, player)},
        position_resolver=lambda c: (c[0], 0, c[1]),
        sound_service=sound_service,  # type: ignore[arg-type]
    )


def test_update_stops_and_removes_when_inactive() -> None:
    sound_service = _FakeSoundService()
    player = _FakePlayer()
    controller = _build_controller(sound_service=sound_service, player=player)

    is_active = controller.update(
        "hum",
        listener_coordinates=(5, 5),
        is_active=False,
    )

    assert is_active is False
    assert player.stop_calls == 1
    assert player.remove_calls == 1
    assert sound_service.calls == []


def test_update_stops_and_removes_when_out_of_range() -> None:
    sound_service = _FakeSoundService()
    player = _FakePlayer()
    controller = _build_controller(sound_service=sound_service, player=player)

    is_active = controller.update(
        "hum",
        listener_coordinates=(20, 20),
        is_active=True,
    )

    assert is_active is False
    assert player.stop_calls == 1
    assert player.remove_calls == 1
    assert sound_service.calls == []


def test_update_plays_sound_when_active_and_in_range() -> None:
    sound_service = _FakeSoundService()
    player = _FakePlayer()
    controller = _build_controller(sound_service=sound_service, player=player)

    is_active = controller.update(
        "hum",
        listener_coordinates=(6, 5),
        is_active=True,
    )

    assert is_active is True
    assert len(sound_service.calls) == 1
    call = sound_service.calls[0]
    assert call["sound"] == "hum.wav"
    assert call["position"] == (5, 0, 5)
    assert call["player"] is player
    assert call["rolloff"] == 1.5
    assert call["loop"] is True
    assert call["retrigger_if_same"] is False


def test_update_many_returns_activity_by_emitter_key() -> None:
    sound_service = _FakeSoundService()
    player = _FakePlayer()
    controller = _build_controller(sound_service=sound_service, player=player)

    results = controller.update_many(
        listener_coordinates=(6, 5),
        is_active_by_key={"hum": True},
    )

    assert results == {"hum": True}


def test_effective_volume_returns_base_volume_for_zero_distance_limit() -> (
    None
):
    volume = ProximityAudioController.effective_volume(
        distance_tiles=3,
        max_distance_tiles=0,
        base_volume=0.6,
        min_volume_at_max_distance=0.1,
        distance_curve_exponent=2.0,
    )

    assert volume == 0.6
