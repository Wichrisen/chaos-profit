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

    def get_effective_client_gain_per_minute(self, business: Business, chaos_pressure: float = 1.0) -> float:
        """
        Returns the final client gain speed for a business after all active effects.
        Negative effects are amplified by current chaos_pressure.
        """
        base = business.base_client_gain_per_minute

        if not business.effects:
            return base

        multiplier = 1.0
        for effect in business.effects:
            strength = effect.strength

            # Only negative effects (debuffs) are made worse by high Ratysurd
            if strength < 0:
                strength *= chaos_pressure

            multiplier *= (1.0 + strength)

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

    def remove_all_negative_effects(self, state: PlayerState) -> int:
        """
        Removes all currently negative effects from all businesses.
        Returns how many effects were removed.
        Used by regular potions and Permanent Cleanse.
        """
        removed = 0
        for business in state.businesses.values():
            before = len(business.effects)
            business.effects = [e for e in business.effects if e.strength >= 0]
            removed += before - len(business.effects)
        return removed

    def apply_chaos_suppression(self, state: PlayerState, duration_minutes: int = 10) -> None:
        """
        Activates temporary Ratysurd suppression.
        For the prototype we store it on the state.
        """
        now = datetime.now(timezone.utc)
        state.chaos_suppression_until = now + timedelta(minutes=duration_minutes)
