import time
import ctypes
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Literal, cast

import pyglet.clock

from sonartk.sound.openal_lite.openal import (
    Listener,
    LoadSound,
    BufferSound,
    Player,
    al,
    alc,
)
from sonartk.sound._output_device_recovery_controller import (
    OutputDeviceRecoveryController,
)
from sonartk.sound.player_pool import PlayerPool
from sonartk.sound.sound_pool import SoundPool

DEFAULT_CHANNEL_VOLUMES: dict[str, float] = {
    "music": 1.0,
    "sfx": 1.0,
    "ui": 1.0,
    "voice": 1.0,
}

ALC_DEFAULT_ALL_DEVICES_SPECIFIER = 0x1012
ALC_ALL_DEVICES_SPECIFIER = 0x1013

PlaybackChannel = Literal["music", "sfx", "ui", "voice"]


@dataclass(frozen=True)
class PlayerRecoveryIntent:
    """Serializable playback state for restoring active players after recovery."""

    old_player_id: int
    sound_path: str
    position: tuple[int, int, int]
    volume: float
    rolloff: float
    loop: bool
    channel: PlaybackChannel


def _clamp_volume(value: float) -> float:
    return max(0.0, min(1.0, value))


class SoundManager:
    """Manage shared audio resources and playback operations."""

    def __init__(
        self,
        *,
        listener: Optional[Listener] = None,
        sound_pool: Optional[SoundPool] = None,
        player_pool: Optional[PlayerPool] = None,
        music_player: Optional[Player] = None,
    ) -> None:
        # Important that listener is initialized before any sounds.
        self.listener: Listener = listener or Listener()
        self.sound_pool: SoundPool = sound_pool or SoundPool()
        self.player_pool: PlayerPool = player_pool or PlayerPool()
        self.music_player: Player = music_player or Player()
        self._channel_volumes: dict[str, float] = dict(DEFAULT_CHANNEL_VOLUMES)
        self._music_fade_callback: Optional[Callable[[float], None]] = None
        self._music_seek_restore_callback: Optional[
            Callable[[float], None]
        ] = None
        self._last_music_path: Optional[str] = None
        self._last_music_loop: bool = True
        self._last_music_volume: float = 1.0
        self._last_music_seek_ratio: float = 0.0
        self._music_target_playing: bool = False
        self._device_watch_callback: Optional[Callable[[float], None]] = None
        self._device_watch_interval_seconds: float = 0.5
        self._follow_default_output: bool = True
        self._recovery_retry_count: int = 1
        self._recovery_in_progress: bool = False
        self._recovery_callbacks: list[Callable[[], None]] = []
        self._status_callback: Optional[Callable[[str], None]] = None
        self._status_delay_seconds: float = 5.0
        self._status_timer_callback: Optional[Callable[[float], None]] = None
        self._status_announced_for_cycle: bool = False
        self._last_known_default_device: str = ""
        self._last_known_current_device: str = ""
        self._last_known_output_inventory_signature: str = ""
        self._backend_error_streak: int = 0
        self._disconnected_streak: int = 0
        self._backend_error_recovery_threshold: int = 2
        self._disconnect_recovery_threshold: int = 2
        self._min_recovery_interval_seconds: float = 1.0
        self._last_recovery_attempt_time_seconds: float = 0.0
        self._music_stall_threshold_seconds: float = 1.5
        self._music_stall_elapsed_seconds: float = 0.0
        self._last_music_byte_offset: Optional[int] = None
        self._player_channels_by_id: dict[int, PlaybackChannel] = {}
        self._last_recovered_player_map: dict[int, Player] = {}
        self._debug_callback: Optional[Callable[[str], None]] = None
        self._recovery_controller = OutputDeviceRecoveryController(self)

    def set_debug_callback(
        self,
        callback: Optional[Callable[[str], None]],
    ) -> None:
        """Set optional debug sink used for non-fatal recovery diagnostics."""
        self._debug_callback = callback

    def _debug(self, message: str) -> None:
        if self._debug_callback is not None:
            self._debug_callback(message)

    def _monotonic_time(self) -> float:
        return time.monotonic()

    @staticmethod
    def _get_player_seek_ratio(player: Player) -> float:
        return float(cast(Any, player).seek)

    @staticmethod
    def _set_player_seek_ratio(player: Player, ratio: float) -> None:
        setattr(player, "seek", ratio)

    def register_recovery_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback invoked after successful audio recovery."""
        if callback not in self._recovery_callbacks:
            self._recovery_callbacks.append(callback)

    def unregister_recovery_callback(
        self, callback: Callable[[], None]
    ) -> None:
        """Unregister a previously registered recovery callback."""
        if callback in self._recovery_callbacks:
            self._recovery_callbacks.remove(callback)

    def start_output_device_watch(
        self,
        *,
        poll_interval_seconds: float = 0.5,
        follow_default_output: bool = True,
        recovery_retry_count: int = 1,
        status_callback: Optional[Callable[[str], None]] = None,
        status_delay_seconds: float = 5.0,
    ) -> None:
        """Watch for output-device disruptions and recover audio automatically."""
        self._recovery_controller.start_output_device_watch(
            poll_interval_seconds=poll_interval_seconds,
            follow_default_output=follow_default_output,
            recovery_retry_count=recovery_retry_count,
            status_callback=status_callback,
            status_delay_seconds=status_delay_seconds,
        )

    def stop_output_device_watch(self) -> None:
        """Stop monitoring output device changes."""
        self._recovery_controller.stop_output_device_watch()

    def recover_output_device(self) -> bool:
        """Attempt recovery once using configured retry policy."""
        return self._begin_recovery(self._recovery_retry_count)

    def take_recovered_player(
        self, previous_player: Player
    ) -> Optional[Player]:
        """Return and consume the recovered replacement for a previous player."""
        return self._last_recovered_player_map.pop(id(previous_player), None)

    def _iter_active_players(self) -> tuple[Player, ...]:
        active_players = getattr(self.player_pool, "_active_players", None)
        if isinstance(active_players, list):
            return tuple(active_players)
        return tuple()

    def _resolve_cached_sound_path_for_player(
        self, player: Player
    ) -> Optional[str]:
        queue = getattr(player, "queue", None)
        if not queue:
            return None

        queued_sound = queue[0]
        for path, cached_sound in self.sound_pool.pool.items():
            if cached_sound is queued_sound:
                return path
        return None

    def _derive_local_volume(
        self,
        effective_volume: float,
        channel: PlaybackChannel,
    ) -> float:
        channel_volume = self._channel_volumes.get(channel, 1.0)
        if channel_volume <= 0.0:
            return 0.0
        return _clamp_volume(effective_volume / channel_volume)

    def _snapshot_active_player_recovery_states(
        self,
    ) -> list[PlayerRecoveryIntent]:
        snapshots: list[PlayerRecoveryIntent] = []

        for player in self._iter_active_players():
            try:
                if not player.playing():
                    continue

                sound_path = self._resolve_cached_sound_path_for_player(player)
                if sound_path is None:
                    continue

                channel = self._player_channels_by_id.get(id(player), "sfx")
                snapshots.append(
                    PlayerRecoveryIntent(
                        old_player_id=id(player),
                        sound_path=sound_path,
                        position=tuple(player.position),
                        volume=self._derive_local_volume(
                            float(player.volume),
                            channel,
                        ),
                        rolloff=float(player.rolloff),
                        loop=bool(player.loop),
                        channel=channel,
                    )
                )
            except Exception as exc:
                self._debug(f"Failed to snapshot active player state: {exc}")
                continue

        return snapshots

    def _restore_active_player_recovery_states(
        self,
        snapshots: list[PlayerRecoveryIntent],
    ) -> None:
        self._last_recovered_player_map.clear()

        for snapshot in snapshots:
            try:
                recovered_player = self.player_pool.get_player()
                self.play_sound(
                    snapshot.sound_path,
                    player=recovered_player,
                    position=snapshot.position,
                    volume=snapshot.volume,
                    channel=snapshot.channel,
                    rolloff=snapshot.rolloff,
                    loop=snapshot.loop,
                    retrigger_if_same=True,
                )
                self._last_recovered_player_map[snapshot.old_player_id] = (
                    recovered_player
                )
            except Exception as exc:
                self._debug(
                    f"Failed to restore active player state for '{snapshot.sound_path}': {exc}"
                )
                continue

    def _safe_default_output_name(self) -> str:
        default_all = self._read_device_name(
            None,
            ALC_DEFAULT_ALL_DEVICES_SPECIFIER,
        )
        if default_all:
            return default_all
        return self._read_device_name(None, alc.ALC_DEFAULT_DEVICE_SPECIFIER)

    def _safe_current_output_name(self) -> str:
        current_all = self._read_device_name(
            self.listener.device,
            ALC_ALL_DEVICES_SPECIFIER,
        )
        if current_all:
            return current_all
        return self._read_device_name(
            self.listener.device, alc.ALC_DEVICE_SPECIFIER
        )

    def _safe_output_device_inventory_signature(self) -> str:
        return "|".join(self._read_device_inventory())

    def _read_device_inventory(self) -> list[str]:
        """Read the playback device inventory from OpenAL multi-string data."""
        devices_all = self._read_device_multistring(ALC_ALL_DEVICES_SPECIFIER)
        if devices_all:
            return devices_all
        return self._read_device_multistring(alc.ALC_DEVICE_SPECIFIER)

    @staticmethod
    def _read_device_multistring(query: int) -> list[str]:
        try:
            raw = alc.alcGetString(None, query)
            if raw is None:
                return []

            pointer = ctypes.cast(raw, ctypes.POINTER(ctypes.c_ubyte))
            devices: list[str] = []
            token = bytearray()

            for index in range(16384):
                value = pointer[index]
                if value == 0:
                    if not token:
                        break
                    devices.append(token.decode("utf-8", errors="ignore"))
                    token.clear()
                    continue
                token.append(value)

            if token:
                devices.append(token.decode("utf-8", errors="ignore"))

            return [name for name in devices if name]
        except Exception:
            return []

    @staticmethod
    def _read_device_name(device: object, query: int) -> str:
        """Read an OpenAL device name and decode to Python string."""
        try:
            raw = alc.alcGetString(device, query)
            if raw is None:
                return ""
            decoded = ctypes.cast(raw, ctypes.c_char_p).value
            if decoded is None:
                return ""
            return decoded.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    @staticmethod
    def _normalize_device_name(name: str) -> str:
        return name.strip().split("\x00", 1)[0]

    def _poll_output_device_health(self, delta_time: float) -> None:
        self._recovery_controller.poll_output_device_health(delta_time)

    @staticmethod
    def _clamp_seek_ratio(value: float) -> float:
        return max(0.0, min(1.0, value))

    def _capture_music_seek_ratio(self) -> float:
        """Capture current music progress as a normalized [0, 1] seek ratio."""
        if self._last_music_path is None:
            self._last_music_seek_ratio = 0.0
            return 0.0

        ratio: Optional[float] = None

        # Prefer byte-offset capture because some backends report seek=1.0
        # transiently during endpoint transitions.
        try:
            queue = self.music_player.queue
            if queue:
                length = float(getattr(queue[0], "length", 0))
                if length > 0:
                    offset = max(
                        self._get_player_byte_offset(self.music_player), 0
                    )
                    ratio = self._clamp_seek_ratio(offset / length)
        except Exception:
            ratio = None

        if ratio is None:
            try:
                ratio = self._clamp_seek_ratio(
                    self._get_player_seek_ratio(self.music_player)
                )
            except Exception:
                ratio = None

        if ratio is None:
            return self._last_music_seek_ratio

        is_playing = False
        try:
            is_playing = bool(self.music_player.playing())
        except Exception:
            is_playing = False

        # Guard against transient zero seek reads when output drops while
        # music is expected to keep playing.
        if (
            ratio <= 0.001
            and 0.0 < self._last_music_seek_ratio < 0.999
            and self._music_target_playing
            and not is_playing
        ):
            return self._last_music_seek_ratio

        # Guard against flaky full-scale reads while previous ratio is meaningful.
        if ratio >= 0.999 and 0.0 < self._last_music_seek_ratio < 0.999:
            return self._last_music_seek_ratio

        self._last_music_seek_ratio = ratio
        return ratio

    def _cancel_music_seek_restore(self) -> None:
        if self._music_seek_restore_callback is not None:
            pyglet.clock.unschedule(self._music_seek_restore_callback)
            self._music_seek_restore_callback = None

    def _schedule_music_seek_restore(
        self,
        target_ratio: float,
        *,
        step_seconds: float = 0.05,
        max_attempts: int = 20,
    ) -> None:
        target = self._clamp_seek_ratio(target_ratio)
        if target <= 0.0:
            return

        self._cancel_music_seek_restore()
        attempts = 0

        def restore(_: float) -> None:
            nonlocal attempts
            attempts += 1

            try:
                self._set_player_seek_ratio(self.music_player, target)
            except Exception:
                pass

            current: Optional[float] = None
            try:
                current = self._clamp_seek_ratio(
                    self._get_player_seek_ratio(self.music_player)
                )
            except Exception:
                current = None

            if current is not None and abs(current - target) <= 0.01:
                self._last_music_seek_ratio = target
                self._cancel_music_seek_restore()
                return

            if attempts >= max_attempts:
                self._cancel_music_seek_restore()

        self._music_seek_restore_callback = restore
        pyglet.clock.schedule_interval(restore, step_seconds)

    def _is_music_playback_stalled(self, delta_time: float) -> bool:
        """Detect stalled music playback when state is PLAYING but offset does not advance."""
        if self._last_music_path is None:
            self._music_stall_elapsed_seconds = 0.0
            self._last_music_byte_offset = None
            return False

        try:
            if not self.music_player.playing():
                self._music_stall_elapsed_seconds = 0.0
                self._last_music_byte_offset = None
                return False

            offset = self._get_player_byte_offset(self.music_player)
        except Exception:
            self._music_stall_elapsed_seconds = 0.0
            self._last_music_byte_offset = None
            return False

        if offset < 0:
            self._music_stall_elapsed_seconds = 0.0
            self._last_music_byte_offset = None
            return False

        self._update_last_music_seek_ratio_from_offset(offset)

        if self._last_music_byte_offset is None:
            self._last_music_byte_offset = offset
            self._music_stall_elapsed_seconds = 0.0
            return False

        if offset != self._last_music_byte_offset:
            self._last_music_byte_offset = offset
            self._music_stall_elapsed_seconds = 0.0
            return False

        self._music_stall_elapsed_seconds += max(delta_time, 0.0)
        return (
            self._music_stall_elapsed_seconds
            >= self._music_stall_threshold_seconds
        )

    @staticmethod
    def _get_player_byte_offset(player: Player) -> int:
        value = al.ALint(0)
        al.alGetSourcei(player.source, al.AL_BYTE_OFFSET, value)
        return int(value.value)

    def _update_last_music_seek_ratio_from_offset(self, offset: int) -> None:
        """Persist music progress from byte offset while playback is healthy."""
        if offset < 0:
            return

        try:
            queue = self.music_player.queue
            if not queue:
                return

            length = float(getattr(queue[0], "length", 0))
            if length <= 0:
                return

            self._last_music_seek_ratio = self._clamp_seek_ratio(
                offset / length
            )
        except Exception:
            return

    @staticmethod
    def _is_device_pointer(value: object) -> bool:
        return isinstance(value, ctypes._Pointer)

    def _has_backend_errors(self) -> bool:
        """Check OpenAL/ALC error state for signs of broken playback backend."""
        try:
            al_error = al.alGetError()
            if al_error != al.AL_NO_ERROR:
                return True
        except Exception:
            return False

        device = self.listener.device
        if not self._is_device_pointer(device):
            return False

        try:
            alc_error = alc.alcGetError(device)
            return bool(alc_error != alc.ALC_NO_ERROR)
        except Exception:
            return False

    def _is_device_disconnected(self) -> bool:
        """Probe ALC_EXT_disconnect when available to detect unplug events."""
        device = self.listener.device
        if not self._is_device_pointer(device):
            return False

        try:
            ext_name = ctypes.c_char_p(b"ALC_EXT_disconnect")
            supported = bool(alc.alcIsExtensionPresent(device, ext_name))
            if not supported:
                return False

            connected = alc.ALCint(1)
            alc.alcGetIntegerv(device, 0x313, 1, connected)
            return int(connected.value) == 0
        except Exception:
            return False

    def _start_recovery_status_timer(self) -> None:
        self._recovery_controller.start_recovery_status_timer()

    def _cancel_recovery_status_timer(self) -> None:
        self._recovery_controller.cancel_recovery_status_timer()

    def _begin_recovery(
        self,
        retry_count: int,
        *,
        skip_soft_reset: bool = False,
    ) -> bool:
        return self._recovery_controller.begin_recovery(
            retry_count,
            skip_soft_reset=skip_soft_reset,
        )

    def _soft_reset_output_device(self) -> bool:
        """Try to reset the current output device without rebuilding players."""
        device = self.listener.device
        if not self._is_device_pointer(device):
            return False

        music_should_be_playing = (
            self._music_target_playing and self._last_music_path is not None
        )
        music_seek_ratio = self._capture_music_seek_ratio()

        try:
            alc.alcResetDeviceSOFT(device, None)
            alc.alcProcessContext(self.listener.context)
        except Exception as exc:
            self._debug(
                f"Soft reset failed while resetting OpenAL device: {exc}"
            )
            return False

        if self._has_backend_errors():
            return False

        default_name = self._safe_default_output_name()
        current_name = self._safe_current_output_name()

        if self._follow_default_output:
            # If route data is incomplete or still mismatched, force full rebuild.
            if not default_name or not current_name:
                return False
            if current_name != default_name:
                return False

        if (
            music_should_be_playing
            and self._last_music_path is not None
            and not self.music_player.playing()
        ):
            self.play_music(
                self._last_music_path,
                loop=self._last_music_loop,
                volume=self._last_music_volume,
                fade_in_seconds=0.0,
                resume_seek_ratio=music_seek_ratio,
            )

        self._last_known_default_device = default_name
        self._last_known_current_device = current_name
        self._last_known_output_inventory_signature = (
            self._safe_output_device_inventory_signature()
        )
        return True

    def _rebuild_audio_graph(self) -> bool:  # noqa: C901
        recovered_snapshots = self._snapshot_active_player_recovery_states()
        cached_paths = list(self.sound_pool.cached_paths())
        cached_channel_volumes = dict(self._channel_volumes)
        last_music_path = self._last_music_path
        last_music_loop = self._last_music_loop
        last_music_volume = self._last_music_volume
        last_music_seek_ratio = self._capture_music_seek_ratio()
        resume_music = (
            last_music_path is not None and self._music_target_playing
        )
        previous_listener_position = tuple(self.listener.position)

        self._cancel_recovery_status_timer()
        self._cancel_music_seek_restore()
        if self._music_fade_callback is not None:
            pyglet.clock.unschedule(self._music_fade_callback)
            self._music_fade_callback = None

        try:
            self.sound_pool.destroy()
        except Exception as exc:
            self._debug(f"Failed to destroy sound pool during recovery: {exc}")
            pass

        try:
            self.player_pool.destroy()
        except Exception as exc:
            self._debug(
                f"Failed to destroy player pool during recovery: {exc}"
            )
            pass

        try:
            self.music_player.delete()
        except Exception as exc:
            self._debug(
                f"Failed to delete music player during recovery: {exc}"
            )
            pass

        try:
            self.listener.delete()
        except Exception as exc:
            self._debug(f"Failed to delete listener during recovery: {exc}")
            pass

        try:
            default_name = self._safe_default_output_name()
            listener_device_name = ""
            if self._follow_default_output and default_name:
                listener_device_name = self._normalize_device_name(
                    default_name
                )

            if listener_device_name:
                self.listener = Listener(listener_device_name)
            else:
                self.listener = Listener()
            self.sound_pool = SoundPool()
            self.player_pool = PlayerPool()
            self.music_player = Player()
            self._channel_volumes = cached_channel_volumes
            self.listener.position = previous_listener_position

            if cached_paths:
                self.sound_pool.load_many(cached_paths)

            if recovered_snapshots:
                self._restore_active_player_recovery_states(
                    recovered_snapshots
                )

            if resume_music and last_music_path is not None:
                self.play_music(
                    last_music_path,
                    loop=last_music_loop,
                    volume=last_music_volume,
                    fade_in_seconds=0.0,
                    resume_seek_ratio=last_music_seek_ratio,
                )

            default_name = self._safe_default_output_name()
            current_name = self._safe_current_output_name()

            if self._follow_default_output:
                if not default_name or not current_name:
                    return False
                if current_name != default_name:
                    return False

            self._last_known_default_device = default_name
            self._last_known_current_device = current_name
            self._last_known_output_inventory_signature = (
                self._safe_output_device_inventory_signature()
            )

            # Keep module-level globals aligned so wrapper-level sync does not
            # restore stale pre-recovery resources.
            global listener
            global sound_pool
            global player_pool
            global music_player
            listener = self.listener
            sound_pool = self.sound_pool
            player_pool = self.player_pool
            music_player = self.music_player
            return True
        except Exception as exc:
            self._debug(f"Audio graph rebuild failed: {exc}")
            self._last_recovered_player_map.clear()
            return False

    def _trigger_play_with_device_retry(
        self,
        trigger: Callable[[], None],
        is_playing: Callable[[], bool],
    ) -> None:
        trigger()
        if self._device_watch_callback is not None and not is_playing():
            # Give backend one immediate retry before recovery.
            trigger()

    def _should_retry_after_recovery_attempt(
        self,
        *,
        attempt: int,
        is_playing: Callable[[], bool],
        allow_recovery: bool,
    ) -> bool:
        if not allow_recovery:
            return False
        if attempt != 0:
            return False
        if self._device_watch_callback is None:
            return False
        if is_playing():
            return False
        recovered = self._begin_recovery(self._recovery_retry_count)
        if not recovered:
            self._debug(
                "Playback trigger failed and recovery attempt did not succeed."
            )
        return recovered

    def play_music(
        self,
        path: str,
        loop: bool = True,
        volume: float = 1.0,
        fade_in_seconds: float = 0.0,
        fade_step_seconds: float = 0.05,
        resume_seek_ratio: Optional[float] = None,
    ) -> None:
        """Load and play background music.

        Any currently playing music is stopped and replaced.
        """
        if fade_in_seconds < 0:
            raise ValueError("fade_in_seconds must be >= 0")
        if fade_in_seconds > 0 and fade_step_seconds <= 0:
            raise ValueError("fade_step_seconds must be > 0")

        for attempt in range(2):
            self._cancel_music_seek_restore()
            if self.music_player.playing():
                self.music_player.stop()
                self.music_player.remove()

            self._last_music_path = path
            self._last_music_loop = loop
            self._last_music_volume = volume
            if resume_seek_ratio is None:
                self._last_music_seek_ratio = 0.0
            else:
                self._last_music_seek_ratio = self._clamp_seek_ratio(
                    resume_seek_ratio
                )
            self._music_target_playing = True
            self.music_player.add(self.sound_pool.load(path))
            self.music_player.loop = loop
            target_volume = self._effective_volume(volume, "music")

            if self._music_fade_callback is not None:
                pyglet.clock.unschedule(self._music_fade_callback)
                self._music_fade_callback = None

            if fade_in_seconds > 0:
                self.music_player.volume = 0.0
                self._schedule_music_fade(
                    target_volume,
                    duration_seconds=fade_in_seconds,
                    step_seconds=fade_step_seconds,
                )
            else:
                self.music_player.volume = target_volume

            self._trigger_play_with_device_retry(
                self.music_player.play,
                self.music_player.playing,
            )

            if self._last_music_seek_ratio > 0.0:
                try:
                    self._set_player_seek_ratio(
                        self.music_player,
                        self._last_music_seek_ratio,
                    )
                except Exception:
                    pass
                self._schedule_music_seek_restore(self._last_music_seek_ratio)

            if self._should_retry_after_recovery_attempt(
                attempt=attempt,
                is_playing=self.music_player.playing,
                allow_recovery=True,
            ):
                continue

            break

    def pause_music(self) -> None:
        """Pause the currently playing music track."""
        self._capture_music_seek_ratio()
        self._music_target_playing = False
        self.music_player.pause()

    def resume_music(self) -> None:
        """Resume playback of the paused music track."""
        self._music_target_playing = True
        self.music_player.play()

    def stop_music(self) -> None:
        """Stop playback of the current music track."""
        self._cancel_music_seek_restore()
        self._music_target_playing = False
        self._last_music_seek_ratio = 0.0
        self.music_player.stop()

    def preload_sounds(
        self, paths: Iterable[str]
    ) -> dict[str, LoadSound | BufferSound]:
        """Preload multiple sounds into the shared sound pool cache."""
        return self.sound_pool.load_many(paths)

    def allocate_players_by_role(
        self, role_names: Iterable[str]
    ) -> dict[str, Player]:
        """Allocate and return players keyed by caller-provided role names."""
        players: dict[str, Player] = {}
        for role_name in role_names:
            normalized = role_name.strip()
            if normalized == "":
                raise ValueError("role_names cannot include empty names")
            if normalized in players:
                raise ValueError(f"Duplicate role name: '{normalized}'")
            players[normalized] = self.player_pool.get_player()
        return players

    def play_sound(  # noqa: C901
        self,
        sound: str | LoadSound | BufferSound,
        player: Optional[Player] = None,
        position: Optional[tuple[int, int, int]] = None,
        volume: float = 1.0,
        channel: PlaybackChannel = "sfx",
        rolloff: float = 0.01,
        loop: bool = False,
        effects: Optional[list[Any]] = None,
        filters: Optional[list[Any]] = None,
        wait_until_finished: bool = False,
        poll_interval_seconds: float = 0.01,
        on_complete: Optional[Callable[[Player], None]] = None,
        completion_poll_interval_seconds: float = 0.01,
        retrigger_if_same: bool = True,
    ) -> Player:
        """Play a sound effect.

        Supports optional player reuse, positional audio, effects, and filters.

        If wait_until_finished is enabled, this call blocks until playback ends.
        Avoid this on the UI thread to prevent freezing input.

        If on_complete is provided, completion is detected non-blockingly via
        pyglet clock polling and callback invocation when playback stops.
        """
        if effects is None:
            effects = []
        if filters is None:
            filters = []
        if wait_until_finished and poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        if on_complete is not None and completion_poll_interval_seconds <= 0:
            raise ValueError("completion_poll_interval_seconds must be > 0")

        requested_sound = sound
        requested_player = player
        active_player: Optional[Player] = None

        for attempt in range(2):
            active_sound = requested_sound
            active_player = requested_player if attempt == 0 else None

            if isinstance(active_sound, str):
                active_sound = self.sound_pool.load(active_sound)
            if active_player is None:
                active_player = self.player_pool.get_player()
            if position is None:
                active_position = self.listener.position
            else:
                active_position = position

            queue_was_replaced = False
            if active_sound not in active_player.queue:
                active_player.stop()
                active_player.remove()
                active_player.add(active_sound)
                queue_was_replaced = True

            if effects:
                for effect in effects:
                    active_player.add_effect(effect)
            if filters:
                for filter in filters:
                    active_player.add_filter(filter)

            active_player.loop = loop
            active_player.rolloff = rolloff
            active_player.position = active_position
            active_player.volume = self._effective_volume(volume, channel)
            should_trigger = (
                queue_was_replaced
                or retrigger_if_same
                or not active_player.playing()
            )
            if should_trigger:
                self._trigger_play_with_device_retry(
                    active_player.play,
                    active_player.playing,
                )

            if (
                should_trigger
                and isinstance(requested_sound, str)
                and self._should_retry_after_recovery_attempt(
                    attempt=attempt,
                    is_playing=active_player.playing,
                    allow_recovery=True,
                )
            ):
                requested_player = None
                continue

            if wait_until_finished:
                while active_player.playing():
                    time.sleep(poll_interval_seconds)

            if on_complete is not None:
                self._schedule_on_complete(
                    active_player,
                    on_complete,
                    completion_poll_interval_seconds,
                )

            self._player_channels_by_id[id(active_player)] = channel

            return active_player

        return (
            active_player
            if active_player is not None
            else self.player_pool.get_player()
        )

    def _schedule_on_complete(
        self,
        player: Player,
        callback: Callable[[Player], None],
        poll_interval_seconds: float,
    ) -> None:
        """Run callback once when the provided player is no longer playing."""

        def poll(_: float) -> None:
            if player.playing():
                return

            pyglet.clock.unschedule(poll)
            callback(player)

        pyglet.clock.schedule_interval(poll, poll_interval_seconds)

    def get_channel_volume(self, channel: str) -> float:
        """Return the current volume scalar for a named channel."""
        return self._channel_volumes[self._validate_channel(channel)]

    def set_channel_volume(self, channel: str, volume: float) -> float:
        """Set and return the clamped volume scalar for a named channel."""
        key = self._validate_channel(channel)
        clamped = _clamp_volume(volume)
        self._channel_volumes[key] = clamped
        return clamped

    def set_music_volume(
        self,
        volume: float,
        fade_seconds: float = 0.0,
        fade_step_seconds: float = 0.05,
    ) -> float:
        """Set music channel volume and optionally fade currently playing music."""
        if fade_seconds < 0:
            raise ValueError("fade_seconds must be >= 0")
        if fade_seconds > 0 and fade_step_seconds <= 0:
            raise ValueError("fade_step_seconds must be > 0")

        target = self.set_channel_volume("music", volume)

        if self._music_fade_callback is not None:
            pyglet.clock.unschedule(self._music_fade_callback)
            self._music_fade_callback = None

        if fade_seconds > 0:
            self._schedule_music_fade(
                target,
                duration_seconds=fade_seconds,
                step_seconds=fade_step_seconds,
            )
        else:
            self.music_player.volume = target

        return target

    def set_sfx_volume(
        self,
        volume: float,
        players: Optional[list[Player]] = None,
    ) -> float:
        """Set sfx channel volume and optionally apply it to active players."""
        target = self.set_channel_volume("sfx", volume)
        if players:
            for player in players:
                self.apply_sfx_volume(player)
        return target

    def apply_sfx_volume(
        self, player: Player, base_volume: float = 1.0
    ) -> None:
        """Apply effective sfx volume to a player using an optional base volume."""
        player.volume = self._effective_volume(base_volume, "sfx")

    def _effective_volume(self, local_volume: float, channel: str) -> float:
        key = self._validate_channel(channel)
        return _clamp_volume(
            _clamp_volume(local_volume) * self._channel_volumes[key]
        )

    def _validate_channel(self, channel: str) -> str:
        if channel not in self._channel_volumes:
            raise ValueError(
                f"Unknown channel '{channel}'. Expected one of {list(self._channel_volumes.keys())}."
            )
        return channel

    def _schedule_music_fade(
        self,
        target_volume: float,
        *,
        duration_seconds: float,
        step_seconds: float,
    ) -> None:
        elapsed = 0.0
        start_volume = self.music_player.volume

        def fade_step(delta_time: float) -> None:
            nonlocal elapsed
            elapsed += delta_time
            if duration_seconds <= 0:
                progress = 1.0
            else:
                progress = min(elapsed / duration_seconds, 1.0)
            self.music_player.volume = _clamp_volume(
                start_volume + (target_volume - start_volume) * progress
            )
            if progress >= 1.0:
                pyglet.clock.unschedule(fade_step)
                if self._music_fade_callback is fade_step:
                    self._music_fade_callback = None

        self._music_fade_callback = fade_step
        pyglet.clock.schedule_interval(fade_step, step_seconds)

    def cleanup(self) -> None:
        """Release all shared audio resources managed by the sound subsystem."""
        self.stop_output_device_watch()
        self._cancel_music_seek_restore()
        if self._music_fade_callback is not None:
            pyglet.clock.unschedule(self._music_fade_callback)
            self._music_fade_callback = None
        self._music_stall_elapsed_seconds = 0.0
        self._last_music_byte_offset = None
        self._player_channels_by_id.clear()
        self._last_recovered_player_map.clear()
        self.sound_pool.destroy()
        self.player_pool.destroy()
        self.listener.delete()
        self.music_player.delete()


_default_manager = SoundManager()

# Backward-compatible module-level shared resources.
listener: Listener = _default_manager.listener
sound_pool: SoundPool = _default_manager.sound_pool
player_pool: PlayerPool = _default_manager.player_pool
music_player: Player = _default_manager.music_player


def _sync_default_manager_from_module() -> None:
    """Keep the default manager aligned with module-level globals."""
    _default_manager.listener = listener
    _default_manager.sound_pool = sound_pool
    _default_manager.player_pool = player_pool
    _default_manager.music_player = music_player


def _call_default_manager(method_name: str, *args: Any, **kwargs: Any) -> Any:
    _sync_default_manager_from_module()
    method = cast(Callable[..., Any], getattr(_default_manager, method_name))
    return method(*args, **kwargs)


def play_music(
    path: str,
    loop: bool = True,
    volume: float = 1.0,
    fade_in_seconds: float = 0.0,
    fade_step_seconds: float = 0.05,
) -> None:
    """Load and play background music."""
    _call_default_manager(
        "play_music",
        path,
        loop=loop,
        volume=volume,
        fade_in_seconds=fade_in_seconds,
        fade_step_seconds=fade_step_seconds,
    )


def pause_music() -> None:
    """Pause the currently playing music track."""
    _call_default_manager("pause_music")


def resume_music() -> None:
    """Resume playback of the paused music track."""
    _call_default_manager("resume_music")


def stop_music() -> None:
    """Stop playback of the current music track."""
    _call_default_manager("stop_music")


def play_sound(
    sound: str | LoadSound | BufferSound,
    player: Optional[Player] = None,
    position: Optional[tuple[int, int, int]] = None,
    volume: float = 1.0,
    channel: PlaybackChannel = "sfx",
    rolloff: float = 0.01,
    loop: bool = False,
    effects: Optional[list[Any]] = None,
    filters: Optional[list[Any]] = None,
    wait_until_finished: bool = False,
    poll_interval_seconds: float = 0.01,
    on_complete: Optional[Callable[[Player], None]] = None,
    completion_poll_interval_seconds: float = 0.01,
    retrigger_if_same: bool = True,
) -> Player:
    """Play a sound effect."""
    return cast(
        Player,
        _call_default_manager(
            "play_sound",
            sound=sound,
            player=player,
            position=position,
            volume=volume,
            channel=channel,
            rolloff=rolloff,
            loop=loop,
            effects=effects,
            filters=filters,
            wait_until_finished=wait_until_finished,
            poll_interval_seconds=poll_interval_seconds,
            on_complete=on_complete,
            completion_poll_interval_seconds=completion_poll_interval_seconds,
            retrigger_if_same=retrigger_if_same,
        ),
    )


def preload_sounds(paths: Iterable[str]) -> dict[str, LoadSound | BufferSound]:
    """Preload multiple sounds into the shared module-level sound pool."""
    return cast(
        dict[str, LoadSound | BufferSound],
        _call_default_manager("preload_sounds", paths),
    )


def allocate_players_by_role(role_names: Iterable[str]) -> dict[str, Player]:
    """Allocate named players from the shared module-level player pool."""
    return cast(
        dict[str, Player],
        _call_default_manager("allocate_players_by_role", role_names),
    )


def clamp_volume(value: float) -> float:
    """Clamp a volume scalar to the supported [0.0, 1.0] range."""
    return _clamp_volume(value)


def get_channel_volume(channel: str) -> float:
    """Return the active volume for a named channel."""
    return cast(float, _call_default_manager("get_channel_volume", channel))


def set_channel_volume(channel: str, volume: float) -> float:
    """Set a named channel volume and return the clamped result."""
    return cast(
        float,
        _call_default_manager("set_channel_volume", channel, volume),
    )


def set_music_volume(
    volume: float,
    fade_seconds: float = 0.0,
    fade_step_seconds: float = 0.05,
) -> float:
    """Set music volume and optionally fade currently playing music."""
    return cast(
        float,
        _call_default_manager(
            "set_music_volume",
            volume,
            fade_seconds=fade_seconds,
            fade_step_seconds=fade_step_seconds,
        ),
    )


def set_sfx_volume(
    volume: float,
    players: Optional[list[Player]] = None,
) -> float:
    """Set sfx volume and optionally apply it to supplied players."""
    return cast(
        float,
        _call_default_manager("set_sfx_volume", volume, players=players),
    )


def apply_sfx_volume(player: Player, base_volume: float = 1.0) -> None:
    """Apply effective sfx volume to a player."""
    _call_default_manager("apply_sfx_volume", player, base_volume=base_volume)


def cleanup() -> None:
    """Release all shared audio resources managed by the sound subsystem."""
    _call_default_manager("cleanup")


def register_audio_recovery_callback(callback: Callable[[], None]) -> None:
    """Register callback invoked after successful automatic audio recovery."""
    _call_default_manager("register_recovery_callback", callback)


def unregister_audio_recovery_callback(callback: Callable[[], None]) -> None:
    """Unregister a callback used for automatic audio recovery notifications."""
    _call_default_manager("unregister_recovery_callback", callback)


def start_output_device_watch(
    *,
    poll_interval_seconds: float = 0.5,
    follow_default_output: bool = True,
    recovery_retry_count: int = 1,
    status_callback: Optional[Callable[[str], None]] = None,
    status_delay_seconds: float = 5.0,
) -> None:
    """Start automatic output-device disruption detection and recovery."""
    _call_default_manager(
        "start_output_device_watch",
        poll_interval_seconds=poll_interval_seconds,
        follow_default_output=follow_default_output,
        recovery_retry_count=recovery_retry_count,
        status_callback=status_callback,
        status_delay_seconds=status_delay_seconds,
    )


def stop_output_device_watch() -> None:
    """Stop automatic output-device disruption detection and recovery."""
    _call_default_manager("stop_output_device_watch")


def take_recovered_player(previous_player: Player) -> Optional[Player]:
    """Return recovered replacement for a previous player after device recovery."""
    return cast(
        Optional[Player],
        _call_default_manager("take_recovered_player", previous_player),
    )


def set_debug_callback(
    callback: Optional[Callable[[str], None]],
) -> None:
    """Set optional debug sink for non-fatal audio/recovery diagnostics."""
    _call_default_manager("set_debug_callback", callback)
