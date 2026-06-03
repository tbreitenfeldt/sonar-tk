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


def test_play_music_schedules_seek_restore_when_resuming_position(
    mocker: MockerFixture,
) -> None:
    """Resumed music should schedule seek restoration retries after play starts."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = object()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = True
    music_player.seek = 0.25

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    schedule_seek_restore = mocker.patch.object(
        manager, "_schedule_music_seek_restore"
    )

    manager.play_music("music/theme.ogg", resume_seek_ratio=0.25)

    schedule_seek_restore.assert_called_once_with(0.25)


def test_stop_music_cancels_pending_seek_restore(
    mocker: MockerFixture,
) -> None:
    """Stopping music should cancel any pending seek-restore callback."""
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
    cancel_seek_restore = mocker.patch.object(
        manager, "_cancel_music_seek_restore"
    )

    manager.stop_music()

    cancel_seek_restore.assert_called_once()


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


def test_sound_manager_instance_allocate_players_by_role(
    mocker: MockerFixture,
) -> None:
    """Test role-based player allocation uses injected player pool."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    player_a = mocker.MagicMock()
    player_b = mocker.MagicMock()
    player_pool.get_player.side_effect = [player_a, player_b]
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    allocated = manager.allocate_players_by_role(["nav", "ambient"])

    assert allocated == {"nav": player_a, "ambient": player_b}
    assert player_pool.get_player.call_count == 2


def test_sound_manager_instance_allocate_players_by_role_rejects_duplicates(
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

    with pytest.raises(ValueError, match="Duplicate role name"):
        manager.allocate_players_by_role(["nav", "nav"])


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


def test_module_allocate_players_by_role_delegates_to_default_manager(
    mocker: MockerFixture,
) -> None:
    manager = mocker.MagicMock()
    expected = {"nav": mocker.MagicMock()}
    manager.allocate_players_by_role.return_value = expected
    mocker.patch.object(sound_manager, "_default_manager", manager)

    result = sound_manager.allocate_players_by_role(["nav"])

    assert result is expected
    manager.allocate_players_by_role.assert_called_once_with(["nav"])


def test_start_output_device_watch_recovers_on_device_change(
    mocker: MockerFixture,
) -> None:
    """Device watch should trigger recovery when current/default outputs diverge."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    schedule_interval = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    mocker.patch("sonartk.sound.sound_manager.pyglet.clock.schedule_once")
    unschedule = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.unschedule"
    )
    recover = mocker.patch.object(
        manager, "_begin_recovery", return_value=True
    )

    names = iter(["Speakers", "Speakers", "Headphones", "Speakers"])
    mocker.patch.object(
        manager,
        "_safe_default_output_name",
        side_effect=lambda: next(names),
    )
    mocker.patch.object(
        manager,
        "_safe_current_output_name",
        side_effect=lambda: next(names),
    )

    manager.start_output_device_watch(poll_interval_seconds=0.25)
    poll_callback = schedule_interval.call_args.args[0]

    poll_callback(0.01)
    recover.assert_called_once_with(1)

    manager.stop_output_device_watch()
    assert unschedule.call_count >= 1


def test_recovery_status_callback_emits_after_threshold(
    mocker: MockerFixture,
) -> None:
    """Recovery status cue should be emitted only when recovery exceeds delay."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    status_callback = mocker.MagicMock()
    schedule_once = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_once"
    )
    mocker.patch("sonartk.sound.sound_manager.pyglet.clock.schedule_interval")
    mocker.patch("sonartk.sound.sound_manager.pyglet.clock.unschedule")
    mocker.patch.object(manager, "_safe_default_output_name", return_value="D")
    mocker.patch.object(manager, "_safe_current_output_name", return_value="C")
    mocker.patch.object(manager, "_rebuild_audio_graph", return_value=True)

    manager.start_output_device_watch(
        poll_interval_seconds=0.25,
        status_callback=status_callback,
        status_delay_seconds=5.0,
    )

    # Simulate slow recovery currently in progress, then fire delay timer.
    manager._recovery_in_progress = True
    manager._start_recovery_status_timer()
    notify = schedule_once.call_args.args[0]
    notify(5.0)

    status_callback.assert_any_call("Audio device changed. Recovering audio.")


