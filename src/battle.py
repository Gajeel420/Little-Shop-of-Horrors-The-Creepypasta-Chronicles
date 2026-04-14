"""
Battle scene – Undertale-style turn-based combat with bullet-dodge phase.

State machine:
  BS_TALKING  → dialogue, then → BS_MENU
  BS_MENU     → player picks FIGHT / ACT / ITEM / MERCY
  BS_FIGHT    → slider mini-game → BS_DODGE
  BS_ACT      → sub-menu picks act → BS_TALKING → BS_DODGE
  BS_ITEM     → sub-menu picks item → heal → BS_DODGE
  BS_MERCY    → spare (if ready) or flee
  BS_DODGE    → bullet phase; SOUL dodges; ends → BS_TALKING / BS_MENU
  BS_SPARE    → enemy spared animation → return to overworld
  BS_VICTORY  → enemy defeated animation → return to overworld
  BS_DEFEAT   → GAME OVER screen
  BS_LEVELUP  → short level-up display → BS_MENU
"""

import pygame
import random
import math
from constants import *
from soul      import Soul
from bullets   import Bullet
from dialogue  import DialogueBox
from ui        import (
    init_fonts, font, draw_text, draw_box, draw_hp_bar,
    draw_battle_box, draw_enemy_sprite, draw_battle_hud,
    draw_main_menu, draw_sub_menu, draw_fight_slider,
    DIALOGUE_AREA_H, MENU_AREA_H
)
from effects import ScreenShake, apply_corruption_tint, apply_scanlines, glitch_text


# ── Battle constants ──────────────────────────────────────────────────────────

DODGE_DURATION  = 5.0   # seconds of bullet phase per turn
PATTERN_INTERVAL = 1.6  # seconds between bullet spawns
SLIDER_SPEED    = 1.4   # oscillations per second


