"""
DealSystem — the second emotional pillar (paired with the Slot).

Deals now scale hard with Ratysurd:
- Timing and frequency tighten as chaos rises.
- Dark deals spawn more often after level 7.
- At 10-11+: "Twisted / ИСКАЖЁННАЯ" deals appear — lower odds, nastier failures (secondary curses, client massacres, permanent scars).
- Resolve text is highly reactive: refusal, success, and failure all change voice and consequences based on current ratysurd and whether the deal was twisted.
- Success can carry a hidden chaotic tithe at extreme levels.
- Designed so that by level 12-13, every deal feels like a potential point of no return.

Matches the emotional weight of the high-chaos SlotSystem.
"""

import random
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple

from ..core.models import PlayerState, Business, Effect


class Deal:
    def __init__(self, business_niche: str, is_dark: bool, success_chance: float, ratysurd_at_appearance: int = 1):
        self.business_niche = business_niche
        self.is_dark = is_dark
        self.success_chance = success_chance  # 0.0 - 1.0
        self.created_at = datetime.now(timezone.utc)
        self.ratysurd_at_appearance = ratysurd_at_appearance
        self.is_twisted = False  # Set later for high-chaos special deals


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

        # Timing tuned for real play (less spammy than early prototype) but still testable.
        time_since_last = (datetime.now(timezone.utc) - self.last_deal_time).total_seconds()

        ratysurd = getattr(state, "ratysurd_level", 1)
        pressure = 1.0 + max(0, (ratysurd - 6) * 0.07)

        # Base intervals get tighter (more pressure) at high ratysurd
        base_normal = random.randint(45, 95)
        normal_interval = max(18, int(base_normal / (1.0 + max(0, (ratysurd - 7) * 0.06))))

        dark_interval = random.randint(140, 260)

        if time_since_last > normal_interval:
            # Dark deals become more common (and nastier) with chaos
            dark_chance = 0.12 + min(0.18, (ratysurd - 6) * 0.025) if ratysurd >= 7 else 0.08
            is_dark = random.random() < dark_chance

            if is_dark and time_since_last < dark_interval:
                return False

            available_businesses = list(state.businesses.keys())
            if not available_businesses:
                return False

            chosen_niche = random.choice(available_businesses)

            # Base success (lower at high ratysurd)
            if is_dark:
                success_chance = random.uniform(0.38, 0.52)
            else:
                success_chance = random.uniform(0.62, 0.76)

            # High chaos makes even normal deals riskier
            if ratysurd >= 10:
                success_chance *= random.uniform(0.82, 0.96)

            deal = Deal(
                business_niche=chosen_niche,
                is_dark=is_dark,
                success_chance=max(0.15, success_chance),
                ratysurd_at_appearance=ratysurd
            )

            # === New: Twisted deals at very high chaos (extra narrative + mechanical bite)
            if ratysurd >= 11 and random.random() < 0.38:
                deal.is_twisted = True
                deal.success_chance = max(0.22, deal.success_chance * 0.78)  # noticeably harder

            self.current_deal = deal
            self.last_deal_time = datetime.now(timezone.utc)
            return True

        return False

    def resolve_deal(self, state: PlayerState, accept: bool, chaos_pressure: float = 1.0) -> Tuple[bool, str]:
        """
        Player decides to accept or refuse the current deal.
        chaos_pressure amplifies negative effects from Ratysurd.
        High ratysurd + twisted deals produce much more dramatic, costly outcomes.
        Returns (success: bool, message: str)
        """
        if self.current_deal is None:
            return False, "Нет активной сделки."

        deal = self.current_deal
        business = state.businesses.get(deal.business_niche)

        if business is None:
            self.current_deal = None
            return False, "Бизнес больше не существует."

        ratysurd = getattr(state, "ratysurd_level", 1)
        self.current_deal = None  # Deal is resolved

        if not accept:
            # Refuse flavor shifts with chaos
            if ratysurd >= 11 and deal.is_twisted:
                return False, "Ты отвергнул сделку. В тишине ты слышишь, как что-то разочарованно выдыхает."
            if deal.is_dark:
                return False, "Ты отказался от тёмной сделки. Умно... но мир запомнил."
            return False, "Ты отказался от сделки."

        # Roll for success
        success = random.random() < deal.success_chance

        deal_type = "ТЁМНАЯ" if deal.is_dark else "Обычная"
        if deal.is_twisted:
            deal_type = "ИСКАЖЁННАЯ " + deal_type

        if success:
            # Success rewards — bigger at high chaos, but sometimes with a "price"
            if deal.is_dark:
                reward_bizneta = random.randint(2800, 7200)
                reward_clients = random.randint(35, 95)
            else:
                reward_bizneta = random.randint(950, 3100)
                reward_clients = random.randint(8, 32)

            # High chaos / twisted success can be double-edged
            price_note = ""
            if (deal.is_twisted or ratysurd >= 12) and random.random() < 0.45:
                # Pay a small chaotic tithe
                tithe = random.randint(180, 420)
                state.bizneta = max(0, state.bizneta - tithe)
                price_note = f" ...но ты чувствуешь, как мир забрал {tithe} Бизнет в качестве «комиссии»."

            state.bizneta += reward_bizneta
            business.clients += reward_clients

            if deal.is_twisted:
                return True, f"УСПЕХ! {deal_type} принесла +{reward_bizneta} Бизнет и +{reward_clients} клиентов.{price_note} (Что-то изменилось в договоре...)"
            return True, f"Успех! {deal_type} сделка принесла +{reward_bizneta} Бизнет и +{reward_clients} клиентов.{price_note}"

        else:
            # FAILURE — the meat of the danger curve
            if deal.is_dark:
                base_strength = random.choice([-0.55, -0.68, -0.82])
                is_permanent = random.random() < (0.45 + min(0.2, (ratysurd - 8) * 0.03))
            else:
                base_strength = random.choice([-0.28, -0.42, -0.55])
                is_permanent = random.random() < (0.14 + min(0.12, (ratysurd - 7) * 0.02))

            strength = base_strength * chaos_pressure
            strength = max(strength, -0.96)

            effect = Effect(
                effect_id="deal_failure" if not deal.is_twisted else "twisted_bargain",
                strength=strength,
                is_permanent=is_permanent,
                applied_at=datetime.now(timezone.utc),
                expires_at=None if is_permanent else (datetime.now(timezone.utc) + timedelta(minutes=random.randint(12, 38)))
            )
            business.effects.append(effect)

            # === Extra bite for twisted / very high chaos failures ===
            extra = ""
            if deal.is_twisted or ratysurd >= 12:
                if state.businesses and random.random() < 0.55:
                    # Secondary curse on another business (or same)
                    other = random.choice(list(state.businesses.values()))
                    secondary = Effect(
                        effect_id="echo_curse",
                        strength=random.choice([-0.32, -0.44]),
                        is_permanent=False,
                        applied_at=datetime.now(timezone.utc),
                        expires_at=datetime.now(timezone.utc) + timedelta(minutes=random.randint(14, 26))
                    )
                    other.effects.append(secondary)
                    extra = " Хаос разлился на другие предприятия."

                # Small direct client massacre on failure at extreme
                if ratysurd >= 13 and business.clients > 10:
                    lost = min(business.clients * 0.18, random.randint(8, 22))
                    business.clients = max(0, business.clients - lost)
                    extra += f" {int(lost)} клиентов сорвались в пропасть."

            msg = f"ПРОВАЛ {deal_type}! На «{deal.business_niche}» наложен эффект ({strength*100:+.0f}% к клиентам)"
            if is_permanent:
                msg += " (СТОЙКИЙ)"
            msg += extra

            if ratysurd >= 11:
                msg += " Мир доволен."

            return False, msg

    def get_current_deal_info(self) -> Optional[str]:
        if self.current_deal is None:
            return None

        deal = self.current_deal
        if deal.is_twisted:
            deal_type = "⚠️ ИСКАЖЁННАЯ СДЕЛКА ⚠️"
        elif deal.is_dark:
            deal_type = "ТЁМНАЯ СДЕЛКА"
        else:
            deal_type = "Обычная сделка"

        chance = int(deal.success_chance * 100)
        pressure_note = ""
        if deal.ratysurd_at_appearance >= 10:
            pressure_note = " [мир давит]"

        return f"{deal_type} для «{deal.business_niche}» (~{chance}%){pressure_note}"

    def clear_current_deal(self):
        self.current_deal = None
