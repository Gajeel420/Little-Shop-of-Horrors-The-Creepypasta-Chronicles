"""
Bullet / projectile system for the battle dodge phase.
All bullets are drawn with pygame primitives.
"""

import pygame
import math
import random
from constants import *


# ── Base bullet ───────────────────────────────────────────────────────────────

class Bullet:
    """A single projectile the player's SOUL must dodge."""

    def __init__(self, x, y, vx, vy, radius=5, color=WHITE, damage=2,
                 shape="circle", width=0, height=0, angle=0):
        self.x      = float(x)
        self.y      = float(y)
        self.vx     = float(vx)
        self.vy     = float(vy)
        self.radius = radius
        self.color  = color
        self.damage = damage
        self.shape  = shape          # "circle", "rect", "bone"
        self.width  = width or radius * 2
        self.height = height or radius * 2
        self.angle  = angle
        self.dead   = False
        self.age    = 0.0
        self.lifetime = 99.0         # override per bullet if needed

    def update(self, dt, box: pygame.Rect):
        self.age += dt
        if self.age > self.lifetime:
            self.dead = True
            return
        self.x += self.vx * dt
        self.y += self.vy * dt
        # Kill when far outside box
        margin = 40
        if (self.x < box.left - margin or self.x > box.right  + margin or
                self.y < box.top  - margin or self.y > box.bottom + margin):
            self.dead = True

    def collides(self, soul_rect: pygame.Rect) -> bool:
        if self.dead:
            return False
        # Simple AABB against circle hitbox
        cx, cy = int(self.x), int(self.y)
        return soul_rect.collidepoint(cx, cy)

    def draw(self, surf: pygame.Surface):
        if self.dead:
            return
        ix, iy = int(self.x), int(self.y)
        if self.shape == "circle":
            pygame.draw.circle(surf, self.color, (ix, iy), self.radius)
        elif self.shape == "rect":
            rect = pygame.Rect(ix - self.width // 2, iy - self.height // 2,
                               self.width, self.height)
            pygame.draw.rect(surf, self.color, rect)
        elif self.shape == "bone":
            # Undertale-style bone: a line with rounded end caps
            hw, hh = self.width // 2, self.height // 2
            body = pygame.Rect(ix - hw, iy - hh, self.width, self.height)
            pygame.draw.rect(surf, self.color, body)
            pygame.draw.circle(surf, self.color, (ix - hw, iy), hh)
            pygame.draw.circle(surf, self.color, (ix + hw, iy), hh)


# ── Homing bullet ─────────────────────────────────────────────────────────────

class HomingBullet(Bullet):
    def __init__(self, x, y, speed, color, damage, soul_ref):
        super().__init__(x, y, 0, 0, radius=5, color=color, damage=damage)
        self._soul = soul_ref
        self._speed = speed

    def update(self, dt, box):
        self.age += dt
        if self.age > self.lifetime:
            self.dead = True
            return
        # Steer toward SOUL
        dx = self._soul.x - self.x
        dy = self._soul.y - self.y
        dist = math.hypot(dx, dy) or 1
        self.vx = (dx / dist) * self._speed
        self.vy = (dy / dist) * self._speed
        self.x += self.vx * dt
        self.y += self.vy * dt
        margin = 40
        if (self.x < box.left - margin or self.x > box.right + margin or
                self.y < box.top - margin or self.y > box.bottom + margin):
            self.dead = True


# ── Pattern factory functions ─────────────────────────────────────────────────
# Each function receives the battle box rect (for sizing/centering) and
# optionally the soul reference.  Returns a list[Bullet].

BOX = pygame.Rect(BBOX_X, BBOX_Y, BBOX_W, BBOX_H)   # convenience default


def _box_edge(box, side):
    """Random point on one edge of the box."""
    if side == 0:   return (random.randint(box.left, box.right), box.top - 6)
    if side == 1:   return (random.randint(box.left, box.right), box.bottom + 6)
    if side == 2:   return (box.left - 6, random.randint(box.top, box.bottom))
    return               (box.right + 6, random.randint(box.top, box.bottom))


# ── Corrupted Succulent ────────────────────────────────────────────────────────

def pattern_thorn_burst(box, soul=None):
    """8-way thorn burst from box center."""
    cx, cy = box.centerx, box.centery
    bullets = []
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        spd = random.uniform(55, 80)
        bullets.append(Bullet(cx, cy, math.cos(rad)*spd, math.sin(rad)*spd,
                               radius=4, color=THORN, damage=2))
    return bullets


