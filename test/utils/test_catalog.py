from enum import Enum

import pytest

from sonartk.util import resolve_name


class Sound(Enum):
    OCEAN = "ocean.wav"
    WIND = "wind.wav"


def test_finds_the_member_by_lower_case_name() -> None:
    assert resolve_name(Sound, "ocean", "sound") is Sound.OCEAN


def test_lookup_ignores_case() -> None:
    assert resolve_name(Sound, "Wind", "sound") is Sound.WIND


def test_none_passes_through() -> None:
    assert resolve_name(Sound, None, "sound") is None


def test_unknown_name_is_rejected_with_context() -> None:
    with pytest.raises(ValueError, match="Unknown sound 'rain' in Sound"):
        resolve_name(Sound, "rain", "sound")


def test_label_is_optional() -> None:
    with pytest.raises(ValueError, match="Unknown entry 'rain'"):
        resolve_name(Sound, "rain")
