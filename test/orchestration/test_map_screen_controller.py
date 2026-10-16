from __future__ import annotations

from typing import Any, Hashable, Mapping

import pytest
from pyglet.window import key
from pytest_mock import MockerFixture

from sonartk.map_builder import (
    DocumentExit,
    DocumentObject,
    MapDocument,
    MapTile,
)
from sonartk.orchestration import map_sound_navigation as navigation
from sonartk.orchestration.map_definition import MapDefinition, ObjectSound
from sonartk.orchestration.map_screen_controller import MapScreenController
from sonartk.orchestration.map_sound_navigation import TerrainAudioProfile
from sonartk.orchestration.object_types import object_types_from_dict
from sonartk.ui.window import Window
from sonartk.util import Direction

PROFILES = {
    "sand": TerrainAudioProfile(movement_sound_file="sand.wav"),
    "wall": TerrainAudioProfile(
        is_passable=False, movement_sound_file="wall.wav"
    ),
}


@pytest.fixture(autouse=True)
def sound(mocker: MockerFixture) -> None:
    for target in (
        "map_play_session.Player",
        "map_play_session.sound_manager",
        "map_sound_navigation.sound_manager",
        "proximity_audio.sound_manager",
        "proximity_audio.Player",
    ):
        mocker.patch(f"sonartk.orchestration.{target}")


def _tile(name: str) -> MapTile:
    return MapTile(name)


def _definitions() -> Mapping[Hashable, MapDefinition]:
    yard = MapDocument(
        key="yard",
        legend={"s": "sand"},
        rows=("sss", "sss", "sss"),
        start=(0, 0),
        exits=(DocumentExit((1, 0), "cabin", (2, 2)),),
        objects=(
            DocumentObject(
                "sign",
                (2, 2),
                sound="hum.wav",
                max_distance_tiles=4,
                properties={"description": ["A sign."]},
            ),
        ),
        music="yard_theme",
        name="The Yard",
    )
    cabin = MapDocument(
        key="cabin",
        legend={"s": "sand"},
        rows=("ssss",) * 4,
        start=(0, 0),
    )
    return {
        "yard": MapDefinition.from_document(yard),
        "cabin": MapDefinition.from_document(cabin),
    }


def _controller(**kwargs: Any) -> MapScreenController:
    window = Window(caption="Test")
    window.transition_to = lambda *_: None  # type: ignore[method-assign]
    return MapScreenController(
        window,
        _definitions(),
        terrain_audio_profiles=PROFILES,
        tile_factory=_tile,
        **kwargs,
    )


def _step(controller: MapScreenController, direction: Direction) -> None:
    assert controller.session is not None
    grid = controller.session.grid
    grid.dispatch_event("on_navigation", grid, direction)


def test_entering_adds_the_screen_and_builds_a_session() -> None:
    controller = _controller()

    controller.enter("yard")

    assert controller.session is not None
    assert controller.session.screen_key == "map:yard"
    assert controller.window.state_machine.contains("map:yard")
    assert controller.loaded is not None
    assert controller.loaded.definition.key == "yard"


def test_objects_get_emitters_and_interaction() -> None:
    controller = _controller()
    controller.enter("yard")
    session = controller.session
    assert session is not None

    assert session.objects.emitters["sign"].sound_path == "hum.wav"
    assert "map:yard:describe:sign" in session.interaction.state_keys.values()


def test_enter_hook_runs_before_sounds_start() -> None:
    events: list[str] = []
    controller = _controller(
        on_enter=lambda definition, session: events.append(
            f"enter {definition.music}"
        )
    )
    assert controller.session is None
    controller.enter("yard")
    assert events == ["enter yard_theme"]


def test_music_and_ambience_follow_the_active_map() -> None:
    events: list[str] = []
    controller = _controller(
        play_music=lambda music: events.append(f"music {music}"),
        stop_music=lambda: events.append("stop music"),
        play_ambience=lambda ambience: events.append(f"ambience {ambience}"),
        stop_ambience=lambda: events.append("stop ambience"),
        on_leave=lambda d: events.append("leave"),
    )
    controller.enter("yard")
    controller.enter("cabin")

    assert events == [
        "stop music",
        "stop ambience",
        "music yard_theme",
        "stop music",
        "stop ambience",
        "leave",
        "stop music",
        "stop ambience",
    ]


def test_ambience_plays_when_the_map_has_it() -> None:
    played: list[Any] = []
    controller = _controller(play_ambience=played.append)
    definitions = dict(_definitions())
    yard = definitions["yard"]
    definitions["yard"] = MapDefinition(
        key=yard.key,
        document=yard.document,
        start=yard.start,
        ambience="wind",
    )
    controller = MapScreenController(
        controller.window,
        definitions,
        terrain_audio_profiles=PROFILES,
        tile_factory=_tile,
        play_ambience=played.append,
    )
    controller.enter("yard")

    assert played == ["wind"]


def test_leave_hook_and_previous_screen_release() -> None:
    left: list[Any] = []
    controller = _controller(on_leave=lambda d: left.append(d.key))
    controller.enter("yard")
    controller.enter("cabin")

    assert left == ["yard"]
    assert not controller.window.state_machine.contains("map:yard")
    assert controller.window.state_machine.contains("map:cabin")


def test_entering_announces_the_map_name(mocker: MockerFixture) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_screen_controller.speech_manager.output"
    )
    controller = _controller()

    controller.enter("yard")
    controller.enter("cabin")

    output.assert_called_once_with("The Yard", interrupt=True)


