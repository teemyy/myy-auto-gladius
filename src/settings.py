SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS           = 60
TITLE         = "Myy Auto Gladius"

# ── Colors ──────────────────────────────────────────────────────────────────
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
DARK_BG    = ( 15,  10,   8)
PANEL_BG   = ( 30,  22,  18)
GOLD_TEXT  = (220, 175,  60)
RED        = (200,  50,  50)
GREEN      = ( 50, 180,  80)
GRAY       = (120, 120, 120)
DARK_GRAY  = ( 55,  55,  55)
BLUE       = ( 60, 120, 200)

# ── Game constants ───────────────────────────────────────────────────────────
TOTAL_STAGES       = 12
BOSS_STAGES        = (4, 8, 12)

# Player starting stats
PLAYER_START_HP      = 120
PLAYER_START_STAMINA = 100
PLAYER_START_GOLD    = 80
PLAYER_START_STR     = 10   # strength:  damage bonus + physical damage reduction
PLAYER_START_AGI     = 10   # agility:   crit chance % + evasion chance %

# Limbs
LIMBS            = ("Head", "Torso", "L-Arm", "R-Arm", "L-Leg", "R-Leg")
MAX_INTEGRITY    = 100

# Stamina change per action: negative = consumed, positive = regenerated
STAMINA_DELTA = {
    "Heavy":  -20,
    "Quick":  -10,
    "Defend": +25,   # Defend restores stamina
    "Ranged":  -8,
}

# Equipment grades in ascending order
WEAPON_GRADES = ("Iron", "Steel", "Mithril", "Adamantite", "Draconic")
ARMOR_TYPES   = ("Cloth", "Leather", "Scale", "Chainmail", "Plate")
