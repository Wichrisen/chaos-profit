"""
Chaos & Profit - Pygame GUI (initial static version)

Resolution: 1366x768
Style: Minimalist + strong colors, Ocean Vibe base.
Slot is currently static (no animation yet).
"""

import pygame
import sys
import math
import re
from pathlib import Path
from datetime import datetime, timezone

try:
    import pygame_gui
    PYGAME_GUI_AVAILABLE = True
except ImportError:
    PYGAME_GUI_AVAILABLE = False
    pygame_gui = None

# Make sure we can import the core game
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.chaos_profit.game import Game
from src.chaos_profit.ui_pygame.colors import get_palette
from src.chaos_profit.ui_pygame.audio import audio
from src.chaos_profit.ui_pygame.assets import (
    load_slot_sprites, get_slot_sprite, prepare_sprites_for_display,
    get_ui_icon, prepare_ui_icons_for_display
)


# Window settings
WIDTH = 1366
HEIGHT = 768
FPS = 60
TITLE = "Хаос & Прибыль — GUI (статичная версия)"

# === SAFE HIGH-CHAOS VISUAL CORRUPTION (micro effects only) ===
# Philosophy: the world feels sick, but the UI must remain readable at all times.
# All effects are:
# - Localized (text, thin borders, 1-2 sparse lines max)
# - Alpha-aware where possible
# - Completely disabled when debug_force_visible=True
# - Start very late (12+) and only get noticeable at 14-15
CORRUPTION_START = 12          # First subtle hints appear
GLITCH_TITLES_FROM = 13        # Title breathing + jitter
SPARSE_CRACKS_FROM = 14        # Extremely sparse thin cracks (slot only)
EXTREME_FROM = 14
MAX_SPARSE_CRACKS = 2          # Hard cap - never dense
CRACK_INTENSITY = 90           # 0-255 alpha for cracks (lower = safer/fainter)


