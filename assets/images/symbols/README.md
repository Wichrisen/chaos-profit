# Slot Machine Symbols — Хаос & Прибыль

Square transparent PNG icons for the slot reels.

## Technical Spec
- **Size**: 128×128 px (native). Pygame will scale if needed.
- **Format**: PNG with alpha channel (no background).
- **Safe zone**: Important icon content inside central 96×96 area.
- **Style**: Dark cyber-ocean / glitch art. High contrast, readable even at small size.
- **Two states per symbol**:
  - `_clean.png` — base "ocean" version (used at Ratysurd < ~10-11)
  - `_corrupted.png` — Glitch+ corrupted version (heavy digital distortion, chromatic aberration, scanlines, tears, deep reds/blacks/magentas). "Less blood, more digital corruption and tearing" per approved direction.

## Naming Convention (strict)
```
slot_<theme>_<state>.png
```

Examples (wave 1 + wave 2):
- `slot_bizneta_clean.jpg` / `_corrupted.jpg`
- `slot_clients_clean.jpg` / `_corrupted.jpg`
- `slot_potion_clean.jpg` / `_corrupted.jpg`
- `slot_bakery_clean.jpg` / `_corrupted.jpg`
- `slot_razlom_clean.jpg` / `_corrupted.jpg`
- `slot_rare_cleanse_clean.jpg` / `_corrupted.jpg`
- `slot_rare_chaos_clean.jpg` / `_corrupted.jpg`

All use the same strict pattern: slot_<theme>_<state>.jpg (or .png)

## Usage in Code
- Loader returns dict: `{"bizneta": {"clean": Surface, "corrupted": Surface}, ...}`
- During reel render:
  - If Ratysurd >= 12 or result contains "cursed"/"CHAOTIC" → prefer corrupted variant when available.
  - Else clean.
- During high-chaos spinning: can mix a few corrupted frames in the scroll pool for extra unease.
- Always provide graceful fallback to emoji/text rendering if file missing or load fails.

## Wave 1 (DONE ✅)
- Bizneta, Clients, Potion (regular) — clean + Glitch+ corrupted
- All 6 sprites generated, loaded, and rendering on stopped reels with chaos tint.

## Wave 2 (in progress)
Business drops (middle reel highlights):
- `slot_bakery_clean.jpg` / `_corrupted.jpg`     — Полуночная Булочная
- `slot_debts_clean.jpg` / `_corrupted.jpg`      — Бюро Незавершённых Дел
- `slot_echo_clean.jpg` / `_corrupted.jpg`       — Эхо-Бар
- `slot_second_clean.jpg` / `_corrupted.jpg`     — Второе Я
- `slot_whisper_clean.jpg` / `_corrupted.jpg`    — Агентство Шёпот
- `slot_razlom_clean.jpg` / `_corrupted.jpg`     — Разлом-Экспресс
- `slot_never_clean.jpg` / `_corrupted.jpg`      — Рынок Никогда

Rare / god-tier:
- `slot_rare_cleanse_clean.jpg` / `_corrupted.jpg`        — Permanent Cleanse
- `slot_rare_chaos_clean.jpg` / `_corrupted.jpg`          — Chaos Suppression

(Using .jpg for now because of generator output; loader handles .png/.jpg transparently. We can batch-convert to PNG+alpha later if desired.)

## Naming Convention (strict)

## How to add / replace a sprite
1. Drop the new PNG in this folder with exact name.
2. No code change needed if loader auto-discovers by filename.
3. (Optional) Run game with debug to verify.

## Generation Notes
All sprites generated via xAI Imagine with consistent "Glitch+" corrupted language after multiple iterations:
- Clean base: elegant, dark, slightly uneasy but still "professional" crime empire.
- Corrupted: violent digital glitch, heavy RGB split, horizontal tears, static, scanlines, shape distortion. Still clearly the same object.

Maintain this language across all future symbols for visual cohesion.
