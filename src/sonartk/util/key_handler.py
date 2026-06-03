import functools
import operator
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    cast,
)

import pyglet
from pyglet.window import key


class Key:
    def __init__(
        self, symbol: int, modifiers: Optional[List[int]] = None
    ) -> None:
        self.symbol: int = symbol
        self.modifiers: int = 0

        if modifiers is None:
            modifiers = []

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
        self.user_args: List[Any] = list(args)
        self.user_kwargs: Dict[str, Any] = kwargs
        self.internal_args: List[Any] = []

    def call(self) -> bool:
        """Invoke the callback with internal and user-provided arguments."""
        if self.callback is not None:
            args: List[Any] = self.internal_args + self.user_args
            kwargs: Dict[str, Any] = self.user_kwargs
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
        self.registered_key_combinations: dict[
            frozenset[Key], Tuple[Callback, float]
        ] = {}
        self.registered_key_releases: dict[Key, Callback] = {}
        self.registered_text_input: Optional[Callback] = None
        self.registered_text_motions: dict[Key, Callback] = {}
        self.pressed_key: Optional[Key] = None
        self.is_key_held_down: bool = False
        self.active_key_combination: Optional[frozenset[Key]] = None
        self.held_repeat_keys: list[Key] = []
        self.active_repeat_key: Optional[Key] = None
        self.currently_pressed_keys: set[Key] = set()
        self.key_interval_counter: float = 0.0
        self.other_keys_pressed: bool = (
            False  # Track if other keys were pressed
        )
        self.is_active: bool = True
        pyglet.clock.schedule_interval(self.update, update_repeat_interval)

    def set_update_check(self, update_repeat_interval: float = 0.01) -> None:
        """Configure and schedule the periodic key-repeat update loop."""
        self.update_repeat_interval = update_repeat_interval
        pyglet.clock.unschedule(self.update)
        pyglet.clock.schedule_interval(
            self.update, self.update_repeat_interval
        )

    def reset_transient_state(self) -> None:
        """Clear runtime press/hold state so detached handlers do not stick keys."""
        self.pressed_key = None
        self.is_key_held_down = False
        self.active_key_combination = None
        self.held_repeat_keys.clear()
        self.active_repeat_key = None
        self.currently_pressed_keys.clear()
        self.key_interval_counter = 0.0
        self.other_keys_pressed = False

    def activate(self, reset_state: bool = True) -> None:
        """Mark this handler active so key updates and events are processed."""
        self.is_active = True
        if reset_state:
            self.reset_transient_state()

    def deactivate(self, reset_state: bool = True) -> None:
        """Mark this handler inactive so scheduled repeats cannot run."""
        self.is_active = False
        if reset_state:
            self.reset_transient_state()

    def update(self, dt: float) -> None:
        """Trigger repeat callbacks while a registered key is held down."""
        if not self.is_active:
            return

        if self.active_key_combination is not None:
            callback, key_repeat_interval = self.registered_key_combinations[
                self.active_key_combination
            ]
            if key_repeat_interval <= 0:
                return
            callback.call()
            pyglet.clock.Clock.sleep(
                key_repeat_interval * 1000 * 1000
            )  # convert to seconds
        elif self.is_key_held_down:
            repeat_key = self.active_repeat_key or self.pressed_key
            if repeat_key is None:
                return

            callback, key_repeat_interval = self.registered_key_presses[
                cast(Key, repeat_key)
            ]
            if key_repeat_interval <= 0:
                return
            callback.call()
            pyglet.clock.Clock.sleep(
                key_repeat_interval * 1000 * 1000
            )  # convert to seconds

    @staticmethod
    def _find_exact_or_symbol_match(
        key: Key,
        keys: Iterable[Key],
    ) -> Optional[Key]:
        """Resolve a tracked key by exact match first, then by symbol."""
        key_list = list(keys)
        if key in key_list:
            return key

        for candidate in reversed(key_list):
            if candidate.symbol == key.symbol:
                return candidate

        return None

    def _get_active_combination(self) -> Optional[frozenset[Key]]:
        """Return the longest registered combo whose keys are all currently held."""
        matched: list[frozenset[Key]] = []
        for combo in self.registered_key_combinations:
            if combo.issubset(self.currently_pressed_keys):
                matched.append(combo)

        if not matched:
            return None

        matched.sort(key=len, reverse=True)
        return matched[0]

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle key-press events and dispatch matching registered callbacks."""
        if not self.is_active:
            return False

        pressed_key: Key = Key(symbol, [modifiers])
        self.currently_pressed_keys.add(pressed_key)

        active_combination = self._get_active_combination()
        if active_combination is not None:
            callback, key_repeat_interval = self.registered_key_combinations[
                active_combination
            ]
            self.active_key_combination = active_combination
            self.is_key_held_down = False
            if self.pressed_key is not None:
                self.other_keys_pressed = True

            if self.update_repeat_interval and key_repeat_interval:
                return True

            return callback.call()

        if pressed_key in self.registered_key_presses:
            callback, key_repeat_interval = self.registered_key_presses[
                pressed_key
            ]
            self.pressed_key = pressed_key
            self.other_keys_pressed = (
                False  # Reset flag when a registered key is pressed
            )

            if self.update_repeat_interval and key_repeat_interval:
                if pressed_key in self.held_repeat_keys:
                    self.held_repeat_keys.remove(pressed_key)
                self.held_repeat_keys.append(pressed_key)
                self.active_repeat_key = pressed_key
                self.is_key_held_down = True
                return True
            else:
                return callback.call()
        else:
            # Some other key was pressed - mark it if we're tracking a key release
            if self.pressed_key is not None:
                self.other_keys_pressed = True
            return False

    def on_key_release(  # noqa: C901
        self, symbol: int, modifiers: int
    ) -> bool:
        """Handle key-release events and dispatch release callbacks when valid."""
        if not self.is_active:
            return False

        raw_released_key: Key = Key(symbol, [modifiers])
        released_key = self._find_exact_or_symbol_match(
            raw_released_key,
            self.currently_pressed_keys,
        )
        if released_key is not None:
            self.currently_pressed_keys.discard(released_key)
        else:
            released_key = raw_released_key

        handled_release = False

        combo_release_key: Optional[Key] = None
        if self.active_key_combination is not None:
            combo_release_key = self._find_exact_or_symbol_match(
                released_key,
                self.active_key_combination,
            )

        if (
            self.active_key_combination is not None
            and combo_release_key is not None
        ):
            old_combo = self.active_key_combination
            self.active_key_combination = self._get_active_combination()
            if self.active_key_combination is not None:
                return True

            for combo_key in old_combo:
                if combo_key not in self.currently_pressed_keys:
                    if combo_key in self.held_repeat_keys:
                        self.held_repeat_keys.remove(combo_key)
                elif combo_key in self.registered_key_presses:
                    _, repeat_interval = self.registered_key_presses[combo_key]
                    if (
                        repeat_interval
                        and combo_key not in self.held_repeat_keys
                    ):
                        self.held_repeat_keys.append(combo_key)

            if self.held_repeat_keys:
                self.pressed_key = self.held_repeat_keys[-1]
                self.active_repeat_key = self.held_repeat_keys[-1]
                self.is_key_held_down = True
            else:
                self.active_repeat_key = None
                self.is_key_held_down = False
            handled_release = True

        release_repeat_key = self._find_exact_or_symbol_match(
            released_key,
            self.held_repeat_keys,
        )
        if release_repeat_key is not None:
            released_key = release_repeat_key

        if released_key in self.held_repeat_keys:
            self.held_repeat_keys.remove(released_key)
            if self.active_repeat_key == released_key:
                self.active_repeat_key = None
            if self.held_repeat_keys:
                self.active_repeat_key = self.held_repeat_keys[-1]
                self.is_key_held_down = True
            else:
                self.is_key_held_down = False
            handled_release = True

        if self.pressed_key == released_key:
            self.other_keys_pressed = False  # Reset flag

            if self.held_repeat_keys:
                self.pressed_key = self.held_repeat_keys[-1]
                self.active_repeat_key = self.held_repeat_keys[-1]
                self.is_key_held_down = True
            else:
                self.active_repeat_key = None
                self.is_key_held_down = False

            return True

        if raw_released_key in self.registered_key_releases:
            # Only trigger if no other keys were pressed during the key hold
            if not self.other_keys_pressed:
                callback = self.registered_key_releases[raw_released_key]
                self.other_keys_pressed = False  # Reset flag
                return callback.call()
            else:
                # Other keys were pressed, so don't trigger and reset flag
                self.other_keys_pressed = False
                return False

        if handled_release:
            return True

        return False

    def on_text(self, text: str) -> bool:
        """Handle text-input events and invoke the registered text callback."""
        if self.registered_text_input:
            self.registered_text_input.internal_args.append(text)
            return self.registered_text_input.call()

        return False

    def on_text_motion(self, motion: int) -> bool:
        """Handle text-motion events and invoke matching motion callbacks."""
        motion_key: Key = Key(motion)

        if motion_key in self.registered_text_motions:
            callback: Callback = self.registered_text_motions[motion_key]
            return callback.call()

        return False

    def add_key_press(
        self,
        callback: Callable,
        key: int | Key | Sequence[int | Key],
        modifiers: Optional[List[int]] = None,
        key_repeat_interval: float = 0.0,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Register a callback for a key or multi-key combination."""
        if modifiers is None:
            modifiers = []

        registered_callback: Optional[Callback] = None
        if isinstance(key, Sequence) and not isinstance(key, (str, bytes)):
            if len(key) < 2:
                raise ValueError(
                    "Please provide at least two keys for a key combination."
                )
            if modifiers:
                raise ValueError(
                    "Please do not provide modifiers when registering a key combination sequence."
                )

            combo_keys: list[Key] = []
            for key_item in key:
                if isinstance(key_item, int):
                    combo_keys.append(Key(key_item))
                elif isinstance(key_item, Key):
                    combo_keys.append(key_item)
                else:
                    raise ValueError(
                        "Key combinations must contain only Key or int values."
                    )

            if len(frozenset(combo_keys)) < 2:
                raise ValueError(
                    "Please provide at least two unique keys for a key combination."
                )

            registered_callback = Callback(callback, *args, **kwargs)
            self.registered_key_combinations[frozenset(combo_keys)] = (
                registered_callback,
                key_repeat_interval,
            )
        elif isinstance(key, int):
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
        modifiers: Optional[List[int]] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Register a callback for a key-release combination."""
        if modifiers is None:
            modifiers = []

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
        """Register the callback used for incoming text input."""
        registered_callback: Callback = Callback(callback, *args, **kwargs)
        self.registered_text_input = registered_callback

    def add_text_motion(
        self, callback: Callable, key: int | Key, *args: Any, **kwargs: Any
    ) -> None:
        """Register a callback for text motion keys."""
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
        """Remove a registered key-press callback."""
        if key in self.registered_key_presses:
            del self.registered_key_presses[key]
            return True

        return False

    def remove_key_release(self, key: Key) -> bool:
        """Remove a registered key-release callback."""
        if key in self.registered_key_releases:
            del self.registered_key_releases[key]
            return True

        return False

    def remove_on_text_input(self) -> None:
        """Clear the registered text-input callback."""
        self.registered_text_input = None

    def remove_text_motion(self, key: Key) -> bool:
        """Remove a registered text-motion callback."""
        if key in self.registered_text_motions:
            del self.registered_text_motions[key]
            return True

        return False

    def update_repeat_interval_for_key(
        self, key: Key, key_repeat_interval: float
    ) -> None:
        """Update repeat timing for a previously registered key-press binding."""
        if key not in self.registered_key_presses:
            raise ValueError(
                f"Unable to find {key} in registered keys to update key_repeat_interval"
            )

        # Update the key_repeat_interval by replacing the tuple
        callback, _ = self.registered_key_presses[key]
        self.registered_key_presses[key] = (callback, key_repeat_interval)

        if key_repeat_interval and not self.update_repeat_interval:
            self.set_update_check()
