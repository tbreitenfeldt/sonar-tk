from typing import Callable, List
import operator
import functools

import pytest
from pytest_mock import MockerFixture
from pyglet.window import key

from sonartk.util.key_handler import Key
from sonartk.util.key_handler import Callback
from sonartk.util.key_handler import KeyHandler


@pytest.fixture
def default_key_handler() -> KeyHandler:
    return KeyHandler()


@pytest.fixture
def key_handler_with_repete() -> KeyHandler:
    return KeyHandler(update_repeat_interval=0.2)


def test_create_key_with_one_modifier() -> None:
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_ALT])
    assert result.symbol == key.D
    assert result.modifiers == key.MOD_ALT


def test_create_key_with_multiple_modifiers() -> None:
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_ALT, key.MOD_CTRL])
    assert result.symbol == key.D
    assert result.modifiers & key.MOD_ALT == key.MOD_ALT
    assert result.modifiers & key.MOD_CTRL == key.MOD_CTRL


def test_create_key_with_no_modifiers() -> None:
    result: Key = Key(symbol=key.D)
    assert result.symbol == key.D
    assert result.modifiers == 0


def test_create_key_with_capslock() -> None:
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_CAPSLOCK, key.MOD_ALT])
    assert result.modifiers & key.MOD_CAPSLOCK == 0


def test_key_eq_is_equals() -> None:
    key1: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    key2: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    assert key1.__eq__(key2)


def test_key_eq_is_not_equals_with_missing_modifier() -> None:
    key1: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    key2: Key = Key(symbol=key.C)
    assert not key1.__eq__(key2)


def test_key_eq_is_not_equals_with_extra_modifier() -> None:
    key1: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    key2: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL, key.MOD_ALT])
    assert not key1.__eq__(key2)


def test_key_eq_is_not_equals_with_different_symbol() -> None:
    key1: Key = Key(key.C)
    key2: Key = Key(key.D)
    assert not key1.__eq__(key2)


def test_key_hash() -> None:
    result: Key = Key(symbol=key.A, modifiers=[key.MOD_COMMAND])
    assert result.__hash__()


def test_key_repr() -> None:
    result: Key = Key(symbol=key.A, modifiers=[key.MOD_COMMAND])
    assert result.__repr__()


def test_callback_call_successful() -> None:
    cb: Callback = Callback(lambda a: True, "test")
    result: bool = cb.call()
    assert result


def test_callback_call_failed() -> None:
    cb: Callback = Callback(lambda: False)  # type: ignore[arg-type]
    result: bool = cb.call()
    assert not result


def test_callback_eq_is_equal() -> None:
    func: Callable = lambda: True
    cb1: Callback = Callback(func)
    cb2: Callback = Callback(func)
    assert cb1.__eq__(cb2)


def test_callback_eq_is_not_equal() -> None:
    cb1: Callback = Callback(lambda: True)
    cb2: Callback = Callback(lambda: False)
    assert not cb1.__eq__(cb2)


def test_callback_hash() -> None:
    cb: Callback = Callback(lambda: True)
    assert cb.__hash__()


def test_callback_repr() -> None:
    cb: Callback = Callback(lambda: True)
    assert cb.__repr__()


def test_key_handler_on_key_press(default_key_handler: KeyHandler) -> None:
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (
        registered_callback,
        0.0,
    )
    assert default_key_handler.on_key_press(
        symbol=key.W,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]
        ),
    )
    # Default handler has no update_repeat_interval, so is_key_held_down stays False
    assert not default_key_handler.is_key_held_down
    assert default_key_handler.pressed_key == key_press


def test_key_handler_on_key_press_already_handled_key(
    default_key_handler: KeyHandler,
) -> None:
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (
        registered_callback,
        0.0,
    )
    default_key_handler.pressed_key = Key(key.F)
    default_key_handler.other_keys_pressed = True
    # The key handler should still register the new key press
    assert default_key_handler.on_key_press(
        symbol=key.W,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]
        ),
    )
    # And it should update the pressed_key
    assert default_key_handler.pressed_key == key_press
    # other_keys_pressed should be reset
    assert not default_key_handler.other_keys_pressed


