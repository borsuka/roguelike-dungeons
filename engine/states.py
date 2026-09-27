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
from ui.highscores import add_score, load_scores, make_entry
from ui.hud import draw_hud, wrap_text
from ui.menus import draw_menu_box, option_lines

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
            y = config.SCREEN_HEIGHT // 2 + i * (config.FONT_SIZE_MENU + config.MENU_OPTION_SPACING)
            renderer.draw_text(text, (center_x, y), color, renderer.menu_font, center=True)


class MainMenuState(MenuState):
    """Главно меню."""

    title = "ПОДЗЕМИЯТА НА КРАЛЯ"
    options = ["Нова игра", "Рекорди", "Изход"]

    def on_select(self, index: int) -> State | None:
        """Нова игра, таблица с рекорди или изход."""
        if index == 0:
            return PlayingState(self.game, World.new_game(self.game.take_seed()))
        if index == 1:
            return HighScoresState(self.game)
        self.game.running = False
        return None

    def on_cancel(self) -> State | None:
        """Esc в главното меню затваря играта."""
        self.game.running = False
        return None

    def render(self, renderer: Renderer) -> None:
        """Менюто плюс подзаглавие и кратка помощ за клавишите."""
        super().render(renderer)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text("Roguelike с процедурно генерирани подземия",
                           (center_x, config.SCREEN_HEIGHT // 4 + config.MENU_SUBTITLE_OFFSET),
                           config.COLOR_GRAY,
                           center=True)
        for i, line in enumerate(config.HELP_LINES):
            y = config.SCREEN_HEIGHT - config.HELP_BOTTOM_OFFSET + i * config.HELP_LINE_HEIGHT
            renderer.draw_text(line, (center_x, y), config.COLOR_GRAY, center=True)


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
            return PauseState(self.game, self)
        if result is Command.SHOW_LOG:
            return MessageLogState(self.game, self)
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
        labelled = [f"{chr(ord('a') + i)}) {text}" for i, text in enumerate(self.options)]
        lines = option_lines(labelled, self.selected)
        draw_menu_box(renderer, "Ново ниво! Избери подобрение", lines,
                      footer="a/b/c или стрелки + Enter")


def letter_index(char: str) -> int | None:
    """'a' → 0, 'b' → 1, ...; None за всичко друго."""
    if len(char) == 1 and "a" <= char <= "z":
        return ord(char) - ord("a")
    return None


class PauseState(MenuState):
    """Пауза върху играта (Esc)."""

    title = "Пауза"
    options = ["Продължи", "Изоставяне (към главното меню)", "Изход от играта"]

    def __init__(self, game: Game, parent: PlayingState) -> None:
        super().__init__(game)
        self.parent = parent

    def on_select(self, index: int) -> State | None:
        """Продължава, изоставя играта или затваря програмата."""
        if index == 0:
            return self.parent
        if index == 1:
            return MainMenuState(self.game)
        self.game.running = False
        return None

    def on_cancel(self) -> State | None:
        """Esc отново – връщане в играта."""
        return self.parent

    def render(self, renderer: Renderer) -> None:
        """Играта отзад и прозорец с опциите."""
        self.parent.render(renderer)
        lines = option_lines(self.options, self.selected)
        draw_menu_box(renderer, self.title, lines, footer="Стрелки + Enter    Esc: продължи")


class MessageLogState(State):
    """Пълната история на съобщенията с превъртане (V)."""

    def __init__(self, game: Game, parent: PlayingState) -> None:
        super().__init__(game)
        self.parent = parent
        self.offset = 0  # колко реда сме превъртели нагоре от най-новото
        self.page_size = 1
        self.total_lines = 0

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Стрелки/PageUp/PageDown превъртат; Esc или V затварят."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name in (config.ESCAPE_KEY, config.LOG_KEY):
            return self.parent
        steps = {**{k: 1 for k in config.MENU_UP_KEYS}, **{k: -1 for k in config.MENU_DOWN_KEYS},
                 **{k: self.page_size for k in config.PAGE_UP_KEYS},
                 **{k: -self.page_size for k in config.PAGE_DOWN_KEYS}}
        if name in steps:
            max_offset = max(0, self.total_lines - self.page_size)
            self.offset = max(0, min(max_offset, self.offset + steps[name]))
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува видимата част от историята."""
        renderer.screen.fill(config.COLOR_PANEL_BG)
        pad = config.PANEL_PADDING * 2
        font = renderer.ui_font
        line_h = font.get_linesize()
        renderer.draw_text("Лог на съобщенията", (config.SCREEN_WIDTH // 2, config.LOG_TITLE_Y),
                           config.COLOR_TITLE, renderer.menu_font, center=True)
        lines: list[tuple[str, config.Color]] = []
        for message in self.parent.world.message_log.messages:
            for line in wrap_text(message.full_text, font, config.SCREEN_WIDTH - 2 * pad):
                lines.append((line, message.color))
        top, bottom = pad + config.LOG_TOP_OFFSET, config.SCREEN_HEIGHT - pad - line_h
        self.page_size = max(1, (bottom - top) // line_h)
        self.total_lines = len(lines)
        end = len(lines) - self.offset
        visible = lines[max(0, end - self.page_size):end]
        for i, (text, color) in enumerate(visible):
            renderer.draw_text(text, (pad, top + i * line_h), color)
        renderer.draw_text("Стрелки / PageUp / PageDown: превъртане    Esc или V: затвори",
                           (config.SCREEN_WIDTH // 2, bottom + line_h // 2), config.COLOR_GRAY,
                           center=True)


class HighScoresState(State):
    """Таблица с най-добрите 10 резултата."""

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self.entries = load_scores(game.highscore_path)

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Enter или Esc – обратно в главното меню."""
        if event.type == pygame.KEYDOWN and (
                key_name(event) in config.CONFIRM_KEYS or key_name(event) == config.ESCAPE_KEY):
            return MainMenuState(self.game)
        return None

    def render(self, renderer: Renderer) -> None:
        """Рисува таблицата."""
        renderer.screen.fill(config.COLOR_BLACK)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text("РЕКОРДИ", (center_x, config.HIGHSCORE_TITLE_Y), config.COLOR_TITLE,
                           renderer.title_font, center=True)
        headers = ["#", "Точки", "Етаж", "Ниво", "Убити", "Ходове", "Победа", "Дата"]
        self._draw_row(renderer, headers, config.HIGHSCORE_HEADER_Y, config.COLOR_GRAY)
        if not self.entries:
            renderer.draw_text("Все още няма рекорди.", (center_x, config.HIGHSCORE_FIRST_ROW_Y),
                               config.COLOR_MENU_TEXT, renderer.menu_font, center=True)
        for i, e in enumerate(self.entries):
            row = [i + 1, e.score, e.floor, e.level, e.kills, e.turns,
                   "да" if e.victory else "не", e.date]
            color = config.COLOR_VICTORY if e.victory else config.COLOR_MENU_TEXT
            y = config.HIGHSCORE_FIRST_ROW_Y + i * config.HIGHSCORE_ROW_HEIGHT
            self._draw_row(renderer, [str(v) for v in row], y, color)
        renderer.draw_text("Enter / Esc – назад",
                           (center_x, config.SCREEN_HEIGHT - config.FOOTER_BOTTOM_OFFSET),
                           config.COLOR_GRAY, center=True)


    @staticmethod
    def _draw_row(renderer: Renderer, cells: list[str], y: int, color: config.Color) -> None:
        """Рисува ред от таблицата: всяка клетка е центрирана в своята колона.

        Шрифтът не е моноширинен, затова колоните са с фиксирани x позиции, а не с интервали.
        """
        for x, cell in zip(config.HIGHSCORE_COLUMNS_X, cells):
            renderer.draw_text(cell, (x, y), color, renderer.menu_font, center=True)


class EndScreenState(State):
    """Общ екран за край на играта: статистика + запис в рекордите.

    Резултатът се записва веднъж – при създаването на екрана.
    """

    title = ""
    title_color: config.Color = config.COLOR_WHITE

    def __init__(self, game: Game, world: World) -> None:
        super().__init__(game)
        self.world = world
        level = world.player.level.current_level if world.player.level else 1
        self.entry = make_entry(floor=world.max_floor, kills=world.kills, turns=world.turn,
                                level=level, victory=world.victory, seed=world.seed)
        self.rank = add_score(game.highscore_path, self.entry)

    def handle_event(self, event: pygame.event.Event) -> State | None:
        """Enter или Esc – към главното меню."""
        if event.type != pygame.KEYDOWN:
            return None
        name = key_name(event)
        if name in config.CONFIRM_KEYS or name == config.ESCAPE_KEY:
            return MainMenuState(self.game)
        return None

    def stats_lines(self) -> list[str]:
        """Редовете със статистиката."""
        e = self.entry
        rank = f"Място в класацията: #{self.rank}" if self.rank else "Не влезе в топ 10."
        return [
            f"Достигнат етаж: {e.floor}",
            f"Ниво: {e.level}",
            f"Убити врагове: {e.kills}",
            f"Ходове: {e.turns}",
            f"Точки: {e.score}",
            rank,
            f"Seed: {e.seed}",
        ]

    def render(self, renderer: Renderer) -> None:
        """Заглавие, статистика и подсказка."""
        renderer.screen.fill(config.COLOR_BLACK)
        center_x = config.SCREEN_WIDTH // 2
        renderer.draw_text(self.title, (center_x, config.END_TITLE_Y), self.title_color,
                           renderer.title_font, center=True)
        for i, line in enumerate(self.stats_lines()):
            y = config.END_STATS_Y + i * config.END_STATS_LINE_HEIGHT
            renderer.draw_text(line, (center_x, y), config.COLOR_MENU_TEXT,
                               renderer.menu_font, center=True)
        renderer.draw_text("Enter – главно меню",
                           (center_x, config.SCREEN_HEIGHT - config.FOOTER_BOTTOM_OFFSET),
                           config.COLOR_GRAY, renderer.menu_font, center=True)


class GameOverState(EndScreenState):
    """Екран след смъртта на играча (permadeath – играта не може да продължи)."""

    title = "ТИ ЗАГИНА"
    title_color = config.COLOR_GAME_OVER


class VictoryState(EndScreenState):
    """Екран след победа над боса."""

    title = "ПОБЕДА! Кралят е свален."
    title_color = config.COLOR_VICTORY
