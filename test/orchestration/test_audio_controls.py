from __future__ import annotations

from typing import Callable, Optional

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.orchestration.audio_controls import bind_volume_hotkeys


class _FakeKeyHandler:
    def __init__(self) -> None:
        self.bindings: list[
            tuple[Callable[[], bool], int, tuple[int, ...]]
        ] = []

    def add_key_press(
        self,
        callback: Callable[[], bool],
        key_code: int,
        modifiers: Optional[list[int]] = None,
    ) -> None:
        self.bindings.append((callback, key_code, tuple(modifiers or [])))


class _FakeWindow:
    def __init__(self) -> None:
        self.key_handler = _FakeKeyHandler()


def _get_callback(
    window: _FakeWindow,
    key_code: int,
    modifiers: tuple[int, ...],
) -> Callable[[], bool]:
    for callback, bound_key, bound_modifiers in window.key_handler.bindings:
        if bound_key == key_code and bound_modifiers == modifiers:
            return callback
    raise AssertionError("Expected key binding was not registered")


def test_bind_volume_hotkeys_registers_expected_shortcuts() -> None:
    window = _FakeWindow()

    bind_volume_hotkeys(window=window)  # type: ignore[arg-type]

    assert len(window.key_handler.bindings) == 4
    _ = _get_callback(window, key.F7, tuple())
    _ = _get_callback(window, key.F6, tuple())
    _ = _get_callback(window, key.F7, (key.MOD_SHIFT,))
    _ = _get_callback(window, key.F6, (key.MOD_SHIFT,))


def test_bind_volume_hotkeys_invokes_sound_manager_helpers(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    sfx_player = object()

    get_channel_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.get_channel_volume",
        side_effect=lambda channel: 0.5 if channel == "music" else 0.4,
    )
    set_music_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_music_volume"
    )
    set_sfx_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_sfx_volume",
        return_value=0.45,
    )

    bind_volume_hotkeys(
        window=window,  # type: ignore[arg-type]
        sfx_player=sfx_player,  # type: ignore[arg-type]
        music_step=0.1,
        sfx_step=0.2,
        couple_music_to_sfx_ratio=0.5,
    )

    increase_music = _get_callback(window, key.F7, tuple())
    decrease_music = _get_callback(window, key.F6, tuple())
    increase_sfx = _get_callback(window, key.F7, (key.MOD_SHIFT,))

    assert increase_music() is True
    assert decrease_music() is True
    assert increase_sfx() is True

    assert get_channel_mock.call_count >= 3
    set_music_mock.assert_any_call(0.6)
    set_music_mock.assert_any_call(0.4)
    called_args, called_kwargs = set_sfx_mock.call_args
    assert called_args[0] == pytest.approx(0.6)
    assert called_kwargs == {"players": [sfx_player]}
    set_music_mock.assert_any_call(0.225)


def test_bind_volume_hotkeys_decrease_sfx_without_coupling(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()

    get_channel_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.get_channel_volume",
        return_value=0.7,
    )
    set_sfx_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_sfx_volume",
        return_value=0.6,
    )
    set_music_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_music_volume"
    )

    bind_volume_hotkeys(
        window=window,  # type: ignore[arg-type]
        sfx_step=0.1,
        couple_music_to_sfx_ratio=None,
    )

    decrease_sfx = _get_callback(window, key.F6, (key.MOD_SHIFT,))
    assert decrease_sfx() is True

    get_channel_mock.assert_called_once_with("sfx")
    set_sfx_mock.assert_called_once_with(0.6, players=None)
    set_music_mock.assert_not_called()


def test_bind_volume_hotkeys_uses_dynamic_sfx_player_resolver(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    first_player = object()
    second_player = object()
    active_player = first_player

    get_channel_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.get_channel_volume",
        return_value=0.5,
    )
    set_sfx_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_sfx_volume",
        return_value=0.5,
    )

    def resolve_player() -> object:
        return active_player

    bind_volume_hotkeys(
        window=window,  # type: ignore[arg-type]
        sfx_player_resolver=resolve_player,  # type: ignore[arg-type]
        sfx_step=0.1,
    )

    increase_sfx = _get_callback(window, key.F7, (key.MOD_SHIFT,))
    assert increase_sfx() is True

    active_player = second_player
    assert increase_sfx() is True

    assert get_channel_mock.call_count == 2
    assert set_sfx_mock.call_count == 2
    first_call_kwargs = set_sfx_mock.call_args_list[0].kwargs
    second_call_kwargs = set_sfx_mock.call_args_list[1].kwargs
    assert first_call_kwargs == {"players": [first_player]}
    assert second_call_kwargs == {"players": [second_player]}


def test_bind_volume_hotkeys_uses_dynamic_sfx_players_resolver(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    first_players = [object(), object()]
    second_players = [object(), object(), object()]
    active_players = first_players

    get_channel_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.get_channel_volume",
        return_value=0.6,
    )
    set_sfx_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_sfx_volume",
        return_value=0.55,
    )
    set_music_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_music_volume"
    )

    def resolve_players() -> list[object]:
        return active_players

    bind_volume_hotkeys(
        window=window,  # type: ignore[arg-type]
        sfx_players_resolver=resolve_players,  # type: ignore[arg-type]
        sfx_step=0.1,
        couple_music_to_sfx_ratio=None,
    )

    increase_sfx = _get_callback(window, key.F7, (key.MOD_SHIFT,))
    assert increase_sfx() is True

    active_players = second_players
    assert increase_sfx() is True

    assert get_channel_mock.call_count == 2
    assert set_sfx_mock.call_count == 2
    first_call_kwargs = set_sfx_mock.call_args_list[0].kwargs
    second_call_kwargs = set_sfx_mock.call_args_list[1].kwargs
    assert first_call_kwargs == {"players": first_players}
    assert second_call_kwargs == {"players": second_players}
    set_music_mock.assert_not_called()


def test_bind_volume_hotkeys_notifies_on_sfx_volume_changed(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    get_channel_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.get_channel_volume",
        return_value=0.5,
    )
    set_sfx_mock = mocker.patch(
        "sonartk.orchestration.audio_controls.sound_manager.set_sfx_volume",
        return_value=0.4,
    )
    on_changed = mocker.MagicMock()

    bind_volume_hotkeys(
        window=window,  # type: ignore[arg-type]
        sfx_step=0.1,
        couple_music_to_sfx_ratio=None,
        on_sfx_volume_changed=on_changed,
    )

    decrease_sfx = _get_callback(window, key.F6, (key.MOD_SHIFT,))
    assert decrease_sfx() is True

    get_channel_mock.assert_called_once_with("sfx")
    set_sfx_mock.assert_called_once_with(0.4, players=None)
    on_changed.assert_called_once_with(0.4)
