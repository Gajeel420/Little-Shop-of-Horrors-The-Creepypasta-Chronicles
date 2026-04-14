"""
Overworld exploration – tile-based maps for each area.

Tile characters:
  '#'  wall                 (solid, dark)
  '.'  floor                (walkable)
  '!'  encounter floor      (random battle chance)
  ','  grass / moss         (walkable decoration)
  ':'  cracked floor        (walkable decoration)
  '~'  water / acid         (impassable hazard)
  'T'  tree / pillar        (impassable decoration)
  'L'  lamp                 (walkable, glowing)
  'S'  player start
  'N'  NPC (interact with Z)
  'M'  memory fragment
  'B'  boss trigger
  '>'  exit to next area
  '*'  save point
  '+'  door / archway       (walkable)
"""

import pygame
import random
from constants import *
from effects   import apply_corruption_tint, apply_scanlines, CreepyOverlay
from ui        import (init_fonts, font, draw_text, draw_box,
                        draw_overworld_hud, DIALOGUE_AREA_H, MENU_AREA_H)
from dialogue  import DialogueBox


# ── Map definitions ───────────────────────────────────────────────────────────

TILE_SIZE = 28   # zoomed-in for readable pixel art

# Tiles the player can walk on
WALKABLE = set(".!,: LSNMB>*+")

MAPS = {
    # 30 columns x 27 rows — every row MUST be exactly 30 chars
    AREA_GARDEN: [
        "##############################",  # 0
        "#S..,.,,...T.,,..L.,,.T.,..,.#",  # 1
        "#..###..####....####..###..,.#",  # 2
        "#..#,,..!..,,....,!..,,#,..,.#",  # 3
        "#..#..##T##...,##T##..#..!,..#",  # 4
        "#..+...,,...N...,,....,+..!,.#",  # 5
        "#..#..##T##...,##T##..#..!...#",  # 6
        "#..#,,..!..,,....,!..,,#,....#",  # 7
        "#..###..####....####..###..M.#",  # 8
        "#.,,..,,..L...*...L..,..,,...#",  # 9
        "#.####..##########..####..!..#",  # 10
        "#..,,.,,..,.,.,.,,..,,..,.!..#",  # 11
        "#..##.####..,...####.##..!...#",  # 12
        "#.,,..,,..!..N..!.,,..,,.....#",  # 13
        "#.####.####..,..####.####.,..#",  # 14
        "#.,,..,,..,.,.,.,,..,,..,....#",  # 15
        "#..##..##..,.,.,.##..##..##..#",  # 16
        "#.,,..,,..,.,.,.,,..,,..,,...#",  # 17
        "#..####.####..+.####.####.M..#",  # 18
        "#.,,..,.,,...*...,,.,..,...,.#",  # 19
        "#.##.####..,.,.,.,.####..##..#",  # 20
        "#.,..,...!..!.!..!..,...,.!..#",  # 21
        "#.####..############..####...#",  # 22
        "#..,..,,..!...B...!..,,.,....#",  # 23
        "#..####..##########..####.,..#",  # 24
        "#.,,..,..,L...,..L..,..,.>...#",  # 25
        "##############################",  # 26
    ],
    AREA_CONSUMPTION: [
        "##############################",  # 0
        "#S..:..:..:..L..:..:..:..!...#",  # 1
        "#.:####.:####..:####.:####.:.#",  # 2
        "#.:..!.:..:..:..:..:.!..:.:..#",  # 3
        "#.####.####..:.:.####.####...#",  # 4
        "#.:..:..:.!.:N:.:!..:..:.!...#",  # 5
        "#.:##.:##.:.:.:.:.##.:##.:...#",  # 6
        "#.:..:..:..:.:.:..:..:..:....#",  # 7
        "#.####.####..:*:..####.####..#",  # 8
        "#.:..:..:..:..:..:..:..:M:...#",  # 9
        "#.:##.####..:.:.:####.##.:...#",  # 10
        "#.:..:..:!.:.N.:.:!..:..:.:..#",  # 11
        "#.####.:####.:.####.:####.:..#",  # 12
        "#.:..:..:..:.:..:..:..:..!...#",  # 13
        "#.:##.:##.:.:.:.:##.:##.:....#",  # 14
        "#.:..:..:..:.:.:..:..:..:....#",  # 15
        "#.####.####.:.:.####.####....#",  # 16
        "#.:..:..:!..:.:..!:..:..:.:..#",  # 17
        "#.:##.####.:+:.####.##.:M....#",  # 18
        "#.:..:..:..L:.:L..:..:..:....#",  # 19
        "#.####.####.:.:.:####.####...#",  # 20
        "#.:..:..:.!.:.:.:!..:..:.!...#",  # 21
        "#.:####.############.####....#",  # 22
        "#..:..:..:!...B...!:..:..!...#",  # 23
        "#.:####.:##########.:####....#",  # 24
        "#.:..:..:..L..*.L:..:..:>.:..#",  # 25
        "##############################",  # 26
    ],
    AREA_DARKNESS: [
        "##############################",  # 0
        "#S....~.........~.....~......#",  # 1
        "#.###.~.####.####.~.####.##..#",  # 2
        "#...!.~...!....!..~..!.......#",  # 3
        "###.#.~.####.####.~.####.##..#",  # 4
        "#.....~...........~..........#",  # 5
        "#.###.~###..~~~~~.###.~.###..#",  # 6
        "#...!.........N.........!....#",  # 7
        "###.####.###.*.###.####.###..#",  # 8
        "#..........L...L..........M..#",  # 9
        "#.###.####.#####.####.###....#",  # 10
        "#...!....!...!...!....!......#",  # 11
        "###.####.###.+.###.####.###..#",  # 12
        "#..........~...~.............#",  # 13
        "#.###.~~.####.####.~~.###....#",  # 14
        "#.....~~...........~~........#",  # 15
        "#.####.~.####N####.~.####....#",  # 16
        "#......~...........~.........#",  # 17
        "#.####.~.####.####.~.####.M..#",  # 18
        "#......~..L...*...L.~........#",  # 19
        "#.###.####.#####.####.###....#",  # 20
        "#...!....!..!.!..!....!......#",  # 21
        "#.####.####..###.####.####...#",  # 22
        "#..........!..B..!...........#",  # 23
        "#.####.####.#####.####.####..#",  # 24
        "#......L.........L........>..#",  # 25
        "##############################",  # 26
    ],
}