def test_key_handler_on_key_press_not_found(
    default_key_handler: KeyHandler,
) -> None:
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (
        registered_callback,
        0.0,
    )
    assert not default_key_handler.on_key_press(
        symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL])
    )


def test_key_handler_on_key_press_with_global_key_repete(
    mocker: MockerFixture, key_handler_with_repete: KeyHandler
) -> None:
    test_value: int = 0

    def test_func() -> bool:
        nonlocal test_value
        test_value += 1
        return True

    key_press: Key = Key(
        symbol=key.L, modifiers=[key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT]
    )
    registered_callback: Callback = Callback(test_func)
    key_handler_with_repete.registered_key_presses[key_press] = (
        registered_callback,
        0.1,  # Non-zero repeat interval
    )
    # Call on_key_press - with update_repeat_interval and key_repeat_interval set,
    # it will enter repeat mode (is_key_held_down=True) and NOT call the callback yet
    assert key_handler_with_repete.on_key_press(
        symbol=key.L,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT]
        ),
    )
    assert key_handler_with_repete.is_key_held_down
    assert key_handler_with_repete.pressed_key == key_press
    # Callback hasn't been called yet since it's in repeat mode
    assert test_value == 0
    # Simulate the scheduled update() being called
    key_handler_with_repete.update(0.01)
    # Now the callback should have been called once
    assert test_value == 1


def test_key_handler_on_key_press_with_key_repete(
    mocker: MockerFixture, default_key_handler: KeyHandler
) -> None:
    test_value: int = 0

    def test_func() -> bool:
        nonlocal test_value
        test_value += 1
        return True

    key_press: Key = Key(
        symbol=key.L, modifiers=[key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT]
    )
    repeat_interval: float = 0.2
    registered_callback: Callback = Callback(test_func)
    default_key_handler.registered_key_presses[key_press] = (
        registered_callback,
        repeat_interval,
    )
    # Call on_key_press - since update_repeat_interval is 0, it will just call the callback once
    assert default_key_handler.on_key_press(
        symbol=key.L,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT]
        ),
    )
    # No repeat mode since default_key_handler has update_repeat_interval=0.0
    assert not default_key_handler.is_key_held_down
    assert default_key_handler.pressed_key == key_press
    # Callback was called once during on_key_press
    assert test_value == 1


def test_key_handler_on_key_release(default_key_handler: KeyHandler) -> None:
    key_release: Key = Key(
        symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT]
    )
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_releases[key_release] = (
        registered_callback
    )
    assert default_key_handler.on_key_release(
        symbol=key.W,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]
        ),
    )
    assert not default_key_handler.is_key_held_down


def test_key_handler_on_key_release_not_found(
    default_key_handler: KeyHandler,
) -> None:
    key_release: Key = Key(
        symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT]
    )
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_releases[key_release] = (
        registered_callback
    )
    assert not default_key_handler.on_key_release(
        symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL])
    )


def test_key_handler_on_key_release_after_key_press(
    default_key_handler: KeyHandler,
) -> None:
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (
        registered_callback,
        0.0,
    )
    assert not default_key_handler.on_key_release(
        symbol=key.W,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]
        ),
    )
    assert not default_key_handler.is_key_held_down


def test_key_handler_on_key_release_after_key_held_down(
    mocker: MockerFixture, key_handler_with_repete: KeyHandler
) -> None:
    test_value: int = 0

    def test_func() -> bool:
        nonlocal test_value
        test_value += 1
        return True

    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(test_func)
    key_handler_with_repete.registered_key_presses[key_press] = (
        registered_callback,
        0.1,  # Non-zero repeat interval
    )
    # Press the key - enters repeat mode
    assert key_handler_with_repete.on_key_press(
        symbol=key.W,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]
        ),
    )
    assert key_handler_with_repete.is_key_held_down
    assert key_handler_with_repete.pressed_key == key_press
    # Callback hasn't been called yet
    assert test_value == 0
    # Simulate update() being called
    key_handler_with_repete.update(0.01)
    assert test_value == 1
    # Register key release handler and release the key
    key_handler_with_repete.registered_key_releases[key_press] = (
        registered_callback
    )
    assert key_handler_with_repete.on_key_release(
        symbol=key.W,
        modifiers=functools.reduce(
            operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]
        ),
    )
    assert not key_handler_with_repete.is_key_held_down
    # pressed_key is still set until another key is pressed
    assert key_handler_with_repete.pressed_key == key_press


