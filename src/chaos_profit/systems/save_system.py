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

from ..core.models import PlayerState, Business, Effect
from .time_system import TimeSystem
from .effect_system import EffectSystem


SAVE_DIR = Path("saves")
SAVE_FILE = SAVE_DIR / "player.json"


class SaveSystem:
    def __init__(self, save_path: Path = SAVE_FILE):
        self.save_path = save_path
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self.effect_system = EffectSystem()
        self.time_system = TimeSystem(self.effect_system)

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
        """Convert PlayerState into a JSON-serializable dictionary."""
        data = {
            "version": state.version,
            "last_played_at": state.last_played_at.isoformat(),
            "ratysurd_level": state.ratysurd_level,
            "kloneta": state.kloneta,
            "kloneta_last_regen_at": state.kloneta_last_regen_at.isoformat(),
            "bizneta": state.bizneta,
            "businesses": {
                niche_id: self._serialize_business(biz)
                for niche_id, biz in state.businesses.items()
            },
            "regular_potions": state.regular_potions,
            "permanent_cleanse_potions": state.permanent_cleanse_potions,
            "chaos_suppression_potions": state.chaos_suppression_potions,
            "total_clients_ever": state.total_clients_ever,
            "total_bizneta_earned": state.total_bizneta_earned,
            "chaos_suppression_until": state.chaos_suppression_until.isoformat() if state.chaos_suppression_until else None,
        }
        return data

    def _serialize_business(self, business: Business) -> dict:
        return {
            "niche_id": business.niche_id,
            "clients": business.clients,
            "effects": [self._serialize_effect(e) for e in business.effects],
            "base_client_gain_per_minute": business.base_client_gain_per_minute,
            "base_bizneta_per_minute": business.base_bizneta_per_minute,
        }

    def _serialize_effect(self, effect: Effect) -> dict:
        return {
            "effect_id": effect.effect_id,
            "strength": effect.strength,
            "is_permanent": effect.is_permanent,
            "applied_at": effect.applied_at.isoformat(),
            "expires_at": effect.expires_at.isoformat() if effect.expires_at else None,
        }

    def _deserialize(self, data: dict) -> PlayerState:
        """Reconstruct PlayerState from dictionary."""

        businesses = {}
        for niche_id, biz_data in data.get("businesses", {}).items():
            effects = [
                Effect(
                    effect_id=e["effect_id"],
                    strength=e["strength"],
                    is_permanent=e["is_permanent"],
                    applied_at=datetime.fromisoformat(e["applied_at"]),
                    expires_at=datetime.fromisoformat(e["expires_at"]) if e.get("expires_at") else None,
                )
                for e in biz_data.get("effects", [])
            ]
            businesses[niche_id] = Business(
                niche_id=biz_data["niche_id"],
                clients=biz_data.get("clients", 0.0),
                effects=effects,
                base_client_gain_per_minute=biz_data.get("base_client_gain_per_minute", 0.0),
                base_bizneta_per_minute=biz_data.get("base_bizneta_per_minute", 0.0),
            )

        state = PlayerState(
            version=data.get("version", 1),
            last_played_at=datetime.fromisoformat(data["last_played_at"]),
            ratysurd_level=data.get("ratysurd_level", 1),
            kloneta=data.get("kloneta", 5),
            kloneta_last_regen_at=datetime.fromisoformat(data["kloneta_last_regen_at"]),
            bizneta=data.get("bizneta", 0.0),
            businesses=businesses,
            regular_potions=data.get("regular_potions", {}),
            permanent_cleanse_potions=data.get("permanent_cleanse_potions", 0),
            chaos_suppression_potions=data.get("chaos_suppression_potions", 0),
            total_clients_ever=data.get("total_clients_ever", 0.0),
            total_bizneta_earned=data.get("total_bizneta_earned", 0.0),
            chaos_suppression_until=datetime.fromisoformat(data["chaos_suppression_until"]) if data.get("chaos_suppression_until") else None,
        )
        return state

    def _apply_offline_progress(self, state: PlayerState, seconds_passed: float) -> PlayerState:
        """
        Apply all time-based systems while the player was away.
        This is one of the most important functions in the game.
        """
        print(f"[SaveSystem] Applying offline progress for {seconds_passed:.0f} seconds...")

        # Use the same time system as the live game for consistency
        self.time_system.apply_time(state, seconds_passed)

        return state