NPC_DIALOGUE = {
    AREA_GARDEN: [
        "\"Seymour...  why are you still here?\"\n\"We all tried to leave.\"",
        "\"The plant feeds on more than flesh.\"\n\"It feeds on hope.\"",
        "\"I remember sunshine.  Do you?\"",
        "\"Don't water anything here.\"\n\"The water is not water.\"",
    ],
    AREA_CONSUMPTION: [
        "\"Sign nothing.  They make the ink\nfrom something you don't want to know.\"",
        "\"Patrick sold me a warranty on my\nown soul.  The deductible was enormous.\"",
        "\"Look at the fine print.  It has\nyour name.  It always did.\"",
        "\"Every door leads to the same room.\"",
    ],
    AREA_DARKNESS: [
        "\"There is no exit.\"\n\"There is only the plant.\"",
        "\"I tried the pacifist route once.\"\n\"...\"\n\"It still remembers me.\"",
        "\"Your save file has been here\nlonger than you realize.\"",
        "\"Don't look at the water.\"\n\"It isn't water.\"",
    ],
}

SAVE_POINT_MSG = [
    "* A familiar warmth.  HP restored.",
    "* The save point glows.  Do you feel it?",
    "* Something preserved this moment.  Good luck.",
]

ENCOUNTER_CHANCE = 0.22   # per step on '!' tile


# ── Tile rendering ────────────────────────────────────────────────────────────

# Each entry: (fill_color or None, character, char_color)
TILE_VISUALS = {
    '#': ((18, 18, 22),    '█', (30, 30, 35)),
    '.': (BLACK,           ' ', BLACK),
    '!': (BLACK,           '·', (40, 40, 40)),
    ',': ((5, 12, 5),      ',', (30, 60, 30)),
    ':': ((10, 8, 8),      ':', (35, 30, 30)),
    '~': ((8, 8, 30),      '~', (30, 50, 120)),
    'T': ((12, 20, 12),    '♣', (20, 50, 20)),
    'L': ((20, 18, 8),     '¤', YELLOW),
    'N': (BLACK,           '☺', CYAN),
    'M': (BLACK,           '◆', GOLD),
    'B': ((20, 0, 0),      '☠', RED),
    '>': (BLACK,           '►', GREEN),
    '*': ((18, 18, 8),     '✦', YELLOW),
    '+': ((15, 12, 8),     '░', (50, 40, 30)),
    'S': (BLACK,           ' ', BLACK),
    ' ': (BLACK,           ' ', BLACK),
}


def _render_tile(surf, f, tile, px, py, corruption_stage=0):
    """Draw one tile as a filled rect + optional character."""
    fill, char, color = TILE_VISUALS.get(tile, (BLACK, ' ', BLACK))

    # Corruption darkens and shifts some tiles
    if corruption_stage >= 2 and fill:
        r, g, b = fill
        fill = (max(0, r - 5), max(0, g - 8), max(0, b - 2))

    if fill:
        pygame.draw.rect(surf, fill, (px, py, TILE_SIZE, TILE_SIZE))

    if char and char != ' ':
        # Lamp tiles glow
        if tile == 'L':
            glow = pygame.Surface((TILE_SIZE + 8, TILE_SIZE + 8), pygame.SRCALPHA)
            glow.fill((40, 35, 10, 30))
            surf.blit(glow, (px - 4, py - 4))

        img = f.render(char, True, color)
        # Center the char in the tile
        cx = px + (TILE_SIZE - img.get_width()) // 2
        cy = py + (TILE_SIZE - img.get_height()) // 2
        surf.blit(img, (cx, cy))


