from typing import Optional
import os

from pyogg import VorbisFile

from sonartk.sound.openal_lite.openal import LoadSound, BufferSound


class SoundPool:
    def __init__(self) -> None:
        self.pool: dict[str, LoadSound | BufferSound] = {}

    def load(self, path: str) -> LoadSound | BufferSound:
        if path in self.pool:
            return self.pool[path]

        sound: Optional[LoadSound | BufferSound] = None
        full_path: str = os.path.join(os.getcwd(), path)
        if path.lower().endswith(".wav"):
            sound = LoadSound(full_path)
        elif path.lower().endswith(".ogg"):
            vorbisFile: VorbisFile = VorbisFile(full_path)
            sound = BufferSound()
            sound.channels = vorbisFile.channels
            sound.bitrate = sound.bitrate
            sound.samplerate = vorbisFile.frequency
            sound.load(vorbisFile.buffer)
        else:
            raise RuntimeError(
                f"SoundPool does not support provided audio file: {path}. Only .wav and .ogg file types are allowed."
            )

        self.pool[path] = sound
        return sound

    def destroy(self) -> None:
        for sound in self.pool.values():
            sound.delete()
        self.pool.clear()
