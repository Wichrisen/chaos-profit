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

    # Simulate some progress
    game.state.bizneta += 150
    game.state.kloneta = min(5, game.state.kloneta + 1)

    print(f"\nAfter some fake progress:")
    print(f"  Bizneta now    : {game.state.bizneta:.2f}")

    # Demonstrate time advancement (foundation for future systems)
    game.advance_time(45)      # 45 seconds
    game.advance_time(3600)    # 1 hour (offline simulation example)

    # Trigger manual save
    game.save()
    print("\n[Manual save triggered]")

    # Simulate shutdown
    game.shutdown()

    print("\n=== Test finished ===")


if __name__ == "__main__":
    main()
