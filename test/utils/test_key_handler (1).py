from typing import Callable, List
import operator
import functools

import pytest
from pytest_mock import MockerFixture
from unittest import mock
from pyglet.window import key

from audio_ui.utils import Key
from audio_ui.utils import Callback
from audio_ui.utils import KeyHandler

@pytest.fixture
def default_key_handler() -> KeyHandler:
    return KeyHandler()

@pytest.fixture
def key_handler_with_repete() -> KeyHandler:
    return KeyHandler(repeat_interval=0.2)

def test_create_key_with_one_modifier():
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_ALT])
    assert result.symbol == key.D
    assert result.modifiers == key.MOD_ALT

def test_create_key_with_multiple_modifiers():
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_ALT, key.MOD_CTRL])
    assert result.symbol == key.D
    assert result.modifiers & key.MOD_ALT == key.MOD_ALT
    assert result.modifiers & key.MOD_CTRL == key.MOD_CTRL

def test_create_key_with_no_modifiers():
    result: Key = Key(symbol=key.D)
    assert result.symbol == key.D
    assert result.modifiers == 0

def test_create_key_with_capslock():
    result: Key = Key(symbol=key.D, modifiers=[key.MOD_CAPSLOCK, key.MOD_ALT])
    assert result.modifiers & key.MOD_CAPSLOCK == 0

def test_key_eq_is_equals():
    key1: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    key2: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    assert key1.__eq__(key2)

def test_key_eq_is_not_equals_with_missing_modifier():
    key1: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    key2: Key = Key(symbol=key.C)
    assert not key1.__eq__(key2)

def test_key_eq_is_not_equals_with_extra_modifier():
    key1: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL])
    key2: Key = Key(symbol=key.C, modifiers=[key.MOD_CTRL, key.MOD_ALT])
    assert not key1.__eq__(key2)

def test_key_eq_is_not_equals_with_different_symbol():
    key1: Key = Key(key.C)
    key2: Key = Key(key.D)
    assert not key1.__eq__(key2)

def test_key_hash():
    result: Key = Key(symbol=key.A, modifiers=[key.MOD_COMMAND])
    assert result.__hash__()

def test_key_repr():
    result: Key = Key(symbol=key.A, modifiers=[key.MOD_COMMAND])
    assert result.__repr__()

def test_callback_call_successful():
    cb: Callback = Callback(lambda a: True, "test")
    result: bool = cb.call()
    assert result

def test_callback_call_failed():
    cb: Callback = Callback(None)
    result: bool = cb.call()
    assert not result

def test_callback_eq_is_equal():
    func: Callable = lambda: True
    cb1: Callback = Callback(func)
    cb2: Callback = Callback(func)
    assert cb1.__eq__(cb2)

def test_callback_eq_is_equal():
    cb1: Callback = Callback(lambda: True)
    cb2: Callback = Callback(lambda: False)
    assert not cb1.__eq__(cb2)

def test_callback_hash():
    cb: Callback = Callback(lambda: True)
    assert cb.__hash__()

def test_callback_repr():
    cb: Callback = Callback(lambda: True)
    assert cb.__repr__()

def test_key_handler_on_key_press(default_key_handler: KeyHandler):
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (registered_callback, 0.0)
    assert default_key_handler.on_key_press(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert default_key_handler.is_key_pressed

def test_key_handler_on_key_press_already_handled_key(default_key_handler: KeyHandler):
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (registered_callback, 0.0)
    default_key_handler.key_held_down = Key(key.F)
    assert not default_key_handler.on_key_press(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))

def test_key_handler_on_key_press_not_found(default_key_handler: KeyHandler):
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (registered_callback, 0.0)
    assert not default_key_handler.on_key_press(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL]))

