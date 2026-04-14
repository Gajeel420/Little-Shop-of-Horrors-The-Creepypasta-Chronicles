"""
UI rendering helpers used by battle.py and overworld.py.
All drawing is done with pygame primitives + text – no image files.
"""

import pygame
import math
from constants import *


# ── Font cache (call init_fonts after pygame.init) ────────────────────────────

_fonts = {}

def init_fonts():
    global _fonts
    _fonts = {
        "sm":  pygame.font.SysFont("monospace", 12),
        "md":  pygame.font.SysFont("monospace", 14),
        "lg":  pygame.font.SysFont("monospace", 18),
        "xl":  pygame.font.SysFont("monospace", 24),
        "xxl": pygame.font.SysFont("monospace", 32),
    }

def font(size="md"):
    return _fonts.get(size, _fonts["md"])


# ── Primitive helpers ─────────────────────────────────────────────────────────

def draw_text(surf, text, pos, color=WHITE, size="md", center=False):
    f   = font(size)
    img = f.render(str(text), True, color)
    x, y = pos
    if center:
        x -= img.get_width() // 2
    surf.blit(img, (x, y))
    return img.get_width()


def draw_box(surf, rect, border_color=WHITE, fill_color=BLACK, border=2):
    pygame.draw.rect(surf, fill_color, rect)
    pygame.draw.rect(surf, border_color, rect, border)


def draw_hp_bar(surf, rect, current, maximum, color=GREEN):
    """Filled HP bar with border."""
    pygame.draw.rect(surf, DARK_GRAY, rect)
    if maximum > 0:
        fill_w = int(rect.width * (current / maximum))
        fill_r = pygame.Rect(rect.left, rect.top, fill_w, rect.height)
        bar_color = color
        frac = current / maximum
        if frac < 0.25:
            bar_color = RED
        elif frac < 0.55:
            bar_color = ORANGE
        pygame.draw.rect(surf, bar_color, fill_r)
    pygame.draw.rect(surf, WHITE, rect, 1)


def draw_wrapped(surf, text, rect, color=WHITE, size="md"):
    f     = font(size)
    words = text.split(" ")
    line  = ""
    y     = rect.top
    lh    = f.get_linesize()
    for word in words:
        test = (line + " " + word).strip()
        if f.size(test)[0] <= rect.width:
            line = test
        else:
            if line:
                surf.blit(f.render(line, True, color), (rect.left, y))
                y += lh
            line = word
        if y + lh > rect.bottom:
            break
    if line and y + lh <= rect.bottom:
        surf.blit(f.render(line, True, color), (rect.left, y))


# ── Battle Box ────────────────────────────────────────────────────────────────

def draw_battle_box(surf, box_rect: pygame.Rect, border_color=WHITE, border=BBOX_BORDER):
    pygame.draw.rect(surf, BLACK, box_rect)
    pygame.draw.rect(surf, border_color, box_rect, border)


# ── Enemy ASCII sprite ────────────────────────────────────────────────────────

def draw_enemy_sprite(surf, art_lines, center_x, top_y, color=WHITE, size="md"):
    f  = font(size)
    lh = f.get_linesize()
    for i, line in enumerate(art_lines):
        img = f.render(line, True, color)
        x   = center_x - img.get_width() // 2
        surf.blit(img, (x, top_y + i * lh))
    return lh * len(art_lines)


# ── Battle HUD (top portion) ──────────────────────────────────────────────────

def draw_battle_hud(surf, enemy, player_hp, player_max_hp, player_lv):
    """Draw enemy name + HP at top, player info at very top-left."""
    # Enemy name + HP
    name_x = SCREEN_W // 2
    draw_text(surf, enemy.name, (name_x, 8), enemy.color, size="lg", center=True)

    hp_bar = pygame.Rect(name_x - 80, 28, 160, 8)
    draw_hp_bar(surf, hp_bar, enemy.hp, enemy.max_hp, color=RED)
    draw_text(surf, f"HP {enemy.hp}/{enemy.max_hp}", (name_x, 40), GRAY, size="sm", center=True)

    # Mercy bar (yellow)
    mercy_bar = pygame.Rect(name_x - 80, 52, 160, 5)
    pygame.draw.rect(surf, DARK_GRAY, mercy_bar)
    fill = int(mercy_bar.width * (enemy.mercy / 100))
    pygame.draw.rect(surf, YELLOW, pygame.Rect(mercy_bar.left, mercy_bar.top, fill, mercy_bar.height))
    pygame.draw.rect(surf, WHITE, mercy_bar, 1)

    # Player stats (bottom-right of screen above menu)
    menu_top = SCREEN_H - MENU_AREA_H - DIALOGUE_AREA_H - 4
    draw_text(surf, f"LV {player_lv}", (8, menu_top - 18), WHITE, size="sm")
    draw_text(surf, f"HP", (8, menu_top - 4), WHITE, size="sm")
    bar = pygame.Rect(28, menu_top - 2, 100, 8)
    draw_hp_bar(surf, bar, player_hp, player_max_hp)
    draw_text(surf, f"{player_hp}/{player_max_hp}", (134, menu_top - 4), WHITE, size="sm")


