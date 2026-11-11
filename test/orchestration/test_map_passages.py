from unittest.mock import Mock, call
from typing import Any, NoReturn

import pytest

from sonartk.map_builder import DocumentExit, MapDocument, MapDocumentError
from sonartk.orchestration import (
    MapPassage,
    ObjectSound,
    expand_passages,
    parse_map_passages,
    passage_exit_emitters,
)
from sonartk.orchestration.map_definition import MapDefinition
from sonartk.orchestration.map_exits import MapExit
from sonartk.orchestration.proximity_audio import (
    ProximityAudioController,
    ProximityAudioEmitter,
)


def passage(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "area": [1, 0, 3, 0],
        "target_map": "other",
        "target_at": [4, 2],
        "transition_sound": "door",
        "beacon": {"sound": "bell", "range": 8, "volume": 0.6},
    }
    data.update(overrides)
    return data


def document(
    *passages: Any, exits: tuple[DocumentExit, ...] = ()
) -> MapDocument:
    return MapDocument(
        key="test",
        legend={"s": "sand"},
        rows=("sssss",) * 5,
        start=(0, 0),
        exits=exits,
        properties={"passages": list(passages)},
    )


def test_parses_rectangle_and_resolves_sounds_without_resolving_exit_twice() -> (
    None
):
    resolve = Mock(side_effect=lambda name, label: f"resolved/{name}")
    doc = document(passage(area=[1, 0, 2, 1]))
    (component,) = parse_map_passages(doc, resolve_sound=resolve)

    assert component.tiles == ((1, 0), (2, 0), (1, 1), (2, 1))
    assert component.beacon == ObjectSound("resolved/bell", 8, 0.6)
    assert component.transition_sound == "door"
    assert resolve.call_args_list == [
        call("bell", "beacon sound"),
        call("door", "transition sound"),
    ]
    expanded = expand_passages(doc, (component,))
    definition = MapDefinition.from_document(
        expanded, resolve_sound=lambda name: f"resolved/{name}"
    )
    assert {exit.coordinates for exit in definition.exits} == set(
        component.tiles
    )
    assert all(exit.sound == "resolved/door" for exit in definition.exits)
    assert all(
        (exit.target_map, exit.target_coordinates) == ("other", (4, 2))
        for exit in definition.exits
    )


def test_optional_defaults_and_no_passages() -> None:
    doc = document(
        passage(transition_sound=None, beacon={"sound": "bell", "range": 3})
    )
    (component,) = parse_map_passages(doc)
    assert component.beacon == ObjectSound("bell", 3, 1.0)
    assert component.transition_sound is None
    assert parse_map_passages(document()) == ()
    assert (
        parse_map_passages(
            MapDocument(
                key="x", legend={"s": "sand"}, rows=("s",), start=(0, 0)
            )
        )
        == ()
    )


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        passage(area=[0, 0, 1]),
        passage(area=[0, 0, 1.0, 1]),
        passage(area=[0, 0, True, 1]),
        passage(area=[2, 0, 1, 0]),
        passage(area=[0, 2, 0, 1]),
        passage(area=[-1, 0, 1, 0]),
        passage(area=[0, 0, 5, 0]),
        passage(target_map=""),
        passage(target_map=1),
        passage(target_at=[0]),
        passage(beacon=None),
        passage(beacon={"sound": "", "range": 1}),
        passage(beacon={"sound": "bell", "range": True}),
        passage(beacon={"sound": "bell", "range": 0}),
        passage(beacon={"sound": "bell", "range": 1.5}),
        passage(beacon={"sound": "bell", "range": 1, "volume": True}),
        passage(beacon={"sound": "bell", "range": 1, "volume": -1}),
        passage(beacon={"sound": "bell", "range": 1, "volume": 2}),
        passage(beacon={"sound": "bell", "range": 1, "volume": float("nan")}),
        passage(transition_sound=""),
    ],
)
def test_invalid_passages_are_rejected(bad: Any) -> None:
    with pytest.raises(MapDocumentError):
        parse_map_passages(document(bad))


def test_passages_property_must_be_a_list() -> None:
    doc = document()
    doc.properties["passages"] = "invalid"
    with pytest.raises(MapDocumentError, match="must be a list"):
        parse_map_passages(doc)


