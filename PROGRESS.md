# PROGRESS

| Етап | Описание | Статус |
|---|---|---|
| 0 | Настройка | ✅ завършен |
| 1 | Скелет на играта | ✅ завършен |
| 2 | BSP генератор | ⏳ предстои |
| 3 | Cellular Automata | ⏳ предстои |
| 4 | FOV и камера | ⏳ предстои |
| 5 | Врагове и бой | ⏳ предстои |
| 6 | Предмети и инвентар | ⏳ предстои |
| 7 | Прогресия и съдържание | ⏳ предстои |
| 8 | UI и полиране | ⏳ предстои |
| 9 | Тестове и качество | ⏳ предстои |
| 10 | Документация и защита | ⏳ предстои |

## Етап 0
- Структура на директориите, `.gitignore`, `requirements.txt` (pygame-ce 2.5.8, pytest 9.1.1),
  `pytest.ini`, `CLAUDE.md`, `README.md`.
- Проверено: `pip install -r requirements.txt` работи; `pytest` се изпълнява (0 теста).

## Етап 1
- `config.py`, `main.py`, `engine/{game,states,input_handler,actions,renderer,world,smoke}.py`,
  `world/{tile,game_map}.py`, `entities/entity.py`.
- State machine: `MainMenuState`, `PlayingState`; Command pattern: `MoveAction`, `WaitAction`.
- Добавен модул `engine/world.py` (логическо състояние без pygame) – не е в оригиналната
  схема, но позволява тестване на логиката без прозорец.
- Добавен `engine/smoke.py` – headless smoke test (`python main.py --smoke N`).
- Тестове: `tests/test_movement.py` (8 посоки, стени, граници), `tests/test_smoke.py`.

## Известни проблеми
- няма
