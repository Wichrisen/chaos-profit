# Хаос & Прибыль (Chaos & Profit)

> Фановая некоммерческая игра про молодого предпринимателя, который вынужден крутить слот-машину, чтобы выживать в мире, где мораль и хаос давно стали одной валютой.

**Жанр**: Idle + слот-машина + management с тёмным нарративом, коррупцией и моральными компромиссами.

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Примечание:** Активная разработка Pygame-версии игры приостановлена. В настоящее время ведётся работа над веб-версией проекта.

## Особенности

- Слот-машина в центре игрового цикла
- Система бизнеса и сделок с тяжёлыми моральными последствиями
- Рейтисурд — чем глубже хаос, тем выше ставки и опаснее последствия
- Проклятия, шрамы и перманентные изменения экономики
- Оффлайн-прогресс + механика «цена успеха» при сбросе

## Как запустить

### Pygame-версия

```bash
python -m src.chaos_profit.ui_pygame
```

### Консольная версия

```bash
python -m src.chaos_profit.ui_console.console_app
```

> **Примечание:** Консольная версия создавалась в основном для тестирования механик и баланса.

## Установка

```bash
git clone https://github.com/Wichrisen/chaos-profit.git
cd chaos-profit

python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

## Структура проекта

- `src/chaos_profit/core/` — игровая механика и логика
- `src/chaos_profit/ui_pygame/` — Pygame-версия
- `src/chaos_profit/ui_console/` — консольная версия
- `assets/` — изображения и звуки
- `packaging/` — конфигурация сборки (PyInstaller)
```