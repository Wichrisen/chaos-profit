# UI Elements — Хаос & Прибыль

Small, crisp icons for the interface (status bar, buttons, modals, effects).

## Technical Spec
- **Recommended sizes**:
  - Status bar / inline: 28×28 or 32×32
  - Action buttons: 32×32 or 40×40 (placed left of text)
  - Inventory / modals: 48×48 or 56×56
  - Larger decorative: 64×64 max for now
- **Format**: PNG with alpha (transparent background)
- **Style consistency**: Same dark cyber-noir / glitch art language as slot symbols.
  - Clean: elegant, high-contrast, dark ocean + gold + subtle teal
  - "Sick" / high Ratysurd: we usually apply runtime red tint + slight jitter instead of separate files (cheaper and more dynamic). Only create dedicated corrupted variants when the icon itself should look *wrong* (e.g. Ratysurd icon at 14+).
- **Safe zone**: Content centered, with 4-6 px padding from edges.

## Naming Convention
```
ui_<purpose>[_variant].png
```

Examples:
- `ui_bizneta.png`
- `ui_kloneta.png`
- `ui_ratysurd.png`
- `ui_potion_time.png`
- `ui_potion_cleanse.png`
- `ui_potion_chaos.png`
- `ui_action_shop.png`
- `ui_action_upgrades.png`
- `ui_action_inventory.png`
- `ui_action_reset.png`
- `ui_effect_scar.png`, `ui_effect_curse.png` (for business cards)

## Loader
Icons are loaded via `assets.py` (same module as slot sprites).  
Call `get_ui_icon("bizneta")` etc.  
Graceful fallback to emoji / nothing if missing.

## Priority Order (suggested)

**Wave 1 (high visual impact, quick win)**
1. Top bar resources: bizneta, kloneta, ratysurd
2. Potion icons (3 types) — used in inventory + toasts
3. 4 action button icons (shop, upgrades, inventory, reset)

**Wave 2**
- Effect / debuff badges for businesses
- Compact logo variants (clean + corrupted)
- Spin button icon / decoration
- Deal / toast icons

## Generation Rules
- Keep the same "Glitch+" corrupted philosophy where applicable.
- Icons must remain readable at 28-32 px.
- High contrast edges.
- Slight inner glow or bevel for premium feel even on dark backgrounds.

Maintain visual cohesion with the slot symbol set.
