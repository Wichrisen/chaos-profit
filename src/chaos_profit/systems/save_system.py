"""
SaveSystem — responsible for loading, saving, offline progress, and full reset.

Design goals:
- Keep PlayerState pure. SaveSystem is the only place that touches the filesystem.
- Offline progress calculation happens here on load.
- Full reset must be clean and reliable.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..core.models import PlayerState


SAVE_DIR = Path("saves")
SAVE_FILE = SAVE_DIR / "player.json"


class SaveSystem:
    def __init__(self, save_path: Path = SAVE_FILE):
        self.save_path = save_path
        self.save_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, state: PlayerState) -> None:
        """Save current state to disk (atomic write recommended in future)."""
        state.last_played_at = datetime.now(timezone.utc)

        data = self._serialize(state)
        self.save_path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    def load(self) -> PlayerState:
        """
        Load state from disk.
        If no save exists → return fresh PlayerState.
        If save exists → calculate offline progress.
        """
        if not self.save_path.exists():
            return PlayerState.new_game()

        data = json.loads(self.save_path.read_text(encoding="utf-8"))
        state = self._deserialize(data)

        # Calculate offline progress
        now = datetime.now(timezone.utc)
        seconds_passed = (now - state.last_played_at).total_seconds()

        if seconds_passed > 0:
            state = self._apply_offline_progress(state, seconds_passed)

        return state

    def reset_to_factory(self) -> PlayerState:
        """Completely reset the game to initial state."""
        fresh_state = PlayerState.new_game()
        self.save(fresh_state)
        return fresh_state

    # ------------------------------------------------------------------
    # Internal helpers (will be expanded later)
    # ------------------------------------------------------------------

    def _serialize(self, state: PlayerState) -> dict:
        # Simple implementation using dataclasses.asdict + custom datetime handling
        from dataclasses import asdict
        data = asdict(state)

        # Convert datetime objects to ISO strings
        def convert(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            return obj

        return json.loads(json.dumps(data, default=convert))

    def _deserialize(self, data: dict) -> PlayerState:
        # TODO: Proper deserialization with datetime reconstruction
        # For now we use a very naive approach
        state = PlayerState(**{k: v for k, v in data.items() if k != "last_played_at"})
        state.last_played_at = datetime.fromisoformat(data["last_played_at"])
        return state

    def _apply_offline_progress(self, state: PlayerState, seconds_passed: float) -> PlayerState:
        """
        Apply all time-based systems while the player was away.
        This is one of the most important functions in the game.
        """
        # TODO: Implement proper offline logic:
        # - Kloneta regen
        # - Bizneta income from businesses (with effects)
        # - Client gain/loss due to effects
        # - Temporary effect expiration

        # Placeholder for now
        print(f"[SaveSystem] Offline time passed: {seconds_passed:.0f} seconds (logic not implemented yet)")
        return state
