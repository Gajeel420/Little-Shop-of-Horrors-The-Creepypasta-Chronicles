"""
Enemy and boss definitions.
Each entity carries: stats, dialogue, ACT options, bullet-pattern list.
"""

import random
from constants import *
from bullets import PATTERNS


# ── Base Enemy ────────────────────────────────────────────────────────────────

class Enemy:
    def __init__(self, name, hp, atk, defense, xp, gold,
                 mercy_threshold, acts, patterns,
                 intro_lines, hurt_lines, spare_lines,
                 area=AREA_GARDEN, is_boss=False,
                 ascii_art=None, color=WHITE):
        self.name             = name
        self.max_hp           = hp
        self.hp               = hp
        self.atk              = atk
        self.defense          = defense
        self.xp               = xp
        self.gold             = gold
        self.mercy            = 0          # 0-100, spare at 100
        self.mercy_threshold  = mercy_threshold
        self.acts             = acts       # list of (label, desc, mercy_gain, effect_fn)
        self.patterns         = patterns   # list of pattern-name strings
        self.intro_lines      = intro_lines
        self.hurt_lines       = hurt_lines
        self.spare_lines      = spare_lines
        self.area             = area
        self.is_boss          = is_boss
        self.ascii_art        = ascii_art or DEFAULT_ART
        self.color            = color
        self.phase            = 0
        self.alive            = True
        self._act_results     = {}   # filled in by subclass or factory

    def current_pattern(self):
        idx = min(self.phase, len(self.patterns) - 1)
        return PATTERNS[self.patterns[idx]]

    def take_damage(self, dmg):
        actual = max(0, dmg - self.defense)
        self.hp = max(0, self.hp - actual)
        if self.hp <= 0:
            self.alive = False
        return actual

    def is_spareable(self):
        return self.mercy >= self.mercy_threshold

    def add_mercy(self, amount):
        self.mercy = min(100, self.mercy + amount)

    def hurt_line(self):
        return random.choice(self.hurt_lines)

    def intro_line(self):
        return random.choice(self.intro_lines)

    def hp_fraction(self):
        return self.hp / self.max_hp


DEFAULT_ART = [
    "  ???  ",
    " [   ] ",
    "  ---  ",
]


# ── Helper to build act-effect dicts ─────────────────────────────────────────

def _act(label, desc, mercy, fn=None):
    """fn(enemy, gs) → dialogue string"""
    return {"label": label, "desc": desc, "mercy": mercy, "fn": fn}


# ── Area 1: The Withering Garden ──────────────────────────────────────────────

def make_corrupted_succulent():
    return Enemy(
        name="Corrupted Succulent",
        hp=14, atk=4, defense=0, xp=8, gold=3,
        mercy_threshold=100,
        acts=[
            _act("Inspect",   "It looks… thirsty.",   10),
            _act("Water It",  "You offer water.  It wilts further.",  30,
                 lambda e, g: "The succulent looks confused."),
            _act("Prune",     "Snip the rotten bits.", 60,
                 lambda e, g: "It lets out a small sigh of relief."),
        ],
        patterns=["thorn_burst", "thorn_rain"],
        intro_lines=[
            "A plant-thing blocks your path.  Its thorns are… wrong.",
            "The succulent stares.  Plants don't stare.",
        ],
        hurt_lines=[
            "It shudders.",
            "Dark sap leaks out.",
            "It hisses.",
        ],
        spare_lines=[
            "You spare the Corrupted Succulent.  It wilts quietly.",
            "It folds its thorns inward.  Gone.",
        ],
        area=AREA_GARDEN,
        ascii_art=[
            "   ,  ,   ",
            "  /|  |\\ ",
            " ( \\  / )",
            "  \\/__\\/ ",
            " [_pot__] ",
        ],
        color=THORN,
    )


