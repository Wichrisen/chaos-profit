# Architecture Overview — Chaos & Profit

**Goal**: Build a clean, testable, and extensible foundation so that adding new mechanics later causes minimal regret.

## Core Principles

- **Purity of the Core**: The `core/` layer must remain 100% pure (no time, no filesystem, no global random).
- **Single Source of Truth**: `PlayerState` contains the entire game state and is the only thing that gets saved/loaded.
- **Systems Layer**: All time-dependent and state-mutating logic lives in `systems/`.
- **SaveSystem is Critical**: It handles loading, offline progress, autosave, and full reset.
- **Effects live inside Business**: As decided during design.

## High-Level Layers

```
src/chaos_profit/
├── core/                 # Pure data models + rules (no side effects)
│   └── models.py
├── systems/              # Game logic (time, state changes, calculations)
│   └── save_system.py
├── ui_console/           # First prototype UI
├── ui_pygame/            # Future graphical UI
└── game.py               # Orchestrator (will be added)
```

## Current Status (30 May 2026)

- `PlayerState`, `Business`, and `Effect` models are defined.
- Basic `SaveSystem` skeleton with load/save/reset/offline hooks exists.
- All major mechanics (businesses, clients, deals, effects, 3 potion types, Ratysurd) are designed at high level.

## Next Priorities

1. Implement real offline progress calculation in SaveSystem.
2. Implement proper serialization/deserialization (with datetime handling).
3. Start building EffectSystem + ClientSystem.
4. Create a minimal console loop to test the core loop.

## Important Decisions

- Effects are stored per-business.
- `base_client_gain_per_minute` is recalculated when Ratysurd level increases.
- Cleanup of expired effects is lazy (mainly on potion use).
- Effects will be made universal over time (not only client speed).
- Full reset must be reliable and leave no dirty data.
