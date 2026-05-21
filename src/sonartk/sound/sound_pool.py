from pathlib import Path
from typing import Iterable

from pyogg import VorbisFile

from sonartk.sound.openal_lite.openal import LoadSound, BufferSound

DEFAULT_OGG_PCM_BITRATE = 16


class SoundPoolError(Exception):
    """Base exception for sound pool operations."""


class UnsupportedAudioFormatError(SoundPoolError):
    """Raised when a sound path has an unsupported file extension."""


class SoundFileNotFoundError(SoundPoolError, FileNotFoundError):
    """Raised when a supported sound file cannot be found."""


class SoundPool:
    def __init__(self, base_path: str | Path | None = None) -> None:
        self.base_path = self._resolve_base_path(base_path)
        self.pool: dict[str, LoadSound | BufferSound] = {}
        self._stats: dict[str, int] = {
            "hits": 0,
            "misses": 0,
            "loads": 0,
            "unloads": 0,
            "unload_misses": 0,
        }

    @staticmethod
    def _resolve_base_path(base_path: str | Path | None) -> Path | None:
        """Resolve an optional base path used for relative sound paths."""
        if base_path is None:
            return None
        return Path(base_path).resolve()

    def _normalize_path(self, path: str) -> Path:
        """Normalize a path for stable cache keys.

        Relative paths are resolved from the configured base path when set,
        otherwise from the current working directory.
        """
        raw_path = Path(path)
        if not raw_path.is_absolute():
            root = self.base_path if self.base_path is not None else Path.cwd()
            raw_path = root / raw_path
        return raw_path.resolve()

    def _load_wav(self, path: Path) -> LoadSound:
        """Load a WAV file into an OpenAL sound buffer."""
        return LoadSound(str(path))

    def _load_ogg(self, path: Path) -> BufferSound:
        """Decode an OGG file and load it into an OpenAL buffer."""
        vorbis_file = VorbisFile(str(path))
        sound = BufferSound()
        sound.channels = vorbis_file.channels
        sound.bitrate = DEFAULT_OGG_PCM_BITRATE
        sound.samplerate = vorbis_file.frequency
        sound.load(vorbis_file.buffer)
        return sound

    @staticmethod
    def _delete_sound(sound: LoadSound | BufferSound) -> None:
        """Delete a sound buffer defensively during cleanup paths."""
        try:
            sound.delete()
        except Exception:
            return

    @property
    def size(self) -> int:
        """Return the number of cached sounds."""
        return len(self.pool)

    def has(self, path: str) -> bool:
        """Return whether a path is currently cached."""
        return str(self._normalize_path(path)) in self.pool

    def cached_paths(self) -> Iterable[str]:
        """Return the normalized cache keys for currently loaded sounds."""
        return tuple(self.pool.keys())

    def get_stats(self) -> dict[str, int]:
        """Return cache usage statistics."""
        return dict(self._stats)

    def load(self, path: str) -> LoadSound | BufferSound:
        """Load and cache an audio file by normalized absolute path."""
        normalized_path = self._normalize_path(path)
        cache_key = str(normalized_path)
        extension = normalized_path.suffix.lower()

        if extension not in (".wav", ".ogg"):
            raise UnsupportedAudioFormatError(
                f"SoundPool does not support provided audio file: {path}. Only .wav and .ogg file types are allowed."
            )

        if cache_key in self.pool:
            self._stats["hits"] += 1
            return self.pool[cache_key]

        self._stats["misses"] += 1

        if not normalized_path.is_file():
            raise SoundFileNotFoundError(
                f"Unable to locate sound file: {normalized_path}"
            )

        sound: LoadSound | BufferSound
        if extension == ".wav":
            sound = self._load_wav(normalized_path)
        else:
            sound = self._load_ogg(normalized_path)

        self.pool[cache_key] = sound
        self._stats["loads"] += 1
        return sound

    def unload(self, path: str) -> bool:
        """Unload a specific cached sound by path.

        Returns True if a sound was removed; otherwise False.
        """
        cache_key = str(self._normalize_path(path))
        sound = self.pool.pop(cache_key, None)
        if sound is None:
            self._stats["unload_misses"] += 1
            return False

        self._delete_sound(sound)
        self._stats["unloads"] += 1
        return True

    def destroy(self) -> None:
        """Destroy."""
        for sound in tuple(self.pool.values()):
            self._delete_sound(sound)
        self.pool.clear()
