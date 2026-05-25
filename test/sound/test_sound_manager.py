from typing import Any, cast

import pytest
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


def test_play_music_applies_music_channel_volume(
    mocker: MockerFixture,
) -> None:
    """Test play_music scales final volume by the music channel volume."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = object()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager.set_music_volume(0.5)

    manager.play_music("music/theme.ogg", volume=0.8)

    assert music_player.volume == 0.4


def test_play_music_with_fade_schedules_and_reaches_target(
    mocker: MockerFixture,
) -> None:
    """Test play_music fade scheduling interpolates and unschedules at completion."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = object()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False
    music_player.volume = 1.0

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    schedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    unschedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )

    manager.play_music(
        "music/theme.ogg",
        volume=0.6,
        fade_in_seconds=1.0,
        fade_step_seconds=0.05,
    )

    assert music_player.volume == 0.0
    schedule_mock.assert_called_once()
    fade_callback = schedule_mock.call_args.args[0]

    fade_callback(0.5)
    assert music_player.volume == pytest.approx(0.3)
    fade_callback(0.5)
    assert music_player.volume == pytest.approx(0.6)
    unschedule_mock.assert_called_with(fade_callback)


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
        position=cast(tuple[int, int, int], (9, 8, 7)),
        rolloff=0.5,
        loop=True,
    )

    assert result is player
    sound_pool.load.assert_not_called()
    player_pool.get_player.assert_not_called()
    player.stop.assert_called_once()
    player.remove.assert_called_once()
    player.add.assert_called_once_with(sound_obj)
    assert player.loop is True
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
    assert player.loop is False
    assert player.rolloff == 0.01
    assert player.position == (5, 5, 5)
    player.play.assert_called_once()


