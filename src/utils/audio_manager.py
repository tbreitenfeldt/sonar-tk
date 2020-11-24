"""
This module was created to manage audio actions and properties in a singalton fassion.
Implementing a true singalton class in python is challenging and often not very readable, so module level variables are used with the name mangling convention
to enforce they are not to be imported from the outside world.
"""

from typing import Dict
import os.path
import time

import pyglet

SOUNDS_DIRECTORY: str = "resources/sounds"
MUSIC_DIRECTORY: str = "resources/music"
SOUND_POOL: Dict[str, "StaticSource"] = {}
MUSIC_POOL: Dict[str, "Source"] = {}
SOUND_VOLUME: float = 1.0
MUSIC_VOLUME: float = 1.0

def get_sound(key: str) -> "StaticSource":
    if key not in SOUND_POOL:
        raise KeyError(f"the sound with the key {key} cannot be found in the sound pool.")

    return SOUND_POOL[key]

def load_sound(filename: str, extended_path: str = "", name: str = "") -> None:
    """loads a sound into the sound_pool, if name is not provided, the key is the filename to the sound."""
    path = os.path.join(SOUNDS_DIRECTORY, extended_path, filename)
    key = name

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find sound. in '{path}")
    if name == "":
        key = filename

    sound: "StaticSource" = pyglet.resource.media(path, streaming=False)
    SOUND_POOL[key] = sound

def auto_load_sounds(extended_path: str = "") -> None:
    """Searches the directory of SOUNDS_DIRECTORY + extended_path, and loads all files in that directory as sounds, using the filename as the key."""
    path = os.path.join(SOUNDS_DIRECTORY, extended_path)
    (_, _, filenames) = next(os.walk(path))

    for filename in filenames:
        key = filename
        load_sound(filename, extended_path, key)

def play_sound(key: str, wait_until_done: bool = False, *args, **kwargs) -> "Player":
    if key not in SOUND_POOL:
        raise KeyError(f"the sound with the key {key} cannot be found in the sound pool.")

    sound: "StaticSource" = SOUND_POOL[key]
    player: "Player" = sound.play()
    player.volume = SOUND_VOLUME

    if wait_until_done:
        time.sleep(sound.duration)

    return player

def load_music(filename: str, extended_path: str = "", name: str = "") -> None:
    path = os.path.join(MUSIC_DIRECTORY, filename, extended_path)
    key: str = name

    if not os.path.isfile(path):
        raise FileNotFoundError(f"Unable to find music. in '{path}")
    if name == "":
        key = filename

        music: "Source" = pyglet.resource.media(path)
        MUSIC_POOL[key] = music

def auto_load_music(extended_path: str = "") -> None:
    """Searches the directory of MUSIC_DIRECTORY + extended_path, and loads all files in that directory as music, using the filename as the key."""
    path = os.path.join(MUSIC_DIRECTORY, extended_path)
    (_, _, filenames) = next(os.walk(path))

    for filename in filenames:
        key = filename
        load_music(filename, extended_path, key)

def play_music(key: str) -> "Player":
    if key not in SOUND_POOL:
        raise KeyError(f"the music with the key {key} cannot be found in the music pool.")

    player: "Player" = MUSIC_POOL[key].play()
    player.volume = MUSIC_VOLUME
    return player
