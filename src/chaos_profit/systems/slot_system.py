"""
SlotSystem — basic implementation of the slot machine for the prototype.

Current goals (MVP scope):
- Costs 1 Kloneta per spin.
- Can drop businesses (determined by middle reel).
- Can drop regular and rare potions.
- Gives Bizneta and clients on regular wins.
- Feels exciting even in text form.
- Easy to expand later with better symbols, weights, and special features.
"""

import random
import time
from dataclasses import dataclass
from typing import Optional, List

from ..core.models import PlayerState, Business, Effect
from datetime import datetime, timezone, timedelta


# Symbol definitions for the prototype
# Format: (symbol_id, display_name, category, weight)
SYMBOLS = [
    # Regular rewards
    ("bizneta_small",  "💰 Small Bizneta",   "reward",  18),
    ("bizneta_medium", "💰💰 Bizneta",       "reward",  10),
    ("clients_small",  "👥 Clients",         "reward",  15),
    ("clients_medium", "👥👥 Clients",       "reward",   8),

    # Potion drops
    ("potion_2min",    "🧪 2min Potion",     "potion",   6),
    ("potion_5min",    "🧪 5min Potion",     "potion",   5),
    ("potion_10min",   "🧪 10min Potion",    "potion",   4),
    ("potion_30min",   "🧪 30min Potion",    "potion",   2),

    # Business drops (these go on the middle reel)
    ("business_bakery",     "🍞 Bakery",           "business", 3),
    ("business_debts",      "📜 Debts Bureau",     "business", 3),
    ("business_echo",       "🍹 Echo Bar",         "business", 3),
    ("business_second",     "🪞 Second Self",      "business", 3),
    ("business_whisper",    "🗣️ Whisper Agency",   "business", 2),
    ("business_razlom",     "🌀 Razlom Express",   "business", 2),
    ("business_never",      "❓ Market of Never",  "business", 2),

    # Rare / special
    ("rare_potion",    "✨ Rare Cleanse",    "rare",     1),
    ("chaos_potion",   "🌪️ Chaos Suppress",  "rare",     1),
]

# Map symbol_id → nice display name for results
SYMBOL_DISPLAY = {s[0]: s[1] for s in SYMBOLS}

# Business symbol_id → nice name (for buying)
BUSINESS_SYMBOL_MAP = {
    "business_bakery":  ("Полуночная Булочная", "A"),
    "business_debts":   ("Бюро Незавершённых Дел", "A"),
    "business_echo":    ("Эхо-Бар", "B"),
    "business_second":  ("Второе Я", "B"),
    "business_whisper": ("Агентство Шёпот", "C"),
    "business_razlom":  ("Разлом-Экспресс", "C"),
    "business_never":   ("Рынок Никогда", "C"),
}


@dataclass
class SpinResult:
    reel1: str
    reel2: str
    reel3: str
    message: str
    bizneta_gained: int = 0
    clients_gained: int = 0
    potion_gained: Optional[str] = None
    business_gained: Optional[str] = None
    is_rare: bool = False