def test_key_handler_on_key_press_with_global_key_repete(mocker: MockerFixture, key_handler_with_repete: KeyHandler):
    test_value: int = 0
    def test_func():
        nonlocal test_value
        test_value += 1
        return True

    pyglet_schedule_interval_mock = mocker.patch("pyglet.clock.schedule_interval")
    key_press: Key = Key(symbol=key.L, modifiers=[key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT])
    registered_callback: Callback = Callback(test_func)
    key_handler_with_repete.registered_key_presses[key_press] = (registered_callback, 0.0)
    assert key_handler_with_repete.on_key_press(symbol=key.L, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT]))
    assert key_handler_with_repete.is_key_pressed
    assert key_handler_with_repete.key_held_down == key_press
    pyglet_schedule_interval_mock.call_args_list[0][0][0]()
    # test_value should due to first being incremented by 1 on the initial call, and then again when the function is triggered for pyglet scheduler
    assert test_value == 2

def test_key_handler_on_key_press_with_key_repete(mocker: MockerFixture, default_key_handler: KeyHandler):
    test_value: int = 0
    def test_func():
        nonlocal test_value
        test_value += 1
        return True

    pyglet_schedule_interval_mock = mocker.patch("pyglet.clock.schedule_interval")
    key_press: Key = Key(symbol=key.L, modifiers=[key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT])
    repeat_interval: float = 0.2
    registered_callback: Callback = Callback(test_func)
    default_key_handler.registered_key_presses[key_press] = (registered_callback, repeat_interval)
    assert default_key_handler.on_key_press(symbol=key.L, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT, key.MOD_ALT]))
    assert default_key_handler.is_key_pressed
    assert default_key_handler.key_held_down == key_press
    pyglet_schedule_interval_mock.call_args_list[0][0][0]()
    # test_value should due to first being incremented by 1 on the initial call, and then again when the function is triggered for pyglet scheduler
    assert test_value == 2

def test_key_handler_on_key_release(default_key_handler: KeyHandler):
    key_release: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_releases[key_release] = registered_callback
    assert default_key_handler.on_key_release(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert not default_key_handler.is_key_pressed

def test_key_handler_on_key_release_not_found(default_key_handler: KeyHandler):
    key_release: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_releases[key_release] = registered_callback
    assert not default_key_handler.on_key_release(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL]))

