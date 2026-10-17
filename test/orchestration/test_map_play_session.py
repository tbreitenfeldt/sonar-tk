from __future__ import annotations

from pyglet.window import key
import pytest
from pytest_mock import MockerFixture

from sonartk.map_builder import Map2d, MapTile
from sonartk.map_builder.map_2d.map_object.character import Character
from sonartk.orchestration.map_interaction import InteractableObject
from sonartk.orchestration.map_play_session import MapPlaySession
from sonartk.orchestration.map_sound_navigation import TerrainAudioProfile
from sonartk.orchestration.proximity_audio import ProximityAudioEmitter
from sonartk.ui.window import Window
from sonartk.util import Direction

PROFILES = {
    "sand": TerrainAudioProfile(movement_sound_file="sand.wav"),
    "wall": TerrainAudioProfile(
        is_passable=False, movement_sound_file="wall.wav"
    ),
    "unused": TerrainAudioProfile(movement_sound_file="unused.wav"),
}


@pytest.fixture
def sound(mocker: MockerFixture) -> dict[str, object]:
    players = mocker.patch("sonartk.orchestration.map_play_session.Player")
    mocker.patch("sonartk.orchestration.proximity_audio.Player")
    manager = mocker.patch(
        "sonartk.orchestration.map_play_session.sound_manager"
    )
    nav_manager = mocker.patch(
        "sonartk.orchestration.map_sound_navigation.sound_manager"
    )
    prox_manager = mocker.patch(
        "sonartk.orchestration.proximity_audio.sound_manager"
    )
    return {
        "players": players,
        "manager": manager,
        "nav": nav_manager,
        "prox": prox_manager,
    }


def _map2d() -> Map2d:
    map2d = Map2d("test", Character("player", (1, 1), Direction.DOWN))
    sand = MapTile("sand")
    wall = MapTile("wall", is_passable=False)
    for _ in range(4):
        map2d.add_row([sand, sand, sand, wall])
    return map2d


def _session(**kwargs: object) -> MapPlaySession:
    return MapPlaySession(
        window=Window(caption="Test"),
        map2d=_map2d(),
        screen_key="map:test",
        terrain_audio_profiles=PROFILES,
        **kwargs,  # type: ignore[arg-type]
    )


def test_builds_a_grid_over_the_map_at_the_player(sound: dict) -> None:
    session = _session()

    assert (session.grid.width, session.grid.height) == (4, 4)
    assert session.grid.current_coordinates == (1, 1)
    assert session.screen.state_machine.contains("grid")


def test_a_custom_grid_key_is_used(sound: dict) -> None:
    session = _session(grid_key="field")
    assert session.screen.state_machine.contains("field")


def test_terrain_profiles_for_other_maps_are_ignored(sound: dict) -> None:
    session = _session()
    assert "unused" not in session.navigation.sound_map


def test_walking_plays_footsteps_and_blocked_tiles_stop_you(
    sound: dict,
) -> None:
    session = _session()
    play = sound["nav"].play_sound  # type: ignore[attr-defined]

    session.grid.dispatch_event("on_navigation", session.grid, Direction.RIGHT)
    assert session.map2d.character.coordinates == (2, 1)
    assert play.call_args.args[0] == "sand.wav"

    session.grid.dispatch_event("on_navigation", session.grid, Direction.RIGHT)
    assert session.map2d.character.coordinates == (2, 1)
    assert play.call_args.args[0] == "wall.wav"


def test_object_sounds_follow_the_player_and_hook_runs(
    sound: dict, mocker: MockerFixture
) -> None:
    hook = mocker.Mock()
    emitter = ProximityAudioEmitter("hum.wav", (0, 0), max_distance_tiles=3)
    session = _session(object_emitters={"hum": emitter}, on_move_success=hook)
    prox_play = sound["prox"].play_sound  # type: ignore[attr-defined]

    session.grid.dispatch_event("on_navigation", session.grid, Direction.LEFT)

    assert prox_play.call_args.args[0] == "hum.wav"
    assert hook.call_args.args[0] == (0, 1)