class SlotSystem:
    def __init__(self):
        # Build weighted pools
        self.reward_pool = [s[0] for s in SYMBOLS if s[2] == "reward"]
        self.potion_pool = [s[0] for s in SYMBOLS if s[2] == "potion"]
        self.business_pool = [s[0] for s in SYMBOLS if s[2] == "business"]
        self.rare_pool = [s[0] for s in SYMBOLS if s[2] == "rare"]

        # Weights for normal spins (middle reel can be business)
        self.normal_weights = {s[0]: s[3] for s in SYMBOLS}

    def can_spin(self, state: PlayerState) -> bool:
        return state.kloneta > 0

    def spin(self, state: PlayerState) -> SpinResult:
        """Perform one spin. Costs 1 Kloneta. Has rolling animation."""
        if not self.can_spin(state):
            return SpinResult("❌", "❌", "❌", "Not enough Kloneta!")

        # Spend Kloneta
        state.kloneta -= 1

        # === Rolling animation (builds tension) ===
        print("\n🎰  Spinning...", end=" ", flush=True)
        for _ in range(8):
            temp1 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp2 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp3 = random.choice(list(SYMBOL_DISPLAY.keys()))
            print(f"\r🎰  {SYMBOL_DISPLAY[temp1]:<18} | {SYMBOL_DISPLAY[temp2]:<18} | {SYMBOL_DISPLAY[temp3]:<18}", end="", flush=True)
            time.sleep(0.06)
        print("\r", end="")

        # Final roll
        reel1 = self._roll_symbol()
        reel2 = self._roll_symbol(allow_business=True)
        reel3 = self._roll_symbol()

        result = self._evaluate_spin(reel1, reel2, reel3, state)
        result.reel1 = SYMBOL_DISPLAY.get(reel1, reel1)
        result.reel2 = SYMBOL_DISPLAY.get(reel2, reel2)
        result.reel3 = SYMBOL_DISPLAY.get(reel3, reel3)

        # Dramatic result
        if result.is_rare or result.business_gained:
            print(f"\n🎰  {result.reel1}  |  {result.reel2}  |  {result.reel3}")
            print("★" * 40)
            print(f"  {result.message}")
            print("★" * 40)
        else:
            print(f"\n🎰  {result.reel1}  |  {result.reel2}  |  {result.reel3}")
            print(f"   → {result.message}")

        return result

    def _roll_symbol(self, allow_business: bool = False) -> str:
        """Roll one symbol with current weights."""
        pool = []
        weights = []

        for sym_id, weight in self.normal_weights.items():
            if not allow_business and sym_id in self.business_pool:
                continue
            pool.append(sym_id)
            weights.append(weight)

        return random.choices(pool, weights=weights, k=1)[0]

    def _evaluate_spin(self, r1: str, r2: str, r3: str, state: PlayerState) -> SpinResult:
        """Decide what the player gets. More dramatic outcomes."""

        # === Business drop (highest value) ===
        if r2 in self.business_pool:
            niche_name, tier = BUSINESS_SYMBOL_MAP[r2]
            business_id = r2.replace("business_", "")

            if business_id not in state.businesses:
                tier_client = {"A": 10.0, "B": 13.5, "C": 17.5}
                tier_biz = {"A": 0.18, "B": 0.15, "C": 0.12}

                new_biz = Business(
                    niche_id=business_id,
                    clients=0.0,
                    base_client_gain_per_minute=tier_client[tier],
                    bizneta_per_client_per_minute=tier_biz[tier],
                )
                state.businesses[business_id] = new_biz
                return SpinResult(r1, r2, r3,
                                  f"★ NEW BUSINESS! {niche_name} (Tier {tier})!",
                                  business_gained=business_id,
                                  is_rare=True)

            else:
                bonus = 1800 if tier == "C" else 1200
                state.bizneta += bonus
                return SpinResult(r1, r2, r3,
                                  f"Duplicate {niche_name}! +{bonus} Bizneta compensation.",
                                  bizneta_gained=bonus)

        # === Rare potion drops (very exciting) ===
        if r1 in self.rare_pool or r3 in self.rare_pool:
            if r1 == "rare_potion" or r3 == "rare_potion":
                state.permanent_cleanse_potions += 1
                return SpinResult(r1, r2, r3,
                                  "✨✨ JACKPOT! PERMANENT CLEANSE POTION! ✨✨",
                                  is_rare=True)
            if r1 == "chaos_potion" or r3 == "chaos_potion":
                state.chaos_suppression_potions += 1
                return SpinResult(r1, r2, r3,
                                  "🌪️🌪️ RARE! CHAOS SUPPRESSION POTION! 🌪️🌪️",
                                  is_rare=True)

        # === Regular potion drops ===
        potion_map = {
            "potion_2min": "2min",
            "potion_5min": "5min",
            "potion_10min": "10min",
            "potion_30min": "30min",
        }
        for reel in (r1, r2, r3):
            if reel in potion_map:
                pot = potion_map[reel]
                state.regular_potions[pot] = state.regular_potions.get(pot, 0) + 1
                return SpinResult(r1, r2, r3, f"Got a {pot} potion!")

        # === Regular rewards with tiers ===
        bizneta = 0
        clients = 0

        reward_count = sum(1 for r in (r1, r2, r3) if "bizneta" in r or "clients" in r)

        for reel in (r1, r2, r3):
            if reel == "bizneta_small":
                bizneta += random.randint(70, 130)
            elif reel == "bizneta_medium":
                bizneta += random.randint(160, 280)
            elif reel == "clients_small":
                clients += random.randint(4, 8)
            elif reel == "clients_medium":
                clients += random.randint(9, 16)

        if bizneta > 0 or clients > 0:
            state.bizneta += bizneta
            if clients > 0 and state.businesses:
                chosen = random.choice(list(state.businesses.values()))
                chosen.clients += clients

            # Make the message more emotional based on size
            if reward_count >= 2 or bizneta + clients >= 25:
                msg = f"NICE! +{bizneta} Bizneta, +{clients} clients"
            else:
                msg = f"+{bizneta} Bizneta, +{clients} clients"

            return SpinResult(r1, r2, r3, msg, bizneta_gained=bizneta, clients_gained=clients)

        # Miss
        messages = [
            "Nothing this time...",
            "Blank... tough luck.",
            "The reels are cold today.",
            "No luck. Try again?",
        ]
        return SpinResult(r1, r2, r3, random.choice(messages))
