from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from sonartk.ui.window import Window
from sonartk.util import speech_manager

DEFAULT_LEVEL_STEPS = 10


@dataclass
class ChannelVolume:
    """A player-adjustable volume for one channel, set in whole steps.

    The level runs from 0 to ``steps``. The engine volume is the level's
    share of ``ceiling``, so even the top level can stay below full scale
    and leave headroom for screen reader speech, which the game cannot mix
    down.

    Attributes:
        label: Name spoken when the volume changes.
        ceiling: Engine volume at the top level.
        apply_to_engine: Receives the engine volume whenever it changes.
        level: Current step.
        steps: Number of steps from silent to the ceiling.
    """

    label: str
    ceiling: float
    apply_to_engine: Callable[[float], object]
    level: int = 7
    steps: int = DEFAULT_LEVEL_STEPS

    @property
    def percent(self) -> int:
        """The level as a whole percentage."""
        return self.level * 100 // self.steps

    @property
    def engine_volume(self) -> float:
        """The volume the sound engine should use."""
        return self.ceiling * self.level / self.steps

    def apply(self) -> None:
        """Push the current volume to the engine."""
        self.apply_to_engine(self.engine_volume)

    def step(self, delta: int) -> bool:
        """Change the level by ``delta`` steps.

        Returns False when the level is already at a limit.
        """
        new_level = max(0, min(self.steps, self.level + delta))
        if new_level == self.level:
            return False
        self.level = new_level
        self.apply()
        return True


@dataclass(frozen=True)
class VolumeHotkeys:
    """Keys that lower and raise one ``ChannelVolume``.

    ``on_change`` runs after each key press, for example to play a sample
    so the new level can be heard.
    """

    volume: ChannelVolume
    down_key: int
    up_key: int
    on_change: Optional[Callable[[ChannelVolume], None]] = None


def bind_level_hotkeys(
    window: Window,
    hotkeys: Sequence[VolumeHotkeys],
    *,
    speak: Optional[Callable[..., object]] = None,
) -> None:
    """Bind volume keys on the window and speak each new level.

    Screens only handle their own keys, so unhandled presses fall through
    to the window and the keys work everywhere. ``speak`` defaults to the
    speech manager's ``output``.
    """

    def make_action(entry: VolumeHotkeys, delta: int) -> Callable[[], bool]:
        def action() -> bool:
            entry.volume.step(delta)
            announce = speak or speech_manager.output
            announce(
                f"{entry.volume.label} volume {entry.volume.percent} percent",
                interrupt=True,
            )
            if entry.on_change is not None:
                entry.on_change(entry.volume)
            return True

        return action

    for entry in hotkeys:
        window.key_handler.add_key_press(
            make_action(entry, -1), entry.down_key
        )
        window.key_handler.add_key_press(make_action(entry, 1), entry.up_key)
