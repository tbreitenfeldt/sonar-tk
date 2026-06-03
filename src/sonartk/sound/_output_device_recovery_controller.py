"""Internal output-device watch and recovery orchestration helpers.

This module is intentionally private and delegates concrete backend work to a
host object (currently SoundManager) via a small protocol surface.
"""

from typing import Callable, Optional, Protocol

import pyglet.clock


class _OutputDeviceRecoveryHost(Protocol):
    """Contract required by OutputDeviceRecoveryController."""

    _device_watch_callback: Optional[Callable[[float], None]]
    _device_watch_interval_seconds: float
    _follow_default_output: bool
    _recovery_retry_count: int
    _status_callback: Optional[Callable[[str], None]]
    _status_delay_seconds: float
    _status_timer_callback: Optional[Callable[[float], None]]
    _status_announced_for_cycle: bool
    _last_known_default_device: str
    _last_known_current_device: str
    _last_known_output_inventory_signature: str
    _backend_error_streak: int
    _disconnected_streak: int
    _backend_error_recovery_threshold: int
    _disconnect_recovery_threshold: int
    _min_recovery_interval_seconds: float
    _last_recovery_attempt_time_seconds: float
    _recovery_in_progress: bool
    _recovery_callbacks: list[Callable[[], None]]

    def _safe_default_output_name(self) -> str: ...

    def _safe_current_output_name(self) -> str: ...

    def _safe_output_device_inventory_signature(self) -> str: ...

    def _has_backend_errors(self) -> bool: ...

    def _is_device_disconnected(self) -> bool: ...

    def _is_music_playback_stalled(self, delta_time: float) -> bool: ...

    def _soft_reset_output_device(self) -> bool: ...

    def _rebuild_audio_graph(self) -> bool: ...

    def _debug(self, message: str) -> None: ...

    def _monotonic_time(self) -> float: ...

    def _begin_recovery(
        self,
        retry_count: int,
        *,
        skip_soft_reset: bool = False,
    ) -> bool: ...

    def _cancel_recovery_status_timer(self) -> None: ...


