from typing import Any, cast

from pytest_mock import MockerFixture

from sonartk.sound import sound_manager
from sonartk.sound.sound_manager import SoundManager

# play_music Tests


def test_play_music_stops_existing_music_before_replacing(
    mocker: MockerFixture,
) -> None:
    """Test play_music stops and removes currently playing music first."""
    music_player = mocker.MagicMock()
    music_player.playing.return_value = True
    mocker.patch.object(sound_manager, "music_player", music_player)

    loaded_sound = object()
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = loaded_sound
    mocker.patch.object(sound_manager, "sound_pool", sound_pool)

    sound_manager.play_music("music/theme.ogg", loop=False)

    music_player.stop.assert_called_once()
    music_player.remove.assert_called_once()
    sound_pool.load.assert_called_once_with("music/theme.ogg")
    music_player.add.assert_called_once_with(loaded_sound)
    assert music_player.loop is False
    music_player.play.assert_called_once()


def test_play_music_does_not_stop_when_nothing_playing(
    mocker: MockerFixture,
) -> None:
    """Test play_music skips stop/remove when music is not playing."""
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False
    mocker.patch.object(sound_manager, "music_player", music_player)

    loaded_sound = object()
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = loaded_sound
    mocker.patch.object(sound_manager, "sound_pool", sound_pool)

    sound_manager.play_music("music/theme.ogg")

    music_player.stop.assert_not_called()
    music_player.remove.assert_not_called()
    sound_pool.load.assert_called_once_with("music/theme.ogg")
    music_player.add.assert_called_once_with(loaded_sound)
    assert music_player.loop is True
    music_player.play.assert_called_once()


# Music control passthrough tests


def test_pause_music_calls_player_pause(mocker: MockerFixture) -> None:
    """Test pause_music delegates to music_player.pause."""
    music_player = mocker.MagicMock()
    mocker.patch.object(sound_manager, "music_player", music_player)

    sound_manager.pause_music()

    music_player.pause.assert_called_once()


def test_resume_music_calls_player_play(mocker: MockerFixture) -> None:
    """Test resume_music delegates to music_player.play."""
    music_player = mocker.MagicMock()
    mocker.patch.object(sound_manager, "music_player", music_player)

    sound_manager.resume_music()

    music_player.play.assert_called_once()


def test_stop_music_calls_player_stop(mocker: MockerFixture) -> None:
    """Test stop_music delegates to music_player.stop."""
    music_player = mocker.MagicMock()
    mocker.patch.object(sound_manager, "music_player", music_player)

    sound_manager.stop_music()

    music_player.stop.assert_called_once()


# play_sound Tests


def test_play_sound_loads_from_path_and_uses_pool_player(
    mocker: MockerFixture,
) -> None:
    """Test play_sound loads sound path and fetches a player when not supplied."""
    loaded_sound = object()

    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = loaded_sound
    mocker.patch.object(sound_manager, "sound_pool", sound_pool)

    player = mocker.MagicMock()
    player.queue = []
    player_pool = mocker.MagicMock()
    player_pool.get_player.return_value = player
    mocker.patch.object(sound_manager, "player_pool", player_pool)

    listener = mocker.MagicMock()
    listener.position = (1, 2, 3)
    mocker.patch.object(sound_manager, "listener", listener)

    result = sound_manager.play_sound("sfx/select.wav")

    assert result is player
    sound_pool.load.assert_called_once_with("sfx/select.wav")
    player_pool.get_player.assert_called_once()
    player.stop.assert_called_once()
    player.remove.assert_called_once()
    player.add.assert_called_once_with(loaded_sound)
    assert player.rolloff == 0.01
    assert player.position == (1, 2, 3)
    player.play.assert_called_once()


def test_play_sound_uses_given_player_and_position_without_loading(
    mocker: MockerFixture,
) -> None:
    """Test play_sound respects explicit player and position for object sound."""
    sound_obj: Any = object()

    sound_pool = mocker.MagicMock()
    mocker.patch.object(sound_manager, "sound_pool", sound_pool)

    player_pool = mocker.MagicMock()
    mocker.patch.object(sound_manager, "player_pool", player_pool)

    player = mocker.MagicMock()
    player.queue = []

    result = sound_manager.play_sound(
        sound=sound_obj,
        player=player,
        position=cast(tuple[int], (9, 8, 7)),
        rolloff=0.5,
    )

    assert result is player
    sound_pool.load.assert_not_called()
    player_pool.get_player.assert_not_called()
    player.stop.assert_called_once()
    player.remove.assert_called_once()
    player.add.assert_called_once_with(sound_obj)
    assert player.rolloff == 0.5
    assert player.position == (9, 8, 7)
    player.play.assert_called_once()


