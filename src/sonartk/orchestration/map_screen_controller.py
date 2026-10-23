from __future__ import annotations

from typing import Any, Callable, Hashable, Mapping, Optional

from sonartk.map_builder import MapTile
from sonartk.orchestration.map_definition import (
    LoadedMap,
    MapDefinition,
    ObjectSound,
    load_map,
)
from sonartk.orchestration.map_exits import MapSwitcher
from sonartk.orchestration.map_interaction import (
    DEFAULT_INTERACT_KEYS,
    InteractableObject,
)
from sonartk.orchestration.map_play_session import (
    DEFAULT_ARROW_KEY_REPEAT_SECONDS,
    MapPlaySession,
    describe_tile_name,
)
from sonartk.orchestration.map_sound_navigation import TerrainAudioProfile
from sonartk.orchestration.object_types import object_tile_name
from sonartk.orchestration.paged_text_state import PagedTextState
from sonartk.orchestration.proximity_audio import ProximityAudioEmitter
from sonartk.sound import sound_manager
from sonartk.ui.window import Window
from sonartk.util import Coordinates, speech_manager


class MapScreenController:
    """Plays whichever of several data-driven maps is active.

    Registers each ``MapDefinition`` with a ``MapSwitcher``. Entering a map
    builds a fresh ``MapPlaySession``, adds its screen to the window and
    moves onto it, releases the previous screen, then starts the sounds.
    Stepping on an exit tile switches maps. Game-specific work such as music
    is supplied through ``on_enter`` and ``on_leave``. Music and ambience can
    be handled by passing ``play_music``, ``stop_music``, ``play_ambience``
    and ``stop_ambience``.

    Args:
        window: Window the map screens are added to.
        definitions: Map definitions by map key; exits refer to these keys.
        terrain_audio_profiles: Terrain name to audio configuration.
        tile_factory: Builds a tile from a legend terrain name.
        on_enter: Called as ``(definition, session)`` once the map's screen
            is active, just before the session's sounds start.
        on_leave: Called with the definition of the map being left, before
            its sounds are stopped.
        play_music: Called with a map's ``music`` value when the map is
            entered, if the map has music.
        stop_music: Called when a map is left, before ``on_leave``, and again
            on entry so sound from an earlier screen does not carry over.
        play_ambience: Like ``play_music``, for the map's ``ambience``.
        stop_ambience: Like ``stop_music``, for ambience.
        on_page_change: Called when an object description advances.
        interact_keys: Keys that examine objects.
        interact_reach_tiles: How far away objects can be examined.
        arrow_key_repeat_interval: Seconds between repeats of a held arrow.
        blend_ambient: Play every distinct ambient sound at once.
        proximity_glide_seconds: Seconds object loops and tile ambients take
            to glide to their new position after each step, instead of
            jumping.
        locate_keys: Keys that speak the current tile and coordinates.
        name_keys: Keys that speak the current map's name.
        describe_tile: Turns a tile into the text spoken for it.
        announce_map_name: Speak the map's name each time it is entered.
        exit_sound: If given, every exit tile gives off this looping
            sound in sync, so the tiles read as one source and exits can be
            found by ear. Exits that have their own sound (a door) do not
            give it off.
        door_beacon: If given, every exit that has its own sound (a door)
            gives off this looping sound, so doors can be found by ear
            without being mistaken for ordinary exits.
    """

    def __init__(
        self,
        window: Window,
        definitions: Mapping[Hashable, MapDefinition],
        *,
        terrain_audio_profiles: Mapping[str, TerrainAudioProfile],
        tile_factory: Callable[[str], MapTile],
        on_enter: Optional[
            Callable[[MapDefinition, MapPlaySession], None]
        ] = None,
        on_leave: Optional[Callable[[MapDefinition], None]] = None,
        play_music: Optional[Callable[[Any], None]] = None,
        stop_music: Optional[Callable[[], None]] = None,
        play_ambience: Optional[Callable[[Any], None]] = None,
        stop_ambience: Optional[Callable[[], None]] = None,
        on_page_change: Optional[Callable[[PagedTextState, int], None]] = None,
        interact_keys: tuple[int, ...] = DEFAULT_INTERACT_KEYS,
        interact_reach_tiles: int = 1,
        arrow_key_repeat_interval: float = DEFAULT_ARROW_KEY_REPEAT_SECONDS,
        blend_ambient: bool = False,
        proximity_glide_seconds: float = 0.0,
        locate_keys: tuple[int, ...] = (),
        name_keys: tuple[int, ...] = (),
        describe_tile: Callable[[MapTile], str] = describe_tile_name,
        exit_sound: Optional[ObjectSound] = None,
        door_beacon: Optional[ObjectSound] = None,
        announce_map_name: bool = True,
    ) -> None:
        self.window = window
        self.terrain_audio_profiles = terrain_audio_profiles
        self.tile_factory = tile_factory
        self.on_enter = on_enter
        self.on_leave = on_leave
        self.play_music = play_music
        self.stop_music = stop_music
        self.play_ambience = play_ambience
        self.stop_ambience = stop_ambience
        self.on_page_change = on_page_change
        self.interact_keys = interact_keys
        self.interact_reach_tiles = interact_reach_tiles
        self.arrow_key_repeat_interval = arrow_key_repeat_interval
        self.blend_ambient = blend_ambient
        self.proximity_glide_seconds = proximity_glide_seconds
        self.locate_keys = locate_keys
        self.name_keys = name_keys
        self.describe_tile = describe_tile
        self.exit_sound = exit_sound
        self.door_beacon = door_beacon
        self.announce_map_name = announce_map_name
        self.switcher: MapSwitcher[LoadedMap] = MapSwitcher()
        for map_key, definition in definitions.items():
            self.switcher.register(map_key, self._loader(definition))
        self.switcher.push_handlers(
            on_map_leave=self._on_map_leave,
            on_map_enter=self._on_map_enter,
        )
        self.session: Optional[MapPlaySession] = None
        self.loaded: Optional[LoadedMap] = None

    def _loader(
        self, definition: MapDefinition
    ) -> Callable[[Optional[Coordinates]], LoadedMap]:
        def load(spawn: Optional[Coordinates]) -> LoadedMap:
            return load_map(definition, self.tile_factory, spawn)

        return load

    def enter(
        self, key: Hashable, spawn: Optional[Coordinates] = None
    ) -> None:
        """Make a map active and move the window onto its screen."""
        self.switcher.switch_to(key, spawn)

    def replace_definition(
        self, key: Hashable, definition: MapDefinition
    ) -> None:
        """Use a new definition the next time the map is entered.

        This lets a game reload a map file while it runs. The active map is
        unchanged until it is entered again.
        """
        self.switcher.register(key, self._loader(definition), replace=True)

    def _on_map_leave(self, key: Hashable, loaded: LoadedMap) -> None:
        if self.stop_music is not None:
            self.stop_music()
        if self.stop_ambience is not None:
            self.stop_ambience()
        if self.on_leave is not None:
            self.on_leave(loaded.definition)
        if self.session is not None:
            self.session.stop_audio()

    def _on_map_enter(
        self,
        key: Hashable,
        loaded: LoadedMap,
        spawn: Optional[Coordinates],
    ) -> None:
        previous = self.session
        self.loaded = loaded
        if previous is not None and previous.screen_key == (
            f"map:{loaded.definition.key}"
        ):
            # Re-entering the same map: free its keys before adding again.
            previous.release()
            previous = None
        session = self.session = self._build_session(loaded)
        self.window.add(session.screen_key, session.screen)
        self.window.transition_to(session.screen_key)
        if previous is not None:
            previous.release()
        definition = loaded.definition
        if self.stop_music is not None:
            self.stop_music()
        if self.stop_ambience is not None:
            self.stop_ambience()
        if self.play_music is not None and definition.music is not None:
            self.play_music(definition.music)
        if self.play_ambience is not None and definition.ambience is not None:
            self.play_ambience(definition.ambience)
        if self.on_enter is not None:
            self.on_enter(definition, session)
        if self.announce_map_name and loaded.definition.name:
            speech_manager.output(loaded.definition.name, interrupt=True)
        session.start_audio()

    def _build_session(self, loaded: LoadedMap) -> MapPlaySession:
        specs = loaded.definition.objects
        blocking = [spec for spec in specs if spec.blocking]
        return MapPlaySession(
            window=self.window,
            map2d=loaded.map2d,
            screen_key=f"map:{loaded.definition.key}",
            terrain_audio_profiles={
                **self.terrain_audio_profiles,
                **{
                    object_tile_name(spec.name): TerrainAudioProfile(
                        is_passable=False,
                        movement_sound_file=spec.collision_sound,
                    )
                    for spec in blocking
                },
            },
            blocked_side_sounds={
                object_tile_name(spec.name): spec.side_sounds
                for spec in blocking
                if spec.side_sounds
            },
            object_emitters={
                **{
                    spec.name: ProximityAudioEmitter(
                        sound_path=spec.sound.sound_file,
                        source_coordinates=spec.coordinates,
                        max_distance_tiles=spec.sound.max_distance_tiles,
                        base_volume=spec.sound.volume,
                        footprint=spec.footprint,
                    )
                    for spec in specs
                    if spec.sound is not None
                },
                **self._exit_emitters(loaded),
            },
            interactables=[
                InteractableObject(
                    spec.name,
                    spec.coordinates,
                    spec.description,
                    spec.footprint,
                )
                for spec in specs
            ],
            on_move_success=self._on_move_success,
            on_page_change=self.on_page_change,
            interact_keys=self.interact_keys,
            interact_reach_tiles=self.interact_reach_tiles,
            arrow_key_repeat_interval=self.arrow_key_repeat_interval,
            blend_ambient=self.blend_ambient,
            proximity_glide_seconds=self.proximity_glide_seconds,
            locate_keys=self.locate_keys,
            name_keys=self.name_keys,
            map_name=loaded.definition.name,
            describe_tile=self.describe_tile,
        )

    def _exit_emitters(
        self, loaded: LoadedMap
    ) -> dict[str, ProximityAudioEmitter]:
        emitters: dict[str, ProximityAudioEmitter] = {}
        for index, map_exit in enumerate(loaded.definition.exits):
            sound = (
                self.exit_sound if map_exit.sound is None else self.door_beacon
            )
            if sound is not None:
                emitters[f"exit:{index}"] = ProximityAudioEmitter(
                    sound_path=sound.sound_file,
                    source_coordinates=map_exit.coordinates,
                    max_distance_tiles=sound.max_distance_tiles,
                    base_volume=sound.volume,
                )
        return emitters

    def _on_move_success(
        self, coordinates: Coordinates, tile: MapTile
    ) -> None:
        if self.loaded is not None:
            map_exit = self.loaded.exits.exit_at(coordinates)
            if map_exit is not None and map_exit.sound is not None:
                sound_manager.play_sound(map_exit.sound)
            self.switcher.try_exit(self.loaded.exits, coordinates)