def test_begin_recovery_cancels_status_timer_on_failed_recovery(
    mocker: MockerFixture,
) -> None:
    """Failed recovery attempts should clear pending status timers."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._status_callback = mocker.MagicMock()
    manager._status_delay_seconds = 5.0
    manager._status_timer_callback = lambda _: None

    cancel_timer = mocker.patch.object(
        manager, "_cancel_recovery_status_timer"
    )
    mocker.patch.object(
        manager, "_soft_reset_output_device", return_value=False
    )
    mocker.patch.object(manager, "_rebuild_audio_graph", return_value=False)

    assert not manager._begin_recovery(0)
    cancel_timer.assert_called_once()
    assert manager._status_announced_for_cycle is False
    assert manager._recovery_in_progress is False


def test_output_device_watch_recovers_on_backend_health_failure(
    mocker: MockerFixture,
) -> None:
    """Recovery should trigger after consecutive backend health failures."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    schedule_interval = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    mocker.patch("sonartk.sound.sound_manager.pyglet.clock.schedule_once")
    recover = mocker.patch.object(
        manager, "_begin_recovery", return_value=True
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    mocker.patch.object(manager, "_has_backend_errors", return_value=True)
    mocker.patch.object(manager, "_is_device_disconnected", return_value=False)

    manager.start_output_device_watch(poll_interval_seconds=0.25)
    poll_callback = schedule_interval.call_args.args[0]

    poll_callback(0.01)
    recover.assert_not_called()

    poll_callback(0.01)

    recover.assert_called_once_with(1)


def test_output_device_watch_applies_recovery_cooldown_for_non_immediate_triggers(
    mocker: MockerFixture,
) -> None:
    """Non-immediate recovery paths should not re-trigger repeatedly within cooldown."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._min_recovery_interval_seconds = 10.0

    schedule_interval = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager,
        "_safe_output_device_inventory_signature",
        return_value="Speakers",
    )
    mocker.patch.object(manager, "_has_backend_errors", return_value=True)
    mocker.patch.object(manager, "_is_device_disconnected", return_value=False)
    mocker.patch.object(
        manager, "_is_music_playback_stalled", return_value=False
    )
    recover = mocker.patch.object(
        manager, "_begin_recovery", return_value=False
    )
    monotonic = mocker.patch(
        "sonartk.sound.sound_manager.time.monotonic",
        side_effect=[100.0, 100.1],
    )

    manager.start_output_device_watch(poll_interval_seconds=0.25)
    poll_callback = schedule_interval.call_args.args[0]

    poll_callback(0.01)
    poll_callback(0.01)
    poll_callback(0.01)

    recover.assert_called_once_with(1)
    assert monotonic.call_count == 2


def test_start_output_device_watch_emits_enabled_status(
    mocker: MockerFixture,
) -> None:
    """Watcher should emit a startup status message when callback is provided."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    status_callback = mocker.MagicMock()
    mocker.patch("sonartk.sound.sound_manager.pyglet.clock.schedule_interval")
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )

    manager.start_output_device_watch(
        status_callback=status_callback,
    )

    status_callback.assert_called_once_with("Audio device monitoring enabled.")


