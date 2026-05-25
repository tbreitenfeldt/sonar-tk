from sonartk.orchestration.audio_lifecycle import IntroGameAudioLifecycle


def test_prepare_intro_stops_intro_time_audio() -> None:
    calls: list[str] = []
    lifecycle = IntroGameAudioLifecycle(
        stop_intro_audio=lambda: calls.append("stop"),
        start_game_music=lambda: calls.append("music"),
        start_game_ambience=lambda: calls.append("ambience"),
    )

    lifecycle.prepare_intro()

    assert calls == ["stop"]


def test_start_game_audio_starts_music_and_ambience() -> None:
    calls: list[str] = []
    lifecycle = IntroGameAudioLifecycle(
        stop_intro_audio=lambda: calls.append("stop"),
        start_game_music=lambda: calls.append("music"),
        start_game_ambience=lambda: calls.append("ambience"),
    )

    lifecycle.start_game_audio()

    assert calls == ["music", "ambience"]
