import functools
import math
import operator
import time
from typing import Any, Callable, Dict, List, Optional, Self, Tuple, cast

import pyglet
from pyglet.window import key


class Key:
    def __init__(self, symbol: int, modifiers: List[int] = []) -> None:
        self.symbol: int = symbol
        self.modifiers: int = 0

        if len(modifiers) == 1:
            self.modifiers = modifiers[0]
        elif len(modifiers) > 1:
            self.modifiers = functools.reduce(operator.ior, modifiers)
        else:
            self.modifiers = 0

        # remove lock keys from the modifiers if present, because there is an issue where if a lock key is on, it causes it to be passed in with all key presses until it is turned off.
        if self.modifiers & key.MOD_CAPSLOCK:
            self.modifiers &= ~key.MOD_CAPSLOCK
        if self.modifiers & key.MOD_NUMLOCK:
            self.modifiers &= ~key.MOD_NUMLOCK
        if self.modifiers & key.MOD_SCROLLLOCK:
            self.modifiers &= ~key.MOD_SCROLLLOCK

    # override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Key):
            return NotImplemented

        return (
            self.symbol == other.symbol and self.modifiers == other.modifiers
        )

    def __hash__(self) -> int:
        return hash((self.symbol, self.modifiers))

    def __repr__(self) -> str:
        return f"({pyglet.window.key.symbol_string(self.symbol)}, {pyglet.window.key.modifiers_string(self.modifiers)})"


class Callback:
    def __init__(self, callback: Callable, *args: Any, **kwargs: Any) -> None:
        self.callback: Callable = callback
        self.user_args: List[str] = list(args)
        self.user_kwargs: Dict[str, str] = kwargs
        self.internal_args: List[str] = []

    def call(self) -> bool:
        if self.callback is not None:
            args: List[str] = self.internal_args + self.user_args
            kwargs: Dict[str, str] = self.user_kwargs
            result: bool = self.callback(*args, **kwargs)
            self.internal_args = []
            return result

        return False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Callback):
            return NotImplemented

        return self.callback == other.callback

    def __hash__(self) -> int:
        return hash(self.callback)

    def __repr__(self) -> str:
        return self.callback.__name__


class KeyHandler:
    def __init__(self, update_repeat_interval: float = 0.0) -> None:
        self.update_repeat_interval: float = update_repeat_interval
        self.registered_key_presses: dict[Key, Tuple[Callback, float]] = {}
        self.registered_key_releases: dict[Key, Callback] = {}
        self.registered_text_input: Optional[Callback] = None
        self.registered_text_motions: dict[Key, Callback] = {}
        self.pressed_key: Optional[Key] = None
        self.is_key_held_down: bool = False
        self.key_interval_counter: float = 0.0
        pyglet.clock.schedule_interval(self.update, update_repeat_interval)

    def set_update_check(self, update_repeat_interval=0.01) -> None:
        self.update_repeat_interval = update_repeat_interval
        pyglet.clock.unschedule(self.update)
        pyglet.clock.schedule_interval(
            self.update, self.update_repeat_interval
        )

    def update(self, dt: float) -> None:
        if self.is_key_held_down:
            callback, key_repeat_interval = self.registered_key_presses[
                cast(Key, self.pressed_key)
            ]
            callback.call()
            pyglet.clock.Clock.sleep(
                key_repeat_interval * 1000 * 1000
            )  # convert to seconds

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        pressed_key: Key = Key(symbol, [modifiers])

        if pressed_key in self.registered_key_presses:
            callback, key_repeat_interval = self.registered_key_presses[
                pressed_key
            ]
            self.pressed_key = pressed_key

            if self.update_repeat_interval and key_repeat_interval:
                self.is_key_held_down = True
                return True
            else:
                return callback.call()
        else:
            return False

    def on_key_release(self, symbol: int, modifiers: int) -> bool:
        released_key: Key = Key(symbol, [modifiers])

        if self.pressed_key == released_key:
            callback, key_repeat_interval = self.registered_key_presses[
                released_key
            ]
            self.pressed_key = None

            if self.is_key_held_down:
                self.is_key_held_down = False

            return True

        if released_key in self.registered_key_releases:
            callback = self.registered_key_releases[released_key]
            return callback.call()

        return False

    def on_text(self, text: str) -> bool:
        if self.registered_text_input:
            self.registered_text_input.internal_args.append(text)
            return self.registered_text_input.call()

        return False

    def on_text_motion(self, motion: int) -> bool:
        motion_key: Key = Key(motion)

        if motion_key in self.registered_text_motions:
            callback: Callback = self.registered_text_motions[motion_key]
            return callback.call()

        return False

    def add_key_press(
        self,
        callback: Callable,
        key: int | Key,
        modifiers: List[int] = [],
        key_repeat_interval: float = 0.0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        registered_callback: Optional[Callback] = None
        if isinstance(key, int):
            key_press: Key = Key(key, modifiers)
            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_key_presses[key_press] = (
                registered_callback,
                key_repeat_interval,
            )
        elif isinstance(key, Key):
            if modifiers:
                raise ValueError(
                    "Please do not provide modifiers if you are giving a Key object."
                )

            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_key_presses[key] = (
                registered_callback,
                key_repeat_interval,
            )
        else:
            raise ValueError("MKey must be either of type Key or int.")

        if key_repeat_interval and not self.update_repeat_interval:
            self.set_update_check()

    def add_key_release(
        self,
        callback: Callable,
        key: int | Key,
        modifiers: List[int] = [],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        registered_callback: Optional[Callback] = None
        if isinstance(key, int):
            key_release: Key = Key(key, modifiers)
            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_key_releases[key_release] = registered_callback
        elif isinstance(key, Key):
            if modifiers:
                raise ValueError(
                    "Please do not provide modifiers if you are giving a Key object."
                )

            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_key_releases[key] = registered_callback
        else:
            raise ValueError("MKey must be either of type Key or int.")

    def add_on_text_input(
        self, callback: Callable, *args: Any, **kwargs: Any
    ) -> None:
        registered_callback: Callback = Callback(callback, *args, **kwargs)
        self.registered_text_input = registered_callback

    def add_text_motion(
        self, callback: Callable, key: int | Key, *args: Any, **kwargs: Any
    ) -> None:
        registered_callback: Optional[Callback] = None
        if isinstance(key, int):
            motion_key: Key = Key(key)
            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_text_motions[motion_key] = registered_callback
        elif isinstance(key, Key):
            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_text_motions[key] = registered_callback
        else:
            raise ValueError("MKey must be either of type Key or int.")

    def remove_key_press(self, key: Key) -> bool:
        if key in self.registered_key_presses:
            del self.registered_key_presses[key]
            return True

        return False

    def remove_key_release(self, key: Key) -> bool:
        if key in self.registered_key_releases:
            del self.registered_key_releases[key]
            return True

        return False

    def remove_on_text_input(self) -> None:
        self.registered_text_input = None

    def remove_text_motion(self, key: Key) -> bool:
        if key in self.registered_text_motions:
            del self.registered_text_motions[key]
            return True

        return False

    def update_repeat_interval_for_key(
        self, key: Key, key_repeat_interval: float
    ) -> None:
        if key not in self.registered_key_presses:
            raise ValueError(
                f"Unable to find {key} in registered keys to update key_repeat_interval"
            )

        # The format of value is (callback, key_repeat_interval),. Need to modify key_repeat_interval
        self.registered_key_presses[key][1] = key_repeat_interval

        if key_repeat_interval and not self.update_key_repeat_interval:
            self.set_update_check()
