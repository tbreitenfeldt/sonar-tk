from typing import Callable
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
    assert default_key_handler.handled_key

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
    assert key_handler_with_repete.handled_key
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
    assert default_key_handler.handled_key
    assert default_key_handler.key_held_down == key_press
    pyglet_schedule_interval_mock.call_args_list[0][0][0]()
    # test_value should due to first being incremented by 1 on the initial call, and then again when the function is triggered for pyglet scheduler
    assert test_value == 2

def test_key_handler_on_key_release(default_key_handler: KeyHandler):
    key_release: Key = Key(symbol=key.W, modifiers=[key.MOD_CTRL, key.MOD_SHIFT])
    registered_callback: Callback = Callback(lambda: True)
    default_key_handler.registered_key_releases[key_release] = registered_callback
    assert default_key_handler.on_key_release(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert not default_key_handler.handled_key

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
    assert not default_key_handler.handled_key

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
    assert key_handler_with_repete.handled_key
    assert key_handler_with_repete.key_held_down == key_press
    pyglet_schedule_interval_mock.call_args_list[0][0][0]()
    # test_value should due to first being incremented by 1 on the initial call, and then again when the function is triggered for pyglet scheduler
    assert test_value == 2
    key_handler_with_repete.registered_key_releases[key_press] = registered_callback
    assert key_handler_with_repete.on_key_release(symbol=key.W, modifiers=functools.reduce(operator.ior, [key.MOD_CTRL, key.MOD_SHIFT]))
    assert not key_handler_with_repete.handled_key
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
    default_key_handler.handled_key = True
    assert not default_key_handler.on_text("a")

def test_key_handler_on_text_with_no_callback_set(default_key_handler: KeyHandler):
    assert not default_key_handler.on_text("a")

