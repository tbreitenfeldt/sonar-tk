from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from sonartk.sound.sound_pool import (
    SoundFileNotFoundError,
    SoundPool,
    UnsupportedAudioFormatError,
)


@pytest.fixture
def sound_pool() -> SoundPool:
    """Create a SoundPool fixture."""
    return SoundPool()


# Initialization Tests


def test_init_starts_with_empty_pool(sound_pool: SoundPool) -> None:
    """Test that SoundPool initializes with an empty cache."""
    assert sound_pool.pool == {}


def test_init_with_base_path_resolves_relative_loads(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test that a configured base path is used for relative loads."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)
    wav_path = audio_dir / "click.wav"
    wav_path.touch()
    sound_pool = SoundPool(base_path=tmp_path)

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    result = sound_pool.load("audio/click.wav")

    expected_path = str(wav_path.resolve())
    assert result is wav_sound
    load_sound.assert_called_once_with(expected_path)
    assert sound_pool.has("audio/click.wav")
    assert sound_pool.size == 1
    assert tuple(sound_pool.cached_paths()) == (expected_path,)


# load Tests


def test_load_returns_cached_sound_without_reloading(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that load returns existing cached sound for repeated path."""
    cached_sound = mocker.MagicMock()
    key = str(sound_pool._normalize_path("audio/select.wav"))
    sound_pool.pool[key] = cached_sound

    load_sound = mocker.patch("sonartk.sound.sound_pool.LoadSound")
    vorbis_file = mocker.patch("sonartk.sound.sound_pool.VorbisFile")
    buffer_sound = mocker.patch("sonartk.sound.sound_pool.BufferSound")

    result = sound_pool.load("audio/select.wav")

    assert result is cached_sound
    load_sound.assert_not_called()
    vorbis_file.assert_not_called()
    buffer_sound.assert_not_called()


def test_load_wav_creates_loadsound_and_caches(
    mocker: MockerFixture, sound_pool: SoundPool, tmp_path: Path
) -> None:
    """Test that .wav files are loaded via LoadSound and cached."""
    wav_path = tmp_path / "audio" / "click.wav"
    wav_path.parent.mkdir(parents=True)
    wav_path.touch()

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    result = sound_pool.load(str(wav_path))

    expected_path = str(wav_path.resolve())
    load_sound.assert_called_once_with(expected_path)
    assert result is wav_sound
    assert sound_pool.pool[expected_path] is wav_sound


def test_load_wav_is_case_insensitive(
    mocker: MockerFixture, sound_pool: SoundPool, tmp_path: Path
) -> None:
    """Test that .WAV extension is handled case-insensitively."""
    wav_path = tmp_path / "audio" / "click.WAV"
    wav_path.parent.mkdir(parents=True)
    wav_path.touch()

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    result = sound_pool.load(str(wav_path))

    expected_path = str(wav_path.resolve())
    load_sound.assert_called_once_with(expected_path)
    assert result is wav_sound


def test_load_ogg_creates_buffer_sound_from_vorbis(
    mocker: MockerFixture, sound_pool: SoundPool, tmp_path: Path
) -> None:
    """Test that .ogg files are decoded and loaded into BufferSound."""
    ogg_path = tmp_path / "audio" / "music.ogg"
    ogg_path.parent.mkdir(parents=True)
    ogg_path.touch()

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

    result = sound_pool.load(str(ogg_path))

    expected_path = str(ogg_path.resolve())
    vorbis_file.assert_called_once_with(expected_path)
    buffer_sound.assert_called_once()
    assert ogg_sound.channels == 2
    assert ogg_sound.bitrate == 16
    assert ogg_sound.samplerate == 44100
    ogg_sound.load.assert_called_once_with(b"ogg-bytes")
    assert result is ogg_sound
    assert sound_pool.pool[expected_path] is ogg_sound


def test_load_ogg_is_case_insensitive(
    mocker: MockerFixture, sound_pool: SoundPool, tmp_path: Path
) -> None:
    """Test that .OGG extension is handled case-insensitively."""
    ogg_path = tmp_path / "audio" / "speech.OGG"
    ogg_path.parent.mkdir(parents=True)
    ogg_path.touch()

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

    result = sound_pool.load(str(ogg_path))

    assert result is ogg_sound
    ogg_sound.load.assert_called_once_with(b"ogg")


def test_load_raises_for_unsupported_file_type(
    sound_pool: SoundPool,
) -> None:
    """Test that unsupported file types raise UnsupportedAudioFormatError."""
    with pytest.raises(
        UnsupportedAudioFormatError, match="Only .wav and .ogg file types"
    ):
        sound_pool.load("audio/effect.mp3")


def test_load_raises_for_missing_supported_file(
    sound_pool: SoundPool,
) -> None:
    """Test that missing .wav/.ogg files raise SoundFileNotFoundError."""
    with pytest.raises(SoundFileNotFoundError, match="Unable to locate"):
        sound_pool.load("audio/missing.wav")


def test_load_caches_and_reuses_newly_loaded_sound(
    mocker: MockerFixture,
    sound_pool: SoundPool,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test normalized paths dedupe to one cache entry and one decode call."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)
    wav_path = audio_dir / "ui.wav"
    wav_path.touch()
    monkeypatch.chdir(tmp_path)

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    first = sound_pool.load("audio/ui.wav")
    second = sound_pool.load("./audio/../audio/ui.wav")

    assert first is wav_sound
    assert second is wav_sound
    load_sound.assert_called_once()
    assert len(sound_pool.pool) == 1


def test_load_absolute_path_ignores_base_path(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test that absolute paths are not rebased through the configured base path."""
    base_path = tmp_path / "assets"
    base_path.mkdir()
    wav_path = tmp_path / "audio" / "ui.wav"
    wav_path.parent.mkdir(parents=True)
    wav_path.touch()
    sound_pool = SoundPool(base_path=base_path)

    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound", return_value=wav_sound
    )

    sound_pool.load(str(wav_path))

    load_sound.assert_called_once_with(str(wav_path.resolve()))


def test_load_many_loads_multiple_paths_and_returns_normalized_keys(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test load_many loads each path and returns normalized cache keys."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)
    wav_path = audio_dir / "click.wav"
    ogg_path = audio_dir / "music.ogg"
    wav_path.touch()
    ogg_path.touch()

    sound_pool = SoundPool(base_path=tmp_path)

    wav_sound = mocker.MagicMock(name="wav_sound")
    ogg_sound = mocker.MagicMock(name="ogg_sound")
    mocker.patch(
        "sonartk.sound.sound_pool.LoadSound",
        return_value=wav_sound,
    )

    vorbis = mocker.MagicMock()
    vorbis.channels = 2
    vorbis.frequency = 44100
    vorbis.buffer = b"ogg"
    mocker.patch("sonartk.sound.sound_pool.VorbisFile", return_value=vorbis)
    mocker.patch(
        "sonartk.sound.sound_pool.BufferSound",
        return_value=ogg_sound,
    )

    loaded = sound_pool.load_many(["audio/click.wav", "audio/music.ogg"])

    expected_wav_key = str(wav_path.resolve())
    expected_ogg_key = str(ogg_path.resolve())
    assert list(loaded.keys()) == [expected_wav_key, expected_ogg_key]
    assert loaded[expected_wav_key] is wav_sound
    assert loaded[expected_ogg_key] is ogg_sound
    assert sound_pool.size == 2


def test_load_many_reuses_cached_sounds_for_equivalent_paths(
    mocker: MockerFixture,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test load_many dedupes through cache when paths normalize equally."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)
    wav_path = audio_dir / "ui.wav"
    wav_path.touch()
    monkeypatch.chdir(tmp_path)

    sound_pool = SoundPool()
    wav_sound = mocker.MagicMock()
    load_sound = mocker.patch(
        "sonartk.sound.sound_pool.LoadSound",
        return_value=wav_sound,
    )

    loaded = sound_pool.load_many(["audio/ui.wav", "./audio/../audio/ui.wav"])

    expected_key = str(wav_path.resolve())
    load_sound.assert_called_once_with(expected_key)
    assert list(loaded.keys()) == [expected_key]
    assert loaded[expected_key] is wav_sound
    assert sound_pool.get_stats()["hits"] == 1
    assert sound_pool.get_stats()["misses"] == 1


def test_load_many_raises_and_keeps_previously_loaded_items_cached(
    mocker: MockerFixture, tmp_path: Path
) -> None:
    """Test load_many stops on first error while preserving prior successful loads."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)
    wav_path = audio_dir / "ok.wav"
    wav_path.touch()

    sound_pool = SoundPool(base_path=tmp_path)
    wav_sound = mocker.MagicMock()
    mocker.patch("sonartk.sound.sound_pool.LoadSound", return_value=wav_sound)

    with pytest.raises(UnsupportedAudioFormatError):
        sound_pool.load_many(["audio/ok.wav", "audio/not-supported.mp3"])

    expected_key = str(wav_path.resolve())
    assert sound_pool.pool == {expected_key: wav_sound}


# unload Tests


def test_unload_removes_and_deletes_cached_sound(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test that unload deletes and removes a cached sound."""
    cached_sound = mocker.MagicMock()
    path = "audio/select.wav"
    key = str(sound_pool._normalize_path(path))
    sound_pool.pool[key] = cached_sound

    result = sound_pool.unload(path)

    assert result is True
    cached_sound.delete.assert_called_once()
    assert key not in sound_pool.pool


def test_unload_returns_false_when_sound_not_cached(
    sound_pool: SoundPool,
) -> None:
    """Test that unload returns False when no matching cache entry exists."""
    assert sound_pool.unload("audio/none.wav") is False


def test_unload_is_defensive_when_delete_raises(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test unload still removes cache entry when delete raises."""
    cached_sound = mocker.MagicMock()
    cached_sound.delete.side_effect = RuntimeError("already deleted")
    path = "audio/select.wav"
    key = str(sound_pool._normalize_path(path))
    sound_pool.pool[key] = cached_sound

    assert sound_pool.unload(path) is True
    assert key not in sound_pool.pool


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


def test_destroy_is_safe_when_sound_delete_raises(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test destroy continues cleanup even if a sound delete raises."""
    sound_a = mocker.MagicMock()
    sound_b = mocker.MagicMock()
    sound_a.delete.side_effect = RuntimeError("bad delete")
    sound_pool.pool["a.wav"] = sound_a
    sound_pool.pool["b.ogg"] = sound_b

    sound_pool.destroy()

    sound_a.delete.assert_called_once()
    sound_b.delete.assert_called_once()
    assert sound_pool.pool == {}


def test_destroy_is_idempotent(sound_pool: SoundPool) -> None:
    """Test destroy can be called repeatedly without error."""
    sound_pool.destroy()
    sound_pool.destroy()
    assert sound_pool.pool == {}


def test_unload_after_destroy_returns_false(sound_pool: SoundPool) -> None:
    """Test unload after destroy safely reports no cached sound."""
    sound_pool.destroy()
    assert sound_pool.unload("audio/none.wav") is False


def test_get_stats_tracks_hits_misses_loads_and_unloads(
    mocker: MockerFixture,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test SoundPool stats counters update across load and unload calls."""
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir(parents=True)
    wav_path = audio_dir / "click.wav"
    wav_path.touch()
    monkeypatch.chdir(tmp_path)

    sound_pool = SoundPool()
    wav_sound = mocker.MagicMock()
    mocker.patch("sonartk.sound.sound_pool.LoadSound", return_value=wav_sound)

    sound_pool.load("audio/click.wav")  # miss + load
    sound_pool.load("audio/click.wav")  # hit
    assert sound_pool.unload("audio/click.wav")  # unload
    assert not sound_pool.unload("audio/click.wav")  # unload miss

    stats = sound_pool.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 1
    assert stats["loads"] == 1
    assert stats["unloads"] == 1
    assert stats["unload_misses"] == 1


def test_cached_paths_and_size_match_pool_contents(
    mocker: MockerFixture, sound_pool: SoundPool
) -> None:
    """Test size and cached_paths introspection reflect current cache state."""
    cached_sound = mocker.MagicMock()
    key = str(sound_pool._normalize_path("audio/a.wav"))
    sound_pool.pool[key] = cached_sound

    assert sound_pool.size == 1
    assert tuple(sound_pool.cached_paths()) == (key,)


def test_destroy_on_empty_pool_is_safe(sound_pool: SoundPool) -> None:
    """Test that destroy handles an empty pool without errors."""
    sound_pool.destroy()
    assert sound_pool.pool == {}