def pattern_thorn_rain(box, soul=None):
    """Thorns fall from the top at random x positions."""
    bullets = []
    for _ in range(6):
        x = random.randint(box.left + 10, box.right - 10)
        bullets.append(Bullet(x, box.top - 5, 0, random.uniform(70, 100),
                               radius=3, color=THORN, damage=1))
    return bullets


# ── Tooth Golem ───────────────────────────────────────────────────────────────

def pattern_tooth_volley(box, soul=None):
    """Row of teeth fired horizontally across."""
    bullets = []
    y_start = box.top + 20
    spacing = 28
    rows = 3
    for r in range(rows):
        y = y_start + r * spacing
        # Alternate directions
        if r % 2 == 0:
            x, vx = box.left - 5, random.uniform(90, 110)
        else:
            x, vx = box.right + 5, -random.uniform(90, 110)
        bullets.append(Bullet(x, y, vx, 0, shape="rect",
                               width=10, height=6, color=WHITE, damage=2))
    return bullets


# ── Shadow Stalker ────────────────────────────────────────────────────────────

def pattern_shadow_teleport(box, soul=None):
    """Near-invisible bullets that appear near the soul's position."""
    if soul is None:
        return pattern_thorn_burst(box)
    bullets = []
    for _ in range(4):
        ox = random.randint(-30, 30)
        oy = random.randint(-30, 30)
        x = max(box.left, min(box.right,  soul.x + ox))
        y = max(box.top,  min(box.bottom, soul.y + oy))
        # Expand outward from spawn point
        ang = math.radians(random.randint(0, 359))
        spd = random.uniform(60, 90)
        b = Bullet(x, y, math.cos(ang)*spd, math.sin(ang)*spd,
                   radius=4, color=(20, 20, 20), damage=3)
        # Give them a dark tint so they're hard to see – creepy!
        b.color = (30, 0, 30)
        bullets.append(b)
    return bullets


# ── Contract Wraith ───────────────────────────────────────────────────────────

def pattern_contract_cascade(box, soul=None):
    """Papers fly in from the sides and drift toward the soul."""
    bullets = []
    for _ in range(5):
        side = random.randint(0, 3)
        x, y = _box_edge(box, side)
        cx, cy = box.centerx, box.centery
        dx, dy = cx - x, cy - y
        dist = math.hypot(dx, dy) or 1
        spd = random.uniform(55, 80)
        b = Bullet(x, y, dx/dist*spd, dy/dist*spd,
                   shape="rect", width=8, height=10,
                   color=CREAM, damage=2)
        bullets.append(b)
    return bullets


# ── Void Tendril ──────────────────────────────────────────────────────────────

def pattern_void_grab(box, soul=None):
    """Slow-moving purple blobs from random edges."""
    bullets = []
    for _ in range(3):
        side = random.randint(0, 3)
        x, y = _box_edge(box, side)
        cx, cy = box.centerx, box.centery
        dx, dy = cx - x, cy - y
        dist = math.hypot(dx, dy) or 1
        spd = random.uniform(40, 60)
        b = Bullet(x, y, dx/dist*spd, dy/dist*spd,
                   radius=8, color=PURPLE, damage=3)
        bullets.append(b)
    return bullets


# ── Orin Scrivello (Boss 1) ───────────────────────────────────────────────────