def test_output_device_watch_recovers_on_device_transition_change(
    mocker: MockerFixture,
) -> None:
    """Watcher should recover when default/current device transitions are observed."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    schedule_interval = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    defaults = iter(["Speakers", "Headphones"])
    currents = iter(["Speakers", "Speakers"])
    mocker.patch.object(
        manager,
        "_safe_default_output_name",
        side_effect=lambda: next(defaults),
    )
    mocker.patch.object(
        manager,
        "_safe_current_output_name",
        side_effect=lambda: next(currents),
    )
    mocker.patch.object(manager, "_has_backend_errors", return_value=False)
    mocker.patch.object(manager, "_is_device_disconnected", return_value=False)
    recover = mocker.patch.object(
        manager, "_begin_recovery", return_value=True
    )

    manager.start_output_device_watch(
        poll_interval_seconds=0.25,
    )
    poll_callback = schedule_interval.call_args.args[0]
    poll_callback(0.01)

    recover.assert_called_once_with(1)


def test_output_device_watch_recovers_on_inventory_change(
    mocker: MockerFixture,
) -> None:
    """Watcher should recover when playback device inventory changes."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    schedule_interval = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    signatures = iter(["Speakers", "Speakers|Headphones"])
    mocker.patch.object(
        manager,
        "_safe_output_device_inventory_signature",
        side_effect=lambda: next(signatures),
    )
    mocker.patch.object(manager, "_has_backend_errors", return_value=False)
    mocker.patch.object(manager, "_is_device_disconnected", return_value=False)
    recover = mocker.patch.object(
        manager, "_begin_recovery", return_value=True
    )

    manager.start_output_device_watch(poll_interval_seconds=0.25)
    poll_callback = schedule_interval.call_args.args[0]
    poll_callback(0.01)

    recover.assert_called_once_with(1, skip_soft_reset=True)


def test_output_watch_recovers_on_music_stall(
    mocker: MockerFixture,
) -> None:
    """Watcher should trigger recovery when playing music offset stalls."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = True
    music_player.source = 1

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"
    manager._music_stall_threshold_seconds = 1.0

    schedule_interval = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    mocker.patch.object(manager, "_has_backend_errors", return_value=False)
    mocker.patch.object(manager, "_is_device_disconnected", return_value=False)
    mocker.patch.object(manager, "_get_player_byte_offset", return_value=1024)
    recover = mocker.patch.object(
        manager, "_begin_recovery", return_value=True
    )

    manager.start_output_device_watch(poll_interval_seconds=0.25)
    poll_callback = schedule_interval.call_args.args[0]

    poll_callback(0.6)
    recover.assert_not_called()

    poll_callback(0.6)
    recover.assert_not_called()

    poll_callback(0.6)
    recover.assert_called_once_with(1)


def test_music_stall_poll_updates_last_seek_ratio_from_offset(
    mocker: MockerFixture,
) -> None:
    """Stall polling should continuously persist seek ratio from byte offsets."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = True
    music_player.source = 1
    music_player.queue = [mocker.MagicMock(length=4000)]

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"
    manager._last_music_seek_ratio = 0.0

    mocker.patch.object(manager, "_get_player_byte_offset", return_value=1000)

    assert not manager._is_music_playback_stalled(0.1)
    assert manager._last_music_seek_ratio == pytest.approx(0.25)


def test_update_seek_ratio_from_offset_ignores_missing_queue(
    mocker: MockerFixture,
) -> None:
    """Seek ratio update should be a no-op when the player queue is empty."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.queue = []

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_seek_ratio = 0.42

    manager._update_last_music_seek_ratio_from_offset(1000)

    assert manager._last_music_seek_ratio == pytest.approx(0.42)


def test_capture_music_seek_ratio_preserves_previous_on_dropout_zero_seek(
    mocker: MockerFixture,
) -> None:
    """Dropout zero-seek reads should not erase a valid saved music position."""
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.queue = []
    music_player.seek = 0.0
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"
    manager._music_target_playing = True
    manager._last_music_seek_ratio = 0.63

    assert manager._capture_music_seek_ratio() == pytest.approx(0.63)
    assert manager._last_music_seek_ratio == pytest.approx(0.63)


def test_soft_reset_returns_false_when_default_mismatch_persists(
    mocker: MockerFixture,
) -> None:
    """Soft reset must fail when follow-default mode still mismatches route."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    listener.device = object()
    listener.context = object()
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._follow_default_output = True

    mocker.patch.object(manager, "_is_device_pointer", return_value=True)
    mocker.patch("sonartk.sound.sound_manager.alc.alcResetDeviceSOFT")
    mocker.patch("sonartk.sound.sound_manager.alc.alcProcessContext")
    mocker.patch.object(manager, "_has_backend_errors", return_value=False)
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Headphones"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )

    assert not manager._soft_reset_output_device()