def make_tooth_golem():
    return Enemy(
        name="Tooth Golem",
        hp=18, atk=5, defense=1, xp=12, gold=4,
        mercy_threshold=100,
        acts=[
            _act("Check",    "LV 2.  ATK 5.  DEF 1.",  0),
            _act("Rattle",   "You shake a tin can.",    20,
                 lambda e, g: "It stops to listen."),
            _act("Floss It", "You mime flossing.",       50,
                 lambda e, g: "The Tooth Golem looks mortified."),
            _act("Praise",   "Good dental hygiene!",     30,
                 lambda e, g: "It beams with pride.  Ow."),
        ],
        patterns=["tooth_volley"],
        intro_lines=[
            "A golem made of human teeth.  It clacks angrily.",
            "\"BRUSH,\" it seems to say.  \"BRUSH.\"",
        ],
        hurt_lines=["Teeth scatter.", "It roars.", "Enamel cracks."],
        spare_lines=[
            "Tooth Golem crumbles into a pile of surprisingly clean teeth.",
        ],
        area=AREA_GARDEN,
        ascii_art=[
            " /TTTTT\\ ",
            "|T T T T|",
            "|_______|",
            "  |   |  ",
            " _|_ _|_ ",
        ],
        color=WHITE,
    )


def make_shadow_stalker():
    return Enemy(
        name="Shadow Stalker",
        hp=20, atk=6, defense=2, xp=15, gold=5,
        mercy_threshold=100,
        acts=[
            _act("Check",       "LV 3.  ATK 6.  DEF 2.",  0),
            _act("Shine Light", "You turn on your phone screen.", 40,
                 lambda e, g: "It recoils.  \"...you weren't supposed to have that.\""),
            _act("Name It",     "\"I see you.\"",          60,
                 lambda e, g: "Being seen changes something in it."),
        ],
        patterns=["shadow_teleport", "thorn_burst"],
        intro_lines=[
            "Something is definitely standing behind you.",
            "You can't look directly at it.  Your eyes slide off.",
        ],
        hurt_lines=[
            "It flickers.",
            "\"...how.\"",
            "Its outline blurs.",
        ],
        spare_lines=[
            "You acknowledge the Shadow Stalker.  Seen, it fades.",
        ],
        area=AREA_GARDEN,
        ascii_art=[
            "  /###\\  ",
            " | ### | ",
            " | ??? | ",
            "  \\###/  ",
            "   |||   ",
        ],
        color=(30, 0, 30),
    )


# ── Area 2: The Consumption District ─────────────────────────────────────────

def make_contract_wraith():
    return Enemy(
        name="Contract Wraith",
        hp=22, atk=6, defense=1, xp=18, gold=6,
        mercy_threshold=100,
        acts=[
            _act("Check",        "LV 4.  ATK 6.  DEF 1.", 0),
            _act("Read Contract","You skim the fine print.", 25,
                 lambda e, g: "You find your save date in clause 47.\n\"That's... impossible.\""),
            _act("Refuse Sign",  "You decline politely.",  50,
                 lambda e, g: "It wavers.  No signature, no power."),
            _act("Burn Contract","You mime burning paper.", 25,
                 lambda e, g: "\"THAT DOCUMENT IS LEGALLY BINDING!\""),
        ],
        patterns=["contract_cascade", "patrick_contracts"],
        intro_lines=[
            "A writhing mass of fine-print paper.",
            f"Clause 1: the player shall not escape.",
        ],
        hurt_lines=[
            "Pages scatter.",
            "\"BREACH OF CONTRACT!\"",
            "It rustles furiously.",
        ],
        spare_lines=[
            "You void the Contract Wraith's agreement.  It dissolves.",
        ],
        area=AREA_CONSUMPTION,
        ascii_art=[
            "  ~~~~~  ",
            " ~[doc]~ ",
            "  ~~~~~  ",
            " ~sign?~ ",
            "  ~~~~~  ",
        ],
        color=CREAM,
    )


