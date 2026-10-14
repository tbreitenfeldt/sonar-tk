from __future__ import annotations

from typing import Any

import pytest
from pytest_mock import MockerFixture

from sonartk.map_builder import (
    DocumentExit,
    DocumentObject,
    MapDocument,
    MapDocumentError,
    MapTile,
)
from sonartk.orchestration.map_definition import (
    MapDefinition,
    MapObjectSpec,
    ObjectSound,
    load_map,
)
from sonartk.orchestration.map_exits import MapExit


def _document(**kwargs: Any) -> MapDocument:
    options: dict[str, Any] = {
        "key": "yard",
        "legend": {"s": "sand"},
        "rows": ("sss", "sss", "sss"),
        "start": (0, 0),
    }
    options.update(kwargs)
    return MapDocument(**options)


def _tile(name: str) -> MapTile:
    return MapTile(name)


def test_from_document_copies_basic_fields() -> None:
    document = _document(music="theme", ambience="wind")

    definition = MapDefinition.from_document(document)

    assert definition.key == "yard"
    assert definition.document is document
    assert definition.start == (0, 0)
    assert definition.music == "theme"
    assert definition.ambience == "wind"
    assert definition.objects == ()
    assert definition.exits == ()


def test_music_and_ambience_are_resolved() -> None:
    document = _document(music="theme", ambience="wind")

    definition = MapDefinition.from_document(
        document,
        resolve_music=str.upper,
        resolve_ambience=lambda name: name[::-1],
    )

    assert definition.music == "THEME"
    assert definition.ambience == "dniw"


def test_missing_music_is_not_resolved() -> None:
    definition = MapDefinition.from_document(
        _document(), resolve_music=str.upper
    )
    assert definition.music is None


def test_unknown_terrain_is_rejected() -> None:
    with pytest.raises(MapDocumentError, match="unknown terrain"):
        MapDefinition.from_document(_document(), known_terrain=["grass"])


def test_known_terrain_is_accepted() -> None:
    MapDefinition.from_document(_document(), known_terrain=["sand"])


def test_exits_become_map_exits() -> None:
    document = _document(exits=(DocumentExit((1, 1), "cabin", (0, 0)),))
    definition = MapDefinition.from_document(document)
    assert definition.exits == (MapExit((1, 1), "cabin", (0, 0)),)


def test_objects_resolve_sound_and_read_descriptions() -> None:
    document = _document(
        objects=(
            DocumentObject(
                "boat",
                (1, 1),
                sound="hum",
                max_distance_tiles=5,
                properties={"description": ["One.", "Two."]},
            ),
            DocumentObject(
                "sign", (2, 2), properties={"description": "Hello."}
            ),
            DocumentObject("rock", (0, 2)),
        )
    )

    definition = MapDefinition.from_document(
        document, resolve_sound=lambda name: f"{name}.wav"
    )

    assert definition.objects == (
        MapObjectSpec(
            "boat", (1, 1), ObjectSound("hum.wav", 5), ("One.", "Two.")
        ),
        MapObjectSpec("sign", (2, 2), None, ("Hello.",)),
        MapObjectSpec("rock", (0, 2), None, ()),
    )


def test_sound_names_are_paths_without_a_resolver() -> None:
    document = _document(
        objects=(DocumentObject("boat", (1, 1), "hum.wav", 5),)
    )
    sound = MapDefinition.from_document(document).objects[0].sound
    assert sound == ObjectSound("hum.wav", 5)


def test_a_sound_needs_a_range() -> None:
    document = _document(objects=(DocumentObject("boat", (1, 1), "hum"),))
    with pytest.raises(ValueError, match="no max_distance_tiles"):
        MapDefinition.from_document(document)


@pytest.mark.parametrize("pages", [5, [1, 2]])
def test_malformed_descriptions_are_rejected(pages: Any) -> None:
    document = _document(
        objects=(
            DocumentObject("sign", (1, 1), properties={"description": pages}),
        )
    )
    with pytest.raises(ValueError, match="description must be text"):
        MapDefinition.from_document(document)


def test_from_file_loads_and_describes(
    tmp_path: Any, mocker: MockerFixture
) -> None:
    document = _document()
    load = mocker.patch(
        "sonartk.orchestration.map_definition.load_map_document",
        return_value=document,
    )

    definition = MapDefinition.from_file(
        tmp_path / "yard.json", resolve_music=str.upper
    )

    load.assert_called_once_with(tmp_path / "yard.json")
    assert definition.key == "yard"


def test_load_map_builds_the_map_exits_and_objects() -> None:
    document = _document(
        objects=(DocumentObject("sign", (1, 1)),),
        exits=(DocumentExit((2, 2), "cabin", (0, 0)),),
    )
    definition = MapDefinition.from_document(document)

    loaded = load_map(definition, _tile)

    assert loaded.map2d.width == 3
    assert loaded.map2d.character.coordinates == (0, 0)
    assert loaded.objects["sign"].coordinates == (1, 1)
    assert loaded.exits.exit_at((2, 2)) == MapExit((2, 2), "cabin", (0, 0))


def test_load_map_honours_a_spawn_override() -> None:
    definition = MapDefinition.from_document(_document())
    loaded = load_map(definition, _tile, spawn=(2, 1))
    assert loaded.map2d.character.coordinates == (2, 1)
