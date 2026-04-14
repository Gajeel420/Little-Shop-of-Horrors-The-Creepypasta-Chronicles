"""
Visual effects and creepypasta horror layer.
Drawn on top of every scene.
"""

import pygame
import random
import string
import math
from constants import *


# ── Screen Shake ──────────────────────────────────────────────────────────────

class ScreenShake:
    def __init__(self):
        self._timer    = 0.0
        self._strength = 0

    def shake(self, duration=0.25, strength=4):
        self._timer    = duration
        self._strength = strength

    def update(self, dt):
        if self._timer > 0:
            self._timer -= dt

    def offset(self):
        if self._timer > 0:
            s = self._strength
            return (random.randint(-s, s), random.randint(-s, s))
        return (0, 0)


# ── Glitch text ───────────────────────────────────────────────────────────────

def glitch_text(text, intensity=0.15):
    """Replace random chars with noise. intensity 0-1."""
    result = []
    for ch in text:
        if ch != " " and random.random() < intensity:
            result.append(random.choice("█▓▒░╬╫╪▲▼◄►■□"))
        else:
            result.append(ch)
    return "".join(result)


# ── Creepypasta overlay ───────────────────────────────────────────────────────

class CreepyOverlay:
    """
    Randomly flashes meta horror messages on screen.
    Draws 'The Watcher' shadow figure in corners.
    """

    WATCHER_ART = [
        "  /|\\  ",
        " / | \\ ",
        "|  |  |",
        " \\_|_/ ",
        "   |   ",
        "  / \\  ",
    ]

    def __init__(self, font_sm, font_lg):
        self.font_sm = font_sm
        self.font_lg = font_lg

        self._msg_timer    = 0.0
        self._msg_interval = random.uniform(25, 50)
        self._current_msg  = ""
        self._msg_alpha    = 0
        self._msg_fade     = 0.0

        self._watcher_visible  = False
        self._watcher_timer    = 0.0
        self._watcher_interval = random.uniform(60, 120)
        self._watcher_corner   = 0   # 0=TL 1=TR 2=BL 3=BR

        self._deaths   = 0
        self._corrupt  = 0

    def set_state(self, deaths, corruption):
        self._deaths  = deaths
        self._corrupt = corruption

    def update(self, dt):
        # ── Creepy message ──────────────────────────────────
        self._msg_timer += dt
        if self._msg_timer >= self._msg_interval and not self._current_msg:
            self._msg_timer    = 0.0
            self._msg_interval = random.uniform(20, 45)
            msg = random.choice(CREEPY_MSGS)
            msg = msg.replace("{deaths}", str(self._deaths))
            self._current_msg  = msg
            self._msg_alpha    = 200
            self._msg_fade     = 0.0

        if self._current_msg:
            self._msg_fade += dt
            if self._msg_fade > 3.0:
                fade_speed = 120
                self._msg_alpha -= fade_speed * dt
                if self._msg_alpha <= 0:
                    self._msg_alpha   = 0
                    self._current_msg = ""

        # ── The Watcher ─────────────────────────────────────
        self._watcher_timer += dt
        if self._watcher_timer >= self._watcher_interval:
            self._watcher_timer    = 0.0
            self._watcher_interval = random.uniform(45, 90)
            self._watcher_visible  = True
            self._watcher_corner   = random.randint(0, 3)

    def notify_approach(self, player_pos):
        """Call when player gets close to watcher corner."""
        if self._watcher_visible:
            cx, cy = self._corner_pos()
            dx, dy = player_pos[0] - cx, player_pos[1] - cy
            if math.hypot(dx, dy) < 60:
                self._watcher_visible = False   # It disappears silently

    def draw(self, surf: pygame.Surface):
        self._draw_watcher(surf)
        self._draw_message(surf)

    def _draw_watcher(self, surf):
        if not self._watcher_visible:
            return
        cx, cy = self._corner_pos()
        dark = pygame.Surface((50, 60), pygame.SRCALPHA)
        dark.fill((0, 0, 0, 0))
        for i, line in enumerate(self.WATCHER_ART):
            txt = self.font_sm.render(line, True, (20, 0, 20))
            dark.blit(txt, (0, i * self.font_sm.get_linesize()))
        dark.set_alpha(160)
        surf.blit(dark, (cx, cy))

    def _draw_message(self, surf):
        if not self._current_msg or self._msg_alpha <= 0:
            return
        alpha = int(max(0, min(255, self._msg_alpha)))
        # Corruption-modulated color
        c = min(255, int(self._corrupt * 2.55))
        color = (c, 255 - c, 0)
        text = self._current_msg
        if self._corrupt > 50:
            text = glitch_text(text, intensity=0.08)
        label = self.font_lg.render(text, True, color)
        label.set_alpha(alpha)
        x = (SCREEN_W - label.get_width()) // 2
        surf.blit(label, (x, 20))

    def _corner_pos(self):
        margin = 4
        w, h = 56, 70
        corners = [
            (margin, margin),
            (SCREEN_W - w - margin, margin),
            (margin, SCREEN_H - h - margin),
            (SCREEN_W - w - margin, SCREEN_H - h - margin),
        ]
        return corners[self._watcher_corner]


# ── Desaturation / corruption tint ───────────────────────────────────────────

def apply_corruption_tint(surf: pygame.Surface, stage: int):
    """
    stage 0: no effect
    stage 1: slight green tint
    stage 2: desaturated
    stage 3: heavy red/monochrome
    """
    if stage == 0:
        return
    w, h = surf.get_size()
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    if stage == 1:
        overlay.fill((0, 30, 0, 18))
    elif stage == 2:
        overlay.fill((0, 20, 0, 40))
    elif stage == 3:
        overlay.fill((40, 0, 0, 60))
    surf.blit(overlay, (0, 0))


# ── VHS scanline effect ───────────────────────────────────────────────────────

def apply_scanlines(surf: pygame.Surface, alpha=30):
    """Horizontal scanline overlay for retro CRT look."""
    h = surf.get_height()
    w = surf.get_width()
    line = pygame.Surface((w, 1), pygame.SRCALPHA)
    line.fill((0, 0, 0, alpha))
    for y in range(0, h, 3):
        surf.blit(line, (0, y))
