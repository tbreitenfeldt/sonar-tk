from typing import Any, cast

from sonartk.orchestration.proximity_audio import (
    ProximityAudioController,
    ProximityAudioEmitter,
)
from sonartk.sound.openal_lite.openal import Player


class _FakePlayer:
    def __init__(self) -> None:
        self.stop_calls = 0
        self.remove_calls = 0
        self.is_playing = False
        self.queue_is_empty = False
        self._seek = 0.0

    def stop(self) -> None:
        self.stop_calls += 1

    def remove(self) -> None:
        self.remove_calls += 1

    def playing(self) -> bool:
        return self.is_playing

    @property
    def seek(self) -> float:
        return self._seek

    @seek.setter
    def seek(self, value: float) -> None:
        if self.queue_is_empty:
            raise IndexError("list index out of range")
        self._seek = value


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


def test_update_forwards_channel_only_when_configured() -> None:
    class _ChannelService(_FakeSoundService):
        def play_sound(self, *args: Any, **kwargs: Any) -> _FakePlayer:  # type: ignore[override]
            self.calls.append(kwargs)
            return _FakePlayer()

    sound_service = _ChannelService()
    emitter = ProximityAudioEmitter(
        sound_path="hum.wav",
        source_coordinates=(5, 5),
        max_distance_tiles=4,
        base_volume=1.0,
        min_volume_at_max_distance=0.0,
        distance_curve_exponent=1.0,
        rolloff=1.0,
        channel="ambience",
    )
    controller = ProximityAudioController(
        emitters={"hum": emitter},
        players={"hum": cast(Player, _FakePlayer())},
        position_resolver=lambda c: (c[0], 0, c[1]),
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    controller.update("hum", listener_coordinates=(5, 5), is_active=True)

    assert sound_service.calls[0]["channel"] == "ambience"


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


def test_emitter_defaults_keep_rolloff_gentle() -> None:
    emitter = ProximityAudioEmitter("hum.wav", (1, 1), max_distance_tiles=5)

    assert emitter.base_volume == 1.0
    assert emitter.min_volume_at_max_distance == 0.0
    assert emitter.distance_curve_exponent == 1.0
    assert emitter.rolloff == 0.05


def test_from_emitters_creates_a_player_per_emitter(mocker) -> None:  # type: ignore[no-untyped-def]
    player_class = mocker.patch(
        "sonartk.orchestration.proximity_audio.Player",
        side_effect=lambda: _FakePlayer(),
    )
    emitters = {
        "a": ProximityAudioEmitter("a.wav", (0, 0), max_distance_tiles=2),
        "b": ProximityAudioEmitter("b.wav", (3, 3), max_distance_tiles=2),
    }

    controller = ProximityAudioController.from_emitters(
        emitters,
        position_resolver=lambda c: (c[0], 0, c[1]),
        sound_service=_FakeSoundService(),  # type: ignore[arg-type]
    )

    assert set(controller.players) == {"a", "b"}
    assert controller.players["a"] is not controller.players["b"]
    assert player_class.call_count == 2


def test_update_at_treats_every_emitter_as_active() -> None:
    sound_service = _FakeSoundService()
    player = _FakePlayer()
    controller = _build_controller(sound_service=sound_service, player=player)

    in_range = controller.update_at((5, 6))
    out_of_range = controller.update_at((50, 50))

    assert in_range == {"hum": True}
    assert out_of_range == {"hum": False}
    assert len(sound_service.calls) == 1
    assert player.stop_calls == 1


def test_stop_all_stops_and_removes_every_player() -> None:
    first, second = _FakePlayer(), _FakePlayer()
    controller = ProximityAudioController(
        emitters={},
        players={"a": first, "b": second},  # type: ignore[dict-item]
        position_resolver=lambda c: (c[0], 0, c[1]),
    )

    controller.stop_all()

    for player in (first, second):
        assert (player.stop_calls, player.remove_calls) == (1, 1)


def _offset_controller(player: _FakePlayer, offset: float):  # type: ignore[no-untyped-def]
    emitter = ProximityAudioEmitter(
        sound_path="hum.wav",
        source_coordinates=(5, 5),
        max_distance_tiles=10,
        start_offset=offset,
    )
    return ProximityAudioController(
        emitters={"hum": emitter},
        players={"hum": cast(Player, player)},
        position_resolver=lambda c: (c[0], 0, c[1]),
        sound_service=_FakeSoundService(),  # type: ignore[arg-type]
    )


def test_start_offset_seeks_a_newly_started_loop() -> None:
    player = _FakePlayer()
    controller = _offset_controller(player, 0.25)

    controller.update_at((5, 5))

    assert player.seek == 0.25


def test_start_offset_does_not_rewind_a_loop_already_playing() -> None:
    player = _FakePlayer()
    player.is_playing = True
    controller = _offset_controller(player, 0.25)

    controller.update_at((5, 5))

    assert player.seek == 0.0


def test_no_start_offset_leaves_the_loop_alone() -> None:
    player = _FakePlayer()
    controller = _offset_controller(player, 0.0)

    controller.update_at((5, 5))

    assert player.seek == 0.0


def test_start_offset_is_skipped_when_nothing_was_queued() -> None:
    player = _FakePlayer()
    player.queue_is_empty = True
    controller = _offset_controller(player, 0.5)

    assert controller.update_at((5, 5)) == {"hum": True}
    assert player.seek == 0.0


def test_footprint_sound_comes_from_the_nearest_tile() -> None:
    emitter = ProximityAudioEmitter(
        sound_path="hum.wav",
        source_coordinates=(5, 5),
        max_distance_tiles=10,
        footprint=((5, 5), (6, 5), (7, 5)),
    )

    assert emitter.nearest_source((9, 6)) == (7, 5)
    assert emitter.nearest_source((0, 5)) == (5, 5)


def test_emitter_without_a_footprint_uses_its_source() -> None:
    emitter = ProximityAudioEmitter(
        sound_path="hum.wav",
        source_coordinates=(5, 5),
        max_distance_tiles=10,
    )

    assert emitter.nearest_source((9, 6)) == (5, 5)


def test_footprint_sounds_the_same_from_either_end() -> None:
    sound_service = _FakeSoundService()
    player = _FakePlayer()
    emitter = ProximityAudioEmitter(
        sound_path="hum.wav",
        source_coordinates=(5, 5),
        max_distance_tiles=10,
        footprint=((5, 5), (6, 5), (7, 5)),
    )
    controller = ProximityAudioController(
        emitters={"hum": emitter},
        players={"hum": cast(Player, player)},
        position_resolver=lambda c: (c[0], 0, c[1]),
        sound_service=sound_service,  # type: ignore[arg-type]
    )

    controller.update("hum", listener_coordinates=(4, 5), is_active=True)
    controller.update("hum", listener_coordinates=(8, 5), is_active=True)

    first, second = sound_service.calls
    assert first["volume"] == second["volume"]
    assert first["position"] == (5, 0, 5)
    assert second["position"] == (7, 0, 5)