def test_soft_reset_returns_false_when_routing_names_unavailable(
    mocker: MockerFixture,
) -> None:
    """Soft reset should force rebuild when route names cannot be read."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    listener.device = object()
    listener.context = object()
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._follow_default_output = True

    mocker.patch.object(manager, "_is_device_pointer", return_value=True)
    mocker.patch("sonartk.sound.sound_manager.alc.alcResetDeviceSOFT")
    mocker.patch("sonartk.sound.sound_manager.alc.alcProcessContext")
    mocker.patch.object(manager, "_has_backend_errors", return_value=False)
    mocker.patch.object(manager, "_safe_default_output_name", return_value="")
    mocker.patch.object(manager, "_safe_current_output_name", return_value="")

    assert not manager._soft_reset_output_device()


def test_soft_reset_restarts_music_with_saved_seek_ratio(
    mocker: MockerFixture,
) -> None:
    """Soft reset should resume music from captured seek position."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    listener.device = object()
    listener.context = object()
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"
    manager._last_music_loop = True
    manager._last_music_volume = 0.7
    manager._music_target_playing = True
    manager._last_music_seek_ratio = 0.42

    mocker.patch.object(manager, "_is_device_pointer", return_value=True)
    mocker.patch("sonartk.sound.sound_manager.alc.alcResetDeviceSOFT")
    mocker.patch("sonartk.sound.sound_manager.alc.alcProcessContext")
    mocker.patch.object(manager, "_has_backend_errors", return_value=False)
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_capture_music_seek_ratio", return_value=0.42
    )
    play_music = mocker.patch.object(manager, "play_music")

    assert manager._soft_reset_output_device()
    play_music.assert_called_once_with(
        "music/theme.ogg",
        loop=True,
        volume=0.7,
        fade_in_seconds=0.0,
        resume_seek_ratio=0.42,
    )


def test_rebuild_audio_graph_resumes_music_with_saved_seek_ratio(
    mocker: MockerFixture,
) -> None:
    """Rebuild should preserve seek position when resuming interrupted music."""
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"
    manager._last_music_loop = True
    manager._last_music_volume = 0.8
    manager._music_target_playing = True

    new_listener = mocker.MagicMock()
    new_listener.position = (0, 0, 0)
    new_sound_pool = mocker.MagicMock()
    new_sound_pool.cached_paths.return_value = []
    new_player_pool = mocker.MagicMock()
    new_music_player = mocker.MagicMock()

    mocker.patch(
        "sonartk.sound.sound_manager.Listener", return_value=new_listener
    )
    mocker.patch(
        "sonartk.sound.sound_manager.SoundPool", return_value=new_sound_pool
    )
    mocker.patch(
        "sonartk.sound.sound_manager.PlayerPool", return_value=new_player_pool
    )
    mocker.patch(
        "sonartk.sound.sound_manager.Player", return_value=new_music_player
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_capture_music_seek_ratio", return_value=0.37
    )
    play_music = mocker.patch.object(manager, "play_music")

    assert manager._rebuild_audio_graph()
    play_music.assert_called_once_with(
        "music/theme.ogg",
        loop=True,
        volume=0.8,
        fade_in_seconds=0.0,
        resume_seek_ratio=0.37,
    )


