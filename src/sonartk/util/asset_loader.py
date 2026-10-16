from __future__ import annotations

from typing import Callable, Iterable

import pyglet.clock


class AssetLoader:
    """Keep only the assets a game currently needs in memory.

    Assets are identified by file path. ``pin`` loads files that stay
    resident for the whole game. ``set_active`` names the files the current
    scene needs now plus files it will probably need next, such as the
    neighbouring maps: the first group loads immediately, the second one file
    per frame so playback is never stalled, and everything else this loader
    loaded earlier is unloaded.

    Unloading deletes the audio buffer, so call ``set_active`` only after the
    sounds that used the old files have been stopped or replaced.

    Args:
        load: Called with a path to load it.
        unload: Called with a path to release it.
    """

    def __init__(
        self,
        load: Callable[[str], object],
        unload: Callable[[str], object],
    ) -> None:
        self._load = load
        self._unload = unload
        self._pinned: set[str] = set()
        self._resident: set[str] = set()
        self._pending: list[str] = []

    @property
    def resident(self) -> frozenset[str]:
        """Paths loaded through this loader, pinned ones included."""
        return frozenset(self._resident | self._pinned)

    @property
    def pending(self) -> tuple[str, ...]:
        """Paths still waiting to be loaded in idle frames."""
        return tuple(self._pending)

    def pin(self, paths: Iterable[str]) -> None:
        """Load paths now and never unload them."""
        for path in paths:
            self._pinned.add(path)
            self._resident.discard(path)
            self._load(path)

    def set_active(
        self,
        now: Iterable[str],
        soon: Iterable[str] = (),
    ) -> None:
        """Make ``now`` ready, queue ``soon`` and unload everything else."""
        needed_now = [p for p in now if p not in self._pinned]
        needed_soon = [
            p
            for p in soon
            if p not in self._pinned and p not in set(needed_now)
        ]
        self._stop_pending()
        keep = set(needed_now) | set(needed_soon)
        for path in sorted(self._resident - keep):
            self._unload(path)
            self._resident.discard(path)
        for path in needed_now:
            if path not in self._resident:
                self._load(path)
                self._resident.add(path)
        self._pending = [p for p in needed_soon if p not in self._resident]
        if self._pending:
            pyglet.clock.schedule_once(self._load_next, 0.0)

    def finish_pending(self) -> None:
        """Load every queued path immediately."""
        while self._pending:
            self._load_next(0.0)

    def _load_next(self, _: float) -> None:
        if not self._pending:
            return
        path = self._pending.pop(0)
        self._load(path)
        self._resident.add(path)
        if self._pending:
            pyglet.clock.schedule_once(self._load_next, 0.0)

    def _stop_pending(self) -> None:
        pyglet.clock.unschedule(self._load_next)
        self._pending = []


def sound_pool_loader() -> AssetLoader:
    """Build a loader backed by the shared sound pool."""
    from sonartk.sound import sound_manager

    return AssetLoader(
        lambda path: sound_manager.sound_pool.load(path),
        lambda path: sound_manager.sound_pool.unload(path),
    )
