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
# Weights are tuned so that businesses feel special, and good outcomes are satisfying but not too frequent.
SYMBOLS = [
    # Regular rewards (most common)
    ("bizneta_small",  "💰 Small Bizneta",   "reward",  20),
    ("bizneta_medium", "💰💰 Bizneta",       "reward",  9),
    ("clients_small",  "👥 Clients",         "reward",  16),
    ("clients_medium", "👥👥 Clients",       "reward",   7),

    # Potion drops
    ("potion_2min",    "🧪 2min Potion",     "potion",   5),
    ("potion_5min",    "🧪 5min Potion",     "potion",   4),
    ("potion_10min",   "🧪 10min Potion",    "potion",   3),
    ("potion_30min",   "🧪 30min Potion",    "potion",   1.5),

    # Business drops (these go on the middle reel)
    # Made rarer so they feel like real highlights when they appear.
    ("business_bakery",     "🍞 Bakery",           "business", 1.8),
    ("business_debts",      "📜 Debts Bureau",     "business", 1.8),
    ("business_echo",       "🍹 Echo Bar",         "business", 1.6),
    ("business_second",     "🪞 Second Self",      "business", 1.6),
    ("business_whisper",    "🗣️ Whisper Agency",   "business", 1.1),
    ("business_razlom",     "🌀 Razlom Express",   "business", 1.0),
    ("business_never",      "❓ Market of Never",  "business", 0.9),

    # Rare / special (very rare)
    ("rare_potion",    "✨ Rare Cleanse",    "rare",     0.8),
    ("chaos_potion",   "🌪️ Chaos Suppress",  "rare",     0.7),
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

        # === Rolling animation changes personality with Ratysurd ===
        ratysurd = state.ratysurd_level
        is_very_high = ratysurd >= 12
        is_high_chaos = ratysurd >= 10

        if is_very_high:
            print("\n◉◉◉  REALITY IS FRACTURING...  ◉◉◉", end=" ", flush=True)
        elif is_high_chaos:
            print("\n🌪️  The reels twist and scream...", end=" ", flush=True)
        else:
            print("\n🎰  Spinning the reels...", end=" ", flush=True)

        # Stage 1 — more erratic at high chaos
        for _ in range(8 if is_very_high else 7):
            temp1 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp2 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp3 = random.choice(list(SYMBOL_DISPLAY.keys()))
            print(f"\r🎰  {SYMBOL_DISPLAY[temp1]:<18} | {SYMBOL_DISPLAY[temp2]:<18} | {SYMBOL_DISPLAY[temp3]:<18}", end="", flush=True)
            time.sleep(0.025 if is_very_high else 0.03 if is_high_chaos else 0.04)

        # Stage 2
        for _ in range(7 if is_very_high else 6):
            temp1 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp2 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp3 = random.choice(list(SYMBOL_DISPLAY.keys()))
            print(f"\r🎰  {SYMBOL_DISPLAY[temp1]:<18} | {SYMBOL_DISPLAY[temp2]:<18} | {SYMBOL_DISPLAY[temp3]:<18}", end="", flush=True)
            time.sleep(0.06 if is_very_high else 0.07 if is_high_chaos else 0.085)

        # Stage 3 — final tension (much slower and heavier at high chaos)
        for _ in range(5 if is_very_high else 4):
            temp1 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp2 = random.choice(list(SYMBOL_DISPLAY.keys()))
            temp3 = random.choice(list(SYMBOL_DISPLAY.keys()))
            print(f"\r🎰  {SYMBOL_DISPLAY[temp1]:<18} | {SYMBOL_DISPLAY[temp2]:<18} | {SYMBOL_DISPLAY[temp3]:<18}", end="", flush=True)
            time.sleep(0.25 if is_very_high else 0.18 if is_high_chaos else 0.22)

        print("\r", end="")

        # Final roll
        reel1 = self._roll_symbol()
        reel2 = self._roll_symbol(allow_business=True)
        reel3 = self._roll_symbol()

        is_chaotic_spin = False

        # === High Ratysurd: chance to corrupt one of the reels ===
        if state.ratysurd_level >= 10 and random.random() < 0.40:
            is_chaotic_spin = True
            # Corrupt one random reel
            corrupt_index = random.randint(0, 2)
            if corrupt_index == 0:
                reel1 = self._get_corrupted_symbol(reel1)
            elif corrupt_index == 1:
                reel2 = self._get_corrupted_symbol(reel2)
            else:
                reel3 = self._get_corrupted_symbol(reel3)

        result = self._evaluate_spin(reel1, reel2, reel3, state)

        if is_chaotic_spin:
            result.message = "CHAOTIC SPIN! " + result.message

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

    def _get_corrupted_symbol(self, original: str) -> str:
        """At high Ratysurd, symbols can twist into corrupted versions with mixed outcomes."""
        mapping = {
            "bizneta_small": "cursed_bizneta",
            "bizneta_medium": "cursed_bizneta",
            "clients_small": "cursed_clients",
            "clients_medium": "cursed_clients",
            "potion_2min": "cursed_potion",
            "potion_5min": "cursed_potion",
            "potion_10min": "cursed_potion",
            "potion_30min": "cursed_potion",
        }
        return mapping.get(original, original)

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
        """Much more emotional and weighty spin outcomes."""

        ratysurd = state.ratysurd_level

        # === Business drop (the best possible outcome) ===
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

                messages = [
                    f"★ NEW BUSINESS UNLOCKED! {niche_name} (Tier {tier})! ★",
                    f"INCREDIBLE! You pulled {niche_name}!",
                    f"THE REELS HAVE SPOKEN! New business: {niche_name}!"
                ]
                return SpinResult(r1, r2, r3, random.choice(messages), business_gained=business_id, is_rare=True)

            else:
                bonus = random.randint(1800, 2800) if tier == "C" else random.randint(1200, 1800)
                state.bizneta += bonus
                return SpinResult(r1, r2, r3, f"Duplicate {niche_name}... +{bonus} Bizneta compensation.", bizneta_gained=bonus)

        # === Rare / God-tier drops ===
        if r1 in self.rare_pool or r3 in self.rare_pool:
            if r1 == "rare_potion" or r3 == "rare_potion":
                state.permanent_cleanse_potions += 1
                return SpinResult(r1, r2, r3, "✨✨✨ HOLY SHIT! PERMANENT CLEANSE POTION! ✨✨✨", is_rare=True)
            if r1 == "chaos_potion" or r3 == "chaos_potion":
                state.chaos_suppression_potions += 1
                return SpinResult(r1, r2, r3, "🌪️🌪️🌪️ INSANE! CHAOS SUPPRESSION POTION! 🌪️🌪️🌪️", is_rare=True)

        # === Corrupted / Twisted outcomes (high Ratysurd only) ===
        if any(x in (r1, r2, r3) for x in ["cursed_bizneta", "cursed_clients", "cursed_potion"]):
            roll = random.random()

            if "cursed_bizneta" in (r1, r2, r3):
                gain = random.randint(520, 980)
                state.bizneta += gain
                if state.businesses and roll < 0.65:
                    # Stronger version: apply to multiple businesses
                    affected = random.sample(list(state.businesses.values()), min(2, len(state.businesses)))
                    for target in affected:
                        curse = Effect(
                            effect_id="slot_curse",
                            strength=random.choice([-0.45, -0.60]),
                            is_permanent=False,
                            applied_at=datetime.now(timezone.utc),
                            expires_at=datetime.now(timezone.utc) + timedelta(minutes=random.randint(18, 30))
                        )
                        target.effects.append(curse)
                    return SpinResult(r1, r2, r3, f"Twisted fortune! +{gain} Bizneta... but the chaos touched several of your businesses.", bizneta_gained=gain)
                else:
                    loss = random.randint(200, 380)
                    state.bizneta = max(0, state.bizneta - loss)
                    return SpinResult(r1, r2, r3, f"Twisted fortune! +{gain} Bizneta... but you lost {loss} in the process.", bizneta_gained=gain)

            if "cursed_clients" in (r1, r2, r3):
                gain = random.randint(22, 38)
                if state.businesses:
                    target = random.choice(list(state.businesses.values()))
                    target.clients += gain
                loss = random.randint(1, 2)
                state.kloneta = max(0, state.kloneta - loss)
                return SpinResult(r1, r2, r3, f"Corrupted clients! +{gain} clients... but you lost {loss} Kloneta.", clients_gained=gain)

            if "cursed_potion" in (r1, r2, r3):
                pot = random.choice(["10min", "30min"])
                state.regular_potions[pot] = state.regular_potions.get(pot, 0) + 1
                if state.businesses:
                    affected = random.sample(list(state.businesses.values()), min(2, len(state.businesses)))
                    for target in affected:
                        curse = Effect(
                            effect_id="slot_curse",
                            strength=-0.50,
                            is_permanent=False,
                            applied_at=datetime.now(timezone.utc),
                            expires_at=datetime.now(timezone.utc) + timedelta(minutes=25)
                        )
                        target.effects.append(curse)
                    return SpinResult(r1, r2, r3, f"Twisted potion... Got a {pot} potion, but chaos touched several of your businesses.", is_rare=True)
                else:
                    return SpinResult(r1, r2, r3, f"Twisted potion... Got a {pot} potion. Something feels deeply off.", is_rare=True)

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

        # === Regular rewards with strong emotional tiers ===
        bizneta = 0
        clients = 0

        reward_count = sum(1 for r in (r1, r2, r3) if "bizneta" in r or "clients" in r)

        for reel in (r1, r2, r3):
            if reel == "bizneta_small":
                bizneta += random.randint(60, 120)
            elif reel == "bizneta_medium":
                bizneta += random.randint(180, 320)
            elif reel == "clients_small":
                clients += random.randint(3, 7)
            elif reel == "clients_medium":
                clients += random.randint(8, 14)

        # Apply Ratysurd variance (higher Ratysurd = more extreme outcomes)
        variance = 1.0
        if ratysurd >= 8:
            variance = random.uniform(0.6, 1.7)   # very swingy
        elif ratysurd >= 5:
            variance = random.uniform(0.75, 1.45)

        bizneta = int(bizneta * variance)
        clients = int(clients * variance)

        if reward_count >= 3:
            state.bizneta += bizneta
            if clients > 0 and state.businesses:
                chosen = random.choice(list(state.businesses.values()))
                chosen.clients += clients
            return SpinResult(r1, r2, r3, f"TRIPLE REWARD! +{bizneta} Bizneta, +{clients} clients", bizneta_gained=bizneta, clients_gained=clients)

        elif reward_count == 2:
            state.bizneta += bizneta
            if clients > 0 and state.businesses:
                chosen = random.choice(list(state.businesses.values()))
                chosen.clients += clients
            return SpinResult(r1, r2, r3, f"Nice! +{bizneta} Bizneta, +{clients} clients", bizneta_gained=bizneta, clients_gained=clients)

        elif reward_count == 1:
            state.bizneta += bizneta
            if clients > 0 and state.businesses:
                chosen = random.choice(list(state.businesses.values()))
                chosen.clients += clients
            return SpinResult(r1, r2, r3, f"+{bizneta} Bizneta, +{clients} clients", bizneta_gained=bizneta, clients_gained=clients)

        # Misses — make them feel different based on Ratysurd
        if ratysurd >= 10:
            miss_messages = [
                "The chaos devours your spin...",
                "Nothing. The reels laugh at you.",
                "Complete blank. The world is getting crueler.",
                "Oof. Even the slot feels the pressure.",
            ]
        elif ratysurd >= 7:
            miss_messages = [
                "The reels are cold...",
                "Nothing this time. Pressure is rising.",
                "Blank. Not great.",
                "The house wins again.",
            ]
        else:
            miss_messages = [
                "Nothing this time...",
                "Blank reels.",
                "No luck.",
                "The reels are silent.",
            ]

        return SpinResult(r1, r2, r3, random.choice(miss_messages))
