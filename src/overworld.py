"""
Overworld exploration – tile-based maps for each area.

Tile characters:
  '#'  wall
  '.'  floor (walkable)
  '!'  encounter floor (random battle chance)
  'S'  player start
  'N'  NPC (interact with Z)
  'M'  memory fragment collectible
  'B'  boss trigger
  '>'  exit to next area
  '*'  save point
"""

import pygame
import random
from constants import *
from effects   import apply_corruption_tint, apply_scanlines, CreepyOverlay
from ui        import (init_fonts, font, draw_text, draw_box,
                        draw_overworld_hud, DIALOGUE_AREA_H, MENU_AREA_H)
from dialogue  import DialogueBox


# ── Map definitions ───────────────────────────────────────────────────────────

TILE_SIZE = 16   # pixels per tile on the 640x480 surface

MAPS = {
    AREA_GARDEN: [
        "###################################",
        "#..*....!....!...N......!..!.....#",
        "#.###.####.####.####.###.####.###",
        "#...!.....!.....!....!....!......#",
        "###.##.####.###.####.###.####.###",
        "#.M..!....!.....!....!..........#",
        "#.###.####.####.####.###.####.###",
        "#....!.....!....N.....!..!.......#",
        "###.###.###.###.###.###.###.###.##",
        "#....!.....!.....!..B..!....!....#",
        "#.###.####.####.####.###.####.###",
        "#....!.....!.....!...M..!....!...#",
        "###################################",
    ],
    AREA_CONSUMPTION: [
        "###################################",
        "#...*....!....!..N......!..!.....#",
        "#.####.####.####.###.####.####.##",
        "#....!.....!....!....!....!......#",
        "###.##.###.###.####.###.###.####.#",
        "#.M...!....!....!....!..........#",
        "#.####.###.####.###.####.###.####",
        "#.....!....!....N....!....!......#",
        "###.###.###.###.###.###.###.###.##",
        "#....!.....!....!...B...!....!...#",
        "#.####.###.####.###.####.###.####",
        "#....!.....!....!...M....!....!..#",
        "###################################",
    ],
    AREA_DARKNESS: [
        "###################################",
        "#....*...!....!..N.....!...!.....#",
        "#.#####.####.###.####.####.#####.#",
        "#....!....!....!....!....!.......#",
        "##.###.###.###.###.###.###.###.###",
        "#.M....!....!....!....!..........#",
        "#.#####.####.###.####.####.#####.#",
        "#.....!....!....N....!....!......#",
        "##.###.###.###.###.###.###.###.###",
        "#....!.....!....!...B...!....!...#",
        "#.#####.####.###.####.####.#####.#",
        "#....!.....!....!...M....!....!..#",
        "###################################",
    ],
}

NPC_DIALOGUE = {
    AREA_GARDEN: [
        "\"Seymour…  why are you still here?\"\n\"We all tried to leave.\"",
        "\"The plant feeds on more than flesh.\"\n\"It feeds on hope.\"",
        "\"I remember sunshine.  Do you?\"",
    ],
    AREA_CONSUMPTION: [
        "\"Sign nothing.  They make the ink\nfrom something you don't want to know about.\"",
        "\"Patrick sold me a warranty on my\nown soul.  The deductible was enormous.\"",
        "\"Look at the fine print.  It has your\nname in there.  It always did.\"",
    ],
    AREA_DARKNESS: [
        "\"There is no exit.\"\n\"There is only the plant.\"",
        "\"I tried the pacifist route once.\"\n\"...\"\n\"It still remembers me.\"",
        "\"Your save file has been here\nlonger than you realize.\"",
    ],
}

SAVE_POINT_MSG = [
    "* A familiar warmth.  HP restored.",
    "* The save point glows.  Do you feel it?",
    "* Something preserved this moment.  Good luck.",
]

ENCOUNTER_CHANCE = 0.20   # per step on '!' tile


# ── Player sprite ─────────────────────────────────────────────────────────────

