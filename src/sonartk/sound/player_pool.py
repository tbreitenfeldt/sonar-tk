from typing import Self
from collections import deque
import time

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
        self.total_alocated_players: int = self._idle_player_pool_size
        self._idle_players: deque[Player] = deque(
            [Player() for _ in range(self._idle_player_pool_size)]
        )
        self._active_players: list[Player] = []

    @property
    def idle_player_pool_size(self) -> int:
        return self._idle_player_pool_size

    @idle_player_pool_size.setter
    def idle_player_pool_size(self, idle_player_pool_size: int) -> None:
        self._idle_players = deque(
            [Player() for _ in range(idle_player_pool_size)]
        )
        self._idle_player_pool_size = idle_player_pool_size

    def get_player(self) -> Player:
        if len(self._idle_players) - 1 <= self.min_remaining_idle_players:
            if self.total_alocated_players + 1 >= self.max_pool_size:
                raise RuntimeError(
                    f"Unable to alocate any more players from Open AL, the max pool size has been reached ({self.max_pool_size})"
                )

            for _ in range(self.pool_expansion_count):
                self._idle_players.append(Player())
            self.total_alocated_players += self.pool_expansion_count
            self._idle_player_pool_size += self.pool_expansion_count

        player: Player = self._idle_players.pop()
        self._idle_player_pool_size -= 1
        self._active_players.append(player)
        return player

    def unload_player(self, player: Player) -> None:
        player.reset()
        index: int = self._active_players.index(player)
        del self._active_players[index]
        self._idle_players.append(player)
        self._idle_player_pool_size -= 1

    def destroy(self) -> None:
        for player in self._idle_players:
            player.delete()
        for player in self._active_players:
            player.delete()

        self._idle_players.clear()
        self._active_players.clear()
