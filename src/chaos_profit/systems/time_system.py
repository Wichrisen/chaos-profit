"""
TimeSystem — handles all time-based game mechanics.

This is the single place where we apply the passage of time to the game state.
Both the live Game and the offline progress in SaveSystem use this.

Currently handles:
- Kloneta regeneration
- Bizneta income from businesses (base)
- Client gain/loss based on effective rates from effects
- Effect expiration over time
"""

from datetime import datetime, timezone

from ..core.models import PlayerState


class TimeSystem:
    def __init__(self, effect_system):
        self.effect_system = effect_system

    def apply_time(self, state: PlayerState, seconds: float) -> None:
        """
        Apply all time-based mechanics for the given number of seconds.
        This method is idempotent and safe to call with any positive number.
        """
        if seconds <= 0:
            return

        self._apply_kloneta_regen(state, seconds)
        self._apply_bizneta_income(state, seconds)
        self._apply_client_changes(state, seconds)

        # Always process effect expirations
        self.effect_system.process_time_effects(state, seconds)

    # ------------------------------------------------------------------
    # Individual mechanics
    # ------------------------------------------------------------------

    def _apply_kloneta_regen(self, state: PlayerState, seconds: float) -> None:
        from datetime import timedelta

        REGEN_INTERVAL = 10 * 60  # 10 minutes
        MAX_KLONETA = 5

        if state.kloneta >= MAX_KLONETA:
            return

        time_since_last = (datetime.now(timezone.utc) - state.kloneta_last_regen_at).total_seconds() + seconds

        if time_since_last < REGEN_INTERVAL:
            return

        cycles = int(time_since_last // REGEN_INTERVAL)
        gained = min(cycles, MAX_KLONETA - state.kloneta)

        if gained > 0:
            state.kloneta += gained
            used_time = gained * REGEN_INTERVAL
            state.kloneta_last_regen_at += timedelta(seconds=used_time)

    def _apply_bizneta_income(self, state: PlayerState, seconds: float) -> None:
        """Income now comes primarily from clients."""
        if not state.businesses:
            return

        minutes = seconds / 60.0
        total_income = 0.0

        for business in state.businesses.values():
            if business.clients <= 0:
                continue

            # Get how much the effects are currently multiplying client-related stats
            effective_gain = self.effect_system.get_effective_client_gain_per_minute(business)
            base_gain = business.base_client_gain_per_minute or 1.0
            client_multiplier = effective_gain / base_gain if base_gain > 0 else 1.0

            # Bizneta income = clients * rate_per_client * effect_multiplier
            income = (
                business.clients
                * business.bizneta_per_client_per_minute
                * client_multiplier
                * minutes
            )
            total_income += income

        if total_income > 0:
            state.bizneta += total_income
            # We can print it from Game level if we want visibility

    def _apply_client_changes(self, state: PlayerState, seconds: float) -> None:
        if not state.businesses:
            return

        minutes = seconds / 60.0
        total_change = 0.0

        for business in state.businesses.values():
            effective_gain = self.effect_system.get_effective_client_gain_per_minute(business)
            delta = effective_gain * minutes

            business.clients += delta
            total_change += delta

            if business.clients < 0:
                business.clients = 0.0

        # Note: We don't print here because this system is used both live and offline.
        # Logging is done at a higher level (Game).