# ── Player sprite ─────────────────────────────────────────────────────────────

class OWPlayer:
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty
        self.px = float(tx * TILE_SIZE + TILE_SIZE // 2)
        self.py = float(ty * TILE_SIZE + TILE_SIZE // 2)
        self.move_cd = 0.0
        self.MOVE_DELAY = 0.12

    def try_move(self, dx, dy, tilemap):
        if self.move_cd > 0:
            return None
        nx, ny = self.tx + dx, self.ty + dy
        if 0 <= ny < len(tilemap) and 0 <= nx < len(tilemap[ny]):
            tile = tilemap[ny][nx]
            if tile in WALKABLE:
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

        self._next_battle_enemy = None
        self._next_scene        = None
        self._npc_pool          = list(NPC_DIALOGUE.get(gs.area, [""]))

        self._show_map_name     = 2.0
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
        self.creepy.set_state(self.gs.deaths, self.gs.corruption)
        self.creepy.update(dt)
        self.creepy.notify_approach(
            (self._player.px, self._player.py)
        )

    def draw(self, surf: pygame.Surface):
        surf.fill(BLACK)
        cs = self.gs.corruption_stage()
        apply_corruption_tint(surf, cs)

        self._draw_map(surf, cs)

        if not self.dlg.is_empty():
            self.dlg.draw(surf)

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

    def _draw_map(self, surf, corruption_stage=0):
        f = font("md")

        # Visible area (exclude HUD/dialogue band at bottom)
        view_h = SCREEN_H - DIALOGUE_AREA_H - MENU_AREA_H - 22

        # Camera centered on player, clamped to map edges
        map_pw = len(self._tilemap[0]) * TILE_SIZE if self._tilemap else 0
        map_ph = len(self._tilemap)    * TILE_SIZE if self._tilemap else 0

        cam_x = int(self._player.px) - SCREEN_W // 2
        cam_y = int(self._player.py) - view_h // 2
        cam_x = max(0, min(cam_x, map_pw - SCREEN_W))
        cam_y = max(0, min(cam_y, map_ph - view_h))

        # Draw visible tiles
        start_tx = max(0, cam_x // TILE_SIZE)
        start_ty = max(0, cam_y // TILE_SIZE)
        end_tx   = min(len(self._tilemap[0]) if self._tilemap else 0,
                       (cam_x + SCREEN_W) // TILE_SIZE + 2)
        end_ty   = min(len(self._tilemap) if self._tilemap else 0,
                       (cam_y + view_h) // TILE_SIZE + 2)

        for ry in range(start_ty, end_ty):
            for rx in range(start_tx, end_tx):
                if ry < len(self._tilemap) and rx < len(self._tilemap[ry]):
                    tile = self._tilemap[ry][rx]
                    px = rx * TILE_SIZE - cam_x
                    py = ry * TILE_SIZE - cam_y
                    _render_tile(surf, f, tile, px, py, corruption_stage)

        # Draw player
        px = int(self._player.px) - cam_x - TILE_SIZE // 2
        py = int(self._player.py) - cam_y - TILE_SIZE // 2
        # Player glow
        glow = pygame.Surface((TILE_SIZE + 6, TILE_SIZE + 6), pygame.SRCALPHA)
        glow.fill((50, 44, 0, 25))
        surf.blit(glow, (px - 3, py - 3))
        # Player character
        img = f.render("@", True, YELLOW)
        cx = px + (TILE_SIZE - img.get_width()) // 2
        cy = py + (TILE_SIZE - img.get_height()) // 2
        surf.blit(img, (cx, cy))

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
            self._next_scene = "ending"

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _load_area(self, area):
        raw  = MAPS.get(area, MAPS[AREA_GARDEN])
        self._tilemap = [list(row) for row in raw]
        sx, sy = 1, 1
        for ry, row in enumerate(self._tilemap):
            for rx, tile in enumerate(row):
                if tile == 'S':
                    sx, sy = rx, ry
                    self._tilemap[ry][rx] = '.'
        self._player = OWPlayer(sx, sy)
        self._frag_collected = False

    def _replace_tile(self, old, new):
        py, px_coord = self._player.ty, self._player.tx
        if (0 <= py < len(self._tilemap) and
                0 <= px_coord < len(self._tilemap[py])):
            if self._tilemap[py][px_coord] == old:
                self._tilemap[py][px_coord] = new
