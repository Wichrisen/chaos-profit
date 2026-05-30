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
from .systems.time_system import TimeSystem
from .systems.deal_system import DealSystem
from .systems.slot_system import SlotSystem, SpinResult


class Game:
    AUTOSAVE_INTERVAL_SECONDS = 60

    def __init__(self):
        self.save_system = SaveSystem()
        self.state: PlayerState = self.save_system.load()

        self.effect_system = EffectSystem()
        self.time_system = TimeSystem(self.effect_system)
        self.deal_system = DealSystem()
        self.slot_system = SlotSystem()
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

        # Delegate all time-based logic to TimeSystem
        self.time_system.apply_time(self.state, seconds)

        # Check for new deals
        self.deal_system.update(self.state, seconds)

        # Update last played time
        self.state.last_played_at = datetime.now(timezone.utc)

    def shutdown(self) -> None:
        """Call this on game exit to ensure everything is saved."""
        self.save()
        print("[Game] Shutdown complete. Progress saved.")

    # ------------------------------------------------------------------
    # Potion usage
    # ------------------------------------------------------------------

    def use_regular_potion(self, duration: str) -> bool:
        """
        Uses one regular potion of the given duration (e.g. '2min', '10min').
        Removes all current negative effects from all businesses.
        """
        if self.state.regular_potions.get(duration, 0) <= 0:
            return False

        self.state.regular_potions[duration] -= 1
        if self.state.regular_potions[duration] <= 0:
            del self.state.regular_potions[duration]

        removed = self.effect_system.remove_all_negative_effects(self.state)
        print(f"Used {duration} potion. Removed {removed} negative effects.")
        return True

    def use_permanent_cleanse(self) -> bool:
        """Uses the rare Permanent Cleanse potion."""
        if self.state.permanent_cleanse_potions <= 0:
            return False

        self.state.permanent_cleanse_potions -= 1
        removed = self.effect_system.remove_all_negative_effects(self.state)
        print(f"Used Permanent Cleanse. Permanently removed {removed} negative effects.")
        return True

    def use_chaos_suppression(self) -> bool:
        """Uses the very rare Chaos Suppression potion (10 min fixed)."""
        if self.state.chaos_suppression_potions <= 0:
            return False

        self.state.chaos_suppression_potions -= 1
        self.effect_system.apply_chaos_suppression(self.state, duration_minutes=10)
        print("Used Chaos Suppression potion. Ratysurd pressure greatly reduced for 10 minutes.")
        return True

    def has_active_chaos_suppression(self) -> bool:
        if not self.state.chaos_suppression_until:
            return False
        return datetime.now(timezone.utc) < self.state.chaos_suppression_until

    def spin_slot(self) -> Optional[SpinResult]:
        """Spin the slot machine. Returns SpinResult or None if not enough Kloneta."""
        if not self.slot_system.can_spin(self.state):
            return None
        result = self.slot_system.spin(self.state)
        return result