def format_number(n: float) -> str:
    """Human-readable formatting for large numbers (used in GUI)."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{int(n / 1_000)}K"
    if n >= 1_000:
        return f"{int(n):,}".replace(",", " ")
    return f"{int(n)}"


def format_play_time(minutes: float) -> str:
    """Smart time formatting for the status bar."""
    if minutes < 60:
        return f"{int(minutes)} мин"
    elif minutes < 1440:  # less than 24 hours
        hours = minutes / 60
        return f"{hours:.1f} ч"
    else:
        days = minutes / 1440
        if days < 10:
            return f"{days:.1f} дн"
        elif days < 70:
            weeks = days / 7
            return f"{weeks:.1f} нед"
        else:
            return f"{days:.0f} дн"


def humanize_niche_id(niche_id: str) -> str:
    """Convert ugly niche ids like 'echo_bar_4' or 'рынок_никогда_2' into readable names."""
    if not niche_id:
        return "Неизвестный бизнес"

    # Remove trailing instance counter (e.g. _4, _2, _17)
    name = re.sub(r'_\d+$', '', niche_id)

    # Replace underscores with spaces
    name = name.replace('_', ' ')

    # Title case (works reasonably for both Russian and English)
    name = name.title()

    # Small cleanups for common patterns
    name = name.replace('  ', ' ').strip()

    return name


def truncate_name(name: str, max_chars: int = 26) -> str:
    """Truncate long names with ellipsis for display in tight spaces."""
    if len(name) <= max_chars:
        return name
    return name[:max_chars - 1].rstrip() + "…"


def _symbol_text_to_key(text: str) -> tuple[str, bool]:
    """
    Map reel display text (after clean_reel stripping or emoji) to sprite logical key + corrupted flag.
    Supports full Wave 1 + Wave 2 set. Falls back to "" if no match (emoji/text render).
    """
    if not text:
        return "", False
    t = text.lower()

    is_corrupted = any(x in t for x in ["cursed", "twisted", "poison", "chaotic", "☠", "💀", "🩸", "глитч", "corrupt"])

    # Wave 1 core
    if "bizneta" in t or "💰" in text:
        return "bizneta", is_corrupted
    if "client" in t or "👥" in text:
        return "clients", is_corrupted
    if "potion" in t or "🧪" in text:
        # Regular potions stay on the "potion" key (we don't have per-duration sprites yet)
        return "potion", is_corrupted

    # Wave 2 — businesses (order matters for partial matches like "razlom")
    if "bakery" in t or "булочн" in t or "🍞" in text:
        return "bakery", is_corrupted
    if "debts" in t or "долг" in t or "бюро" in t or "📜" in text:
        return "debts", is_corrupted
    if "echo" in t or "эхо" in t or "🍹" in text:
        return "echo", is_corrupted
    if "second" in t or "второе" in t or "зеркал" in t or "🪞" in text:
        return "second", is_corrupted
    if "whisper" in t or "шёпот" in t or "шепот" in t or "🗣" in text:
        return "whisper", is_corrupted
    if "razlom" in t or "разлом" in t or "🌀" in text:
        return "razlom", is_corrupted
    if "never" in t or "никогда" in t or "рынок" in t or "❓" in text:
        return "never", is_corrupted

    # Wave 2 — rare god-tier potions (use dedicated keys)
    if "cleanse" in t or "permanent" in t or "✨" in text or "свящ" in t:
        return "rare_cleanse", is_corrupted
    if "suppress" in t or "подав" in t or "🌪" in text:
        return "rare_chaos", is_corrupted
    if "chaos" in t and "potion" in t:
        # fallback for rare chaos suppression results
        return "rare_chaos", is_corrupted

    # Fallback — will render as emoji/short text
    return "", False


def draw_button(screen, rect, text, font, base_color, hover_color, text_color, is_hovered, is_pressed=False, border_color=None):
    """Simple consistent button drawer with hover and high-chaos support."""
    x, y, w, h = rect
    color = hover_color if is_hovered else base_color

    # Slight press effect
    offset = 2 if is_pressed else 0

    pygame.draw.rect(screen, color, (x + offset, y + offset, w, h), border_radius=6)

    if border_color:
        pygame.draw.rect(screen, border_color, (x + offset, y + offset, w, h), 2, border_radius=6)
    else:
        pygame.draw.rect(screen, text_color, (x + offset, y + offset, w, h), 1, border_radius=6)

    label = font.render(text, True, text_color)
    label_rect = label.get_rect(center=(x + w // 2 + offset, y + h // 2 + offset))
    screen.blit(label, label_rect)


class PygameApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))

        # Now safe to convert sprites to display format + alpha + dark transparency
        prepare_sprites_for_display()
        prepare_ui_icons_for_display()

        self.clock = pygame.time.Clock()
        self.running = True

        # Load the actual game logic
        self.game = Game()
        self.font = pygame.font.SysFont("arial", 20)
        self.font_big = pygame.font.SysFont("arial", 28)
        self.font_reel = pygame.font.SysFont("arial", 18, bold=True)
        self.font_title = pygame.font.SysFont("arial", 36)

        self.palette = get_palette(self.game.state.ratysurd_level)

        # Warm slot symbol sprites (graceful fallback if missing)
        load_slot_sprites()

        self.last_spin_result = None  # For displaying result in static slot
        self.showing_reset_confirm = False
        self.showing_shop = False
        self.showing_upgrades = False
        self.time_speed = 1.0   # 0 = paused, 1 = normal, 5, 10, etc.
        self.hovered_business = None  # For hover tooltips on businesses
        self.debug_force_visible = True  # Set to False for normal high-chaos visuals
        self.empire_sickness = 0.0

        # Toast notification system
        self.toasts = []  # list of dicts: {text, color, timer, max_time}

        # Inventory (potions) modal
        self.showing_inventory = False

        # Onboarding / First-time experience
        self.has_seen_onboarding = False
        self.showing_onboarding = False
        self.has_spun_once = False

        # Slot machine spinning animation state
        self.is_spinning = False
        self.spin_start_time = 0.0
        self.spin_result = None
        self.reel_stop_times = [0.0, 0.0, 0.0]  # when each reel stops (in seconds since spin start)

        # Full-window glitch effect for Chaotic Spin results
        self.chaotic_glitch_until = 0  # timestamp (ms) until which the glitch is active

        # === pygame_gui (Hybrid UI) ===
        self.ui_manager = None
        self.showing_settings = False   # Example of a future pygame_gui window

        if PYGAME_GUI_AVAILABLE:
            self.ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT))
            # Theme can be customized later
            # self.ui_manager.get_theme().load_theme('data/themes/theme.json')

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        self.game.shutdown()

    def handle_events(self):
        for event in pygame.event.get():
            if self.ui_manager:
                self.ui_manager.process_events(event)

            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.showing_reset_confirm:
                        self.showing_reset_confirm = False
                    else:
                        self.running = False

                # Temporary debug hotkey: press R to force-show reset modal (for testing)
                if event.key == pygame.K_r:
                    self.showing_reset_confirm = not self.showing_reset_confirm
                    if self.showing_reset_confirm:
                        self.showing_shop = False
                        self.showing_upgrades = False
                    print(f"[DEBUG] Forced showing_reset_confirm = {self.showing_reset_confirm}")

                # Hybrid UI test: Open pygame_gui Settings window
                if event.key == pygame.K_F1 and self.ui_manager:
                    self._toggle_settings_window()

                # Debug: Print Kloneta regeneration status (press T)
                if event.key == pygame.K_t:
                    self._debug_kloneta_status()

                # Spin with SPACE
                if event.key == pygame.K_SPACE:
                    if not self.is_spinning:
                        self._start_slot_spin()

            if PYGAME_GUI_AVAILABLE and event.type == pygame_gui.UI_BUTTON_PRESSED:
                if hasattr(self, 'close_settings_button') and event.ui_element == self.close_settings_button:
                    if self.settings_window:
                        self.settings_window.kill()
                        self.settings_window = None
                        self.showing_settings = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Remember if the reset modal was already open *before* we process this click.
                # This prevents the "click outside modal" logic from immediately closing it
                # on the same click that opened it from the bottom button.
                reset_modal_was_open = self.showing_reset_confirm

                # Consistent bottom bar Y for all click detection in the bottom strip
                bottom_y = HEIGHT - 58

                # Slot button area (big spin button)
                if 920 < mx < 1220 and 350 < my < 418:
                    if not self.is_spinning:
                        self._start_slot_spin()

                # Speed control buttons (using same bottom bar calculation)
                speeds = [0, 1, 5, 10]
                for i, speed in enumerate(speeds):
                    bx = 36 + i * 52
                    if bx < mx < bx + 48 and bottom_y + 8 < my < bottom_y + 40:
                        self.time_speed = speed
                        break

                # Manual fast forward buttons
                time_base = 36 + 220
                for i in range(4):
                    bx = time_base + i * 55
                    if bx < mx < bx + 50 and bottom_y + 8 < my < bottom_y + 40:
                        minutes = [1, 5, 10, 30][i]
                        self._advance_time(minutes * 60)
                        break

                # Potion usage
                pot_base = 510
                if pot_base < mx < pot_base + 100 and bottom_y + 8 < my < bottom_y + 40:
                    self._try_use_potion("10min")
                elif pot_base + 108 < mx < pot_base + 243 and bottom_y + 8 < my < bottom_y + 40:
                    self._try_use_potion("permanent")
                elif pot_base + 250 < mx < pot_base + 385 and bottom_y + 8 < my < bottom_y + 40:
                    self._try_use_potion("suppression")

                # Deal buttons (bottom-right deal panel)
                if self.game.deal_system.current_deal:
                    deal_panel_x = WIDTH - 510
                    deal_y = HEIGHT - 153
                    # Accept button
                    if deal_panel_x + 12 < mx < deal_panel_x + 152 and deal_y + 52 < my < deal_y + 78:
                        self._resolve_deal(accept=True)
                    # Refuse button
                    elif deal_panel_x + 165 < mx < deal_panel_x + 305 and deal_y + 52 < my < deal_y + 78:
                        self._resolve_deal(accept=False)

                # Shop item clicks
                if self.showing_shop:
                    shop_w = 520
                    shop_h = 420
                    shop_x = (WIDTH - shop_w) // 2
                    shop_y = (HEIGHT - shop_h) // 2 - 20
                    start_y = shop_y + 105

                    for i in range(7):
                        y_pos = start_y + i * 42
                        if shop_x + 15 < mx < shop_x + shop_w - 15 and y_pos < my < y_pos + 38:
                            if self.game.buy_business(i):
                                # Success toast
                                options = self.game.get_shop_options()
                                if i < len(options):
                                    biz_name = options[i]["name"]
                                    self.add_toast(f"Бизнес куплен: {biz_name}", (90, 200, 160))
                                audio.play("buy_business")
                                self.showing_shop = False  # close after purchase
                            break

                # Upgrades panel clicks - proper row detection
                if self.showing_upgrades:
                    panel_w = 620
                    panel_h = 520
                    panel_x = (WIDTH - panel_w) // 2
                    panel_y = (HEIGHT - panel_h) // 2 - 40

                    # Close if clicking outside the panel
                    if not (panel_x < mx < panel_x + panel_w and panel_y < my < panel_y + panel_h):
                        self.showing_upgrades = False
                    else:
                        # Check which upgrade row was clicked
                        if hasattr(self, 'upgrade_click_regions'):
                            for rect, business_id, up_type in self.upgrade_click_regions:
                                rx, ry, rw, rh = rect
                                if rx < mx < rx + rw and ry < my < ry + rh:
                                    if self.game.upgrade_business(business_id, up_type):
                                        # Nice display name for upgrade type
                                        up_names = {"growth": "Рост", "efficiency": "Эффективность", "resilience": "Устойчивость"}
                                        up_name = up_names.get(up_type, up_type)
                                        display_name = humanize_niche_id(business_id)
                                        self.add_toast(f"Улучшено: {display_name} — {up_name}", (130, 190, 230))
                                        audio.play("upgrade")
                                    break  # only upgrade one per click

                # Onboarding panel - click anywhere to close
                if self.showing_onboarding:
                    self.showing_onboarding = False
                    self.has_seen_onboarding = True
                    # We don't save it yet for simplicity, it will show again on restart
                    # until we add proper persistence

                # Inventory panel clicks
                if self.showing_inventory:
                    panel_w = 480
                    panel_h = 320
                    panel_x = (WIDTH - panel_w) // 2
                    panel_y = (HEIGHT - panel_h) // 2 - 30

                    # Close if clicking outside
                    if not (panel_x < mx < panel_x + panel_w and panel_y < my < panel_y + panel_h):
                        self.showing_inventory = False
                    else:
                        # Check use buttons
                        if hasattr(self, 'inventory_use_regions'):
                            for rect, potion_key in self.inventory_use_regions:
                                rx, ry, rw, rh = rect
                                if rx < mx < rx + rw and ry < my < ry + rh:
                                    # Map key to potion type used in _try_use_potion
                                    key_to_type = {
                                        "10min": "10min",
                                        "permanent": "permanent",
                                        "suppression": "suppression",
                                    }
                                    ptype = key_to_type.get(potion_key)
                                    if ptype:
                                        self._try_use_potion(ptype)
                                    break

                # Vertical action buttons (under Businesses)
                if hasattr(self, 'vertical_action_rects'):
                    for rect, action in self.vertical_action_rects:
                        rx, ry, rw, rh = rect
                        if rx < mx < rx + rw and ry < my < ry + rh:
                            if action == "shop":
                                self.showing_shop = not self.showing_shop
                                if self.showing_shop:
                                    self.showing_inventory = False
                                    self.showing_upgrades = False
                                    self.showing_reset_confirm = False
                            elif action == "upgrades":
                                self.showing_upgrades = not self.showing_upgrades
                                if self.showing_upgrades:
                                    self.showing_shop = False
                                    self.showing_inventory = False
                                    self.showing_reset_confirm = False
                            elif action == "inventory":
                                self.showing_inventory = not self.showing_inventory
                                if self.showing_inventory:
                                    self.showing_shop = False
                                    self.showing_upgrades = False
                                    self.showing_reset_confirm = False
                            elif action == "reset":
                                if not self.showing_reset_confirm:
                                    self.showing_reset_confirm = True
                                    self.showing_shop = False
                                    self.showing_upgrades = False
                                    self.showing_inventory = False

                            audio.play("ui_click")  # click feedback for action buttons
                            break

                # Reset confirmation modal buttons.
                # We only process clicks on the modal if it was already open BEFORE this mouse event.
                # This prevents the opening click (on the bottom "Сброс" button) from being treated as "outside click".
                if reset_modal_was_open:
                    modal_w = 360
                    modal_h = 130
                    modal_x = (WIDTH - modal_w) // 2
                    modal_y = (HEIGHT - modal_h) // 2 - 20

                    # Yes button ("ДА, СБРОСИТЬ")
                    if modal_x + 25 < mx < modal_x + 165 and modal_y + 78 < my < modal_y + 110:
                        self.game.reset_to_factory()
                        self.last_spin_result = None
                        self.palette = get_palette(self.game.state.ratysurd_level)
                        self.showing_reset_confirm = False
                        self.showing_shop = False
                        self.showing_upgrades = False
                        self.showing_inventory = False
                        self.time_speed = 1.0  # reset speed too for clean state
                        self.add_toast("Прогресс сброшен", (200, 120, 120))
                    # Cancel button ("ОТМЕНА")
                    elif modal_x + 195 < mx < modal_x + 335 and modal_y + 78 < my < modal_y + 110:
                        self.showing_reset_confirm = False
                    else:
                        # Click outside the modal → cancel
                        if not (modal_x < mx < modal_x + modal_w and modal_y < my < modal_y + modal_h):
                            self.showing_reset_confirm = False

    def update(self, dt: float):
        # === Onboarding trigger ===
        if not self.has_seen_onboarding and not self.has_spun_once and len(self.game.state.businesses) == 0:
            self.showing_onboarding = True

        # Real-time time progression
        if self.time_speed > 0:
            game_seconds = dt * self.time_speed
            self.game.advance_time(game_seconds)
            # Also let deals check for new opportunities
            self.game.deal_system.update(self.game.state, game_seconds)

        # Keep palette in sync with current Ratysurd
        current_level = self.game.state.ratysurd_level
        self.palette = get_palette(current_level)

        # Update toasts (age them)
        for toast in self.toasts[:]:
            toast["timer"] -= dt
            if toast["timer"] <= 0:
                self.toasts.remove(toast)

        # pygame_gui update
        if self.ui_manager:
            self.ui_manager.update(dt)

        # Slot spinning animation update + audio
        if self.is_spinning:
            current_time = pygame.time.get_ticks() / 1000.0 - self.spin_start_time

            # Play individual reel stop sounds
            for i in range(3):
                stop_time = self.reel_stop_times[i]
                # Check if this reel just stopped (within this frame)
                if current_time >= stop_time and not hasattr(self, f"_reel_stopped_{i}"):
                    setattr(self, f"_reel_stopped_{i}", True)
                    audio.play(f"reel_stop_{i + 1}", volume=0.9 + i * 0.05)

            if current_time >= self.reel_stop_times[2]:  # last reel finished
                audio.stop("reel_spin_loop")

                # Play result sound based on outcome
                if self.spin_result:
                    msg = self.spin_result.message.lower()
                    if "chaotic" in msg or "cursed" in msg or "twisted" in msg:
                        audio.play("slot_result_chaotic", volume=1.0)
                    elif any(word in msg for word in ["больш", "много", "отлично", "редк"]):
                        audio.play("slot_result_good", volume=0.95)
                    else:
                        audio.play("slot_result_bad", volume=0.7)

                self.last_spin_result = self.spin_result
                self.is_spinning = False
                self.spin_result = None
                self.has_spun_once = True

                # Trigger full-window glitch if this was a Chaotic Spin
                if self.last_spin_result:
                    msg = self.last_spin_result.message.lower()
                    if "chaotic" in msg or "cursed" in msg or "twisted" in msg:
                        self.chaotic_glitch_until = pygame.time.get_ticks() + 3000  # 3 seconds of intense glitch (matches chaotic sound length)

                # Reset per-reel stop flags for next spin
                for i in range(3):
                    if hasattr(self, f"_reel_stopped_{i}"):
                        delattr(self, f"_reel_stopped_{i}")

    def _advance_time(self, seconds: float):
        """Advance game time and update deals."""
        self.game.advance_time(seconds)
        # Force deal system to check for new deals
        self.game.deal_system.update(self.game.state, seconds)

    def _try_use_potion(self, potion_type: str):
        success = False
        if potion_type == "10min":
            success = self.game.use_regular_potion("10min")
        elif potion_type == "permanent":
            success = self.game.use_permanent_cleanse()
        elif potion_type == "suppression":
            success = self.game.use_chaos_suppression()

        if success:
            print(f"[GUI] Used potion: {potion_type}")
            potion_names = {
                "10min": "Зелье времени (10 мин)",
                "permanent": "Постоянное очищение",
                "suppression": "Подавление хаоса"
            }
            name = potion_names.get(potion_type, potion_type)
            self.add_toast(f"Использовано: {name}", (100, 200, 180))
            audio.play("potion_use")

    def _start_slot_spin(self):
        """Starts the visual spinning animation for the slot machine."""
        if self.is_spinning:
            return
        if not self.game.slot_system.can_spin(self.game.state):
            return

        # Get the final result immediately (consumes Kloneta, determines outcome)
        result = self.game.spin_slot()
        self.spin_result = result
        self.last_spin_result = None  # hide previous result during spin

        # === AUDIO ===
        audio.play("slot_click")
        audio.play_loop("reel_spin_loop", volume=0.85)

        # Reset reel stop flags
        for i in range(3):
            if hasattr(self, f"_reel_stopped_{i}"):
                delattr(self, f"_reel_stopped_{i}")

        # Start spinning state
        self.is_spinning = True
        self.spin_start_time = pygame.time.get_ticks() / 1000.0

        # Classic staggered reel stop times (in seconds)
        base = 0.85
        self.reel_stop_times = [
            base,           # left reel
            base + 0.45,    # middle reel
            base + 0.90,    # right reel (longest)
        ]

    def _resolve_deal(self, accept: bool):
        pressure = self.game.get_effective_chaos_pressure()
        success, message = self.game.deal_system.resolve_deal(
            self.game.state, accept, chaos_pressure=pressure
        )
        print(f"[GUI] Deal result: {message}")

        # Toast feedback for deals
        if accept:
            self.add_toast("Сделка принята", (80, 200, 140) if success else (220, 90, 90))
        else:
            self.add_toast("Сделка отклонена", (180, 180, 200))

    def add_toast(self, text: str, color=None, duration: float = 2.6):
        """Add a temporary notification toast."""
        if color is None:
            color = (170, 210, 230)  # default info color

        self.toasts.append({
            "text": text,
            "color": color,
            "timer": duration,
            "max_time": duration
        })

        # Limit number of simultaneous toasts
        if len(self.toasts) > 6:
            self.toasts.pop(0)

    # === pygame_gui Hybrid Methods ===

    def _toggle_settings_window(self):
        """Example of opening a pygame_gui window (hybrid approach)."""
        if not self.ui_manager:
            print("[Hybrid] pygame_gui is not available.")
            return

        if hasattr(self, 'settings_window') and self.settings_window:
            self.settings_window.kill()
            self.settings_window = None
            self.showing_settings = False
            return

        # Create a simple settings window using pygame_gui
        self.settings_window = pygame_gui.elements.UIWindow(
            rect=pygame.Rect(400, 150, 500, 400),
            manager=self.ui_manager,
            window_display_title="Настройки",
            object_id="#settings_window"
        )

        # Add some elements as example
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(20, 20, 460, 30),
            text="Настройки игры (пример pygame_gui)",
            manager=self.ui_manager,
            container=self.settings_window
        )

        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(20, 70, 200, 30),
            text="Громкость музыки:",
            manager=self.ui_manager,
            container=self.settings_window
        )

        self.volume_slider = pygame_gui.elements.UIHorizontalSlider(
            relative_rect=pygame.Rect(230, 70, 200, 30),
            start_value=0.8,
            value_range=(0.0, 1.0),
            manager=self.ui_manager,
            container=self.settings_window
        )

        self.close_settings_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(180, 320, 140, 40),
            text="Закрыть",
            manager=self.ui_manager,
            container=self.settings_window
        )

        self.showing_settings = True
        print("[Hybrid] Settings window opened using pygame_gui")

    def _debug_kloneta_status(self):
        """Debug helper: shows current Kloneta regeneration status."""
        state = self.game.state
        now = datetime.now(timezone.utc)
        time_since_last = (now - state.kloneta_last_regen_at).total_seconds()

        print("\n=== KLONETA DEBUG ===")
        print(f"Current Kloneta: {state.kloneta}/5")
        print(f"Last regen at:   {state.kloneta_last_regen_at}")
        print(f"Time since last: {time_since_last:.1f} seconds ({time_since_last/60:.1f} minutes)")
        print(f"Regen interval:  300 seconds (5 minutes)")
        print(f"Time until next: {max(0, 300 - time_since_last):.1f} seconds")
        print("=====================\n")

    def _draw_onboarding_panel(self):
        """Simple first-time guidance panel."""
        panel_w = 520
        panel_h = 340
        panel_x = (WIDTH - panel_w) // 2
        panel_y = (HEIGHT - panel_h) // 2 - 40

        # Background
        bg = (28, 30, 38)
        border = (100, 80, 120)
        pygame.draw.rect(self.screen, bg, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, border, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        # Title
        title = self.font_big.render("Добро пожаловать в Хаос", True, (230, 200, 255))
        self.screen.blit(title, (panel_x + 30, panel_y + 20))

        # Content
        lines = [
            "Ты управляешь империей в мире, который постепенно сходит с ума.",
            "",
            "Тебе выдали 1000 Бизнет на старте, чтобы сразу начать.",
            "",
            "• Покупай бизнесы в «Магазине»",
            "• Зарабатывай Бизнету",
            "• Крути слот-машину (тратит Клонету)",
            "• Клонета восстанавливается раз в 5 реальных минут",
            "• Чем выше Рейтисурд — тем опаснее и интереснее становится",
            "",
            "Начни с покупки первого бизнеса и одного спина."
        ]

        y = panel_y + 65
        for line in lines:
            text = self.font.render(line, True, (200, 195, 210))
            self.screen.blit(text, (panel_x + 30, y))
            y += 26

        # Close button area hint
        hint = self.font.render("Кликни в любом месте, чтобы закрыть", True, (160, 150, 170))
        self.screen.blit(hint, (panel_x + 30, panel_y + panel_h - 35))

    def _draw_active_deal_panel(self, y: int):
        """Simple but functional deal display."""
        pal = self.palette
        deal = self.game.deal_system.current_deal
        if not deal:
            return

        width = 480
        x = WIDTH - width - 30

        # Background
        pygame.draw.rect(self.screen, pal.panel_bg, (x, y, width, 85))
        border_col = pal.accent_danger if deal.is_dark or deal.is_twisted else pal.panel_border
        pygame.draw.rect(self.screen, border_col, (x, y, width, 85), 2)

        # Deal info
        deal_type = "ТЁМНАЯ" if deal.is_dark else "Обычная"
        if getattr(deal, 'is_twisted', False):
            deal_type = "ИСКАЖЁННАЯ"

        deal_name = truncate_name(humanize_niche_id(deal.business_niche), max_chars=30)
        title = self.font.render(f"{deal_type} СДЕЛКА — {deal_name}", True, pal.text)
        self.screen.blit(title, (x + 12, y + 8))

        chance = int(deal.success_chance * 100)
        chance_text = self.font.render(f"Шанс успеха: ~{chance}%", True, pal.text_dim)
        self.screen.blit(chance_text, (x + 12, y + 32))

        # Accept / Refuse buttons
        btn_y = y + 52
        pygame.draw.rect(self.screen, pal.accent, (x + 12, btn_y, 140, 26), border_radius=4)
        self.screen.blit(self.font.render("ПРИНЯТЬ", True, pal.text), (x + 35, btn_y + 4))

        pygame.draw.rect(self.screen, pal.accent_danger, (x + 165, btn_y, 140, 26), border_radius=4)
        self.screen.blit(self.font.render("ОТКАЗАТЬСЯ", True, pal.text), (x + 180, btn_y + 4))

    def _draw_reset_confirm_modal(self):
        """Dangerous action confirmation modal — now actually visible."""
        pal = self.palette
        state = self.game.state

        modal_w = 360
        modal_h = 130
        modal_x = (WIDTH - modal_w) // 2
        modal_y = (HEIGHT - modal_h) // 2 - 20

        # Semi-opaque dark background for the modal (safe, never pure black)
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))  # subtle dimming
        self.screen.blit(overlay, (0, 0))

        # Modal panel
        if self.debug_force_visible:
            bg = (38, 32, 36)
            border = (160, 50, 55)
        else:
            bg = (32, 26, 30)
            border = (170, 45, 50) if state.ratysurd_level >= 10 else (140, 50, 55)

        pygame.draw.rect(self.screen, bg, (modal_x, modal_y, modal_w, modal_h), border_radius=10)
        pygame.draw.rect(self.screen, border, (modal_x, modal_y, modal_w, modal_h), 3, border_radius=10)

        # Warning title (no emoji to avoid font issues)
        title = self.font_big.render("СБРОСИТЬ ПРОГРЕСС?", True, (255, 180, 160))
        self.screen.blit(title, (modal_x + 30, modal_y + 14))

        # Warning text
        warning = self.font.render("Весь прогресс, бизнесы, улучшения и зелья будут потеряны.", True, pal.text_dim)
        self.screen.blit(warning, (modal_x + 25, modal_y + 48))

        # Yes button (danger)
        yes_rect = (modal_x + 25, modal_y + 78, 140, 32)
        draw_button(
            self.screen,
            yes_rect,
            "ДА, СБРОСИТЬ",
            self.font,
            (160, 30, 30),
            (200, 45, 45),
            (255, 230, 230),
            False
        )

        # No / Cancel button
        no_rect = (modal_x + 195, modal_y + 78, 140, 32)
        draw_button(
            self.screen,
            no_rect,
            "ОТМЕНА",
            self.font,
            (70, 70, 80),
            (100, 100, 110),
            pal.text,
            False
        )

    def _draw_toasts(self):
        """Draw active notification toasts in the top-right corner."""
        if not self.toasts:
            return

        pal = self.palette
        x = WIDTH - 260
        y = 82
        toast_height = 26
        spacing = 4

        for i, toast in enumerate(self.toasts):
            current_y = y + i * (toast_height + spacing)

            # Fade out in the last 0.5 seconds
            alpha = 255
            if toast["timer"] < 0.5:
                alpha = int(255 * (toast["timer"] / 0.5))

            # Background
            bg_color = (28, 32, 40) if self.debug_force_visible else tuple(max(22, c - 4) for c in pal.panel_bg)
            pygame.draw.rect(self.screen, bg_color, (x, current_y, 245, toast_height), border_radius=5)

            # Subtle border
            border_col = tuple(min(255, c + 30) for c in toast["color"])
            pygame.draw.rect(self.screen, border_col, (x, current_y, 245, toast_height), 1, border_radius=5)

            # Text (with alpha if fading)
            text_surf = self.font.render(toast["text"], True, toast["color"])
            if alpha < 255:
                text_surf.set_alpha(alpha)
            self.screen.blit(text_surf, (x + 10, current_y + 5))

    def _draw_chaotic_glitch_overlay(self):
        """Intense full-window glitch effect for Chaotic Spin results."""
        if pygame.time.get_ticks() > self.chaotic_glitch_until:
            return

        # Create a working surface
        glitch_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

        # Copy current screen content
        glitch_surface.blit(self.screen, (0, 0))

        current_time = pygame.time.get_ticks()

        # === Horizontal tearing bands ===
        num_bands = 7 + (current_time % 5)
        for _ in range(num_bands):
            y = (current_time * 7 + _ * 97) % HEIGHT
            band_height = 8 + (current_time % 13)
            offset = int((current_time * 0.8 + _ * 23) % 40) - 20

            # Slice and shift horizontally
            band = glitch_surface.subsurface((0, y, WIDTH, min(band_height, HEIGHT - y))).copy()
            glitch_surface.blit(band, (offset, y))

        # === Random glitch blocks (heavy distortion) ===
        for _ in range(5):
            bx = (current_time * 3 + _ * 137) % (WIDTH - 80)
            by = (current_time * 5 + _ * 211) % (HEIGHT - 60)
            bw = 40 + (current_time % 80)
            bh = 12 + (current_time % 25)

            block = glitch_surface.subsurface((bx, by, min(bw, WIDTH - bx), min(bh, HEIGHT - by))).copy()

            # Random strong offset + slight color shift
            shift_x = (current_time % 17) - 8
            shift_y = ((current_time + _ * 7) % 11) - 5

            # Red/crimson tint on glitch blocks
            block.fill((180, 30, 40), special_flags=pygame.BLEND_RGB_MULT)
            glitch_surface.blit(block, (bx + shift_x, by + shift_y))

        # === Strong red corruption overlay ===
        red_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        intensity = 35 + int((current_time % 800) / 25)
        red_overlay.fill((140, 15, 25, min(85, intensity)))
        glitch_surface.blit(red_overlay, (0, 0))

        # === RGB split (subtle but nasty) ===
        r = glitch_surface.copy()
        g = glitch_surface.copy()
        b = glitch_surface.copy()

        r.fill((255, 0, 0), special_flags=pygame.BLEND_RGB_MULT)
        g.fill((0, 255, 0), special_flags=pygame.BLEND_RGB_MULT)
        b.fill((0, 0, 255), special_flags=pygame.BLEND_RGB_MULT)

        offset = 2 + (current_time % 3)
        glitch_surface.blit(r, (offset, 0), special_flags=pygame.BLEND_RGB_ADD)
        glitch_surface.blit(g, (-offset, 0), special_flags=pygame.BLEND_RGB_ADD)
        glitch_surface.blit(b, (0, 1), special_flags=pygame.BLEND_RGB_ADD)

        # Blit the final glitched version over the screen
        self.screen.blit(glitch_surface, (0, 0))

    def _draw_vertical_action_buttons(self, x: int, start_y: int):
        """Vertical action buttons column under the Slot Machine (compact but nice)."""
        pal = self.palette
        state = self.game.state

        buttons = [
            ("Магазин",    "shop",      (50, 75, 95),  (75, 110, 140), "action_shop"),
            ("Улучшения",  "upgrades",  (65, 55, 90),  (95, 75, 125), "action_upgrades"),
            ("Инвентарь",  "inventory", (50, 80, 90),  (75, 115, 125), "action_inventory"),
            ("Сброс",      "reset",     (140, 35, 35), (180, 50, 50),  "action_reset"),
        ]

        btn_w = 200
        btn_h = 36
        gap = 6
        icon_size_btn = 26

        mouse_pos = pygame.mouse.get_pos()

        # Very subtle background container for the column
        container_height = 4 * btn_h + 3 * gap + 8
        container_color = (22, 25, 32) if not self.debug_force_visible else (30, 33, 40)

        # Add world corruption tint to the action buttons at high Ratysurd
        if not self.debug_force_visible and state.ratysurd_level >= 14:
            total_neg = sum(len([e for e in b.effects if e.strength < 0]) for b in state.businesses.values())
            if total_neg >= 6:
                container_color = (30, 18, 20)

        pygame.draw.rect(self.screen, container_color, (x - 6, start_y - 4, btn_w + 12, container_height), border_radius=6)

        for i, (label, action, base, hover, icon_name) in enumerate(buttons):
            by = start_y + i * (btn_h + gap)

            is_hovered = x < mouse_pos[0] < x + btn_w and by < mouse_pos[1] < by + btn_h

            if action == "reset":
                is_high = state.ratysurd_level >= 10
                base_c = (155, 32, 32) if is_high else base
                hover_c = (195, 48, 48) if is_high else hover
                txt_c = (255, 225, 225) if is_high else pal.text
            else:
                base_c = base
                hover_c = hover
                txt_c = pal.text

            # Draw button background + border manually so we can place icon + shifted text nicely
            color = hover_c if is_hovered else base_c
            pygame.draw.rect(self.screen, color, (x, by, btn_w, btn_h), border_radius=6)
            pygame.draw.rect(self.screen, txt_c, (x, by, btn_w, btn_h), 1, border_radius=6)

            # Icon on the left
            icon = get_ui_icon(icon_name, icon_size_btn)
            icon_x = x + 10
            icon_y = by + (btn_h - icon_size_btn) // 2

            if icon:
                draw_icon = icon
                if action == "reset" and not self.debug_force_visible and state.ratysurd_level >= 12:
                    draw_icon = icon.copy()
                    t = pygame.Surface((icon_size_btn, icon_size_btn), pygame.SRCALPHA)
                    t.fill((200, 40, 50, 55))
                    draw_icon.blit(t, (0, 0))
                self.screen.blit(draw_icon, (icon_x, icon_y))

            # Text shifted right to make space for icon
            text_x = x + 10 + icon_size_btn + 8 if icon else x + 12
            text_y = by + (btn_h - self.font_big.get_height()) // 2
            label_surf = self.font_big.render(label, True, txt_c)
            self.screen.blit(label_surf, (text_x, text_y))

            if not hasattr(self, 'vertical_action_rects'):
                self.vertical_action_rects = []
            self.vertical_action_rects.append(((x, by, btn_w, btn_h), action))

    def _draw_inventory_panel(self):
        """Inventory modal focused on potions."""
        pal = self.palette
        state = self.game.state

        panel_w = 480
        panel_h = 320
        panel_x = (WIDTH - panel_w) // 2
        panel_y = (HEIGHT - panel_h) // 2 - 30

        # Background
        bg = (26, 30, 38) if self.debug_force_visible else (24, 26, 34)
        border = (90, 110, 130) if self.debug_force_visible else (80, 100, 120)
        pygame.draw.rect(self.screen, bg, (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, border, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=10)

        # Title
        title = self.font_big.render("ИНВЕНТАРЬ — Зелья", True, pal.text)
        self.screen.blit(title, (panel_x + 25, panel_y + 18))

        # Potion data
        potions = [
            {
                "key": "10min",
                "icon": "potion_time",
                "name": "Зелье Времени",
                "count": state.regular_potions.get("10min", 0),
                "desc": "Ускоряет время на 10 реальных минут.",
                "color": (90, 180, 160),
            },
            {
                "key": "permanent",
                "icon": "potion_cleanse",
                "name": "Постоянное Очищение",
                "count": state.permanent_cleanse_potions,
                "desc": "Снимает все негативные эффекты с бизнесов.",
                "color": (140, 160, 220),
            },
            {
                "key": "suppression",
                "icon": "potion_chaos",
                "name": "Подавление Хаоса",
                "count": state.chaos_suppression_potions,
                "desc": "Сильно снижает давление Рейтисурда на 15 мин.",
                "color": (200, 140, 140),
            },
        ]

        start_y = panel_y + 65
        icon_size_inv = 42
        for i, pot in enumerate(potions):
            row_y = start_y + i * 78

            # Row background
            row_bg = (32, 36, 44) if self.debug_force_visible else (28, 30, 38)
            pygame.draw.rect(self.screen, row_bg, (panel_x + 20, row_y, panel_w - 40, 68), border_radius=6)

            # Potion icon
            pot_icon = get_ui_icon(pot["icon"], icon_size_inv)
            icon_x = panel_x + 32
            if pot_icon:
                self.screen.blit(pot_icon, (icon_x, row_y + 13))
            text_offset = icon_size_inv + 18 if pot_icon else 0

            # Potion name + count
            name_text = f"{pot['name']}  ×{pot['count']}"
            name_col = pot['color'] if pot['count'] > 0 else (120, 120, 130)
            self.screen.blit(self.font_big.render(name_text, True, name_col), (panel_x + 35 + text_offset, row_y + 8))

            # Description
            self.screen.blit(self.font.render(pot['desc'], True, pal.text_dim), (panel_x + 35 + text_offset, row_y + 32))

            # Use button
            btn_x = panel_x + panel_w - 130
            btn_y = row_y + 18
            btn_w = 95
            btn_h = 32

            can_use = pot['count'] > 0
            base_c = (55, 95, 80) if can_use else (50, 50, 55)
            hover_c = (75, 130, 105) if can_use else (55, 55, 60)

            # Store clickable region for later (we'll handle in events)
            if not hasattr(self, 'inventory_use_regions'):
                self.inventory_use_regions = []
            self.inventory_use_regions.append( ( (btn_x, btn_y, btn_w, btn_h), pot['key'] ) )

            draw_button(
                self.screen,
                (btn_x, btn_y, btn_w, btn_h),
                "Использовать",
                self.font,
                base_c,
                hover_c,
                (230, 255, 240) if can_use else (140, 140, 145),
                False
            )

        # Close hint
        hint = self.font.render("Кликни ещё раз по 'Инвентарь' или вне окна, чтобы закрыть", True, pal.text_dim)
        self.screen.blit(hint, (panel_x + 25, panel_y + panel_h - 28))

    def draw(self):
        self.upgrade_click_regions = []
        self.inventory_use_regions = []
        self.vertical_action_rects = []
        self.hovered_business = None

        pal = self.palette
        state = self.game.state

        # === Empire Sickness Level (for global interface corruption) ===
        total_neg = sum(len([e for e in b.effects if e.strength < 0]) for b in state.businesses.values())
        rat_sickness = max(0, (state.ratysurd_level - 10) / 5.0)
        self.empire_sickness = min(1.0, rat_sickness + (total_neg / 25.0))

        # ==================== DEBUG SECTION ====================
        # (debug_force_visible still controls forced bright colors for visibility testing)

        # Always apply a strong visibility floor so the game is never pitch black.
        # This is the main fix for the "black screen" issue.
        def _vis(c, floor=32):
            return tuple(max(floor, v) for v in c)

        bg = _vis(pal.bg, 32)
        panel_bg = _vis(pal.panel_bg, 28)
        panel_border = _vis(pal.panel_border, 55)
        slot_reel_bg = _vis(pal.slot_reel_bg, 30)

        # When debug is on, force an even brighter, high-contrast slate for development
        if self.debug_force_visible:
            bg = (38, 42, 52)
            panel_bg = (34, 38, 48)
            panel_border = (85, 95, 115)
            slot_reel_bg = (36, 40, 50)

        self.screen.fill(bg)

        # === TOP BAR ===
        self.draw_top_bar()

        # === BUSINESSES (left side) ===
        self.draw_businesses_panel(50, 95)

        # === ACTION BUTTONS (vertical column under Slot Machine) ===
        self._draw_vertical_action_buttons(830, 545)

        # === SLOT (big static block on the right) ===
        self.draw_slot_placeholder(810, 95)  # Balanced position for better visual rhythm

        # Subtle vertical divider (safe micro corruption)
        divider_x = 785
        if not self.debug_force_visible and state.ratysurd_level >= CORRUPTION_START:
            divider_color = (75, 25, 28) if state.ratysurd_level >= 14 else (55, 35, 45)
        else:
            divider_color = (40, 50, 60)
        pygame.draw.line(self.screen, divider_color, (divider_x, 100), (divider_x, 615), 1)

        # === BOTTOM INFO ===
        self.draw_bottom_info()

        # === UPGRADES PANEL ===
        if self.showing_upgrades:
            self._draw_upgrades_panel()

        # === INVENTORY PANEL (potions) ===
        if self.showing_inventory:
            self._draw_inventory_panel()

        # === SHOP PANEL ===

        if self.showing_shop:
            shop_w = 520
            shop_h = 420
            shop_x = (WIDTH - shop_w) // 2
            shop_y = (HEIGHT - shop_h) // 2 - 20

            # Background
            shop_bg = (30, 34, 44) if self.debug_force_visible else (26, 30, 40)
            pygame.draw.rect(self.screen, shop_bg, (shop_x, shop_y, shop_w, shop_h), border_radius=8)
            pygame.draw.rect(self.screen, (70, 90, 120), (shop_x, shop_y, shop_w, shop_h), 2, border_radius=8)

            # Title
            title = self.font_big.render("МАГАЗИН — Покупка бизнеса", True, pal.text)
            self.screen.blit(title, (shop_x + 20, shop_y + 15))

            # Current money
            money = self.font.render(f"У вас: {format_number(state.bizneta)} Бизнет", True, pal.bizneta)
            self.screen.blit(money, (shop_x + 20, shop_y + 50))

            # Next cost
            cost = self.game.get_next_business_cost()
            cost_text = self.font.render(f"Стоимость следующего: {format_number(cost)} Бизнет", True, pal.text_dim)
            self.screen.blit(cost_text, (shop_x + 20, shop_y + 72))

            # List of businesses
            options = self.game.get_shop_options()
            start_y = shop_y + 105
            for i, opt in enumerate(options[:7]):
                y_pos = start_y + i * 42
                can_afford = state.bizneta >= opt["cost"]

                # Row background
                row_color = (25, 30, 40) if can_afford else (20, 20, 22)
                pygame.draw.rect(self.screen, row_color, (shop_x + 15, y_pos, shop_w - 30, 38), border_radius=4)

                text = f"{opt['name']} (Tier {opt['tier']})  —  {format_number(opt['cost'])} Б"
                color = pal.text if can_afford else (100, 100, 100)
                self.screen.blit(self.font.render(text, True, color), (shop_x + 25, y_pos + 9))

            # Close hint
            close_hint = self.font.render("Кликни ещё раз по 'Магазин' чтобы закрыть", True, pal.text_dim)
            self.screen.blit(close_hint, (shop_x + 20, shop_y + shop_h - 30))

        # === TOASTS (notifications) ===
        self._draw_toasts()

        # === ONBOARDING (first time help) ===
        if self.showing_onboarding:
            self._draw_onboarding_panel()

        # === RESET CONFIRMATION MODAL (must be drawn last so it's on top) ===
        if self.showing_reset_confirm:
            self._draw_reset_confirm_modal()

        # === CHAOTIC SPIN FULL-WINDOW GLITCH ===
        if self.chaotic_glitch_until > pygame.time.get_ticks():
            self._draw_chaotic_glitch_overlay()

        # === Global Interface Sickness Overlay (high Ratysurd + high empire corruption) ===
        if not self.debug_force_visible and self.empire_sickness > 0.4:
            sickness_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            alpha = int(12 * self.empire_sickness)
            sickness_overlay.fill((110, 15, 20, alpha))
            self.screen.blit(sickness_overlay, (0, 0))

        # === pygame_gui (drawn on top of custom UI) ===
        if self.ui_manager:
            self.ui_manager.draw_ui(self.screen)

        # Present the frame
        pygame.display.flip()

    def _draw_business_tooltip(self, business_id: str, mouse_pos):
        """Draw detailed hover info for a business."""
        pal = self.palette
        state = self.game.state
        business = state.businesses[business_id]

        # Calculate useful values
        effective_gain = self.game.effect_system.get_effective_client_gain_per_minute(business)
        income_per_min = business.clients * business.bizneta_per_client_per_minute

        # Upgrade multipliers
        growth_mult = business.get_client_gain_multiplier_from_upgrades()
        eff_mult = business.get_bizneta_per_client_multiplier_from_upgrades()
        res_mult = business.get_resilience_multiplier()

        # Tooltip size and position (try to show to the right, fall back left)
        tooltip_w = 340
        tooltip_h = 180
        tx = mouse_pos[0] + 15
        ty = mouse_pos[1] - 10

        if tx + tooltip_w > WIDTH - 20:
            tx = mouse_pos[0] - tooltip_w - 15

        # Background
        bg = (20, 18, 26) if state.ratysurd_level < 12 else (24, 14, 18)
        pygame.draw.rect(self.screen, bg, (tx, ty, tooltip_w, tooltip_h), border_radius=6)
        border = (70, 50, 90) if state.ratysurd_level < 12 else (110, 40, 55)
        pygame.draw.rect(self.screen, border, (tx, ty, tooltip_w, tooltip_h), 2, border_radius=6)

        current_y = ty + 10

        # Header (humanized)
        display_name = humanize_niche_id(business_id)
        header = self.font_big.render(display_name, True, pal.text)
        self.screen.blit(header, (tx + 12, current_y))
        current_y += 28

        # Income
        income_text = self.font.render(f"Текущий доход: {format_number(income_per_min)} Б/мин", True, pal.bizneta)
        self.screen.blit(income_text, (tx + 12, current_y))
        current_y += 22

        # Client gain
        gain_text = self.font.render(f"Набор клиентов: {effective_gain:.1f}/мин", True, pal.text)
        self.screen.blit(gain_text, (tx + 12, current_y))
        current_y += 24

        # Upgrades breakdown
        self.screen.blit(self.font.render("Улучшения:", True, pal.text), (tx + 12, current_y))
        current_y += 18

        up_text = self.font.render(f"  Growth: +{int((growth_mult-1)*100)}% клиентов", True, pal.text_dim)
        self.screen.blit(up_text, (tx + 16, current_y))
        current_y += 16

        up_text = self.font.render(f"  Efficiency: +{int((eff_mult-1)*100)}% дохода", True, pal.text_dim)
        self.screen.blit(up_text, (tx + 16, current_y))
        current_y += 16

        up_text = self.font.render(f"  Resilience: -{int((1-res_mult)*100)}% от дебаффов", True, pal.text_dim)
        self.screen.blit(up_text, (tx + 16, current_y))
        current_y += 20

        # Active effects
        if business.effects:
            self.screen.blit(self.font.render("Активные эффекты:", True, pal.accent_danger), (tx + 12, current_y))
            current_y += 18

            for eff in business.effects[:4]:  # limit
                strength = int(eff.strength * 100)
                if eff.is_permanent:
                    time_str = "постоянно"
                elif eff.expires_at:
                    remaining = max(0, (eff.expires_at - datetime.now(timezone.utc)).total_seconds() / 60)
                    time_str = f"{remaining:.0f} мин"
                else:
                    time_str = ""

                eff_str = f"  {strength:+d}% клиентов  {time_str}"
                self.screen.blit(self.font.render(eff_str, True, (200, 80, 80)), (tx + 16, current_y))
                current_y += 15

    def _draw_upgrades_panel(self):
        """Proper upgrades panel with clickable rows."""
        pal = self.palette
        state = self.game.state

        panel_w = 620
        panel_h = 520
        panel_x = (WIDTH - panel_w) // 2
        panel_y = (HEIGHT - panel_h) // 2 - 40

        # Background with corruption tint at high chaos (but always visible)
        if self.debug_force_visible:
            bg_color = (32, 36, 46)
            border_color = (85, 70, 110)
        else:
            bg_color = (26, 24, 34) if state.ratysurd_level < 12 else (28, 20, 26)
            border_color = (75, 60, 95) if state.ratysurd_level < 12 else (95, 45, 55)

        pygame.draw.rect(self.screen, bg_color, (panel_x, panel_y, panel_w, panel_h), border_radius=8)
        pygame.draw.rect(self.screen, border_color, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=8)

        # Title + current money
        title = self.font_big.render("УЛУЧШЕНИЯ БИЗНЕСОВ", True, pal.text)
        self.screen.blit(title, (panel_x + 20, panel_y + 15))

        money_text = self.font.render(f"Бизнет: {format_number(state.bizneta)}", True, pal.bizneta)
        money_rect = money_text.get_rect()
        money_x = panel_x + panel_w - 25 - money_rect.width   # right-aligned with padding
        self.screen.blit(money_text, (money_x, panel_y + 18))

        if not state.businesses:
            msg = self.font.render("Сначала купи бизнесы в магазине.", True, pal.text_dim)
            self.screen.blit(msg, (panel_x + 20, panel_y + 55))
            return

        # Store clickable regions for this frame
        self.upgrade_click_regions = []   # list of (rect, business_id, upgrade_type)

        current_y = panel_y + 55

        for niche_id, business in list(state.businesses.items())[:5]:   # limit for space
            upgrades = self.game.get_business_upgrades(niche_id)
            if not upgrades:
                continue

            # Business header
            header_color = pal.text
            if state.ratysurd_level >= 13:
                header_color = (220, 180, 180)
            full_name = humanize_niche_id(niche_id)
            display_name = truncate_name(full_name, max_chars=22)
            header = self.font.render(display_name, True, header_color)
            self.screen.blit(header, (panel_x + 20, current_y))
            current_y += 26

            for up_type in ["growth", "efficiency", "resilience"]:
                data = upgrades[up_type]
                level = data["level"]
                cost = data["next_cost"]
                can_afford = state.bizneta >= cost

                row_h = 23
                row_rect = (panel_x + 20, current_y, panel_w - 40, row_h)

                # Row background
                if can_afford:
                    row_bg = (35, 45, 35) if state.ratysurd_level < 12 else (45, 25, 25)
                else:
                    row_bg = (25, 28, 32) if state.ratysurd_level < 12 else (30, 20, 22)

                pygame.draw.rect(self.screen, row_bg, row_rect, border_radius=3)

                border = (70, 125, 80) if can_afford else (60, 60, 60)
                if state.ratysurd_level >= 13 and not can_afford:
                    border = (55, 25, 25)
                pygame.draw.rect(self.screen, border, row_rect, 1, border_radius=3)

                # Small arrow to indicate it's clickable
                arrow = "→ " if can_afford else "  "
                text_color = pal.text if can_afford else (115, 115, 115)
                if state.ratysurd_level >= 13 and not can_afford:
                    text_color = (100, 70, 70)

                row_text = f"{arrow}{up_type:12}  Lv.{level:2}   →   {format_number(cost):>7} Б"
                self.screen.blit(self.font.render(row_text, True, text_color), (panel_x + 26, current_y + 3))

                self.upgrade_click_regions.append((row_rect, niche_id, up_type))

                current_y += row_h + 2

            current_y += 10  # space between businesses

        # Close hint
        hint_color = pal.text_dim
        if state.ratysurd_level >= 13:
            hint_color = (140, 100, 100)
        hint = self.font.render("Кликни 'Улучшения' ещё раз, чтобы закрыть", True, hint_color)
        self.screen.blit(hint, (panel_x + 20, panel_y + panel_h - 28))

    def draw_top_bar(self):
        state = self.game.state
        pal = self.palette

        # Background strip - more corrupted at high chaos, but never fully black
        top_bg = pal.panel_bg
        if state.ratysurd_level >= 13:
            top_bg = (max(12, top_bg[0]-8), max(8, top_bg[1]-6), max(8, top_bg[2]-6))

        # Extra sickness tint on top bar when empire is heavily corrupted
        if not self.debug_force_visible and self.empire_sickness > 0.5:
            top_bg = (
                min(255, top_bg[0] + int(20 * self.empire_sickness)),
                max(5, int(top_bg[1] - 10 * self.empire_sickness)),
                max(5, int(top_bg[2] - 8 * self.empire_sickness)),
            )

        pygame.draw.rect(self.screen, top_bg, (0, 0, WIDTH, 70))
        border_col = pal.accent_danger if state.ratysurd_level >= CORRUPTION_START else pal.panel_border
        pygame.draw.line(self.screen, border_col, (0, 70), (WIDTH, 70), 2)

        # === Compact Logo (clean or corrupted based on chaos level) ===
        is_corrupted_logo = (state.ratysurd_level >= 12 or self.empire_sickness > 0.45)
        logo_name = "logo_compact_corrupted" if is_corrupted_logo else "logo_compact_clean"
        logo = get_ui_icon(logo_name)

        logo_height = 54
        logo_x = 28
        logo_y = 8

        if logo:
            # Scale to nice height while preserving aspect
            scale_ratio = logo_height / logo.get_height()
            logo_w = int(logo.get_width() * scale_ratio)
            if logo_w > 340:  # safety cap so it doesn't overlap resources
                logo_w = 340
                logo_height = int(logo.get_height() * (logo_w / logo.get_width()))

            scaled_logo = pygame.transform.smoothscale(logo, (logo_w, logo_height))

            if is_corrupted_logo and not self.debug_force_visible:
                # Apply subtle glitch / breathing on corrupted logo
                t = pygame.time.get_ticks()
                jitter_x = math.sin(t / 70) * 1.3
                jitter_y = math.sin(t / 95) * 0.6
                alpha = int(225 + math.sin(t / 280) * 30)

                glitch_logo = scaled_logo.copy()
                glitch_logo.set_alpha(alpha)

                self.screen.blit(glitch_logo, (logo_x + jitter_x, logo_y + jitter_y))

                # Extra red corruption overlay at very high levels
                if state.ratysurd_level >= 14 or self.empire_sickness > 0.7:
                    red_overlay = pygame.Surface((logo_w, logo_height), pygame.SRCALPHA)
                    red_overlay.fill((160, 25, 35, 38))
                    self.screen.blit(red_overlay, (logo_x + jitter_x, logo_y + jitter_y))
            else:
                self.screen.blit(scaled_logo, (logo_x, logo_y))
        else:
            # Fallback to text if logo files are missing
            title = self.font_title.render("ХАОС & ПРИБЫЛЬ", True, pal.text)
            self.screen.blit(title, (40, 18))

        # === Resources with icons ===
        y = 20
        icon_size = 24
        start_x = 390   # pushed right to give room for compact logo
        col_width = 185

        # Kloneta
        klon_icon = get_ui_icon("kloneta", icon_size)
        if klon_icon:
            self.screen.blit(klon_icon, (start_x, y + 2))
        klon_text = self.font.render(f"Клонета: {state.kloneta}/5", True, pal.kloneta)
        self.screen.blit(klon_text, (start_x + icon_size + 6, y))

        # Bizneta
        biz_x = start_x + col_width
        biz_icon = get_ui_icon("bizneta", icon_size)
        if biz_icon:
            self.screen.blit(biz_icon, (biz_x, y + 2))
        biz_text = self.font.render(f"Бизнета: {format_number(state.bizneta)}", True, pal.bizneta)
        self.screen.blit(biz_text, (biz_x + icon_size + 6, y))

        # Ratysurd + pressure - more menacing at high chaos
        rat_x = biz_x + col_width
        pressure = self.game.get_effective_chaos_pressure()
        rat_color = pal.accent_danger if state.ratysurd_level >= 10 else pal.text
        if state.ratysurd_level >= 14:
            rat_color = (225, 45, 45)

        rat_icon = get_ui_icon("ratysurd", icon_size)
        if rat_icon:
            # Apply light red tint on high sickness / high ratysurd
            draw_rat = rat_icon
            if not self.debug_force_visible and (state.ratysurd_level >= 13 or self.empire_sickness > 0.4):
                draw_rat = rat_icon.copy()
                tint = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                alpha = 45 if state.ratysurd_level >= 14 else 30
                tint.fill((200, 40, 50, alpha))
                draw_rat.blit(tint, (0, 0))
            self.screen.blit(draw_rat, (rat_x, y + 2))

        rat_label = self.font.render(f"Рейтисурд: {state.ratysurd_level} (x{pressure:.2f})", True, rat_color)

        # Micro breathing + jitter on Ratysurd (SAFE)
        if not self.debug_force_visible and state.ratysurd_level >= GLITCH_TITLES_FROM:
            t = pygame.time.get_ticks()
            breath = (math.sin(t / 320) + 1) / 2
            jitter = math.sin(t / 85) * 0.8
            alpha = int(200 + breath * 55)
            rat_label.set_alpha(alpha)
            self.screen.blit(rat_label, (rat_x + icon_size + 6 + jitter, y))
        else:
            self.screen.blit(rat_label, (rat_x + icon_size + 6, y))

        # Extra sickly jitter on very high empire sickness
        if not self.debug_force_visible and self.empire_sickness > 0.6:
            t = pygame.time.get_ticks()
            extra_jitter = math.sin(t / 40) * 1.2
            sick_rat = self.font.render(
                f"Рейтисурд: {state.ratysurd_level} (x{pressure:.2f})",
                True, (230, 60, 70)
            )
            sick_rat.set_alpha(int(180 + math.sin(t / 180) * 40))
            self.screen.blit(sick_rat, (rat_x + icon_size + 6 + extra_jitter, y))

    def draw_businesses_panel(self, x: int, y: int):
        pal = self.palette
        state = self.game.state

        panel_width = 740
        # Dynamic height based on content (less wasted space)
        num_businesses = len(state.businesses)
        card_height = 52
        header_height = 42
        bottom_padding = 38
        content_height = max(80, num_businesses * (card_height + 3) + 10)
        panel_height = header_height + content_height + bottom_padding

        # Panel
        if self.debug_force_visible:
            use_panel_bg = (28, 30, 38)
            use_border = (70, 80, 100)
        else:
            use_panel_bg = pal.panel_bg
            use_border = pal.accent_danger if state.ratysurd_level >= 12 else pal.panel_border

        pygame.draw.rect(self.screen, use_panel_bg, (x, y, panel_width, panel_height))
        pygame.draw.rect(self.screen, use_border, (x, y, panel_width, panel_height), 2)

        # Subtle high-chaos accent border only (safe micro effect)
        if not self.debug_force_visible and state.ratysurd_level >= CORRUPTION_START:
            accent = (75, 40, 45) if state.ratysurd_level >= GLITCH_TITLES_FROM else (65, 55, 70)
            pygame.draw.rect(self.screen, accent, (x+2, y+2, panel_width-4, panel_height-4), 1)

        # Stronger world corruption on the businesses panel at very high Ratysurd
        if not self.debug_force_visible and state.ratysurd_level >= 14:
            # Count overall corruption in the player's empire
            total_neg = sum(len([e for e in b.effects if e.strength < 0]) for b in state.businesses.values())
            if total_neg >= 8:  # Player's empire is heavily corrupted
                corruption_border = (100, 20, 25)
                pygame.draw.rect(self.screen, corruption_border, (x+1, y+1, panel_width-2, panel_height-2), 2)

        # Header
        pygame.draw.rect(self.screen, (pal.panel_bg[0]+8, pal.panel_bg[1]+8, pal.panel_bg[2]+10), (x+2, y+2, panel_width-4, 36))
        title = self.font_big.render("БИЗНЕСЫ", True, pal.text)

        # Micro-animation: light glitch + breathing on title (SAFE)
        if not self.debug_force_visible and state.ratysurd_level >= GLITCH_TITLES_FROM:
            t = pygame.time.get_ticks()
            jitter_x = math.sin(t / 70) * 0.9
            jitter_y = math.sin(t / 95) * 0.6
            glitch_alpha = int(140 + math.sin(t / 280) * 55)   # toned down

            glitch_title = self.font_big.render("БИЗНЕСЫ", True, (160, 45, 50))
            glitch_title.set_alpha(glitch_alpha)
            self.screen.blit(glitch_title, (x + 18 + jitter_x, y + 8 + jitter_y))

        self.screen.blit(title, (x + 18, y + 8))

        if not state.businesses:
            no_biz = self.font.render("Пока нет бизнесов. Крути слот или покупай в магазине.", True, pal.text_dim)
            self.screen.blit(no_biz, (x + 18, y + 55))
            return

        mouse_pos = pygame.mouse.get_pos()
        self.hovered_business = None
        total_income = 0.0
        current_y = y + 48

        for niche_id, biz in list(state.businesses.items())[:8]:
            effective_gain = self.game.effect_system.get_effective_client_gain_per_minute(biz)
            income_per_min = biz.clients * biz.bizneta_per_client_per_minute
            total_income += income_per_min

            card_rect = (x+6, current_y, panel_width-12, card_height-2)

            # Hover detection
            if card_rect[0] < mouse_pos[0] < card_rect[0] + card_rect[2] and card_rect[1] < mouse_pos[1] < card_rect[1] + card_rect[3]:
                self.hovered_business = niche_id

            # Card background — scales with corruption level
            neg_effects = len([e for e in biz.effects if e.strength < 0])
            corruption = min(neg_effects, 6) / 6.0   # 0.0 to 1.0

            base_r = min(255, pal.panel_bg[0] + 8)
            base_g = min(255, pal.panel_bg[1] + 8)
            base_b = min(255, pal.panel_bg[2] + 10)

            # More negative effects = more red/sick tint
            card_bg = (
                int(base_r + corruption * 35),
                int(max(15, base_g - corruption * 25)),
                int(max(15, base_b - corruption * 20)),
            )

            pygame.draw.rect(self.screen, card_bg, card_rect)

            # Name (humanized + truncated for card)
            full_name = humanize_niche_id(niche_id)
            display_name = truncate_name(full_name)
            name_color = pal.text if effective_gain > 0 else pal.accent_danger
            name_text = self.font.render(display_name, True, name_color)
            self.screen.blit(name_text, (x + 14, current_y + 6))

            # Effects display — clearer at high corruption
            if biz.effects:
                neg = len([e for e in biz.effects if e.strength < 0])
                if neg > 0:
                    if neg >= 4:
                        eff_text = f"СИЛЬНАЯ ПОРЧА ({neg})"
                        eff_color = (255, 80, 80)
                    elif neg >= 2:
                        eff_text = f"Порча: {neg}"
                        eff_color = (245, 90, 90)
                    else:
                        eff_text = "Лёгкая порча"
                        eff_color = (220, 110, 110) if state.ratysurd_level >= 12 else pal.accent_danger

                    self.screen.blit(self.font.render(eff_text, True, eff_color), (x + 14, current_y + 27))

                    # Extra visual corruption on heavily debuffed cards
                    if neg >= 3:
                        border_strength = min(neg, 6)
                        border_color = (110 + border_strength*8, 15, 15)
                        pygame.draw.rect(self.screen, border_color, card_rect, 1 + (neg // 3))

                        # Small "cracks" on very corrupted businesses (high Ratysurd)
                        if neg >= 4 and state.ratysurd_level >= 13:
                            crack_col = (130, 25, 25)
                            # A couple of thin red lines inside the card
                            pygame.draw.line(self.screen, crack_col, (x + 20, current_y + 20), (x + 60, current_y + 35), 1)
                            if neg >= 5:
                                pygame.draw.line(self.screen, crack_col, (x + card_rect[2] - 50, current_y + 18), (x + card_rect[2] - 15, current_y + 40), 1)

            # Clients bar — more broken looking when heavily debuffed
            clients = biz.clients
            bar_w = 235
            bar_h = 10
            bar_x = x + 175
            bar_y = current_y + 25

            bar_bg = pal.slot_reel_bg
            if neg_effects >= 3:
                # Heavily corrupted businesses have "damaged" client bars
                bar_bg = (55, 20, 22) if state.ratysurd_level >= 13 else (45, 22, 24)

            pygame.draw.rect(self.screen, bar_bg, (bar_x, bar_y, bar_w, bar_h))

            fill = min(bar_w, int((clients / 800000.0) * bar_w)) if clients > 0 else 0
            fill_col = pal.accent if effective_gain > 0 else pal.accent_danger
            pygame.draw.rect(self.screen, fill_col, (bar_x, bar_y, max(2, fill), bar_h))

            info = self.font.render(
                f"{format_number(clients)} кл  •  {format_number(income_per_min)} Б/мин",
                True, pal.text_dim
            )
            self.screen.blit(info, (x + 430, current_y + 8))

            # Show current upgrade levels (very useful info)
            up = biz.upgrades
            if up:
                g = up.get("growth", 0)
                e = up.get("efficiency", 0)
                r = up.get("resilience", 0)
                up_str = f"G{g} E{e} R{r}"
                up_color = (170, 150, 210) if state.ratysurd_level < 12 else (200, 130, 200)
                up_text = self.font.render(up_str, True, up_color)
                self.screen.blit(up_text, (x + 620, current_y + 8))

            current_y += card_height + 2

        # Summary at bottom of panel
        summary_y = y + panel_height - 28
        summary = self.font.render(f"Общий доход: ~{format_number(total_income)} Бизнет/мин", True, pal.bizneta)
        self.screen.blit(summary, (x + 14, summary_y))

        # === HOVER TOOLTIP ===
        if self.hovered_business and self.hovered_business in state.businesses:
            self._draw_business_tooltip(self.hovered_business, mouse_pos)

    def draw_slot_placeholder(self, x: int, y: int):
        """Improved static slot for Variant A. Shows last result reels when available."""
        pal = self.palette
        state = self.game.state

        width = 500
        height = 440

        # Main panel — stronger presence
        if self.debug_force_visible:
            use_panel_bg = (28, 30, 38)
            use_border = (70, 80, 100)
        else:
            use_panel_bg = pal.panel_bg
            use_border = pal.accent_danger if state.ratysurd_level >= 10 else pal.panel_border

        pygame.draw.rect(self.screen, use_panel_bg, (x, y, width, height))
        border_width = 4 if state.ratysurd_level >= 12 else 3 if state.ratysurd_level >= 8 else 2
        pygame.draw.rect(self.screen, use_border, (x, y, width, height), border_width)

        # Very subtle high-chaos accent border only (safe micro)
        if not self.debug_force_visible and state.ratysurd_level >= CORRUPTION_START:
            accent = (65, 28, 32) if state.ratysurd_level >= GLITCH_TITLES_FROM else (55, 45, 55)
            pygame.draw.rect(self.screen, accent, (x+3, y+3, width-6, height-6), 1)

        # Persistent world corruption on the slot itself at very high Ratysurd
        if not self.debug_force_visible and state.ratysurd_level >= 14:
            total_neg = sum(len([e for e in b.effects if e.strength < 0]) for b in state.businesses.values())
            if total_neg >= 8:
                # The slot feels "sick" when the player's empire is heavily corrupted
                sick_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
                sick_overlay.fill((80, 15, 18, 22))
                self.screen.blit(sick_overlay, (x, y))
                pygame.draw.rect(self.screen, (90, 20, 25), (x+2, y+2, width-4, height-4), 1)

        # === SAFE SPARSE CRACKS (only on slot, only at extreme levels) ===
        # Max 2 thin lines, low alpha, only on the "most corrupted" object in the game.
        if (not self.debug_force_visible and
                state.ratysurd_level >= SPARSE_CRACKS_FROM):
            crack_surf = pygame.Surface((width, height), pygame.SRCALPHA)
            crack_col = (120, 35, 40, CRACK_INTENSITY)

            # Just two very sparse, hesitant cracks
            # (never dense patterns, never on businesses panel)
            for i in range(min(MAX_SPARSE_CRACKS, state.ratysurd_level - 12)):
                y1 = 55 + i * 95
                # Main thin crack
                pygame.draw.line(crack_surf, crack_col,
                                 (12, y1), (width - 18, y1 + 22 + i * 4), 1)
                # Tiny secondary branch (very faint feeling)
                pygame.draw.line(crack_surf, (110, 30, 35, CRACK_INTENSITY - 25),
                                 (width - 55, y1 + 18), (width - 14, y1 - 12), 1)

            self.screen.blit(crack_surf, (x, y))

        # === CHAOS SPIN VISUAL INSTABILITY ===
        if self.is_spinning and state.ratysurd_level >= 13:
            # Subtle red "fever" overlay on the whole slot during chaotic spins
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            alpha = 25 + (state.ratysurd_level - 13) * 8
            if state.ratysurd_level >= 14:
                alpha += 15
            overlay.fill((120, 20, 25, min(70, alpha)))
            self.screen.blit(overlay, (x, y))

        # Header
        header_tint = (pal.panel_bg[0]+12, pal.panel_bg[1]+6, pal.panel_bg[2]+8) if state.ratysurd_level >= 10 else (pal.panel_bg[0]+10, pal.panel_bg[1]+8, pal.panel_bg[2]+12)
        pygame.draw.rect(self.screen, header_tint, (x+3, y+3, width-6, 36))
        title = self.font_big.render("СЛОТ-МАШИНА", True, pal.text)

        # Micro-animation: light glitch + breathing on title (SAFE)
        if not self.debug_force_visible and state.ratysurd_level >= GLITCH_TITLES_FROM:
            t = pygame.time.get_ticks()
            jitter_x = math.sin(t / 65) * 1.1
            jitter_y = math.sin(t / 88) * 0.7
            glitch_alpha = int(135 + math.sin(t / 310) * 50)

            glitch_title = self.font_big.render("СЛОТ-МАШИНА", True, (165, 50, 55))
            glitch_title.set_alpha(glitch_alpha)
            self.screen.blit(glitch_title, (x + 18 + jitter_x, y + 8 + jitter_y))

        self.screen.blit(title, (x + 18, y + 8))

        # === THREE REELS ===
        reel_width = 130
        reel_height = 165          # slightly tighter
        reel_y = y + 52
        reel_spacing = 20
        start_x = x + 40

        reels_to_show = ["???", "???", "???"]

        # === SPINNING ANIMATION LOGIC (improved base feel) ===
        if self.is_spinning:
            current_time = pygame.time.get_ticks() / 1000.0 - self.spin_start_time

            # === CHAOS-CORRUPTED SPIN POOL ===
            base_pool = ["💰", "👥", "🧪", "🍞", "📜", "❓", "🌀"]

            chaos_level = max(0, state.ratysurd_level - 10)  # 0 at 10, ramps up

            spin_pool = base_pool.copy()

            # Inject corrupted symbols as Ratysurd grows
            if chaos_level >= 2:  # 12+
                spin_pool += ["💀", "☠️", "🩸"] * 2
            if chaos_level >= 3:  # 13+
                spin_pool += ["🌪️", "❗", "🌀"] * 2
            if chaos_level >= 4:  # 14+
                spin_pool += ["💀", "☠️", "🕳️", "🔥"] * 3

            for i in range(3):
                stop_time = self.reel_stop_times[i]

                if current_time < stop_time:
                    # Reel is still spinning — calculate smooth scrolling offset
                    time_left = stop_time - current_time
                    spin_duration = stop_time  # total time this reel has been spinning

                    # Ease the speed: fast at start, strong slowdown near the end
                    if time_left > 0.35:
                        speed = 26.0  # very fast
                    else:
                        # Smooth deceleration in the last 350ms
                        t = time_left / 0.35
                        speed = 4.0 + (22.0 * (t ** 2))  # quadratic ease-out

                    # Different phase per reel so they don't look synchronized
                    phase = i * 2.3
                    scroll_pos = (current_time * speed + phase) % len(spin_pool)

                    # Pick the symbol that should be in the center right now
                    center_idx = int(scroll_pos) % len(spin_pool)
                    reels_to_show[i] = spin_pool[center_idx]
                else:
                    # Reel has stopped — show final symbol
                    if self.spin_result:
                        final_reels = [
                            self.spin_result.reel1,
                            self.spin_result.reel2,
                            self.spin_result.reel3,
                        ]
                        def clean_reel(text: str) -> str:
                            parts = text.split(" ", 1)
                            return parts[1][:16] if len(parts) > 1 else text[:16]
                        reels_to_show[i] = clean_reel(final_reels[i])
        else:
            # Normal static display (after spin or when idle)
            if self.last_spin_result:
                def clean_reel(text: str) -> str:
                    parts = text.split(" ", 1)
                    if len(parts) > 1:
                        return parts[1][:16]
                    return text[:16]

                reels_to_show = [
                    clean_reel(self.last_spin_result.reel1),
                    clean_reel(self.last_spin_result.reel2),
                    clean_reel(self.last_spin_result.reel3),
                ]

        is_chaotic = (self.last_spin_result or self.spin_result) and (
            "CHAOTIC" in (self.last_spin_result or self.spin_result).message or
            "cursed" in getattr((self.last_spin_result or self.spin_result), 'message', '').lower()
        )

        # Per-reel render data (used for nice scrolling effect)
        reel_render_data = []
        for i in range(3):
            data = {
                "symbol": reels_to_show[i],
                "y_offset": 0.0,
                "is_spinning": False
            }

            if self.is_spinning:
                stop_time = self.reel_stop_times[i]
                current_time = pygame.time.get_ticks() / 1000.0 - self.spin_start_time

                if current_time < stop_time:
                    data["is_spinning"] = True
                    time_left = stop_time - current_time

                    # Calculate smooth vertical scroll offset (0.0 to 1.0)
                    if time_left > 0.35:
                        speed = 26.0
                    else:
                        t = time_left / 0.35
                        speed = 4.0 + (22.0 * (t ** 2))

                    phase = i * 2.3
                    scroll_pos = (current_time * speed + phase) % 1.0   # fractional part only
                    y_off = scroll_pos * reel_height

                    # === CHAOS JITTER during spin ===
                    if state.ratysurd_level >= 12:
                        jitter_strength = 0
                        if state.ratysurd_level >= 14:
                            jitter_strength = 6 + (state.ratysurd_level - 14) * 2
                        elif state.ratysurd_level >= 12:
                            jitter_strength = 3

                        if jitter_strength > 0:
                            import random
                            # Small random vertical glitch every frame
                            y_off += random.randint(-jitter_strength, jitter_strength)

                    data["y_offset"] = y_off

            reel_render_data.append(data)

        for i in range(3):
            rx = start_x + i * (reel_width + reel_spacing)
            symbol_text = reels_to_show[i]

            # Determine reel color based on symbol type (even in static version)
            lower = symbol_text.lower()
            reel_str = ""
            if self.last_spin_result:
                reel_str = (self.last_spin_result.reel1 + self.last_spin_result.reel2 + self.last_spin_result.reel3).lower()

            if "bizneta" in lower or "💰" in reel_str:
                reel_color = (45, 38, 20)  # dark gold
                text_col = pal.bizneta
            elif "client" in lower:
                reel_color = (20, 38, 48)
                text_col = pal.kloneta
            elif "potion" in lower or "🧪" in symbol_text:
                reel_color = (22, 42, 35)
                text_col = (90, 210, 140)
            # Wave 2 businesses — distinct "underworld contract" purple-grey
            elif any(x in lower for x in ["bakery", "debts", "echo", "second", "whisper", "razlom", "never", "булочн", "долг", "эхо", "второе", "шёпот", "разлом", "никогда"]):
                reel_color = (38, 28, 48)  # deep bruised purple
                text_col = (200, 170, 220)
            # Rare god-tier — special ethereal
            elif any(x in lower for x in ["cleanse", "suppress", "rare", "permanent"]) or any(x in symbol_text for x in ["✨", "🌪"]):
                reel_color = (32, 35, 52)  # dark void with gold hint
                text_col = (235, 220, 140)
            elif is_chaotic or "cursed" in lower or "twisted" in lower:
                reel_color = (38, 12, 12)
                text_col = pal.accent_danger
            else:
                reel_color = pal.slot_reel_bg
                text_col = pal.text if not is_chaotic else pal.accent_danger

            # Reel background - more corrupted at high chaos but never too dark
            if self.debug_force_visible:
                reel_color = (34, 38, 48)
            elif self.is_spinning and state.ratysurd_level >= 13:
                # During spin on high chaos — reels look unstable/sick
                reel_color = (50, 18, 22) if state.ratysurd_level >= 14 else (38, 20, 24)
            elif state.ratysurd_level >= 13:
                reel_color = tuple(max(22, c - 12) for c in reel_color)

            pygame.draw.rect(self.screen, reel_color, (rx, reel_y, reel_width, reel_height), border_radius=8)
            pygame.draw.rect(self.screen, pal.panel_border, (rx, reel_y, reel_width, reel_height), 2, border_radius=8)

            reel_data = reel_render_data[i]

            if reel_data["is_spinning"]:
                # === NICE PHYSICAL SCROLLING EFFECT + CHAOS DISTORTION ===
                y_off = reel_data["y_offset"]

                # Extra chaos jitter on symbol positions (on top of scroll offset)
                extra_jitter_x = 0
                extra_jitter_y = 0
                if state.ratysurd_level >= 13:
                    import random
                    jitter = 1 + (state.ratysurd_level - 13) * 0.6
                    extra_jitter_x = random.randint(-int(jitter), int(jitter))
                    extra_jitter_y = random.randint(-int(jitter), int(jitter))

                # Use more corrupted pool for visual scrolling on high chaos
                if state.ratysurd_level >= 13:
                    spin_pool = ["💰", "👥", "🧪", "🍞", "💀", "☠️", "🩸", "🌪️", "🌀"]
                else:
                    spin_pool = ["💰", "👥", "🧪", "🍞", "📜", "❓", "🌀"]

                idx = spin_pool.index(symbol_text) if symbol_text in spin_pool else 0

                top_symbol = spin_pool[(idx - 1) % len(spin_pool)]
                bot_symbol = spin_pool[(idx + 1) % len(spin_pool)]

                # Corrupted color tint during spin on high Ratysurd
                draw_col = text_col
                if state.ratysurd_level >= 14:
                    draw_col = (220, 80, 80)  # sickly red

                # Top symbol (coming in)
                top_surf = self.font_reel.render(top_symbol, True, draw_col)
                top_rect = top_surf.get_rect(center=(rx + reel_width // 2 + extra_jitter_x, reel_y + reel_height // 2 - 3 - reel_height + y_off + extra_jitter_y))
                self.screen.blit(top_surf, top_rect)

                # Center symbol
                center_surf = self.font_reel.render(symbol_text, True, draw_col)
                center_rect = center_surf.get_rect(center=(rx + reel_width // 2 + extra_jitter_x, reel_y + reel_height // 2 - 3 + y_off + extra_jitter_y))
                self.screen.blit(center_surf, center_rect)

                # Bottom symbol (leaving)
                bot_surf = self.font_reel.render(bot_symbol, True, draw_col)
                bot_rect = bot_surf.get_rect(center=(rx + reel_width // 2 + extra_jitter_x, reel_y + reel_height // 2 - 3 + reel_height + y_off + extra_jitter_y))
                self.screen.blit(bot_surf, bot_rect)
            else:
                # Normal centered symbol (stopped or idle)
                key, is_corr = _symbol_text_to_key(symbol_text)
                sprite = get_slot_sprite(key, is_corr) if key else None

                if sprite:
                    # Nice big icon inside the reel window (reels are 130x165)
                    target = 106
                    if sprite.get_width() != target or sprite.get_height() != target:
                        spr = pygame.transform.smoothscale(sprite, (target, target))
                    else:
                        spr = sprite

                    # Extra chaos sickness tint on the sprite itself at high Ratysurd
                    if (not self.debug_force_visible and
                            (state.ratysurd_level >= 13 or is_chaotic or is_corr)):
                        spr = spr.copy()
                        tint = pygame.Surface((target, target), pygame.SRCALPHA)
                        if state.ratysurd_level >= 14 or is_corr:
                            tint.fill((170, 35, 45, 42))
                        else:
                            tint.fill((120, 25, 35, 28))
                        spr.blit(tint, (0, 0))

                    icon_rect = spr.get_rect(center=(rx + reel_width // 2, reel_y + reel_height // 2 - 2))
                    self.screen.blit(spr, icon_rect)
                else:
                    # Graceful fallback — original emoji / short text
                    symbol = self.font_reel.render(symbol_text, True, text_col)
                    text_rect = symbol.get_rect(center=(rx + reel_width // 2, reel_y + reel_height // 2 - 3))
                    self.screen.blit(symbol, text_rect)

        # === BIG SPIN BUTTON (much stronger hover + high chaos corruption) ===
        btn_x, btn_y = x + 100, y + 235   # tightened for better rhythm with reels
        btn_w, btn_h = 300, 68

        mouse_pos = pygame.mouse.get_pos()
        hovered = btn_x < mouse_pos[0] < btn_x + btn_w and btn_y < mouse_pos[1] < btn_y + btn_h
        can_spin = state.kloneta > 0

        if self.is_spinning:
            # During spin
            base = (60, 60, 70)
            border = (90, 90, 100)
            txt_c = (180, 180, 190)
            label = "КРУТИТСЯ..."
            can_spin = False  # force disabled look
        elif not can_spin:
            # "Dead" button at high chaos - kept visible on purpose
            if state.ratysurd_level >= EXTREME_FROM:
                base = (38, 18, 18)
                border = (120, 35, 35)
                txt_c = (210, 70, 70)
            elif state.ratysurd_level >= CORRUPTION_START:
                base = (42, 20, 20)
                border = (110, 45, 45)
                txt_c = (195, 80, 80)
            else:
                base = (48, 24, 24)
                border = (95, 50, 50)
                txt_c = pal.text_dim
            label = "СЛОТ ИЗНОШЕН"
        else:
            if hovered:
                base = (70, 220, 240) if state.ratysurd_level < 10 else (240, 80, 90)
            else:
                base = pal.accent if state.ratysurd_level < 10 else (200, 60, 70)
            border = pal.text
            txt_c = pal.text
            label = "КРУТИТЬ (1 Клонета)"

        draw_button(
            self.screen,
            (btn_x, btn_y, btn_w, btn_h),
            label,
            self.font_big,
            base,
            base,
            txt_c,
            hovered,
            border_color=border
        )

        # === FIRST LIGHT MICRO-ANIMATION (пункт 3 start) ===
        # Very subtle pulsing border glow on the spin button when it can be used
        if can_spin and not self.is_spinning:
            pulse = (math.sin(pygame.time.get_ticks() / 280) + 1) / 2   # 0..1 slow pulse
            glow_alpha = int(40 + pulse * 55)
            glow_color = (100, 220, 240) if state.ratysurd_level < 10 else (240, 90, 100)

            glow_surface = pygame.Surface((btn_w + 12, btn_h + 12), pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*glow_color, glow_alpha), (0, 0, btn_w + 12, btn_h + 12), border_radius=10)
            self.screen.blit(glow_surface, (btn_x - 6, btn_y - 6))

        # === LAST RESULT BOX — now much more prominent and atmospheric ===
        result_box_y = y + 310
        result_box_height = 92   # taller for more presence

        if self.last_spin_result:
            is_bad = "CHAOTIC" in self.last_spin_result.message or "cursed" in self.last_spin_result.message.lower() or "twisted" in self.last_spin_result.message.lower()

            # Micro-animation: very subtle tremble on the result box at high chaos or on bad results
            tremble_x = 0
            tremble_y = 0
            if state.ratysurd_level >= 12 or is_bad:
                t = pygame.time.get_ticks()
                tremble_x = math.sin(t / 55) * 0.7
                tremble_y = math.sin(t / 72) * 0.5

            # Background box — much stronger corruption at high chaos
            if is_bad:
                if state.ratysurd_level >= 14:
                    box_color = (48, 22, 22)
                elif state.ratysurd_level >= 12:
                    box_color = (40, 20, 20)
                else:
                    box_color = (32, 18, 18)
            else:
                box_color = (22, 32, 28) if state.ratysurd_level < 12 else (20, 28, 25)

            pygame.draw.rect(self.screen, box_color, (x + 15 + tremble_x, result_box_y + tremble_y, width - 30, result_box_height), border_radius=6)

            border_c = pal.accent_danger if is_bad else (65, 130, 95)
            if state.ratysurd_level >= 13:
                border_c = (190, 45, 45) if is_bad else (75, 155, 105)
            pygame.draw.rect(self.screen, border_c, (x + 15 + tremble_x, result_box_y + tremble_y, width - 30, result_box_height), 2, border_radius=6)

            # Very sparse corruption lines on result box (only on truly bad chaotic outcomes)
            if not self.debug_force_visible and state.ratysurd_level >= EXTREME_FROM and is_bad:
                for i in range(1):  # deliberately only 1 line here
                    ly = result_box_y + 18 + i * 22
                    pygame.draw.line(self.screen, (125, 40, 40), (x + 22, ly + tremble_y), (x + width - 28, ly + 6 + tremble_y), 1)

            # Header for the result
            header_color = (200, 80, 80) if is_bad else (100, 200, 150)
            if state.ratysurd_level >= 13:
                header_color = (240, 70, 70) if is_bad else (80, 210, 140)
            header = self.font.render("ПОСЛЕДНИЙ СПИН", True, header_color)
            self.screen.blit(header, (x + 25 + tremble_x, result_box_y + 6 + tremble_y))

            # Message
            msg_color = (245, 100, 100) if is_bad else (110, 220, 160)
            msg = self.font.render(self.last_spin_result.message[:58], True, msg_color)
            self.screen.blit(msg, (x + 25 + tremble_x, result_box_y + 26 + tremble_y))

            # Symbols row — more prominent
            if self.last_spin_result:
                small_reels = [
                    clean_reel(self.last_spin_result.reel1),
                    clean_reel(self.last_spin_result.reel2),
                    clean_reel(self.last_spin_result.reel3),
                ]
                summary_x = x + 25
                for sr in small_reels:
                    s = self.font.render(sr, True, pal.text)
                    self.screen.blit(s, (summary_x + tremble_x, result_box_y + 52 + tremble_y))
                    summary_x += 155

        else:
            if not can_spin:
                if state.ratysurd_level >= 13:
                    status1 = self.font.render("СЛОТ ИЗНОШЕН", True, (180, 30, 30))
                    status2 = self.font.render("Мир забрал последние искры. Жди... или используй зелье.", True, pal.text_dim)
                    self.screen.blit(status1, (x + 18, result_box_y + 10))
                    self.screen.blit(status2, (x + 18, result_box_y + 38))
                else:
                    status = self.font.render("Нет Клонет. Жди регенерации или используй зелье.", True, pal.accent_danger)
                    self.screen.blit(status, (x + 18, result_box_y + 20))
            else:
                if self.last_spin_result is None:
                    idle = self.font.render("Крути слот, чтобы начать", True, pal.text_dim)
                    self.screen.blit(idle, (x + 18, result_box_y + 25))
                else:
                    status = self.font.render("Крути слот — статичная версия интерфейса", True, pal.text_dim)
                    self.screen.blit(status, (x + 18, result_box_y + 20))

    def draw_bottom_info(self):
        pal = self.palette
        state = self.game.state

        y = HEIGHT - 58
        pygame.draw.rect(self.screen, pal.panel_bg, (0, y, WIDTH, 58))
        pygame.draw.line(self.screen, pal.panel_border, (0, y), (WIDTH, y), 2)

        mouse_pos = pygame.mouse.get_pos()

        # === TIME CONTROLS (left group) ===
        time_x = 36
        pygame.draw.rect(self.screen, (min(255, pal.panel_bg[0]+8), min(255, pal.panel_bg[1]+8), min(255, pal.panel_bg[2]+10)), (time_x-6, y+4, 440, 40), border_radius=6)

        # Speed controls with hover
        speeds = [0, 1, 5, 10]
        speed_labels = ["||", "1×", "5×", "10×"]
        for i, (speed, label) in enumerate(zip(speeds, speed_labels)):
            bx = time_x + i * 52
            is_active = (self.time_speed == speed) or (speed == 0 and self.time_speed == 0)
            hovered_speed = bx < mouse_pos[0] < bx + 48 and y + 8 < mouse_pos[1] < y + 40

            if is_active:
                base_c = (95, 55, 55)
            elif hovered_speed:
                base_c = (70, 70, 85)
            else:
                base_c = (50, 50, 55)

            draw_button(self.screen, (bx, y + 8, 48, 32), label, self.font, base_c, (120, 80, 80) if is_active else (85, 85, 100), pal.text, hovered_speed or is_active)

        # Manual fast forward buttons
        for i, (label, mins) in enumerate([("1 мин", 1), ("5 мин", 5), ("10 мин", 10), ("30 мин", 30)]):
            bx = time_x + 220 + i * 55
            hovered = bx < mouse_pos[0] < bx + 52 and y + 8 < mouse_pos[1] < y + 40
            base_c = (70, 90, 110) if state.ratysurd_level < 10 else (90, 50, 50)
            hover_c = pal.accent if state.ratysurd_level < 10 else (200, 70, 70)
            draw_button(self.screen, (bx, y + 8, 50, 32), label, self.font, base_c, hover_c, pal.text, hovered)

        # === POTIONS (middle group) ===
        pot_x = 510
        pygame.draw.rect(self.screen, (min(255, pal.panel_bg[0]+8), min(255, pal.panel_bg[1]+8), min(255, pal.panel_bg[2]+10)), (pot_x-6, y+4, 395, 40), border_radius=6)

        reg = state.regular_potions.get("10min", 0)
        perm = state.permanent_cleanse_potions
        supp = state.chaos_suppression_potions

        # Potion buttons with hover
        pot_buttons = [
            (pot_x,       100, f"10min ({reg})",     "10min"),
            (pot_x + 108, 135, f"Permanent ({perm})", "permanent"),
            (pot_x + 250, 135, f"Suppression ({supp})", "suppression"),
        ]

        for bx, bw, label, ptype in pot_buttons:
            hovered = bx < mouse_pos[0] < bx + bw and y + 8 < mouse_pos[1] < y + 40
            base_c = (55, 75, 65) if state.ratysurd_level < 10 else (70, 35, 40)
            hover_c = (80, 160, 120) if state.ratysurd_level < 10 else (180, 70, 80)
            draw_button(self.screen, (bx, y + 8, bw, 32), label, self.font, base_c, hover_c, pal.text, hovered)

        # === STATUS (right) — умный и не обрезающийся ===
        time_str = format_play_time(state.total_time_advanced / 60)
        base_info = f"Время: {time_str}  •  Бизнесов: {len(state.businesses)}  •  ESC — выход"

        text = self.font.render(base_info, True, pal.text_dim)

        # Calculate safe right boundary (leave space for speed indicator + margin)
        right_limit = WIDTH - 155

        # If text is too long, switch to compact mode
        if text.get_width() > (right_limit - (pot_x + 300)):
            compact_info = f"{time_str} • {len(state.businesses)} бизн • ESC"
            text = self.font.render(compact_info, True, pal.text_dim)

        # Position so it never overflows the right controls
        status_x = min(pot_x + 400, right_limit - text.get_width() - 8)
        self.screen.blit(text, (status_x, y + 17))







        # Current time speed indicator - prominent
        speed_text = f"{int(self.time_speed)}×" if self.time_speed > 0 else "PAUSED"
        speed_color = (220, 50, 50) if self.time_speed == 0 else (100, 200, 255) if self.time_speed == 1 else (255, 180, 60)
        speed_label = self.font.render(f"⚡ {speed_text}", True, speed_color)
        self.screen.blit(speed_label, (WIDTH - 140, y + 17))

        # === DEALS PANEL (appears when active) ===
        if self.game.deal_system.current_deal:
            self._draw_active_deal_panel(y - 95)


def main():
    app = PygameApp()
    app.run()


    def _draw_business_tooltip(self, business_id: str, mouse_pos):
        """Draw detailed hover info for a business."""
        pal = self.palette
        state = self.game.state
        business = state.businesses[business_id]

        effective_gain = self.game.effect_system.get_effective_client_gain_per_minute(business)
        income_per_min = business.clients * business.bizneta_per_client_per_minute

        growth_mult = business.get_client_gain_multiplier_from_upgrades()
        eff_mult = business.get_bizneta_per_client_multiplier_from_upgrades()
        res_mult = business.get_resilience_multiplier()

        tooltip_w = 340
        tooltip_h = 175
        tx = mouse_pos[0] + 15
        ty = mouse_pos[1] - 10

        if tx + tooltip_w > WIDTH - 20:
            tx = mouse_pos[0] - tooltip_w - 15

        bg = (20, 18, 26) if state.ratysurd_level < 12 else (24, 14, 18)
        pygame.draw.rect(self.screen, bg, (tx, ty, tooltip_w, tooltip_h), border_radius=6)
        border = (70, 50, 90) if state.ratysurd_level < 12 else (110, 40, 55)
        pygame.draw.rect(self.screen, border, (tx, ty, tooltip_w, tooltip_h), 2, border_radius=6)

        current_y = ty + 10

        # Header (humanized)
        display_name = humanize_niche_id(business_id)
        header = self.font_big.render(display_name, True, pal.text)
        self.screen.blit(header, (tx + 12, current_y))
        current_y += 26

        income_text = self.font.render(f"Доход: {format_number(income_per_min)} Б/мин", True, pal.bizneta)
        self.screen.blit(income_text, (tx + 12, current_y))
        current_y += 20

        gain_text = self.font.render(f"Набор: {effective_gain:.1f} кл/мин", True, pal.text)
        self.screen.blit(gain_text, (tx + 12, current_y))
        current_y += 22

        self.screen.blit(self.font.render("Улучшения:", True, pal.text), (tx + 12, current_y))
        current_y += 16

        self.screen.blit(self.font.render(f"  Growth +{int((growth_mult-1)*100)}% клиентов", True, pal.text_dim), (tx + 16, current_y))
        current_y += 15
        self.screen.blit(self.font.render(f"  Efficiency +{int((eff_mult-1)*100)}% дохода", True, pal.text_dim), (tx + 16, current_y))
        current_y += 15
        self.screen.blit(self.font.render(f"  Resilience -{int((1-res_mult)*100)}% дебаффов", True, pal.text_dim), (tx + 16, current_y))
        current_y += 18

        if business.effects:
            self.screen.blit(self.font.render("Эффекты:", True, pal.accent_danger), (tx + 12, current_y))
            current_y += 16
            for eff in business.effects[:3]:
                strength = int(eff.strength * 100)
                if eff.is_permanent:
                    tstr = "пост."
                elif eff.expires_at:
                    rem = max(0, (eff.expires_at - datetime.now(timezone.utc)).total_seconds() / 60)
                    tstr = f"{rem:.0f}м"
                else:
                    tstr = ""
                self.screen.blit(self.font.render(f"  {strength:+d}% {tstr}", True, (200, 80, 80)), (tx + 16, current_y))
                current_y += 14

        if state.ratysurd_level >= 14:
            self.screen.blit(self.font.render("Мир сильно давит...", True, (150, 50, 50)), (tx + 12, ty + tooltip_h - 18))


if __name__ == "__main__":
    main()
