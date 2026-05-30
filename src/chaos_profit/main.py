"""
Entry point for the console prototype.

This is temporary scaffolding to test the foundation.
"""

from .game import Game


def main():
    print("=== Chaos & Profit - Foundation Test ===\n")

    game = Game()

    print(f"Loaded state:")
    print(f"  Ratysurd Level : {game.state.ratysurd_level}")
    print(f"  Kloneta        : {game.state.kloneta}")
    print(f"  Bizneta        : {game.state.bizneta:.2f}")
    print(f"  Businesses     : {len(game.state.businesses)}")
    print(f"  Last played    : {game.state.last_played_at}")

    # Simulate some progress + lower Kloneta to demonstrate regen
    game.state.bizneta += 150
    game.state.kloneta = 2   # Artificially lower it for demo

    print(f"\nAfter some fake progress:")
    print(f"  Bizneta now    : {game.state.bizneta:.2f}")
    print(f"  Kloneta now    : {game.state.kloneta}")

    # Demonstrate time advancement
    print("\n--- Time Advancement Demo ---")
    game.advance_time(45)           # 45 seconds → should do nothing
    game.advance_time(600)          # 10 minutes → should regen 1 Kloneta
    game.advance_time(25 * 60)      # 25 minutes → should regen 2 more (capped at 5)

    # Trigger manual save
    game.save()
    print("\n[Manual save triggered]")

    # Simulate shutdown
    game.shutdown()

    print("\n=== Test finished ===")


if __name__ == "__main__":
    main()
