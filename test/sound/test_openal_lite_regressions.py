from typing import Any, cast

from pytest import MonkeyPatch

from sonartk.sound.openal_lite import openal


def test_player_set_direction_and_velocity_target_source(
    monkeypatch: MonkeyPatch,
) -> None:
    """Direction/velocity setters must update source properties, not listener."""
    player = cast(Any, openal.Player.__new__(openal.Player))
    player.source = 123
    player._direction = [0.0, 0.0, 0.0]
    player._velocity = [0.0, 0.0, 0.0]

    source_calls: list[tuple[int, int, float, float, float]] = []
    listener_calls: list[tuple[int, float, float, float]] = []

    def fake_source3f(
        source: int, enum: int, x: float, y: float, z: float
    ) -> None:
        source_calls.append((source, enum, x, y, z))

    def fake_listener3f(enum: int, x: float, y: float, z: float) -> None:
        listener_calls.append((enum, x, y, z))

    monkeypatch.setattr(openal.al, "alSource3f", fake_source3f)
    monkeypatch.setattr(openal.al, "alListener3f", fake_listener3f)

    player._set_direction((1, 2, 3))
    player._set_velocity((4, 5, 6))

    assert listener_calls == []
    assert source_calls == [
        (123, openal.al.AL_DIRECTION, 1.0, 2.0, 3.0),
        (123, openal.al.AL_VELOCITY, 4.0, 5.0, 6.0),
    ]


def test_efxslot_delete_uses_aux_slot_deletion(
    monkeypatch: MonkeyPatch,
) -> None:
    """EFX slot cleanup must delete auxiliary slots, not sound buffers."""
    slot = cast(Any, openal.EFXslot.__new__(openal.EFXslot))
    slot.slot = openal.al.ALuint(7)

    calls: list[str] = []

    def fake_set_effect(effect: object) -> None:
        assert effect is None
        calls.append("set_effect")

    def fake_delete_aux_slots(_count: int, _slot: object) -> None:
        calls.append("delete_aux_slot")

    def fake_delete_buffers(_count: int, _slot: object) -> None:
        calls.append("delete_buffers")

    monkeypatch.setattr(slot, "set_effect", fake_set_effect)
    monkeypatch.setattr(
        openal.efx, "alDeleteAuxiliaryEffectSlots", fake_delete_aux_slots
    )
    monkeypatch.setattr(openal.al, "alDeleteBuffers", fake_delete_buffers)

    slot.delete()

    assert calls == ["set_effect", "delete_aux_slot"]


def test_player_reset_and_delete_remove_all_effects_and_filters() -> None:
    """Cleanup loops should remove every effect/filter entry."""
    player = cast(Any, openal.Player.__new__(openal.Player))
    player.queue = []
    player._effect = ["e1", "e2", "e3"]
    player._filter = ["f1", "f2"]
    player.source = 456

    player.playing = lambda: False
    player.stop = lambda: None
    player.remove = lambda: None

    removed_effects: list[str] = []
    removed_filters: list[str] = []

    def del_effect(effect: str) -> None:
        removed_effects.append(effect)
        player._effect.remove(effect)

    def del_filter(filtr: str) -> None:
        removed_filters.append(filtr)
        player._filter.remove(filtr)

    player.del_effect = del_effect
    player.del_filter = del_filter

    player.reset()

    assert removed_effects == ["e1", "e2", "e3"]
    assert removed_filters == ["f1", "f2"]
    assert player._effect == []
    assert player._filter == []


def test_listener_delete_clears_current_context_before_destroy(
    monkeypatch: MonkeyPatch,
) -> None:
    """Listener teardown should clear current context before destroy."""
    listener = cast(Any, openal.Listener.__new__(openal.Listener))
    listener.captureDev = None
    listener.context = object()
    listener.device = object()

    teardown_calls: list[str] = []

    monkeypatch.setattr(
        openal.alc,
        "alcMakeContextCurrent",
        lambda ctx: teardown_calls.append(
            "make_none" if ctx is None else "make_other"
        ),
    )
    monkeypatch.setattr(
        openal.alc,
        "alcDestroyContext",
        lambda _ctx: teardown_calls.append("destroy"),
    )
    monkeypatch.setattr(
        openal.alc,
        "alcCloseDevice",
        lambda _dev: teardown_calls.append("close"),
    )

    listener.delete()

    assert teardown_calls == ["make_none", "destroy", "close"]
