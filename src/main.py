"""
Little Shop of Horrors: The Creepypasta Chronicles
Retro Undertale-style Python RPG

Run:
    pip install pygame
    python src/main.py          (from repo root)
  or
    python main.py              (from src/)

Controls:
    Arrow keys / WASD  – move / navigate menus
    Z / Enter / Space  – confirm
    X / Escape         – back / cancel
"""

import sys, os
# Allow running from repo root or from src/
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import pygame
from constants   import *
from game_state  import GameState
from save_system import delete_save, new_save, save_game
from effects     import CreepyOverlay, apply_scanlines, apply_corruption_tint, ScreenShake
from ui          import init_fonts, font, draw_text, draw_box


# ── Title Screen ──────────────────────────────────────────────────────────────

class TitleScene:
    OPTIONS    = ["New Game", "Continue", "Quit"]
    TAGLINE    = "feed me, seymour."
    SKULL_ART  = [
        "  /|||||\\  ",
        " | o   o | ",
        " |  ---  | ",
        " | ||||| | ",
        "  \\_____/  ",
    ]

    def __init__(self, has_save: bool):
        self._idx        = 0
        self._has_save   = has_save
        self._next       = None
        self._glitch_t   = 0.0
        self._title_wave = 0.0

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_UP, pygame.K_w):
            self._idx = (self._idx - 1) % len(self.OPTIONS)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self._idx = (self._idx + 1) % len(self.OPTIONS)
        elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
            choice = self.OPTIONS[self._idx]
            if choice == "New Game":
                delete_save()
                self._next = "new_game"
            elif choice == "Continue":
                if self._has_save:
                    self._next = "overworld"
                else:
                    self._idx = 0  # no save – ignore
            elif choice == "Quit":
                pygame.quit()
                sys.exit()

    def update(self, dt):
        self._glitch_t   += dt
        self._title_wave += dt * 2

    def draw(self, surf: pygame.Surface):
        surf.fill(BLACK)
        # Scroll wave on title text
        title = GAME_TITLE
        cx = SCREEN_W // 2
        y0 = 18
        draw_text(surf, title, (cx, y0), LEAF_GREEN, size="sm", center=True)

        # Sub-tagline
        import math
        wave = int(math.sin(self._title_wave) * 3)
        draw_text(surf, self.TAGLINE, (cx, y0 + 20 + wave), DARK_GREEN, size="sm", center=True)

        # Skull art
        for i, line in enumerate(self.SKULL_ART):
            draw_text(surf, line, (cx, 58 + i * 14), RED, size="md", center=True)

        # Menu options
        for i, opt in enumerate(self.OPTIONS):
            y = 160 + i * 26
            is_sel = (i == self._idx)
            color  = YELLOW if is_sel else WHITE
            if opt == "Continue" and not self._has_save:
                color = DIM
            if is_sel:
                draw_text(surf, "♥", (cx - 55, y), SOUL_COLOR, size="md")
            draw_text(surf, opt, (cx - 40, y), color, size="md")

        # Footer
        draw_text(surf, "Z/Enter=Select   Arrow Keys=Navigate",
                  (cx, SCREEN_H - 22), DIM, size="sm", center=True)

        apply_scanlines(surf, alpha=20)

    def next_scene(self):
        return self._next


# ── Ending Scene ──────────────────────────────────────────────────────────────

ENDING_TEXT = {
    END_TRUE: [
        "TRUE ENDING",
        "",
        "You held the locket and walked into the light.",
        "Audrey II shrank.  Not defeated – freed.",
        "Seymour didn't come back.",
        "",
        "But the garden grew again.  Small.  Green.  Alive.",
        "",
        "somewhere that's green.",
    ],
    END_DARK: [
        "DARK ENDING",
        "",
        "You fed it everything.",
        "The shop.  The street.  The sky.",
        "",
        "AUDREY II speaks:",
        "\"Finally.  I was so hungry.\"",
        "",
        "The credits roll in a language no one remembers.",
        "",
        "don't you feel good about yourself.",
    ],
    END_NORMAL: [
        "NORMAL ENDING",
        "",
        "You destroyed the plant.",
        "The vines receded.  The town breathed.",
        "",
        "Seymour stood in the empty shop.",
        "He thought of Audrey.",
        "He thought about what he'd become.",
        "",
        "He didn't feel like a hero.",
    ],
    END_GOLDEN: [
        "GOLDEN ENDING",
        "",
        "Eight fragments.  One locket.  One choice.",
        "",
        "You offered the memories back.",
        "Audrey II remembered being a seed.",
        "Being small.  Being afraid.",
        "",
        "\"I just wanted to grow,\" it said.",
        "",
        "You let it.",
        "",
        "The garden is strange now.  But it's yours.",
        "",
        "★  TRUE PACIFIST  ★",
    ],
}


