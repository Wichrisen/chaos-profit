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

        # Get current pressure (affected by Chaos Suppression potion)
        pressure = self.get_effective_chaos_pressure()

        # Delegate all time-based logic to TimeSystem
        self.time_system.apply_time(self.state, seconds, chaos_pressure=pressure)

        # Track total time and handle Ratysurd growth
        self.state.total_time_advanced += seconds
        self._check_ratysurd_growth()

        # Check for new deals
        self.deal_system.update(self.state, seconds)

        # Update last played time
        self.state.last_played_at = datetime.now(timezone.utc)

    def _check_ratysurd_growth(self) -> None:
        """
        Simple automatic Ratysurd growth for the prototype.
        Every ~25-30 minutes of total played time → +1 level (capped at 15 for now).
        """
        thresholds = [25, 55, 90, 130, 175, 225, 280, 340, 405, 475, 550, 630, 715, 805]  # cumulative minutes

        current_level = self.state.ratysurd_level
        minutes_played = self.state.total_time_advanced / 60

        for i, threshold in enumerate(thresholds):
            target_level = i + 2  # level 2 at first threshold, etc.
            if minutes_played >= threshold and current_level < target_level:
                self.state.ratysurd_level = target_level
                print(f"\n⚠️  РЕЙТИСУРД ПОВЫСИЛСЯ ДО {target_level}! Мир становится опаснее...")

                # Reset last played time reference for pressure feeling
                self.state.last_played_at = datetime.now(timezone.utc)
                break

        # Hard cap for prototype
        if self.state.ratysurd_level > 15:
            self.state.ratysurd_level = 15

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

    def get_chaos_pressure_multiplier(self) -> float:
        """
        Returns how much 'harder' the game currently is due to Ratysurd.
        This is a global multiplier applied to negative effect strength.
        Tuned for MVP feel: noticeable growth after level 6-7.
        """
        level = self.state.ratysurd_level

        if level <= 3:
            return 1.0
        elif level <= 6:
            return 1.0 + (level - 3) * 0.08   # slow ramp
        else:
            # Stronger growth after the "danger zone" starts
            return 1.24 + (level - 6) * 0.12

    def get_effective_chaos_pressure(self) -> float:
        """
        The actual pressure the player is feeling right now.
        If Chaos Suppression potion is active, pressure is heavily reduced.
        """
        base = self.get_chaos_pressure_multiplier()

        if self.has_active_chaos_suppression():
            # Suppression makes high Ratysurd feel much more manageable
            return max(1.0, base * 0.45)

        return base

    def spin_slot(self) -> Optional[SpinResult]:
        """Spin the slot machine. Returns SpinResult or None if not enough Kloneta."""
        if not self.slot_system.can_spin(self.state):
            return None
        result = self.slot_system.spin(self.state)
        return result