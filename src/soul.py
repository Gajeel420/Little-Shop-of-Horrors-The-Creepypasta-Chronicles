"""
Player's SOUL – the heart the player controls in the battle dodge phase.
Drawn entirely with pygame primitives (no image files needed).
"""

import pygame
from constants import *


class Soul:
    def __init__(self, box_rect: pygame.Rect):
        self.box   = box_rect
        self.x     = float(box_rect.centerx)
        self.y     = float(box_rect.centery)
        self.inv   = 0.0    # invincibility timer
        self.alive = True
        self._corruption = 0   # 0-100, shifts color yellow→red

    # ── Color ─────────────────────────────────────────────────────────────────
    @property
    def color(self):
        t = min(1.0, self._corruption / 100.0)
        r = int(YELLOW[0] + t * (RED[0] - YELLOW[0]))
        g = int(YELLOW[1] + t * (RED[1] - YELLOW[1]))
        b = int(YELLOW[2] + t * (RED[2] - YELLOW[2]))
        return (r, g, b)

    def set_corruption(self, c):
        self._corruption = max(0, min(100, c))

    # ── Reset position to box center ──────────────────────────────────────────
    def reset(self):
        self.x     = float(self.box.centerx)
        self.y     = float(self.box.centery)
        self.alive = True
        self.inv   = 0.0

    # ── Input + physics ───────────────────────────────────────────────────────
    def update(self, dt, keys):
        if not self.alive:
            return
        if self.inv > 0:
            self.inv -= dt

        vx, vy = 0.0, 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: vx = -SOUL_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: vx =  SOUL_SPEED
        if keys[pygame.K_UP]    or keys[pygame.K_w]: vy = -SOUL_SPEED
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: vy =  SOUL_SPEED

        # Diagonal normalise
        if vx and vy:
            vx *= 0.707
            vy *= 0.707

        self.x = max(self.box.left  + SOUL_R,
                     min(self.box.right  - SOUL_R, self.x + vx * dt))
        self.y = max(self.box.top   + SOUL_R,
                     min(self.box.bottom - SOUL_R, self.y + vy * dt))

    # ── Collision rect ────────────────────────────────────────────────────────
    def rect(self) -> pygame.Rect:
        return pygame.Rect(self.x - SOUL_R, self.y - SOUL_R,
                           SOUL_R * 2, SOUL_R * 2)

    def is_invincible(self):
        return self.inv > 0

    def hit(self) -> bool:
        """Returns True if damage was accepted (not invincible)."""
        if self.inv <= 0:
            self.inv = INV_TIME
            return True
        return False

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, surf: pygame.Surface):
        if not self.alive:
            return
        # Blink while invincible
        if self.inv > 0 and int(self.inv * 10) % 2 == 0:
            return
        _draw_heart(surf, (int(self.x), int(self.y)), SOUL_R, self.color)


def _draw_heart(surf, pos, r, color):
    """Pixel-art heart / SOUL shape."""
    x, y = pos
    # Two bumps on top + diamond body
    pygame.draw.circle(surf, color, (x - r // 2, y - r // 3), r // 2)
    pygame.draw.circle(surf, color, (x + r // 2, y - r // 3), r // 2)
    points = [
        (x - r,     y - r // 4),
        (x,         y + r),
        (x + r,     y - r // 4),
        (x,         y - r // 2),
    ]
    pygame.draw.polygon(surf, color, points)
