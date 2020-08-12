"""
This module was created to manage audio actions and properties in a singalton fassion.
Implementing a true singalton class in python is challenging and often not very readable, so module level variables are used with the name mangling convention
to enforce they are not to be imported from the outside world.
"""

from typing import Dict
import os.path

import pygame
from pygame.mixer import Sound
from pygame.mixer import Channel

SOUNDS_DIRECTORY: str = "resources/sounds"
MUSIC_DIRECTORY: str = "resources/music"
sound_pool: Dict[str, Sound] = {}
channel_pool: Dict[str, Channel] = {}
MUSIC_VOLUME_FACTOR = 1.8

def get_sound(key: str):
    if key not in sound_pool:
        raise KeyError(f"the sound with the key {key} cannot be found in the sound pool.")

    return sound_pool[key]

def get_channel(id: str):
    if id not in channel_pool:
        if len(channel_pool) == 8:
            raise ValueError("Unable to create a new channel with that ID because 8 channels have been created already.")
        channel_pool[id] = Channel(id)

    return channel_pool[id]

def load_sound(filename: str, extended_path: str = "", name: str = "") -> None:
    """loads a sound into the sound_pool, if name is not provided, the key is the filename to the sound."""
    path = os.path.join(SOUNDS_DIRECTORY, extended_path, filename)
    key = name

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find sound. in '{path}")
    if name == "":
        key = filename

    sound = Sound(path)
    sound_pool[key] = sound

def auto_load_sounds(extended_path: str = "") -> None:
    """Searches the directory of SOUNDS_DIRECTORY + extended_path, and loads all files in that directory as sounds, using the filename as the key."""
    path = os.path.join(SOUNDS_DIRECTORY, extended_path)
    (_, _, filenames) = next(os.walk(path))

    for filename in filenames:
        key = filename
        load_sound(filename, extended_path, key)

def play_sound(key: str, wait_until_done: bool = False, *args, **kwargs) -> Channel:
    if key not in sound_pool:
        raise KeyError(f"the sound with the key {key} cannot be found in the sound pool.")

    sound = sound_pool[key]
    sound.set_volume(1)
    channel: Channel = sound.play(*args, **kwargs)

    if wait_until_done:
        sound_length: int = sound.get_length() * 1000
        pygame.time.wait(int(sound_length))

    return channel

def play_sound_on_channel(key: str, channel: Channel, wait_tell_done: bool = False, *args, **kwargs) -> None:
    if key not in sound_pool:
        raise KeyError(f"the sound with the key {key} cannot be found in the sound pool.")
    if channel is None:
        raise ValueError("Channel cannot be None.")

    sound = sound_pool[key]
    sound.set_volume(global_sound_volume)
    channel.play(sound, *args, **kwargs)

    if wait_tell_done:
        sound_length: int = sound.get_length() * 1000
        pygame.time.wait(sound_length)


def stop_sound(key: str):
    if key not in sound_pool:
        raise KeyError(f"the sound with the key {key} cannot be found in the sound pool.")

    sound = sound_pool[key]
    sound.stop()

def set_sound_volume(volume):
    global_music_volume = volume
    for i in range(pygame.mixer.get_num_channels()):
        channel = Channel(i)
def load_music(file_path: str) -> None:
    path = os.path.join(MUSIC_DIRECTORY, file_path)

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find music. in '{path}")

    pygame.mixer.music.load(path)

def play_music(volume=1.0, *args, **kwargs) -> None:
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play(*args, **kwargs)

def pause_music() -> None:
    pygame.mixer.music.pause()

def unpause_music() -> None:
    pygame.mixer.music.unpause()

def stop_music() -> None:
    pygame.mixer.music.stop()

def increase_music_volume() -> None:
    if pygame.mixer.music.get_busy():
        current_volume: float = pygame.mixer.music.get_volume()
        new_volume: float = round(current_volume * MUSIC_VOLUME_FACTOR, 3)

        if new_volume == 0:
            pygame.mixer.music.set_volume(0.02)
        elif new_volume <= 1:
            pygame.mixer.music.set_volume(new_volume)

def decrease_music_volume() -> None:
    if pygame.mixer.music.get_busy():
        current_volume: float = pygame.mixer.music.get_volume()
        new_volume: float = round(current_volume / MUSIC_VOLUME_FACTOR, 3)

        if new_volume <= 0.02:
            pygame.mixer.music.set_volume(0)
        elif new_volume > 0:
            pygame.mixer.music.set_volume(new_volume)
