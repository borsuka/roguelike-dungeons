# CLAUDE.md – конвенции на проекта

Roguelike игра на Python (`pygame-ce`), университетски проект. Читателят на кода е студент,
който трябва да може да обясни всеки файл пред преподавател.

## Среда
- Python 3.11+ (разработено на 3.14), виртуална среда в `.venv/`.
- Зависимости: само `pygame-ce` и `pytest` (виж `requirements.txt`). Нищо друго извън
  стандартната библиотека.
- Без външни графични файлове – всичко се рисува програмно (правоъгълници + символи).
- Тестове: `python -m pytest -v`.
- Headless smoke test: `python main.py --smoke 200` (използва `SDL_VIDEODRIVER=dummy`).

## Стил на кода
- PEP 8, максимум 100 символа на ред.
- Type hints навсякъде; всеки модул започва с `from __future__ import annotations`.
- Docstrings за всеки клас и публична функция (Google стил), **на български**.
- Коментари – кратки, на български, при нетривиалните стъпки (защо, не какво).
- Имената в кода (класове, функции, променливи) са на английски.
- Без магически числа – всички константи и баланс са в `config.py`.
- Функции до ~40 реда; по-дългите се разделят.
- Яснота пред "хитър" код.

## Архитектура
- Логическите модули (`world/`, `systems/`, `components/`, `entities/`, `engine/actions.py`,
  `engine/turn_manager.py`, `engine/world.py`, `engine/camera.py`, `ui/message_log.py`,
  `ui/highscores.py`) **не импортират pygame** – тестват се без прозорец.
- pygame се използва само в `main.py`, `engine/game.py`, `engine/states.py`,
  `engine/input_handler.py`, `engine/renderer.py`, `engine/smoke.py`, `ui/hud.py`,
  `ui/menus.py`.
- Модули извън първоначалната схема: `engine/world.py` (логическо състояние),
  `engine/camera.py`, `engine/smoke.py`, `components/consumable.py`,
  `components/equippable.py`, `tests/helpers.py`.
- Нов враг/предмет = нов запис в `config.ENEMIES` / `config.ITEMS` + тегла за спаунване;
  нов тип AI/ефект = нов клас в `components/ai.py` / `components/consumable.py` и ред във
  фабриката (`entities/factories.py`).
- Композиция пред наследяване: `Actor` има компоненти (Fighter, AI, Inventory, Equipment, Level).
- Command pattern: всяко действие е обект с `perform(world) -> bool`.
- State pattern: екраните на играта са отделни State класове.
- Целият random минава през `systems/rng.py` (детерминизъм по seed).

## Документация
- `README.md` (инсталация, контроли), `ARCHITECTURE.md` (модули, диаграми, алгоритми с
  Big-O), `DEFENSE.md` (въпроси за защитата), `PROGRESS.md` (история на етапите).
- При промяна на алгоритъм/архитектура – обнови и `ARCHITECTURE.md`/`DEFENSE.md`.

## Работен процес
- Всеки етап: план → код → pytest → headless smoke test → commit `stage N: описание`
  → обновяване на `PROGRESS.md`.
- Никога не променяй тест само за да мине – поправи кода.
- Незавършеното се записва в `PROGRESS.md`.