def test_resolver_errors_are_propagated() -> None:
    def fail(name: str, label: str) -> NoReturn:
        raise ValueError(f"{label}: {name}")

    with pytest.raises(ValueError, match="beacon sound: bell"):
        parse_map_passages(document(passage()), resolve_sound=fail)


def test_expansion_preserves_ordinary_exits_and_is_idempotent() -> None:
    legacy = DocumentExit((4, 4), "legacy", (0, 0))
    doc = document(passage(), exits=(legacy,))
    passages = parse_map_passages(doc)
    expanded = expand_passages(doc, passages)

    assert doc.exits == (legacy,)
    assert expanded.exits == (legacy,) + passages[0].exits()
    assert expand_passages(expanded, passages) == expanded


def test_expand_rejects_overlaps_conflicts_and_out_of_bounds() -> None:
    doc = document(passage(), passage())
    with pytest.raises(MapDocumentError, match="Overlapping passages"):
        expand_passages(doc, parse_map_passages(doc))
    doc = document(passage(), exits=(DocumentExit((1, 0), "wrong", (0, 0)),))
    with pytest.raises(MapDocumentError, match="conflicts"):
        expand_passages(doc, parse_map_passages(doc))
    bad = MapPassage(((10, 0),), "other", (0, 0), ObjectSound("a", 1))
    with pytest.raises(MapDocumentError, match="outside"):
        expand_passages(document(), (bad,))
    with pytest.raises(ValueError, match="at least one tile"):
        MapPassage((), "other", (0, 0), ObjectSound("a", 1))


def test_beacon_uses_one_player_and_tracks_nearest_tile() -> None:
    (component,) = parse_map_passages(document(passage()))
    emitter = component.emitter()
    player = Mock()
    player.playing.return_value = True
    service = Mock()
    controller = ProximityAudioController(
        emitters={"passage": emitter},
        players={"passage": player},
        position_resolver=lambda tile: (*tile, 0),
        sound_service=service,
    )
    assert emitter.footprint == component.tiles
    assert emitter.start_offset == 0
    for x in (1, 2, 3):
        assert controller.update_at((x, 1)) == {"passage": True}
        actual = service.play_sound.call_args
        assert actual.kwargs["position"] == (x, 0, 0)
        assert actual.kwargs["player"] is player
        assert actual.kwargs["loop"] is True
        assert actual.kwargs["retrigger_if_same"] is False
        assert actual.kwargs["volume"] == pytest.approx(0.6 * 7 / 8)
    assert service.play_sound.call_count == 3
    assert controller.update_at((12, 0)) == {"passage": False}
    player.stop.assert_called_once()


def test_passage_emitters_replace_only_their_exit_tiles() -> None:
    doc = document(
        passage(),
        passage(area=[0, 3, 1, 3], transition_sound=None),
        exits=(DocumentExit((4, 4), "legacy", (0, 0)),),
    )
    passages = parse_map_passages(doc)
    definition = MapDefinition.from_document(expand_passages(doc, passages))
    old = {
        f"exit:{i}": ProximityAudioEmitter("old", e.coordinates, 2)
        for i, e in enumerate(definition.exits)
    }
    old["object"] = ProximityAudioEmitter("object", (0, 0), 2)
    result = passage_exit_emitters(definition.exits, passages, old)
    assert set(result) == {"object", "exit:0", "exit:1", "exit:4"}
    assert result["exit:0"] is old["exit:0"]
    assert result["object"] is old["object"]
    assert result["exit:1"].footprint == passages[0].tiles
    assert result["exit:4"].footprint == passages[1].tiles
    assert len(old) == 7


def test_passage_emitters_reject_missing_duplicate_or_overlapping_tiles() -> (
    None
):
    (component,) = parse_map_passages(document(passage()))
    exits = [MapExit(tile, "other", (4, 2)) for tile in component.tiles]
    with pytest.raises(ValueError, match="No exit registered"):
        passage_exit_emitters(exits[:-1], [component], {})
    with pytest.raises(ValueError, match="Duplicate exit"):
        passage_exit_emitters(exits + exits[:1], [component], {})
    with pytest.raises(ValueError, match="Overlapping passages"):
        passage_exit_emitters(exits, [component, component], {})
    exits[0] = MapExit(component.tiles[0], "wrong", (4, 2))
    with pytest.raises(ValueError, match="conflicts with passage"):
        passage_exit_emitters(exits, [component], {})
