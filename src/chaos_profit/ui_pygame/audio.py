"""
Simple and robust Audio Manager for Chaos & Profit.

Usage:
    from .audio import audio

    audio.play("spin_start")
    audio.play("reel_stop_1")
    audio.play("big_win")
"""

import pygame
from pathlib import Path
from typing import Dict, Optional


class AudioManager:
    def __init__(self, base_path: Optional[Path] = None):
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.enabled = True
        self.master_volume = 0.8

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except pygame.error as e:
                print(f"[Audio] Failed to initialize mixer: {e}")
                self.enabled = False
                return

        # Default sound folder
        if base_path is None:
            # Go up from ui_pygame to the project root and into assets/sounds
            self.sound_dir = Path(__file__).parent.parent.parent.parent / "assets" / "sounds"
        else:
            self.sound_dir = base_path

        self.sound_dir.mkdir(parents=True, exist_ok=True)

        # Preload common sounds (will be silent if files don't exist yet)
        self._load_default_sounds()

    def _load_default_sounds(self):
        """Define all sound names we plan to use."""
        sound_definitions = {
            # Slot machine
            "slot_click": "slot_click.wav",           # Clicking the big spin button
            "reel_spin_loop": "reel_spin_loop.wav",   # Looping sound while reels are spinning
            "reel_stop_1": "reel_stop_1.wav",         # Left reel stops
            "reel_stop_2": "reel_stop_2.wav",         # Middle reel stops (slightly more dramatic)
            "reel_stop_3": "reel_stop_3.wav",         # Right reel stops (most dramatic)
            "slot_result_good": "slot_result_good.wav",
            "slot_result_bad": "slot_result_bad.wav",
            "slot_result_chaotic": "slot_result_chaotic.wav",

            # UI
            "ui_click": "ui_click.wav",
            "ui_success": "ui_success.wav",
            "ui_danger": "ui_danger.wav",

            # General game
            "buy_business": "buy_business.wav",
            "upgrade": "upgrade.wav",
            "potion_use": "potion_use.wav",
            "deal_accept": "deal_accept.wav",
            "deal_refuse": "deal_refuse.wav",
        }

        for name, filename in sound_definitions.items():
            self._load_sound(name, filename)

    def _load_sound(self, name: str, filename: str):
        """Load a single sound file. Does nothing if file doesn't exist."""
        if not self.enabled:
            return

        filepath = self.sound_dir / filename
        if filepath.exists():
            try:
                sound = pygame.mixer.Sound(str(filepath))
                sound.set_volume(self.master_volume)
                self.sounds[name] = sound
            except Exception as e:
                print(f"[Audio] Failed to load {filename}: {e}")
        else:
            # File not present yet — that's fine during development
            pass

    def play(self, name: str, volume: float = 1.0):
        """Play a sound by name. Silently fails if sound doesn't exist."""
        if not self.enabled or name not in self.sounds:
            return

        try:
            sound = self.sounds[name]
            sound.set_volume(self.master_volume * volume)
            sound.play()
        except Exception as e:
            print(f"[Audio] Error playing '{name}': {e}")

    def play_loop(self, name: str, volume: float = 1.0):
        """Play a sound on loop (-1 = infinite)."""
        if not self.enabled or name not in self.sounds:
            return
        try:
            sound = self.sounds[name]
            sound.set_volume(self.master_volume * volume)
            sound.play(loops=-1)
        except Exception as e:
            print(f"[Audio] Error playing loop '{name}': {e}")

    def stop(self, name: str):
        """Stop a specific looping sound."""
        if not self.enabled or name not in self.sounds:
            return
        try:
            self.sounds[name].stop()
        except Exception:
            pass

    def set_master_volume(self, volume: float):
        """Set global volume (0.0 - 1.0)."""
        self.master_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.master_volume)

    def toggle(self):
        """Mute / unmute all sounds."""
        self.enabled = not self.enabled
        if not self.enabled:
            pygame.mixer.stop()


# Global instance — import this everywhere
audio = AudioManager()