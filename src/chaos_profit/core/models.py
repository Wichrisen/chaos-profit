"""
Core data models for Chaos & Profit.

Design principles:
- This module must remain 100% pure (no time, no I/O, no randomness).
- All logic that depends on time or side effects lives in the systems layer.
- Effects are stored inside each Business (as decided).
- PlayerState is the single source of truth for the entire game state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict


@dataclass
class Effect:
    """
    A single effect applied to a specific business.

    strength: multiplier to the target stat.
        Example: -0.45 means -45% to client gain speed.
    is_permanent: True = стойкий (removed only by potion), False = temporary.
    """
    effect_id: str
    strength: float
    is_permanent: bool
    applied_at: datetime
    expires_at: datetime | None = None


@dataclass
class Business:
    """Represents one instance of a business (niche)."""
    niche_id: str
    clients: float = 0.0

    # Effects that are currently applied to this business
    effects: List[Effect] = field(default_factory=list)

    # Base values without effects.
    # These are recalculated when Ratysurd level changes.
    base_client_gain_per_minute: float = 0.0

    # How much Bizneta this business earns per client per minute (base).
    # Total income = clients * bizneta_per_client_per_minute * effect_multipliers
    bizneta_per_client_per_minute: float = 0.15  # Default: 0.15 Bizneta per client per minute

    # Upgrades for this business (simple MVP system)
    # Possible keys: "growth", "efficiency", "resilience"
    # Each level gives a permanent bonus to this business only.
    upgrades: Dict[str, int] = field(default_factory=dict)

    def get_client_gain_multiplier_from_upgrades(self) -> float:
        """Returns multiplier from upgrades (e.g. 1.15 for level 1 Growth)."""
        level = self.upgrades.get("growth", 0)
        return 1.0 + level * 0.15

    def get_bizneta_per_client_multiplier_from_upgrades(self) -> float:
        """Returns multiplier from upgrades for bizneta income."""
        level = self.upgrades.get("efficiency", 0)
        return 1.0 + level * 0.12

    def get_resilience_multiplier(self) -> float:
        """
        Returns a multiplier that reduces negative effect strength.
        Level 1 Resilience → negative effects are 10% weaker on this business.
        """
        level = self.upgrades.get("resilience", 0)
        return 1.0 - level * 0.10  # Makes negative effects less severe


@dataclass
class PlayerState:
    """
    The complete state of the player's game.

    This is the only object that gets saved/loaded.
    """
    version: int = 1
    last_played_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    ratysurd_level: int = 1

    # Resources
    kloneta: int = 5
    kloneta_last_regen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    bizneta: float = 0.0

    # All businesses the player currently owns.
    # Key = niche_id, Value = Business instance.
    # Duplicates are allowed (multiple businesses of same niche).
    businesses: Dict[str, Business] = field(default_factory=dict)

    # Potions inventory
    regular_potions: Dict[str, int] = field(default_factory=dict)  # e.g. {"2min": 3, "30min": 1}
    permanent_cleanse_potions: int = 0
    chaos_suppression_potions: int = 0   # New very rare potion (10 min fixed)

    # Simple statistics
    total_clients_ever: float = 0.0
    total_bizneta_earned: float = 0.0

    # Temporary global effects
    chaos_suppression_until: datetime | None = None  # Activated by the rare Chaos Suppression potion

    # Progression tracking
    total_time_advanced: float = 0.0  # Total seconds the player has advanced time (for Ratysurd growth)

    @classmethod
    def new_game(cls) -> "PlayerState":
        """Factory method for a completely fresh game state."""
        now = datetime.now(timezone.utc)
        return cls(
            ratysurd_level=1,
            kloneta=5,
            kloneta_last_regen_at=now,
            last_played_at=now,
            bizneta=0.0,
            businesses={},
            regular_potions={},
            permanent_cleanse_potions=0,
            chaos_suppression_potions=0,
            chaos_suppression_until=None,
            total_time_advanced=0.0,
        )