def test_name_announcement_can_be_disabled(mocker: MockerFixture) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_screen_controller.speech_manager.output"
    )

    _controller(announce_map_name=False).enter("yard")

    output.assert_not_called()


def test_name_key_speaks_the_map_name(mocker: MockerFixture) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_play_session.speech_manager.output"
    )
    controller = _controller(name_keys=(key.M,), announce_map_name=False)
    controller.enter("yard")
    assert controller.session is not None
    handler = controller.session.grid.key_handler
    handler.activate()

    assert handler.on_key_press(key.M, 0)
    output.assert_called_once_with("The Yard", interrupt=True)

    output.reset_mock()
    controller.enter("cabin")
    assert controller.session is not None
    handler = controller.session.grid.key_handler
    handler.activate()
    assert handler.on_key_press(key.M, 0)
    output.assert_not_called()


def test_hooks_are_optional() -> None:
    controller = _controller()
    controller.enter("yard")
    controller.enter("cabin")
    assert controller.switcher.current_key == "cabin"


def test_stepping_on_an_exit_switches_maps() -> None:
    controller = _controller()
    controller.enter("yard")

    _step(controller, Direction.RIGHT)

    assert controller.switcher.current_key == "cabin"
    assert controller.session is not None
    assert controller.session.map2d.character.coordinates == (2, 2)


def test_ordinary_steps_stay_on_the_map() -> None:
    controller = _controller()
    controller.enter("yard")
    _step(controller, Direction.UP)
    assert controller.switcher.current_key == "yard"


def test_move_success_before_any_map_is_ignored() -> None:
    controller = _controller()
    controller._on_move_success((0, 0), MapTile("sand"))


def test_unknown_maps_are_rejected() -> None:
    with pytest.raises(KeyError):
        _controller().enter("nowhere")


def test_session_options_are_passed_through(mocker: MockerFixture) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_play_session.speech_manager.output"
    )
    pages: list[int] = []
    controller = _controller(
        on_page_change=lambda state, index: pages.append(index),
        interact_keys=(key.E,),
        locate_keys=(key.C,),
        blend_ambient=True,
        announce_map_name=False,
        describe_tile=lambda tile: "tile",
    )
    controller.enter("yard")
    session = controller.session
    assert session is not None

    assert session.navigation.blend_ambient is True
    assert session.describe_tile(MapTile("sand")) == "tile"
    handler = session.grid.key_handler
    handler.activate()
    assert handler.on_key_press(key.C, 0)
    output.assert_called_once_with("tile, x 0, y 0", interrupt=True)


def test_exit_sound_marks_every_exit_tile() -> None:
    controller = _controller(exit_sound=ObjectSound("door.wav", 9, 0.5))

    controller.enter("yard")

    session = controller.session
    assert session is not None
    emitter = session.objects.emitters["exit:0"]
    assert emitter.sound_path == "door.wav"
    assert emitter.source_coordinates == (1, 0)
    assert emitter.max_distance_tiles == 9
    assert emitter.base_volume == 0.5

    plain = _controller()
    plain.enter("yard")
    assert plain.session is not None
    assert "exit:0" not in plain.session.objects.emitters


def test_returning_to_a_map_does_not_collide_with_released_states() -> None:
    controller = _controller()
    controller.enter("yard")
    controller.enter("cabin")

    assert not controller.window.state_machine.contains("map:yard")
    assert not controller.window.state_machine.contains(
        "map:yard:describe:sign"
    )

    controller.enter("yard")

    assert controller.window.state_machine.contains("map:yard:describe:sign")


def _log_controller() -> MapScreenController:
    kinds = object_types_from_dict(
        {
            "log": {
                "footprint": [[0, 0], [1, 0]],
                "collision_sound": "thud.wav",
                "side_sounds": {"north": "north.wav"},
                "loop": {"sound": "creak.wav", "max_distance_tiles": 9},
                "description": ["A log."],
            }
        }
    )
    yard = MapDocument(
        key="yard",
        legend={"s": "sand"},
        rows=("sssss",) * 5,
        start=(0, 0),
        objects=(DocumentObject("log", (2, 2), type="log"),),
    )
    window = Window(caption="Test")
    window.transition_to = lambda *_: None  # type: ignore[method-assign]
    return MapScreenController(
        window,
        {"yard": MapDefinition.from_document(yard, object_types=kinds)},
        terrain_audio_profiles=PROFILES,
        tile_factory=_tile,
    )


def _play_sound() -> Any:
    return navigation.sound_manager.play_sound


def _sounds_played() -> list[str]:
    return [call.args[0] for call in _play_sound().call_args_list]


def test_a_typed_object_blocks_with_its_collision_sound() -> None:
    controller = _log_controller()
    controller.enter("yard", spawn=(1, 2))
    _play_sound().reset_mock()

    _step(controller, Direction.RIGHT)

    assert _sounds_played() == ["thud.wav"]


def test_a_typed_object_plays_a_sound_per_side() -> None:
    controller = _log_controller()
    controller.enter("yard", spawn=(3, 3))
    _play_sound().reset_mock()

    _step(controller, Direction.DOWN)

    assert _sounds_played() == ["north.wav"]


def test_a_typed_object_is_one_loop_examined_from_any_tile() -> None:
    controller = _log_controller()
    controller.enter("yard", spawn=(3, 3))
    session = controller.session
    assert session is not None

    emitter = session.objects.emitters["log"]
    assert emitter.footprint == ((2, 2), (3, 2))
    assert emitter.sound_path == "creak.wav"
    assert session.interaction.nearest() == "log"