def make_void_tendril():
    return Enemy(
        name="Void Tendril",
        hp=28, atk=8, defense=3, xp=22, gold=7,
        mercy_threshold=100,
        acts=[
            _act("Check",    "LV 5.  ATK 8.  DEF 3.", 0),
            _act("Sever",    "You try to cut it.",    20,
                 lambda e, g: "It regrows but looks impressed."),
            _act("Speak",    "\"What are you?\"",     40,
                 lambda e, g: "A long pause.  Then: \"...hungry.\""),
            _act("Feed Memory", "You share a thought.", 40,
                 lambda e, g: "It recoils from the warmth."),
        ],
        patterns=["void_grab", "shadow_teleport"],
        intro_lines=[
            "A tendril of pure darkness probes the air.",
            "It reaches for you.  Or something inside you.",
        ],
        hurt_lines=["It retracts.", "\"...pain?\"", "The darkness ripples."],
        spare_lines=["The Void Tendril pulls back into its tear and seals it."],
        area=AREA_DARKNESS,
        ascii_art=[
            "   |||   ",
            "  /|||\\ ",
            " ( ||| )",
            "  \\|||/ ",
            "   vvv   ",
        ],
        color=PURPLE,
    )


# ── Boss 1: Orin Scrivello ────────────────────────────────────────────────────

def make_orin():
    e = Enemy(
        name="Orin Scrivello DDS",
        hp=120, atk=8, defense=3, xp=80, gold=20,
        mercy_threshold=100,
        acts=[
            _act("Check",       "LV 8.  ATK 8.  DEF 3.", 0),
            _act("Dodge Drill", "You sidestep the drill.", 15,
                 lambda e, g: "\"Hold STILL!\""),
            _act("Flatter",     "\"Nice gas mask.\"",       25,
                 lambda e, g: "He preens.  His guard drops."),
            _act("Gaslight",    "\"You are the patient now.\"", 20,
                 lambda e, g: "He looks genuinely confused."),
            _act("Name Patient","\"Seymour sends his regards.\"", 40,
                 lambda e, g: "He freezes.  \"...Seymour?\""),
        ],
        patterns=["orin_drill", "orin_gas", "orin_tools"],
        intro_lines=[
            "ORIN SCRIVELLO emerges from the dark.\n\"Open wide, Seymour.\"",
            "\"I've been waiting for you.\"\nHis drill revs.",
        ],
        hurt_lines=[
            "\"INSOLENT PATIENT!\"",
            "He spits teeth.",
            "The drill sparks.",
            "\"You'll regret that.\"",
        ],
        spare_lines=[
            "Orin lowers his drill slowly.\n\"...I remember what I was.\"",
            "He crumbles.  Not destroyed – just… done.",
        ],
        area=AREA_GARDEN,
        is_boss=True,
        ascii_art=[
            "  [####]  ",
            " [o    o] ",
            " [  ++  ] ",
            " [ /--\\ ] ",
            "  [####]  ",
        ],
        color=GRAY,
    )
    e.phase_thresholds = [0.70, 0.40]   # phase 1 at 70%, phase 2 at 40%
    return e


# ── Boss 2: Patrick Martin ────────────────────────────────────────────────────

