"""
EffectSystem — handles all logic related to effects on businesses.

Responsibilities:
- Calculating effective stats after applying effects (e.g. client gain speed)
- Processing time passage (expiring temporary effects)
- Lazy cleanup of expired effects

Effects are stored inside each Business (as decided).
"""

from datetime import datetime, timezone, timedelta
from typing import List

from ..core.models import PlayerState, Business, Effect


class EffectSystem:
    def __init__(self):
        pass

    def get_effective_client_gain_per_minute(self, business: Business) -> float:
        """
        Returns the final client gain speed for a business after all active effects.
        Currently only supports multiplicative effects on client gain.
        """
        base = business.base_client_gain_per_minute

        if not business.effects:
            return base

        multiplier = 1.0
        for effect in business.effects:
            # For now we treat all effects as multiplicative on client gain speed.
            # In the future we can expand with target + modifier_type.
            multiplier *= (1.0 + effect.strength)

        return base * multiplier

    def process_time_effects(self, state: PlayerState, seconds: float) -> None:
        """
        Advance time for all effects across all businesses.
        - Expires temporary effects that have run out.
        - (Future) Can apply continuous effects like client loss over time.
        """
        if seconds <= 0:
            return

        now = datetime.now(timezone.utc)

        for business in state.businesses.values():
            if not business.effects:
                continue

            # Remove expired temporary effects
            active_effects: List[Effect] = []
            for effect in business.effects:
                if effect.is_permanent:
                    active_effects.append(effect)
                    continue

                if effect.expires_at and effect.expires_at <= now:
                    # Effect has expired → do not keep it
                    continue

                active_effects.append(effect)

            business.effects = active_effects

    def clean_expired_effects(self, business: Business) -> None:
        """
        Force cleanup of expired temporary effects on a single business.
        Called lazily, e.g. when using a potion or viewing the business.
        """
        now = datetime.now(timezone.utc)
        business.effects = [
            e for e in business.effects
            if e.is_permanent or (e.expires_at and e.expires_at > now)
        ]

    def apply_effect(self, business: Business, effect: Effect) -> None:
        """Convenience method to add an effect to a business."""
        business.effects.append(effect)

    def has_active_negative_effects(self, business: Business) -> bool:
        """Quick check if the business currently has any negative effects."""
        return any(e.strength < 0 for e in business.effects)