def test_play_sound_applies_channel_scaled_volume(
    mocker: MockerFixture,
) -> None:
    """Test play_sound scales player volume using channel and local volume."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = object()
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
    manager.set_sfx_volume(0.5)

    manager.play_sound("sfx/select.wav", volume=0.6)

    assert player.volume == pytest.approx(0.3)


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
        position=cast(tuple[int, int, int], (4, 3, 2)),
        loop=True,
        rolloff=0.42,
    )

    assert result is player
    assert player.loop is True
    assert player.rolloff == 0.42
    assert player.position == (4, 3, 2)
    player.play.assert_called_once()


def test_play_sound_reapplies_effects_and_filters_when_reusing_queue(
    mocker: MockerFixture,
) -> None:
    """Test play_sound reapplies effects and filters for already-queued sounds."""
    sound_obj: Any = object()
    player = mocker.MagicMock()
    player.queue = [sound_obj]
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

    player.stop.assert_not_called()
    player.remove.assert_not_called()
    player.add.assert_not_called()
    player.add_effect.assert_any_call(effect_1)
    player.add_effect.assert_any_call(effect_2)
    player.add_filter.assert_called_once_with(filter_1)


def test_play_sound_waits_until_finished_when_requested(
    mocker: MockerFixture,
) -> None:
    """Test play_sound blocks and polls until the player is no longer playing."""
    sound_obj: Any = object()
    player = mocker.MagicMock()
    player.queue = [sound_obj]
    player.playing.side_effect = [True, True, False]
    sleep_mock = mocker.patch("sonartk.sound.sound_manager.time.sleep")

    mocker.patch.object(
        sound_manager, "listener", mocker.MagicMock(position=(0, 0, 0))
    )

    result = sound_manager.play_sound(
        sound_obj,
        player=player,
        wait_until_finished=True,
        poll_interval_seconds=0.02,
    )

    assert result is player
    assert player.playing.call_count == 3
    sleep_mock.assert_called_with(0.02)
    assert sleep_mock.call_count == 2


def test_play_sound_rejects_non_positive_poll_interval(
    mocker: MockerFixture,
) -> None:
    """Test play_sound validates poll interval when waiting is enabled."""
    player = mocker.MagicMock()
    player.queue = []

    mocker.patch.object(
        sound_manager, "listener", mocker.MagicMock(position=(0, 0, 0))
    )

    with pytest.raises(ValueError, match="poll_interval_seconds must be > 0"):
        sound_manager.play_sound(
            object(),  # type: ignore[arg-type]
            player=player,
            wait_until_finished=True,
            poll_interval_seconds=0,
        )


def test_play_sound_schedules_non_blocking_on_complete_callback(
    mocker: MockerFixture,
) -> None:
    """Test play_sound schedules and invokes on_complete without blocking."""
    sound_obj: Any = object()
    player = mocker.MagicMock()
    player.queue = [sound_obj]
    player.playing.side_effect = [True, False]
    on_complete = mocker.MagicMock()

    mocker.patch.object(
        sound_manager, "listener", mocker.MagicMock(position=(0, 0, 0))
    )
    schedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    unschedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )

    sound_manager.play_sound(
        sound_obj,
        player=player,
        on_complete=on_complete,
        completion_poll_interval_seconds=0.05,
    )

    schedule_mock.assert_called_once()
    poll = schedule_mock.call_args.args[0]
    interval = schedule_mock.call_args.args[1]
    assert interval == 0.05
    on_complete.assert_not_called()

    poll(0.01)
    on_complete.assert_not_called()
    unschedule_mock.assert_not_called()

    poll(0.01)
    unschedule_mock.assert_called_once_with(poll)
    on_complete.assert_called_once_with(player)


def test_play_sound_rejects_invalid_completion_poll_interval(
    mocker: MockerFixture,
) -> None:
    """Test play_sound validates non-blocking completion poll interval."""
    player = mocker.MagicMock()
    player.queue = []

    mocker.patch.object(
        sound_manager, "listener", mocker.MagicMock(position=(0, 0, 0))
    )

    with pytest.raises(
        ValueError,
        match="completion_poll_interval_seconds must be > 0",
    ):
        sound_manager.play_sound(
            object(),  # type: ignore[arg-type]
            player=player,
            on_complete=lambda _: None,
            completion_poll_interval_seconds=0,
        )


def test_channel_helpers_apply_and_validate(mocker: MockerFixture) -> None:
    """Test channel helpers clamp values, apply to players, and validate names."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    sfx_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    assert manager.set_channel_volume("sfx", 1.4) == 1.0
    assert manager.set_channel_volume("music", -1.0) == 0.0
    manager.set_sfx_volume(0.25, players=[sfx_player])
    assert sfx_player.volume == pytest.approx(0.25)

    with pytest.raises(ValueError, match="Unknown channel"):
        manager.get_channel_volume("bad")


def test_module_clamp_volume_function() -> None:
    """Test module-level clamp_volume keeps values within [0, 1]."""
    assert sound_manager.clamp_volume(-0.1) == 0.0
    assert sound_manager.clamp_volume(0.5) == 0.5
    assert sound_manager.clamp_volume(10.0) == 1.0


def test_play_music_validates_fade_arguments(mocker: MockerFixture) -> None:
    """Test play_music rejects invalid fade-in argument combinations."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    with pytest.raises(ValueError, match="fade_in_seconds must be >= 0"):
        manager.play_music("music/theme.ogg", fade_in_seconds=-0.1)

    with pytest.raises(ValueError, match="fade_step_seconds must be > 0"):
        manager.play_music(
            "music/theme.ogg",
            fade_in_seconds=1.0,
            fade_step_seconds=0.0,
        )


def test_play_music_unschedules_previous_fade_callback(
    mocker: MockerFixture,
) -> None:
    """Test replacing music unschedules any prior fade callback first."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = object()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    old_callback = mocker.MagicMock()
    manager._music_fade_callback = old_callback
    unschedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )

    manager.play_music("music/theme.ogg")

    unschedule_mock.assert_called_once_with(old_callback)
    assert manager._music_fade_callback is None


