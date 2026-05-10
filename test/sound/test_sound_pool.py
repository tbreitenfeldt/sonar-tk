import os

import pytest
from pytest_mock import MockerFixture

from sonartk.sound.sound_pool import SoundPool


@pytest.fixture
def sound_pool() -> SoundPool:
    """Create a SoundPool fixture."""
    return SoundPool()


# Initialization Tests


def test_init_starts_with_empty_pool(sound_pool: SoundPool) -> None:
    """Test that SoundPool initializes with an empty cache."""
    assert sound_pool.pool == {}


# load Tests


def test_load_returns_cached_sound_without_reloading(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that load returns existing cached sound for repeated path."""
    cached_sound = mocker.MagicMock()
    sound_pool.pool["audio/select.wav"] = cached_sound

    load_sound = mocker.patch("sonartk.sound.sound_pool.LoadSound")
    vorbis_file = mocker.patch("sonartk.sound.sound_pool.VorbisFile")
    buffer_sound = mocker.patch("sonartk.sound.sound_pool.BufferSound")

    result = sound_pool.load("audio/select.wav")

    assert result is cached_sound
    load_sound.assert_not_called()
    vorbis_file.assert_not_called()
    buffer_sound.assert_not_called()


def test_load_wav_creates_loadsound_and_caches(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that .wav files are loaded via LoadSound and cached."""
    mocker.patch("sonartk.sound.sound_pool.os.getcwd", return_value="C:/game")

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    result = sound_pool.load("audio/click.wav")

    expected_path = os.path.join("C:/game", "audio/click.wav")
    load_sound.assert_called_once_with(expected_path)
    assert result is wav_sound
    assert sound_pool.pool["audio/click.wav"] is wav_sound


def test_load_wav_is_case_insensitive(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that .WAV extension is handled case-insensitively."""
    mocker.patch("sonartk.sound.sound_pool.os.getcwd", return_value="C:/game")

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    result = sound_pool.load("audio/click.WAV")

    expected_path = os.path.join("C:/game", "audio/click.WAV")
    load_sound.assert_called_once_with(expected_path)
    assert result is wav_sound


def test_load_ogg_creates_buffer_sound_from_vorbis(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that .ogg files are decoded and loaded into BufferSound."""
    mocker.patch("sonartk.sound.sound_pool.os.getcwd", return_value="C:/game")

    vorbis = mocker.MagicMock()
    vorbis.channels = 2
    vorbis.frequency = 44100
    vorbis.buffer = b"ogg-bytes"
    vorbis_file = mocker.patch(
        "sonartk.sound.sound_pool.VorbisFile", return_value=vorbis
    )

    ogg_sound = mocker.MagicMock()
    ogg_sound.bitrate = 320000
    buffer_sound = mocker.patch(
        "sonartk.sound.sound_pool.BufferSound", return_value=ogg_sound
    )

    result = sound_pool.load("audio/music.ogg")

    expected_path = os.path.join("C:/game", "audio/music.ogg")
    vorbis_file.assert_called_once_with(expected_path)
    buffer_sound.assert_called_once()
    assert ogg_sound.channels == 2
    assert ogg_sound.samplerate == 44100
    ogg_sound.load.assert_called_once_with(b"ogg-bytes")
    assert result is ogg_sound
    assert sound_pool.pool["audio/music.ogg"] is ogg_sound


def test_load_ogg_is_case_insensitive(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that .OGG extension is handled case-insensitively."""
    mocker.patch("sonartk.sound.sound_pool.os.getcwd", return_value="C:/game")

    vorbis = mocker.MagicMock()
    vorbis.channels = 1
    vorbis.frequency = 22050
    vorbis.buffer = b"ogg"
    mocker.patch("sonartk.sound.sound_pool.VorbisFile", return_value=vorbis)

    ogg_sound = mocker.MagicMock()
    ogg_sound.bitrate = 128000
    mocker.patch(
        "sonartk.sound.sound_pool.BufferSound", return_value=ogg_sound
    )

    result = sound_pool.load("audio/speech.OGG")

    assert result is ogg_sound
    ogg_sound.load.assert_called_once_with(b"ogg")


def test_load_raises_for_unsupported_file_type(
    sound_pool: SoundPool,
) -> None:
    """Test that unsupported file types raise RuntimeError."""
    with pytest.raises(RuntimeError, match="Only .wav and .ogg file types"):
        sound_pool.load("audio/effect.mp3")


def test_load_caches_and_reuses_newly_loaded_sound(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that a first load is cached and reused on the second call."""
    mocker.patch("sonartk.sound.sound_pool.os.getcwd", return_value="C:/game")

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    first = sound_pool.load("audio/ui.wav")
    second = sound_pool.load("audio/ui.wav")

    assert first is wav_sound
    assert second is wav_sound
    load_sound.assert_called_once()


# destroy Tests


def test_destroy_calls_delete_on_all_sounds_and_clears_pool(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that destroy deletes every cached sound and clears the cache."""
    sound_a = mocker.MagicMock()
    sound_b = mocker.MagicMock()
    sound_pool.pool["a.wav"] = sound_a
    sound_pool.pool["b.ogg"] = sound_b

    sound_pool.destroy()

    sound_a.delete.assert_called_once()
    sound_b.delete.assert_called_once()
    assert sound_pool.pool == {}


def test_destroy_on_empty_pool_is_safe(sound_pool: SoundPool) -> None:
    """Test that destroy handles an empty pool without errors."""
    sound_pool.destroy()
    assert sound_pool.pool == {}