def pattern_orin_drill(box, soul=None):
    """Fast drill line: 3 tight bullets in a column sweeping across."""
    bullets = []
    y_positions = [box.top + box.height // 4,
                   box.centery,
                   box.top + 3 * box.height // 4]
    for y in y_positions:
        vx = random.choice([-1, 1]) * random.uniform(110, 140)
        x  = box.right + 5 if vx < 0 else box.left - 5
        b = Bullet(x, y, vx, 0, radius=5, color=GRAY, damage=4, shape="rect",
                   width=14, height=6)
        bullets.append(b)
    return bullets


def pattern_orin_gas(box, soul=None):
    """Slow gas cloud bullets that linger and expand."""
    bullets = []
    for _ in range(4):
        x = random.randint(box.left + 10, box.right - 10)
        y = random.randint(box.top  + 10, box.bottom - 10)
        b = Bullet(x, y, random.uniform(-20, 20), random.uniform(-20, 20),
                   radius=10, color=(100, 200, 100), damage=2)
        b.lifetime = 2.5
        bullets.append(b)
    return bullets


def pattern_orin_tools(box, soul=None):
    """Dental tools (bone-shaped) fly in horizontally."""
    bullets = []
    for i in range(4):
        y = box.top + 20 + i * (box.height - 40) // 3
        vx = random.choice([-1, 1]) * random.uniform(100, 130)
        x  = box.right + 5 if vx < 0 else box.left - 5
        b = Bullet(x, y, vx, 0, shape="bone", width=18, height=6,
                   color=WHITE, damage=3)
        bullets.append(b)
    return bullets


# ── Patrick Martin (Boss 2) ───────────────────────────────────────────────────

def pattern_patrick_clones(box, soul=None):
    """8 mirrored bullets from all cardinal + diagonal edges."""
    cx, cy = box.centerx, box.centery
    bullets = []
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        sx = cx - math.cos(rad) * (box.width // 2 + 5)
        sy = cy - math.sin(rad) * (box.height // 2 + 5)
        spd = random.uniform(70, 100)
        b = Bullet(sx, sy, math.cos(rad)*spd, math.sin(rad)*spd,
                   radius=5, color=MAGENTA, damage=2)
        bullets.append(b)
    return bullets


def pattern_patrick_contracts(box, soul=None):
    """Papers aimed at the soul's current position."""
    if soul is None:
        return pattern_contract_cascade(box)
    bullets = []
    for _ in range(6):
        side = random.randint(0, 3)
        x, y = _box_edge(box, side)
        dx, dy = soul.x - x, soul.y - y
        dist = math.hypot(dx, dy) or 1
        spd = random.uniform(80, 110)
        b = Bullet(x, y, dx/dist*spd, dy/dist*spd,
                   shape="rect", width=8, height=10,
                   color=CREAM, damage=3)
        bullets.append(b)
    return bullets


# ── Audrey II (Final Boss) ────────────────────────────────────────────────────

def pattern_audrey_bite(box, soul=None):
    """Radial bite wave from all sides simultaneously."""
    bullets = []
    for side in range(4):
        for _ in range(3):
            x, y = _box_edge(box, side)
            cx, cy = box.centerx, box.centery
            dx, dy = cx - x, cy - y
            dist = math.hypot(dx, dy) or 1
            spd = random.uniform(90, 120)
            b = Bullet(x, y, dx/dist*spd, dy/dist*spd,
                       radius=7, color=LEAF_GREEN, damage=4)
            bullets.append(b)
    return bullets


def pattern_audrey_vine_sweep(box, soul=None):
    """Thorn vines sweep across the box in pairs."""
    bullets = []
    for i in range(5):
        y = box.top + i * (box.height // 4)
        delay_factor = i * 0.1
        b = Bullet(box.left - 5, y, 120, 0,
                   shape="bone", width=20, height=7, color=LEAF_GREEN, damage=3)
        b.age = -delay_factor   # stagger via negative starting age
        bullets.append(b)
    return bullets


def pattern_audrey_spores(box, soul=None):
    """Spiraling green spore bullets."""
    cx, cy = box.centerx, box.centery
    bullets = []
    for i in range(12):
        angle = math.radians(i * 30)
        spd   = random.uniform(50, 80)
        b = Bullet(cx, cy, math.cos(angle)*spd, math.sin(angle)*spd,
                   radius=5, color=DARK_GREEN, damage=2)
        bullets.append(b)
    return bullets


def pattern_audrey_memory(box, soul=None):
    """Homing memory-orbs (phase 2+)."""
    if soul is None:
        return pattern_audrey_bite(box)
    bullets = []
    for side in range(4):
        x, y = _box_edge(box, side)
        b = HomingBullet(x, y, speed=70, color=(80, 0, 80), damage=4, soul_ref=soul)
        b.lifetime = 4.0
        bullets.append(b)
    return bullets


# ── Pattern registry (used by entities) ──────────────────────────────────────
PATTERNS = {
    "thorn_burst":       pattern_thorn_burst,
    "thorn_rain":        pattern_thorn_rain,
    "tooth_volley":      pattern_tooth_volley,
    "shadow_teleport":   pattern_shadow_teleport,
    "contract_cascade":  pattern_contract_cascade,
    "void_grab":         pattern_void_grab,
    "orin_drill":        pattern_orin_drill,
    "orin_gas":          pattern_orin_gas,
    "orin_tools":        pattern_orin_tools,
    "patrick_clones":    pattern_patrick_clones,
    "patrick_contracts": pattern_patrick_contracts,
    "audrey_bite":       pattern_audrey_bite,
    "audrey_vine_sweep": pattern_audrey_vine_sweep,
    "audrey_spores":     pattern_audrey_spores,
    "audrey_memory":     pattern_audrey_memory,
}