def test_key_handler_on_text(default_key_handler: KeyHandler) -> None:
    test_value: str = ""

    def test_func(text: str) -> bool:
        nonlocal test_value
        test_value = text
        return True

    default_key_handler.registered_text_input = Callback(test_func)
    text: str = "a"
    assert default_key_handler.on_text(text)
    assert test_value == text
    assert len(default_key_handler.registered_text_input.internal_args) == 0


def test_key_handler_on_text_already_handled(
    default_key_handler: KeyHandler,
) -> None:
    default_key_handler.is_key_held_down = True
    assert not default_key_handler.on_text("a")


def test_key_handler_on_text_with_no_callback_set(
    default_key_handler: KeyHandler,
) -> None:
    assert not default_key_handler.on_text("a")


def test_key_handler_on_text_motion(default_key_handler: KeyHandler) -> None:
    key_motion = Key(key.MOTION_PREVIOUS_WORD)  # noqa: F841
    default_key_handler.registered_text_motions[key_motion] = Callback(
        lambda: True
    )
    assert default_key_handler.on_text_motion(key.MOTION_PREVIOUS_WORD)


def test_key_handler_on_text_motion_failed(
    default_key_handler: KeyHandler,
) -> None:
    key_motion: Key = Key(key.MOTION_DOWN)  # noqa: F841
    default_key_handler.registered_text_motions[key_motion] = Callback(
        lambda: True
    )
    assert not default_key_handler.on_text_motion(key.MOTION_PREVIOUS_WORD)


