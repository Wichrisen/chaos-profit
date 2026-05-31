"""
Asset loader for Хаос & Прибыль.

Currently handles slot machine symbols (clean + corrupted variants).
Designed to be zero-dependency beyond pygame and to fail gracefully:
missing files → emoji/text fallback everywhere.
"""

from pathlib import Path
from typing import Optional, Dict
import pygame


# === Paths ===
_UI_PYGAME_DIR = Path(__file__).parent
# Project root = 3 levels up from the ui_pygame/ directory (ui_pygame → chaos_profit → src → root)
PROJECT_ROOT = _UI_PYGAME_DIR.parent.parent.parent
SYMBOLS_DIR = PROJECT_ROOT / "assets" / "images" / "symbols"


# === Logical symbol keys used in drawing code ===
# Wave 1 (core)
SLOT_SYMBOLS = [
    "bizneta", "clients", "potion",
    # Wave 2 — businesses (middle reel) + god-tier rares
    "bakery", "debts", "echo", "second", "whisper", "razlom", "never",
    "rare_cleanse", "rare_chaos",
]


def _find_symbol_file(logical: str, variant: str) -> Optional[Path]:
    """Look for slot_<logical>_<variant>.{png,jpg,jpeg}"""
    for ext in (".png", ".jpg", ".jpeg"):
        p = SYMBOLS_DIR / f"slot_{logical}_{variant}{ext}"
        if p.exists():
            return p
    return None


def _make_dark_pixels_transparent(surf: pygame.Surface, threshold: int = 22) -> pygame.Surface:
    """
    Simple pure-pygame helper: any pixel darker than threshold in all channels
    gets its alpha reduced (makes black backgrounds from generated JPGs blend
    nicely on our dark reels). Non-destructive to bright icon content.
    """
    if not surf.get_flags() & pygame.SRCALPHA:
        surf = surf.convert_alpha()

    w, h = surf.get_size()
    # Lock for pixel access (fast path)
    try:
        surf.lock()
        for y in range(h):
            for x in range(w):
                r, g, b, a = surf.get_at((x, y))
                if r <= threshold and g <= threshold and b <= threshold:
                    # Make very dark pixels more transparent, keep a little for edge softness
                    new_alpha = int(a * 0.15)
                    surf.set_at((x, y), (r, g, b, new_alpha))
    finally:
        surf.unlock()
    return surf


# Cache
_slot_sprites: Dict[str, Dict[str, Optional[pygame.Surface]]] = {}
_sprites_loaded = False


def load_slot_sprites() -> Dict[str, Dict[str, Optional[pygame.Surface]]]:
    """
    Load all known slot symbols (clean + corrupted).

    Returns:
        {
            "bizneta": {"clean": Surface|None, "corrupted": Surface|None},
            ...
        }
    """
    global _slot_sprites, _sprites_loaded
    if _sprites_loaded:
        return _slot_sprites

    _slot_sprites = {}

    for key in SLOT_SYMBOLS:
        _slot_sprites[key] = {"clean": None, "corrupted": None}

        for variant in ("clean", "corrupted"):
            path = _find_symbol_file(key, variant)
            if path:
                try:
                    raw = pygame.image.load(str(path))
                    # Do NOT call convert_alpha() here — it requires an active display on some platforms (macOS + pygame-ce).
                    # We will convert on first use in the UI after the screen exists.
                    processed = raw
                    if processed.get_width() > 160 or processed.get_height() > 160:
                        processed = pygame.transform.smoothscale(processed, (128, 128))
                    _slot_sprites[key][variant] = processed
                    print(f"[Assets] Loaded slot sprite: {path.name}")
                except Exception as e:
                    print(f"[Assets] WARNING: failed to load {path}: {e}")
            # else: silent — we will fallback to emoji

    _sprites_loaded = True
    return _slot_sprites