def test_move_success_without_a_hook_is_fine(sound: dict) -> None:
    session = _session()
    session.grid.dispatch_event("on_navigation", session.grid, Direction.LEFT)
    assert session.map2d.character.coordinates == (0, 1)


def test_interactables_are_wired_to_the_grid_keys(sound: dict) -> None:
    session = _session(
        interactables=[InteractableObject("sign", (1, 2), ("Hello.",))],
        interact_keys=(key.E,),
    )
    assert session.interaction.nearest() == "sign"
    assert session.interaction.state_keys == {"sign": "map:test:describe:sign"}


def test_start_audio_positions_the_listener_and_starts_sounds(
    sound: dict,
) -> None:
    emitter = ProximityAudioEmitter("hum.wav", (2, 1), max_distance_tiles=3)
    session = _session(object_emitters={"hum": emitter})

    session.start_audio()

    manager = sound["manager"]
    assert manager.listener.position == session.navigation.position_resolver(
        (1, 1)
    )
    assert sound["prox"].play_sound.call_args.args[0] == "hum.wav"  # type: ignore[attr-defined]


def test_start_audio_faces_the_listener_north_with_z_up(sound: dict) -> None:
    _session().start_audio()

    listener = sound["manager"].listener
    assert listener.at_orientation == (0.0, 1.0, 0.0)
    assert listener.up_orientation == (0.0, 0.0, 1.0)


def test_the_listener_orientation_can_be_left_alone(sound: dict) -> None:
    session = _session(listener_orientation=None)
    listener = sound["manager"].listener
    listener.at_orientation = "unchanged"

    session.start_audio()

    assert listener.at_orientation == "unchanged"


def test_stop_audio_releases_object_and_ambient_players(sound: dict) -> None:
    emitter = ProximityAudioEmitter("hum.wav", (2, 1), max_distance_tiles=3)
    session = _session(object_emitters={"hum": emitter})
    object_player = session.objects.players["hum"]
    ambient = session.navigation.ambient_player

    session.stop_audio()

    object_player.stop.assert_called_once_with()  # type: ignore[attr-defined]
    object_player.remove.assert_called_once_with()  # type: ignore[attr-defined]
    ambient.stop.assert_called_once_with()  # type: ignore[union-attr]
    ambient.remove.assert_called_once_with()  # type: ignore[union-attr]


def test_stop_audio_without_an_ambient_player(sound: dict) -> None:
    session = _session()
    session.navigation.ambient_player = None

    session.stop_audio()


def test_locate_key_speaks_the_tile_and_coordinates(
    sound: dict, mocker: MockerFixture
) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_play_session.speech_manager.output"
    )
    session = _session(locate_keys=(key.C,))

    handler = session.grid.key_handler
    handler.activate()
    assert handler.on_key_press(key.C, 0)

    output.assert_called_once_with("sand, x 1, y 1", interrupt=True)


def test_locate_uses_a_custom_tile_description(
    sound: dict, mocker: MockerFixture
) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_play_session.speech_manager.output"
    )
    session = _session(describe_tile=lambda tile: f"<{tile.name}>")

    assert session.speak_location() is True

    output.assert_called_once_with("<sand>, x 1, y 1", interrupt=True)


def test_locate_speaks_height_only_above_level_zero(
    sound: dict, mocker: MockerFixture
) -> None:
    output = mocker.patch(
        "sonartk.orchestration.map_play_session.speech_manager.output"
    )
    session = _session()
    session.map2d.set_elevations({(1, 1): 6})

    session.speak_location()

    output.assert_called_once_with("sand, x 1, y 1, height 6", interrupt=True)


def test_tile_names_are_spoken_with_spaces() -> None:
    from sonartk.orchestration.map_play_session import describe_tile_name

    assert describe_tile_name(MapTile("shallow_water")) == "shallow water"


def test_blend_ambient_is_passed_to_navigation(sound: dict) -> None:
    assert _session(blend_ambient=True).navigation.blend_ambient is True
    assert _session().navigation.blend_ambient is False