class OWPlayer:
    def __init__(self, tx, ty):
        self.tx = tx    # tile x
        self.ty = ty    # tile y
        self.px = float(tx * TILE_SIZE + TILE_SIZE // 2)
        self.py = float(ty * TILE_SIZE + TILE_SIZE // 2)
        self.move_cd = 0.0     # cooldown between moves
        self.MOVE_DELAY = 0.12

    def try_move(self, dx, dy, tilemap):
        if self.move_cd > 0:
            return None
        nx, ny = self.tx + dx, self.ty + dy
        if 0 <= ny < len(tilemap) and 0 <= nx < len(tilemap[ny]):
            tile = tilemap[ny][nx]
            if tile != '#':
                self.tx = nx
                self.ty = ny
                self.px = float(nx * TILE_SIZE + TILE_SIZE // 2)
                self.py = float(ny * TILE_SIZE + TILE_SIZE // 2)
                self.move_cd = self.MOVE_DELAY
                return tile
        return None

    def update(self, dt):
        if self.move_cd > 0:
            self.move_cd -= dt

    def draw(self, surf, font_obj, offset_x=0, offset_y=0):
        x = int(self.px) - TILE_SIZE // 2 + offset_x
        y = int(self.py) - TILE_SIZE // 2 + offset_y
        # Small '@' character for Seymour
        img = font_obj.render("@", True, YELLOW)
        surf.blit(img, (x, y))


# ── OverworldScene ────────────────────────────────────────────────────────────

class OverworldScene:
    def __init__(self, gs, creepy: CreepyOverlay):
        self.gs       = gs
        self.creepy   = creepy
        self._tilemap = None
        self._player  = None
        self._load_area(gs.area)

        self.dlg_rect  = pygame.Rect(0, SCREEN_H - DIALOGUE_AREA_H - MENU_AREA_H,
                                     SCREEN_W, DIALOGUE_AREA_H)
        self.dlg       = DialogueBox(font("md"), self.dlg_rect)

        self._next_battle_enemy = None   # set before transitioning
        self._next_scene        = None   # "battle", "ending"
        self._npc_pool          = list(NPC_DIALOGUE.get(gs.area, [""]))

        self._show_map_name     = 2.0    # display area name for 2s on enter
        self._frag_collected    = False

    # ── Scene interface ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key = event.key
        confirm = key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE)

        if not self.dlg.is_empty():
            if confirm:
                self.dlg.advance()
            return

        # Movement
        dx, dy = 0, 0
        if key in (pygame.K_LEFT,  pygame.K_a): dx = -1
        if key in (pygame.K_RIGHT, pygame.K_d): dx =  1
        if key in (pygame.K_UP,    pygame.K_w): dy = -1
        if key in (pygame.K_DOWN,  pygame.K_s): dy =  1

        if dx or dy:
            tile = self._player.try_move(dx, dy, self._tilemap)
            if tile is not None:
                self._on_step(tile)

    def update(self, dt):
        self._player.update(dt)
        self.dlg.update(dt)
        if self._show_map_name > 0:
            self._show_map_name -= dt
        # Update creepy overlay
        self.creepy.set_state(self.gs.deaths, self.gs.corruption)
        self.creepy.update(dt)
        # Notify watcher of player pos
        self.creepy.notify_approach(
            (self._player.px, self._player.py)
        )

    def draw(self, surf: pygame.Surface):
        surf.fill(BLACK)
        apply_corruption_tint(surf, self.gs.corruption_stage())

        self._draw_map(surf)
        self._player.draw(surf, font("sm"))

        # Dialogue box
        if not self.dlg.is_empty():
            self.dlg.draw(surf)

        # Area name banner
        if self._show_map_name > 0:
            area_names = {
                AREA_GARDEN:      "~ The Withering Garden ~",
                AREA_CONSUMPTION: "~ The Consumption District ~",
                AREA_DARKNESS:    "~ The Outer Darkness ~",
            }
            name = area_names.get(self.gs.area, self.gs.area)
            alpha = int(min(255, self._show_map_name * 120))
            label = font("lg").render(name, True, CREAM)
            label.set_alpha(alpha)
            surf.blit(label, ((SCREEN_W - label.get_width()) // 2, 30))

        draw_overworld_hud(surf, self.gs)
        self.creepy.draw(surf)
        apply_scanlines(surf, alpha=14)

    def next_scene(self):
        return self._next_scene

    def pop_enemy(self):
        e = self._next_battle_enemy
        self._next_battle_enemy = None
        self._next_scene        = None
        return e

    # ── Map drawing ───────────────────────────────────────────────────────────

    def _draw_map(self, surf):
        f  = font("sm")
        lh = TILE_SIZE

        # Camera: center on player
        cam_x = int(self._player.px) - SCREEN_W // 2
        cam_y = int(self._player.py) - (SCREEN_H - DIALOGUE_AREA_H - MENU_AREA_H - 30) // 2
        cam_x = max(0, cam_x)
        cam_y = max(0, cam_y)

        for ry, row in enumerate(self._tilemap):
            for rx, tile in enumerate(row):
                px = rx * TILE_SIZE - cam_x
                py = ry * TILE_SIZE - cam_y
                if px < -TILE_SIZE or px > SCREEN_W or py < -TILE_SIZE or py > SCREEN_H:
                    continue

                char, color = _tile_render(tile)
                img = f.render(char, True, color)
                surf.blit(img, (px, py))

        # Re-draw player with camera offset
        px = int(self._player.px) - cam_x - TILE_SIZE // 2
        py = int(self._player.py) - cam_y - TILE_SIZE // 2
        img = f.render("@", True, YELLOW)
        surf.blit(img, (px, py))

    # ── Tile step handler ─────────────────────────────────────────────────────

    def _on_step(self, tile):
        if tile == '!':
            if random.random() < ENCOUNTER_CHANCE:
                self._trigger_random_battle()

        elif tile == 'N':
            msg = random.choice(self._npc_pool) if self._npc_pool else "..."
            self.dlg.push(msg)

        elif tile == 'M':
            if not self._frag_collected:
                self._frag_collected = True
                self.gs.add_memory_frag()
                msg = f"* Memory Fragment found!  [{self.gs.memory_frags}/8]"
                if self.gs.has_locket:
                    msg += "\nAudrey's Locket materializes in your pocket."
                self.dlg.push(msg)
                self.gs.save()
                # Remove tile
                self._replace_tile('M', '.')

        elif tile == 'B':
            self._trigger_boss_battle()

        elif tile == '>':
            self._advance_area()

        elif tile == '*':
            self.gs.hp = self.gs.max_hp
            self.gs.save()
            msg = random.choice(SAVE_POINT_MSG)
            if self.gs.deaths > 0:
                msg += f"\n  (you have died {self.gs.deaths} time{'s' if self.gs.deaths != 1 else ''})"
            self.dlg.push(msg)

    def _trigger_random_battle(self):
        from entities import get_random_enemy
        enemy = get_random_enemy(self.gs.area)
        self._next_battle_enemy = enemy
        self._next_scene        = "battle"

    def _trigger_boss_battle(self):
        from entities import get_boss
        boss = get_boss(self.gs.area, self.gs)
        if boss is None:
            return
        self._next_battle_enemy = boss
        self._next_scene        = "battle"
        # Remove boss tile so it doesn't re-trigger
        self._replace_tile('B', '.')

    def _advance_area(self):
        order = [AREA_GARDEN, AREA_CONSUMPTION, AREA_DARKNESS]
        idx   = order.index(self.gs.area) if self.gs.area in order else -1
        if idx < len(order) - 1:
            self.gs.area    = order[idx + 1]
            self.gs.chapter = idx + 1
            self.gs.save()
            self._load_area(self.gs.area)
            self._npc_pool = list(NPC_DIALOGUE.get(self.gs.area, [""]))
            self._show_map_name = 2.0
        else:
            # Reached the end – trigger ending
            self._next_scene = "ending"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_area(self, area):
        raw  = MAPS.get(area, MAPS[AREA_GARDEN])
        self._tilemap = [list(row) for row in raw]
        # Find start tile 'S'
        sx, sy = 2, 1
        for ry, row in enumerate(self._tilemap):
            for rx, tile in enumerate(row):
                if tile == 'S':
                    sx, sy = rx, ry
                    self._tilemap[ry][rx] = '.'
        self._player = OWPlayer(sx, sy)

    def _replace_tile(self, old, new):
        py, px_coord = self._player.ty, self._player.tx
        if (0 <= py < len(self._tilemap) and
                0 <= px_coord < len(self._tilemap[py])):
            if self._tilemap[py][px_coord] == old:
                self._tilemap[py][px_coord] = new


def _tile_render(tile):
    """Return (char, color) for a tile character."""
    return {
        '#': ('█', DARK_GRAY),
        '.': (' ', BLACK),
        '!': ('·', DIM),
        'N': ('☺', CYAN),
        'M': ('◆', GOLD),
        'B': ('☠', RED),
        '>': ('►', GREEN),
        '*': ('✦', YELLOW),
        'S': (' ', BLACK),
    }.get(tile, (' ', BLACK))