DIALOGUE_AREA_H = 80
MENU_AREA_H     = 36


# ── Bottom menu (FIGHT / ACT / ITEM / MERCY) ──────────────────────────────────

MENU_LABELS  = ["FIGHT", "ACT", "ITEM", "MERCY"]
MENU_COLORS  = [RED, CYAN, ORANGE, YELLOW]

def draw_main_menu(surf, selected: int):
    menu_y = SCREEN_H - MENU_AREA_H + 4
    slot_w = SCREEN_W // 4
    for i, (label, col) in enumerate(zip(MENU_LABELS, MENU_COLORS)):
        x = i * slot_w + slot_w // 2
        is_sel = (i == selected)
        c = col if is_sel else DIM
        # Cursor heart
        if is_sel:
            _draw_small_heart(surf, (x - 32, menu_y + 8), SOUL_COLOR)
        draw_text(surf, label, (x - 20, menu_y + 2), c, size="md")
    # Border line
    pygame.draw.line(surf, WHITE, (0, SCREEN_H - MENU_AREA_H),
                     (SCREEN_W, SCREEN_H - MENU_AREA_H), 1)


def draw_sub_menu(surf, items, selected, title=""):
    """Generic sub-menu panel (ACT list / ITEM list)."""
    panel = pygame.Rect(30, SCREEN_H - DIALOGUE_AREA_H - MENU_AREA_H - 10,
                        SCREEN_W - 60, DIALOGUE_AREA_H + MENU_AREA_H + 6)
    draw_box(surf, panel)
    if title:
        draw_text(surf, title, (panel.left + 6, panel.top + 4), YELLOW, size="sm")
    row_h = 16
    start_y = panel.top + (20 if title else 6)
    for i, item in enumerate(items):
        label = item if isinstance(item, str) else item["label"]
        y = start_y + i * row_h
        if y + row_h > panel.bottom - 4:
            break
        is_sel = (i == selected)
        color  = YELLOW if is_sel else WHITE
        if is_sel:
            _draw_small_heart(surf, (panel.left + 4, y + 2), SOUL_COLOR)
        draw_text(surf, label, (panel.left + 18, y), color, size="sm")


# ── FIGHT slider ─────────────────────────────────────────────────────────────

def draw_fight_slider(surf, t: float, box_x=150, box_y=400,
                      box_w=340, box_h=18):
    """
    t = 0.0..1.0 (oscillating cursor position).
    Returns 'power zone' rect for hit detection.
    """
    # Background track
    track = pygame.Rect(box_x, box_y, box_w, box_h)
    pygame.draw.rect(surf, DARK_GRAY, track)
    pygame.draw.rect(surf, WHITE, track, 1)

    # Power zone (sweet spot)
    sweet_w = int(box_w * 0.18)
    sweet_x = box_x + (box_w - sweet_w) // 2
    sweet   = pygame.Rect(sweet_x, box_y, sweet_w, box_h)
    pygame.draw.rect(surf, YELLOW, sweet)

    # Cursor
    cx = box_x + int(t * box_w)
    pygame.draw.rect(surf, WHITE, pygame.Rect(cx - 2, box_y - 2, 4, box_h + 4))

    draw_text(surf, "* Press Z / ENTER to strike!", (box_x, box_y - 18), WHITE, size="sm")
    return sweet


# ── HUD for overworld ─────────────────────────────────────────────────────────

def draw_overworld_hud(surf, gs):
    """Draw HP + LV + area name at bottom."""
    y   = SCREEN_H - 22
    draw_text(surf, f"LV {gs.lv}", (6, y), WHITE, size="sm")
    bar = pygame.Rect(36, y + 2, 90, 8)
    draw_hp_bar(surf, bar, gs.hp, gs.max_hp)
    draw_text(surf, f"{gs.hp}/{gs.max_hp}", (132, y), WHITE, size="sm")

    area_name = {
        AREA_GARDEN:      "The Withering Garden",
        AREA_CONSUMPTION: "The Consumption District",
        AREA_DARKNESS:    "The Outer Darkness",
    }.get(gs.area, gs.area)
    draw_text(surf, area_name, (SCREEN_W // 2, y), GRAY, size="sm", center=True)

    frags = gs.memory_frags
    draw_text(surf, f"[{frags}/8]", (SCREEN_W - 50, y), GOLD if frags > 0 else DIM, size="sm")


# ── Small heart icon ──────────────────────────────────────────────────────────

def _draw_small_heart(surf, pos, color):
    x, y = pos
    r = 4
    pygame.draw.circle(surf, color, (x - r // 2 + 1, y - r // 4), r // 2)
    pygame.draw.circle(surf, color, (x + r // 2 - 1, y - r // 4), r // 2)
    pts = [(x - r, y), (x, y + r), (x + r, y), (x, y - r // 2)]
    pygame.draw.polygon(surf, color, pts)