def test_cleanup_unschedules_active_music_fade_callback(
    mocker: MockerFixture,
) -> None:
    """Test cleanup unschedules active music fade callback before teardown."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    callback = mocker.MagicMock()
    manager._music_fade_callback = callback
    unschedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )

    manager.cleanup()

    unschedule_mock.assert_called_once_with(callback)
    assert manager._music_fade_callback is None


def test_module_volume_wrappers_delegate_to_default_manager(
    mocker: MockerFixture,
) -> None:
    """Test module-level volume helpers forward calls to the default manager."""
    manager = mocker.MagicMock()
    manager.get_channel_volume.return_value = 0.4
    manager.set_channel_volume.return_value = 0.5
    manager.set_music_volume.return_value = 0.6
    manager.set_sfx_volume.return_value = 0.7
    mocker.patch.object(sound_manager, "_default_manager", manager)

    player = mocker.MagicMock()

    assert sound_manager.get_channel_volume("music") == 0.4
    assert sound_manager.set_channel_volume("music", 0.9) == 0.5
    assert sound_manager.set_music_volume(0.8, fade_seconds=1.0) == 0.6
    assert sound_manager.set_sfx_volume(0.3, players=[player]) == 0.7
    sound_manager.apply_sfx_volume(player, base_volume=0.2)

    manager.get_channel_volume.assert_called_once_with("music")
    manager.set_channel_volume.assert_called_once_with("music", 0.9)
    manager.set_music_volume.assert_called_once_with(
        0.8,
        fade_seconds=1.0,
        fade_step_seconds=0.05,
    )
    manager.set_sfx_volume.assert_called_once_with(0.3, players=[player])
    manager.apply_sfx_volume.assert_called_once_with(player, base_volume=0.2)


def test_set_music_volume_validates_and_schedules_fade(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    with pytest.raises(ValueError, match="fade_seconds must be >= 0"):
        manager.set_music_volume(0.5, fade_seconds=-1.0)

    with pytest.raises(ValueError, match="fade_step_seconds must be > 0"):
        manager.set_music_volume(0.5, fade_seconds=1.0, fade_step_seconds=0)

    old_callback = mocker.MagicMock()
    manager._music_fade_callback = old_callback
    unschedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )
    schedule_mock = mocker.patch.object(manager, "_schedule_music_fade")

    target = manager.set_music_volume(0.8, fade_seconds=1.0)

    assert target == 0.8
    unschedule_mock.assert_called_once_with(old_callback)
    schedule_mock.assert_called_once_with(
        0.8,
        duration_seconds=1.0,
        step_seconds=0.05,
    )


def test_schedule_music_fade_with_non_positive_duration_completes_immediately(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.volume = 0.2

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    schedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    unschedule_mock = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )

    manager._schedule_music_fade(
        0.9,
        duration_seconds=0.0,
        step_seconds=0.05,
    )

    fade_callback = schedule_mock.call_args.args[0]
    manager._music_fade_callback = mocker.MagicMock()
    fade_callback(0.01)

    assert music_player.volume == pytest.approx(0.9)
    unschedule_mock.assert_called_once_with(fade_callback)


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


def test_sound_manager_instance_preload_sounds_uses_injected_pool(
    mocker: MockerFixture,
) -> None:
    """Test SoundManager.preload_sounds delegates to injected sound_pool."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    expected = {"/abs/audio/a.wav": object()}
    sound_pool.load_many.return_value = expected
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    result = manager.preload_sounds(["audio/a.wav"])

    assert result is expected
    sound_pool.load_many.assert_called_once_with(["audio/a.wav"])


def test_module_preload_sounds_delegates_to_default_manager(
    mocker: MockerFixture,
) -> None:
    """Test module-level preload_sounds forwards to default manager."""
    manager = mocker.MagicMock()
    expected = {"/abs/audio/click.wav": object()}
    manager.preload_sounds.return_value = expected
    mocker.patch.object(sound_manager, "_default_manager", manager)

    paths = ["audio/click.wav", "audio/music.ogg"]
    result = sound_manager.preload_sounds(paths)

    assert result is expected
    manager.preload_sounds.assert_called_once_with(paths)
