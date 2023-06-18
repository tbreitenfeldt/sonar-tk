from typing import Callable
import pytest
from pytest_mock import MockerFixture
from pyglet.window import key

from audio_ui.utils import Key
from audio_ui.utils import Callback
from audio_ui.utils import KeyHandler

@pytest.fixture
def default_key_handler() -> KeyHandler:
    return KeyHandler()

@pytest.fixture
def key_handler_with_repete() -> KeyHandler:
    return KeyHandler(key=0.2)

def test_create_key_with_one_modifier():
    result: Key = Key(key.D, key.MOD_ALT, key_repeat_interval=0.1)
    assert result.symbol == key.D
    assert result.key_repeat_interval == 0.1
    assert result.modifiers == key.MOD_ALT

def test_create_key_with_multiple_modifiers():
    result: Key = Key(key.D, key.MOD_ALT, key.MOD_CTRL)
    assert result.symbol == key.D
    assert result.key_repeat_interval == 0
    assert result.modifiers & key.MOD_ALT == key.MOD_ALT
    assert result.modifiers & key.MOD_CTRL == key.MOD_CTRL

def test_create_key_with_no_modifiers():
    result: Key = Key(key.D)
    assert result.symbol == key.D
    assert result.key_repeat_interval == 0
    assert result.modifiers == 0

def test_create_key_with_capslock():
    result: Key = Key(key.D, key.MOD_CAPSLOCK, key.MOD_ALT)
    assert result.modifiers & key.MOD_CAPSLOCK == 0

def test_key_eq_is_equals():
    key1: Key = Key(key.C, key.MOD_CTRL)
    key2: Key = Key(key.C, key.MOD_CTRL)
    assert key1.__eq__(key2)

def test_key_eq_is_not_equals_with_missing_modifier():
    key1: Key = Key(key.C, key.MOD_CTRL)
    key2: Key = Key(key.C)
    assert not key1.__eq__(key2)

def test_key_eq_is_not_equals_with_extra_modifier():
    key1: Key = Key(key.C, key.MOD_CTRL)
    key2: Key = Key(key.C, key.MOD_CTRL, key.MOD_ALT)
    assert not key1.__eq__(key2)

def test_key_eq_is_not_equals_with_different_symbol():
    key1: Key = Key(key.C)
    key2: Key = Key(key.D)
    assert not key1.__eq__(key2)

def test_key_hash():
    result: Key = Key(key.A, key.MOD_COMMAND)
    assert result.__hash__()

def test_key_repr():
    result: Key = Key(key.A, key.MOD_COMMAND)
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

def test_key_handler_on_key_press(default_key_handler):
    pass