def test_key_handler_add_key_press_with_key_object(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    key_pressed: Key = Key(key.N)
    default_key_handler.add_key_press(callback, key_pressed)
    assert len(default_key_handler.registered_key_presses) == 1
    assert key_pressed in default_key_handler.registered_key_presses
    assert default_key_handler.registered_key_presses[key_pressed][
        0
    ] == Callback(callback)
    assert default_key_handler.registered_key_presses[key_pressed][1] == 0.0


def test_key_handler_add_key_press_with_key_object_and_modifiers(
    default_key_handler: KeyHandler,
) -> None:
    with pytest.raises(ValueError):
        callback: Callable = lambda: True
        key_pressed: Key = Key(key.N)
        default_key_handler.add_key_press(
            callback=callback, key=key_pressed, modifiers=[key.MOD_ACCEL]
        )


def test_key_handler_add_key_press_with_key_int(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    symbol: int = key.PAGEDOWN
    modifiers: List[int] = [key.MOD_ACCEL]
    repete_interval: float = 0.2
    default_key_handler.add_key_press(
        callback,
        key=symbol,
        modifiers=modifiers,
        key_repeat_interval=repete_interval,
    )
    key_pressed: Key = Key(symbol, modifiers)
    assert len(default_key_handler.registered_key_presses) == 1
    assert key_pressed in default_key_handler.registered_key_presses
    assert default_key_handler.registered_key_presses[key_pressed][
        0
    ] == Callback(callback)
    assert (
        default_key_handler.registered_key_presses[key_pressed][1]
        == repete_interval
    )


def test_key_handler_add_key_press_with_error(
    default_key_handler: KeyHandler,
) -> None:
    with pytest.raises(ValueError):
        # This should raise ValueError because we can't pass both a Key object and modifiers
        default_key_handler.add_key_press(lambda: True, key=Key(key.A), modifiers=[key.MOD_CTRL])  # type: ignore[arg-type]


def test_key_handler_add_key_release_with_key_object(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    key_released: Key = Key(key.N)
    default_key_handler.add_key_release(callback, key_released)
    assert len(default_key_handler.registered_key_releases) == 1
    assert key_released in default_key_handler.registered_key_releases
    assert default_key_handler.registered_key_releases[
        key_released
    ] == Callback(callback)


def test_key_handler_add_key_release_with_key_object_and_modifiers(
    default_key_handler: KeyHandler,
) -> None:
    with pytest.raises(ValueError):
        callback: Callable = lambda: True
        key_released: Key = Key(key.N)
        default_key_handler.add_key_release(
            callback=callback, key=key_released, modifiers=[key.MOD_ACCEL]
        )


def test_key_handler_add_key_release_with_key_int(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    symbol: int = key.PAGEDOWN
    modifiers: List[int] = [key.MOD_ACCEL]
    default_key_handler.add_key_release(
        callback, key=symbol, modifiers=modifiers
    )
    key_released: Key = Key(symbol, modifiers)
    assert len(default_key_handler.registered_key_releases) == 1
    assert key_released in default_key_handler.registered_key_releases
    assert default_key_handler.registered_key_releases[
        key_released
    ] == Callback(callback)


def test_key_handler_add_key_release_with_error(
    default_key_handler: KeyHandler,
) -> None:
    with pytest.raises(ValueError):
        # This should raise ValueError because we can't pass both a Key object and modifiers
        default_key_handler.add_key_release(lambda: True, key=Key(key.A), modifiers=[key.MOD_CTRL])  # type: ignore[arg-type]


def test_key_handler_add_on_text_input(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    default_key_handler.add_on_text_input(callback)
    assert default_key_handler.registered_text_input == Callback(callback)


def test_key_handler_add_text_motion_with_key_object(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    text_motion: Key = Key(key.MOTION_BEGINNING_OF_FILE)
    default_key_handler.add_text_motion(callback, text_motion)
    assert len(default_key_handler.registered_text_motions) == 1
    assert text_motion in default_key_handler.registered_text_motions
    assert default_key_handler.registered_text_motions[
        text_motion
    ] == Callback(callback)


def test_key_handler_add_text_motion_with_key_int(
    default_key_handler: KeyHandler,
) -> None:
    callback: Callable = lambda: True
    key_motion: int = key.MOTION_BEGINNING_OF_FILE
    default_key_handler.add_text_motion(callback, key=key_motion)
    text_motion: Key = Key(key_motion)
    assert len(default_key_handler.registered_text_motions) == 1
    assert text_motion in default_key_handler.registered_text_motions
    assert default_key_handler.registered_text_motions[
        text_motion
    ] == Callback(callback)


def test_key_handler_add_text_motion_with_error(
    default_key_handler: KeyHandler,
) -> None:
    with pytest.raises(ValueError):
        # This should raise ValueError because key must be int or Key
        default_key_handler.add_text_motion(lambda: True, key="invalid")  # type: ignore[arg-type]


def test_key_handler_remove_key_press_success(
    default_key_handler: KeyHandler,
) -> None:
    key_press: Key = Key(key.W)
    default_key_handler.registered_key_presses[key_press] = (
        Callback(lambda: True),
        0.0,
    )
    assert default_key_handler.remove_key_press(key_press)
    assert key_press not in default_key_handler.registered_key_presses


def test_key_handler_remove_key_press_failed(
    default_key_handler: KeyHandler,
) -> None:
    key_press: Key = Key(key.W)
    default_key_handler.registered_key_presses[key_press] = (
        Callback(lambda: True),
        0.0,
    )
    assert not default_key_handler.remove_key_press(Key(key.L))
    assert key_press in default_key_handler.registered_key_presses


def test_key_handler_remove_key_release_success(
    default_key_handler: KeyHandler,
) -> None:
    key_release: Key = Key(key.W)
    default_key_handler.registered_key_releases[key_release] = Callback(
        lambda: True
    )
    assert default_key_handler.remove_key_release(key_release)
    assert key_release not in default_key_handler.registered_key_releases


def test_key_handler_remove_key_release_failed(
    default_key_handler: KeyHandler,
) -> None:
    key_release: Key = Key(key.W)
    default_key_handler.registered_key_releases[key_release] = Callback(
        lambda: True
    )
    assert not default_key_handler.remove_key_release(Key(key.L))
    assert key_release in default_key_handler.registered_key_releases


def test_key_handler_remove_on_text_input(
    default_key_handler: KeyHandler,
) -> None:
    default_key_handler.registered_text_input = Callback(lambda: True)
    default_key_handler.remove_on_text_input()
    assert default_key_handler.registered_text_input is None


def test_key_handler_remove_text_motion_success(
    default_key_handler: KeyHandler,
) -> None:
    text_motion: Key = Key(key.W)
    default_key_handler.registered_text_motions[text_motion] = Callback(
        lambda: True
    )
    assert default_key_handler.remove_text_motion(text_motion)
    assert text_motion not in default_key_handler.registered_text_motions


def test_key_handler_remove_text_motion_failed(
    default_key_handler: KeyHandler,
) -> None:
    text_motion: Key = Key(key.W)
    default_key_handler.registered_text_motions[text_motion] = Callback(
        lambda: True
    )
    assert not default_key_handler.remove_text_motion(Key(key.L))
    assert text_motion in default_key_handler.registered_text_motions


def test_key_with_numlock() -> None:
    """Test that NUMLOCK modifier is removed"""
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_NUMLOCK, key.MOD_ALT])
    assert result.modifiers & key.MOD_NUMLOCK == 0
    assert result.modifiers & key.MOD_ALT == key.MOD_ALT


def test_key_with_scrolllock() -> None:
    """Test that SCROLLLOCK modifier is removed"""
    result: Key = Key(
        symbol=key.D, modifiers=[key.MOD_SCROLLLOCK, key.MOD_CTRL]
    )
    assert result.modifiers & key.MOD_SCROLLLOCK == 0
    assert result.modifiers & key.MOD_CTRL == key.MOD_CTRL


def test_callback_eq_with_non_callback() -> None:
    """Test Callback.__eq__ with non-Callback object"""
    cb: Callback = Callback(lambda: True)
    assert cb.__eq__("not a callback") == NotImplemented


def test_key_handler_on_key_press_other_key_tracking() -> None:
    """Test that other_keys_pressed flag is set when unregistered key is pressed"""
    handler: KeyHandler = KeyHandler()
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL])
    handler.registered_key_presses[key_press] = (Callback(lambda: True), 0.0)

    # Press the registered key
    handler.on_key_press(key.W, key.MOD_CTRL)
    assert handler.pressed_key == key_press
    assert not handler.other_keys_pressed

    # Press an unregistered key
    assert not handler.on_key_press(key.A, 0)
    assert handler.other_keys_pressed


def test_key_handler_on_key_release_with_other_keys_pressed() -> None:
    """Test that key release doesn't trigger callback if other keys were pressed"""
    handler: KeyHandler = KeyHandler()
    key_release: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL])
    callback_called = False

    def test_callback() -> bool:
        nonlocal callback_called
        callback_called = True
        return True

    handler.registered_key_releases[key_release] = Callback(test_callback)
    # Set pressed_key to a different key so we test the registered_key_releases path
    handler.pressed_key = Key(key.A)
    handler.other_keys_pressed = True

    # Release should not trigger callback because other_keys_pressed is True
    assert not handler.on_key_release(key.W, key.MOD_CTRL)
    assert not callback_called
    assert not handler.other_keys_pressed  # Flag should be reset


