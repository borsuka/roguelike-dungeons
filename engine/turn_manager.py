"""Редуване на ходовете: първо играчът, после всички врагове."""

from __future__ import annotations

from engine.actions import Action
from engine.world import World


class TurnManager:
    """Изпълнява един пълен ход на света.

    Играта е turn-based: светът "стои", докато играчът не направи валидно действие.
    Тогава всеки жив враг получава точно един ход.
    """

    def __init__(self, world: World) -> None:
        self.world = world

    def play_turn(self, action: Action) -> bool:
        """Изпълнява действието на играча и (ако е валидно) ходовете на враговете.

        Args:
            action: Действието на играча.

        Returns:
            True, ако е изигран ход (действието е било валидно).
        """
        world = self.world
        floor_before = world.floor
        if not action.perform(world):
            return False
        world.turn += 1
        world.update_fov()  # враговете "виждат" играча на новата му позиция
        if world.floor == floor_before:  # след слизане новият етаж започва на спокойствие
            self.enemy_turns()
            world.update_fov()
        return True

    def enemy_turns(self) -> None:
        """Всеки жив враг: регенерация, после решение на AI и изпълнението му."""
        world = self.world
        for actor in list(world.game_map.actors):
            if actor is world.player or actor.ai is None or not actor.is_alive:
                continue
            actor.fighter.regenerate()
            actor.ai.decide(world).perform(world)
            if world.game_over:
                break
