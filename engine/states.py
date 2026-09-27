"""Екрани на играта (State pattern).

Всеки екран е отделен клас с два метода:
- `handle_event(event)` – реагира на вход и може да върне нов State (преход);
- `render(renderer)` – рисува себе си.
Така `Game` не съдържа нито един `if` за "в кой екран сме".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

import config
from engine.actions import Action, DropItemAction, UseItemAction
from engine.camera import Camera
from engine.input_handler import Command, key_name, translate_key
from engine.renderer import Renderer
from engine.turn_manager import TurnManager
from engine.world import World
from ui.hud import draw_hud
from ui.menus import draw_menu_box

if TYPE_CHECKING:
    from engine.game import Game
    from entities.item import Item


class State:
    """Базов клас за екран.

    Attributes:
        game: Главният обект на играта (за достъп до настройки и изход).
    """

    def __init__(self, game: Game) -> None:
        self.game = game

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Обработва събитие. Връща нов State при преход, иначе None."""
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува екрана."""


class MenuState(State):
    """Общ екран с вертикален списък от опции, избирани със стрелки и Enter."""

    title = ""
    options: list[str] = []

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.selected = 0

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Стрелки мести избора, Enter го потвърждава."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name in config.MENU_UP_KEYS:
            self.selected = (self.selected - 1) % len(self.options)
        elif name in config.MENU_DOWN_KEYS:
            self.selected = (self.selected + 1) % len(self.options)
        elif name in config.CONFIRM_KEYS:
            return self.on_select(self.selected)
        elif name == config.ESCAPE_KEY:
            return self.on_cancel()
        return None

    def on_select(self, index: int) -> State | None:
        """Извиква се при избор на опция."""
        return None

    def on_cancel(self) -> State | None:
        """Извиква се при Esc."""
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува заглавие и опции в центъра на екрана."""
        renderer.screen.fill(config.COLOR_BLACK)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text(self.title, (center_x, config.SCREEN_HEIGHT // 4),
                           config.COLOR_TITLE, renderer.title_font, center=True)
        for i, option in enumerate(self.options):
            selected = i == self.selected
            color = config.COLOR_MENU_SELECTED if selected else config.COLOR_MENU_TEXT
            text = f"> {option} <" if selected else option
            y = config.SCREEN_HEIGHT // 2 + i * (config.FONT_SIZE_MENU + 12)
            renderer.draw_text(text, (center_x, y), color, renderer.menu_font, center=True)


class MainMenuState(MenuState):
    """Главно меню."""

    title = "ПОДЗЕМИЯТА НА КРАЛЯ"
    options = ["Нова игра", "Изход"]

    def on_select(self, index: int) -> State | None:
        """Стартира нова игра или затваря програмата."""
        if index == 0:
            return PlayingState(self.game, World.new_game(self.game.take_seed()))
        self.game.running = False
        return None

    def on_cancel(self) -> State | None:
        """Esc в главното меню затваря играта."""
        self.game.running = False
        return None


class PlayingState(State):
    """Самата игра: карта, играч, ходове."""

    def __init__(self, game: Game, world: World) -> None:
        super().__init__(game)
        self.world = world
        self.turn_manager = TurnManager(world)
        self.camera = Camera(config.VIEW_WIDTH_TILES, config.VIEW_HEIGHT_TILES,
                             world.game_map.width, world.game_map.height)

    def perform(self, action: Action) -> State:
        """Изиграва ход и връща следващия екран (себе си или край на играта)."""
        self.turn_manager.play_turn(action)
        return self.next_state()

    def next_state(self) -> State:
        """Край на играта, победа, ново ниво или продължаване на играта."""
        world = self.world
        if world.game_over:
            return GameOverState(self.game, world)
        if world.victory:
            return VictoryState(self.game, world)
        level = world.player.level
        if level is not None and level.requires_level_up:
            return LevelUpState(self.game, self)
        return self

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Превежда клавиша в действие/команда."""
        if event.type != pygame.KEYDOWN:
            return None
        result = translate_key(event, self.world.player)
        if result is Command.PAUSE:
            return MainMenuState(self.game)
        if result is Command.INVENTORY:
            return InventoryState(self.game, self, drop_mode=False)
        if result is Command.DROP:
            return InventoryState(self.game, self, drop_mode=True)
        if isinstance(result, Action):
            return self.perform(result)
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува света и панела."""
        renderer.screen.fill(config.COLOR_BLACK)
        self.camera.center_on(*self.world.player.position)
        renderer.draw_world(self.world, self.camera)
        draw_hud(renderer, self.world)


class InventoryState(State):
    """Екран с раницата: буква → използвай (или изхвърли) предмета."""

    def __init__(self, game: Game, parent: PlayingState, drop_mode: bool) -> None:
        super().__init__(game)
        self.parent = parent
        self.drop_mode = drop_mode

    @property
    def items(self) -> list[Item]:
        """Предметите в раницата на играча."""
        inventory = self.parent.world.player.inventory
        return inventory.items if inventory is not None else []

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """a–z избира предмет; Esc затваря."""
        if event.type != pygame.KEYDOWN:
            return None
        if key_name(event) == config.ESCAPE_KEY:
            return self.parent
        index = letter_index(event.unicode)
        if index is None or index >= len(self.items):
            return None
        return self.on_item_selected(self.items[index])

    def on_item_selected(self, item: Item) -> State:
        """Изхвърля, насочва или използва предмета."""
        player = self.parent.world.player
        if self.drop_mode:
            return self.parent.perform(DropItemAction(player, item))
        if item.consumable is not None and item.consumable.needs_target:
            return TargetingState(self.game, self.parent, item)
        return self.parent.perform(UseItemAction(player, item))

    def render(self, renderer: Renderer) -> None:
        """Рисува играта и прозорец със списъка."""
        self.parent.render(renderer)
        equipment = self.parent.world.player.equipment
        lines = []
        for i, item in enumerate(self.items):
            suffix = " (екипиран)" if equipment and equipment.is_equipped(item) else ""
            lines.append((f"{chr(ord('a') + i)}) {item.name}{suffix}", item.color))
        title = "Изхвърли предмет" if self.drop_mode else "Инвентар"
        draw_menu_box(renderer, title, lines, footer="a–z: избор    Esc: затвори")


class TargetingState(State):
    """Избор на целева клетка с курсор (за свитъка на объркването)."""

    def __init__(self, game: Game, parent: PlayingState, item: Item) -> None:
        super().__init__(game)
        self.parent = parent
        self.item = item
        world = parent.world
        enemies = sorted(world.visible_enemies(),
                         key=lambda e: world.player.distance_to(*e.position))
        # Курсорът започва върху най-близкия видим враг (ако има такъв).
        self.cursor = enemies[0].position if enemies else world.player.position

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Стрелки мести курсора, Enter потвърждава, Esc отказва."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name == config.ESCAPE_KEY:
            return self.parent
        if name in config.CONFIRM_KEYS:
            action = UseItemAction(self.parent.world.player, self.item, target=self.cursor)
            return self.parent.perform(action)
        if name in config.MOVE_KEYS:
            dx, dy = config.MOVE_KEYS[name]
            x, y = self.cursor[0] + dx, self.cursor[1] + dy
            if self.parent.world.game_map.in_bounds(x, y):
                self.cursor = (x, y)
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува играта, курсора и подсказка."""
        self.parent.render(renderer)
        renderer.draw_cursor(self.parent.camera, *self.cursor)
        renderer.draw_text("Избери цел: стрелки, Enter – потвърди, Esc – откажи",
                           (config.PANEL_PADDING, config.PANEL_PADDING), config.COLOR_CURSOR)


class LevelUpState(State):
    """Избор на подобрение при ново ниво (не може да се пропусне с Esc)."""

    def __init__(self, game: Game, parent: PlayingState) -> None:
        super().__init__(game)
        self.parent = parent
        self.selected = 0

    @property
    def options(self) -> list[str]:
        """Текстовете на трите избора."""
        fighter = self.parent.world.player.fighter
        return [
            f"Издръжливост: +{config.LEVEL_UP_HP} max HP (сега {fighter.max_hp})",
            f"Сила: +{config.LEVEL_UP_ATTACK} атака (сега {fighter.attack})",
            f"Ловкост: +{config.LEVEL_UP_DEFENSE} защита (сега {fighter.defense})",
        ]

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Стрелки + Enter или директно a/b/c."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        index = letter_index(event.unicode)
        if index is not None and index < len(self.options):
            return self.apply(index)
        if name in config.MENU_UP_KEYS:
            self.selected = (self.selected - 1) % len(self.options)
        elif name in config.MENU_DOWN_KEYS:
            self.selected = (self.selected + 1) % len(self.options)
        elif name in config.CONFIRM_KEYS:
            return self.apply(self.selected)
        return None

    def apply(self, index: int) -> State:
        """Прилага избора и продължава (или пита отново при още едно ниво)."""
        world = self.parent.world
        level = world.player.level
        assert level is not None
        choices = (level.increase_max_hp, level.increase_attack, level.increase_defense)
        choices[index]()
        world.message_log.add(f"Ниво {level.current_level}!", config.COLOR_MSG_LEVEL_UP)
        return self.parent.next_state()

    def render(self, renderer: Renderer) -> None:
        """Рисува играта и менюто с изборите."""
        self.parent.render(renderer)
        lines = []
        for i, text in enumerate(self.options):
            color = config.COLOR_MENU_SELECTED if i == self.selected else config.COLOR_MENU_TEXT
            lines.append((f"{chr(ord('a') + i)}) {text}", color))
        draw_menu_box(renderer, "Ново ниво! Избери подобрение", lines,
                      footer="a/b/c или стрелки + Enter")


def letter_index(char: str) -> int | None:
    """'a' → 0, 'b' → 1, ...; None за всичко друго."""
    if len(char) == 1 and "a" <= char <= "z":
        return ord(char) - ord("a")
    return None


class GameOverState(State):
    """Екран след смъртта на играча (permadeath – играта не може да продължи)."""

    def __init__(self, game: Game, world: World) -> None:
        super().__init__(game)
        self.world = world
        self.camera = Camera(config.VIEW_WIDTH_TILES, config.VIEW_HEIGHT_TILES,
                             world.game_map.width, world.game_map.height)

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Enter или Esc – към главното меню."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name in config.CONFIRM_KEYS or name == config.ESCAPE_KEY:
            return MainMenuState(self.game)
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува замръзналия свят и надпис отгоре."""
        renderer.screen.fill(config.COLOR_BLACK)
        self.camera.center_on(*self.world.player.position)
        renderer.draw_world(self.world, self.camera)
        draw_hud(renderer, self.world)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text("ТИ ЗАГИНА", (center_x, config.SCREEN_HEIGHT // 3),
                           config.COLOR_GAME_OVER, renderer.title_font, center=True)
        renderer.draw_text("Enter – главно меню", (center_x, config.SCREEN_HEIGHT // 3 + 60),
                           config.COLOR_MENU_TEXT, renderer.menu_font, center=True)


class VictoryState(State):
    """Екран след победа над боса."""

    def __init__(self, game: Game, world: World) -> None:
        super().__init__(game)
        self.world = world

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Enter или Esc – към главното меню."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name in config.CONFIRM_KEYS or name == config.ESCAPE_KEY:
            return MainMenuState(self.game)
        return None

    def render(self, renderer: Renderer) -> None:
        """Надпис за победа."""
        renderer.screen.fill(config.COLOR_BLACK)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text("ПОБЕДА!", (center_x, config.SCREEN_HEIGHT // 3),
                           config.COLOR_VICTORY, renderer.title_font, center=True)
        renderer.draw_text("Кралят на подземието е победен.",
                           (center_x, config.SCREEN_HEIGHT // 3 + 60),
                           config.COLOR_MENU_TEXT, renderer.menu_font, center=True)
        renderer.draw_text("Enter – главно меню", (center_x, config.SCREEN_HEIGHT // 3 + 110),
                           config.COLOR_GRAY, renderer.menu_font, center=True)
