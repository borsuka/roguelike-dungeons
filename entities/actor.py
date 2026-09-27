"""Actor – същество, което може да се бие (играч или враг)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import config
from config import Color
from entities.entity import Entity, RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.equipment import Equipment
    from components.fighter import Fighter
    from components.inventory import Inventory
    from components.level import Level


class Actor(Entity):
    """Същество, съставено от компоненти (композиция вместо дълбока йерархия).

    Играчът и враговете са един и същ клас – разликата е само в компонентите:
    играчът има Inventory/Level и няма AI, враговете имат AI.

    Attributes:
        fighter: Живот и бой (задължителен).
        ai: Изкуствен интелект (None за играча и труповете).
        inventory: Раница (само играчът).
        equipment: Екипирани предмети (само играчът).
        level: Опит и нива (само играчът).
    """

    def __init__(
        self, x: int, y: int, char: str, color: Color, name: str, fighter: Fighter,
        ai: BaseAI | None = None, inventory: Inventory | None = None,
        equipment: Equipment | None = None, level: Level | None = None,
    ) -> None:
        super().__init__(x, y, char, color, name, blocks_movement=True,
                         render_order=RenderOrder.ACTOR)
        self.fighter = fighter
        self.kind = ""  # ключ от config.ENEMIES ("goblin", "boss"...); празен за играча
        self.ai = ai
        self.inventory = inventory
        self.equipment = equipment
        self.level = level
        for component in (fighter, ai, inventory, equipment, level):
            if component is not None:
                component.owner = self

    @property
    def is_alive(self) -> bool:
        """True, докато има живот."""
        return not self.fighter.is_dead

    def become_corpse(self) -> None:
        """Превръща съществото в труп: не блокира, не мисли, рисува се отдолу."""
        self.char = config.CORPSE_CHAR
        self.color = config.COLOR_CORPSE
        self.blocks_movement = False
        self.ai = None
        self.render_order = RenderOrder.CORPSE
        self.name = f"останки от {self.name}"

    def replace_ai(self, ai: BaseAI | None) -> None:
        """Сменя AI-то (напр. при объркване) и го свързва със собственика."""
        self.ai = ai
        if ai is not None:
            ai.owner = self