def test_rebuild_audio_graph_updates_module_globals(
    mocker: MockerFixture,
) -> None:
    """Recovery should update module globals used by wrapper sync."""
    from sonartk.sound import sound_manager as module

    old_listener = module.listener
    old_sound_pool = module.sound_pool
    old_player_pool = module.player_pool
    old_music_player = module.music_player

    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    new_listener = mocker.MagicMock()
    new_listener.position = (0, 0, 0)
    new_sound_pool = mocker.MagicMock()
    new_sound_pool.cached_paths.return_value = []
    new_player_pool = mocker.MagicMock()
    new_music_player = mocker.MagicMock()

    mocker.patch(
        "sonartk.sound.sound_manager.Listener", return_value=new_listener
    )
    mocker.patch(
        "sonartk.sound.sound_manager.SoundPool", return_value=new_sound_pool
    )
    mocker.patch(
        "sonartk.sound.sound_manager.PlayerPool", return_value=new_player_pool
    )
    mocker.patch(
        "sonartk.sound.sound_manager.Player", return_value=new_music_player
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )

    assert manager._rebuild_audio_graph()
    assert module.listener is new_listener
    assert module.sound_pool is new_sound_pool
    assert module.player_pool is new_player_pool
    assert module.music_player is new_music_player

    module.listener = old_listener
    module.sound_pool = old_sound_pool
    module.player_pool = old_player_pool
    module.music_player = old_music_player


def test_take_recovered_player_returns_and_consumes_mapping(
    mocker: MockerFixture,
) -> None:
    """Recovered player mapping should be one-time consumable by previous player."""
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

    previous_player = mocker.MagicMock()
    recovered_player = mocker.MagicMock()
    manager._last_recovered_player_map[id(previous_player)] = recovered_player

    assert manager.take_recovered_player(previous_player) is recovered_player
    assert manager.take_recovered_player(previous_player) is None