class EndingScene:
    def __init__(self, ending_key: str):
        self._key     = ending_key
        self._lines   = ENDING_TEXT.get(ending_key, ["THE END"])
        self._idx     = 0
        self._timer   = 0.0
        self._done    = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE):
                if self._idx < len(self._lines) - 1:
                    self._idx += 1
                else:
                    self._done = True

    def update(self, dt):
        self._timer += dt

    def draw(self, surf: pygame.Surface):
        surf.fill(BLACK)
        colors = {
            END_TRUE:   CYAN,
            END_DARK:   RED,
            END_NORMAL: GRAY,
            END_GOLDEN: GOLD,
        }
        title_color = colors.get(self._key, WHITE)

        visible = self._lines[:self._idx + 1]
        for i, line in enumerate(visible):
            c = title_color if i == 0 else WHITE
            s = "xl" if i == 0 else "md"
            draw_text(surf, line, (SCREEN_W // 2, 60 + i * 26),
                      c, size=s, center=True)

        if self._idx >= len(self._lines) - 1:
            if int(self._timer * 2) % 2 == 0:
                draw_text(surf, "[ Press Z ]",
                          (SCREEN_W // 2, SCREEN_H - 30), DIM, size="sm", center=True)

        apply_scanlines(surf, alpha=25)

    def is_done(self):
        return self._done


# ── Main Game class ───────────────────────────────────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(GAME_TITLE)

        self.win    = pygame.display.set_mode((SCREEN_W * SCALE, SCREEN_H * SCALE))
        self.surf   = pygame.Surface((SCREEN_W, SCREEN_H))
        self.clock  = pygame.time.Clock()

        init_fonts()

        from save_system import load_game
        saved = load_game()
        self.gs = GameState()

        self.creepy = CreepyOverlay(font("sm"), font("sm"))
        self.shake  = ScreenShake()

        self._scene  = None
        self._battle = None
        self._ending = None

        self._goto_title(has_save=(saved is not None))

    # ── Scene management ──────────────────────────────────────────────────────

    def _goto_title(self, has_save=False):
        self._scene = TitleScene(has_save)

    def _goto_overworld(self):
        from overworld import OverworldScene
        self._scene = OverworldScene(self.gs, self.creepy)

    def _goto_battle(self, enemy):
        from battle import BattleScene
        self._battle = BattleScene(self.gs, enemy)
        self._scene  = self._battle

    def _goto_ending(self):
        """Determine which ending and show it."""
        gs = self.gs
        # Golden: all 8 frags + locket + spared Audrey II
        if gs.has_locket and gs.kills == 0:
            key = END_GOLDEN
        elif gs.kills == 0:
            key = END_TRUE
        elif gs.route == ROUTE_GENOCIDE:
            key = END_DARK
        else:
            key = END_NORMAL
        gs.unlock_ending(key)
        gs.save()
        self._ending = EndingScene(key)
        self._scene  = self._ending

    # ── Main loop ─────────────────────────────────────────────────────────────

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.gs.save()
                    pygame.quit()
                    sys.exit()
                self._scene.handle_event(event)

            # Update
            self._scene.update(dt)
            self.shake.update(dt)

            # Draw
            self._scene.draw(self.surf)

            # Apply shake offset
            ox, oy = self.shake.offset()
            self.win.fill(BLACK)
            scaled = pygame.transform.scale(
                self.surf, (SCREEN_W * SCALE, SCREEN_H * SCALE)
            )
            self.win.blit(scaled, (ox * SCALE, oy * SCALE))
            pygame.display.flip()

            # Scene transitions
            self._handle_transitions()

    def _handle_transitions(self):
        ns = self._scene.next_scene() if hasattr(self._scene, "next_scene") else None
        if ns is None:
            return

        # Title → overworld
        if isinstance(self._scene, TitleScene):
            if ns in ("new_game", "overworld"):
                if ns == "new_game":
                    from save_system import new_save, save_game
                    save_game(new_save())
                    self.gs = GameState()
                self._goto_overworld()

        # Overworld → battle
        elif hasattr(self._scene, "pop_enemy") and ns == "battle":
            enemy = self._scene.pop_enemy()
            if enemy:
                self._goto_battle(enemy)

        # Overworld → ending
        elif hasattr(self._scene, "pop_enemy") and ns == "ending":
            self._goto_ending()

        # Battle → overworld / gameover
        elif isinstance(self._scene, type(self._battle)) and self._battle:
            if ns == "overworld":
                outcome = self._battle.outcome()
                if outcome == "victory":
                    self.shake.shake(0.3, 5)
                self._battle = None
                self._goto_overworld()
            elif ns == "gameover":
                self.gs.save()
                self._battle = None
                self._goto_overworld()   # restart at last save

        # Ending scene done
        elif isinstance(self._scene, EndingScene):
            if self._scene.is_done():
                self._goto_title(has_save=True)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    Game().run()
