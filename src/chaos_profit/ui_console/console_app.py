"""
Minimal Console Prototype for Chaos & Profit.

This is a temporary interactive interface to manually test the core systems.
It will be replaced / expanded later when we have more mechanics (Deals, Potions, Slot, etc.).
"""

import sys
from datetime import datetime, timezone

from ..game import Game


class ConsoleApp:
    def __init__(self):
        self.game = Game()
        self.running = True

    def run(self):
        print("=== Chaos & Profit — Console Prototype ===")
        print("Type 'help' for commands.\n")
        self._print_status()

        while self.running:
            try:
                command = input("\n> ").strip().lower()
                self._handle_command(command)
            except KeyboardInterrupt:
                print("\nExiting...")
                self._shutdown()
            except Exception as e:
                print(f"Error: {e}")

    def _handle_command(self, command: str):
        if command in ("q", "quit", "exit"):
            self._shutdown()
        elif command in ("h", "help", "?"):
            self._print_help()
        elif command in ("s", "status", "st"):
            self._print_status()
        elif command.startswith("a ") or command.startswith("advance "):
            self._handle_advance(command)
        elif command in ("1m", "5m", "10m", "30m", "1h", "2h"):
            self._handle_quick_advance(command)
        elif command in ("save", "sv"):
            self.game.save()
            print("Game saved manually.")
        elif command in ("reset", "rst"):
            confirm = input("Are you sure you want to reset all progress? (y/n): ").strip().lower()
            if confirm == "y":
                self.game.reset_to_factory()
                print("Game has been reset to factory state.")
                self._print_status()
        elif command in ("tick", "t"):
            self.game.tick()
            print("Tick processed (autosave check).")
        elif command in ("deals", "deal", "d"):
            self._handle_deals()
        elif command in ("accept", "yes", "y"):
            self._resolve_current_deal(accept=True)
        elif command in ("refuse", "no", "n"):
            self._resolve_current_deal(accept=False)
        elif command in ("potions", "p", "inv"):
            self._print_potions()
        elif command.startswith("use "):
            self._handle_use_potion(command)
        elif command in ("shop", "buy", "b"):
            self._print_shop()
        elif command.startswith("buy "):
            self._handle_buy_business(command)
        elif command in ("spin", "slot", "🎰"):
            self._handle_spin()
        else:
            print("Unknown command. Type 'help'.")

    def _handle_advance(self, command: str):
        parts = command.split()
        if len(parts) < 2:
            print("Usage: advance <minutes>  (or a <minutes>)")
            return

        try:
            minutes = float(parts[1])
            if minutes <= 0:
                print("Please enter a positive number of minutes.")
                return

            seconds = minutes * 60
            self.game.advance_time(seconds)
            self._print_status()
        except ValueError:
            print("Invalid number. Please enter minutes as a number (e.g. 60 or 10.5)")

    def _handle_quick_advance(self, command: str):
        mapping = {
            "1m": 1,
            "5m": 5,
            "10m": 10,
            "30m": 30,
            "1h": 60,
            "2h": 120,
        }
        minutes = mapping.get(command, 0)
        if minutes > 0:
            self.game.advance_time(minutes * 60)
            self._print_status()

    def _handle_deals(self):
        info = self.game.deal_system.get_current_deal_info()
        if info:
            print(f"\nАктивная сделка: {info}")
            print("Напиши 'accept' / 'yes' чтобы принять или 'refuse' / 'no' чтобы отказаться.")
        else:
            print("Сейчас нет активных сделок.")

    def _resolve_current_deal(self, accept: bool):
        success, message = self.game.deal_system.resolve_deal(self.game.state, accept)
        print(message)
        self._print_status()

    def _print_potions(self):
        state = self.game.state
        print("\n=== Potions ===")
        print(f"Regular potions:")
        if state.regular_potions:
            for dur, count in sorted(state.regular_potions.items()):
                print(f"  {dur}: {count}")
        else:
            print("  None")
        print(f"Permanent Cleanse: {state.permanent_cleanse_potions}")
        print(f"Chaos Suppression: {state.chaos_suppression_potions}")
        print("Use with: use 2min / use 10min / use permanent / use suppression")

    def _get_ratysurd_pressure_text(self, level: int) -> str:
        if level <= 3:
            return "Calm"
        elif level <= 6:
            return "Rising"
        elif level <= 9:
            return "High"
        elif level <= 12:
            return "Dangerous"
        else:
            return "Extreme"

    def _handle_use_potion(self, command: str):
        parts = command.split(maxsplit=1)
        if len(parts) < 2:
            print("Usage: use <type>   (e.g. use 10min, use permanent, use suppression)")
            return

        potion = parts[1].strip().lower()

        success = False
        if potion in ("2min", "5min", "10min", "30min"):
            success = self.game.use_regular_potion(potion)
        elif potion in ("permanent", "cleanse"):
            success = self.game.use_permanent_cleanse()
        elif potion in ("suppression", "chaos", "suppress"):
            success = self.game.use_chaos_suppression()
        else:
            print(f"Unknown potion type: {potion}")
            return

        if success:
            self._print_status()
        else:
            print("You don't have that potion.")

    # ------------------------------------------------------------------
    # Shop / Buying businesses
    # ------------------------------------------------------------------

    BUSINESSES = [
        ("Полуночная Булочная", "A"),
        ("Бюро Незавершённых Дел", "A"),
        ("Эхо-Бар", "B"),
        ("Второе Я", "B"),
        ("Агентство Шёпот", "C"),
        ("Разлом-Экспресс", "C"),
        ("Рынок Никогда", "C"),
    ]

    def _get_next_business_cost(self) -> int:
        """Each new business costs 20% more than the previous one."""
        base_cost = 1000
        owned = len(self.game.state.businesses)
        return int(base_cost * (1.2 ** owned))

    def _print_shop(self):
        cost = self._get_next_business_cost()
        print(f"\n=== Shop ===")
        print(f"Next business cost: {cost} Бизнет")
        print("Available niches:")
        for i, (name, tier) in enumerate(self.BUSINESSES, 1):
            print(f"  {i}. {name} (Tier {tier})")
        print("\nUse: buy <number>  (e.g. buy 3)")

    def _handle_buy_business(self, command: str):
        parts = command.split()
        if len(parts) < 2:
            print("Usage: buy <number>")
            return

        try:
            index = int(parts[1]) - 1
        except ValueError:
            print("Please enter a valid number.")
            return

        if index < 0 or index >= len(self.BUSINESSES):
            print("Invalid business number.")
            return

        name, tier = self.BUSINESSES[index]
        cost = self._get_next_business_cost()

        if self.game.state.bizneta < cost:
            print(f"Not enough Bizneta. Need {cost}, have {self.game.state.bizneta:.0f}.")
            return

        # Create a new business instance
        from src.chaos_profit.core.models import Business

        # Base values per tier
        tier_client_gain = {"A": 10.0, "B": 13.5, "C": 17.5}
        tier_bizneta_per_client = {"A": 0.18, "B": 0.15, "C": 0.12}  # Tier C grows fast but earns less per client

        base_client_gain = tier_client_gain[tier]
        bizneta_per_client = tier_bizneta_per_client[tier]

        new_business = Business(
            niche_id=name.lower().replace(" ", "_").replace("-", "_"),
            clients=0.0,
            base_client_gain_per_minute=base_client_gain,
            bizneta_per_client_per_minute=bizneta_per_client,
        )

        self.game.state.bizneta -= cost
        self.game.state.businesses[new_business.niche_id] = new_business

        print(f"Bought {name} for {cost} Бизнет!")
        self._print_status()

    def _handle_spin(self):
        result = self.game.spin_slot()
        if result is None:
            print("Not enough Kloneta to spin!")
            return

        print(f"\n🎰  {result.reel1}  |  {result.reel2}  |  {result.reel3}")
        print(result.message)

        if result.bizneta_gained or result.clients_gained:
            print(f"   (+{result.bizneta_gained} Bizneta, +{result.clients_gained} clients)")

        self._print_status()

    def _print_status(self):
        state = self.game.state
        now = datetime.now(timezone.utc)

        print("\n" + "=" * 50)
        pressure = self._get_ratysurd_pressure_text(state.ratysurd_level)
        print(f"RATYSURD LEVEL: {state.ratysurd_level}   [{pressure}]")
        print("-" * 50)
        print(f"Kloneta: {state.kloneta}/5")
        print(f"Bizneta: {state.bizneta:,.2f}")
        print(f"Last played: {state.last_played_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Time since last action: {(now - state.last_played_at).total_seconds() / 60:.1f} min")

        # Show active global suppression
        if state.chaos_suppression_until and now < state.chaos_suppression_until:
            remaining = (state.chaos_suppression_until - now).total_seconds() / 60
            print(f"*** CHAOS SUPPRESSION ACTIVE: {remaining:.1f} min left ***")
        print("-" * 50)

        if state.businesses:
            print("BUSINESSES:")
            total_bizneta_per_min = 0.0

            for niche_id, biz in state.businesses.items():
                effective_gain = self.game.effect_system.get_effective_client_gain_per_minute(biz)
                bizneta_per_min = biz.clients * biz.bizneta_per_client_per_minute * (effective_gain / biz.base_client_gain_per_minute if biz.base_client_gain_per_minute > 0 else 1.0)
                total_bizneta_per_min += bizneta_per_min

                print(f"  • {niche_id:20} | Clients: {biz.clients:7.2f} | Gain: {effective_gain:6.2f}/min | Bizneta: {bizneta_per_min:6.2f}/min")

                if biz.effects:
                    print("      Active effects:")
                    for eff in biz.effects:
                        strength_pct = int(eff.strength * 100)
                        if eff.is_permanent:
                            time_str = "permanent"
                        else:
                            if eff.expires_at:
                                remaining = (eff.expires_at - now).total_seconds() / 60
                                time_str = f"{max(0, remaining):.1f} min left"
                            else:
                                time_str = "temporary"
                        print(f"        - {eff.effect_id}: {strength_pct:+d}% to clients ({time_str})")

            print(f"\n  Total estimated Bizneta income: {total_bizneta_per_min:.2f} / min")
        else:
            print("No businesses owned yet.")

        print("-" * 50)
        print(f"Potions:")
        print(f"  Regular: {state.regular_potions}")
        print(f"  Permanent Cleanse: {state.permanent_cleanse_potions}")
        print(f"  Chaos Suppression: {state.chaos_suppression_potions}")
        print("=" * 50)

    def _print_help(self):
        print("""
Available commands:
  status, s, st          - Show current game state (includes Ratysurd pressure)
  advance <minutes>, a   - Advance time (e.g. 'advance 60' or 'a 30')
  1m, 5m, 10m, 30m, 1h, 2h - Quick time advance
  deals, d               - Show current deal (if any)
  accept / refuse        - Accept or refuse the current deal
  potions, p, inv        - Show potion inventory
  use <type>             - Use a potion (e.g. use 10min, use permanent, use suppression)
  shop, buy              - Open shop to buy new businesses
  spin, slot, 🎰         - Spin the slot machine (costs 1 Kloneta)
  save, sv               - Force manual save
  reset, rst             - Full reset to factory state (with confirmation)
  tick, t                - Force a game tick (autosave check)
  help, h, ?             - Show this help
  quit, q, exit          - Save and exit
        """.strip())

    def _shutdown(self):
        self.game.shutdown()
        self.running = False
        print("Goodbye!")


def main():
    app = ConsoleApp()
    app.run()


if __name__ == "__main__":
    main()
