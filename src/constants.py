"""
Little Shop of Horrors: The Creepypasta Chronicles
Constants and Configuration
"""

# ── Display ──────────────────────────────────────────────────────────────────
SCREEN_W   = 640
SCREEN_H   = 480
SCALE      = 2          # pixel-art upscale factor (renders at 640x480, displays at 1280x960)
FPS        = 60
GAME_TITLE = "Little Shop of Horrors: The Creepypasta Chronicles"

# ── Color Palette ────────────────────────────────────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
YELLOW     = (255, 220,   0)   # SOUL / menu cursor
RED        = (220,  20,  20)   # damage / danger
DARK_RED   = ( 80,   0,   0)
GREEN      = ( 40, 180,  40)   # HP bar (healthy)
DARK_GREEN = (  0,  60,   0)
LEAF_GREEN = (100, 200,  60)   # plant/Audrey attacks
CYAN       = (  0, 200, 200)   # frost / ice
ORANGE     = (230, 120,   0)   # fire attacks
PURPLE     = (130,   0, 190)   # dark magic / void
MAGENTA    = (200,   0, 140)   # corporate / Patrick
GRAY       = (130, 130, 130)
DARK_GRAY  = ( 28,  28,  28)
DIM        = ( 55,  55,  55)
CREAM      = (240, 215, 160)   # warm UI text
BLOOD      = (150,   0,   0)   # genocide tint
THORN      = ( 60, 100,  30)   # thorn bullets
GOLD       = (255, 200,  50)   # golden items / locket

# ── Battle Box (inner dimensions) ────────────────────────────────────────────
BBOX_X, BBOX_Y = 196, 165
BBOX_W, BBOX_H = 248, 175
BBOX_BORDER    = 3

# ── Soul / Player ─────────────────────────────────────────────────────────────
SOUL_SPEED  = 180        # pixels per second
SOUL_R      = 6          # collision radius
SOUL_COLOR  = (255, 220, 0)   # same as YELLOW; explicit alias used in UI
INV_TIME    = 1.5        # invincibility seconds after a hit

# ── Base Stats ────────────────────────────────────────────────────────────────
BASE_HP  = 20
BASE_ATK = 5
BASE_DEF = 2

# EXP thresholds for LV 1-10
LEVEL_EXP       = [0, 50, 120, 210, 320, 450, 620, 830, 1090, 1400, 9999]
LEVEL_HP_BONUS  = 4
LEVEL_ATK_BONUS = 1

# ── Areas ─────────────────────────────────────────────────────────────────────
AREA_GARDEN      = "garden"
AREA_CONSUMPTION = "consumption"
AREA_DARKNESS    = "darkness"

# ── Battle States ─────────────────────────────────────────────────────────────
BS_MENU    = "menu"
BS_FIGHT   = "fight"
BS_ACT     = "act"
BS_ITEM    = "item"
BS_MERCY   = "mercy"
BS_DODGE   = "dodge"
BS_TALKING = "talking"
BS_VICTORY = "victory"
BS_DEFEAT  = "defeat"
BS_SPARE   = "spare"
BS_LEVELUP = "levelup"

M_FIGHT = 0
M_ACT   = 1
M_ITEM  = 2
M_MERCY = 3

# ── Routes & Endings ──────────────────────────────────────────────────────────
ROUTE_PACIFIST = "pacifist"
ROUTE_NEUTRAL  = "neutral"
ROUTE_GENOCIDE = "genocide"

END_TRUE   = "true"     # self-sacrifice, spare everything
END_DARK   = "dark"     # genocide
END_NORMAL = "normal"   # neutral / kill Audrey
END_GOLDEN = "golden"   # all 8 memory fragments + locket

# ── Creepypasta Messages ──────────────────────────────────────────────────────
CREEPY_MSGS = [
    "YOU SHOULD NOT BE HERE.",
    "how many times have you let them die?",
    "SEYMOUR...  why do you keep running?",
    "your save file is hungry.",
    "DO NOT TURN AROUND.",
    "it knows your name.",
    "have you tried being a COWARD?",
    "the plant remembers every death.",
    "you cannot save them all.",
    "WHY WON'T YOU JUST FEED IT?",
    "he's right behind you.",
    "[MEMORY FRAGMENT CORRUPTED]",
    "this town died a long time ago.",
    "FEED.  ME.  SEYMOUR.",
    "there is no pacifist route here.",
    "the flowers are not flowers.",
    "turn back.   TURN BACK.",
]