class BattleScene:
    def __init__(self, gs, enemy):
        self.gs    = gs
        self.enemy = enemy

        # Layout rects
        self.box_rect = pygame.Rect(BBOX_X, BBOX_Y, BBOX_W, BBOX_H)
        self.dlg_rect = pygame.Rect(
            0, SCREEN_H - DIALOGUE_AREA_H - MENU_AREA_H,
            SCREEN_W, DIALOGUE_AREA_H
        )

        self.soul   = Soul(self.box_rect)
        self.soul.set_corruption(gs.corruption)

        self.dlg    = DialogueBox(font("md"), self.dlg_rect)
        self.shake  = ScreenShake()

        # State
        self.state        = BS_TALKING
        self.menu_idx     = M_FIGHT
        self.sub_idx      = 0
        self.sub_items    = []

        # Dodge phase
        self.bullets          = []
        self.dodge_timer      = 0.0
        self.pattern_timer    = 0.0
        self.dodge_dmg_dealt  = 0   # total damage taken this dodge phase

        # Fight slider
        self.slider_t      = 0.0
        self.slider_dir    = 1
        self.slider_active = False
        self._slider_sweet = None   # set each frame

        # Outcome
        self._next_scene = None   # "overworld", "gameover"
        self._outcome    = None   # "victory", "spare", "flee", "defeat"
        self._level_before = gs.lv

        # Start with intro dialogue
        intro = enemy.intro_line()
        self.dlg.push(intro)

        # Boss phase tracking
        self._phase_warned = [False] * 3

    # ── Scene interface ────────────────────────────────────────────────────────

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        key = event.key
        confirm = key in (pygame.K_z, pygame.K_RETURN, pygame.K_SPACE)
        cancel  = key in (pygame.K_x, pygame.K_ESCAPE)
        up      = key == pygame.K_UP
        down    = key == pygame.K_DOWN
        left    = key == pygame.K_LEFT
        right   = key == pygame.K_RIGHT

        # ── Talking state: advance dialogue ─────────────────
        if self.state == BS_TALKING:
            if confirm:
                if self.dlg.ready():
                    self._after_talking()
                else:
                    self.dlg.advance()
            return

        # ── Main menu navigation ─────────────────────────────
        if self.state == BS_MENU:
            if left:
                self.menu_idx = (self.menu_idx - 1) % 4
            elif right:
                self.menu_idx = (self.menu_idx + 1) % 4
            elif confirm:
                self._select_menu(self.menu_idx)
            return

        # ── Fight slider ──────────────────────────────────────
        if self.state == BS_FIGHT:
            if confirm:
                self._resolve_fight()
            return

        # ── ACT sub-menu ──────────────────────────────────────
        if self.state == BS_ACT:
            if up:
                self.sub_idx = (self.sub_idx - 1) % len(self.sub_items)
            elif down:
                self.sub_idx = (self.sub_idx + 1) % len(self.sub_items)
            elif confirm:
                self._resolve_act(self.sub_idx)
            elif cancel:
                self.state = BS_MENU
            return

        # ── ITEM sub-menu ─────────────────────────────────────
        if self.state == BS_ITEM:
            if up:
                self.sub_idx = (self.sub_idx - 1) % max(1, len(self.sub_items))
            elif down:
                self.sub_idx = (self.sub_idx + 1) % max(1, len(self.sub_items))
            elif confirm:
                self._resolve_item(self.sub_idx)
            elif cancel:
                self.state = BS_MENU
            return

        # ── MERCY sub-menu ────────────────────────────────────
        if self.state == BS_MERCY:
            if up:
                self.sub_idx = (self.sub_idx - 1) % len(self.sub_items)
            elif down:
                self.sub_idx = (self.sub_idx + 1) % len(self.sub_items)
            elif confirm:
                self._resolve_mercy(self.sub_idx)
            elif cancel:
                self.state = BS_MENU
            return

        # ── Defeat / victory ──────────────────────────────────
        if self.state in (BS_DEFEAT, BS_VICTORY, BS_SPARE):
            if confirm:
                self._next_scene = "overworld" if self.state != BS_DEFEAT else "gameover"

        # ── Level up ─────────────────────────────────────────
        if self.state == BS_LEVELUP:
            if confirm:
                self.state = BS_MENU

    def update(self, dt):
        self.shake.update(dt)

        if self.state == BS_TALKING:
            self.dlg.update(dt)

        elif self.state == BS_FIGHT:
            # Animate slider
            self.slider_t += SLIDER_SPEED * self.slider_dir * dt * 2
            if self.slider_t >= 1.0:
                self.slider_t = 1.0
                self.slider_dir = -1
            elif self.slider_t <= 0.0:
                self.slider_t = 0.0
                self.slider_dir = 1

        elif self.state == BS_DODGE:
            self._update_dodge(dt)

        elif self.state == BS_SPARE:
            self.dlg.update(dt)

        # Check boss phase transitions
        if self.enemy.is_boss and self.state not in (BS_VICTORY, BS_SPARE, BS_DEFEAT):
            self._check_boss_phase()

    def draw(self, surf: pygame.Surface):
        surf.fill(BLACK)
        cs = self.gs.corruption_stage()
        apply_corruption_tint(surf, cs)

        # Enemy sprite (top area)
        enemy_center_x = SCREEN_W // 2
        sprite_top_y   = 70
        enemy_color = self.enemy.color
        if self.state == BS_DODGE and self.dodge_timer > DODGE_DURATION - 0.5:
            # Flash enemy at end of dodge phase
            pass
        draw_enemy_sprite(surf, self.enemy.ascii_art,
                          enemy_center_x, sprite_top_y, color=enemy_color)

        # HUD
        draw_battle_hud(surf, self.enemy, self.gs.hp, self.gs.max_hp, self.gs.lv)

        # ── State-specific rendering ──
        if self.state in (BS_DODGE,):
            draw_battle_box(surf, self.box_rect)
            self.soul.draw(surf)
            for b in self.bullets:
                b.draw(surf)
            # Dodge timer bar
            frac  = max(0, self.dodge_timer / DODGE_DURATION)
            tbar  = pygame.Rect(BBOX_X, BBOX_Y + BBOX_H + 6, BBOX_W, 4)
            pygame.draw.rect(surf, DARK_GRAY, tbar)
            pygame.draw.rect(surf, CYAN,
                             pygame.Rect(tbar.left, tbar.top,
                                         int(tbar.width * frac), tbar.height))

        elif self.state == BS_FIGHT:
            self._slider_sweet = draw_fight_slider(surf, self.slider_t)

        elif self.state in (BS_TALKING, BS_VICTORY, BS_SPARE):
            self.dlg.draw(surf)
            if self.state != BS_TALKING:
                draw_text(surf, "[ Press Z to continue ]",
                          (SCREEN_W // 2, SCREEN_H - 20), GRAY, size="sm", center=True)

        elif self.state == BS_DEFEAT:
            _draw_game_over(surf)

        elif self.state == BS_LEVELUP:
            _draw_level_up(surf, self.gs)

        # Menus
        if self.state == BS_MENU:
            draw_main_menu(surf, self.menu_idx)
        elif self.state == BS_ACT:
            draw_sub_menu(surf, self.sub_items, self.sub_idx, title="* ACT")
        elif self.state == BS_ITEM:
            draw_sub_menu(surf, self.sub_items, self.sub_idx, title="* ITEM")
        elif self.state == BS_MERCY:
            draw_sub_menu(surf, self.sub_items, self.sub_idx, title="* MERCY")

        # Screen shake offset applied by main loop via shake.offset()
        apply_scanlines(surf, alpha=18)

    def next_scene(self):
        return self._next_scene

    def outcome(self):
        return self._outcome

    # ── Menu resolution ───────────────────────────────────────────────────────

    def _select_menu(self, idx):
        if idx == M_FIGHT:
            self.state        = BS_FIGHT
            self.slider_t     = 0.0
            self.slider_dir   = 1

        elif idx == M_ACT:
            self.sub_items = self.enemy.acts
            self.sub_idx   = 0
            self.state     = BS_ACT

        elif idx == M_ITEM:
            items = self.gs.items
            self.sub_items = items if items else ["(nothing)"]
            self.sub_idx   = 0
            self.state     = BS_ITEM

        elif idx == M_MERCY:
            opts = []
            if self.enemy.is_spareable():
                opts.append("Spare")
            opts.append("Flee")
            self.sub_items = opts
            self.sub_idx   = 0
            self.state     = BS_MERCY

    # ── FIGHT resolution ──────────────────────────────────────────────────────

    def _resolve_fight(self):
        sweet = self._slider_sweet
        hit_sweet = (sweet is not None and
                     sweet.left / SCREEN_W <= self.slider_t <= sweet.right / SCREEN_W)

        base_atk  = self.gs.atk
        crit_roll = random.random() < 0.10 + (0.05 * self.gs.lv)
        mult = 3.0 if crit_roll else (1.5 if hit_sweet else 1.0)
        dmg  = max(1, int(base_atk * mult) - self.enemy.defense)

        actual = self.enemy.take_damage(dmg)
        self.shake.shake()

        msg = f"You deal {actual} damage!"
        if crit_roll:
            msg += "\n* Critical hit!"
        if hit_sweet:
            msg += "\n* Well-timed!"

        self.gs.d["player_atk"]  # just read to force no-op

        self.dlg.push(msg)
        self.state = BS_TALKING
        self._post_player_action()

    # ── ACT resolution ────────────────────────────────────────────────────────

    def _resolve_act(self, idx):
        act = self.enemy.acts[idx]
        self.enemy.add_mercy(act["mercy"])

        result = ""
        if act.get("fn"):
            result = act["fn"](self.enemy, self.gs) or ""

        lines = [f"* {self.enemy.name}: {result}"] if result else [f"* {act['desc']}"]
        self.dlg.push(lines)
        self.state = BS_TALKING
        self._post_player_action()

    # ── ITEM resolution ───────────────────────────────────────────────────────

    ITEM_EFFECTS = {
        "Monster Candy": (10, "It's sugary and vaguely sentient.  HP +10."),
        "Bandage":       (20, "You patch yourself up.  HP +20."),
        "Thorn Tea":     (30, "Tastes like the garden.  HP +30."),
    }

    def _resolve_item(self, idx):
        items = self.gs.items
        if not items:
            self.state = BS_MENU
            return
        item = items[idx % len(items)]
        heal, msg = self.ITEM_EFFECTS.get(item, (5, f"Used {item}."))
        self.gs.use_item(item)
        self.gs.heal(heal)
        self.dlg.push(msg)
        self.state = BS_TALKING
        self._post_player_action()

    # ── MERCY resolution ──────────────────────────────────────────────────────

    def _resolve_mercy(self, idx):
        choice = self.sub_items[idx]
        if choice == "Spare":
            self._do_spare()
        elif choice == "Flee":
            self._do_flee()

    def _do_spare(self):
        self.gs.add_spare()
        lines = self.enemy.spare_lines or ["You spare them."]
        self.dlg.push(random.choice(lines) if lines else "* You spare it.")
        self.state   = BS_SPARE
        self._outcome = "spare"

    def _do_flee(self):
        self._outcome    = "flee"
        self._next_scene = "overworld"

    # ── Dodge phase ───────────────────────────────────────────────────────────

    def _start_dodge(self):
        self.state          = BS_DODGE
        self.dodge_timer    = DODGE_DURATION
        self.pattern_timer  = 0.0
        self.dodge_dmg_dealt = 0
        self.bullets        = []
        self.soul.reset()
        self.soul.set_corruption(self.gs.corruption)

        # Boss: show talk line during dodge
        hurt = self.enemy.hurt_line()
        self.dlg.push(hurt)

    def _update_dodge(self, dt):
        keys = pygame.key.get_pressed()
        self.soul.update(dt, keys)
        self.dlg.update(dt)

        # Spawn bullet patterns
        self.pattern_timer -= dt
        if self.pattern_timer <= 0:
            self.pattern_timer = PATTERN_INTERVAL
            pattern_fn = self.enemy.current_pattern()
            new_bullets = pattern_fn(self.box_rect, self.soul)
            self.bullets.extend(new_bullets)

        # Update bullets
        for b in self.bullets:
            b.update(dt, self.box_rect)

        # Collision
        soul_rect = self.soul.rect()
        for b in self.bullets:
            if not b.dead and b.collides(soul_rect):
                if self.soul.hit():
                    dmg = self.gs.take_damage(b.atk if hasattr(b, 'atk') else b.damage)
                    self.dodge_dmg_dealt += dmg
                    self.shake.shake(0.15, 3)
                    b.dead = True
                    if self.gs.hp <= 0:
                        self._trigger_defeat()
                        return

        self.bullets = [b for b in self.bullets if not b.dead]

        # Timer
        self.dodge_timer -= dt
        if self.dodge_timer <= 0:
            self._end_dodge()

    def _end_dodge(self):
        self.bullets = []
        if self.dodge_dmg_dealt == 0:
            self.dlg.push("You took no damage!")
        self.state = BS_TALKING

    def _trigger_defeat(self):
        self.state   = BS_DEFEAT
        self._outcome = "defeat"
        self.gs.add_death()
        self.gs.save()

    # ── Post-action routing ───────────────────────────────────────────────────

    def _post_player_action(self):
        """After player acts: check if enemy is dead, else go to dodge."""
        if not self.enemy.alive:
            self._trigger_victory()

    def _after_talking(self):
        """Called when dialogue finishes."""
        if self._outcome == "spare":
            self._next_scene = "overworld"
            return

        if not self.enemy.alive:
            self._trigger_victory()
            return

        if self.state == BS_TALKING:
            # Check if we just finished the intro or an action
            if self.gs.hp > 0 and self.enemy.alive:
                self._start_dodge()

    def _trigger_victory(self):
        self.gs.add_kill()
        lines = [
            f"* {self.enemy.name} was defeated.",
            f"  EXP +{self.enemy.xp}",
        ]
        if self.gs.lv > self._level_before:
            self.state = BS_LEVELUP
        else:
            self.state  = BS_VICTORY
        self.dlg.push(lines)
        self._outcome = "victory"

    # ── Boss phase checks ─────────────────────────────────────────────────────

    def _check_boss_phase(self):
        thresholds = getattr(self.enemy, "phase_thresholds", [])
        for i, t in enumerate(thresholds):
            if (not self._phase_warned[i] and
                    self.enemy.hp_fraction() <= t):
                self._phase_warned[i] = True
                self.enemy.phase = i + 1
                self.dlg.push(f"* {self.enemy.name} enters phase {i+2}!", glitch=(i >= 1))


# ── Stand-alone drawing helpers ───────────────────────────────────────────────

def _draw_game_over(surf):
    surf.fill(BLACK)
    draw_text(surf, "GAME OVER", (SCREEN_W // 2, 180), RED, size="xxl", center=True)
    draw_text(surf, "but it doesn't have to be.",
              (SCREEN_W // 2, 230), GRAY, size="md", center=True)
    draw_text(surf, "Press Z to return.",
              (SCREEN_W // 2, 270), DIM, size="sm", center=True)


def _draw_level_up(surf, gs):
    surf.fill(BLACK)
    draw_text(surf, f"LEVEL UP!  LV {gs.lv}", (SCREEN_W // 2, 170), YELLOW, size="xl", center=True)
    draw_text(surf, f"Max HP  +{LEVEL_HP_BONUS}   →  {gs.max_hp}",
              (SCREEN_W // 2, 210), GREEN, size="md", center=True)
    draw_text(surf, f"ATK  +{LEVEL_ATK_BONUS}   →  {gs.atk}",
              (SCREEN_W // 2, 232), ORANGE, size="md", center=True)
    draw_text(surf, "Press Z to continue.",
              (SCREEN_W // 2, 270), DIM, size="sm", center=True)
