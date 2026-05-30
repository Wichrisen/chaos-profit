"""
DealSystem — handles the appearance and resolution of Normal and Dark Deals.

Current simplified version:
- Deals can "pop" for random businesses over time.
- Only one deal can be active at a time (for simplicity in the prototype).
- The player can accept or refuse the current deal.
- On failure, a negative effect is applied to the business.
- On success, the player gets Bizneta and sometimes clients.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from ..core.models import PlayerState, Business, Effect


class Deal:
    def __init__(self, business_niche: str, is_dark: bool, success_chance: float):
        self.business_niche = business_niche
        self.is_dark = is_dark
        self.success_chance = success_chance  # 0.0 - 1.0
        self.created_at = datetime.now(timezone.utc)


class DealSystem:
    def __init__(self):
        self.current_deal: Optional[Deal] = None
        self.last_deal_time: datetime = datetime.now(timezone.utc)

    def update(self, state: PlayerState, seconds_passed: float) -> bool:
        """
        Called periodically (from Game.advance_time).
        Returns True if a new deal appeared.
        """
        if self.current_deal is not None:
            return False  # Already have an active deal

        # Very rough timing for the prototype
        # We deliberately make deals quite frequent here so the player can test the effect/potion loop easily.
        time_since_last = (datetime.now(timezone.utc) - self.last_deal_time).total_seconds()

        # Prototype tuning: deals appear often for testing
        normal_interval = random.randint(25, 55)   # seconds (very frequent for dev testing)
        dark_interval = random.randint(120, 240)   # 2-4 minutes

        if time_since_last > normal_interval:
            # Decide if it's a dark deal (rare)
            is_dark = random.random() < 0.15  # 15% chance for dark when a deal pops

            if is_dark and time_since_last < dark_interval:
                return False  # Not enough time for dark deal yet

            available_businesses = list(state.businesses.keys())
            if not available_businesses:
                return False

            chosen_niche = random.choice(available_businesses)

            # Success chance ranges as discussed earlier
            if is_dark:
                success_chance = random.uniform(0.40, 0.50)  # 40-50% for dark
            else:
                success_chance = random.uniform(0.65, 0.75)  # 65-75% for normal

            self.current_deal = Deal(
                business_niche=chosen_niche,
                is_dark=is_dark,
                success_chance=success_chance
            )
            self.last_deal_time = datetime.now(timezone.utc)
            return True

        return False

    def resolve_deal(self, state: PlayerState, accept: bool) -> Tuple[bool, str]:
        """
        Player decides to accept or refuse the current deal.
        Returns (success: bool, message: str)
        """
        if self.current_deal is None:
            return False, "Нет активной сделки."

        deal = self.current_deal
        business = state.businesses.get(deal.business_niche)

        if business is None:
            self.current_deal = None
            return False, "Бизнес больше не существует."

        self.current_deal = None  # Deal is resolved

        if not accept:
            return False, "Ты отказался от сделки."

        # Roll for success
        success = random.random() < deal.success_chance

        if success:
            # Success rewards (basic for prototype)
            reward_bizneta = random.randint(800, 2500) if not deal.is_dark else random.randint(2500, 6000)
            reward_clients = random.randint(5, 25) if not deal.is_dark else random.randint(20, 80)

            state.bizneta += reward_bizneta
            business.clients += reward_clients

            deal_type = "Тёмная" if deal.is_dark else "Обычная"
            return True, f"Успех! {deal_type} сделка принесла +{reward_bizneta} Бизнет и +{reward_clients} клиентов."

        else:
            # Failure → apply negative effect
            deal_type = "Тёмная" if deal.is_dark else "Обычная"

            # Determine effect strength — scales with Ratysurd (especially after level 7)
            ratysurd = state.ratysurd_level

            if deal.is_dark:
                base_strength = random.choice([-0.50, -0.65, -0.75])
                is_permanent = random.random() < 0.40
            else:
                base_strength = random.choice([-0.25, -0.40, -0.50])
                is_permanent = random.random() < 0.12

            # Scaling: after level 6 the danger grows noticeably
            if ratysurd > 6:
                scaling = 1.0 + (ratysurd - 6) * 0.08   # +8% strength per level after 6
                base_strength *= scaling

            # Clamp so it doesn't become completely ridiculous in prototype
            strength = max(base_strength, -0.92)  # max ~92% penalty for now

            effect = Effect(
                effect_id="deal_failure",
                strength=strength,
                is_permanent=is_permanent,
                applied_at=datetime.now(timezone.utc),
                expires_at=None if is_permanent else (datetime.now(timezone.utc) + timedelta(minutes=random.randint(15, 45)))
            )

            business.effects.append(effect)

            msg = f"Провал {deal_type} сделки! На бизнес наложен эффект ({strength*100:+.0f}% к клиентам)"
            if is_permanent:
                msg += " (стойкий)"

            return False, msg

    def get_current_deal_info(self) -> Optional[str]:
        if self.current_deal is None:
            return None

        deal = self.current_deal
        deal_type = "ТЁМНАЯ СДЕЛКА" if deal.is_dark else "Обычная сделка"
        chance = int(deal.success_chance * 100)

        return f"{deal_type} для '{deal.business_niche}' (шанс успеха ~{chance}%)"

    def clear_current_deal(self):
        self.current_deal = None
