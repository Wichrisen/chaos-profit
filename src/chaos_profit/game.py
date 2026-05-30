"""
Game orchestrator.

This will be the main class that ties systems together and runs the game loop.
For now it is just a placeholder.
"""

from .core.models import PlayerState
from .systems.save_system import SaveSystem


class Game:
    def __init__(self):
        self.save_system = SaveSystem()
        self.state: PlayerState = self.save_system.load()

    def save(self):
        self.save_system.save(self.state)

    def reset(self):
        self.state = self.save_system.reset_to_factory()
