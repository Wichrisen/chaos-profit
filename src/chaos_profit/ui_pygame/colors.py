"""
Color palette for Chaos & Profit - Ocean Vibe base with Ratysurd corruption.

Base aesthetic: Minimalist + strong colors.
Ocean Vibe (low Ratysurd): Deep water blues, teal accents, clean and slightly cold.
As Ratysurd rises: Palette shifts toward darker, more oppressive, sickly, and corrupted tones.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Colors:
    # Background
    bg: Tuple[int, int, int]
    # Main panels / cards
    panel_bg: Tuple[int, int, int]
    panel_border: Tuple[int, int, int]
    # Text
    text: Tuple[int, int, int]
    text_dim: Tuple[int, int, int]
    # Accents
    accent: Tuple[int, int, int]          # Primary action / positive
    accent_danger: Tuple[int, int, int]   # Negative / chaos
    # Slot specific
    slot_bg: Tuple[int, int, int]
    slot_reel_bg: Tuple[int, int, int]
    # Resources
    bizneta: Tuple[int, int, int]
    kloneta: Tuple[int, int, int]
    # Ratysurd levels (used for dynamic tinting)
    ratysurd_low: Tuple[int, int, int]
    ratysurd_mid: Tuple[int, int, int]
    ratysurd_high: Tuple[int, int, int]
    ratysurd_extreme: Tuple[int, int, int]


# === BASE OCEAN VIBE (Ratysurd 1-4) ===
OCEAN = Colors(
    bg=(18, 26, 40),              # Deep ocean night - raised floor for visibility (was 10,18,32)
    panel_bg=(22, 32, 50),
    panel_border=(48, 78, 108),
    text=(220, 230, 240),
    text_dim=(140, 160, 180),
    accent=(60, 200, 220),        # Bright teal/cyan
    accent_danger=(220, 80, 90),
    slot_bg=(8, 14, 26),
    slot_reel_bg=(20, 35, 55),
    bizneta=(255, 215, 90),       # Gold
    kloneta=(120, 200, 255),      # Light blue
    ratysurd_low=(80, 180, 160),
    ratysurd_mid=(70, 160, 140),
    ratysurd_high=(60, 130, 110),
    ratysurd_extreme=(50, 100, 90),
)


def get_palette(ratysurd_level: int) -> Colors:
    """
    Returns a palette that gets progressively darker, colder, and more corrupted
    as Ratysurd increases.
    """
    if ratysurd_level <= 4:
        return OCEAN

    # Start shifting from ocean toward something more oppressive
    # We do a simple linear interpolation toward a "corrupted ocean" theme
    t = min((ratysurd_level - 4) / 11.0, 1.0)  # 0 at L4, 1 at L15

    def lerp(a: int, b: int, t: float) -> int:
        return int(a + (b - a) * t)

    # Target "Abyssal / Corrupted" palette
    target = Colors(
        bg=(24, 22, 30),                  # Dark but never pure black — safety floor for visibility
        panel_bg=(30, 26, 34),
        panel_border=(70, 30, 40),
        text=(200, 190, 185),
        text_dim=(110, 100, 95),
        accent=(200, 70, 90),             # Sickly red-pink
        accent_danger=(255, 50, 60),
        slot_bg=(18, 15, 22),
        slot_reel_bg=(28, 23, 30),
        bizneta=(220, 160, 60),           # Tarnished gold
        kloneta=(90, 140, 180),
        ratysurd_low=(120, 50, 60),
        ratysurd_mid=(140, 40, 50),
        ratysurd_high=(160, 30, 40),
        ratysurd_extreme=(180, 20, 30),
    )

    # Blend between OCEAN and target
    return Colors(
        bg=tuple(lerp(OCEAN.bg[i], target.bg[i], t) for i in range(3)),
        panel_bg=tuple(lerp(OCEAN.panel_bg[i], target.panel_bg[i], t) for i in range(3)),
        panel_border=tuple(lerp(OCEAN.panel_border[i], target.panel_border[i], t) for i in range(3)),
        text=tuple(lerp(OCEAN.text[i], target.text[i], t) for i in range(3)),
        text_dim=tuple(lerp(OCEAN.text_dim[i], target.text_dim[i], t) for i in range(3)),
        accent=tuple(lerp(OCEAN.accent[i], target.accent[i], t) for i in range(3)),
        accent_danger=tuple(lerp(OCEAN.accent_danger[i], target.accent_danger[i], t) for i in range(3)),
        slot_bg=tuple(lerp(OCEAN.slot_bg[i], target.slot_bg[i], t) for i in range(3)),
        slot_reel_bg=tuple(lerp(OCEAN.slot_reel_bg[i], target.slot_reel_bg[i], t) for i in range(3)),
        bizneta=tuple(lerp(OCEAN.bizneta[i], target.bizneta[i], t) for i in range(3)),
        kloneta=tuple(lerp(OCEAN.kloneta[i], target.kloneta[i], t) for i in range(3)),
        ratysurd_low=tuple(lerp(OCEAN.ratysurd_low[i], target.ratysurd_low[i], t) for i in range(3)),
        ratysurd_mid=tuple(lerp(OCEAN.ratysurd_mid[i], target.ratysurd_mid[i], t) for i in range(3)),
        ratysurd_high=tuple(lerp(OCEAN.ratysurd_high[i], target.ratysurd_high[i], t) for i in range(3)),
        ratysurd_extreme=tuple(lerp(OCEAN.ratysurd_extreme[i], target.ratysurd_extreme[i], t) for i in range(3)),
    )