def test_play_sound_adds_effects_and_filters(
    mocker: MockerFixture,
) -> None:
    """Test play_sound adds all provided effects and filters."""
    sound_obj: Any = object()
    player = mocker.MagicMock()
    player.queue = []

    effect_1 = object()
    effect_2 = object()
    filter_1 = object()

    mocker.patch.object(
        sound_manager, "listener", mocker.MagicMock(position=(0, 0, 0))
    )

    sound_manager.play_sound(
        sound=sound_obj,
        player=player,
        effects=[effect_1, effect_2],
        filters=[filter_1],
    )

    player.add_effect.assert_any_call(effect_1)
    player.add_effect.assert_any_call(effect_2)
    player.add_effect.assert_called_with(effect_2)
    player.add_filter.assert_called_once_with(filter_1)


def test_play_sound_reuses_existing_queued_sound(
    mocker: MockerFixture,
) -> None:
    """Test play_sound does not requeue when sound is already in player queue."""
    sound_obj: Any = object()
    player = mocker.MagicMock()
    player.queue = [sound_obj]

    mocker.patch.object(
        sound_manager, "listener", mocker.MagicMock(position=(5, 5, 5))
    )

    result = sound_manager.play_sound(sound_obj, player=player)

    assert result is player
    player.stop.assert_not_called()
    player.remove.assert_not_called()
    player.add.assert_not_called()
    assert player.position == (5, 5, 5)
    player.play.assert_called_once()


def test_play_sound_uses_custom_position_when_reusing_queue(
    mocker: MockerFixture,
) -> None:
    """Test play_sound applies explicit position even when queue already has sound."""
    sound_obj: Any = object()
    player = mocker.MagicMock()
    player.queue = [sound_obj]

    result = sound_manager.play_sound(
        sound_obj,
        player=player,
        position=cast(tuple[int], (4, 3, 2)),
    )

    assert result is player
    assert player.position == (4, 3, 2)
    player.play.assert_called_once()


# cleanup Tests


def test_cleanup_releases_all_audio_resources(mocker: MockerFixture) -> None:
    """Test cleanup destroys pools and deletes listener/music player."""
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    listener = mocker.MagicMock()
    music_player = mocker.MagicMock()

    mocker.patch.object(sound_manager, "sound_pool", sound_pool)
    mocker.patch.object(sound_manager, "player_pool", player_pool)
    mocker.patch.object(sound_manager, "listener", listener)
    mocker.patch.object(sound_manager, "music_player", music_player)

    sound_manager.cleanup()

    sound_pool.destroy.assert_called_once()
    player_pool.destroy.assert_called_once()
    listener.delete.assert_called_once()
    music_player.delete.assert_called_once()


def test_sound_manager_instance_play_music_uses_injected_dependencies(
    mocker: MockerFixture,
) -> None:
    """Test SoundManager instance can be constructed with injected services."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False
    loaded_sound = object()
    sound_pool.load.return_value = loaded_sound

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    manager.play_music("music/theme.ogg", loop=False)

    sound_pool.load.assert_called_once_with("music/theme.ogg")
    music_player.add.assert_called_once_with(loaded_sound)
    assert music_player.loop is False
    music_player.play.assert_called_once()


def test_sound_manager_instance_play_sound_uses_injected_pools(
    mocker: MockerFixture,
) -> None:
    """Test SoundManager.play_sound uses injected pool/listener resources."""
    listener = mocker.MagicMock()
    listener.position = (7, 8, 9)
    sound_pool = mocker.MagicMock()
    loaded_sound = object()
    sound_pool.load.return_value = loaded_sound
    player_pool = mocker.MagicMock()
    player = mocker.MagicMock()
    player.queue = []
    player_pool.get_player.return_value = player
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    result = manager.play_sound("sfx/select.wav")

    assert result is player
    sound_pool.load.assert_called_once_with("sfx/select.wav")
    player_pool.get_player.assert_called_once()
    assert player.position == (7, 8, 9)
