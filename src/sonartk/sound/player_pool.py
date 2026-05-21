from collections import deque

from sonartk.sound.openal_lite.openal import Player


class PlayerPool:
    def __init__(self) -> None:
        self._idle_player_pool_size: int = 15
        self.max_pool_size: int = 256  # soft limit enforced by OpenAL
        self.pool_expansion_count: int = (
            10  # Used to increase pool size if condition is met
        )
        self.min_remaining_idle_players: int = (
            2  # the minimum number of idle players before expansion
        )
        self.total_allocated_players: int = self._idle_player_pool_size
        self._idle_players: deque[Player] = deque(
            [Player() for _ in range(self._idle_player_pool_size)]
        )
        self._active_players: list[Player] = []

    @property
    def total_alocated_players(self) -> int:
        """Backward-compatible alias for total_allocated_players."""
        return self.total_allocated_players

    @total_alocated_players.setter
    def total_alocated_players(self, value: int) -> None:
        """Backward-compatible alias for total_allocated_players."""
        self.total_allocated_players = value

    @property
    def idle_player_pool_size(self) -> int:
        """Return the idle player pool size."""
        return self._idle_player_pool_size

    @idle_player_pool_size.setter
    def idle_player_pool_size(self, idle_player_pool_size: int) -> None:
        """Set the idle player pool size."""
        if idle_player_pool_size < 0:
            raise ValueError("idle_player_pool_size must be >= 0")

        for player in self._idle_players:
            player.delete()
        self._idle_players = deque(
            [Player() for _ in range(idle_player_pool_size)]
        )
        self._idle_player_pool_size = idle_player_pool_size
        self.total_allocated_players = (
            len(self._active_players) + self._idle_player_pool_size
        )

    def get_player(self) -> Player:
        """Get player."""
        if len(self._idle_players) - 1 <= self.min_remaining_idle_players:
            remaining_capacity = (
                self.max_pool_size - self.total_allocated_players
            )
            if remaining_capacity <= 0:
                raise RuntimeError(
                    f"Unable to alocate any more players from Open AL, the max pool size has been reached ({self.max_pool_size})"
                )

            expansion = min(self.pool_expansion_count, remaining_capacity)
            for _ in range(expansion):
                self._idle_players.append(Player())
            self.total_allocated_players += expansion
            self._idle_player_pool_size += expansion

        player: Player = self._idle_players.pop()
        self._idle_player_pool_size -= 1
        self._active_players.append(player)
        return player

    def unload_player(self, player: Player) -> None:
        """Unload player."""
        index: int = self._active_players.index(player)
        player.reset()
        del self._active_players[index]
        self._idle_players.append(player)
        self._idle_player_pool_size += 1

    def destroy(self) -> None:
        """Destroy."""
        for player in self._idle_players:
            player.delete()
        for player in self._active_players:
            player.delete()

        self._idle_players.clear()
        self._active_players.clear()
        self._idle_player_pool_size = 0
        self.total_allocated_players = 0