def make_patrick():
    e = Enemy(
        name="Patrick Martin",
        hp=160, atk=10, defense=4, xp=120, gold=30,
        mercy_threshold=100,
        acts=[
            _act("Check",       "LV 10.  ATK 10.  DEF 4.", 0),
            _act("Read Fine Print", "You actually read his contract.", 30,
                 lambda e, g: (
                     f"Clause 9: Player save started {g.save_date}.\n"
                     "\"H-how do you know that?\""
                 )),
            _act("Refuse",      "\"I'm not buying what you're selling.\"", 30,
                 lambda e, g: "He flickers.  Salesmen need customers."),
            _act("Counter-Offer","\"Here's MY deal.\"", 40,
                 lambda e, g: "He has no response.  The script is gone."),
        ],
        patterns=["patrick_clones", "patrick_contracts"],
        intro_lines=[
            "PATRICK MARTIN, Salesman Supreme.\n\"Have I got a deal for YOU.\"",
            "He smiles.  Too many teeth.\n\"Sign here.  And here.  And everywhere.\"",
        ],
        hurt_lines=[
            "\"That's not how negotiation works!\"",
            "A clone pops.",
            "\"Pain clause not included!\"",
            "He straightens his tie.",
        ],
        spare_lines=[
            "Patrick's smile finally breaks.\n\"I just wanted to matter.\"",
        ],
        area=AREA_CONSUMPTION,
        is_boss=True,
        ascii_art=[
            "  (====)  ",
            " ( o  o ) ",
            " (  __  ) ",
            "  (====)  ",
            "  /|  |\\  ",
        ],
        color=MAGENTA,
    )
    e.phase_thresholds = [0.65, 0.35]
    return e


# ── Boss 3: Audrey II ─────────────────────────────────────────────────────────

def make_audrey_ii(gs=None):
    deaths = gs.deaths if gs else 0
    frags  = gs.memory_frags if gs else 0
    save_date = gs.save_date if gs else "unknown"

    e = Enemy(
        name="Audrey II",
        hp=240, atk=14, defense=5, xp=300, gold=0,
        mercy_threshold=100,
        acts=[
            _act("Check",     "LV ???.  It defies measurement.", 0),
            _act("Refuse",    "\"I won't feed you.\"", 30,
                 lambda e, g: "\"SEYMOUR.  You've said that before.\""),
            _act("Remember",  "You think of Audrey.",  40,
                 lambda e, g: "The plant flinches.  A real flinch."),
            _act("Locket",    "You hold out the locket.", 100,
                 lambda e, g: (
                     "Audrey II freezes.\n\"Where did you find that?\""
                     if g.has_locket
                     else "You reach for something that isn't there."
                 )),
        ],
        patterns=["audrey_bite", "audrey_vine_sweep", "audrey_spores", "audrey_memory"],
        intro_lines=[
            f"FEED ME SEYMOUR.\n(You have died {deaths} times.  It remembers.)",
            "The plant has grown through the ceiling, the walls, the sky.\n"
            "\"There is no Seymour.  There is only the hunger.\"",
        ],
        hurt_lines=[
            "\"THAT TICKLES.\"",
            f"\"You've done this {deaths} times, Seymour.\"",
            "It bleeds something green and luminous.",
            "\"THE MORE YOU FIGHT THE HUNGRIER I GET.\"",
        ],
        spare_lines=[
            "Audrey II goes still.\n\"...is it over?\"",
        ],
        area=AREA_DARKNESS,
        is_boss=True,
        ascii_art=[
            " /||||||\\",
            "| O    O |",
            "|  \\--/  |",
            " \\______/",
            "   ||||  ",
        ],
        color=LEAF_GREEN,
    )
    e.phase_thresholds = [0.65, 0.30]
    e.memory_frags_collected = frags
    return e


# ── Enemy pool by area ────────────────────────────────────────────────────────

def get_random_enemy(area):
    pools = {
        AREA_GARDEN:      [make_corrupted_succulent, make_tooth_golem, make_shadow_stalker],
        AREA_CONSUMPTION: [make_contract_wraith, make_shadow_stalker],
        AREA_DARKNESS:    [make_void_tendril, make_contract_wraith],
    }
    makers = pools.get(area, pools[AREA_GARDEN])
    return random.choice(makers)()


def get_boss(area, gs=None):
    bosses = {
        AREA_GARDEN:      make_orin,
        AREA_CONSUMPTION: make_patrick,
        AREA_DARKNESS:    lambda: make_audrey_ii(gs),
    }
    fn = bosses.get(area)
    return fn() if fn else None
