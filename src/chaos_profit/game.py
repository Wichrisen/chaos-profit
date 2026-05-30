"""
Game orchestrator.

Responsible for:
- Holding the current game state
- Managing SaveSystem
- Autosaving (every 60 seconds by default)
- Clean shutdown
"""

from datetime import datetime, timezone

from .core.models import PlayerState
from .systems.save_system import SaveSystem
from .systems.effect_system import EffectSystem


class Game:
    AUTOSAVE_INTERVAL_SECONDS = 60

    def __init__(self):
        self.save_system = SaveSystem()
        self.state: PlayerState = self.save_system.load()

        self.effect_system = EffectSystem()
        self._last_autosave = datetime.now(timezone.utc)

    def save(self) -> None:
        """Force save the current state."""
        self.save_system.save(self.state)
        self._last_autosave = datetime.now(timezone.utc)

    def reset_to_factory(self) -> None:
        """Completely reset the game."""
        self.state = self.save_system.reset_to_factory()
        self._last_autosave = datetime.now(timezone.utc)

    def tick(self, dt: float = 0.0) -> None:
        """
        Should be called regularly (e.g. in the main loop).
        Handles autosaving for now.
        Later this can also drive other time-based systems.
        """
        now = datetime.now(timezone.utc)
        if (now - self._last_autosave).total_seconds() >= self.AUTOSAVE_INTERVAL_SECONDS:
            self.save()

    def advance_time(self, seconds: float) -> None:
        """
        Advance game time by a given amount of seconds.
        This is the main method for applying time-based mechanics
        (both in real-time and during offline progress).
        """
        if seconds <= 0:
            return

        print(f"[Game] Advancing time by {seconds:.0f} seconds...")

        # Apply time-based mechanics in order
        self._apply_kloneta_regen(seconds)
        self._apply_bizneta_income(seconds)
        self._apply_client_changes(seconds)

        # Process effects (expiration + future continuous effects)
        self.effect_system.process_time_effects(self.state, seconds)

        # Update last played time
        self.state.last_played_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Time-based mechanics (implemented step by step)
    # ------------------------------------------------------------------

    def _apply_bizneta_income(self, seconds: float) -> None:
        """Начисление Бизнет от всех бизнесов за прошедшее время (базовое, без эффектов пока)."""
        if not self.state.businesses:
            return

        minutes = seconds / 60.0
        total_income = 0.0

        for business in self.state.businesses.values():
            # На этом шаге — только база. Эффекты добавим позже.
            income = business.base_bizneta_per_minute * minutes
            total_income += income

        if total_income > 0:
            self.state.bizneta += total_income
            print(f"  → Earned +{total_income:.2f} Bizneta from businesses")

    def _apply_client_changes(self, seconds: float) -> None:
        """
        Apply client gain or loss over time for all businesses,
        using the effective rate from the EffectSystem.
        """
        if not self.state.businesses:
            return

        minutes = seconds / 60.0
        total_client_change = 0.0

        for business in self.state.businesses.values():
            effective_gain = self.effect_system.get_effective_client_gain_per_minute(business)
            client_delta = effective_gain * minutes

            business.clients += client_delta
            total_client_change += client_delta

            # Prevent clients from going negative
            if business.clients < 0:
                business.clients = 0.0

        if abs(total_client_change) > 0.01:
            direction = "gained" if total_client_change > 0 else "lost"
            print(f"  → Clients {direction} {abs(total_client_change):.2f} across all businesses")

    def _apply_kloneta_regen(self, seconds: float) -> None:
        """
        Regenerate Kloneta based on time passed.
        Rule: +1 Kloneta every 10 minutes, max 5.
        """
        from datetime import timedelta

        REGEN_INTERVAL = 10 * 60  # 10 minutes in seconds
        MAX_KLONETA = 5

        if self.state.kloneta >= MAX_KLONETA:
            return

        now = datetime.now(timezone.utc)

        # Calculate how much time has actually passed since last regen
        time_since_last = (now - self.state.kloneta_last_regen_at).total_seconds() + seconds

        if time_since_last < REGEN_INTERVAL:
            return

        cycles = int(time_since_last // REGEN_INTERVAL)
        gained = min(cycles, MAX_KLONETA - self.state.kloneta)

        if gained > 0:
            self.state.kloneta += gained
            print(f"  → Regenerated +{gained} Kloneta (now {self.state.kloneta}/{MAX_KLONETA})")

            # Advance the last regen time by the exact amount used
            used_time = gained * REGEN_INTERVAL
            self.state.kloneta_last_regen_at += timedelta(seconds=used_time)

    def shutdown(self) -> None:
        """Call this on game exit to ensure everything is saved."""
        self.save()
        print("[Game] Shutdown complete. Progress saved.")