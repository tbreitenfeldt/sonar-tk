from __future__ import annotations

from typing import Optional, Protocol, cast

from sonartk.sound import sound_manager
from sonartk.sound.openal_lite.openal import Player


class _SoundServiceLike(Protocol):
    def play_sound(
        self,
        sound: str,
        *,
        volume: float = 1.0,
        loop: bool = False,
        channel: str = "sfx",
    ) -> Player: ...

    def set_channel_volume(self, channel: str, volume: float) -> float: ...

    def apply_channel_volume(
        self, player: Player, channel: str, base_volume: float = 1.0
    ) -> float: ...


class ChannelLoop:
    """One looping sound on a named channel, such as an ambience bed.

    Starting a loop replaces the previous one. The loop keeps its own gain,
    so changing the channel volume while it plays rescales it correctly
    instead of overwriting the gain. The loop is relative to the listener, so
    walking never changes its distance or gain.
    """

    def __init__(
        self,
        channel: str,
        *,
        sound_service: Optional[_SoundServiceLike] = None,
    ) -> None:
        self.channel = channel
        self.sound_service = sound_service or cast(
            _SoundServiceLike, sound_manager
        )
        self.player: Optional[Player] = None
        self.gain = 1.0

    @property
    def is_playing(self) -> bool:
        """Whether a loop has been started and not stopped."""
        return self.player is not None

    def play(self, sound: str, gain: float = 1.0) -> Player:
        """Loop ``sound`` at ``gain``, replacing any current loop."""
        self.stop()
        self.gain = gain
        self.player = self.sound_service.play_sound(
            sound, volume=gain, loop=True, channel=self.channel
        )
        self.player.source_relative = True
        self.player.position = (0, 0, 0)
        return self.player

    def stop(self) -> None:
        """Stop and release the current loop, if any."""
        if self.player is not None:
            self.player.stop()
            self.player.remove()
            self.player = None
        self.gain = 1.0

    def set_volume(self, volume: float) -> float:
        """Set the channel volume and rescale the loop already playing.

        Returns the clamped channel volume.
        """
        clamped = self.sound_service.set_channel_volume(self.channel, volume)
        if self.player is not None:
            self.sound_service.apply_channel_volume(
                self.player, self.channel, self.gain
            )
        return clamped