def get_slot_sprite(logical_key: str, corrupted: bool = False) -> Optional[pygame.Surface]:
    """Convenience accessor. Returns None if not loaded / missing."""
    sprites = load_slot_sprites()
    entry = sprites.get(logical_key)
    if not entry:
        return None
    variant = "corrupted" if corrupted else "clean"
    return entry.get(variant)


def has_sprite(logical_key: str) -> bool:
    """Quick check if at least one variant exists for this key."""
    sprites = load_slot_sprites()
    entry = sprites.get(logical_key, {})
    return bool(entry.get("clean") or entry.get("corrupted"))


def get_available_slot_keys() -> list:
    return list(load_slot_sprites().keys())


def prepare_sprites_for_display():
    """
    Call this once AFTER pygame.display.set_mode() has been called.
    Converts all loaded sprites to the display format + alpha and applies
    the dark-pixel transparency pass so they blend beautifully on dark reels.
    """
    sprites = load_slot_sprites()
    for key, variants in sprites.items():
        for variant, surf in list(variants.items()):
            if surf is None:
                continue
            try:
                if not (surf.get_flags() & pygame.SRCALPHA):
                    surf = surf.convert_alpha()
                # Now safe to do the expensive per-pixel work
                surf = _make_dark_pixels_transparent(surf, threshold=26)
                # Downscale if still huge
                if surf.get_width() > 140:
                    surf = pygame.transform.smoothscale(surf, (128, 128))
                variants[variant] = surf
            except Exception as e:
                print(f"[Assets] prepare warning for {key}/{variant}: {e}")


# === UI Icons (status bar, buttons, effects, potions, etc.) ===
UI_DIR = PROJECT_ROOT / "assets" / "images" / "ui"

_ui_icons: Dict[str, Optional[pygame.Surface]] = {}
_ui_icons_loaded = False


def _find_ui_icon(name: str) -> Optional[Path]:
    for ext in (".png", ".jpg", ".jpeg"):
        p = UI_DIR / f"ui_{name}{ext}"
        if p.exists():
            return p
    return None


def load_ui_icons():
    """Pre-scan (optional, icons load lazily on first get_ui_icon call)."""
    global _ui_icons_loaded
    _ui_icons_loaded = True
    # We do lazy loading on demand for simplicity


def get_ui_icon(name: str, size: Optional[int] = None) -> Optional[pygame.Surface]:
    """
    Load a UI icon by logical name (without 'ui_' prefix).

    Example: get_ui_icon("bizneta") looks for ui_bizneta.png / .jpg
    Returns a Surface (converted on first use after display init).
    Caches the result.
    """
    if name in _ui_icons:
        surf = _ui_icons[name]
    else:
        path = _find_ui_icon(name)
        if not path:
            _ui_icons[name] = None
            return None

        try:
            raw = pygame.image.load(str(path))
            surf = raw
            if size and (surf.get_width() != size or surf.get_height() != size):
                surf = pygame.transform.smoothscale(surf, (size, size))
            _ui_icons[name] = surf
            print(f"[Assets] Loaded UI icon: {path.name}")
        except Exception as e:
            print(f"[Assets] WARNING: failed to load UI icon {path}: {e}")
            _ui_icons[name] = None
            return None

    # Lazy convert after display exists (safe on macOS + pygame-ce)
    if surf and not (surf.get_flags() & pygame.SRCALPHA):
        try:
            surf = surf.convert_alpha()
            _ui_icons[name] = surf
        except Exception:
            pass  # will try again next time or when blitting

    if size and surf and (surf.get_width() != size or surf.get_height() != size):
        surf = pygame.transform.smoothscale(surf, (size, size))
        _ui_icons[name] = surf

    return surf


def prepare_ui_icons_for_display():
    """Call after pygame.display.set_mode() to convert all already-loaded UI icons."""
    for name, surf in list(_ui_icons.items()):
        if surf and not (surf.get_flags() & pygame.SRCALPHA):
            try:
                _ui_icons[name] = surf.convert_alpha()
            except Exception:
                pass


# Warm the cache on import (cheap — only does disk work when actually called first time)
# We call load explicitly from main.py at startup for clear logging.