def test_key_handler_on_key_release_unreleased_tracked_key() -> None:
    """Test releasing a key that was being tracked but not in registered_key_releases"""
    handler: KeyHandler = KeyHandler()
    key_press: Key = Key(symbol=key.W)
    handler.pressed_key = key_press
    handler.other_keys_pressed = False

    # Release the tracked key (not in registered_key_releases)
    assert handler.on_key_release(key.W, 0)

    def test_callback_call_with_none_callback() -> None:
        """Test Callback.call() returns False when callback is set to None."""
        cb: Callback = Callback(lambda: True)
        cb.callback = None  # type: ignore[assignment]
        assert not cb.call()

    def test_add_key_press_raises_for_invalid_key_type(
        default_key_handler: KeyHandler,
    ) -> None:
        """Test add_key_press raises ValueError for non-int, non-Key types."""
        with pytest.raises(
            ValueError, match="MKey must be either of type Key or int"
        ):
            default_key_handler.add_key_press(lambda: True, key=1.5)  # type: ignore[arg-type]

    def test_add_key_release_raises_for_invalid_key_type(
        default_key_handler: KeyHandler,
    ) -> None:
        """Test add_key_release raises ValueError for non-int, non-Key types."""
        with pytest.raises(
            ValueError, match="MKey must be either of type Key or int"
        ):
            default_key_handler.add_key_release(lambda: True, key=1.5)  # type: ignore[arg-type]

    assert not handler.other_keys_pressed


