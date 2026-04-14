"""Global game state – wraps the save dict with helper methods."""

from constants import *
from save_system import new_save, save_game, load_game


class GameState:
    def __init__(self):
        data = load_game() or new_save()
        self.d = data
        self._update_route()

    # ── Simple property aliases ───────────────────────────────────────────────
    @property
    def area(self):          return self.d["area"]
    @area.setter
    def area(self, v):       self.d["area"] = v

    @property
    def chapter(self):       return self.d["chapter"]
    @chapter.setter
    def chapter(self, v):    self.d["chapter"] = v

    @property
    def hp(self):            return self.d["player_hp"]
    @hp.setter
    def hp(self, v):         self.d["player_hp"] = max(0, min(int(v), self.max_hp))

    @property
    def max_hp(self):        return self.d["player_max_hp"]
    @max_hp.setter
    def max_hp(self, v):     self.d["player_max_hp"] = int(v)

    @property
    def atk(self):           return self.d["player_atk"]
    @property
    def defense(self):       return self.d["player_def"]
    @property
    def lv(self):            return self.d["player_lv"]
    @property
    def exp(self):           return self.d["player_exp"]
    @property
    def kills(self):         return self.d["kills"]
    @property
    def spares(self):        return self.d["spares"]
    @property
    def deaths(self):        return self.d["death_count"]
    @property
    def corruption(self):    return self.d["corruption"]
    @property
    def memory_frags(self):  return self.d["memory_frags"]
    @property
    def has_locket(self):    return self.d["has_locket"]
    @property
    def items(self):         return self.d["items"]
    @property
    def save_date(self):     return self.d["save_date"]
    @property
    def ng_plus(self):       return self.d["ng_plus"]
    @property
    def route(self):         return self.d["route"]
    @property
    def flags(self):         return self.d["flags"]

    # ── Mutation helpers ──────────────────────────────────────────────────────
    def add_kill(self):
        self.d["kills"] += 1
        self.d["corruption"] = min(100, self.d["corruption"] + 5)
        self._give_exp(20)
        self._update_route()

    def add_spare(self):
        self.d["spares"] += 1
        self.d["corruption"] = max(0, self.d["corruption"] - 2)
        self._give_exp(10)
        self._update_route()

    def add_death(self):
        self.d["death_count"] += 1
        self.d["corruption"] = min(100, self.d["corruption"] + 3)

    def add_memory_frag(self):
        if self.d["memory_frags"] < 8:
            self.d["memory_frags"] += 1
        if self.d["memory_frags"] >= 8:
            self.d["has_locket"] = True

    def set_flag(self, key, val=True):
        self.d["flags"][key] = val

    def get_flag(self, key, default=False):
        return self.d["flags"].get(key, default)

    def heal(self, amount):
        self.hp = self.hp + amount

    def take_damage(self, raw):
        actual = max(1, raw - self.defense)
        self.hp = self.hp - actual
        return actual

    def add_item(self, name):
        self.d["items"].append(name)

    def use_item(self, name):
        if name in self.d["items"]:
            self.d["items"].remove(name)
            return True
        return False

    def unlock_ending(self, e):
        if e not in self.d["endings"]:
            self.d["endings"].append(e)

    def save(self):
        save_game(self.d)

    # ── Derived helpers ───────────────────────────────────────────────────────
    def corruption_stage(self):
        c = self.corruption
        if c < 25: return 0
        if c < 50: return 1
        if c < 75: return 2
        return 3

    def _give_exp(self, amount):
        self.d["player_exp"] += amount
        self._check_level_up()

    def _check_level_up(self):
        while self.d["player_lv"] < len(LEVEL_EXP) - 1:
            needed = LEVEL_EXP[self.d["player_lv"]]
            if self.d["player_exp"] >= needed:
                self.d["player_lv"] += 1
                self.d["player_max_hp"] += LEVEL_HP_BONUS
                self.d["player_hp"] = self.d["player_max_hp"]
                self.d["player_atk"] += LEVEL_ATK_BONUS
            else:
                break

    def _update_route(self):
        k = self.d["kills"]
        if k == 0:
            self.d["route"] = ROUTE_PACIFIST
        elif k >= 10:
            self.d["route"] = ROUTE_GENOCIDE
        else:
            self.d["route"] = ROUTE_NEUTRAL

    def next_level_exp(self):
        lv = self.d["player_lv"]
        if lv >= len(LEVEL_EXP) - 1:
            return self.d["player_exp"]
        return LEVEL_EXP[lv]
