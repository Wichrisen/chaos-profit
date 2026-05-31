# Packaging / Build Configuration

This folder contains everything related to building distributable versions of the game.

## Current Status (as of late May 2026)

- We are preparing the project for proper distribution.
- A starter PyInstaller `.spec` file is included (`chaos_profit.spec`).
- The goal is to produce clean Windows `.exe` builds (macOS and Linux are lower priority for now).

## How to build (once ready)

```bash
# From the project root
pyinstaller packaging/chaos_profit.spec
```

The resulting executable will be in the `dist/` folder.

## Notes

- Assets are included via the `datas` section.
- We use the package entry point `src.chaos_profit.ui_pygame.__main__`.
- Later we will likely add:
  - Proper icon
  - Version embedding
  - One-folder vs one-file decision
  - GitHub Actions workflow for automatic builds

## DO NOT commit build artifacts

The following are already ignored by `.gitignore`:
- `build/`
- `dist/`
- `*.spec~` (backup spec files)