class OutputDeviceRecoveryController:
    """Internal coordinator for output-device watch and recovery orchestration."""

    def __init__(self, host: _OutputDeviceRecoveryHost) -> None:
        self._host = host

    def start_output_device_watch(
        self,
        *,
        poll_interval_seconds: float = 0.5,
        follow_default_output: bool = True,
        recovery_retry_count: int = 1,
        status_callback: Optional[Callable[[str], None]] = None,
        status_delay_seconds: float = 5.0,
    ) -> None:
        """Start polling output-device health and enable automatic recovery."""
        if poll_interval_seconds <= 0:
            raise ValueError("poll_interval_seconds must be > 0")
        if recovery_retry_count < 0:
            raise ValueError("recovery_retry_count must be >= 0")
        if status_delay_seconds < 0:
            raise ValueError("status_delay_seconds must be >= 0")

        self.stop_output_device_watch()
        self._host._device_watch_interval_seconds = poll_interval_seconds
        self._host._follow_default_output = follow_default_output
        self._host._recovery_retry_count = recovery_retry_count
        self._host._status_callback = status_callback
        self._host._status_delay_seconds = status_delay_seconds
        self._host._status_announced_for_cycle = False
        self._host._last_known_default_device = (
            self._host._safe_default_output_name()
        )
        self._host._last_known_current_device = (
            self._host._safe_current_output_name()
        )
        self._host._last_known_output_inventory_signature = (
            self._host._safe_output_device_inventory_signature()
        )

        def poll(delta_time: float) -> None:
            self.poll_output_device_health(delta_time)

        self._host._device_watch_callback = poll
        pyglet.clock.schedule_interval(poll, poll_interval_seconds)
        if self._host._status_callback is not None:
            self._host._status_callback("Audio device monitoring enabled.")

    def stop_output_device_watch(self) -> None:
        """Stop polling and cancel any pending delayed recovery status prompt."""
        if self._host._device_watch_callback is not None:
            pyglet.clock.unschedule(self._host._device_watch_callback)
            self._host._device_watch_callback = None
        self.cancel_recovery_status_timer()

    def poll_output_device_health(self, delta_time: float) -> None:
        """Evaluate health signals and trigger recovery when thresholds are met."""
        if self._host._recovery_in_progress:
            return

        previous_default = self._host._last_known_default_device
        previous_current = self._host._last_known_current_device
        previous_inventory_signature = (
            self._host._last_known_output_inventory_signature
        )
        default_name = self._host._safe_default_output_name()
        current_name = self._host._safe_current_output_name()
        inventory_signature = (
            self._host._safe_output_device_inventory_signature()
        )
        default_changed = bool(
            default_name
            and previous_default
            and default_name != previous_default
        )
        current_changed = bool(
            current_name
            and previous_current
            and current_name != previous_current
        )
        inventory_changed = bool(
            inventory_signature
            and previous_inventory_signature
            and inventory_signature != previous_inventory_signature
        )

        if default_name:
            self._host._last_known_default_device = default_name
        if current_name:
            self._host._last_known_current_device = current_name
        if inventory_signature:
            self._host._last_known_output_inventory_signature = (
                inventory_signature
            )

        backend_error = self._host._has_backend_errors()
        disconnected = self._host._is_device_disconnected()
        if backend_error:
            self._host._backend_error_streak += 1
        else:
            self._host._backend_error_streak = 0

        if disconnected:
            self._host._disconnected_streak += 1
        else:
            self._host._disconnected_streak = 0

        needs_recovery = False
        force_full_recovery = False
        immediate_recovery = False
        if not current_name:
            needs_recovery = True
            immediate_recovery = True
        elif (
            self._host._follow_default_output
            and default_name
            and current_name != default_name
        ):
            needs_recovery = True
            immediate_recovery = True
        elif self._host._follow_default_output and (
            default_changed or current_changed
        ):
            needs_recovery = True
            immediate_recovery = True
        elif self._host._follow_default_output and inventory_changed:
            needs_recovery = True
            force_full_recovery = True
            immediate_recovery = True
        elif (
            self._host._backend_error_streak
            >= self._host._backend_error_recovery_threshold
            or self._host._disconnected_streak
            >= self._host._disconnect_recovery_threshold
        ):
            needs_recovery = True
        elif self._host._is_music_playback_stalled(delta_time):
            needs_recovery = True

        if not needs_recovery:
            return

        now = self._host._monotonic_time()
        if (
            not immediate_recovery
            and now - self._host._last_recovery_attempt_time_seconds
            < self._host._min_recovery_interval_seconds
        ):
            return

        self._host._last_recovery_attempt_time_seconds = now

        if force_full_recovery:
            if self._host._begin_recovery(
                self._host._recovery_retry_count,
                skip_soft_reset=True,
            ):
                self._host._backend_error_streak = 0
                self._host._disconnected_streak = 0
        else:
            if self._host._begin_recovery(self._host._recovery_retry_count):
                self._host._backend_error_streak = 0
                self._host._disconnected_streak = 0

    def start_recovery_status_timer(self) -> None:
        """Schedule delayed user-facing recovery status if recovery is slow."""
        status_callback = self._host._status_callback
        if status_callback is None or self._host._status_delay_seconds <= 0:
            return
        if self._host._status_timer_callback is not None:
            return

        self._host._status_announced_for_cycle = False

        def notify(_: float) -> None:
            self._host._status_timer_callback = None
            if (
                self._host._recovery_in_progress
                and not self._host._status_announced_for_cycle
            ):
                self._host._status_announced_for_cycle = True
                status_callback("Audio device changed. Recovering audio.")

        self._host._status_timer_callback = notify
        pyglet.clock.schedule_once(notify, self._host._status_delay_seconds)

    def cancel_recovery_status_timer(self) -> None:
        """Cancel any scheduled delayed recovery status notification."""
        if self._host._status_timer_callback is not None:
            pyglet.clock.unschedule(self._host._status_timer_callback)
            self._host._status_timer_callback = None

    def begin_recovery(
        self,
        retry_count: int,
        *,
        skip_soft_reset: bool = False,
    ) -> bool:
        """Run one recovery cycle and invoke registered callbacks on success."""
        if self._host._recovery_in_progress:
            return False

        self._host._recovery_in_progress = True
        self.start_recovery_status_timer()
        success = False

        try:
            if not skip_soft_reset and self._host._soft_reset_output_device():
                success = True

            attempts = retry_count + 1
            if not success:
                for _ in range(attempts):
                    if self._host._rebuild_audio_graph():
                        success = True
                        break

            if success:
                for callback in tuple(self._host._recovery_callbacks):
                    try:
                        callback()
                    except Exception as exc:
                        self._host._debug(
                            f"Recovery callback failed but was suppressed: {exc}"
                        )
                        continue

            return success
        finally:
            self._host._cancel_recovery_status_timer()
            self._host._status_announced_for_cycle = False
            self._host._recovery_in_progress = False
