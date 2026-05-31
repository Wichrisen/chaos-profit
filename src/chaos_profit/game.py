"""
Game orchestrator.

Responsible for:
- Holding the current game state
- Managing SaveSystem
- Autosaving (every 60 seconds by default)
- Clean shutdown
"""

from datetime import datetime, timezone

from .core.models import PlayerState, Effect, Business
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
        Ratysurd growth with real, permanent world escalation.
        Catches up multiple levels if a large time chunk was advanced (offline or long session).
        Crossing 7 / 10 / 13 applies permanent "the world broke here" mechanical scars.
        """
        thresholds = [25, 55, 90, 130, 175, 225, 280, 340, 405, 475, 550, 630, 715, 805]

        minutes_played = self.state.total_time_advanced / 60
        level = self.state.ratysurd_level

        changed = False
        for i, threshold in enumerate(thresholds):
            target = i + 2
            if minutes_played >= threshold and level < target:
                level = target
                self.state.ratysurd_level = level
                self._apply_ratysurd_milestone(level)
                self.state.last_played_at = datetime.now(timezone.utc)
                changed = True

        # Hard cap
        if self.state.ratysurd_level > 15:
            self.state.ratysurd_level = 15

        if changed:
            # one final pressure reminder after possible multiple jumps
            print(f"\n(Текущий уровень Рейтисурда: {self.state.ratysurd_level})")

    def _apply_ratysurd_milestone(self, new_level: int) -> None:
        """Apply permanent world-breaking changes when crossing key thresholds."""
        if new_level in self.state.triggered_milestones:
            return  # already fired

        self.state.triggered_milestones.append(new_level)

        if new_level == 7:
            print("\n" + "◈" * 60)
            print("  РЕЙТИСУРД ДОСТИГ 7 — ПЕРВЫЕ ТРЕЩИНЫ В РЕАЛЬНОСТИ")
            print("  Тёмные сделки теперь появляются чаще. Мир начал замечать тебя.")
            print("  Все будущие негативные эффекты от провалов стали чуть опаснее.")
            print("◈" * 60)

            # Permanent mechanical shift: global +12% strength to all future negative effects
            # We simulate this by giving every existing business a small "world is watching" scar
            for biz in self.state.businesses.values():
                scar = Effect(
                    effect_id="world_crack_7",
                    strength=-0.12,
                    is_permanent=True,
                    applied_at=datetime.now(timezone.utc),
                )
                biz.effects.append(scar)

        elif new_level == 10:
            print("\n" + "▓" * 60)
            print("  РЕЙТИСУРД 10 — ЗАВЕСА ПРОРВАНА")
            print("  Хаос теперь активно вползает в твои предприятия даже без сделок.")
            print("  Слот и тёмные сделки стали значительно рискованнее. Обратного пути нет.")
            print("▓" * 60)

            for biz in self.state.businesses.values():
                scar = Effect(
                    effect_id="veil_thinned",
                    strength=-0.18,
                    is_permanent=True,
                    applied_at=datetime.now(timezone.utc),
                )
                biz.effects.append(scar)

            # Second scar for extra weight at this milestone
            for biz in self.state.businesses.values():
                scar2 = Effect(
                    effect_id="something_watches",
                    strength=-0.09,
                    is_permanent=True,
                    applied_at=datetime.now(timezone.utc),
                )
                biz.effects.append(scar2)

        elif new_level == 13:
            print("\n" + "◉" * 60)
            print("  РЕЙТИСУРД 13 — МИР ГОЛОДЕН")
            print("  Даже успешные действия теперь иногда оставляют шрамы.")
            print("  Ты больше не гость в этом мире. Ты — часть его безумия.")
            print("  С этого момента почти все негативные эффекты будут стойкими.")
            print("◉" * 60)

            for biz in self.state.businesses.values():
                scar = Effect(
                    effect_id="world_hungry",
                    strength=-0.25,
                    is_permanent=True,
                    applied_at=datetime.now(timezone.utc),
                )
                biz.effects.append(scar)

        elif new_level == 15:
            print("\n" + "◉◉◉" * 20)
            print("  МАКСИМАЛЬНЫЙ РЕЙТИСУРД. МИР БОЛЬШЕ НЕ ПРИТВОРЯЕТСЯ.")
            print("◉◉◉" * 20)

        else:
            # Regular level-up messages that slowly get darker
            if new_level >= 11:
                print(f"\n⚠️  РЕЙТИСУРД {new_level}. Мир уже не притворяется.")
            elif new_level >= 8:
                print(f"\n⚠️  РЕЙТИСУРД ПОВЫСИЛСЯ ДО {new_level}. Давление усиливается.")
            else:
                print(f"\n⚠️  РЕЙТИСУРД ПОВЫСИЛСЯ ДО {new_level}! Мир становится опаснее...")

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

    # ------------------------------------------------------------------
    # Shop (Buying new businesses)
    # ------------------------------------------------------------------

    BUSINESS_TEMPLATES = [
        ("Полуночная Булочная",       "A", 10.0, 0.18),
        ("Бюро Незавершённых Дел",    "A", 10.0, 0.18),
        ("Эхо-Бар",                   "B", 13.5, 0.15),
        ("Второе Я",                  "B", 13.5, 0.15),
        ("Агентство «Шёпот»",         "C", 17.5, 0.12),
        ("Разлом-Экспресс",           "C", 17.5, 0.12),
        ("Рынок «Никогда»",           "C", 17.5, 0.12),
    ]

    def get_next_business_cost(self) -> int:
        """Returns the cost of the next business (increases by 20% each time)."""
        owned = len(self.state.businesses)
        base = 1000
        return int(base * (1.2 ** owned))

    def get_shop_options(self):
        """Returns list of available businesses with current price."""
        cost = self.get_next_business_cost()
        return [
            {
                "index": i,
                "name": name,
                "tier": tier,
                "cost": cost,
                "client_gain": client_gain,
                "bizneta_per_client": bizneta_per
            }
            for i, (name, tier, client_gain, bizneta_per) in enumerate(self.BUSINESS_TEMPLATES)
        ]

    def buy_business(self, template_index: int) -> bool:
        """Attempts to buy a business from the shop."""
        if template_index < 0 or template_index >= len(self.BUSINESS_TEMPLATES):
            return False

        cost = self.get_next_business_cost()
        if self.state.bizneta < cost:
            return False

        name, tier, client_gain, bizneta_per = self.BUSINESS_TEMPLATES[template_index]

        # Create unique niche_id (allow duplicates)
        niche_id = f"{name.lower().replace(' ', '_').replace('«', '').replace('»', '')}_{len(self.state.businesses)}"

        new_business = Business(
            niche_id=niche_id,
            clients=0.0,
            base_client_gain_per_minute=client_gain,
            bizneta_per_client_per_minute=bizneta_per,
        )

        self.state.bizneta -= cost
        self.state.businesses[niche_id] = new_business

        print(f"Bought {name} for {cost} Бизнет!")
        return True

    # ------------------------------------------------------------------
    # Business Upgrades
    # ------------------------------------------------------------------

    UPGRADE_TYPES = ["growth", "efficiency", "resilience"]

    def get_upgrade_cost(self, current_level: int) -> int:
        """Returns the cost to upgrade to the next level."""
        base = 800
        return int(base * (1.6 ** current_level))

    def get_business_upgrades(self, business_id: str):
        """Returns current upgrade levels and next costs for a business."""
        if business_id not in self.state.businesses:
            return None

        business = self.state.businesses[business_id]
        result = {}
        for up_type in self.UPGRADE_TYPES:
            level = business.upgrades.get(up_type, 0)
            cost = self.get_upgrade_cost(level)
            result[up_type] = {
                "level": level,
                "next_cost": cost
            }
        return result

    def upgrade_business(self, business_id: str, upgrade_type: str) -> bool:
        """Attempts to upgrade a business in one of the three categories."""
        if business_id not in self.state.businesses:
            return False
        if upgrade_type not in self.UPGRADE_TYPES:
            return False

        business = self.state.businesses[business_id]
        current_level = business.upgrades.get(upgrade_type, 0)
        cost = self.get_upgrade_cost(current_level)

        if self.state.bizneta < cost:
            return False

        self.state.bizneta -= cost
        business.upgrades[upgrade_type] = current_level + 1

        print(f"Upgraded {business_id} - {upgrade_type} to level {current_level + 1}")
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