def test_rebuild_audio_graph_restores_currently_playing_players(
    mocker: MockerFixture,
) -> None:
    """Active playing players should be restored and mapped during rebuild."""
    old_player = mocker.MagicMock()
    old_player.playing.return_value = True
    old_player.queue = [object()]
    old_player.position = (1, 0, 2)
    old_player.volume = 0.42
    old_player.rolloff = 1.1
    old_player.loop = True

    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.pool = {"music/river.wav": old_player.queue[0]}
    sound_pool.cached_paths.return_value = ["music/river.wav"]
    player_pool = mocker.MagicMock()
    player_pool._active_players = [old_player]
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._player_channels_by_id[id(old_player)] = "sfx"

    new_listener = mocker.MagicMock()
    new_listener.position = (0, 0, 0)
    new_sound_pool = mocker.MagicMock()
    new_sound_pool.cached_paths.return_value = []
    new_player_pool = mocker.MagicMock()
    recovered_player = mocker.MagicMock()
    new_player_pool.get_player.return_value = recovered_player
    new_music_player = mocker.MagicMock()

    mocker.patch(
        "sonartk.sound.sound_manager.Listener", return_value=new_listener
    )
    mocker.patch(
        "sonartk.sound.sound_manager.SoundPool", return_value=new_sound_pool
    )
    mocker.patch(
        "sonartk.sound.sound_manager.PlayerPool", return_value=new_player_pool
    )
    mocker.patch(
        "sonartk.sound.sound_manager.Player", return_value=new_music_player
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    play_sound = mocker.patch.object(manager, "play_sound")

    assert manager._rebuild_audio_graph()
    assert play_sound.call_count >= 1
    assert play_sound.call_args_list[0].args[0] == "music/river.wav"
    assert play_sound.call_args_list[0].kwargs["player"] is recovered_player
    assert manager.take_recovered_player(old_player) is recovered_player


def test_music_seek_ratio_helpers_get_and_set(mocker: MockerFixture) -> None:
    """Internal seek helpers should read/write the player seek attribute."""
    player = mocker.MagicMock()
    player.seek = 0.35

    assert SoundManager._get_player_seek_ratio(player) == pytest.approx(0.35)
    SoundManager._set_player_seek_ratio(player, 0.6)
    assert player.seek == pytest.approx(0.6)


def test_trigger_play_with_device_retry_retries_once_when_watch_enabled(
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
    manager._device_watch_callback = lambda _: None

    trigger = mocker.MagicMock()
    playing = mocker.MagicMock(side_effect=[False, False])

    manager._trigger_play_with_device_retry(trigger, playing)

    assert trigger.call_count == 2


def test_should_retry_after_recovery_attempt_guard_paths(
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

    is_playing = mocker.MagicMock(return_value=False)
    assert not manager._should_retry_after_recovery_attempt(
        attempt=1,
        is_playing=is_playing,
        allow_recovery=True,
    )

    assert not manager._should_retry_after_recovery_attempt(
        attempt=0,
        is_playing=is_playing,
        allow_recovery=False,
    )


def test_should_retry_after_recovery_attempt_logs_failed_recovery(
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
    manager._device_watch_callback = lambda _: None
    debug_sink = mocker.MagicMock()
    manager.set_debug_callback(debug_sink)
    mocker.patch.object(manager, "_begin_recovery", return_value=False)

    result = manager._should_retry_after_recovery_attempt(
        attempt=0,
        is_playing=mocker.MagicMock(return_value=False),
        allow_recovery=True,
    )

    assert not result
    debug_sink.assert_called()


def test_module_set_debug_callback_delegates_to_default_manager(
    mocker: MockerFixture,
) -> None:
    callback = mocker.MagicMock()
    call_default = mocker.patch(
        "sonartk.sound.sound_manager._call_default_manager"
    )

    sound_manager.set_debug_callback(callback)

    call_default.assert_called_once_with("set_debug_callback", callback)


def test_module_recovery_wrappers_delegate_to_default_manager(
    mocker: MockerFixture,
) -> None:
    manager = mocker.MagicMock()
    callback = mocker.MagicMock()
    previous_player = mocker.MagicMock()
    recovered_player = mocker.MagicMock()
    manager.take_recovered_player.return_value = recovered_player
    mocker.patch.object(sound_manager, "_default_manager", manager)

    sound_manager.register_audio_recovery_callback(callback)
    sound_manager.unregister_audio_recovery_callback(callback)
    sound_manager.start_output_device_watch(
        poll_interval_seconds=0.2,
        follow_default_output=False,
        recovery_retry_count=2,
        status_callback=callback,
        status_delay_seconds=1.5,
    )
    sound_manager.stop_output_device_watch()
    result = sound_manager.take_recovered_player(previous_player)

    assert result is recovered_player
    manager.register_recovery_callback.assert_called_once_with(callback)
    manager.unregister_recovery_callback.assert_called_once_with(callback)
    manager.start_output_device_watch.assert_called_once_with(
        poll_interval_seconds=0.2,
        follow_default_output=False,
        recovery_retry_count=2,
        status_callback=callback,
        status_delay_seconds=1.5,
    )
    manager.stop_output_device_watch.assert_called_once_with()
    manager.take_recovered_player.assert_called_once_with(previous_player)


def test_schedule_music_seek_restore_handles_zero_target_and_max_attempts(
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

    schedule = mocker.patch(
        "sonartk.sound.sound_manager.pyglet.clock.schedule_interval"
    )
    cancel = mocker.patch.object(manager, "_cancel_music_seek_restore")

    manager._schedule_music_seek_restore(0.0)
    schedule.assert_not_called()

    schedule.reset_mock()
    manager._schedule_music_seek_restore(0.5, max_attempts=2)
    schedule.assert_called_once()
    restore = schedule.call_args.args[0]

    mocker.patch.object(manager, "_get_player_seek_ratio", return_value=0.0)
    restore(0.01)
    restore(0.01)
    assert cancel.call_count >= 2


def test_is_music_playback_stalled_reset_branches(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = False
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"
    manager._music_stall_elapsed_seconds = 2.0
    manager._last_music_byte_offset = 99

    assert not manager._is_music_playback_stalled(0.1)
    assert manager._music_stall_elapsed_seconds == 0.0
    assert manager._last_music_byte_offset is None


def test_is_music_playback_stalled_handles_offset_errors_and_negative_offsets(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    music_player.playing.return_value = True
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._last_music_path = "music/theme.ogg"

    mocker.patch.object(
        manager,
        "_get_player_byte_offset",
        side_effect=RuntimeError("offset failure"),
    )
    assert not manager._is_music_playback_stalled(0.1)

    mocker.patch.object(manager, "_get_player_byte_offset", return_value=-1)
    assert not manager._is_music_playback_stalled(0.1)


def test_backend_error_and_disconnect_branches(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    listener.device = object()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )

    mocker.patch.object(manager, "_is_device_pointer", return_value=True)
    mocker.patch("sonartk.sound.sound_manager.al.alGetError", return_value=1)
    assert manager._has_backend_errors()

    mocker.patch(
        "sonartk.sound.sound_manager.al.alGetError",
        side_effect=RuntimeError("al failed"),
    )
    assert not manager._has_backend_errors()

    mocker.patch(
        "sonartk.sound.sound_manager.alc.alcIsExtensionPresent",
        return_value=False,
    )
    assert not manager._is_device_disconnected()

    mocker.patch(
        "sonartk.sound.sound_manager.alc.alcIsExtensionPresent",
        return_value=True,
    )

    def _set_disconnected(
        _device: object,
        _token: int,
        _size: int,
        out_value: Any,
    ) -> None:
        out_value.value = 0

    mocker.patch(
        "sonartk.sound.sound_manager.alc.alcGetIntegerv",
        side_effect=_set_disconnected,
    )
    assert manager._is_device_disconnected()


def test_soft_reset_returns_false_when_backend_reset_raises(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    listener.device = object()
    listener.context = object()
    sound_pool = mocker.MagicMock()
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    debug = mocker.MagicMock()
    manager.set_debug_callback(debug)

    mocker.patch.object(manager, "_is_device_pointer", return_value=True)
    mocker.patch(
        "sonartk.sound.sound_manager.alc.alcResetDeviceSOFT",
        side_effect=RuntimeError("reset failed"),
    )

    assert not manager._soft_reset_output_device()
    debug.assert_called()


def test_rebuild_audio_graph_handles_teardown_failures_and_listener_fallback(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    listener.position = (1, 2, 3)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    sound_pool.destroy.side_effect = RuntimeError("sound destroy failed")
    player_pool = mocker.MagicMock()
    player_pool.destroy.side_effect = RuntimeError("player destroy failed")
    music_player = mocker.MagicMock()
    music_player.delete.side_effect = RuntimeError("delete failed")
    listener.delete.side_effect = RuntimeError("listener delete failed")
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._follow_default_output = False
    debug = mocker.MagicMock()
    manager.set_debug_callback(debug)

    new_listener = mocker.MagicMock()
    new_listener.position = (0, 0, 0)
    mocker.patch(
        "sonartk.sound.sound_manager.Listener", return_value=new_listener
    )
    mocker.patch(
        "sonartk.sound.sound_manager.SoundPool",
        return_value=mocker.MagicMock(),
    )
    mocker.patch(
        "sonartk.sound.sound_manager.PlayerPool",
        return_value=mocker.MagicMock(),
    )
    mocker.patch(
        "sonartk.sound.sound_manager.Player", return_value=mocker.MagicMock()
    )
    mocker.patch.object(
        manager, "_safe_default_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager, "_safe_current_output_name", return_value="Speakers"
    )
    mocker.patch.object(
        manager,
        "_safe_output_device_inventory_signature",
        return_value="Speakers|Headphones",
    )

    assert manager._rebuild_audio_graph()
    assert debug.call_count >= 4


def test_rebuild_audio_graph_follow_default_post_checks(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()

    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    manager._follow_default_output = True

    mocker.patch(
        "sonartk.sound.sound_manager.Listener", return_value=mocker.MagicMock()
    )
    mocker.patch(
        "sonartk.sound.sound_manager.SoundPool",
        return_value=mocker.MagicMock(),
    )
    mocker.patch(
        "sonartk.sound.sound_manager.PlayerPool",
        return_value=mocker.MagicMock(),
    )
    mocker.patch(
        "sonartk.sound.sound_manager.Player", return_value=mocker.MagicMock()
    )

    names = iter(
        ["Speakers", "", "Speakers", "Speakers", "Headphones", "Speakers"]
    )
    mocker.patch.object(
        manager,
        "_safe_default_output_name",
        side_effect=lambda: next(names),
    )
    mocker.patch.object(
        manager,
        "_safe_current_output_name",
        side_effect=lambda: next(names),
    )

    assert not manager._rebuild_audio_graph()
    assert not manager._rebuild_audio_graph()


def test_rebuild_audio_graph_returns_false_on_constructor_failure(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.cached_paths.return_value = []
    player_pool = mocker.MagicMock()
    music_player = mocker.MagicMock()
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=music_player,
    )
    debug = mocker.MagicMock()
    manager.set_debug_callback(debug)

    mocker.patch(
        "sonartk.sound.sound_manager.Listener",
        side_effect=RuntimeError("listener ctor failed"),
    )

    assert not manager._rebuild_audio_graph()
    debug.assert_called()


def test_play_music_suppresses_seek_set_errors_and_retries_once(
    mocker: MockerFixture,
) -> None:
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

    mocker.patch.object(
        manager,
        "_set_player_seek_ratio",
        side_effect=RuntimeError("seek failed"),
    )
    mocker.patch.object(
        manager,
        "_should_retry_after_recovery_attempt",
        side_effect=[True, False],
    )

    manager.play_music("music/theme.ogg", resume_seek_ratio=0.3)

    assert sound_pool.load.call_count == 2


def test_allocate_players_by_role_rejects_empty_role_name(
    mocker: MockerFixture,
) -> None:
    manager = SoundManager(
        listener=mocker.MagicMock(),
        sound_pool=mocker.MagicMock(),
        player_pool=mocker.MagicMock(),
        music_player=mocker.MagicMock(),
    )

    with pytest.raises(ValueError, match="cannot include empty names"):
        manager.allocate_players_by_role(["  "])


def test_play_sound_continue_recovery_and_exhaustion_paths(
    mocker: MockerFixture,
) -> None:
    listener = mocker.MagicMock()
    listener.position = (0, 0, 0)
    sound_pool = mocker.MagicMock()
    sound_pool.load.return_value = object()
    player_pool = mocker.MagicMock()
    player_a = mocker.MagicMock()
    player_a.queue = []
    player_b = mocker.MagicMock()
    player_b.queue = []
    player_pool.get_player.side_effect = [player_a, player_b]
    manager = SoundManager(
        listener=listener,
        sound_pool=sound_pool,
        player_pool=player_pool,
        music_player=mocker.MagicMock(),
    )

    mocker.patch.object(
        manager,
        "_should_retry_after_recovery_attempt",
        side_effect=[True, True],
    )

    result = manager.play_sound("sfx/step.wav")

    assert result is player_b
    assert player_pool.get_player.call_count == 2


def test_play_sound_skips_trigger_when_same_sound_already_playing(
    mocker: MockerFixture,
) -> None:
    sound: Any = object()
    player = mocker.MagicMock()
    player.queue = [sound]
    player.playing.return_value = True

    manager = SoundManager(
        listener=mocker.MagicMock(position=(0, 0, 0)),
        sound_pool=mocker.MagicMock(),
        player_pool=mocker.MagicMock(),
        music_player=mocker.MagicMock(),
    )
    trigger = mocker.patch.object(manager, "_trigger_play_with_device_retry")

    manager.play_sound(sound, player=player, retrigger_if_same=False)

    trigger.assert_not_called()
