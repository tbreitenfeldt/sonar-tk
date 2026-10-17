import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from sonartk.map_builder.map_2d.map_document import (
    DocumentExit,
    DocumentObject,
    MapDocument,
    MapDocumentError,
    build_map2d_from_document,
    load_map_document,
    save_map_document,
)
from sonartk.map_builder.map_2d.map_tile import MapTile
from sonartk.orchestration.map_exits import MapExit, MapExitRegistry
from sonartk.util import Direction


def tile_factory(terrain: str) -> MapTile:
    return MapTile(terrain, is_passable=terrain != "sea")


def make_document(**overrides: Any) -> MapDocument:
    values: dict[str, Any] = {
        "key": "cove",
        "legend": {"~": "sea", "s": "sand"},
        "rows": ("~~~~", "~ss~", "ssss"),
        "start": (1, 0),
        "objects": (
            DocumentObject("boat", (2, 1), "boat_loop", 12, {"k": 1}),
            DocumentObject("rock", (0, 0)),
        ),
        "exits": (DocumentExit((3, 0), "cave", (0, 5)),),
        "music": "calm",
        "ambience": "wind",
        "properties": {"theme": "beach"},
    }
    values.update(overrides)
    return MapDocument(**values)


class TestDocument:
    def test_dimensions_and_lookup_use_north_first_rows(self) -> None:
        document = make_document()
        assert (document.width, document.height) == (4, 3)
        assert document.code_at((0, 2)) == "~"
        assert document.terrain_at((1, 1)) == "sand"
        assert document.terrain_at((0, 0)) == "sand"
        assert document.terrain_at((3, 1)) == "sea"

    def test_code_at_rejects_outside(self) -> None:
        with pytest.raises(IndexError):
            make_document().code_at((4, 0))

    def test_dict_round_trip(self) -> None:
        document = make_document()
        assert MapDocument.from_dict(document.to_dict()) == document

    def test_file_round_trip_writes_one_row_per_line(
        self, tmp_path: Path
    ) -> None:
        document = make_document()
        path = tmp_path / "cove.json"
        save_map_document(document, path)
        assert load_map_document(path) == document
        lines = path.read_text(encoding="utf-8").splitlines()
        assert any(line.strip() == '"~~~~",' for line in lines)

    def test_exit_sound_round_trips_and_is_omitted_when_unset(self) -> None:
        plain = DocumentExit((3, 0), "cave", (0, 5))
        loud = DocumentExit((3, 0), "cave", (0, 5), "door")
        for exit_ in (plain, loud):
            document = make_document(exits=(exit_,))
            data = document.to_dict()
            assert ("sound" in data["exits"][0]) is (exit_.sound is not None)
            assert MapDocument.from_dict(data).exits == (exit_,)

    def test_name_round_trips(self) -> None:
        document = MapDocument(
            key="a", legend={"s": "sand"}, rows=("s",), start=(0, 0), name="A"
        )

        assert MapDocument.from_dict(document.to_dict()).name == "A"
        assert "name" not in replace(document, name=None).to_dict()

    def test_optional_fields_default(self) -> None:
        data = {
            "key": "k",
            "legend": {"s": "sand"},
            "rows": ["ss"],
            "start": [0, 0],
        }
        document = MapDocument.from_dict(data)
        assert document.objects == ()
        assert document.exits == ()
        assert document.music is None
        assert document.properties == {}

    def test_unparsable_json_is_reported(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("{nope", encoding="utf-8")
        with pytest.raises(MapDocumentError, match="not valid JSON"):
            load_map_document(path)

    @pytest.mark.parametrize(
        "change, message",
        [
            ({"key": ""}, "non-empty"),
            ({"rows": ()}, "non-empty strings"),
            ({"rows": ("~~", "")}, "non-empty strings"),
            ({"rows": ("~~~~", "~~")}, "Row 1 has width 2"),
            ({"rows": ("~~~~", "~x~~")}, "missing from the legend"),
            ({"legend": {"ab": "sea", "~": "sea", "s": "sand"}}, "single"),
            ({"legend": {"~": "", "s": "sand"}}, "terrain name"),
            ({"start": (9, 0)}, "start position"),
            ({"start": (0, -1)}, "start position"),
            ({"version": 2}, "Unsupported"),
            (
                {
                    "objects": (
                        DocumentObject("a", (0, 0)),
                        DocumentObject("a", (1, 0)),
                    )
                },
                "Duplicate object",
            ),
            ({"objects": (DocumentObject("a", (9, 9)),)}, "object 'a'"),
            (
                {"objects": (DocumentObject("a", (0, 0), "s", -1),)},
                "max_distance_tiles",
            ),
            (
                {
                    "exits": (
                        DocumentExit((0, 0), "a", (0, 0)),
                        DocumentExit((0, 0), "b", (0, 0)),
                    )
                },
                "Duplicate exit",
            ),
            ({"exits": (DocumentExit((9, 0), "a", (0, 0)),)}, "exit position"),
        ],
    )
    def test_validation_rejects(
        self, change: dict[str, Any], message: str
    ) -> None:
        with pytest.raises(MapDocumentError, match=message):
            make_document(**change)

    @pytest.mark.parametrize(
        "mutate, message",
        [
            (lambda d: d.pop("key"), "Missing required field 'key'"),
            (lambda d: d.update(version=9), "Unsupported map document"),
            (lambda d: d.update(start=[1]), "two integers"),
            (lambda d: d.update(start=[1, "a"]), "two integers"),
            (lambda d: d.update(start=[True, 0]), "two integers"),
            (lambda d: d.update(start="ab"), "two integers"),
            (lambda d: d.update(objects=[{"name": "x"}]), "'at'"),
            (lambda d: d.update(exits=[{"at": [0, 0]}]), "target_map"),
            (lambda d: d.update(legend=5), "Malformed"),
        ],
    )
    def test_from_dict_rejects_malformed(
        self, mutate: Any, message: str
    ) -> None:
        data = make_document().to_dict()
        mutate(data)
        with pytest.raises(MapDocumentError, match=message):
            MapDocument.from_dict(data)

    def test_from_dict_requires_an_object(self) -> None:
        with pytest.raises(MapDocumentError, match="JSON object"):
            MapDocument.from_dict([])  # type: ignore[arg-type]


class TestBuildMap:
    def test_tiles_land_at_the_documented_coordinates(self) -> None:
        map2d = build_map2d_from_document(make_document(), tile_factory)
        assert (map2d.width, map2d.height) == (4, 3)
        assert map2d.get_tile((0, 2)).name == "sea"
        assert map2d.get_tile((1, 1)).name == "sand"
        assert map2d.get_tile((3, 1)).name == "sea"
        assert not map2d.get_tile((0, 2)).is_passable

    def test_character_objects_and_sharing(self) -> None:
        map2d = build_map2d_from_document(
            make_document(), tile_factory, orientation=Direction.UP
        )
        assert map2d.character.coordinates == (1, 0)
        assert map2d.character.name == "player"
        assert map2d.character.directional_orientation is Direction.UP
        boat = map2d.get_map_object_at((2, 1))
        assert boat is not None
        assert boat.name == "boat"
        assert map2d.get_tile((0, 0)) is map2d.get_tile((3, 0))

    def test_factory_called_once_per_terrain(self) -> None:
        calls: list[str] = []

        def factory(terrain: str) -> MapTile:
            calls.append(terrain)
            return tile_factory(terrain)

        build_map2d_from_document(make_document(), factory)
        assert sorted(calls) == ["sand", "sea"]

    def test_spawn_overrides_start_and_is_checked(self) -> None:
        document = make_document()
        map2d = build_map2d_from_document(
            document, tile_factory, spawn=(2, 0), character_name="hero"
        )
        assert map2d.character.coordinates == (2, 0)
        assert map2d.character.name == "hero"
        with pytest.raises(MapDocumentError, match="outside"):
            build_map2d_from_document(document, tile_factory, spawn=(9, 9))
        with pytest.raises(MapDocumentError, match="not passable"):
            build_map2d_from_document(document, tile_factory, spawn=(0, 2))


def test_exit_registry_from_document() -> None:
    registry = MapExitRegistry.from_document(make_document())
    assert len(registry) == 1
    assert registry.exit_at((3, 0)) == MapExit((3, 0), "cave", (0, 5))
    assert registry.exit_at((0, 0)) is None


def test_saved_json_is_plain_data(tmp_path: Path) -> None:
    path = tmp_path / "m.json"
    save_map_document(make_document(), path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["rows"][0] == "~~~~"
    assert data["exits"][0] == {
        "at": [3, 0],
        "target_map": "cave",
        "target_at": [0, 5],
    }


def test_require_terrain_accepts_known_terrain() -> None:
    make_document().require_terrain(["sea", "sand", "rock"])


def test_require_terrain_names_the_unknown_terrain() -> None:
    with pytest.raises(MapDocumentError, match="'cove' uses unknown.*sea"):
        make_document().require_terrain(["sand"])
