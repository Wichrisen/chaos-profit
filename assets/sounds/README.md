# Sounds for Chaos & Profit

Place your `.wav` files here (or `.ogg`).

## Required for current implementation (priority order)

### Slot Machine (highest impact)
- `slot_click.wav`          — Clicking the big spin button
- `reel_spin_loop.wav`      — Looping sound while reels are spinning (should be seamless)
- `reel_stop_1.wav`         — Left reel stops
- `reel_stop_2.wav`         — Middle reel stops (a bit more weight)
- `reel_stop_3.wav`         — Right reel stops (most dramatic)
- `slot_result_good.wav`    — Positive outcome
- `slot_result_bad.wav`     — Neutral or slightly negative
- `slot_result_chaotic.wav` — Chaotic / cursed outcome (scary/distorted)

### UI & General
- `ui_click.wav`            — General button clicks
- `buy_business.wav`        — Buying a business
- `upgrade.wav`             — Applying an upgrade
- `potion_use.wav`          — Using any potion
- `ui_success.wav`          — Positive feedback
- `ui_danger.wav`           — Dangerous action (like reset)

## Tips
- Keep sounds short (0.3s – 1.5s for most effects).
- Normalize volume between files.
- For the looping reel sound, make sure it loops cleanly.
- You can start with just the slot sounds — they will have the biggest effect on the game feel.

## How to add new sounds
1. Add the file to this folder.
2. Add the name → filename mapping in `audio.py` inside `sound_definitions`.
3. Call `audio.play("your_sound_name")` from the game code.

## Удобный конвертер (рекомендуется)
Если у тебя есть MP3 файлы в папке Downloads, запусти скрипт из корня проекта:

```bash
python convert_sounds.py
```

Он поможет:
- Выбрать нужные MP3 файлы
- Сопоставить их с правильными названиями звуков
- Автоматически конвертировать в .wav (самый надёжный формат для Pygame) и положить в `assets/sounds/`
