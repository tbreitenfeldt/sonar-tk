from typing import cast
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from sonartk.sound.player_pool import PlayerPool


@pytest.fixture
def player_factory(
    mocker: MockerFixture,
) -> tuple[MagicMock, list[MagicMock]]:
    """Patch Player constructor and return created mock players."""
    created_players: list[MagicMock] = []

    def make_player() -> MagicMock:
        player = cast(MagicMock, mocker.MagicMock())
        created_players.append(player)
        return player

    player_ctor = cast(
        MagicMock,
        mocker.patch(
            "sonartk.sound.player_pool.Player", side_effect=make_player
        ),
    )
    return player_ctor, created_players


@pytest.fixture
def player_pool(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> PlayerPool:
    """Create a PlayerPool with mocked Player instances."""
    _, _ = player_factory
    return PlayerPool()


# Initialization Tests


def test_init_sets_default_configuration(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> None:
    """Test that __init__ sets default pool configuration values."""
    _, _ = player_factory
    pool = PlayerPool()

    assert pool.idle_player_pool_size == 15
    assert pool.max_pool_size == 256
    assert pool.pool_expansion_count == 10
    assert pool.min_remaining_idle_players == 2
    assert pool.total_allocated_players == 15


def test_init_creates_initial_idle_players(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> None:
    """Test that __init__ creates the initial idle player pool."""
    player_ctor, created_players = player_factory
    pool = PlayerPool()

    assert player_ctor.call_count == 15
    assert len(created_players) == 15
    assert len(pool._idle_players) == 15
    assert len(pool._active_players) == 0


# idle_player_pool_size Property Tests


def test_idle_player_pool_size_setter_rebuilds_idle_players(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> None:
    """Test that setting idle_player_pool_size rebuilds the idle pool."""
    player_ctor, _ = player_factory
    pool = PlayerPool()

    pool.idle_player_pool_size = 5

    assert pool.idle_player_pool_size == 5
    assert len(pool._idle_players) == 5
    assert player_ctor.call_count == 20


def test_idle_player_pool_size_setter_raises_for_negative_size(
    player_pool: PlayerPool,
) -> None:
    """Test that setting a negative idle pool size raises ValueError."""
    with pytest.raises(ValueError, match="must be >= 0"):
        player_pool.idle_player_pool_size = -1


# get_player Tests


def test_get_player_returns_player_and_marks_active(
    player_pool: PlayerPool,
) -> None:
    """Test that get_player returns a player and moves it to active list."""
    player = player_pool.get_player()

    assert player is not None
    assert len(player_pool._active_players) == 1
    assert player_pool._active_players[0] is player
    assert len(player_pool._idle_players) == 14
    assert player_pool.idle_player_pool_size == 14


def test_get_player_expands_pool_when_idle_is_low(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> None:
    """Test that get_player expands the pool when idle threshold is reached."""
    player_ctor, _ = player_factory
    pool = PlayerPool()
    pool.min_remaining_idle_players = 20

    pool.get_player()

    assert player_ctor.call_count == 25
    assert pool.total_allocated_players == 25
    assert pool.idle_player_pool_size == 24
    assert len(pool._idle_players) == 24
    assert len(pool._active_players) == 1


def test_get_player_raises_error_when_max_pool_reached(
    player_pool: PlayerPool,
) -> None:
    """Test that get_player raises RuntimeError when max pool size is reached."""
    player_pool.min_remaining_idle_players = 20
    player_pool.total_allocated_players = player_pool.max_pool_size

    with pytest.raises(RuntimeError, match="max pool size has been reached"):
        player_pool.get_player()


def test_get_player_expansion_respects_remaining_capacity(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> None:
    """Test expansion does not exceed max_pool_size when near capacity."""
    _, _ = player_factory
    pool = PlayerPool()
    pool.min_remaining_idle_players = 20
    pool.pool_expansion_count = 10
    pool.max_pool_size = 18
    pool.total_allocated_players = 15

    pool.get_player()

    assert pool.total_allocated_players == 18
    assert pool.idle_player_pool_size == 17


def test_total_alocated_players_alias_maps_to_corrected_name(
    player_factory: tuple[MagicMock, list[MagicMock]],
) -> None:
    """Test backward-compatible typo alias maps to total_allocated_players."""
    _, _ = player_factory
    pool = PlayerPool()

    pool.total_alocated_players = 22

    assert pool.total_allocated_players == 22
    assert pool.total_alocated_players == 22


# unload_player Tests


def test_unload_player_resets_and_returns_player_to_idle(
    player_pool: PlayerPool,
) -> None:
    """Test that unload_player resets player and returns it to idle pool."""
    player = cast(MagicMock, player_pool.get_player())

    player_pool.unload_player(player)

    player.reset.assert_called_once()
    assert player not in player_pool._active_players
    assert player in player_pool._idle_players
    assert len(player_pool._active_players) == 0
    assert player_pool.idle_player_pool_size == 15


def test_unload_player_raises_when_player_not_active(
    player_pool: PlayerPool, mocker: MockerFixture
) -> None:
    """Test that unload_player raises ValueError for unknown player."""
    unknown_player = cast(MagicMock, mocker.MagicMock())

    with pytest.raises(ValueError):
        player_pool.unload_player(unknown_player)

    unknown_player.reset.assert_not_called()


# destroy Tests


def test_destroy_deletes_all_players_and_clears_collections(
    player_pool: PlayerPool,
) -> None:
    """Test that destroy deletes idle and active players and clears storage."""
    player_a = cast(MagicMock, player_pool.get_player())
    player_b = cast(MagicMock, player_pool.get_player())

    idle_before = [cast(MagicMock, p) for p in player_pool._idle_players]

    player_pool.destroy()

    for player in idle_before:
        player.delete.assert_called_once()

    player_a.delete.assert_called_once()
    player_b.delete.assert_called_once()

    assert len(player_pool._idle_players) == 0
    assert len(player_pool._active_players) == 0
    assert player_pool.idle_player_pool_size == 0
    assert player_pool.total_allocated_players == 0
