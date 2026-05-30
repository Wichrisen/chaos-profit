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

    def _print_status(self):
        state = self.game.state
        now = datetime.now(timezone.utc)

        print("\n" + "=" * 50)
        print(f"RATYSURD LEVEL: {state.ratysurd_level}")
        print("-" * 50)
        print(f"Kloneta: {state.kloneta}/5")
        print(f"Bizneta: {state.bizneta:,.2f}")
        print(f"Last played: {state.last_played_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"Time since last action: {(now - state.last_played_at).total_seconds() / 60:.1f} min")
        print("-" * 50)

        if state.businesses:
            print("BUSINESSES:")
            for niche_id, biz in state.businesses.items():
                effective_gain = self.game.effect_system.get_effective_client_gain_per_minute(biz)
                effects_str = ""
                if biz.effects:
                    effects_str = f"  | Effects: {len(biz.effects)} active"
                print(f"  • {niche_id:20} | Clients: {biz.clients:7.2f} | Gain: {effective_gain:6.2f}/min{effects_str}")
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
  status, s, st          - Show current game state
  advance <minutes>, a   - Advance time (e.g. 'advance 60' or 'a 30')
  1m, 5m, 10m, 30m, 1h, 2h - Quick time advance
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
