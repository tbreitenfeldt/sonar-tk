from __future__ import annotations

from typing import Callable, Optional, cast

from pytest_mock import MockerFixture

from sonartk.orchestration.scene_audio_state import SceneAudioState
from sonartk.sound.openal_lite.openal import Player


class _FakeWindow:
    def __init__(self) -> None:
        self.pushed: list[object] = []
        self.popped_count = 0

    def push_window_handlers(self, *args: object, **kwargs: object) -> None:
        self.pushed.extend(args)

    def pop_window_handlers(self) -> None:
        self.popped_count += 1


class _FakeSoundService:
    def __init__(self) -> None:
        self.last_on_complete: Optional[Callable[[Player], None]] = None

    def play_sound(
        self,
        sound: str,
        player: Optional[Player] = None,
        on_complete: Optional[Callable[[Player], None]] = None,
    ) -> Player:
        self.last_on_complete = on_complete
        return cast(Player, player)


def test_scene_audio_state_setup_plays_sound_and_pushes_handlers(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    sound_service = _FakeSoundService()
    player = mocker.MagicMock()

    state = SceneAudioState(
        window=window,  # type: ignore[arg-type]
        scene_sound="intro.wav",
        scene_player=player,
        next_state_key="main",
        sound_service=sound_service,
    )

    change_state = mocker.MagicMock()
    assert state.setup(change_state) is True
    assert len(window.pushed) == 1
    assert sound_service.last_on_complete is not None


def test_scene_audio_state_continue_transitions_once_and_runs_callback(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    sound_service = _FakeSoundService()
    player = mocker.MagicMock()
    on_continue = mocker.MagicMock()
    change_state = mocker.MagicMock()

    state = SceneAudioState(
        window=window,  # type: ignore[arg-type]
        scene_sound="intro.wav",
        scene_player=player,
        next_state_key="main",
        on_continue=on_continue,
        sound_service=sound_service,
    )
    state.setup(change_state)

    assert state.continue_to_next_state() is True
    assert state.continue_to_next_state() is True

    player.stop.assert_called_once()
    change_state.assert_called_once_with("main", False)
    on_continue.assert_called_once()


def test_scene_audio_state_on_complete_invokes_continue(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    sound_service = _FakeSoundService()
    player = mocker.MagicMock()
    change_state = mocker.MagicMock()

    state = SceneAudioState(
        window=window,  # type: ignore[arg-type]
        scene_sound="intro.wav",
        scene_player=player,
        next_state_key="main",
        sound_service=sound_service,
    )
    state.setup(change_state)

    assert sound_service.last_on_complete is not None
    sound_service.last_on_complete(player)

    change_state.assert_called_once_with("main", False)


def test_scene_audio_state_exit_pops_handlers() -> None:
    window = _FakeWindow()
    sound_service = _FakeSoundService()

    state = SceneAudioState(
        window=window,  # type: ignore[arg-type]
        scene_sound="intro.wav",
        scene_player=object(),  # type: ignore[arg-type]
        next_state_key="main",
        sound_service=sound_service,
    )
    state.setup(lambda *_: None)

    assert state.exit() is True
    assert window.popped_count == 1


def test_scene_audio_state_continue_without_stop_flag(
    mocker: MockerFixture,
) -> None:
    window = _FakeWindow()
    sound_service = _FakeSoundService()
    player = mocker.MagicMock()
    change_state = mocker.MagicMock()

    state = SceneAudioState(
        window=window,  # type: ignore[arg-type]
        scene_sound="intro.wav",
        scene_player=player,
        next_state_key="main",
        stop_sound_on_continue=False,
        sound_service=sound_service,
    )
    state.setup(change_state)

    assert state.continue_to_next_state() is True
    player.stop.assert_not_called()


def test_scene_audio_state_update_returns_true() -> None:
    window = _FakeWindow()
    sound_service = _FakeSoundService()

    state = SceneAudioState(
        window=window,  # type: ignore[arg-type]
        scene_sound="intro.wav",
        scene_player=object(),  # type: ignore[arg-type]
        next_state_key="main",
        sound_service=sound_service,
    )

    assert state.update(0.016) is True
