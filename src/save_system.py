"""Save / Load system – JSON file on disk."""

import json, os, datetime

SAVE_FILE = "lsoh_save.json"


def new_save():
    return {
        "death_count":   0,
        "kills":         0,
        "spares":        0,
        "area":          "garden",
        "chapter":       0,
        "player_hp":     20,
        "player_max_hp": 20,
        "player_atk":    5,
        "player_def":    2,
        "player_lv":     1,
        "player_exp":    0,
        "corruption":    0,        # 0-100
        "items":         ["Monster Candy", "Monster Candy"],
        "memory_frags":  0,        # 0-8 → golden ending
        "has_locket":    False,
        "route":         "neutral",
        "endings":       [],
        "flags":         {},
        "save_date":     datetime.datetime.now().strftime("%Y-%m-%d"),
        "ng_plus":       False,
    }


def save_game(data):
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_game():
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE) as f:
            return json.load(f)
    except Exception:
        return None   # corrupted


def delete_save():
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)
