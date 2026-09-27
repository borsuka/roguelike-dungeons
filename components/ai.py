"""Изкуствен интелект на враговете.

Всеки AI клас има метод `decide(world)`, който връща Action – същите действия, които
използва и играчът (Command pattern). AI само решава КАКВО да прави; изпълнението е
отговорност на действието.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import config
from engine.actions import Action, BumpAction, MeleeAction, MoveAction, WaitAction
from systems import pathfinding

if TYPE_CHECKING:
    from engine.world import World
    from entities.actor import Actor

Point = tuple[int, int]


class BaseAI:
    """Базов клас за AI.

    Attributes:
        owner: Actor, когото управлява.
    """

    def __init__(self) -> None:
        self.owner: Actor | None = None

    @property
    def actor(self) -> Actor:
        """Собственикът (гарантирано зададен след закачане към Actor)."""
        assert self.owner is not None, "AI не е закачен към Actor"
        return self.owner

    def decide(self, world: World) -> Action:
        """Решава какво да прави този ход."""
        raise NotImplementedError

    def can_see_player(self, world: World) -> bool:
        """Вижда ли играча.

        Използваме зрителното поле на играча: ако врагът е в него, значи между тях няма
        стена и те се виждат взаимно (shadowcasting е почти симетричен).
        """
        return world.player.is_alive and world.game_map.is_visible(self.actor.x, self.actor.y)

    def step_towards(self, world: World, target: Point) -> Action | None:
        """MoveAction към първата клетка от A* пътя до `target` (None, ако няма път)."""
        actor = self.actor
        occupied = {
            a.position for a in world.game_map.actors
            if a is not actor and a is not world.player
        }
        path = pathfinding.find_path(world.game_map.walkable_grid(), actor.position,
                                     target, occupied)
        if not path:
            return None
        next_x, next_y = path[0]
        return MoveAction(actor, next_x - actor.x, next_y - actor.y)


class HostileAI(BaseAI):
    """Преследва играча, докато го вижда или го е видял в последните N хода ("памет").

    Attributes:
        memory_turns: Колко хода помни последната позиция на играча.
        last_known: Последната видяна позиция на играча (или None).
        turns_since_seen: Колко хода не го е виждал.
    """

    def __init__(self, memory_turns: int = config.AI_MEMORY_TURNS) -> None:
        super().__init__()
        self.memory_turns = memory_turns
        self.last_known: Point | None = None
        self.turns_since_seen = 0

    def update_memory(self, world: World) -> bool:
        """Обновява паметта. Връща дали играчът се вижда в момента."""
        if self.can_see_player(world):
            self.last_known = world.player.position
            self.turns_since_seen = 0
            return True
        self.turns_since_seen += 1
        if self.turns_since_seen > self.memory_turns:
            self.last_known = None  # забравил е
        return False

    def decide(self, world: World) -> Action:
        """Атакува, ако е до играча; иначе се приближава по A*; иначе чака."""
        actor, player = self.actor, world.player
        sees_player = self.update_memory(world)
        if self.last_known is None:
            return WaitAction(actor)
        if sees_player and actor.distance_to(*player.position) <= 1:
            return MeleeAction(actor, player.x - actor.x, player.y - actor.y)
        step = self.step_towards(world, self.last_known)
        if step is None:
            if actor.position == self.last_known:
                self.last_known = None  # стигнал е мястото, но играча го няма
            return WaitAction(actor)
        return step


class ConfusedAI(BaseAI):
    """Временно състояние: съществото се лута в случайни посоки.

    Обгръща (decorator) истинския AI и го връща след `turns_remaining` хода.
    Докато е объркан, врагът може да удари и друг враг, ако се блъсне в него.

    Attributes:
        previous_ai: AI-то, което ще бъде възстановено.
        turns_remaining: Оставащи ходове объркване.
    """

    def __init__(self, previous_ai: BaseAI | None, turns: int) -> None:
        super().__init__()
        self.previous_ai = previous_ai
        self.turns_remaining = turns

    def decide(self, world: World) -> Action:
        """Случайна посока; след изтичане на времето – връща старото AI."""
        actor = self.actor
        if self.turns_remaining <= 0:
            actor.replace_ai(self.previous_ai)
            world.message_log.add(f"{actor.name} вече не е объркан.", config.COLOR_MSG_MAGIC)
            return WaitAction(actor)
        self.turns_remaining -= 1
        dx, dy = world.rng.choice(pathfinding.DIRECTIONS_8)
        return BumpAction(actor, dx, dy)
