# PROGRESS

| Етап | Описание | Статус |
|---|---|---|
| 0 | Настройка | ✅ завършен |
| 1 | Скелет на играта | ✅ завършен |
| 2 | BSP генератор | ✅ завършен |
| 3 | Cellular Automata | ✅ завършен |
| 4 | FOV и камера | ✅ завършен |
| 5 | Врагове и бой | ✅ завършен |
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

## Етап 2
- `systems/rng.py` – централизиран random; seed за етаж N = SHA-256(seed, "map", N).
- `world/connectivity.py` – BFS разстояния, flood fill, региони, най-далечна точка.
- `world/generators/base.py` – `Rect`, `GenerationResult`, абстрактен `DungeonGenerator`
  (шаблонен метод: издълбай → старт → стълби → проверка за свързаност).
- `world/generators/bsp.py` – BSP дърво, стаи в листата, L-коридори между най-близките
  стаи на двете поддървета; стълби в най-далечната (по път) стая.
- `--seed` аргумент; seed-ът се показва в долния панел.
- **Отклонение от плана:** простата камера (`engine/camera.py`) е добавена още тук, защото
  картата 80x45 е по-голяма от екрана (40x18 тайла). FOV остава за Етап 4.
- Тестове: `test_bsp.py`, `test_connectivity.py`, `test_camera.py` (70 теста общо).

## Етап 3
- `world/generators/cellular.py` – 45% начални стени, 5 итерации (≥5 стени в 3x3 → стена;
  в първите 2 итерации и 0 стени → стена), пази се най-големият регион; ако е < 40% от
  площта – нов опит с под-seed, изведен от текущия генератор (детерминистично).
- Нечетни етажи – BSP, четни – пещери (`engine/world.py: make_generator`).
- `DescendAction` (`>` или Enter върху стълбите) генерира нов етаж.
- Smoke тестът понякога поставя играча на стълбите, за да мине през много етажи.
- Тестове: `test_cellular.py` (рамка, един регион, % под, детерминизъм, правилото, слизане).

## Етап 4
- `world/fov.py` – recursive shadowcasting в 8 октанта (радиус `FOV_RADIUS = 8`),
  плюс `bresenham_line` и `has_line_of_sight` (ще се ползват от стрелците в Етап 7).
- `GameMap.visible` / `GameMap.explored`; `World.update_fov()` след всеки ход и при слизане.
- Рендериране: видимо – пълни цветове, изследвано – затъмнено, неизследвано – черно;
  обектите се рисуват само ако са във FOV. Камерата (от Етап 2) следва играча.
- Тестове: `test_fov.py` (стена блокира, стартът е видим, радиус, симетрия, ръб на картата,
  explored се натрупва).

## Етап 5
- `components/fighter.py` – HP (винаги в [0, max_hp]), атака/защита като свойства
  (база + бонуси от екипировка), `take_damage`, `heal`, `regenerate`.
- `components/ai.py` – `BaseAI`, `HostileAI` (вижда играча → запомня позицията за
  `AI_MEMORY_TURNS` хода; съседен → `MeleeAction`; иначе стъпка по A*).
- `entities/actor.py` (композиция), `entities/factories.py`, `EnemyDef` таблица в config.
- `systems/pathfinding.py` – A* (8 посоки, Chebyshev, heapq, заетите клетки = цена +10).
- `systems/combat.py` – max(1, атака − защита) ± 1, 5% крит ×2, 5% пропуск.
- `engine/turn_manager.py` – играч → FOV → всички врагове (регенерация + AI) → FOV.
- `engine/actions.py` – `MeleeAction`, `BumpAction` (движение или атака).
- `ui/message_log.py` (обединява повторения), `ui/hud.py` (HP лента, статистики, лог).
- `world/spawner.py` – претеглен избор по етаж (засега плъх и гоблин), не в стартовата зона.
- `GameOverState` при смърт.
- Тестове: `test_pathfinding.py`, `test_combat.py`, `test_message_log.py` (149 общо).

## Известни проблеми
- няма
