from enum import Enum
from pathlib import Path

import pytest

from sonartk.util import AssetCatalog, resolve_name


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


def test_asset_catalog_builds_keys_from_paths(tmp_path: Path) -> None:
    (tmp_path / "shared" / "sfx" / "ui").mkdir(parents=True)
    click = tmp_path / "shared" / "sfx" / "ui" / "menu_click.wav"
    click.write_bytes(b"wav")
    catalog = AssetCatalog.from_directory(tmp_path)

    assert catalog.keys == ("shared/sfx/ui/menu_click",)
    assert catalog.require("shared/sfx/ui/menu_click") == str(click)


def test_asset_catalog_rejects_unknown_keys(tmp_path: Path) -> None:
    catalog = AssetCatalog.from_directory(tmp_path)

    with pytest.raises(ValueError, match="Unknown sound 'beach/music'"):
        catalog.require("beach/music", "sound")


def test_asset_catalog_resolves_optional_and_many(tmp_path: Path) -> None:
    (tmp_path / "maps" / "beach").mkdir(parents=True)
    beach = tmp_path / "maps" / "beach" / "music.wav"
    forest = tmp_path / "maps" / "forest" / "music.wav"
    forest.parent.mkdir(parents=True)
    beach.write_bytes(b"wav")
    forest.write_bytes(b"wav")

    catalog = AssetCatalog.from_directory(tmp_path)

    assert catalog.get(None, "sound") is None
    assert catalog.get("maps/beach/music", "sound") == str(beach)
    assert catalog.many(
        ("maps/beach/music", "maps/forest/music"), "sound"
    ) == [str(beach), str(forest)]


def test_asset_catalog_lists_a_folder(tmp_path: Path) -> None:
    for name in ("maps/beach/music", "maps/beach/sfx/a", "maps/beachy/x"):
        file = tmp_path / f"{name}.wav"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(b"wav")
    catalog = AssetCatalog.from_directory(tmp_path)

    assert catalog.keys_under("maps/beach/") == (
        "maps/beach/music",
        "maps/beach/sfx/a",
    )
    assert catalog.paths_under("Maps/Beach") == [
        str(tmp_path / "maps" / "beach" / "music.wav"),
        str(tmp_path / "maps" / "beach" / "sfx" / "a.wav"),
    ]
    assert catalog.keys_under("maps/none") == ()