def test_key_handler_update_repeat_interval_for_key_not_found() -> None:
    """Test update_repeat_interval_for_key with key not in registered keys"""
    handler: KeyHandler = KeyHandler()
    test_key: Key = Key(key.W)

    with pytest.raises(ValueError, match="Unable to find"):
        handler.update_repeat_interval_for_key(test_key, 0.5)


def test_key_handler_update_repeat_interval_for_key_success() -> None:
    """Test update_repeat_interval_for_key successfully updates interval"""
    handler: KeyHandler = KeyHandler()
    test_key: Key = Key(key.W)
    handler.registered_key_presses[test_key] = (Callback(lambda: True), 0.1)

    handler.update_repeat_interval_for_key(test_key, 0.5)
    assert handler.registered_key_presses[test_key][1] == 0.5


def test_key_handler_update_repeat_interval_for_key_enables_update() -> None:
    """Test update_repeat_interval_for_key calls set_update_check when needed"""
    handler: KeyHandler = KeyHandler()  # update_repeat_interval is 0.0
    test_key: Key = Key(key.W)
    handler.registered_key_presses[test_key] = (Callback(lambda: True), 0.0)

    # Set a non-zero repeat interval, which should trigger set_update_check
    handler.update_repeat_interval_for_key(test_key, 0.5)
    assert handler.registered_key_presses[test_key][1] == 0.5
    # update_repeat_interval should now be set (default 0.01 from set_update_check)
    assert handler.update_repeat_interval == 0.01


def test_key_handler_update_repeat_interval_for_key_no_update_needed() -> None:
    """Test update_repeat_interval_for_key when set_update_check is not needed"""
    handler: KeyHandler = KeyHandler(update_repeat_interval=0.1)  # Already set
    test_key: Key = Key(key.W)
    handler.registered_key_presses[test_key] = (Callback(lambda: True), 0.2)

    # Update to a different non-zero interval - should NOT call set_update_check
    # since update_repeat_interval is already set
    handler.update_repeat_interval_for_key(test_key, 0.3)
    assert handler.registered_key_presses[test_key][1] == 0.3
    assert handler.update_repeat_interval == 0.1  # Unchanged


def test_key_handler_update_when_not_held_down() -> None:
    """Test update() method when is_key_held_down is False (early exit branch)"""
    handler: KeyHandler = KeyHandler(update_repeat_interval=0.1)

    # When is_key_held_down is False, update should exit early
    handler.is_key_held_down = False
    handler.update(0.01)  # Should exit without error

    # Test that it actually does something when is_key_held_down is True
    callback_count = 0

    def test_callback() -> bool:
        nonlocal callback_count
        callback_count += 1
        return True

    key_press: Key = Key(key.W)
    handler.registered_key_presses[key_press] = (
        Callback(test_callback),
        0.001,
    )
    handler.pressed_key = key_press
    handler.is_key_held_down = True

    handler.update(0.01)
    assert callback_count == 1
