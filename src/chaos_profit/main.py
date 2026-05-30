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

    # Create a temporary test business with a negative effect to demonstrate EffectSystem + client changes
    from datetime import datetime, timezone, timedelta
    from src.chaos_profit.core.models import Business, Effect

    test_business = Business(
        niche_id="test_business",
        clients=100.0,
        base_bizneta_per_minute=3.0,
        base_client_gain_per_minute=20.0,   # Base 20 clients per minute
    )

    # Apply a strong temporary negative effect (-60% client gain for 30 minutes)
    negative_effect = Effect(
        effect_id="client_leak",
        strength=-0.60,
        is_permanent=False,
        applied_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    test_business.effects.append(negative_effect)

    game.state.businesses["test_business"] = test_business

    # Show effective client gain before time passes
    effective_gain = game.effect_system.get_effective_client_gain_per_minute(test_business)
    print(f"\nTest business effective client gain: {effective_gain:.2f} / min (base was 20.0)")
    print(f"Starting clients on test business: {test_business.clients:.2f}")

    # Demonstrate time advancement + effect expiration
    print("\n--- Time Advancement Demo ---")
    game.advance_time(45)           # 45 seconds
    game.advance_time(600)          # 10 minutes
    game.advance_time(25 * 60)      # 25 minutes

    # Show final state after time passed
    print(f"\nFinal clients on test business: {test_business.clients:.2f}")
    remaining_effects = len(test_business.effects)
    print(f"Effects remaining on test business: {remaining_effects}")

    # Trigger manual save
    game.save()
    print("\n[Manual save triggered]")

    # Simulate shutdown
    game.shutdown()

    print("\n=== Test finished ===")


if __name__ == "__main__":
    main()