def test_key_handler_on_key_release_after_key_press(default_key_handler: KeyHandler):
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_presses[key_press] = (registered_callback, 0.0)
    assert not default_key_handler.on_key_release(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert not default_key_handler.is_key_pressed

def test_key_handler_on_key_release_after_key_held_down(mocker: MockerFixture, key_handler_with_repete: KeyHandler):
    test_value: int = 0
    def test_func():
        nonlocal test_value
        test_value += 1
        return True

    pyglet_schedule_interval_mock = mocker.patch("pyglet.clock.schedule_interval")
    pyglet_unschedule_mock = mocker.patch("pyglet.clock.unschedule")
    key_press: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(test_func)
    key_handler_with_repete.registered_key_presses[key_press] = (registered_callback, 0.0)
    assert key_handler_with_repete.on_key_press(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert key_handler_with_repete.is_key_pressed
    assert key_handler_with_repete.key_held_down == key_press
    pyglet_schedule_interval_mock.call_args_list[0][0][0]()
    # test_value should due to first being incremented by 1 on the initial call, and then again when the function is triggered for pyglet scheduler
    assert test_value == 2
    key_handler_with_repete.registered_key_releases[key_press] = registered_callback
    assert key_handler_with_repete.on_key_release(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert not key_handler_with_repete.is_key_pressed
    assert key_handler_with_repete.key_held_down is None


def test_key_handler_on_text(default_key_handler: KeyHandler):
    test_value: str = ""
    def test_func(text: str):
        nonlocal test_value
        test_value = text
        return True

    default_key_handler.registered_text_input = Callback(test_func)
    text: str = "a"
    assert default_key_handler.on_text(text)
    assert test_value == text
    assert len(default_key_handler.registered_text_input.internal_args) == 0

def test_key_handler_on_text_already_handled(default_key_handler: KeyHandler):
    default_key_handler.is_key_pressed = True
    assert not default_key_handler.on_text("a")

def test_key_handler_on_text_with_no_callback_set(default_key_handler: KeyHandler):
    assert not default_key_handler.on_text("a")

def test_key_handler_on_text_motion(default_key_handler: KeyHandler):
    key_motion: Key = Key(key.MOTION_PREVIOUS_WORD)
    default_key_handler.registered_text_motions[key_motion] = Callback(lambda: True)
    assert default_key_handler.on_text_motion(key.MOTION_PREVIOUS_WORD)

def test_key_handler_on_text_motion_failed(default_key_handler: KeyHandler):
    key_motion: Key = Key(key.MOTION_DOWN)
    default_key_handler.registered_text_motions[key] = Callback(lambda: True)
    assert not default_key_handler.on_text_motion(key.MOTION_PREVIOUS_WORD)

def test_key_handler_add_key_press_with_key_object(default_key_handler: KeyHandler):
    callback: callable = lambda: True
    key_pressed: Key = Key(key.N)
    default_key_handler.add_key_press(callback, key_pressed)
    assert len(default_key_handler.registered_key_presses) == 1
    assert key_pressed in default_key_handler.registered_key_presses
    assert default_key_handler.registered_key_presses[key_pressed][0] == Callback(callback)
    assert default_key_handler.registered_key_presses[key_pressed][1] == 0.0

def test_key_handler_add_key_press_with_key_object_and_modifiers(default_key_handler: KeyHandler):
    with pytest.raises(ValueError):
        callback: callable = lambda: True
        key_pressed: Key = Key(key.N)
        default_key_handler.add_key_press(callback=callback, key=key_pressed, modifiers=key.MOD_ACCEL)

def test_key_handler_add_key_press_with_key_int(default_key_handler: KeyHandler):
    callback: callable = lambda: True
    symbol: int = key.PAGEDOWN
    modifiers: List[int] = [key.MOD_ACCEL]
    repete_interval: float = 0.2
    default_key_handler.add_key_press(callback, key=symbol, modifiers=modifiers, repeat_interval=repete_interval)
    key_pressed: Key = Key(symbol, modifiers)
    assert len(default_key_handler.registered_key_presses) == 1
    assert key_pressed in default_key_handler.registered_key_presses
    assert default_key_handler.registered_key_presses[key_pressed][0] == Callback(callback)
    assert default_key_handler.registered_key_presses[key_pressed][1] == repete_interval

def test_key_handler_add_key_press_with_error(default_key_handler: KeyHandler):
    with pytest.raises(ValueError):
        default_key_handler.add_key_press(lambda: True, None)

def test_key_handler_add_key_release_with_key_object(default_key_handler: KeyHandler):
    callback: callable = lambda: True
    key_released: Key = Key(key.N)
    default_key_handler.add_key_release(callback, key_released)
    assert len(default_key_handler.registered_key_releases) == 1
    assert key_released in default_key_handler.registered_key_releases
    assert default_key_handler.registered_key_releases[key_released] == Callback(callback)

def test_key_handler_add_key_release_with_key_object_and_modifiers(default_key_handler: KeyHandler):
    with pytest.raises(ValueError):
        callback: callable = lambda: True
        key_released: Key = Key(key.N)
        default_key_handler.add_key_release(callback=callback, key=key_released, modifiers=key.MOD_ACCEL)

def test_key_handler_add_key_release_with_key_int(default_key_handler: KeyHandler):
    callback: callable = lambda: True
    symbol: int = key.PAGEDOWN
    modifiers: List[int] = [key.MOD_ACCEL]
    default_key_handler.add_key_release(callback, key=symbol, modifiers=modifiers)
    key_released: Key = Key(symbol, modifiers)
    assert len(default_key_handler.registered_key_releases) == 1
    assert key_released in default_key_handler.registered_key_releases
    assert default_key_handler.registered_key_releases[key_released] == Callback(callback)

def test_key_handler_add_key_release_with_error(default_key_handler: KeyHandler):
    with pytest.raises(ValueError):
        default_key_handler.add_key_release(lambda: True, None)

def test_key_handler_add_on_text_input(default_key_handler: KeyHandler):
    callback: Callable = lambda: True
    default_key_handler.add_on_text_input(callback)
    assert default_key_handler.registered_text_input == Callback(callback)

def test_key_handler_add_text_motion_with_key_object(default_key_handler: KeyHandler):
    callback: callable = lambda: True
    text_motion: Key = Key(key.MOTION_BEGINNING_OF_FILE)
    default_key_handler.add_text_motion(callback, text_motion)
    assert len(default_key_handler.registered_text_motions) == 1
    assert text_motion in default_key_handler.registered_text_motions
    assert default_key_handler.registered_text_motions[text_motion] == Callback(callback)

def test_key_handler_add_text_motion_with_key_int(default_key_handler: KeyHandler):
    callback: callable = lambda: True
    key_motion: int = key.MOTION_BEGINNING_OF_FILE
    default_key_handler.add_text_motion(callback, key=key_motion)
    text_motion: Key = Key(key_motion)
    assert len(default_key_handler.registered_text_motions) == 1
    assert text_motion in default_key_handler.registered_text_motions
    assert default_key_handler.registered_text_motions[text_motion] == Callback(callback)

def test_key_handler_add_text_motion_with_error(default_key_handler: KeyHandler):
    with pytest.raises(ValueError):
        default_key_handler.add_text_motion(lambda: True, None)

def test_key_handler_remove_key_press_success(default_key_handler: KeyHandler):
    key_press: Key = Key(key.W)
    default_key_handler.registered_key_presses[key_press] = lambda: True
    assert default_key_handler.remove_key_press(key_press)
    assert key_press not in default_key_handler.registered_key_presses

def test_key_handler_remove_key_press_failed(default_key_handler: KeyHandler):
    key_press: Key = Key(key.W)
    default_key_handler.registered_key_presses[key_press] = lambda: True
    assert not default_key_handler.remove_key_press(Key(key.L))
    assert key_press in default_key_handler.registered_key_presses

def test_key_handler_remove_key_release_success(default_key_handler: KeyHandler):
    key_release: Key = Key(key.W)
    default_key_handler.registered_key_releases[key_release] = lambda: True
    assert default_key_handler.remove_key_release(key_release)
    assert key_release not in default_key_handler.registered_key_releases

def test_key_handler_remove_key_release_failed(default_key_handler: KeyHandler):
    key_release: Key = Key(key.W)
    default_key_handler.registered_key_releases[key_release] = lambda: True
    assert not default_key_handler.remove_key_release(Key(key.L))
    assert key_release in default_key_handler.registered_key_releases

def test_key_handler_remove_on_text_input(default_key_handler: KeyHandler):
    default_key_handler.registered_text_input = Callback(lambda: True)
    default_key_handler.remove_on_text_input()
    assert default_key_handler.registered_text_input is None

def test_key_handler_remove_text_motion_success(default_key_handler: KeyHandler):
    text_motion: Key = Key(key.W)
    default_key_handler.registered_text_motions[text_motion] = lambda: True
    assert default_key_handler.remove_text_motion(text_motion)
    assert text_motion not in default_key_handler.registered_text_motions

def test_key_handler_remove_text_motion_failed(default_key_handler: KeyHandler):
    text_motion: Key = Key(key.W)
    default_key_handler.registered_text_motions[text_motion] = lambda: True
    assert not default_key_handler.remove_text_motion(Key(key.L))
    assert text_motion in default_key_handler.registered_text_motions
