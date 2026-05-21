from pathlib import Path

from pytest import MonkeyPatch

from sonartk.sound.openal_lite import openal
from sonartk.sound.sound_pool import SoundPool


def test_sound_pool_loads_real_wav_fixture_with_base_path(
    monkeypatch: MonkeyPatch,
) -> None:
    """Integration test for loading a real WAV fixture through SoundPool."""
    # Patch low-level OpenAL calls so fixture decoding can be tested reliably.
    monkeypatch.setattr(openal.al, "alGenBuffers", lambda _n, _buf: None)
    monkeypatch.setattr(
        openal.al,
        "alBufferData",
        lambda _buf, _fmt, _data, _length, _rate: None,
    )
    monkeypatch.setattr(
        openal.al,
        "alDeleteBuffers",
        lambda _n, _buf: None,
    )

    repo_root = Path(__file__).resolve().parents[2]
    fixture_path = repo_root / "examples" / "game" / "step_dirt.wav"
    assert fixture_path.is_file()

    sound_pool = SoundPool(base_path=repo_root)

    first = sound_pool.load("examples/game/step_dirt.wav")
    second = sound_pool.load(str(fixture_path))

    assert first is second
    assert sound_pool.size == 1

    # Ensure cleanup path still succeeds with real fixture-backed sound object.
    assert sound_pool.unload("examples/game/step_dirt.wav")
    assert sound_pool.size == 0
