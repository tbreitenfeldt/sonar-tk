from __future__ import annotations

from typing import Optional

from sonartk.sound.channel_loop import ChannelLoop


class _FakePlayer:
    def __init__(self) -> None:
        self.stopped = 0
        self.removed = 0

    def stop(self) -> None:
        self.stopped += 1

    def remove(self) -> None:
        self.removed += 1


class _FakeSound:
    def __init__(self) -> None:
        self.played: list[dict[str, object]] = []
        self.players: list[_FakePlayer] = []
        self.channel_volumes: list[tuple[str, float]] = []
        self.applied: list[tuple[object, str, float]] = []

    def play_sound(
        self,
        sound: str,
        *,
        volume: float = 1.0,
        loop: bool = False,
        channel: str = "sfx",
    ) -> _FakePlayer:
        self.played.append(
            {
                "sound": sound,
                "volume": volume,
                "loop": loop,
                "channel": channel,
            }
        )
        player = _FakePlayer()
        self.players.append(player)
        return player

    def set_channel_volume(self, channel: str, volume: float) -> float:
        clamped = min(max(volume, 0.0), 1.0)
        self.channel_volumes.append((channel, clamped))
        return clamped

    def apply_channel_volume(
        self, player: object, channel: str, base_volume: float = 1.0
    ) -> float:
        self.applied.append((player, channel, base_volume))
        return base_volume


def _loop(
    service: Optional[_FakeSound] = None,
) -> tuple[ChannelLoop, _FakeSound]:
    service = service or _FakeSound()
    return ChannelLoop("ambience", sound_service=service), service  # type: ignore[arg-type]


def test_play_loops_on_the_channel_with_its_gain() -> None:
    loop, service = _loop()

    player = loop.play("ocean.wav", gain=0.4)

    assert service.played == [
        {
            "sound": "ocean.wav",
            "volume": 0.4,
            "loop": True,
            "channel": "ambience",
        }
    ]
    assert loop.player is player
    assert loop.gain == 0.4
    assert loop.is_playing


def test_default_gain_is_full() -> None:
    loop, service = _loop()
    loop.play("ocean.wav")
    assert service.played[0]["volume"] == 1.0


def test_play_replaces_the_current_loop() -> None:
    loop, service = _loop()
    loop.play("ocean.wav")
    loop.play("wind.wav")

    first = service.players[0]
    assert (first.stopped, first.removed) == (1, 1)
    assert loop.player is service.players[1]


def test_stop_releases_the_loop_and_resets_the_gain() -> None:
    loop, service = _loop()
    loop.play("ocean.wav", gain=0.3)

    loop.stop()

    player = service.players[0]
    assert (player.stopped, player.removed) == (1, 1)
    assert loop.player is None
    assert loop.gain == 1.0
    assert not loop.is_playing


def test_stop_without_a_loop_is_harmless() -> None:
    loop, _ = _loop()
    loop.stop()
    assert not loop.is_playing


def test_set_volume_rescales_the_playing_loop_by_its_gain() -> None:
    loop, service = _loop()
    player = loop.play("wind.wav", gain=0.46)

    result = loop.set_volume(0.5)

    assert result == 0.5
    assert service.channel_volumes == [("ambience", 0.5)]
    assert service.applied == [(player, "ambience", 0.46)]


def test_set_volume_clamps_and_skips_players_when_idle() -> None:
    loop, service = _loop()

    assert loop.set_volume(3.0) == 1.0
    assert service.applied == []


def test_defaults_to_the_shared_sound_manager(mocker) -> None:  # type: ignore[no-untyped-def]
    from sonartk.sound import sound_manager

    assert ChannelLoop("ambience").sound_service is sound_manager
