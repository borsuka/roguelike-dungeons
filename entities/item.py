"""Item – предмет, който може да лежи на земята или да е в раницата."""

from __future__ import annotations

from typing import TYPE_CHECKING

from config import Color
from entities.entity import Entity, RenderOrder

if TYPE_CHECKING:
    from components.consumable import Consumable
    from components.equippable import Equippable


class Item(Entity):
    """Предмет. Поведението му идва от компонент (композиция):

    - `consumable` – еднократна употреба (отвара, свитък);
    - `equippable` – може да се екипира (оръжие, броня).

    Attributes:
        consumable: Компонент за употреба или None.
        equippable: Компонент за екипиране или None.
    """

    def __init__(
        self, x: int, y: int, char: str, color: Color, name: str,
        consumable: Consumable | None = None, equippable: Equippable | None = None,
    ) -> None:
        super().__init__(x, y, char, color, name, blocks_movement=False,
                         render_order=RenderOrder.ITEM)
        self.consumable = consumable
        self.equippable = equippable
        for component in (consumable, equippable):
            if component is not None:
                component.owner = self
