from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class IntroGameAudioLifecycle:
    """Coordinate intro-state silence and game-state audio startup.

    This helper keeps intro scenes quiet while still allowing game audio
    (music + ambience) to start together when intro exits.
    """

    stop_intro_audio: Callable[[], None]
    start_game_music: Callable[[], None]
    start_game_ambience: Callable[[], None]

    def prepare_intro(self) -> None:
        """Stop long-running ambience/music while intro audio is active."""
        self.stop_intro_audio()

    def start_game_audio(self) -> None:
        """Start game-state music and ambience together."""
        self.start_game_music()
        self.start_game_ambience()
