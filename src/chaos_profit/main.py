"""
Entry point for the console prototype.
"""

from .game import Game


def main():
    game = Game()
    print("Chaos & Profit - Core loaded successfully!")
    print(f"Current Ratysurd level: {game.state.ratysurd_level}")
    print(f"Kloneta: {game.state.kloneta}")
    print(f"Bizneta: {game.state.bizneta}")
    print(f"Businesses owned: {len(game.state.businesses)}")


if __name__ == "__main__":
    main()
