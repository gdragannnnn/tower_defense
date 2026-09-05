#!/usr/bin/env python3

# ADMIN LOGIN – username: admin    password: dominous7

import faulthandler
import pygame, math, random, time, json, os, hashlib

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tower Defense")

# ── Colors ───────────────────────────────────────────────────────────────────
WHITE = (255, 255, 255)
RED = (200, 0, 0)
DARK_RED = (150, 0, 0)
BLUE = (0, 100, 255)
DARK_BLUE = (0, 0, 150)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
DARKGRAY = (100, 100, 100)
ORANGE = (255, 165, 0)
PURPLE = (160, 32, 240)
PINK = (255, 105, 180)
CYAN = (0, 255, 255)
BROWN = (139, 69, 19)
GRAY = (120, 120, 120)
GOLD = (255, 215, 0)
DARK_BG = (50, 130, 60)

clock = pygame.time.Clock()
_ANTON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Anton-Regular.ttf")
if os.path.exists(_ANTON):
    font      = pygame.font.Font(_ANTON, 18)
    font_lg   = pygame.font.Font(_ANTON, 24)
    font_btn  = pygame.font.Font(_ANTON, 24)
    font_start = pygame.font.Font(_ANTON, 22)
    font_arena_wave = pygame.font.Font(_ANTON, 21)
    font_sm   = pygame.font.Font(_ANTON, 15)
    font_shop = pygame.font.Font(_ANTON, 20)
    font_shop_sm = pygame.font.Font(_ANTON, 17)
    font_tiny = pygame.font.Font(_ANTON, 13)
else:
    font      = pygame.font.SysFont("verdana", 18)
    font_lg   = pygame.font.SysFont("verdana", 24)
    font_btn  = pygame.font.SysFont("verdana", 24)
    font_start = pygame.font.SysFont("verdana", 22)
    font_arena_wave = pygame.font.SysFont("verdana", 21)
    font_sm   = pygame.font.SysFont("verdana", 15)
    font_shop = pygame.font.SysFont("verdana", 20)
    font_shop_sm = pygame.font.SysFont("verdana", 17)
    font_tiny = pygame.font.SysFont("verdana", 13)

path = [(0, 300), (200, 300), (200, 500), (600, 500), (600, 100), (WIDTH, 100)]
BOSS_RADIUS = 35


def draw_tower_base(cx, cy, color, angle):
    """Draw a tower base + turret at (cx,cy) facing `angle` (rad).

    Matches actlook.png: pale icy-blue fill, thick dark navy outline, smooth
    edges. Rendered with 3x supersampling and smooth-scaled down so all curves
    and rotations look clean. The `color` parameter still lightly tints the
    body so different tower types remain distinguishable.
    """
    # [118;1:3uGeometry (logical pixels — final output is the same size as before)
    body_w, body_h = 26, 22
    tri_w = 12
    front_r = 5
    barrel_w, barrel_h = 28, 12
    barrel_off_x = body_w // 2 + 14

    # Reference palette from actlook.png: pale icy blue body, dark navy outline
    PALE = (215, 230, 245)
    NAVY = (28, 50, 92)
    base_fill = tuple(min(255, int(PALE[i] * 0.78 + color[i] * 0.22)) for i in range(3))
    edge_col = tuple(max(0, min(255, int(NAVY[i] * 0.7 + (color[i] // 3) * 0.3))) for i in range(3))
    barrel_fill = base_fill

    # Supersample 3x then smoothscale down for clean anti-aliased edges
    SS = 3
    pad = 6
    half = max(barrel_off_x + barrel_h, body_w // 2 + tri_w) + pad
    size = (half * 2) * SS
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    scx = scy = size // 2

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    def rot(px, py):
        return (scx + (px * cos_a - py * sin_a) * SS,
                scy + (px * sin_a + py * cos_a) * SS)

    def rot_i(px, py):
        x, y = rot(px, py)
        return (int(round(x)), int(round(y)))

    OUTLINE_W = 3            # logical outline thickness (will be supersampled)
    ow = OUTLINE_W * SS

    # ── 1. BARREL (capsule). Drawn first so the body covers its back end. ──
    bx0, bx1 = barrel_off_x - barrel_w, barrel_off_x
    bh = barrel_h / 2
    cap_r = int(round(bh * SS))

    # Filled rectangle body of the capsule
    barrel_pts = [rot(bx0, -bh), rot(bx1, -bh), rot(bx1, bh), rot(bx0, bh)]
    pygame.draw.polygon(surf, barrel_fill, barrel_pts)
    # Filled end caps
    front_cap = rot_i(bx1, 0)
    back_cap = rot_i(bx0, 0)
    pygame.draw.circle(surf, barrel_fill, front_cap, cap_r)
    pygame.draw.circle(surf, barrel_fill, back_cap, cap_r)
    # Capsule outline: top + bottom edges and the two semicircle caps
    pygame.draw.line(surf, edge_col, rot(bx0, -bh), rot(bx1, -bh), ow)
    pygame.draw.line(surf, edge_col, rot(bx0,  bh), rot(bx1,  bh), ow)
    pygame.draw.circle(surf, edge_col, front_cap, cap_r, ow)
    pygame.draw.circle(surf, edge_col, back_cap, cap_r, ow)

    # ── 2. BASE silhouette: pointed back, gently rounded front corners ──
    seg = 10  # more segments => smoother corners after scale-down
    pts = []
    pts.append(rot(-body_w / 2 - tri_w, 0))               # back tip
    pts.append(rot(-body_w / 2, -body_h / 2))             # top-back corner
    pts.append(rot(body_w / 2 - front_r, -body_h / 2))    # top edge
    for i in range(1, seg):
        ang = -math.pi / 2 + (math.pi / 2) * (i / seg)
        lx = body_w / 2 - front_r + front_r * math.cos(ang)
        ly = -front_r + front_r * math.sin(ang)
        pts.append(rot(lx, ly))
    pts.append(rot(body_w / 2, -front_r))                  # right edge top
    pts.append(rot(body_w / 2, front_r))                   # right edge bot
    for i in range(1, seg):
        ang = (math.pi / 2) * (i / seg)
        lx = body_w / 2 - front_r + front_r * math.cos(ang)
        ly = front_r + front_r * math.sin(ang)
        pts.append(rot(lx, ly))
    pts.append(rot(body_w / 2 - front_r, body_h / 2))      # bottom-right
    pts.append(rot(-body_w / 2, body_h / 2))               # bottom-back

    pygame.draw.polygon(surf, base_fill, pts)
    pygame.draw.polygon(surf, edge_col, pts, ow)

    # Smoothscale down to logical size and blit
    final = pygame.transform.smoothscale(surf, (size // SS, size // SS))
    screen.blit(final, (cx - final.get_width() // 2, cy - final.get_height() // 2))


def draw_extra_barrel(cx, cy, angle, color, length=24, width=8):
    """Render a simple navy-outlined barrel from a tower center, rotated by `angle`.

    Used for multi-turret (MG/airstrike) and spray-fan (gunner gold) visuals.
    """
    SS = 3
    pad = 4
    size = (length + pad) * 2 * SS
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    scx = scy = size // 2
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    NAVY = (28, 50, 92)
    bw = width / 2
    pts = [
        (scx + (-2 * cos_a - -bw * sin_a) * SS, scy + (-2 * sin_a + -bw * cos_a) * SS),
        (scx + (length * cos_a - -bw * sin_a) * SS, scy + (length * sin_a + -bw * cos_a) * SS),
        (scx + (length * cos_a - bw * sin_a) * SS, scy + (length * sin_a + bw * cos_a) * SS),
        (scx + (-2 * cos_a - bw * sin_a) * SS, scy + (-2 * sin_a + bw * cos_a) * SS),
    ]
    pygame.draw.polygon(surf, color, pts)
    pygame.draw.polygon(surf, NAVY, pts, 3 * SS)
    cap_r = int(round(bw * SS))
    cap = (scx + length * cos_a * SS, scy + length * sin_a * SS)
    pygame.draw.circle(surf, color, (int(cap[0]), int(cap[1])), cap_r)
    pygame.draw.circle(surf, NAVY, (int(cap[0]), int(cap[1])), cap_r, 3 * SS)
    final = pygame.transform.smoothscale(surf, (size // SS, size // SS))
    screen.blit(final, (cx - final.get_width() // 2, cy - final.get_height() // 2))


def draw_machine_gun_base(cx, cy, spin_angle):
    """Pristine Gold Machine Gun: rounded-square base + 8 outward rotating turrets."""
    sq, rr = 18, 6
    # Base square (axis-aligned, looks same from all angles since it's symmetrical)
    pygame.draw.rect(screen, (30, 80, 30), (cx - sq, cy - sq, sq * 2, sq * 2), border_radius=rr)
    pygame.draw.rect(screen, (10, 40, 10), (cx - sq, cy - sq, sq * 2, sq * 2), 3, border_radius=rr)
    # 8 rectangular turrets radiating outward
    for i in range(8):
        ang = spin_angle + i * math.pi / 4
        draw_extra_barrel(cx, cy, ang, (80, 160, 80), length=20, width=6)
    # Center riveted hub
    pygame.draw.circle(screen, (200, 210, 50), (cx, cy), 7)
    pygame.draw.circle(screen, (10, 40, 10), (cx, cy), 7, 2)


def draw_pristine_ring(cx, cy, tier, radius=26):
    """Bronze / Silver / Gold halo ring under a tower indicating pristine tier."""
    PRISTINE_COLS = {
        "bronze": ((205, 130, 50), (140, 80, 25)),
        "silver": ((220, 220, 230), (150, 150, 165)),
        "gold":   ((255, 210, 65), (180, 140, 20)),
    }
    if tier not in PRISTINE_COLS:
        return
    light, dark = PRISTINE_COLS[tier]
    pygame.draw.circle(screen, dark, (cx, cy), radius + 2, 4)
    pygame.draw.circle(screen, light, (cx, cy), radius, 3)
    # 4 small studs around the ring for premium feel
    for i in range(4):
        a = math.pi / 4 + i * math.pi / 2
        sx = int(cx + radius * math.cos(a))
        sy = int(cy + radius * math.sin(a))
        pygame.draw.circle(screen, light, (sx, sy), 3)
        pygame.draw.circle(screen, dark, (sx, sy), 3, 1)


def draw_frost_rings(cx, cy, outer_radius, angle):
    outer_rect = pygame.Rect(cx - outer_radius, cy - outer_radius, outer_radius * 2, outer_radius * 2)
    inner_radius = 24
    inner_rect = pygame.Rect(cx - inner_radius, cy - inner_radius, inner_radius * 2, inner_radius * 2)
    for i in range(8):
        start = angle + i * math.pi / 4
        col = (0, 165, 255) if i % 2 == 0 else (0, 35, 145)
        pygame.draw.arc(screen, col, outer_rect, start, start + math.pi / 6, 6)
    for i in range(8):
        start = -angle + i * math.pi / 4
        col = (0, 70, 210) if i % 2 == 0 else (0, 15, 95)
        pygame.draw.arc(screen, col, inner_rect, start, start + math.pi / 5, 3)

ALL_ABILITIES = [
    {"name": "Regeneration",    "desc": "Regenerates HP over time.", "params": [{"label": "Regen rate (HP/sec)", "key": "regen_rate", "default": "3"}]},
    {"name": "Vampiric Dash",   "desc": "Dashes to a tower and drains HP.", "params": [{"label": "Drain % of tower HP", "key": "drain_pct", "default": "20"}]},
    {"name": "Tower Raider",    "desc": "Directly attacks towers.", "params": []},
    {"name": "Reflection",      "desc": "Reflects damage back to nearby towers.", "params": [{"label": "Reflect %", "key": "reflect_pct", "default": "30"}, {"label": "Reflect interval (sec)", "key": "reflect_rate", "default": "1.0"}]},
    {"name": "Summoning",       "desc": "Summons minions periodically.", "params": [{"label": "Summon interval (sec)", "key": "summon_interval", "default": "5"}]},
    {"name": "Split",           "desc": "Splits into 2 smaller enemies on death.", "params": [{"label": "Child HP", "key": "child_hp", "default": "50"}, {"label": "Child desc", "key": "child_desc", "default": "Split child"}]},
    {"name": "Vengeance",       "desc": "Below 50% HP: swiping dash at towers. Range shown visually.", "params": [{"label": "Swipe range (px)", "key": "swipe_range", "default": "80"}]},
    {"name": "Plague",          "desc": "Shoots plague pellets that poison towers.", "params": []},
    {"name": "Shielder",        "desc": "Blue shield absorbs bullets. Size shown visually.", "params": [{"label": "Shield HP", "key": "shield_hp", "default": "200"}, {"label": "Shield radius (px)", "key": "shield_radius", "default": "40"}]},
    {"name": "Warping",         "desc": "Becomes invincible periodically.", "params": [{"label": "Invincibility duration (sec)", "key": "invis_dur", "default": "2"}]},
    {"name": "Distractor",      "desc": "Towers and goblins target this first.", "params": []},
    {"name": "Distractor Ball", "desc": "Shoots a ball that towers target until it dies.", "params": [{"label": "Ball HP", "key": "ball_hp", "default": "100"}]},
    {"name": "Teleportation",   "desc": "Teleports forward along the path.", "params": []},
    {"name": "Berserker",       "desc": "Below 25% HP: speed and damage doubled.", "params": []},
    {"name": "Spectral",        "desc": "20% chance to phase through bullets entirely.", "params": []},
    {"name": "Corrosive",       "desc": "Leaves an acid trail damaging nearby towers.", "params": []},
    {"name": "Leech",           "desc": "Drains HP from nearby enemies to heal itself.", "params": []},
    {"name": "Phantom Strike",  "desc": "Rapidly strikes all towers in range simultaneously.", "params": []},
    {"name": "Eruption",        "desc": "On death: AoE explosion damages nearby towers.", "params": []},
    {"name": "Fortified",       "desc": "Immune to slow and freeze effects.", "params": []},
    {"name": "Rebirth",         "desc": "Respawns once at 25% HP when first killed.", "params": []},
    {"name": "Chain Lightning", "desc": "When hit, zaps nearby towers for bonus damage.", "params": []},
    {"name": "Shadow Clone",    "desc": "Creates a decoy copy that towers prioritize.", "params": []},
]

PATHS = [
    {"id": "default", "name": "Default", "cost": 0, "desc": "The classic route", "points": [(0, 300), (200, 300), (200, 500), (600, 500), (600, 100), (WIDTH, 100)]},
    {
        "id": "zigzag",
        "name": "Zigzag",
        "cost": 7500,
        "desc": "Sharp turns, more distance",
        "points": [(0, 350), (120, 350), (120, 180), (280, 180), (280, 510), (450, 510), (450, 150), (630, 150), (630, 510), (820, 510), (820, 100), (WIDTH, 100)],
    },
    {
        "id": "long",
        "name": "Long Way",
        "cost": 150000,
        "desc": "A longer march across the map",
        "points": [(0, 380), (150, 380), (150, 100), (370, 100), (370, 560), (580, 560), (580, 200), (WIDTH, 200)],
    },
    {
        "id": "loop",
        "name": "Loop",
        "cost": 300000,
        "desc": "Path crosses itself — place towers inside the loop!",
        "points": [(0, 350), (400, 350), (400, 150), (750, 150), (750, 500), (250, 500), (250, 175), (WIDTH, 175)],
    },
]

# ── Upgrade table  (3 levels per tower = max_level 4) ─────────────────────────
UPGRADE_TABLE = {
    "gunner": [
        {"cost": 500, "damage": 0, "range": 0, "health": 50, "bullets": 2, "desc": "Sputters 2 bullets per shot"},
        {"cost": 5000, "damage": 0, "range": 0, "health": 100, "bullets": 3, "desc": "Sputters 3 bullets per shot"},
        {"cost": 15000, "damage": 50, "range": 25, "health": 150, "desc": "+50 damage, +25 range"},
        {"cost": 40000, "damage": 75, "range": 50, "health": 200, "desc": "+75 damage, +50 range"},
        {"cost": 80000, "damage": 105, "range": 50, "health": 300, "blood": True, "desc": "Blood Tier 1: +105 dmg, +50 range"},
        {"cost": 130000, "damage": 200, "range": -75, "health": 500, "blood": True, "homing": True, "desc": "Blood Tier 2: +200 dmg, -75 range, homing!"},
        {"cost": 150000, "damage": 300, "range": 25, "health": 800, "blood": True, "bullets": 5, "desc": "Blood Tier 3: 5 bullets, +300 dmg, +25 range"},
        {"cost": 7500000, "damage": 1200, "range": 40, "health": 1500, "pristine": "bronze", "bullets": 7, "desc": "Pristine Bronze: +1200 dmg, 7 bullets, +40 range"},
        {"cost": 50000000, "damage": 1200, "range": 0, "health": 2500, "pristine": "silver", "bullets": 10, "desc": "Pristine Silver: +1200 dmg, 10 bullets"},
        {"cost": 100000000, "damage": 2400, "range": 0, "health": 5000, "pristine": "gold", "bullets": 10, "spray": True, "desc": "Pristine Gold: +2400 dmg, 10 bullets in 3 directions"},
    ],
    "sniper": [
        {"cost": 1000, "damage": 50, "range": 50, "health": 75, "desc": "Longer barrel, sharper sight"},
        {"cost": 2500, "damage": 75, "range": 50, "health": 100, "desc": "High-velocity round"},
        {"cost": 5000, "damage": 100, "range": 75, "health": 150, "desc": "Max range & penetration"},
        {"cost": 75000, "damage": 200, "range": 100, "health": 300, "blood": True, "desc": "Blood Tier 1"},
        {"cost": 200000, "damage": 400, "range": 150, "health": 600, "blood": True, "desc": "Blood Tier 2: Homing unlocked!"},
        {"cost": 600000, "damage": 800, "range": 200, "health": 1200, "blood": True, "desc": "Blood Tier 3"},
        {"cost": 7500000, "damage": 1000, "range": 100, "health": 2000, "pristine": "bronze", "stun": 180, "desc": "Pristine Bronze: +1000 dmg, +100 range, stuns 3 sec"},
        {"cost": 50000000, "damage": 2000, "range": 150, "health": 3500, "pristine": "silver", "stun": 300, "desc": "Pristine Silver: +2000 dmg, +150 range, stuns 5 sec"},
        {"cost": 100000000, "damage": 2500, "range": 300, "health": 6000, "pristine": "gold", "stun": 420, "desc": "Pristine Gold: +2500 dmg, +300 range, stuns 7 sec"},
    ],
    "machine_gun": [
        {"cost": 2000, "damage": 5, "range": 5, "health": 100, "desc": "Faster fire rate"},
        {"cost": 5000, "damage": 10, "range": 5, "health": 150, "desc": "Extended clip"},
        {"cost": 10000, "damage": 15, "range": 10, "health": 200, "desc": "Max fire rate & range"},
        {"cost": 80000, "damage": 30, "range": 20, "health": 400, "blood": True, "desc": "Blood Tier 1"},
        {"cost": 250000, "damage": 60, "range": 30, "health": 800, "blood": True, "desc": "Blood Tier 2: Homing unlocked!"},
        {"cost": 800000, "damage": 120, "range": 50, "health": 1500, "blood": True, "desc": "Blood Tier 3"},
        {"cost": 7500000, "damage": 200, "range": 50, "health": 2500, "pristine": "bronze", "turrets": 2, "desc": "Pristine Bronze: +200 dmg, 2 turrets"},
        {"cost": 50000000, "damage": 500, "range": 75, "health": 4000, "pristine": "silver", "turrets": 4, "desc": "Pristine Silver: +500 dmg, 4 turrets"},
        {"cost": 100000000, "damage": 1000, "range": 100, "health": 7500, "pristine": "gold", "turrets": 8, "spin": True, "desc": "Pristine Gold: +1000 dmg, 8 spinning turrets"},
    ],
    "heavy_machine_gun": [
        {"cost": 50000, "damage": 20, "range": 10, "health": 300, "desc": "Heavy barrel upgrade"},
        {"cost": 150000, "damage": 100, "range": 20, "health": 500, "desc": "Armour-piercing rounds"},
        {"cost": 300000, "damage": 50, "range": 20, "health": 750, "desc": "Max armour & firepower"},
        {"cost": 500000, "damage": 200, "range": 40, "health": 1000, "blood": True, "desc": "Blood Tier 1"},
        {"cost": 1000000, "damage": 400, "range": 60, "health": 2000, "blood": True, "desc": "Blood Tier 2: Homing unlocked!"},
        {"cost": 2000000, "damage": 800, "range": 80, "health": 4000, "blood": True, "desc": "Blood Tier 3"},
        {"cost": 7500000, "damage": 100, "range": 75, "health": 6000, "pristine": "bronze", "shrap": 100, "desc": "Pristine Bronze: +100 dmg, +75 range, shrapnel 100"},
        {"cost": 50000000, "damage": 500, "range": 100, "health": 9000, "pristine": "silver", "shrap": 300, "pierce": 1, "desc": "Pristine Silver: +500 dmg, shrapnel 300, pierces 1"},
        {"cost": 100000000, "damage": 1000, "range": 250, "health": 15000, "pristine": "gold", "shrap": 750, "pierce": 3, "homing": True, "desc": "Pristine Gold: +1000 dmg, +250 range, shrapnel 750, pierces 3, homing"},
    ],
    "airstrike": [
        {"cost": 10000, "damage": 25, "range": 10, "health": 100, "desc": "Bigger payload"},
        {"cost": 25000, "damage": 50, "range": 20, "health": 200, "desc": "Wider blast radius"},
        {"cost": 50000, "damage": 100, "range": 30, "health": 300, "desc": "Max blast, wider radius"},
        {"cost": 150000, "damage": 500, "range": 50, "health": 500, "blood": True, "desc": "Blood Tier 1"},
        {"cost": 400000, "damage": 1000, "range": 80, "health": 1000, "blood": True, "desc": "Blood Tier 2: Homing unlocked!"},
        {"cost": 1000000, "damage": 2000, "range": 120, "health": 2000, "blood": True, "desc": "Blood Tier 3"},
        {"cost": 7500000, "damage": 1000, "range": 150, "health": 4000, "pristine": "bronze", "splash_bonus": 500, "loader": True, "load_speed": 1.0, "max_ammo": 3, "desc": "Pristine Bronze: +1000 dmg, +150 range, goblin loader (needs builder hut)"},
        {"cost": 50000000, "damage": 1200, "range": 200, "health": 6000, "pristine": "silver", "splash_bonus": 500, "loader": True, "load_speed": 1.8, "max_ammo": 3, "desc": "Pristine Silver: +1200 dmg, faster goblin loader"},
        {"cost": 100000000, "damage": 1500, "range": 250, "health": 10000, "pristine": "gold", "splash_bonus": 800, "turrets": 3, "loader": True, "load_speed": 2.6, "max_ammo": 3, "burst_fire": True, "desc": "Pristine Gold: 3 rotating turrets, 3-shot burst, fastest loader"},
    ],
    "Goblin Hut": [
        {"cost": 35000, "damage": 0, "range": 0, "health": 200, "desc": "Goblins: +2 capacity, stronger"},
        {"cost": 75000, "damage": 0, "range": 0, "health": 500, "desc": "Elite goblins, max 5, big HP"},
        {"cost": 150000, "damage": 0, "range": 0, "health": 500, "desc": "+HP +dmg +speed per goblin"},
        {"cost": 300000, "damage": 0, "range": 0, "health": 1000, "blood": True, "desc": "Blood Goblins: brutal stats"},
        {"cost": 600000, "damage": 0, "range": 0, "health": 2000, "blood": True, "desc": "7 Blood Goblins, max power"},
        {"cost": 1200000, "damage": 0, "range": 0, "health": 4000, "blood": True, "desc": "9 Ultimate Blood Goblins"},
        {"cost": 7500000, "damage": 0, "range": 0, "health": 5000, "pristine": "bronze", "gob_dmg": 100, "barb_chance": 5, "desc": "Pristine Bronze: 9 goblins → 3 barbarians, 5% sword throw"},
        {"cost": 50000000, "damage": 0, "range": 0, "health": 8000, "pristine": "silver", "gob_dmg": 250, "barb_chance": 15, "spikes": 4, "desc": "Pristine Silver: +200 dmg, 4 spinning spikes, 15% throw"},
        {"cost": 100000000, "damage": 0, "range": 0, "health": 15000, "pristine": "gold", "gob_dmg": 1250, "barb_chance": 65, "spikes": 8, "desc": "Pristine Gold: +400 dmg, 8 spikes, 65% throw"},
    ],
    "builder_hut": [
        {"cost": 50000, "damage": 0, "range": 0, "health": 200, "desc": "Faster speed, repairs walls too"},
        {"cost": 100000, "damage": 0, "range": 0, "health": 200, "desc": "+rock dmg, +repair, +range"},
        {"cost": 200000, "damage": 0, "range": 0, "health": 200, "desc": "Max speed, rapid repairs"},
        {"cost": 300000, "damage": 0, "range": 0, "health": 1000, "blood": True, "desc": "Repairs walls; heals at hut"},
        {"cost": 600000, "damage": 0, "range": 0, "health": 2000, "blood": True, "desc": "2x faster repairs"},
        {"cost": 1200000, "damage": 0, "range": 0, "health": 4000, "blood": True, "desc": "Max power, instant repairs"},
        {"cost": 7500000, "damage": 0, "range": 0, "health": 5000, "pristine": "bronze", "heal": (5, 120), "desc": "Pristine Bronze: helper hut, heals 5 every 2 sec"},
        {"cost": 50000000, "damage": 0, "range": 0, "health": 8000, "pristine": "silver", "heal": (10, 90), "chimney": True, "desc": "Pristine Silver: heals 10 / 1.5s, chimney distractor"},
        {"cost": 100000000, "damage": 0, "range": 0, "health": 15000, "pristine": "gold", "heal": (25, 45), "instant_chance": 5, "desc": "Pristine Gold: heals 25 / 0.75s, 5% instant heal"},
    ],
    "Valkyrie Hut": [
        {"cost": 50000, "damage": 0, "range": 0, "health": 300, "desc": "Valkyries move quicker"},
        {"cost": 100000, "damage": 0, "range": 0, "health": 500, "desc": "Valkyries move even faster"},
        {"cost": 0, "damage": 0, "range": 0, "health": 0, "desc": "COMBINE: Drag a maxed Goblin Hut here!"},
        {"cost": 7500000, "damage": 100, "range": 0, "health": 3000, "pristine": "bronze", "extra_valk": 1, "barbaric": True, "desc": "Pristine Bronze: +1 valkyrie, barbaric mode"},
        {"cost": 50000000, "damage": 500, "range": 0, "health": 5000, "pristine": "silver", "extra_valk": 1, "barbaric": True, "desc": "Pristine Silver: +1 valkyrie, more barbaric"},
        {"cost": 100000000, "damage": 1000, "range": 0, "health": 10000, "pristine": "gold", "extra_valk": 1, "split_barbs": 3, "desc": "Pristine Gold: +1 valkyrie, splits into 3 barbarians on death"},
    ],
    "frost_laser": [
        {"cost": 8000, "damage": 0, "range": 20, "health": 100, "desc": "Wider chill zone; stronger slow"},
        {"cost": 18000, "damage": 0, "range": 30, "health": 150, "desc": "Extended range; deep freeze"},
        {"cost": 40000, "damage": 0, "range": 40, "health": 200, "desc": "Max chill: 70% slow"},
        {"cost": 120000, "damage": 25, "range": 50, "health": 400, "blood": True, "desc": "Blood Tier 1: Electric zap, chains 3"},
        {"cost": 300000, "damage": 60, "range": 70, "health": 800, "blood": True, "desc": "Blood Tier 2: Faster zap, chains 4"},
        {"cost": 800000, "damage": 150, "range": 100, "health": 1500, "blood": True, "desc": "Blood Tier 3: Rapid zap, chains 5"},
        {"cost": 7500000, "damage": 300, "range": 50, "health": 3000, "pristine": "bronze", "slow_bonus": 0.10, "chain_bonus": 2, "desc": "Pristine Bronze: +300 dmg, +2 chain, +10% slow"},
        {"cost": 50000000, "damage": 500, "range": 50, "health": 5000, "pristine": "silver", "slow_bonus": 0.25, "chain_bonus": 1, "desc": "Pristine Silver: +500 dmg, +1 chain, +25% slow"},
        {"cost": 100000000, "damage": 750, "range": 50, "health": 10000, "pristine": "gold", "slow_bonus": 0.30, "chain_bonus": 2, "freeze": True, "desc": "Pristine Gold: +750 dmg, freeze 1s every 3s"},
    ],
}

GOBLIN_COLORS = [
    (0, 200, 0),  # tier 0 - green
    (255, 165, 0),  # tier 1 - orange
    (220, 60, 0),  # tier 2 - red-orange
    (180, 0, 0),  # tier 3 - dark red
    (120, 0, 0),  # tier 4 (blood) - very dark red
    (80, 0, 0),  # tier 5 (blood) - near-black red
]

# ── Bestiary data ─────────────────────────────────────────────────────────────
BESTIARY_ENEMIES = [
    # Ordered by wave introduction (ascending)
    {"id": "scout", "name": "Scout", "color": RED, "shape": "circle", "desc": "Fast and light. Introduced in the first wave."},
    {"id": "soldier", "name": "Soldier", "color": BLUE, "shape": "circle", "desc": "Balanced speed and health."},
    {"id": "berserker", "name": "Berserker", "color": (255, 80, 0), "shape": "pentagon", "desc": "A bit fast and fragile but does high end damage."},
    {"id": "heavy", "name": "Heavy", "color": DARK_BLUE, "shape": "circle", "desc": "Slow and tough. Deals high damage."},
    {"id": "doom_knight", "name": "Doom Knight", "color": (80, 80, 90), "shape": "square", "desc": "Heavily armoured. Slow but hard to bring down."},
    {"id": "ghost", "name": "Ghost", "color": DARK_RED, "shape": "circle", "desc": "Invisible to most towers. Only snipers can target it."},
    {"id": "runner", "name": "Runner", "color": PURPLE, "shape": "square", "desc": "Moderate speed. Tricky to pin down."},
    {"id": "necromancer", "name": "Necromancer", "color": (90, 0, 120), "shape": "pentagon", "desc": "Raises skeleton minions every few seconds."},
    {"id": "dasher", "name": "Dasher", "color": PINK, "shape": "square", "desc": "Extremely fast but fragile."},
    {"id": "tortoise", "name": "Tortoise", "color": (80, 120, 0), "shape": "pentagon", "desc": "Agonisingly slow with enormous health."},
    {"id": "spectral_wolf", "name": "Spectral Wolf", "color": (180, 220, 255), "shape": "diamond", "desc": "Fast spectral predator. Only snipers can see it."},
    {"id": "tank", "name": "Tank", "color": CYAN, "shape": "square", "desc": "Very slow and very tough."},
    {"id": "specter", "name": "Specter", "color": (180, 230, 255), "shape": "pentagon", "desc": "Ethereal. Only snipers and airstrikes can see it."},
    {"id": "bruiser", "name": "Joker", "color": BROWN, "shape": "square", "desc": "Distracts Goblins from other attackers."},
    {"id": "charger", "name": "Charger", "color": ORANGE, "shape": "triangle", "desc": "Fast with decent health."},
    {"id": "lightning_bug", "name": "Lightning Bug", "color": (200, 255, 50), "shape": "star", "desc": "Blindingly fast. Falls to a single good hit."},
    {"id": "venom_crawler", "name": "Venom Crawler", "color": (50, 180, 30), "shape": "pentagon", "desc": "Agonisingly slow, laced with venom and enormous health."},
    {"id": "golem", "name": "Golem", "color": GRAY, "shape": "triangle", "desc": "Massive health. Very slow."},
    {"id": "phase_shifter", "name": "Phase Shifter", "color": (200, 100, 255), "shape": "diamond", "desc": "Phases in and out of reality. Sniper-only."},
    {"id": "gargoyle", "name": "Gargoyle", "color": (160, 160, 160), "shape": "star", "desc": "Stone skin. Tanky and relentless."},
    {"id": "wizard", "name": "Wizard", "color": (75, 0, 130), "shape": "diamond", "desc": "Spawns minions every 5 seconds. Mid-game threat"},
    {"id": "titan", "name": "Titan", "color": BLACK, "shape": "triangle", "desc": "Attacks towers. Enormous health. Goblins target it."},
    {"id": "plague_rat", "name": "Plague Rat", "color": (100, 180, 50), "shape": "star", "desc": "Splits into 3 smaller rats on death."},
    {"id": "war_mammoth", "name": "War Mammoth", "color": (120, 70, 30), "shape": "hexagon", "desc": "Ancient war beast. Kill towers slowly."},
    {"id": "sprinter", "name": "Sprinter", "color": GREEN, "shape": "triangle", "desc": "Very fast with high health."},
    {"id": "phantom", "name": "Phantom", "color": (80, 0, 80), "shape": "diamond", "desc": "Sniper-only. Extremely tough and slow. Very problematic."},
    {"id": "null_specter", "name": "Null Specter", "color": (20, 0, 40), "shape": "star", "desc": "Void-born shade. Invisible to most towers."},
    {"id": "paladin", "name": "Paladin", "color": GOLD, "shape": "star", "desc": "Slowly regenerates health. Hard to whittle down."},
    {"id": "flame_imp", "name": "Flame Imp", "color": (255, 80, 30), "shape": "triangle", "desc": "Blazingly fast and erratic. Fragile but relentless."},
    {"id": "shade", "name": "Shade", "color": (75, 12, 140), "shape": "diamond", "desc": "Tough and moderately fast."},
    {"id": "storm_rider", "name": "Storm Rider", "color": (60, 160, 255), "shape": "triangle", "desc": "Rides the storm. Very fast with decent endurance."},
    {"id": "tower_raider", "name": "Tower Raider", "color": (220, 50, 200), "shape": "diamond", "desc": "Ignores the path. Hunts towers directly. Appears wave 30+."},
    {"id": "frost_giant", "name": "Frost Giant", "color": (100, 200, 240), "shape": "hexagon", "desc": "Glacially slow but nearly impossible to destroy."},
    {"id": "shadow_dancer", "name": "Shadow Dancer", "color": (30, 30, 120), "shape": "hexagon", "desc": "Weaves side to side. Hard to hit consistently."},
    {"id": "blood_spawn", "name": "Blood Spawn", "color": (180, 0, 30), "shape": "circle", "desc": "Splits into two weaker copies on death."},
    # Blood Storm enemies (wave 35+)
    {"id": "vampire", "name": "Vampire", "color": (150, 0, 80), "shape": "hexagon", "desc": "Dashes to towers and drains 20% of their HP. Terrifying, Biggest threat after The Colossus."},
    {"id": "wraith", "name": "Wraith", "color": (200, 200, 220), "shape": "hexagon", "desc": "Fast and ethereal. Only snipers can see it."},
    {"id": "blood_bat", "name": "Blood Bat", "color": (180, 0, 20), "shape": "triangle", "desc": "Very fast blood-crazed bat swarm."},
    {"id": "shadow_hound", "name": "Shadow Hound", "color": (90, 0, 120), "shape": "pentagon", "desc": "Fast shadow beast. Only snipers can track it."},
    {"id": "stone_giant", "name": "Stone Giant", "color": (110, 110, 110), "shape": "hexagon", "desc": "Impossibly slow but with enormous HP."},
    {"id": "fury_beast", "name": "Fury Beast", "color": (255, 120, 30), "shape": "pentagon", "desc": "Speeds up as its health drops."},
    {"id": "chaos_sprite", "name": "Chaos Sprite", "color": (255, 50, 255), "shape": "star", "desc": "Erratic and unpredictable. Hard to focus."},
    {"id": "void_walker", "name": "Void Walker", "color": (10, 0, 30), "shape": "diamond", "desc": "Fast and very durable. Comes from the void."},
    {"id": "plague_bearer", "name": "Plague Bearer", "color": (30, 80, 20), "shape": "pentagon", "desc": "Slow but carries devastating health."},
    {"id": "bone_lord", "name": "Bone Lord", "color": (220, 210, 190), "shape": "pentagon", "desc": "Ancient undead warrior with high health."},
    {"id": "plague_moth", "name": "Plague Moth", "color": (80, 160, 30), "shape": "star", "desc": "Releases plague rats when killed."},
    {"id": "crystal_drake", "name": "Crystal Drake", "color": (100, 200, 255), "shape": "hexagon", "desc": "Crystalline armour gives enormous health."},
    {"id": "sand_wraith", "name": "Sand Wraith", "color": (200, 180, 100), "shape": "diamond", "desc": "Invisible to most towers. Only snipers can hit it."},
    {"id": "storm_eagle", "name": "Storm Eagle", "color": (100, 180, 255), "shape": "triangle", "desc": "Blindingly fast aerial unit."},
    {"id": "night_terror", "name": "Night Terror", "color": (10, 10, 20), "shape": "diamond", "desc": "Fast and ferocious creature of the dark."},
    {"id": "leviathan", "name": "Leviathan", "color": (80, 0, 120), "shape": "hexagon", "desc": "Colossal health and huge reward. Rare and terrifying."},
    {"id": "abomination", "name": "Abomination", "color": (100, 20, 80), "shape": "hexagon", "desc": "Splits into two smaller horrors on death."},
    {"id": "shadow_fiend", "name": "Shadow Fiend", "color": (20, 20, 100), "shape": "diamond", "desc": "Fast shadow creature, hard to pin down."},
    {"id": "iron_golem", "name": "Iron Golem", "color": (60, 60, 70), "shape": "hexagon", "desc": "Barely moves, but has titanic health."},
    {"id": "lich", "name": "Lich", "color": (200, 200, 150), "shape": "pentagon", "desc": "Ancient undead sorcerer with high resilience."},
    {"id": "doom_bringer", "name": "Doom Bringer", "color": (120, 0, 20), "shape": "hexagon", "desc": "Brings destruction with enormous health."},
    {"id": "crypt_walker", "name": "Crypt Walker", "color": (210, 200, 180), "shape": "pentagon", "desc": "Undead revenant. High health and eerie resilience."},
    {"id": "elder_dragon", "name": "Elder Dragon", "color": (150, 120, 0), "shape": "hexagon", "desc": "Massive health and huge coin reward."},
    {"id": "dreadnought", "name": "Dreadnought", "color": (60, 70, 80), "shape": "hexagon", "desc": "Iron fortress of flesh. Hunts towers. Massive health."},
    {"id": "molten_titan", "name": "Molten Titan", "color": (200, 80, 0), "shape": "hexagon", "desc": "Living magma. Colossal health. The ultimate threat."},
    {"id": "void_shade", "name": "Void Shade", "color": (15, 0, 35), "shape": "diamond", "desc": "Vanishes into the void. Fast, durable, sniper-only."},
    {"id": "obsidian_guardian", "name": "Obsidian Guardian", "color": (35, 35, 45), "shape": "hexagon", "desc": "Armoured late-game wall with heavy damage reduction."},
    {"id": "mirror_wisp", "name": "Mirror Wisp", "color": (190, 230, 255), "shape": "diamond", "desc": "Shatters into mirror fragments on death."},
    {"id": "ember_colossus", "name": "Ember Colossus", "color": (230, 70, 15), "shape": "hexagon", "desc": "Burns towers that stand too close."},
    {"id": "frost_weaver", "name": "Frost Weaver", "color": (120, 220, 255), "shape": "star", "desc": "Freezes nearby towers, slowing their fire rate."},
    {"id": "shield_mender", "name": "Shield Mender", "color": (80, 220, 150), "shape": "pentagon", "desc": "Repairs nearby enemies in pulses."},
    {"id": "blink_stalker", "name": "Blink Stalker", "color": (160, 70, 255), "shape": "diamond", "desc": "Blinks forward along the path."},
    {"id": "thornback_beast", "name": "Thornback Beast", "color": (60, 130, 55), "shape": "pentagon", "desc": "Thorn armour blocks a large chunk of damage."},
    {"id": "swarm_queen", "name": "Swarm Queen", "color": (130, 70, 170), "shape": "hexagon", "desc": "Summons minions while advancing."},
    {"id": "arcane_orb", "name": "Arcane Orb", "color": (230, 90, 255), "shape": "circle", "desc": "Cycles through invulnerable magic phases."},
    {"id": "acid_spitter", "name": "Acid Spitter", "color": (120, 255, 40), "shape": "triangle", "desc": "Melts nearby towers and walls with acid."},
    {"id": "siren_banshee", "name": "Siren Banshee", "color": (210, 210, 255), "shape": "star", "desc": "Screams to hasten nearby enemies."},
    {"id": "gravity_slug", "name": "Gravity Slug", "color": (70, 50, 110), "shape": "circle", "desc": "Warps gravity, heavily slowing nearby towers."},
    {"id": "rune_giant", "name": "Rune Giant", "color": (50, 120, 200), "shape": "hexagon", "desc": "Regenerates through carved defensive runes."},
    {"id": "void_reaper", "name": "Void Reaper", "color": (5, 5, 45), "shape": "diamond", "desc": "Sniper-only reaper that phases out of danger."},
    {"id": "celestial_drake", "name": "Celestial Drake", "color": (255, 230, 120), "shape": "hexagon", "desc": "Regenerates and calls lightning onto towers."},
    {"id": "shadow_priest", "name": "Shadow Priest", "color": (40, 0, 80), "shape": "pentagon", "desc": "Heals nearby enemies and slows tower fire rate with dark auras."},
    {"id": "lava_lurker", "name": "Lava Lurker", "color": (180, 60, 10), "shape": "hexagon", "desc": "Burns nearby towers rapidly with liquid magma."},
    {"id": "psy_fiend", "name": "Psy Fiend", "color": (200, 50, 200), "shape": "diamond", "desc": "Periodically phases backward to evade fire."},
    {"id": "glacial_creep", "name": "Glacial Creep", "color": (80, 200, 240), "shape": "circle", "desc": "Massive health. Heavily slows all nearby towers."},
    {"id": "dust_devil", "name": "Dust Devil", "color": (200, 180, 120), "shape": "star", "desc": "Warps forward when critically wounded."},
    {"id": "crimson_stalker", "name": "Crimson Stalker", "color": (200, 0, 40), "shape": "diamond", "desc": "Sniper-only. Splits into three on death."},
    {"id": "mimic", "name": "Mimic", "color": (150, 150, 255), "shape": "star", "desc": "Cycles through invulnerable shape-shift phases."},
    {"id": "thunder_ram", "name": "Thunder Ram", "color": (50, 80, 200), "shape": "pentagon", "desc": "Charges and slams towers for heavy damage."},
    {"id": "plague_crawler", "name": "Plague Crawler", "color": (60, 120, 30), "shape": "hexagon", "desc": "Regenerates health and corrodes nearby towers with plague."},
    {"id": "void_colossus", "name": "Void Colossus", "color": (20, 0, 50), "shape": "hexagon", "desc": "Sniper-only. Enormous health, regenerates, and phases in and out of reality."},
    # ── Shadow Storm enemies (waves 75–80) ────────────────────────────────────
    {"id": "shadow_wraith", "name": "Shadow Wraith", "color": (90, 0, 140), "shape": "diamond", "desc": "Sniper-only. Fast and elusive — born of the shadow storm."},
    {"id": "void_harbinger", "name": "Void Harbinger", "color": (30, 0, 60), "shape": "star", "desc": "Heralds the void; tough and steady."},
    {"id": "umbral_stalker", "name": "Umbral Stalker", "color": (140, 60, 200), "shape": "triangle", "desc": "Sniper-only. Shadowy hunter that slips through normal vision."},
    {"id": "abyssal_juggernaut", "name": "Abyssal Juggernaut", "color": (60, 20, 120), "shape": "hexagon", "desc": "Massive shadow-storm tank. 90k HP."},
    {"id": "phantom_warlord", "name": "Phantom Warlord", "color": (180, 100, 230), "shape": "pentagon", "desc": "Commands shadow legions with deadly precision."},
    {"id": "void_emperor", "name": "Void Emperor", "color": (20, 0, 30), "shape": "circle", "desc": "Ultimate shadow-storm enemy. 150k HP, 15 dmg."},
    # ── New enemies ───────────────────────────────────────────────────────────
    {"id": "spike_hopper", "name": "Spike Hopper", "color": (220, 100, 60), "shape": "triangle", "desc": "Bouncing spike-ball. Fast and erratic."},
    {"id": "ember_wolf", "name": "Ember Wolf", "color": (240, 90, 40), "shape": "diamond", "desc": "Flame-cloaked wolf. Swift hunter of the late waves."},
    {"id": "crystal_shard", "name": "Crystal Shard", "color": (160, 230, 255), "shape": "star", "desc": "Splinter of living crystal. Refracts incoming fire."},
    {"id": "blight_walker", "name": "Blight Walker", "color": (90, 140, 50), "shape": "pentagon", "desc": "Slow plague host. Massive HP, leaves toxic trail."},
    {"id": "stormcaller", "name": "Stormcaller", "color": (100, 130, 255), "shape": "star", "desc": "Calls down lightning. Summons sparks every few seconds."},
    {"id": "void_serpent", "name": "Void Serpent", "color": (40, 0, 70), "shape": "diamond", "desc": "Sniper-only. Slithers through reality, very tough."},
    {"id": "iron_sentinel", "name": "Iron Sentinel", "color": (80, 90, 110), "shape": "hexagon", "desc": "Heavy guard. Trades speed for staggering durability."},
    {"id": "cursed_jester", "name": "Cursed Jester", "color": (220, 60, 200), "shape": "square", "desc": "Tricky and erratic. Distracts goblins with illusions."},
    {"id": "fungal_horror", "name": "Fungal Horror", "color": (140, 200, 90), "shape": "pentagon", "desc": "Splits into 4 spores on death."},
    {"id": "blade_dancer", "name": "Blade Dancer", "color": (210, 230, 255), "shape": "diamond", "desc": "Twin-blade duelist. Lightning-fast and precise."},
    {"id": "nether_imp", "name": "Nether Imp", "color": (90, 0, 130), "shape": "triangle", "desc": "Tiny dark imp. Swarms in numbers."},
    {"id": "obsidian_titan", "name": "Obsidian Titan", "color": (25, 25, 35), "shape": "hexagon", "desc": "Black-stone goliath. Crushing weight, near-immortal."},
    {"id": "blood_moth", "name": "Blood Moth", "color": (180, 40, 80), "shape": "star", "desc": "Crimson-winged swarmer. Very fast and elusive."},
    {"id": "ash_revenant", "name": "Ash Revenant", "color": (160, 150, 140), "shape": "pentagon", "desc": "Burnt undead warrior. Regenerates from embers."},
    {"id": "omen_specter", "name": "Omen Specter", "color": (10, 0, 40), "shape": "circle", "desc": "Sniper-only. A bad omen of the deepest waves."},
]

BESTIARY_BOSSES = [
    {"id": "boss_1", "name": "The Void", "color": (0, 0, 0), "shape": "circle", "desc": "First boss. Enormous health."},
    {"id": "boss_2", "name": "Shadow King", "color": (50, 0, 50), "shape": "triangle", "desc": "Faster than The Void. Dark sorcery."},
    {"id": "boss_3", "name": "Blood Lord", "color": (100, 0, 0), "shape": "diamond", "desc": "Very high damage output."},
    {"id": "boss_4", "name": "Ocean Titan", "color": (0, 0, 100), "shape": "square", "desc": "Massive health, moderate speed."},
    {"id": "boss_5", "name": "Abyss Walker", "color": (4, 0, 20), "shape": "pentagon", "desc": "Near-unstoppable. 100,000 HP."},
    {"id": "boss_6", "name": "The Colossus", "color": (0, 30, 80), "shape": "hexagon", "desc": "500k HP. The ultimate threat."},
    {"id": "boss_7", "name": "Rat King", "color": (80, 50, 0), "shape": "star", "desc": "Spawns 10 plague rats on death."},
    {"id": "boss_8", "name": "Plague Bearer", "color": (0, 80, 20), "shape": "pentagon", "desc": "Regenerates HP rapidly."},
    {"id": "boss_9", "name": "Storm Phoenix", "color": (100, 150, 255), "shape": "triangle", "desc": "Extremely fast. 80,000 HP."},
    {"id": "boss_10", "name": "Iron Golem King", "color": (60, 60, 60), "shape": "hexagon", "desc": "Sluggish but nearly indestructible."},
    {"id": "boss_11", "name": "Blood Emperor", "color": (150, 0, 0), "shape": "star", "desc": "Blood Storm tyrant. 2.5 million HP."},
    {"id": "boss_12", "name": "The Abyssal Titan", "color": (5, 0, 30), "shape": "hexagon", "desc": "5 million HP. Revives once. Spawns void fragments on death."},
    # ── Shadow Storm bosses (cycle in past wave 75) ───────────────────────────
    {"id": "boss_shadow_lord", "name": "Shadow Lord", "color": (50, 0, 100), "shape": "diamond", "desc": "12 million HP. Lord of the shadow realm."},
    {"id": "boss_void_titan", "name": "Void Titan", "color": (100, 0, 200), "shape": "hexagon", "desc": "25 million HP. Towering void colossus."},
    {"id": "boss_abyss_king", "name": "Abyss King", "color": (30, 0, 60), "shape": "star", "desc": "50 million HP. Final shadow-storm sovereign."},
    # ── New bosses ────────────────────────────────────────────────────────────
    {"id": "boss_chaos_emperor", "name": "Chaos Emperor", "color": (160, 20, 200), "shape": "star", "desc": "100 million HP. Tyrant of unending chaos."},
    {"id": "boss_eternal_god", "name": "Eternal God", "color": (255, 230, 80), "shape": "circle", "desc": "250 million HP. The final eternal threat."},
]

# ── Game globals ──────────────────────────────────────────────────────────────
coins = 400
hp = 20
users = {}
logout_menu_open = False
skip_wave_open = False
skip_wave_str = ""
skip_wave_rect_obj = pygame.Rect(0, 0, 0, 0)
arena_vpad_rects = {}        # {"up","down","left","right"} → Rect
arena_vpad_fire_rect = pygame.Rect(0, 0, 0, 0)
arena_vpad_held = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}
onscreen_kb_rects = {}       # key_label → Rect
kb_shift = False
keyboard_panel_rect = pygame.Rect(0, 0, 0, 0)  # set by draw_onscreen_keyboard
mobile_mode = False
mobile_mode_menu_rect = pygame.Rect(0, 0, 0, 0)
path_shop_open = False
selected_path_id = "default"
owned_path_ids = {"default"}
menu_path_rects = {}
return_rect_obj = pygame.Rect(0, 0, 0, 0)
logged_in_user = None
is_admin = False
speed_2x = False
nightmare_mode = False
show_ranges = False
upgrade_menu_upgrade_rect = None
upgrade_menu_close_rect = None
upgrade_menu_sell_rect = None
upgrade_menu_move_rect = None
upgrade_menu_revive_rect = None
moving_tower_obj = None
arena_moving_tower_obj = None
signup_error = ""
login_error = ""
admin_delete_buttons = {}

_pending_shop_tooltip = None  # drawn on top of everything at end of frame

blood_storm_active = False
blood_storm_splash_timer = 0
blood_storm_info_open = False
blood_storm_info_rect = pygame.Rect(0, 0, 0, 0)
blood_storm_info_close_rect = pygame.Rect(0, 0, 0, 0)
# ── Shadow Storm (after wave 75) ──────────────────────────────────────────────
shadow_storm_active = False
shadow_storm_splash_timer = 0
shadow_storm_info_open = False
shadow_storm_info_rect = pygame.Rect(0, 0, 0, 0)
shadow_storm_info_close_rect = pygame.Rect(0, 0, 0, 0)
selected_wall = None
sell_rect_wall = None
wall_upgrade_rect = None
wall_sell_rect = None
wall_close_rect = None

pack_howl_frames = 0  # spectral_wolf death: speed-boost all enemies
discovered_enemies = set()
achievement_queue = []

# ── Valkyrie Hut globals ──────────────────────────────────────────────────────
valkyrie_combine_mode = False  # True when waiting for player to click a goblin hut to merge
valkyrie_combine_hut = None  # The Valkyrie Hut Tower waiting for the merge
combine_anim_timer = 0  # Frames remaining for the golden merge flash
combine_anim_pos = None  # (x, y) world position of the merge animation
arena_valkyrie_combine_mode = False
arena_valkyrie_combine_hut = None
arena_combine_anim_timer = 0
arena_combine_anim_pos = None
bestiary_open = False
bestiary_tab = "enemies"
bestiary_scroll = 0
bestiary_close_rect = pygame.Rect(0, 0, 0, 0)
bestiary_tab_rects = {}
bestiary_up_rect = pygame.Rect(0, 0, 0, 0)
bestiary_down_rect = pygame.Rect(0, 0, 0, 0)

# ── Admin command console ─────────────────────────────────────────────────────
cmd_console_open = False
cmd_console_str = ""
cmd_console_output = ""
cmd_console_inp_rect = pygame.Rect(0, 0, 0, 0)
cmd_console_help_shown = False  # commands only revealed after typing 'help'

# ── Create entity (custom enemy/boss) ─────────────────────────────────────────
create_entity_open = False
create_entity_type = "enemy"
create_entity_fields = {
    "name": "", "desc": "", "hp": "100", "dmg": "2", "spd": "1.5",
    "reward": "20", "wave": "1", "r": "180", "g": "60", "b": "60",
}
create_entity_shape = "circle"
create_entity_shape_idx = 0
create_entity_ability = ""
create_entity_ab_params = {}
create_entity_active_field = None
create_entity_help_open = False
create_entity_help_scroll = 0
custom_enemies = []
custom_bosses = []


def load_custom_creatures():
    global custom_enemies, custom_bosses
    if os.path.exists("custom_creatures.json"):
        try:
            with open("custom_creatures.json") as _f:
                _d = json.load(_f)
            custom_enemies[:] = _d.get("enemies", [])
            custom_bosses[:] = _d.get("bosses", [])
            for _c in custom_enemies + custom_bosses:
                _col = _c.get("color")
                if isinstance(_col, list):
                    _c["color"] = tuple(_col)
        except Exception:
            pass


def save_custom_creatures():
    try:
        with open("custom_creatures.json", "w") as _f:
            json.dump({
                "enemies": [{**e, "color": list(e["color"])} for e in custom_enemies],
                "bosses": [{**b, "color": list(b["color"])} for b in custom_bosses],
            }, _f)
    except Exception:
        pass

# ── Leaderboard ────────────────────────────────────────────────────────────────
leaderboard_open = False
leaderboard_tab = "normal"
leaderboard_scroll = 0
leaderboard_close_rect = pygame.Rect(0, 0, 0, 0)
leaderboard_tab_rects = {}

# ── Nightmare lock ─────────────────────────────────────────────────────────────
nightmare_locked = False
nightmare_last_click = 0.0
nm_double_click_threshold = 0.45

# ── Frost laser show circles ───────────────────────────────────────────────────
frost_show_circles = False
frost_show_circles_rect = pygame.Rect(0, 0, 0, 0)
arena_frost_show_circles_rect = pygame.Rect(0, 0, 0, 0)

shop_tab = "towers"
placing_tower = False
placing_wall = False
placing_bomb = False
wall_rot = 0  # rotation (deg) for the next TD wall placement
selected_tower = None
selected_tower_object = None
shop_open = False
shop_x = -170
shop_slide_speed = 15

walls = []
bombs = []
walls_placed_count = 0
bombs_placed_count = 0

enemies = []
towers = []
coins_list = []
dead_towers = []
enemy_timer = 0
wave_number = 1
wave_active = False
enemies_spawned = 0
enemies_to_spawn = 0
spawn_interval = 30

state = "MENU"

tower_prices = {"gunner": 100, "sniper": 200, "machine_gun": 1000, "airstrike": 5000, "Goblin Hut": 15000, "frost_laser": 4000, "heavy_machine_gun": 50000, "builder_hut": 35000, "Valkyrie Hut": 100000}


# ── Helper functions ──────────────────────────────────────────────────────────
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def load_users():
    global users
    if os.path.exists("users.json"):
        with open("users.json") as f:
            users = json.load(f)


def save_users():
    with open("users.json", "w") as f:
        json.dump(users, f)


def get_tower_price(tower_type):
    base = tower_prices[tower_type]
    count = sum(1 for t in towers if t.type == tower_type)
    return int(base * (1.2**count))


def get_arena_tower_price(tower_type):
    base = tower_prices[tower_type]
    count = sum(1 for t in arena_towers if t.type == tower_type)
    return int(base * (1.2**count))


def get_wall_cost():
    return 500


def get_bomb_cost():
    return int(100000 * (1.5**bombs_placed_count))


def get_bomb_aoe_damage():
    return int(500 * (1.5**bombs_placed_count))


def get_bomb_boss_damage():
    return int(10000 * (1.5**bombs_placed_count))


def point_to_segment_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def is_near_path(x, y, threshold=30):
    for i in range(len(path) - 1):
        if point_to_segment_dist(x, y, path[i][0], path[i][1], path[i + 1][0], path[i + 1][1]) < threshold:
            return True
    return False


def draw_shape(surface, color, cx, cy, radius, shape, outline=None, lw=2):
    cx, cy = int(cx), int(cy)
    if shape == "circle":
        pygame.draw.circle(surface, color, (cx, cy), radius)
        if outline:
            pygame.draw.circle(surface, outline, (cx, cy), radius, lw)
    elif shape == "square":
        r = pygame.Rect(cx - radius, cy - radius, radius * 2, radius * 2)
        pygame.draw.rect(surface, color, r)
        if outline:
            pygame.draw.rect(surface, outline, r, lw)
    elif shape == "triangle":
        pts = [(cx, cy - radius), (cx - radius, cy + radius), (cx + radius, cy + radius)]
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, lw)
    elif shape == "diamond":
        pts = [(cx, cy - radius), (cx + radius, cy), (cx, cy + radius), (cx - radius, cy)]
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, lw)
    elif shape == "pentagon":
        pts = [(cx + radius * math.cos(math.radians(-90 + i * 72)), cy + radius * math.sin(math.radians(-90 + i * 72))) for i in range(5)]
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, lw)
    elif shape == "star":
        pts = []
        for i in range(10):
            r = radius if i % 2 == 0 else radius * 0.45
            a = math.radians(-90 + i * 36)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, lw)
    elif shape == "hexagon":
        pts = [(cx + radius * math.cos(math.radians(i * 60)), cy + radius * math.sin(math.radians(i * 60))) for i in range(6)]
        pygame.draw.polygon(surface, color, pts)
        if outline:
            pygame.draw.polygon(surface, outline, pts, lw)


def record_enemy_kill(type_id):
    if type_id not in discovered_enemies:
        discovered_enemies.add(type_id)
        entry = next((b for b in BESTIARY_ENEMIES + BESTIARY_BOSSES if b["id"] == type_id), None)
        name = entry["name"] if entry else type_id
        achievement_queue.append((f"New enemy discovered: {name}!", time.time() + 3.5))


def reset_bestiary():
    discovered_enemies.clear()
    achievement_queue.clear()


# ── Enemy class ───────────────────────────────────────────────────────────────
class Enemy:
    def __init__(self, color, damage, speed, reward, health, visible_to="all", radius=12, type_id="unknown", shape="circle"):
        self.color = color
        self.damage = damage
        self.speed = speed
        self.base_speed = speed
        self.reward = reward
        self.path_index = 0
        self.x, self.y = path[0]
        self.health = health
        self.max_health = health
        self.visible_to = visible_to
        self.radius = radius
        self.type_id = type_id
        self.shape = shape
        self.is_boss = False
        self.is_wizard = color == (75, 0, 130)
        self.is_summoner = type_id in ("necromancer", "swarm_queen")
        self.targets_towers = False
        self.is_tower_raider = False
        self.plague_rat = type_id == "plague_rat"
        self.regen_rate = 12 if type_id == "rune_giant" else (6 if type_id == "celestial_drake" else (3 if type_id == "paladin" else 0))
        self.zigzag = type_id == "shadow_dancer"
        self.last_minion_time = time.time()
        self.minions = []
        self.bob_offset = 0
        self.bob_dir = 1
        # Pristine sniper stun (frames remaining where this enemy cannot move)
        self.stun_timer = 0

    def _move_along_path(self, eff):
        # Robust path follow: handles overshoot and 0-distance landings
        # (previously enemies could stick on a waypoint when dist == 0)
        guard = 0
        while eff > 0 and self.path_index + 1 < len(path) and guard < 8:
            guard += 1
            tx, ty = path[self.path_index + 1]
            dx, dy = tx - self.x, ty - self.y
            dist = math.hypot(dx, dy)
            if dist <= eff:
                # snap to waypoint and continue with leftover speed
                self.x = float(tx)
                self.y = float(ty)
                self.path_index += 1
                eff -= max(dist, 0.0001)
            else:
                self.x += (dx / dist) * eff
                self.y += (dy / dist) * eff
                if self.zigzag:
                    self.x += math.sin(time.time() * 4) * 2
                eff = 0

    def move(self):
        # Sniper-pristine stun: enemy cannot move while stun_timer > 0
        if getattr(self, "stun_timer", 0) > 0:
            self.stun_timer = max(0, self.stun_timer - (2 if speed_2x else 1))
            return
        eff = self.base_speed * (2 if speed_2x else 1) * (3 if nightmare_mode else 1) * getattr(self, "frost_slow_mult", 1.0)

        # ── Vampire dash logic ────────────────────────────────────────────────
        if getattr(self, "is_vampire", False):
            phase = getattr(self, "vampire_phase", 0)
            if phase == 0:
                # Normal path movement + countdown to next dash
                self._move_along_path(eff)
                self.vampire_timer = getattr(self, "vampire_timer", 0) + (2 if speed_2x else 1)
                if self.vampire_timer >= 300 and towers:
                    tgt = min(towers, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
                    self.vampire_target = tgt
                    self.vampire_saved_x = self.x
                    self.vampire_saved_y = self.y
                    self.vampire_saved_idx = self.path_index
                    self.vampire_phase = 1
                    self.vampire_timer = 0
            elif phase == 1:
                # Dash toward tower
                tgt = getattr(self, "vampire_target", None)
                if not tgt or getattr(tgt, "health", 0) <= 0:
                    self.vampire_phase = 3
                else:
                    dx = tgt.x - self.x
                    dy = tgt.y - self.y
                    d = math.hypot(dx, dy)
                    if d < 28:
                        # Impact — drain 20% of tower max HP, heal self
                        drain = max(1, int(tgt.max_health * 0.20))
                        tgt.take_damage(drain)
                        self.health = min(self.max_health, self.health + drain)
                        self.vampire_phase = 2
                        self.vampire_hit_timer = 22
                    else:
                        sp = eff * 2.5
                        self.x += dx / d * sp
                        self.y += dy / d * sp
            elif phase == 2:
                # Hit animation pause
                self.vampire_hit_timer = getattr(self, "vampire_hit_timer", 0) - 1
                if self.vampire_hit_timer <= 0:
                    self.vampire_phase = 3
            elif phase == 3:
                # Return to saved path position
                tx = getattr(self, "vampire_saved_x", self.x)
                ty = getattr(self, "vampire_saved_y", self.y)
                dx = tx - self.x
                dy = ty - self.y
                d = math.hypot(dx, dy)
                if d < 10:
                    self.x = tx
                    self.y = ty
                    self.path_index = getattr(self, "vampire_saved_idx", self.path_index)
                    self.vampire_phase = 0
                else:
                    sp = eff * 2.0
                    self.x += dx / d * sp
                    self.y += dy / d * sp
            self.bob_offset += self.bob_dir * 0.5
            if abs(self.bob_offset) > 5:
                self.bob_dir *= -1
            return
        # ─────────────────────────────────────────────────────────────────────

        tick = 2 if speed_2x else 1

        # ── New enemy abilities ───────────────────────────────────────────────
        # Pack Howl speed boost (from spectral_wolf death)
        if pack_howl_frames > 0:
            eff *= 1.5
        if self.type_id != "siren_banshee":
            for _e in arena_enemies:
                if _e is not self and _e.type_id == "siren_banshee" and _e.health > 0 and math.hypot(_e.wx - self.wx, _e.wy - self.wy) < 150:
                    eff *= 1.35
                    break
        if self.type_id != "siren_banshee":
            for _e in enemies:
                if _e is not self and _e.type_id == "siren_banshee" and _e.health > 0 and math.hypot(_e.x - self.x, _e.y - self.y) < 150:
                    eff *= 1.35
                    break

        # Flame Imp frenzy: faster as HP drops
        if self.type_id == "flame_imp":
            hp_r = max(0.0, self.health / max(1, self.max_health))
            eff = self.base_speed * (1.0 + (1.0 - hp_r) * 1.5) * (2 if speed_2x else 1) * (3 if nightmare_mode else 1)

        # Blood Spawn blood rage: +60% when below 50% HP
        if getattr(self, "blood_spawn", False) and self.health < self.max_health * 0.5:
            eff *= 1.6

        # Shadow Hound / Thunder Ram pounce — handled before normal movement
        if self.type_id in ("shadow_hound", "thunder_ram"):
            ph = getattr(self, "pounce_phase", 0)
            if ph == 1:  # dashing to tower
                pt = getattr(self, "pounce_target", None)
                if not pt or getattr(pt, "health", 0) <= 0:
                    self.pounce_phase = 2
                else:
                    pdx = pt.x - self.x
                    pdy = pt.y - self.y
                    pd = math.hypot(pdx, pdy)
                    if pd < 24:
                        _pdmg = 150 if self.type_id == "thunder_ram" else 80
                        pt.take_damage(_pdmg)
                        self.pounce_phase = 2
                    else:
                        self.x += pdx / pd * eff * 3
                        self.y += pdy / pd * eff * 3
                self.bob_offset += self.bob_dir * 0.5
                if abs(self.bob_offset) > 5:
                    self.bob_dir *= -1
                return
            elif ph == 2:  # returning to saved path position
                rx = getattr(self, "pounce_save_x", self.x)
                ry = getattr(self, "pounce_save_y", self.y)
                rdx = rx - self.x
                rdy = ry - self.y
                rd = math.hypot(rdx, rdy)
                if rd < 10:
                    self.x = rx
                    self.y = ry
                    self.path_index = getattr(self, "pounce_save_idx", self.path_index)
                    self.pounce_phase = 0
                else:
                    self.x += rdx / rd * eff * 2.5
                    self.y += rdy / rd * eff * 2.5
                self.bob_offset += self.bob_dir * 0.5
                if abs(self.bob_offset) > 5:
                    self.bob_dir *= -1
                return

        # Psy Fiend: reverse along path when in psy_reverse mode
        if self.type_id == "psy_fiend" and getattr(self, "psy_reverse", False) and self.path_index > 0:
            _ptx, _pty = path[self.path_index - 1]
            _pdx, _pdy = _ptx - self.x, _pty - self.y
            _pd = math.hypot(_pdx, _pdy) or 1
            self.x += _pdx / _pd * eff
            self.y += _pdy / _pd * eff
            if _pd < 5:
                self.path_index = max(0, self.path_index - 1)
        else:
            self._move_along_path(eff)

        # ── Per-frame ability processing ─────────────────────────────────────
        # Frost Laser lvl 3+: disable enemy abilities while in aura
        if getattr(self, "frost_disabled", False):
            self.war_tremor_timer = 0
            self.storm_timer = 0
            self.plague_dust_timer = 0
            self.plague_crawl_timer = 0
            self.psy_timer = 0
            self.void_step_timer = 0
            self.pounce_timer = 0
            self.vampire_timer = 0
            self.last_minion_time = time.time()
            self.frost_disabled = False
            self.bob_offset += self.bob_dir * 0.5
            if abs(self.bob_offset) > 5:
                self.bob_dir *= -1
            return
        # Phase Shifter phase cycle (invincibility windows)
        if self.type_id in ("phase_shifter", "arcane_orb", "void_reaper", "mimic", "void_colossus"):
            self.phase_timer = getattr(self, "phase_timer", 0) + tick
            if 300 <= self.phase_timer < 390:
                self.phase_immune = True
            else:
                self.phase_immune = False
            if self.phase_timer >= 390:
                self.phase_timer = 0

        # War Mammoth tremor: damage nearby towers periodically
        if self.type_id == "war_mammoth":
            self.war_tremor_timer = getattr(self, "war_tremor_timer", 0) + tick
            if self.war_tremor_timer >= 400:
                self.war_tremor_timer = 0
                for _t in towers:
                    if math.hypot(_t.x - self.x, _t.y - self.y) < 150:
                        _t.take_damage(30)

        # Storm Rider lightning: zap nearest tower periodically
        if self.type_id in ("storm_rider", "celestial_drake"):
            self.storm_timer = getattr(self, "storm_timer", 0) + tick
            if self.storm_timer >= 200:
                self.storm_timer = 0
                near_t = [_t for _t in towers if math.hypot(_t.x - self.x, _t.y - self.y) < 200]
                if near_t:
                    min(near_t, key=lambda _t: math.hypot(_t.x - self.x, _t.y - self.y)).take_damage(60)

        # Shadow Hound / Thunder Ram pounce cooldown timer (phase 0 = idle)
        if self.type_id in ("shadow_hound", "thunder_ram"):
            self.pounce_timer = getattr(self, "pounce_timer", 0) + tick
            if self.pounce_timer >= 250 and towers:
                near_t = [_t for _t in towers if math.hypot(_t.x - self.x, _t.y - self.y) < 260]
                if near_t:
                    self.pounce_target = min(near_t, key=lambda _t: math.hypot(_t.x - self.x, _t.y - self.y))
                    self.pounce_save_x = self.x
                    self.pounce_save_y = self.y
                    self.pounce_save_idx = self.path_index
                    self.pounce_phase = 1
                    self.pounce_timer = 0

        # Plague Moth dust: periodically heal nearby enemies
        if getattr(self, "plague_moth", False):
            self.plague_dust_timer = getattr(self, "plague_dust_timer", 0) + tick
            if self.plague_dust_timer >= 200:
                self.plague_dust_timer = 0
                for _e in enemies:
                    if _e is not self and math.hypot(_e.x - self.x, _e.y - self.y) < 100:
                        _e.health = min(_e.max_health, _e.health + 15)

        if self.type_id in ("shield_mender", "shadow_priest"):
            self.plague_dust_timer = getattr(self, "plague_dust_timer", 0) + tick
            if self.plague_dust_timer >= 160:
                self.plague_dust_timer = 0
                for _e in enemies:
                    if _e is not self and _e.health > 0 and math.hypot(_e.x - self.x, _e.y - self.y) < 130:
                        _e.health = min(_e.max_health, _e.health + 40)

        # Psy Fiend: periodically reverses path direction for 60 frames
        if self.type_id == "psy_fiend":
            self.psy_timer = getattr(self, "psy_timer", 0) + tick
            self.psy_reverse = getattr(self, "psy_reverse", False)
            if self.psy_reverse and self.psy_timer >= 60:
                self.psy_reverse = False
                self.psy_timer = 0
            elif not self.psy_reverse and self.psy_timer >= 300:
                self.psy_reverse = True
                self.psy_timer = 0

        # Dust Devil: blink forward once when below 40% HP
        if self.type_id == "dust_devil" and not getattr(self, "dust_blinked", False):
            if self.health < self.max_health * 0.4:
                self.dust_blinked = True
                self.path_index = min(len(path) - 1, self.path_index + 3)
                if self.path_index < len(path):
                    self.x, self.y = path[self.path_index]

        if self.type_id in ("ember_colossus", "acid_spitter", "lava_lurker"):
            self.war_tremor_timer = getattr(self, "war_tremor_timer", 0) + tick
            if self.war_tremor_timer >= 150:
                self.war_tremor_timer = 0
                dmg = 55 if self.type_id == "ember_colossus" else 75 if self.type_id == "acid_spitter" else 65
                for _t in towers:
                    if math.hypot(_t.x - self.x, _t.y - self.y) < 135:
                        _t.take_damage(dmg)
                for _w in walls[:]:
                    if math.hypot(_w.x - self.x, _w.y - self.y) < 110:
                        _w.health -= dmg

        # Plague Crawler: corrodes nearby towers with plague
        if self.type_id == "plague_crawler":
            self.plague_crawl_timer = getattr(self, "plague_crawl_timer", 0) + tick
            if self.plague_crawl_timer >= 200:
                self.plague_crawl_timer = 0
                for _t in towers:
                    if math.hypot(_t.x - self.x, _t.y - self.y) < 120:
                        _t.take_damage(40)

        if self.type_id in ("void_shade", "blink_stalker"):
            self.void_step_timer = getattr(self, "void_step_timer", 0) + tick
            if self.void_step_timer >= (220 if self.type_id == "blink_stalker" else 300):
                self.void_step_timer = 0
                self.path_index = min(len(path) - 1, self.path_index + (1 if self.type_id == "blink_stalker" else 2))
                if self.path_index < len(path):
                    self.x, self.y = path[self.path_index]

        # ── End abilities ────────────────────────────────────────────────────

        if self.regen_rate > 0:
            self.health = min(self.max_health, self.health + self.regen_rate * (2 if speed_2x else 1))
        if self.is_wizard or self.is_summoner:
            now = time.time()
            cd = 5 / 3 if blood_storm_active else 5
            if now - self.last_minion_time > cd and len(self.minions) < 3:
                m = Minion(self.x, self.y)
                if blood_storm_active:
                    m.health = m.max_health = 180
                    m.attack_damage = 45
                self.minions.append(m)
                self.last_minion_time = now
                self.summon_ring_t = getattr(self, "summon_ring_t", 0)
                self.summon_ring_t = 18  # trigger animation
        # Decay summon ring animation
        if getattr(self, "summon_ring_t", 0) > 0:
            self.summon_ring_t -= 2 if speed_2x else 1
        # Titan & Dreadnought: seek nearest tower directly, ignore path
        if self.type_id in ("titan", "dreadnought") and towers:
            near_walls_blk = [w for w in walls if w.health > 0 and math.hypot(w.x - self.x, w.y - self.y) < 50]
            if near_walls_blk:
                _bw = min(near_walls_blk, key=lambda w: math.hypot(w.x - self.x, w.y - self.y))
                _dx = _bw.x - self.x
                _dy = _bw.y - self.y
                _d = math.hypot(_dx, _dy) or 1
                if _d > Wall.R + self.radius:
                    self.x += eff * _dx / _d
                    self.y += eff * _dy / _d
                else:
                    _bw.take_damage(self.damage * 2)
            else:
                _tgt = min(towers, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
                _dx = _tgt.x - self.x
                _dy = _tgt.y - self.y
                _d = math.hypot(_dx, _dy) or 1
                if _d > 20:
                    self.x += eff * _dx / _d
                    self.y += eff * _dy / _d
                else:
                    _now = time.time()
                    if _now - getattr(self, "tower_atk_last", 0) >= 1.0:
                        _tgt.take_damage(max(25, self.damage * 8))
                        self.tower_atk_last = _now
            self.bob_offset += self.bob_dir * 0.5
            if abs(self.bob_offset) > 5:
                self.bob_dir *= -1
            return
        self.bob_offset += self.bob_dir * 0.5
        if abs(self.bob_offset) > 5:
            self.bob_dir *= -1

    def draw(self):
        by = self.y + self.bob_offset
        draw_shape(screen, self.color, self.x, by, self.radius, self.shape)
        for m in self.minions:
            m.draw()
        ix = int(self.x)
        iby = int(by)
        # Frost slow visual: glowing icy halo + frost crystals on enemies in a chill zone
        _fsm = getattr(self, "frost_slow_mult", 1.0)
        if _fsm < 0.95:
            _intensity = max(0.0, min(1.0, (1.0 - _fsm) * 1.6))
            _alpha = int(120 * _intensity)
            _frost_r = self.radius + 6
            _fs = pygame.Surface((_frost_r * 2 + 4, _frost_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_fs, (140, 220, 255, _alpha), (_frost_r + 2, _frost_r + 2), _frost_r)
            pygame.draw.circle(_fs, (200, 240, 255, min(220, _alpha + 80)), (_frost_r + 2, _frost_r + 2), _frost_r, 2)
            screen.blit(_fs, (ix - _frost_r - 2, iby - _frost_r - 2))
        # Vampire hit-impact ring
        if getattr(self, "is_vampire", False) and getattr(self, "vampire_phase", 0) == 2:
            t = getattr(self, "vampire_hit_timer", 0)
            r = int((22 - t) * 3 + 12)
            alpha_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(alpha_surf, (220, 0, 80, 160), (r + 2, r + 2), r, 4)
            screen.blit(alpha_surf, (ix - r - 2, iby - r - 2))
        # Wizard/Necromancer summon ring on summon
        _sum_t = getattr(self, "summon_ring_t", 0)
        if _sum_t > 0:
            _rr = int((18 - _sum_t) * 4 + 14)
            _ra = max(0, int(_sum_t * 12))
            _rs = pygame.Surface((_rr * 2 + 4, _rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_rs, (200, 80, 255, _ra), (_rr + 2, _rr + 2), _rr, 3)
            screen.blit(_rs, (ix - _rr - 2, iby - _rr - 2))
        # War mammoth tremor shockwave
        _wt = getattr(self, "war_tremor_timer", 0)
        if self.type_id == "war_mammoth" and _wt > 370:
            _wr = int((_wt - 370) * 10)
            _wa = max(0, 200 - int((_wt - 370) * 7))
            _ws = pygame.Surface((_wr * 2 + 4, _wr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_ws, (180, 120, 50, _wa), (_wr + 2, _wr + 2), _wr, 4)
            screen.blit(_ws, (ix - _wr - 2, iby - _wr - 2))
        # Storm rider lightning bolt to nearest tower
        _st = getattr(self, "storm_timer", 0)
        if self.type_id in ("storm_rider", "celestial_drake") and _st > 180 and towers:
            _near = [_t for _t in towers if math.hypot(_t.x - self.x, _t.y - self.y) < 220]
            if _near:
                _nt = min(_near, key=lambda _t: math.hypot(_t.x - self.x, _t.y - self.y))
                _midx = (ix + _nt.x) // 2 + int(math.sin(time.time() * 20) * 18)
                _midy = (iby + _nt.y) // 2 + int(math.cos(time.time() * 20) * 18)
                pygame.draw.line(screen, (100, 180, 255), (ix, iby), (_midx, _midy), 2)
                pygame.draw.line(screen, (200, 230, 255), (_midx, _midy), (_nt.x, _nt.y), 2)
        # Shadow hound pounce glow
        if self.type_id in ("shadow_hound", "thunder_ram") and getattr(self, "pounce_phase", 0) == 1:
            _ps = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_ps, (160, 0, 255, 100), (self.radius + 2, self.radius + 2), self.radius + 4)
            screen.blit(_ps, (ix - self.radius - 2, iby - self.radius - 2))
        # Phase shifter shimmer when immune
        if getattr(self, "phase_immune", False):
            _ph = pygame.Surface((self.radius * 2 + 14, self.radius * 2 + 14), pygame.SRCALPHA)
            draw_shape(_ph, (200, 100, 255, 80), self.radius + 7, self.radius + 7, self.radius + 6, self.shape)
            screen.blit(_ph, (ix - self.radius - 7, iby - self.radius - 7))
        # Fury beast rage aura at low HP
        if getattr(self, "fury_beast", False) and self.health < self.max_health * 0.5:
            _fp = int(time.time() * 8) % 8
            _fr = self.radius + 6 + _fp
            _fs = pygame.Surface((_fr * 2 + 4, _fr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_fs, (255, 80, 0, 110), (_fr + 2, _fr + 2), _fr, 3)
            screen.blit(_fs, (ix - _fr - 2, iby - _fr - 2))
        # Paladin regen glow
        if getattr(self, "regen_rate", 0) > 0:
            _pp = int(time.time() * 5) % 10
            if _pp < 5:
                _rgs = pygame.Surface((self.radius * 2 + 16, self.radius * 2 + 16), pygame.SRCALPHA)
                pygame.draw.circle(_rgs, (0, 220, 80, 70 + _pp * 10), (self.radius + 8, self.radius + 8), self.radius + 6, 3)
                screen.blit(_rgs, (ix - self.radius - 8, iby - self.radius - 8))
        # Plague moth dust cloud
        _pdt = getattr(self, "plague_dust_timer", 0)
        if (getattr(self, "plague_moth", False) or self.type_id == "shield_mender") and _pdt > 120:
            for _di in range(2):
                _dsx = ix + int(math.sin(time.time() * 4 + _di * 2.1) * 22)
                _dsy = iby + int(math.cos(time.time() * 4 + _di * 2.1) * 22)
                _das = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(_das, ((100, 200, 50, 90) if self.type_id != "shield_mender" else (80, 255, 180, 100)), (8, 8), 6)
                screen.blit(_das, (_dsx - 8, _dsy - 8))
        # Void shade teleport flash
        _vsf = getattr(self, "void_step_timer", 0)
        if self.type_id in ("void_shade", "blink_stalker") and _vsf > (200 if self.type_id == "blink_stalker" else 280):
            _vfr = int((_vsf - (200 if self.type_id == "blink_stalker" else 280)) * 5)
            _vfs = pygame.Surface((_vfr * 2 + 4, _vfr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_vfs, (80, 0, 160, max(0, 180 - _vfr * 12)), (_vfr + 2, _vfr + 2), _vfr, 4)
            screen.blit(_vfs, (ix - _vfr - 2, iby - _vfr - 2))
        if self.type_id in ("ember_colossus", "acid_spitter", "frost_weaver", "gravity_slug", "siren_banshee",
                            "lava_lurker", "glacial_creep", "shadow_priest", "plague_crawler"):
            pulse = int(time.time() * 6) % 18
            rr = self.radius + 12 + pulse
            tint = {
                "ember_colossus": (255, 90, 20, 80),
                "acid_spitter": (150, 255, 40, 80),
                "frost_weaver": (120, 220, 255, 75),
                "gravity_slug": (120, 80, 220, 75),
                "siren_banshee": (210, 210, 255, 70),
                "lava_lurker": (220, 60, 10, 90),
                "glacial_creep": (80, 200, 255, 85),
                "shadow_priest": (80, 0, 160, 75),
                "plague_crawler": (80, 200, 50, 80),
            }[self.type_id]
            aura = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(aura, tint, (rr + 2, rr + 2), rr, 3)
            screen.blit(aura, (ix - rr - 2, iby - rr - 2))
        # Psy Fiend reverse-phase shimmer
        if self.type_id == "psy_fiend" and getattr(self, "psy_reverse", False):
            _pfs = pygame.Surface((self.radius * 2 + 14, self.radius * 2 + 14), pygame.SRCALPHA)
            draw_shape(_pfs, (220, 80, 255, 80), self.radius + 7, self.radius + 7, self.radius + 6, self.shape)
            screen.blit(_pfs, (ix - self.radius - 7, iby - self.radius - 7))
        # Void Colossus phase shimmer (same as phase_immune)
        if self.type_id == "void_colossus" and getattr(self, "phase_immune", False):
            _vcs = pygame.Surface((self.radius * 2 + 18, self.radius * 2 + 18), pygame.SRCALPHA)
            draw_shape(_vcs, (80, 0, 200, 90), self.radius + 9, self.radius + 9, self.radius + 8, self.shape)
            screen.blit(_vcs, (ix - self.radius - 9, iby - self.radius - 9))
        if self.type_id in ("obsidian_guardian", "thornback_beast", "mirror_wisp"):
            rr = self.radius + 7 + (int(time.time() * 5) % 5)
            tint = (180, 180, 210, 85) if self.type_id == "obsidian_guardian" else ((80, 220, 80, 80) if self.type_id == "thornback_beast" else (200, 240, 255, 90))
            guard = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(guard, tint, (rr + 2, rr + 2), rr, 2)
            screen.blit(guard, (ix - rr - 2, iby - rr - 2))

    def draw_health_bar(self):
        by = self.y + self.bob_offset
        pygame.draw.rect(screen, RED, (self.x - 20, by - self.radius - 10, 40, 5))
        pygame.draw.rect(screen, GREEN, (self.x - 20, by - self.radius - 10, 40 * (self.health / self.max_health), 5))
        for m in self.minions:
            m.draw_health_bar()

    def reached_end(self):
        if self.type_id in ("titan", "dreadnought"):
            return False
        return self.path_index == len(path) - 1


# ── Tower Raider ──────────────────────────────────────────────────────────────
_TOWER_RAIDER_PALETTE = [
    (220, 50, 200), (240, 90, 60), (90, 200, 240), (180, 220, 60),
    (255, 160, 40), (140, 80, 220), (60, 220, 140), (240, 220, 80),
]
_TOWER_RAIDER_SHAPES = ["diamond", "triangle", "pentagon", "star", "hexagon", "square"]


class TowerRaider(Enemy):
    COLOR = (220, 50, 200)

    def __init__(self, health, reward):
        # Pick a random shape + color so raiders aren't identical every spawn
        _col = random.choice(_TOWER_RAIDER_PALETTE)
        _shp = random.choice(_TOWER_RAIDER_SHAPES)
        super().__init__(_col, 4, 1.6, reward, health, radius=16, type_id="tower_raider", shape=_shp)
        self.targets_towers = True
        self.is_tower_raider = True
        self.attack_range = 20
        self.attack_damage = 5
        self.attack_cd = 1.0
        self.last_atk = time.time()
        self.target_tower = None

    def move(self):
        eff = self.base_speed * (2 if speed_2x else 1) * (3 if nightmare_mode else 1)
        # find nearest wall near towers first (if any)
        target = self._pick_target()
        if target:
            dx = target.x - self.x
            dy = target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > self.attack_range:
                self.x += eff * dx / dist
                self.y += eff * dy / dist
            else:
                now = time.time()
                if now - self.last_atk >= self.attack_cd:
                    target.take_damage(self.attack_damage)
                    self.last_atk = now
        self.bob_offset += self.bob_dir * 0.5
        if abs(self.bob_offset) > 5:
            self.bob_dir *= -1

    def _pick_target(self):
        if not towers:
            return None
        # Pristine Silver+ Builder Hut chimney distractor: if a chimney builder
        # hut is within 220px, attack other enemies instead of towers.
        chimney_huts = [t for t in towers if t.type == "builder_hut" and getattr(t, "chimney_distractor", False)]
        if chimney_huts:
            ch = min(chimney_huts, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
            if math.hypot(ch.x - self.x, ch.y - self.y) < 220:
                # Find a nearby non-raider, non-minion enemy to attack instead
                others = [e for e in enemies if e is not self and getattr(e, "health", 0) > 0
                          and not getattr(e, "is_tower_raider", False)
                          and not getattr(e, "is_minion", False)]
                if others:
                    return min(others, key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
        nearest_tower = min(towers, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
        nearby_walls = [w for w in walls if w.health > 0 and math.hypot(w.x - nearest_tower.x, w.y - nearest_tower.y) < 80]
        if nearby_walls:
            return min(nearby_walls, key=lambda w: math.hypot(w.x - self.x, w.y - self.y))
        return nearest_tower

    def reached_end(self):
        return False

    def draw(self):
        by = self.y + self.bob_offset
        pts = [(int(self.x), int(by - self.radius)), (int(self.x + self.radius), int(by)), (int(self.x), int(by + self.radius)), (int(self.x - self.radius), int(by))]
        pygame.draw.polygon(screen, self.COLOR, pts)
        pygame.draw.polygon(screen, WHITE, pts, 2)

    def draw_health_bar(self):
        by = self.y + self.bob_offset
        pygame.draw.rect(screen, RED, (self.x - 20, by - self.radius - 10, 40, 5))
        pygame.draw.rect(screen, GREEN, (self.x - 20, by - self.radius - 10, 40 * (self.health / self.max_health), 5))


# ── Minion ────────────────────────────────────────────────────────────────────
class Minion:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.health = 60
        self.max_health = 60
        self.speed = 1.2
        self.attack_range = 40
        self.attack_damage = 15
        self.attack_cd = 1.0
        self.last_atk = time.time()
        self.target = None

    def update(self, tw, _):
        eff = self.speed * (2 if speed_2x else 1)
        pool = []
        for t in tw:
            pool.append(t)
            if hasattr(t, "goblins"):
                pool.extend(t.goblins)
            if hasattr(t, "builders"):
                pool.extend(t.builders)
        # Invalidate target if it's been removed (e.g. tower was sold) so the
        # minion won't get stuck attacking a phantom reference.
        if self.target is not None and self.target not in pool:
            self.target = None
        if not self.target or getattr(self.target, "health", 0) <= 0:
            self.target = min((p for p in pool if getattr(p, "health", 0) > 0), key=lambda p: math.hypot(p.x - self.x, p.y - self.y), default=None)
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dist = math.hypot(dx, dy)
            if dist > self.attack_range:
                self.x += eff * dx / dist
                self.y += eff * dy / dist
            else:
                now = time.time()
                if now - self.last_atk >= self.attack_cd:
                    self.target.take_damage(self.attack_damage)
                    self.last_atk = now

    def draw(self):
        pygame.draw.circle(screen, (150, 0, 200), (int(self.x), int(self.y)), 8)

    def draw_health_bar(self):
        pygame.draw.rect(screen, RED, (self.x - 10, self.y - 15, 20, 4))
        pygame.draw.rect(screen, GREEN, (self.x - 10, self.y - 15, 20 * (self.health / self.max_health), 4))


# ── Goblin ────────────────────────────────────────────────────────────────────
class Goblin:
    def __init__(self, x, y, tier=0):
        self.x, self.y = x, y
        self.tier = tier
        # Stats per tier: (max_health, attack_damage, speed)
        stats = [
            (100, 30, 1.5),  # tier 0 - basic
            (150, 50, 3.0),  # tier 1 - upgraded
            (220, 80, 4.5),  # tier 2 - elite
            (400, 120, 5.0),  # tier 3 - veteran
            (600, 200, 5.5),  # tier 4 - blood
            (1200, 400, 6.5),  # tier 5 - ultimate blood
        ]
        t = min(tier, len(stats) - 1)
        self.max_health = stats[t][0]
        self.health = self.max_health
        self.attack_damage = stats[t][1]
        self.speed = stats[t][2]
        self.color = GOBLIN_COLORS[t]
        self.target = None
        self.attack_range = 40
        self.attack_cd = 1.0
        self.last_atk = time.time()
        self.alive = True
        self.parent_hut = None  # Goblin Hut that spawned us (for kill tracking)

    def _priority(self, e):
        if getattr(e, "is_tower_raider", False):
            return 0
        if getattr(e, "targets_towers", False):
            return 1
        return 2

    def _best(self, pool):
        scored = []
        for e in pool:
            if e.health <= 0:
                continue
            scored.append((self._priority(e), math.hypot(e.x - self.x, e.y - self.y), e))
            for m in getattr(e, "minions", []):
                if getattr(m, "health", 0) > 0:
                    scored.append((1, math.hypot(m.x - self.x, m.y - self.y), m))
        if not scored:
            return None
        scored.sort(key=lambda s: (s[0], s[1]))
        return scored[0][2]

    def update_unique(self, pool, _all):
        eff = self.speed * (2 if speed_2x else 1)
        self.target = self._best(pool)
        if self.target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            d = math.hypot(dx, dy)
            if d > self.attack_range:
                self.x += eff * dx / d
                self.y += eff * dy / d
            else:
                now = time.time()
                if now - self.last_atk > self.attack_cd:
                    _wa_g = self.target.health > 0
                    self.target.health -= self.attack_damage
                    if _wa_g and self.target.health <= 0 and self.parent_hut is not None:
                        self.parent_hut.kills += 1
                    self.last_atk = now
        if self.max_health > self.health:
            self.health += 0.1

    def take_damage(self, amt):
        self.health -= amt
        if self.health <= 0:
            self.alive = False

    def draw(self):
        # Barbarian look (goblin hut pristine): bigger body, brown helmet, sword
        if getattr(self, "barbarian", False):
            cx, cy = int(self.x), int(self.y)
            pygame.draw.circle(screen, (90, 50, 30), (cx, cy), 11)               # body
            pygame.draw.circle(screen, (40, 20, 10), (cx, cy), 11, 2)            # outline
            pygame.draw.rect(screen, (130, 90, 40), (cx - 8, cy - 12, 16, 6))    # helmet
            pygame.draw.rect(screen, (60, 30, 10), (cx - 8, cy - 12, 16, 6), 1)
            # Sword: pointing right
            pygame.draw.line(screen, (220, 220, 230), (cx + 6, cy + 2), (cx + 16, cy - 4), 2)
            pygame.draw.line(screen, (140, 80, 30), (cx + 4, cy + 4), (cx + 8, cy), 3)
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 8)

    def draw_health_bar(self):
        pygame.draw.rect(screen, RED, (self.x - 10, self.y - 15, 20, 4))
        pygame.draw.rect(screen, GREEN, (self.x - 10, self.y - 15, 20 * max(0, self.health / self.max_health), 4))


# ── Valkyrie ─────────────────────────────────────────────────────────────────
class Valkyrie:
    SPLASH_R = 80

    def __init__(self, x, y, mode="minion_focus"):
        self.x, self.y = float(x), float(y)
        self.home_x = float(x)
        self.home_y = float(y)
        self.speed = 2.5
        self.health = 600
        self.max_health = 600
        self.damage = 250
        self.attack_range = 38
        self.attack_cd = 1.4
        self.last_atk = time.time()
        self.alive = True
        self.mode = mode  # "minion_focus" or "raider_focus"
        self.spin_angle = random.uniform(0, 360)
        self.attacking = False
        self.atk_flash = 0
        self.spin_burst = 0
        self.target = None
        self.arena_mode = False
        # Pristine ability state
        self.barb_chance = 0.0       # base 0; raised by hut barbaric flag
        self.barbaric = False         # currently in barbaric (red) mode
        self.barbaric_kills = 0       # counts kills while barbaric (resets at 30)
        self.barbaric_timer = 0       # ticks remaining of barbaric mode
        self.split_count = 0          # 0 = no split; 3 = split into 3 barbarians on death
        self.barb_axe_swap = 0        # frames since last axe-stab swap
        self.barb_hack_phase = 0      # 0..1 oscillating hack animation phase
        self.parent_hut = None  # Valkyrie Hut that spawned us (for kill tracking)

    def _target_pos(self, target):
        return (getattr(target, "x", getattr(target, "wx", self.x)), getattr(target, "y", getattr(target, "wy", self.y)))

    def _find_target(self, enemies, forced_target=None):
        if forced_target and getattr(forced_target, "health", 0) > 0:
            return forced_target
        live = [e for e in enemies if e.health > 0]
        if self.mode == "minion_focus":
            minions = [e for e in live if getattr(e, "is_minion", False)]
            if minions:
                return min(minions, key=lambda e: math.hypot(self._target_pos(e)[0] - self.x, self._target_pos(e)[1] - self.y))
            non_raiders = [e for e in live if not getattr(e, "is_tower_raider", False)]
            if non_raiders:
                return min(non_raiders, key=lambda e: math.hypot(self._target_pos(e)[0] - self.x, self._target_pos(e)[1] - self.y))
        else:
            raiders = [e for e in live if getattr(e, "is_tower_raider", False)]
            if raiders:
                return min(raiders, key=lambda e: math.hypot(self._target_pos(e)[0] - self.x, self._target_pos(e)[1] - self.y))
        return min(live, key=lambda e: math.hypot(self._target_pos(e)[0] - self.x, self._target_pos(e)[1] - self.y)) if live else None

    def update(self, enemies, forced_target=None):
        tick = 2 if speed_2x else 1
        eff = self.speed * tick
        self.target = self._find_target(enemies, forced_target)
        if self.target:
            tx, ty = self._target_pos(self.target)
            dx = tx - self.x
            dy = ty - self.y
            d = math.hypot(dx, dy) or 1
            if d > self.attack_range:
                self.x += eff * dx / d
                self.y += eff * dy / d
                self.attacking = False
            else:
                self.attacking = True
                now = time.time()
                # Barbaric: 5x faster axe-hacking; hits on a tight cooldown
                eff_cd = self.attack_cd * 0.2 if self.barbaric else self.attack_cd
                if now - self.last_atk > eff_cd:
                    dmg_mult = 2.0 if self.barbaric else 1.0
                    for e in enemies:
                        ex, ey = self._target_pos(e)
                        if math.hypot(ex - self.x, ey - self.y) < self.SPLASH_R and e.health > 0:
                            e.health -= self.damage * dmg_mult
                    self.last_atk = now
                    self.atk_flash = 18
                    self.spin_burst = 0 if self.barbaric else 18
                    self.barb_axe_swap = (self.barb_axe_swap + 1) % 2
                    # Roll barbaric activation
                    if not self.barbaric and self.barb_chance > 0 and random.random() < self.barb_chance:
                        self.barbaric = True
                        self.barbaric_timer = 300  # 5 seconds at 60fps
                # End barbaric after 5-second timer
                if self.barbaric:
                    self.barbaric_timer -= tick
                    if self.barbaric_timer <= 0:
                        self.barbaric = False
                        self.barbaric_timer = 0
                    # Hack animation oscillates while barbaric
                    self.barb_hack_phase = (self.barb_hack_phase + 0.6 * tick) % (2 * math.pi)
        else:
            self.attacking = False
            dx = self.home_x - self.x
            dy = self.home_y - self.y
            d = math.hypot(dx, dy) or 1
            if d > 5:
                self.x += eff * dx / d
                self.y += eff * dy / d
        if self.atk_flash > 0:
            self.atk_flash -= tick
        if self.spin_burst > 0:
            self.spin_angle = (self.spin_angle + 28 * tick) % 360
            self.spin_burst -= tick
        elif self.attacking:
            self.spin_angle = (self.spin_angle + 8 * tick) % 360
        self.health = min(self.max_health, self.health + 0.06 * tick)

    def draw(self):
        if self.arena_mode:
            cx, cy = a2s(self.x, self.y)
        else:
            cx, cy = int(self.x), int(self.y)
        # Match valks.png: normal = grey core w/ red ring; barbaric = full red, double axe up-flare
        if self.barbaric:
            inner = (180, 30, 30)
            ring = (220, 50, 50)
        elif self.barb_chance > 0:
            # Pristine valks (non-barbaric) = grey core w/ red outline
            inner = (140, 140, 140)
            ring = (200, 30, 30)
        else:
            inner = (200, 130, 255) if self.mode == "raider_focus" else (255, 190, 80)
            ring = WHITE
        pygame.draw.circle(screen, inner, (cx, cy), 10)
        pygame.draw.circle(screen, ring, (cx, cy), 10, 3)
        # Axes
        if self.barbaric:
            # Two axes hacking up/down rapidly
            hack = math.sin(self.barb_hack_phase) * 14  # +/- 14 px swing
            for sign in (-1, 1):
                base_a = math.radians(-90 + sign * 22)
                ax_len = 18
                ex = cx + int(ax_len * math.cos(base_a))
                ey = cy + int(ax_len * math.sin(base_a) + hack * sign)
                pygame.draw.line(screen, (170, 30, 30), (cx, cy), (ex, ey), 3)
                pygame.draw.circle(screen, (220, 60, 60), (ex, ey), 5)
                pygame.draw.circle(screen, (90, 0, 0), (ex, ey), 5, 1)
        else:
            r = 15 if self.attacking else 12
            for i in range(2):
                a = math.radians(self.spin_angle + i * 180)
                bx = cx + int(r * math.cos(a))
                by = cy + int(r * math.sin(a))
                pygame.draw.line(screen, (200, 160, 40), (cx, cy), (bx, by), 2)
                pygame.draw.circle(screen, (240, 200, 60), (bx, by), 5)
        if self.atk_flash > 0:
            s = pygame.Surface((self.SPLASH_R * 2, self.SPLASH_R * 2), pygame.SRCALPHA)
            alpha = min(160, self.atk_flash * 9)
            flash_col = (255, 80, 80, alpha) if self.barbaric else (255, 220, 80, alpha)
            pygame.draw.circle(s, flash_col, (self.SPLASH_R, self.SPLASH_R), self.SPLASH_R)
            screen.blit(s, (cx - self.SPLASH_R, cy - self.SPLASH_R))

    def draw_health_bar(self):
        if self.arena_mode:
            sx, sy = a2s(self.x, self.y)
        else:
            sx, sy = int(self.x), int(self.y)
        pygame.draw.rect(screen, RED, (sx - 12, sy - 22, 24, 4))
        pygame.draw.rect(screen, GREEN, (sx - 12, sy - 22, int(24 * max(0, self.health / self.max_health)), 4))


# ── Builder ───────────────────────────────────────────────────────────────────
def _apply_builder_level(b, lvl):
    """Apply the per-level stat bonuses for a Builder Hut upgrade level.
    Called both when the hut is upgraded AND when a fresh builder spawns
    so the abilities persist even if the builder was dead at upgrade time.
    """
    if lvl >= 1 and not getattr(b, "_lvl1_applied", False):
        b._lvl1_applied = True
        b.upgraded = True
        b.repairs_walls = True
        b.speed += 0.5
        b.stone_cd = max(90, b.stone_cd - 40)
        b.repair_cd = max(65, b.repair_cd - 30)
        b.stone_range += 30
    if lvl >= 2 and not getattr(b, "_lvl2_applied", False):
        b._lvl2_applied = True
        b.stone_damage += 20
        b.repair_amt += 2
        b.speed += 0.4
        b.stone_cd = max(55, b.stone_cd - 35)
        b.repair_cd = max(40, b.repair_cd - 25)
        b.stone_range += 40
    if lvl >= 3 and not getattr(b, "_lvl3_applied", False):
        b._lvl3_applied = True
        b.stone_damage += 30
        b.repair_amt += 3
        b.speed += 0.5
        b.stone_cd = max(25, b.stone_cd - 30)
        b.repair_cd = max(20, b.repair_cd - 20)
        b.stone_range += 50
    if lvl >= 4 and not getattr(b, "_lvl4_applied", False):
        b._lvl4_applied = True
        b.speed += 0.6
        b.stone_damage += 50
        b.repair_amt += 5
        b.stone_cd = max(15, b.stone_cd - 10)
        b.repair_cd = max(15, b.repair_cd - 5)
    if lvl >= 5 and not getattr(b, "_lvl5_applied", False):
        b._lvl5_applied = True
        b.speed += 0.8
        b.stone_damage += 80
        b.repair_amt += 8
        b.stone_cd = max(8, b.stone_cd - 7)
        b.repair_cd = max(8, b.repair_cd - 7)
    if lvl >= 6 and not getattr(b, "_lvl6_applied", False):
        b._lvl6_applied = True
        b.speed += 1.0
        b.stone_damage += 150
        b.repair_amt += 15
        b.stone_cd = max(4, b.stone_cd - 4)
        b.repair_cd = max(4, b.repair_cd - 4)


class Builder:
    def __init__(self, x, y, upgraded=False):
        self.x, self.y = float(x), float(y)
        self.home_x = float(x)
        self.home_y = float(y)
        self.upgraded = upgraded
        self.health = 150
        self.max_health = 150
        self.speed = 0.8
        self.repair_cd = 100
        self.repair_timer = 0
        self.repair_amt = 3
        self.stone_cd = 140
        self.stone_timer = 0
        self.stone_damage = 12
        self.stone_range = 110
        self.bullets = []
        self.alive = True
        self.repairs_walls = upgraded  # True once builder hut has its first upgrade
        self.valk_target = None  # Valkyrie Hut tower being constructed
        self.hammer_timer = 0  # Used for hammering animation
        self.parent_hut = None  # Builder Hut that spawned us (for kill tracking)

    def take_damage(self, amt):
        self.health -= amt
        if self.health <= 0:
            self.alive = False

    def update(self, tw, en):
        spd = self.speed * (2 if speed_2x else 1)
        tick = 2 if speed_2x else 1

        # ── Valkyrie Hut construction: go to hut, hammer until built ──────────
        if self.valk_target is not None:
            vt = self.valk_target
            if not getattr(vt, "valk_built", False):
                dx = vt.x - self.x
                dy = vt.y - self.y
                d = math.hypot(dx, dy) or 1
                if d > 22:
                    self.x += spd * dx / d
                    self.y += spd * dy / d
                else:
                    self.hammer_timer = (self.hammer_timer + tick) % 24
                return
            else:
                self.valk_target = None  # done

        # Seek and repair nearest damaged tower (whole map, not range-gated)
        damaged = [t for t in tw if t.health < t.max_health]
        # Also repair damaged walls if upgrades allow it
        damaged_walls = [w for w in walls if w.health < w.max_health] if self.repairs_walls else []
        if damaged:
            tgt = min(damaged, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
            dx = tgt.x - self.x
            dy = tgt.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 20:
                self.x += spd * dx / dist
                self.y += spd * dy / dist
            else:
                self.repair_timer += tick
                if self.repair_timer >= self.repair_cd:
                    # Pristine Gold: 5% chance to instantly fully heal
                    if getattr(self, "instant_heal_chance", 0) > 0 and random.uniform(0, 100) < self.instant_heal_chance:
                        tgt.health = tgt.max_health
                    else:
                        tgt.health = min(tgt.max_health, tgt.health + self.repair_amt)
                    self.repair_timer = 0
        elif damaged_walls:
            tgt = min(damaged_walls, key=lambda w: math.hypot(w.x - self.x, w.y - self.y))
            dx = tgt.x - self.x
            dy = tgt.y - self.y
            dist = math.hypot(dx, dy)
            if dist > 20:
                self.x += spd * dx / dist
                self.y += spd * dy / dist
            else:
                self.repair_timer += tick
                if self.repair_timer >= self.repair_cd:
                    tgt.health = min(tgt.max_health, tgt.health + self.repair_amt * 5)
                    self.repair_timer = 0
        else:
            # Return to home when nothing to repair — heal at hut
            dx = self.home_x - self.x
            dy = self.home_y - self.y
            dist = math.hypot(dx, dy)
            if dist > 5:
                self.x += spd * dx / dist
                self.y += spd * dy / dist
            else:
                # Heals when resting at hut
                self.health = min(self.max_health, self.health + 0.05 * tick)

        # Throw stones at any nearby enemy (always, regardless of upgrade level)
        self.stone_timer += tick
        nearby = [e for e in en if math.hypot(e.x - self.x, e.y - self.y) < self.stone_range and getattr(e, "health", 0) > 0]
        if nearby and self.stone_timer >= self.stone_cd:
            tgt2 = min(nearby, key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
            self.bullets.append(Bullet(self.x, self.y, tgt2, self.stone_damage, (180, 140, 80), owner=self.parent_hut))
            self.stone_timer = 0

        # Move bullets
        for b in self.bullets[:]:
            b.move()
            if b.hit():
                if b.damage > 0:
                    _wa_b = b.target.health > 0
                    b.target.health -= b.damage
                    if _wa_b and b.target.health <= 0 and b.owner is not None:
                        b.owner.kills += 1
                self.bullets.remove(b)
            elif b.off_screen():
                self.bullets.remove(b)

    def draw(self):
        bob = 0
        if self.valk_target is not None and not getattr(self.valk_target, "valk_built", False):
            bob = int(4 * math.sin(math.radians(self.hammer_timer * 30)))
        c = (200, 180, 50) if self.upgraded else (180, 140, 50)
        cx, cy = int(self.x), int(self.y) + bob
        pygame.draw.circle(screen, c, (cx, cy), 9)
        pygame.draw.circle(screen, (255, 200, 100), (cx, cy), 9, 2)
        if self.valk_target is not None and not getattr(self.valk_target, "valk_built", False):
            hammer_x = cx + 10
            hammer_y = cy - 6 + bob
            pygame.draw.rect(screen, (180, 140, 50), (hammer_x, hammer_y, 8, 4))
            pygame.draw.line(screen, (160, 120, 40), (cx + 9, cy), (hammer_x + 4, hammer_y + 4), 2)
        for b in self.bullets:
            b.draw()

    def draw_health_bar(self):
        pygame.draw.rect(screen, RED, (self.x - 10, self.y - 17, 20, 4))
        pygame.draw.rect(screen, GREEN, (self.x - 10, self.y - 17, 20 * max(0, self.health / self.max_health), 4))


# ── Helper (Builder Hut Pristine companion) ──────────────────────────────────
class Helper:
    """Pristine Builder Hut companion. Heals the lowest-health tower.
    Has its own small hut (offset from main) where it rests and heals itself."""
    def __init__(self, hut_x, hut_y, heal_amount=5, heal_interval=120):
        # Helper hut is offset to the right of the main builder hut
        self.hut_x = float(hut_x) + 30
        self.hut_y = float(hut_y) + 18
        self.x = self.hut_x
        self.y = self.hut_y
        self.health = 120
        self.max_health = 120
        self.speed = 1.4
        self.heal_amount = heal_amount
        self.heal_interval = heal_interval
        self.heal_timer = 0
        self.alive = True
        self.bob = 0.0

    def take_damage(self, amt):
        self.health = max(0, self.health - amt)
        if self.health <= 0:
            self.alive = False

    def update(self, tw):
        tick = 2 if speed_2x else 1
        spd = self.speed * tick
        # Find tower with lowest health (only damaged ones); exclude self/owner/walls
        damaged = [t for t in tw if t.health < t.max_health]
        if damaged:
            tgt = min(damaged, key=lambda t: t.health / max(1, t.max_health))
            dx = tgt.x - self.x
            dy = tgt.y - self.y
            d = math.hypot(dx, dy)
            if d > 18:
                self.x += spd * dx / d
                self.y += spd * dy / d
            else:
                self.heal_timer += tick
                if self.heal_timer >= self.heal_interval:
                    tgt.health = min(tgt.max_health, tgt.health + self.heal_amount)
                    self.heal_timer = 0
        else:
            # Return to helper hut
            dx = self.hut_x - self.x
            dy = self.hut_y - self.y
            d = math.hypot(dx, dy)
            if d > 3:
                self.x += spd * dx / d
                self.y += spd * dy / d
            else:
                # Heal self in hut
                self.health = min(self.max_health, self.health + 0.08 * tick)
        self.bob = (self.bob + 0.15 * tick) % (2 * math.pi)

    def draw(self):
        cx, cy = int(self.x), int(self.y)
        # Helper sprite: yellow circle with darker outline (matches builderhut.png helper)
        pygame.draw.circle(screen, (210, 160, 40), (cx, cy), 8)
        pygame.draw.circle(screen, (140, 90, 20), (cx, cy), 8, 2)

    def draw_health_bar(self):
        pygame.draw.rect(screen, RED, (self.x - 10, self.y - 15, 20, 3))
        pygame.draw.rect(screen, GREEN, (self.x - 10, self.y - 15, 20 * max(0, self.health / self.max_health), 3))


# ── Barbarian (split-valkyrie spawn) ──────────────────────────────────────────
class Barbarian:
    """Spawned when a Pristine Gold Valkyrie dies (split into 3).
    Charges at the nearest enemy and stabs with two axes (red, fast, low HP)."""
    def __init__(self, x, y, damage=600):
        self.x, self.y = float(x), float(y)
        self.health = 220
        self.max_health = 220
        self.speed = 3.2
        self.damage = damage
        self.attack_range = 32
        self.attack_cd = 0.7
        self.last_atk = time.time()
        self.alive = True
        self.target = None
        self.atk_flash = 0
        self.spin_angle = random.uniform(0, 360)
        self.lifetime = 600  # ~10 sec at 60fps; despawns after

    def update(self, enemies):
        tick = 2 if speed_2x else 1
        eff = self.speed * tick
        self.lifetime -= tick
        if self.lifetime <= 0:
            self.alive = False
            return
        live = [e for e in enemies if getattr(e, "health", 0) > 0]
        if not live:
            return
        self.target = min(live, key=lambda e: math.hypot(e.x - self.x, e.y - self.y))
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        d = math.hypot(dx, dy) or 1
        if d > self.attack_range:
            self.x += eff * dx / d
            self.y += eff * dy / d
        else:
            now = time.time()
            if now - self.last_atk > self.attack_cd:
                _wa_v = self.target.health > 0
                self.target.health -= self.damage
                if _wa_v and self.target.health <= 0 and self.parent_hut is not None:
                    self.parent_hut.kills += 1
                self.last_atk = now
                self.atk_flash = 12
        if self.atk_flash > 0:
            self.atk_flash -= tick
        self.spin_angle = (self.spin_angle + 12 * tick) % 360

    def take_damage(self, amt):
        self.health = max(0, self.health - amt)
        if self.health <= 0:
            self.alive = False

    def draw(self):
        cx, cy = int(self.x), int(self.y)
        # Red filled circle with darker red ring (barbaric look)
        pygame.draw.circle(screen, (170, 30, 30), (cx, cy), 8)
        pygame.draw.circle(screen, (220, 50, 50), (cx, cy), 8, 2)
        # Two crossed mini-axes
        for i in range(2):
            a = math.radians(self.spin_angle + i * 180)
            ex = cx + int(11 * math.cos(a))
            ey = cy + int(11 * math.sin(a))
            pygame.draw.line(screen, (180, 180, 180), (cx, cy), (ex, ey), 2)
            pygame.draw.circle(screen, (220, 220, 220), (ex, ey), 3)
        if self.atk_flash > 0:
            s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 80, 80, min(180, self.atk_flash * 14)), (20, 20), 18)
            screen.blit(s, (cx - 20, cy - 20))

    def draw_health_bar(self):
        pygame.draw.rect(screen, RED, (self.x - 10, self.y - 15, 20, 3))
        pygame.draw.rect(screen, GREEN, (self.x - 10, self.y - 15, 20 * max(0, self.health / self.max_health), 3))


# ── Wall ──────────────────────────────────────────────────────────────────────
class Wall:
    W = 64
    H = 20
    R = 32  # collision half-diagonal (approx) — kept for compat

    LEVEL_STATS = {
        1: {"max_health": 1500, "cost": 0,      "edge": (220, 180, 80)},
        2: {"max_health": 4000, "cost": 50000,  "edge": (180, 220, 255)},
        3: {"max_health": 9000, "cost": 250000, "edge": (200, 100, 255)},
    }
    max_level = 3

    def __init__(self, x, y, angle=0):
        self.x, self.y = x, y
        self.level = 1
        self.max_health = 1500
        self.health = 1500
        self.angle = angle  # degrees
        self.upgrade_cost_spent = 0
        self.on_path = is_near_path(x, y, 30)

    def upgrade(self):
        if self.level >= self.max_level:
            return
        self.level += 1
        stats = self.LEVEL_STATS[self.level]
        hp_gain = stats["max_health"] - self.LEVEL_STATS[self.level - 1]["max_health"]
        self.max_health = stats["max_health"]
        self.health = min(self.max_health, self.health + hp_gain)
        self.upgrade_cost_spent += stats["cost"]

    def is_blocking(self):
        return self.level >= 3

    def take_damage(self, amt):
        self.health -= amt

    def draw(self):
        ratio = max(0.0, self.health / self.max_health)
        stats = self.LEVEL_STATS[self.level]
        edge_col = stats["edge"]
        if self.level == 1:
            cr = int(180 * ratio + 60 * (1 - ratio))
            cg = int(140 * ratio + 40 * (1 - ratio))
            cb = int(80 * ratio + 20 * (1 - ratio))
            fill = (cr, cg, cb)
        elif self.level == 2:
            fill = (int(40 * ratio + 20 * (1 - ratio)), int(80 * ratio + 30 * (1 - ratio)), int(160 * ratio + 60 * (1 - ratio)))
        else:
            fill = (int(60 * ratio + 20 * (1 - ratio)), int(20 * ratio + 10 * (1 - ratio)), int(90 * ratio + 30 * (1 - ratio)))
        surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        surf.fill(fill)
        pygame.draw.rect(surf, edge_col, (0, 0, self.W, self.H), 2)
        for _li in range(self.level):
            pygame.draw.circle(surf, WHITE, (6 + _li * 8, self.H // 2), 3)
        rot = pygame.transform.rotate(surf, -self.angle)
        screen.blit(rot, (self.x - rot.get_width() // 2, self.y - rot.get_height() // 2))
        if self.health < self.max_health:
            bw, bh = self.W, 5
            bx = self.x - bw // 2
            by = self.y - rot.get_height() // 2 - 8
            pygame.draw.rect(screen, RED, (bx, by, bw, bh))
            pygame.draw.rect(screen, GREEN, (bx, by, int(bw * ratio), bh))


# ── Bomb ──────────────────────────────────────────────────────────────────────
class Bomb:
    TRIGGER_R = 16
    EXPLOSION_R = 100

    def __init__(self, x, y, aoe_damage, boss_aoe_damage):
        self.x = x
        self.y = y
        self.aoe_damage = aoe_damage
        self.boss_aoe_dmg = boss_aoe_damage
        self.active = True
        self.flash_timer = 0

    def check(self, en_list):
        """Return True if bomb exploded."""
        for e in en_list:
            if math.hypot(e.x - self.x, e.y - self.y) < self.TRIGGER_R + e.radius:
                self._explode(e, en_list)
                self.active = False
                return True
        return False

    def _explode(self, trigger, en_list):
        # Trigger enemy
        if getattr(trigger, "is_boss", False):
            trigger.health *= 0.25  # 75% loss
        else:
            trigger.health = 0
        # AoE
        for e in en_list:
            d = math.hypot(e.x - self.x, e.y - self.y)
            if d < self.EXPLOSION_R and e is not trigger:
                if getattr(e, "is_boss", False):
                    e.health -= self.boss_aoe_dmg
                else:
                    e.health -= self.aoe_damage
        # Flash effect
        self.flash_timer = 20

    def draw(self):
        pygame.draw.circle(screen, (30, 30, 30), (int(self.x), int(self.y)), self.TRIGGER_R)
        pygame.draw.circle(screen, (255, 60, 0), (int(self.x), int(self.y)), self.TRIGGER_R, 3)
        label = font_sm.render("BOMB", True, (255, 60, 0))
        screen.blit(label, (self.x - label.get_width() // 2, self.y - self.TRIGGER_R - 14))


# ── Bullet ────────────────────────────────────────────────────────────────────
class Bullet:
    def __init__(self, x, y, target, damage, color=YELLOW, splash=False, homing=False, stun=0, shrap=0, pierce=0, vx_override=None, vy_override=None, homing_delay=0, owner=None):
        self.x, self.y = x, y
        self.target = target
        self.damage = damage
        self.speed = 8
        self.color = color
        self.splash = splash
        self.splash_r = 60 if splash else 0
        self.homing = homing
        self.homing_delay = homing_delay  # frames to travel straight before becoming homing
        self.owner = owner  # tower that fired this bullet (for kill tracking)
        # Pristine ability fields
        self.stun = stun          # frames of stun applied on hit (sniper pristine)
        self.shrap = shrap        # additional AoE damage on hit (heavy MG pristine)
        self.pierce = pierce      # remaining additional enemies the bullet can pass through
        self._hit_set = set()     # ids of enemies already hit by this bullet (for pierce)
        self.triangle_shell = False  # gold airstrike: render as isosceles triangle
        # Compute fixed direction for straight-line travel
        if target:
            dx, dy = target.x - x, target.y - y
            d = math.hypot(dx, dy)
            if d:
                self.vx = dx / d * self.speed
                self.vy = dy / d * self.speed
            else:
                self.vx, self.vy = 0.0, -self.speed
        else:
            self.vx, self.vy = 0.0, -self.speed

    def move(self):
        # Homing delay: travel straight first, then become homing
        if self.homing_delay > 0:
            self.homing_delay -= 1
            self.x += self.vx
            self.y += self.vy
            return
        if self.homing and self.target and self.target.health > 0:
            # Homing: steer toward target's current position
            dx, dy = self.target.x - self.x, self.target.y - self.y
            d = math.hypot(dx, dy)
            if d:
                self.x += dx / d * self.speed
                self.y += dy / d * self.speed
        else:
            # Straight: fixed direction
            self.x += self.vx
            self.y += self.vy

    def hit(self):
        if not self.target:
            return False
        radius = 16 if self.homing else 14
        return math.hypot(self.target.x - self.x, self.target.y - self.y) < radius

    def off_screen(self):
        return not (0 <= self.x <= WIDTH and 0 <= self.y <= HEIGHT)

    def draw(self):
        if self.triangle_shell:
            # Isosceles triangle pointing in direction of motion
            ang = math.atan2(self.vy, self.vx) if (self.vx or self.vy) else 0
            tip = (self.x + math.cos(ang) * 9, self.y + math.sin(ang) * 9)
            left = (self.x + math.cos(ang + 2.6) * 6, self.y + math.sin(ang + 2.6) * 6)
            right = (self.x + math.cos(ang - 2.6) * 6, self.y + math.sin(ang - 2.6) * 6)
            pygame.draw.polygon(screen, self.color, [tip, left, right])
            pygame.draw.polygon(screen, (80, 30, 0), [tip, left, right], 1)
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 5)


# ── Goblin Loader (carries airstrike ammo from builder hut) ───────────────────
class GoblinLoader:
    """Walks between a builder hut and the airstrike, ferrying ammo one at a time."""
    def __init__(self, airstrike, hut, speed=1.0):
        self.airstrike = airstrike
        self.hut = hut
        self.x = float(hut.x)
        self.y = float(hut.y)
        self.speed = speed
        self.carrying = 0  # 0 = empty, 1 = carrying one ammo
        self.state = "to_hut"  # "to_hut" or "to_airstrike"
        self.alive = True

    def _find_nearest_hut(self):
        huts = [t for t in towers if t.type == "builder_hut" and t.health > 0]
        if not huts:
            return None
        return min(huts, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))

    def update(self):
        if not self.airstrike or self.airstrike.health <= 0:
            self.alive = False
            return
        if not self.hut or self.hut.health <= 0:
            new_hut = self._find_nearest_hut()
            if not new_hut:
                # No hut available; loader idles next to airstrike
                self.hut = None
                return
            self.hut = new_hut
        # Idle at hut once airstrike is fully loaded
        if self.airstrike.ammo >= self.airstrike.max_ammo and self.carrying == 0:
            self.state = "to_hut"
            dx = self.hut.x - self.x
            dy = self.hut.y - self.y
            d = math.hypot(dx, dy)
            spd = self.speed * (2 if speed_2x else 1)
            if d > 4:
                self.x += dx / d * spd
                self.y += dy / d * spd
            return
        target_x = self.hut.x if self.state == "to_hut" else self.airstrike.x
        target_y = self.hut.y if self.state == "to_hut" else self.airstrike.y
        dx = target_x - self.x
        dy = target_y - self.y
        d = math.hypot(dx, dy)
        spd = self.speed * (2 if speed_2x else 1)
        if d > 4:
            self.x += dx / d * spd
            self.y += dy / d * spd
        else:
            if self.state == "to_hut":
                # Only pick up ammo if airstrike still needs some
                if self.airstrike.ammo < self.airstrike.max_ammo:
                    self.carrying = 1
                    self.state = "to_airstrike"
            else:
                if self.airstrike.ammo < self.airstrike.max_ammo:
                    self.airstrike.ammo += 1
                self.carrying = 0
                self.state = "to_hut"

    def draw(self):
        ix, iy = int(self.x), int(self.y)
        # Goblin body
        pygame.draw.circle(screen, (60, 140, 50), (ix, iy), 7)
        pygame.draw.circle(screen, (20, 70, 20), (ix, iy), 7, 2)
        # Eyes
        pygame.draw.circle(screen, WHITE, (ix - 2, iy - 2), 1)
        pygame.draw.circle(screen, WHITE, (ix + 2, iy - 2), 1)
        # Carrying ammo indicator above head — small isosceles triangle (rocket)
        if self.carrying > 0:
            pts = [(ix, iy - 16), (ix - 3, iy - 10), (ix + 3, iy - 10)]
            pygame.draw.polygon(screen, ORANGE, pts)
            pygame.draw.polygon(screen, (120, 60, 0), pts, 1)


# ── Tower ─────────────────────────────────────────────────────────────────────
class Tower:
    def __init__(self, x, y, range_, damage, cooldown, tower_type, cost):
        self.x, self.y = x, y
        self.range = range_
        self.damage = damage
        self.cooldown = cooldown
        self.timer = 0
        self.type = tower_type
        self.cost = cost
        self.bullets = []
        self.kills = 0  # lifetime enemy kills attributed to this tower
        self.goblins = []
        self.goblin_timer = 0
        self.builders = []
        self.builder_timer = 0
        self.builder_respawn_wave = 0
        self.helpers = []  # Pristine Builder Hut companion(s)
        self.chimney_smoke = []  # list of (x,y,age) puffs
        self.max_health = max(100, cost // 20)
        self.health = self.max_health
        self.level = 1
        self.max_level = 11 if tower_type == "gunner" else 10
        self.upgrade_cost_spent = 0
        self.muzzle_flash_timer = 0
        self.muzzle_flash_pos = None
        self.turret_angle = 0.0  # rad — direction turret/base faces (towards last target)
        self.bullets_per_shot = 1  # gunner upgrades raise this
        # Frost Laser visuals / aura
        self.spin_angle = 0.0
        self.frost_zap_timer = 0
        # Goblin Hut upgrade tracking
        self.goblin_tier = 0  # 0=basic 1=upgraded 2=elite
        self.max_goblins = 3
        # Builder Hut upgrade tracking
        self.builder_upgraded = False
        self.homing = False
        # ── Pristine upgrade fields ───────────────────────────────────────────
        self.pristine = None              # None | "bronze" | "silver" | "gold"
        self.stun_frames = 0              # sniper: frames of stun applied per hit
        self.shrap_dmg = 0                # heavy MG: AoE shrapnel damage on impact
        self.pierce = 0                   # heavy MG: extra enemies a bullet can pierce
        self.spray = False                # gunner gold: 3-direction spray
        self.turret_count = 1             # MG/airstrike: number of barrels visible
        self.spin_turrets = False         # MG gold: spinning gold turrets
        self.fire_dps = 0                 # airstrike: fire trail dmg/sec (legacy, unused)
        self.splash_bonus = 0             # airstrike: extra splash radius
        # Pristine airstrike: ammo + goblin loader system
        self.has_loader = False           # airstrike pristine: needs goblin loader
        self.load_speed = 0.0             # loader walking speed
        self.max_ammo = 0                 # max airstrike ammo
        self.ammo = 0                     # current loaded ammo
        self.burst_fire = False           # airstrike gold: 3-shot burst per round
        self.airstrike_turret_idx = 0     # airstrike gold: which turret fires next
        self.airstrike_burst_left = 0     # how many shots remaining in current burst
        self.assembly_angle = 0.0         # airstrike gold: current rotation of 3-turret assembly
        self.loader = None                # GoblinLoader instance
        self.gob_dmg_bonus = 0            # goblin hut: per-goblin dmg bonus
        self.barb_throw_chance = 0        # goblin hut: % to throw a sword
        self.spike_count = 0              # goblin hut: spinning spikes around hut
        self.heal_amount = 0              # builder hut helper: heal per tick
        self.heal_interval = 0            # builder hut helper: ticks between heals
        self.heal_timer = 0
        self.chimney_distractor = False
        self.instant_heal_chance = 0
        self.extra_valkyries = 0
        self.barbaric_valk = False
        self.split_barbarians = 0
        self.frost_slow_bonus = 0.0       # frost laser pristine: extra slow
        self.frost_chain_bonus = 0
        self.frost_freeze = False
        self.freeze_timer = 0
        # Valkyrie Hut tracking
        if tower_type == "Valkyrie Hut":
            self.max_level = 7
            self.valk_built = False
            self.valk_kills = 0
            self.valk_kills_needed = 100
            self.valkyries = []
            self.valk_speed = 2.5
            self.valk_combined = False
            self.barbarians_spawned = []
        else:
            self.valk_built = False
            self.valk_kills = 0
            self.valk_kills_needed = 100
            self.valkyries = []
            self.valk_speed = 2.5
            self.valk_combined = False
            self.barbarians_spawned = []

    def take_damage(self, amt):
        self.health = max(0, self.health - amt)

    def upgrade(self):
        global coins
        if self.level >= self.max_level:
            return
        # Valkyrie Hut cannot be upgraded while it is still being built
        if self.type == "Valkyrie Hut" and not self.valk_built:
            return
        lvl_index = self.level - 1  # 0..5 for levels 1→7
        table = UPGRADE_TABLE.get(self.type, [])
        if lvl_index >= len(table):
            return
        info = table[lvl_index]
        # Blood upgrades require blood storm to be active
        if info.get("blood") and not blood_storm_active:
            return
        # Pristine upgrades require shadow storm to be active
        if info.get("pristine") and not shadow_storm_active:
            return
        # Pristine airstrike requires a builder hut (for goblin loader)
        if info.get("loader") and self.type == "airstrike":
            if not any(t.type == "builder_hut" and t.health > 0 for t in towers):
                return
        if coins < info["cost"]:
            return
        coins -= info["cost"]
        self.upgrade_cost_spent += info["cost"]

        # Apply generic bonuses
        self.damage += info["damage"]
        self.range += info["range"]
        self.max_health += info["health"]
        self.health += info["health"]

        # ── Pristine ability application (works for all towers) ──────────────
        if info.get("pristine"):
            self.pristine = info["pristine"]
            if "stun" in info:
                self.stun_frames = info["stun"]
            if "shrap" in info:
                self.shrap_dmg = info["shrap"]
            if "pierce" in info:
                self.pierce = info["pierce"]
            if "spray" in info:
                self.spray = True
            if "turrets" in info:
                self.turret_count = info["turrets"]
            if "spin" in info:
                self.spin_turrets = True
            if "fire" in info:
                self.fire_dps = info["fire"]
            if "splash_bonus" in info:
                self.splash_bonus = info["splash_bonus"]
            if info.get("loader"):
                self.has_loader = True
                self.load_speed = info.get("load_speed", 1.0)
                self.max_ammo = info.get("max_ammo", 3)
                if self.ammo == 0:
                    self.ammo = self.max_ammo  # start fully loaded
                # Spawn the goblin loader from the nearest builder hut
                if self.type == "airstrike" and self.loader is None:
                    _huts = [t for t in towers if t.type == "builder_hut" and t.health > 0]
                    if _huts:
                        _h = min(_huts, key=lambda t: math.hypot(t.x - self.x, t.y - self.y))
                        self.loader = GoblinLoader(self, _h, self.load_speed)
                elif self.loader is not None:
                    # Update existing loader's speed when upgrading tier
                    self.loader.speed = self.load_speed
            if info.get("burst_fire"):
                self.burst_fire = True
            if "gob_dmg" in info:
                self.gob_dmg_bonus = info["gob_dmg"]
            if "barb_chance" in info:
                self.barb_throw_chance = info["barb_chance"]
                # Convert existing goblins to barbarians so visuals update immediately
                if self.type == "Goblin Hut":
                    for _g in self.goblins:
                        if not getattr(_g, "barbarian", False):
                            _g.barbarian = True
                            _g.max_health = int(_g.max_health * 3)
                            _g.health = _g.max_health
            if "spikes" in info:
                self.spike_count = info["spikes"]
            if "heal" in info:
                self.heal_amount, self.heal_interval = info["heal"]
                # Builder Hut: spawn / refresh helper companion
                if self.type == "builder_hut":
                    if not self.helpers:
                        self.helpers.append(Helper(self.x, self.y, self.heal_amount, self.heal_interval))
                    else:
                        for h in self.helpers:
                            h.heal_amount = self.heal_amount
                            h.heal_interval = self.heal_interval
            if "chimney" in info:
                self.chimney_distractor = True
            if "instant_chance" in info:
                self.instant_heal_chance = info["instant_chance"]
            if "extra_valk" in info:
                self.extra_valkyries += info["extra_valk"]
            if "barbaric" in info:
                self.barbaric_valk = True
            if "split_barbs" in info:
                self.split_barbarians = info["split_barbs"]
            if "slow_bonus" in info:
                self.frost_slow_bonus += info["slow_bonus"]
            if "chain_bonus" in info:
                self.frost_chain_bonus += info["chain_bonus"]
            if "freeze" in info:
                self.frost_freeze = True
            # Apply per-goblin damage bonus if Goblin Hut
            if self.type == "Goblin Hut" and "gob_dmg" in info:
                for g in self.goblins:
                    g.attack_damage += info["gob_dmg"]

        # ── Goblin Hut ────────────────────────────────────────────────────────
        if self.type == "Goblin Hut":
            if self.level == 1:
                self.max_goblins = 5
                self.goblin_tier = 1
                gc = GOBLIN_COLORS[1]
                for g in self.goblins:
                    g.tier = 1
                    g.max_health = 150
                    g.attack_damage = 50
                    g.color = gc
            elif self.level == 2:
                self.goblin_tier = 2
                self.max_health = max(self.max_health, 800)
                self.health = min(self.health + 650, self.max_health)
                gc = GOBLIN_COLORS[2]
                for g in self.goblins:
                    g.tier = 2
                    g.max_health = 220
                    g.attack_damage = 80
                    g.color = gc
                    g.speed = 3
            elif self.level == 3:
                self.goblin_tier = 3
                gc = GOBLIN_COLORS[3]
                for g in self.goblins:
                    g.tier = 3
                    g.max_health = 400
                    g.attack_damage = 120
                    g.speed = 5.0
                    g.color = gc
            elif self.level == 4:  # blood tier 1
                self.goblin_tier = 4
                self.max_goblins = 7
                gc = GOBLIN_COLORS[4]
                for g in self.goblins:
                    g.tier = 4
                    g.max_health = 600
                    g.attack_damage = 200
                    g.color = gc
                    g.speed = 5.5
            elif self.level == 5:  # blood tier 2
                self.goblin_tier = 5
                gc = GOBLIN_COLORS[5]
                for g in self.goblins:
                    g.tier = 5
                    g.max_health = 1200
                    g.attack_damage = 400
                    g.color = gc
                    g.speed = 6.5
            elif self.level == 6:  # blood tier 3
                self.goblin_tier = 5
                self.max_goblins = 9
                gc = GOBLIN_COLORS[5]
                for g in self.goblins:
                    g.tier = 5
                    g.max_health = 2000
                    g.attack_damage = 600
                    g.color = gc
                    g.speed = 7.0

        # ── Builder Hut ───────────────────────────────────────────────────────
        elif self.type == "builder_hut":
            if self.level == 1:
                self.builder_upgraded = True
            for b in self.builders:
                _apply_builder_level(b, self.level)

        # ── Valkyrie Hut ──────────────────────────────────────────────────────
        elif self.type == "Valkyrie Hut":
            if self.level == 1:
                self.valk_speed = 3.8
                for v in self.valkyries:
                    v.speed = self.valk_speed
            elif self.level == 2:
                self.valk_speed = 5.2
                for v in self.valkyries:
                    v.speed = self.valk_speed
            # Level 3 is handled by _do_goblin_combine — don't auto-upgrade

        # ── Sniper ────────────────────────────────────────────────────────────
        elif self.type == "sniper":
            self.cooldown = max(15, self.cooldown - 10)

        # ── Airstrike ─────────────────────────────────────────────────────────
        elif self.type == "airstrike":
            self.cooldown = max(30, self.cooldown - 15)

        # ── Gunner — sputter bullets per shot ────────────────────────────────
        if self.type == "gunner" and "bullets" in info:
            self.bullets_per_shot = info["bullets"]

        # Homing — explicit per-upgrade flag, plus legacy Blood Tier 2 (level 5→6) for non-gunners
        if info.get("homing"):
            self.homing = True
        elif self.level == 5 and self.type not in ("Goblin Hut", "builder_hut", "Valkyrie Hut", "gunner"):
            self.homing = True

        self.level += 1

    def _do_goblin_combine(self):
        """Called when a maxed Goblin Hut is merged into this Valkyrie Hut."""
        self.level = 4  # max level
        self.valk_combined = True
        self.valk_speed = 7.0
        # Replace valkyries: 2 minion-focus + 3 raider-focus, all souped up
        self.valkyries = []
        for i in range(2):
            v = Valkyrie(self.x + random.randint(-25, 25), self.y + random.randint(-25, 25), "minion_focus")
            v.parent_hut = self
            v.speed = self.valk_speed
            v.damage = 600
            v.home_x = self.x
            v.home_y = self.y
            self.valkyries.append(v)
        for i in range(3):
            v = Valkyrie(self.x + random.randint(-25, 25), self.y + random.randint(-25, 25), "raider_focus")
            v.parent_hut = self
            v.speed = self.valk_speed
            v.damage = 600
            v.home_x = self.x
            v.home_y = self.y
            self.valkyries.append(v)

    def _shoot_tower_attackers_first(self, enemies):
        """Return enemies sorted so tower-attackers are targeted first."""
        return sorted(enemies, key=lambda e: (0 if (getattr(e, "targets_towers", False) or getattr(e, "is_tower_raider", False)) else 1, math.hypot(e.x - self.x, e.y - self.y)))

    def shoot(self, enemies_list):
        # ── Goblin loader (airstrike pristine) ────────────────────────────────
        if self.loader is not None:
            self.loader.update()
            if not self.loader.alive:
                self.loader = None

        # ── Frost Laser aura ──────────────────────────────────────────────────
        if self.type == "frost_laser":
            self.spin_angle = (self.spin_angle + (0.04 * (2 if speed_2x else 1))) % (2 * math.pi)
            slow_table = [0.55, 0.50, 0.45, 0.40, 0.35, 0.30]
            slow_mult = slow_table[min(self.level - 1, len(slow_table) - 1)]
            slow_mult = max(0.05, slow_mult - getattr(self, "frost_slow_bonus", 0.0))
            for _fe in enemies_list:
                if _fe.health > 0 and math.hypot(_fe.x - self.x, _fe.y - self.y) <= self.range:
                    _fe.frost_slow_mult = min(getattr(_fe, "frost_slow_mult", 1.0), slow_mult)
                    # Lvl 3+: disable enemy abilities while in range
                    if self.level >= 3:
                        _fe.frost_disabled = True
            # Pristine Gold: freeze (1s stun) every 3 sec to all enemies in range
            if self.frost_freeze:
                self.freeze_timer += 2 if speed_2x else 1
                if self.freeze_timer >= 180:  # 3 seconds
                    self.freeze_timer = 0
                    for _fe in enemies_list:
                        if _fe.health > 0 and math.hypot(_fe.x - self.x, _fe.y - self.y) <= self.range:
                            _fe.stun_timer = max(getattr(_fe, "stun_timer", 0), 60)
            # Gold Pristine: zap 3 enemies at once (electric beams, NOT projectiles)
            if self.pristine == "gold":
                self.timer += 2 if speed_2x else 1
                gold_cd = 30  # zap every 30 ticks (~0.5s)
                if self.timer >= gold_cd:
                    self.timer = 0
                    _gold_cands = sorted(
                        [e for e in enemies_list if e.health > 0 and math.hypot(e.x - self.x, e.y - self.y) <= self.range and not getattr(e, "phase_immune", False)],
                        key=lambda e: math.hypot(e.x - self.x, e.y - self.y)
                    )
                    if _gold_cands:
                        _gold_zap_lines = []
                        _gold_used = set()
                        for _fi in range(3):
                            _gold_avail = [e for e in _gold_cands if id(e) not in _gold_used]
                            if not _gold_avail:
                                break
                            _gtarget = _gold_avail[0]
                            _gold_used.add(id(_gtarget))
                            _eff_f = max(1, int(self.damage * (1.0 - _fi * 0.1)))
                            _was_alive_z = _gtarget.health > 0
                            _gtarget.health -= _eff_f
                            if _was_alive_z and _gtarget.health <= 0:
                                self.kills += 1
                            _gold_zap_lines.append((self.x, self.y))
                            _gold_zap_lines.append((_gtarget.x, _gtarget.y))
                        if _gold_zap_lines:
                            self.zap_lines = _gold_zap_lines
                            self.zap_flash = 8
                        self.turret_angle = math.atan2(_gold_cands[0].y - self.y, _gold_cands[0].x - self.x)

            # Blood/Pristine non-gold tiers: 3 separate electric zap beams each in a different direction
            elif self.level >= 4:
                self.frost_zap_timer += 2 if speed_2x else 1
                zap_interval = {4: 300, 5: 240, 6: 180, 7: 150, 8: 120, 9: 90, 10: 60}.get(self.level, 300)
                if self.frost_zap_timer >= zap_interval:
                    self.frost_zap_timer = 0
                    chain_counts = {4: 3, 5: 4, 6: 5, 7: 6, 8: 8, 9: 9, 10: 10}
                    _n_beams = min(3, chain_counts.get(self.level, 3) + getattr(self, "frost_chain_bonus", 0))
                    _candidates = sorted(
                        [e for e in enemies_list if e.health > 0 and math.hypot(e.x - self.x, e.y - self.y) <= self.range],
                        key=lambda e: math.hypot(e.x - self.x, e.y - self.y)
                    )
                    _zapped = []
                    if _candidates:
                        _zap_lines = [(self.x, self.y)]
                        # Fire up to _n_beams separate zaps, each in a different direction
                        _used_ids = set()
                        for _bi in range(_n_beams):
                            # Pick enemy NOT yet zapped, farthest angle from previous
                            _avail = [e for e in _candidates if id(e) not in _used_ids]
                            if not _avail:
                                break
                            if _bi == 0:
                                _e = _avail[0]  # closest first
                            else:
                                # Pick the one with most different angle to previous zap target
                                _prev_ang = math.atan2(_zapped[-1].y - self.y, _zapped[-1].x - self.x)
                                _e = max(_avail, key=lambda e: abs(math.atan2(e.y - self.y, e.x - self.x) - _prev_ang))
                            _used_ids.add(id(_e))
                            _wa_zap = _e.health > 0
                            _e.health -= self.damage
                            if _wa_zap and _e.health <= 0:
                                self.kills += 1
                            _zapped.append(_e)
                            # Each zap line goes directly from tower to its target (not chained)
                            _zap_lines.append((self.x, self.y))
                            _zap_lines.append((_e.x, _e.y))
                        if not hasattr(self, "zap_lines"):
                            self.zap_lines = []
                        self.zap_lines = _zap_lines
                        self.zap_flash = 8
            if hasattr(self, "zap_flash") and self.zap_flash > 0:
                self.zap_flash -= 1
                if hasattr(self, "zap_lines") and len(self.zap_lines) >= 2:
                    # zap_lines is a flat list of paired points: [from, to, from, to, ...]
                    _zl = self.zap_lines
                    for _zi in range(0, len(_zl) - 1, 2):
                        p1 = (int(_zl[_zi][0]), int(_zl[_zi][1]))
                        p2 = (int(_zl[_zi + 1][0]), int(_zl[_zi + 1][1]))
                        pygame.draw.line(screen, (20, 80, 255), p1, p2, 7)
                        pygame.draw.line(screen, (120, 220, 255), p1, p2, 3)
            # Move and resolve frost_laser projectile bullets (gold pristine 3-laser)
            # The regular shooting block below excludes "frost_laser", so without
            # this loop our self.bullets would never move or apply damage.
            if self.bullets:
                for _b in self.bullets[:]:
                    _b.move()
                    if _b.off_screen():
                        self.bullets.remove(_b)
                        continue
                    if _b.hit() and _b.target:
                        if _b.target.health > 0 and not getattr(_b.target, "phase_immune", False):
                            _dr_fl = getattr(_b.target, "damage_reduction", 0.0)
                            _b.target.health -= max(1, int(_b.damage * (1.0 - _dr_fl)))
                            if _b.target.health <= 0 and _b.owner is not None:
                                _b.owner.kills += 1
                        if _b in self.bullets:
                            self.bullets.remove(_b)

        # ── Shooting logic ────────────────────────────────────────────────────
        if self.type not in ("Goblin Hut", "builder_hut", "Valkyrie Hut", "frost_laser"):
            # Regular towers cannot see tower_raiders or minion-type enemies
            visible = [e for e in enemies_list if not getattr(e, "is_tower_raider", False) and not getattr(e, "is_minion", False)]
            sorted_enemies = self._shoot_tower_attackers_first(visible)
            _aura_mult = getattr(self, "aura_fire_mult", 1.0)
            if self.timer <= 0:
                # Pick up to bullets_per_shot in-range eligible targets (closest first / raiders first)
                in_range = []
                for enemy in sorted_enemies:
                    if math.hypot(enemy.x - self.x, enemy.y - self.y) >= self.range:
                        continue
                    if enemy.visible_to == "sniper_only" and self.type not in ("sniper", "airstrike"):
                        continue
                    if getattr(enemy, "phase_immune", False):
                        continue
                    in_range.append(enemy)
                    if len(in_range) >= max(1, self.bullets_per_shot):
                        break
                # Airstrike pristine: must have ammo to fire (loaded by goblin)
                if self.type == "airstrike" and self.has_loader and self.ammo <= 0:
                    in_range = []
                    self.timer = 20
                # Gold airstrike (3 turret assembly): rotate-to-aim before firing.
                # The whole assembly turns until the active turret points at the enemy,
                # only then does it shoot. After firing, the next turret becomes active
                # and the assembly rotates again to bring it onto the target.
                if self.type == "airstrike" and self.turret_count >= 3 and in_range:
                    _primary_aim = in_range[0]
                    _target_angle = math.atan2(_primary_aim.y - self.y, _primary_aim.x - self.x)
                    _ti = self.airstrike_turret_idx
                    _desired_assembly = _target_angle - _ti * (2 * math.pi / 3)
                    _diff = (_desired_assembly - self.assembly_angle + math.pi) % (2 * math.pi) - math.pi
                    _rot_speed = 0.10 * (2 if speed_2x else 1)
                    if abs(_diff) <= _rot_speed:
                        self.assembly_angle = _desired_assembly
                    else:
                        self.assembly_angle += _rot_speed * (1 if _diff > 0 else -1)
                        # Not aligned yet — don't fire this frame
                        in_range = []
                if in_range:
                    primary = in_range[0]
                    self.turret_angle = math.atan2(primary.y - self.y, primary.x - self.x)
                    # Gold airstrike: muzzle is at the active turret's outward edge
                    if self.type == "airstrike" and self.turret_count >= 3:
                        _ti = self.airstrike_turret_idx
                        _t_world = self.assembly_angle + _ti * (2 * math.pi / 3)
                        _toff_r = 22
                        _t_cx = self.x + math.cos(_t_world) * _toff_r
                        _t_cy = self.y + math.sin(_t_world) * _toff_r
                        # Muzzle hole sits a few px past the turret center, outward
                        mx = _t_cx + math.cos(_t_world) * 6
                        my = _t_cy + math.sin(_t_world) * 6
                        # Advance to next turret for the next shot
                        self.airstrike_turret_idx = (_ti + 1) % 3
                    else:
                        # Muzzle position out the front of the base (aligned with turret_angle)
                        mx_off = {"gunner": 22, "sniper": 28, "machine_gun": 22, "heavy_machine_gun": 28, "airstrike": 24}.get(self.type, 18)
                        mx = self.x + math.cos(self.turret_angle) * mx_off
                        my = self.y + math.sin(self.turret_angle) * mx_off
                    # Machine Gun Pristine Gold: spray up to 8 bullets, each targeting a different
                    # in-range enemy; travel straight for 1 second then become homing
                    if self.type == "machine_gun" and self.spin_turrets:
                        _mg_visible = [e for e in sorted_enemies if math.hypot(e.x - self.x, e.y - self.y) < self.range and not getattr(e, "phase_immune", False)]
                        _mg_targets = _mg_visible[:8]
                        _mg_used_ids = set()
                        for _mgi in range(8):
                            if _mgi < len(_mg_targets):
                                _mg_t = _mg_targets[_mgi]
                                _mg_used_ids.add(id(_mg_t))
                                _bmg = Bullet(self.x, self.y, _mg_t, max(1, int(self.damage * 0.65)), (150, 255, 80), homing=True, homing_delay=60, owner=self)
                            else:
                                # Fill remaining slots with directional bullets toward nearest enemy
                                _ang_mg = self.spin_angle + _mgi * math.pi / 4
                                _bmg = Bullet(self.x, self.y, None, max(1, int(self.damage * 0.5)), (120, 220, 60), owner=self)
                                _bmg.vx = math.cos(_ang_mg) * 8
                                _bmg.vy = math.sin(_ang_mg) * 8
                            self.bullets.append(_bmg)
                    else:
                        for enemy in in_range:
                            _dr = getattr(enemy, "damage_reduction", 0.0)
                            if self.type == "sniper":
                                eff_dmg = max(1, int(self.damage * (1.0 - _dr)))
                                self.bullets.append(Bullet(mx, my, enemy, eff_dmg, BLUE, homing=self.homing, stun=self.stun_frames, owner=self))
                            elif self.type == "airstrike":
                                splash_extra = self.splash_bonus
                                eff_dmg = max(1, int((self.damage + 500) * (1.0 - _dr)))
                                # Gold: triangular shell visual flag
                                _gold_air = (self.turret_count >= 3)
                                b = Bullet(mx, my, enemy, eff_dmg, ORANGE, splash=True, homing=self.homing, owner=self)
                                if splash_extra:
                                    b.splash_r += splash_extra
                                if _gold_air:
                                    b.triangle_shell = True
                                self.bullets.append(b)
                                # Consume one ammo per shot
                                if self.has_loader:
                                    self.ammo = max(0, self.ammo - 1)
                            elif self.type == "heavy_machine_gun" and (self.shrap_dmg > 0 or self.pierce > 0 or self.homing):
                                # Pristine heavy MG: real travelling bullet that can pierce / detonate shrapnel
                                bc = YELLOW
                                eff_dmg = max(1, int(self.damage * (1.0 - _dr)))
                                self.bullets.append(Bullet(mx, my, enemy, eff_dmg, bc, homing=self.homing, shrap=self.shrap_dmg, pierce=self.pierce, owner=self))
                            else:
                                if self.type == "machine_gun":
                                    bc = DARK_GREEN
                                else:
                                    bc = YELLOW
                                eff_dmg = max(1, int(self.damage * (1.0 - _dr)))
                                # Gunner: ALL bullets are homing
                                _hm = True if self.type == "gunner" else self.homing
                                self.bullets.append(Bullet(mx, my, enemy, eff_dmg, bc, homing=_hm, owner=self))
                    # Gunner Pristine Gold: spray 2 extra fans 30° to either side (homing)
                    if self.type == "gunner" and self.spray and in_range:
                        primary = in_range[0]
                        for ang_off in (math.radians(30), math.radians(-30)):
                            for _ in range(self.bullets_per_shot):
                                # Homing bullet — keeps target so it tracks
                                b = Bullet(mx, my, primary, max(1, int(self.damage * 0.7)), YELLOW, homing=True, owner=self)
                                # Initial velocity offset by ±30° from target direction
                                base_ang = math.atan2(primary.y - self.y, primary.x - self.x)
                                ang = base_ang + ang_off
                                b.vx = math.cos(ang) * 8
                                b.vy = math.sin(ang) * 8
                                self.bullets.append(b)
                    self.timer = int(self.cooldown * _aura_mult)
                    # No muzzle flash for airstrike (it creates distracting flicker)
                    if self.type != "airstrike":
                        self.muzzle_flash_pos = (int(mx), int(my))
                        self.muzzle_flash_timer = 5
            else:
                self.timer = max(0, self.timer - (2 if speed_2x else 1))

            for b in self.bullets[:]:
                b.move()
                # Collateral damage: bullet damages non-targeted enemies it passes through
                if b.damage > 0 and not b.splash:
                    for _col_e in enemies_list:
                        if _col_e is b.target or _col_e.health <= 0 or id(_col_e) in b._hit_set:
                            continue
                        if math.hypot(_col_e.x - b.x, _col_e.y - b.y) < 11:
                            if not getattr(_col_e, "phase_immune", False):
                                _dr_col = getattr(_col_e, "damage_reduction", 0.0)
                                _col_e.health -= max(1, int(b.damage * 0.5 * (1.0 - _dr_col)))
                                b._hit_set.add(id(_col_e))
                if b.hit():
                    if b.splash:
                        for e in enemies_list:
                            if math.hypot(e.x - b.x, e.y - b.y) < b.splash_r:
                                _dr2 = getattr(e, "damage_reduction", 0.0)
                                if not getattr(e, "phase_immune", False):
                                    _was_alive = e.health > 0
                                    e.health -= max(1, int(b.damage * (1.0 - _dr2)))
                                    if _was_alive and e.health <= 0 and b.owner is not None:
                                        b.owner.kills += 1
                        self.bullets.remove(b)
                    elif b.damage > 0:
                        if b.target and not getattr(b.target, "phase_immune", False):
                            _was_alive = b.target.health > 0
                            b.target.health -= b.damage  # damage already scaled at creation
                            if _was_alive and b.target.health <= 0 and b.owner is not None:
                                b.owner.kills += 1
                            if b.stun > 0:
                                b.target.stun_timer = max(getattr(b.target, "stun_timer", 0), b.stun)
                            if b.shrap > 0:
                                for e in enemies_list:
                                    if e is b.target or e.health <= 0:
                                        continue
                                    if math.hypot(e.x - b.x, e.y - b.y) < 70:
                                        _dr3 = getattr(e, "damage_reduction", 0.0)
                                        if not getattr(e, "phase_immune", False):
                                            _wsa = e.health > 0
                                            e.health -= max(1, int(b.shrap * (1.0 - _dr3)))
                                            if _wsa and e.health <= 0 and b.owner is not None:
                                                b.owner.kills += 1
                            if b.pierce > 0:
                                b._hit_set.add(id(b.target))
                                b.pierce -= 1
                                _next, _bd = None, 1e9
                                for e in enemies_list:
                                    if e.health <= 0 or id(e) in b._hit_set:
                                        continue
                                    _d = math.hypot(e.x - b.x, e.y - b.y)
                                    if _d < _bd and _d < 220:
                                        _bd, _next = _d, e
                                if _next:
                                    b.target = _next
                                    if not b.homing:
                                        ang = math.atan2(_next.y - b.y, _next.x - b.x)
                                        b.vx = math.cos(ang) * b.speed
                                        b.vy = math.sin(ang) * b.speed
                                else:
                                    self.bullets.remove(b)
                            else:
                                self.bullets.remove(b)
                        else:
                            self.bullets.remove(b)
                    else:
                        self.bullets.remove(b)
                elif b.off_screen():
                    self.bullets.remove(b)

        # ── Goblin Hut ───────────────────────────────────────── ��──────────────
        if self.type == "Goblin Hut":
            self.goblin_timer += 2 if speed_2x else 1
            if self.goblin_timer >= 600 and len(self.goblins) < self.max_goblins:
                ng = Goblin(self.x, self.y, self.goblin_tier)
                ng.parent_hut = self
                if self.barb_throw_chance > 0:
                    ng.barbarian = True
                    ng.max_health = int(ng.max_health * 3)
                    ng.health = ng.max_health
                    ng.attack_damage = int(ng.attack_damage * (1 + self.gob_dmg_bonus / 100.0))
                self.goblins.append(ng)
                self.goblin_timer = 0

            live = [e for e in enemies_list if e.health > 0]
            # All goblins prioritise tower raiders
            raiders = [e for e in live if getattr(e, "is_tower_raider", False)]
            pool = raiders if raiders else live
            n_e = len(pool)
            n_g = len(self.goblins)
            if n_g <= n_e or raiders:
                assigned = set()
                for g in self.goblins[:]:
                    avail = [e for e in pool if id(e) not in assigned]
                    if not avail:
                        avail = pool
                    g.update_unique(avail, enemies_list)
                    if g.target:
                        assigned.add(id(g.target))
                    if g.health <= 0:
                        self.goblins.remove(g)
            else:
                for i, g in enumerate(self.goblins[:]):
                    tgt_pool = [pool[i % n_e]] if pool else []
                    g.update_unique(tgt_pool, enemies_list)
                    if g.health <= 0:
                        self.goblins.remove(g)

        # ── Builder Hut ───────────────────────────────────────────────────────
        if self.type == "builder_hut":
            self.builder_timer += 2 if speed_2x else 1
            if len(self.builders) == 0 and wave_number >= self.builder_respawn_wave:
                if self.builder_timer >= 600:
                    nb = Builder(self.x, self.y, self.builder_upgraded)
                    nb.parent_hut = self
                    # Re-apply ALL upgrade levels so a builder spawning AFTER
                    # the hut was upgraded still gets the abilities.
                    for _lv in range(1, self.level + 1):
                        _apply_builder_level(nb, _lv)
                    # Pristine Gold instant-heal hook for builders
                    nb.instant_heal_chance = self.instant_heal_chance
                    self.builders.append(nb)
                    self.builder_timer = 0
            for b in self.builders[:]:
                # Pass instant heal chance through to live builders too
                b.instant_heal_chance = self.instant_heal_chance
                b.update(towers, enemies_list)
                if not b.alive:
                    self.builders.remove(b)
                    self.builder_respawn_wave = wave_number + 5
                    self.builder_timer = 0
            # Pristine Helper companion(s)
            for h in self.helpers[:]:
                h.update(towers)
                if not h.alive:
                    self.helpers.remove(h)
            # Chimney smoke + distractor (Pristine Silver+)
            if self.chimney_distractor:
                # Spawn a smoke puff every ~12 ticks
                if not hasattr(self, "_smoke_t"):
                    self._smoke_t = 0
                self._smoke_t += 2 if speed_2x else 1
                if self._smoke_t >= 12:
                    self._smoke_t = 0
                    self.chimney_smoke.append([self.x - 16, self.y - 24, 0])
                # Age & cull
                for puff in self.chimney_smoke[:]:
                    puff[2] += 1
                    puff[1] -= 0.6
                    puff[0] += random.uniform(-0.3, 0.3)
                    if puff[2] > 60:
                        self.chimney_smoke.remove(puff)

        # ── Valkyrie Hut ──────────────────────────────────────────────────────
        if self.type == "Valkyrie Hut":
            if not self.valk_built:
                # Assign nearest free builder to come here (only if none assigned yet)
                already_assigned = any(b.valk_target is self for bt in towers if bt.type == "builder_hut" for b in bt.builders)
                if not already_assigned:
                    for bt in towers:
                        if bt.type == "builder_hut":
                            for b in bt.builders:
                                if b.valk_target is None:
                                    b.valk_target = self
                                    break
                            else:
                                continue
                            break
                # Kill count tracked in main loop
            else:
                # Hut is built — update valkyries
                live_targets = [e for e in enemies_list if getattr(e, "health", 0) > 0]
                # Pristine barbaric activation chance (per pristine tier)
                _barb_chance = 0.0
                if self.barbaric_valk:
                    _barb_chance = {"bronze": 0.02, "silver": 0.06, "gold": 0.12}.get(self.pristine, 0.02)
                for i, v in enumerate(self.valkyries[:]):
                    # Push pristine fields onto the valk so it picks them up
                    v.barb_chance = _barb_chance
                    v.split_count = self.split_barbarians
                    assigned = live_targets[i % len(live_targets)] if live_targets else None
                    v.update(enemies_list, assigned)
                    if v.health <= 0:
                        # Pristine Gold split: spawn 3 barbarians on death
                        if self.split_barbarians > 0:
                            for _ in range(self.split_barbarians):
                                self.barbarians_spawned = self.barbarians_spawned + [Barbarian(v.x + random.randint(-10, 10), v.y + random.randint(-10, 10), damage=int(v.damage))]
                        self.valkyries.remove(v)
                # Update barbarians (gold pristine spawns)
                if not hasattr(self, "barbarians_spawned"):
                    self.barbarians_spawned = []
                for b in self.barbarians_spawned[:]:
                    b.update(enemies_list)
                    if not b.alive:
                        self.barbarians_spawned.remove(b)
                # Respawn: max 3 normally, 5 if combined; +extra_valkyries pristine bonus
                max_v = (5 if self.valk_combined else 3) + self.extra_valkyries
                if len(self.valkyries) < max_v and random.random() < 0.002:
                    mode = "raider_focus" if (self.valk_combined and len([x for x in self.valkyries if x.mode == "raider_focus"]) < 3) else "minion_focus"
                    # Pristine Silver+ valks prioritize tower raiders too
                    if self.pristine in ("silver", "gold") and len([x for x in self.valkyries if x.mode == "raider_focus"]) < (self.extra_valkyries + 1):
                        mode = "raider_focus"
                    v = Valkyrie(self.x + random.randint(-20, 20), self.y + random.randint(-20, 20), mode)
                    v.parent_hut = self
                    v.speed = self.valk_speed
                    v.home_x = self.x
                    v.home_y = self.y
                    if self.valk_combined:
                        v.damage = 600
                    # Pristine damage bonus from upgrade table is already on the hut;
                    # propagate damage so each fresh valk benefits.
                    if self.pristine:
                        v.damage = max(v.damage, 250 + self.damage)
                    v.barb_chance = _barb_chance
                    v.split_count = self.split_barbarians
                    self.valkyries.append(v)

    def draw(self):
        color_map = {
            "gunner": (0, 0, 255),
            "sniper": (0, 0, 150),
            "machine_gun": DARK_GREEN,
            "airstrike": ORANGE,
            "heavy_machine_gun": (100, 50, 0),
            "frost_laser": (80, 200, 240),
            "builder_hut": (180, 140, 50),
            "Valkyrie Hut": (160, 80, 220),
        }
        if self.type == "Goblin Hut":
            c = [(0, 150, 0), (50, 180, 50), GRAY, GRAY][min(self.level - 1, 3)]
        else:
            c = color_map.get(self.type, (0, 0, 255))

        # Frost Laser: always show spinning rings so the slow zone is visible.
        # When toggle is ON show full bright rings; when OFF show a faint translucent aura.
        if self.type == "frost_laser":
            if frost_show_circles:
                draw_frost_rings(self.x, self.y, int(self.range), self.spin_angle)
            else:
                _r = int(self.range)
                _aur = pygame.Surface((_r * 2 + 4, _r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(_aur, (80, 180, 255, 35), (_r + 2, _r + 2), _r)
                pygame.draw.circle(_aur, (140, 220, 255, 90), (_r + 2, _r + 2), _r, 2)
                screen.blit(_aur, (int(self.x) - _r - 2, int(self.y) - _r - 2))
                # Tiny rotating frost arc on the tower so user sees it's active
                pygame.draw.arc(screen, (140, 220, 255),
                                pygame.Rect(int(self.x) - 18, int(self.y) - 18, 36, 36),
                                self.spin_angle, self.spin_angle + math.pi / 2, 3)

        # Spinning turret animation tick (MG / airstrike gold)
        # MG only spins when a wave is active
        if self.spin_turrets:
            _wave_going = wave_active if state == "GAME" else arena_wave_active
            if self.type == "machine_gun":
                if _wave_going:
                    self.spin_angle = (self.spin_angle + 0.06) % (2 * math.pi)
            else:
                self.spin_angle = (self.spin_angle + 0.06) % (2 * math.pi)

        # Tower-base + turret artwork for shooting towers
        if self.type in ("gunner", "sniper", "machine_gun", "heavy_machine_gun", "airstrike"):
            if self.type == "machine_gun" and self.spin_turrets:
                # Pristine Gold MG: special rotating 8-barrel base
                draw_machine_gun_base(self.x, self.y, self.spin_angle)
            else:
                # ── Gunner: 2 small side turrets sitting UNDER the main base
                # (drawn first so the body sits on top — only the protruding bits show)
                if self.type == "gunner":
                    # Two small side turrets tucked UNDER the gunner body
                    # (drawn first so the body sits on top — only the protruding tips show)
                    g_turret_col = (60, 70, 200)
                    g_edge = (15, 25, 90)
                    g_hole = (10, 10, 30)
                    for _side_off in (math.pi / 2, -math.pi / 2):
                        a = self.turret_angle + _side_off
                        # Distance 11 keeps the turret centers inside the body so
                        # only the outer edges poke out from beneath the gunner
                        tx = self.x + math.cos(a) * 11
                        ty = self.y + math.sin(a) * 11
                        rect = pygame.Rect(int(tx - 6), int(ty - 6), 12, 12)
                        pygame.draw.rect(screen, g_turret_col, rect, border_radius=3)
                        pygame.draw.rect(screen, g_edge, rect, 2, border_radius=3)
                        # Small barrel hole pointing outward
                        hx = tx + math.cos(a) * 4
                        hy = ty + math.sin(a) * 4
                        pygame.draw.circle(screen, g_hole, (int(hx), int(hy)), 2)

                # ── Gold Airstrike: 3 rounded-square turrets around a circular base
                # (matches airstrike.png — rotates as a unit to aim before firing)
                if self.type == "airstrike" and self.turret_count >= 3:
                    base_r = 16
                    body_col = (220, 110, 30)
                    edge_col = (130, 60, 0)
                    turret_col = (175, 95, 25)
                    barrel_hole = (60, 30, 0)
                    turret_size = 14
                    turret_offset_r = 22
                    # Draw 3 turret blocks FIRST (under the base)
                    for i in range(3):
                        a = self.assembly_angle + i * (2 * math.pi / 3)
                        tx = self.x + math.cos(a) * turret_offset_r
                        ty = self.y + math.sin(a) * turret_offset_r
                        # Rounded-square turret block
                        rect = pygame.Rect(int(tx - turret_size / 2), int(ty - turret_size / 2),
                                           turret_size, turret_size)
                        pygame.draw.rect(screen, turret_col, rect, border_radius=4)
                        pygame.draw.rect(screen, edge_col, rect, 2, border_radius=4)
                        # Highlight the active firing turret
                        if i == self.airstrike_turret_idx:
                            hl = pygame.Rect(rect.x - 2, rect.y - 2, rect.w + 4, rect.h + 4)
                            pygame.draw.rect(screen, (255, 230, 100), hl, 2, border_radius=5)
                        # Barrel hole on the OUTWARD side of each turret
                        hx = tx + math.cos(a) * 5
                        hy = ty + math.sin(a) * 5
                        pygame.draw.circle(screen, barrel_hole, (int(hx), int(hy)), 3)
                        pygame.draw.circle(screen, edge_col, (int(hx), int(hy)), 3, 1)
                    # Central circular orange base on top
                    pygame.draw.circle(screen, body_col, (int(self.x), int(self.y)), base_r)
                    pygame.draw.circle(screen, edge_col, (int(self.x), int(self.y)), base_r, 3)
                    # Small inner hole detail (per airstrike.png)
                    pygame.draw.circle(screen, (170, 80, 20), (int(self.x), int(self.y)), 6)
                    pygame.draw.circle(screen, edge_col, (int(self.x), int(self.y)), 6, 1)
                else:
                    # ── Gunner Pristine Gold spray-fan: 2 extra barrels at ±25°
                    # Drawn FIRST so they tuck UNDER the main body
                    if self.spray:
                        fan_col = (255, 210, 65)
                        draw_extra_barrel(self.x, self.y, self.turret_angle + math.radians(25), fan_col, length=24, width=7)
                        draw_extra_barrel(self.x, self.y, self.turret_angle - math.radians(25), fan_col, length=24, width=7)

                    draw_tower_base(self.x, self.y, c, self.turret_angle)

                    # ── HMG final upgrade: stock detail (3 lines + 2 rectangles) on the back of the gun
                    if self.type == "heavy_machine_gun" and self.level >= self.max_level:
                        ba = self.turret_angle + math.pi  # back direction
                        cosA, sinA = math.cos(ba), math.sin(ba)
                        cosP, sinP = math.cos(ba + math.pi / 2), math.sin(ba + math.pi / 2)
                        stock_col = (60, 35, 15)
                        edge_col = (20, 10, 0)
                        # 2 stacked rectangles forming the gun stock/butt
                        for off, w, h in ((10, 8, 14), (20, 10, 16)):
                            ccx = self.x + cosA * off
                            ccy = self.y + sinA * off
                            pts = []
                            for sx, sy in ((-w, -h), (w, -h), (w, h), (-w, h)):
                                px = ccx + (cosA * sy + cosP * sx) * 0.5
                                py = ccy + (sinA * sy + sinP * sx) * 0.5
                                pts.append((int(px), int(py)))
                            pygame.draw.polygon(screen, stock_col, pts)
                            pygame.draw.polygon(screen, edge_col, pts, 2)
                        # 3 parallel detail lines across the stock (perpendicular to barrel)
                        for line_off in (12, 16, 20):
                            cx_l = self.x + cosA * line_off
                            cy_l = self.y + sinA * line_off
                            x1 = cx_l + cosP * 5
                            y1 = cy_l + sinP * 5
                            x2 = cx_l - cosP * 5
                            y2 = cy_l - sinP * 5
                            pygame.draw.line(screen, (200, 170, 60), (int(x1), int(y1)), (int(x2), int(y2)), 2)

                    # ── Multi-turret extras (MG / Airstrike pristine non-gold): N evenly-spaced barrels
                    if self.turret_count > 1:
                        # Tier-based barrel color
                        barrel_col = ((255, 210, 65) if self.pristine == "gold"
                                      else ((220, 220, 230) if self.pristine == "silver"
                                      else ((205, 130, 50) if self.pristine == "bronze" else c)))
                        base_angle = 0.0
                        # Skip index 0 — that's the main turret already drawn by draw_tower_base
                        for i in range(1, self.turret_count):
                            a = self.turret_angle + base_angle + (2 * math.pi * i / self.turret_count)
                            draw_extra_barrel(self.x, self.y, a, barrel_col,
                                              length=22 if self.type == "machine_gun" else 26,
                                              width=7 if self.type == "machine_gun" else 9)
        else:
            pygame.draw.circle(screen, c, (self.x, self.y), 15)
            # Pristine ring for maxed hut-type towers (builder_hut, goblin_hut, valkyrie_hut, frost_laser)
            if self.pristine and self.type in ("builder_hut", "Goblin Hut", "Valkyrie Hut", "frost_laser"):
                draw_pristine_ring(self.x, self.y, self.pristine, radius=22)
            # Frost Laser Pristine Gold: 3 concentric circles getting smaller on top of the base
            if self.type == "frost_laser" and self.pristine == "gold":
                for _fr, _fa in [(12, 200), (8, 180), (5, 220)]:
                    _fs = pygame.Surface((_fr * 2 + 2, _fr * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(_fs, (100, 220, 255, _fa), (_fr + 1, _fr + 1), _fr)
                    pygame.draw.circle(_fs, (20, 80, 200, 220), (_fr + 1, _fr + 1), _fr, 2)
                    screen.blit(_fs, (self.x - _fr - 1, self.y - _fr - 1))

            # Goblin Hut Pristine: spinning spikes around the hut (silver=4, gold=8)
            if self.type == "Goblin Hut" and self.spike_count > 0:
                self.spin_angle = (self.spin_angle + 0.05) % (2 * math.pi)
                spike_color = (255, 210, 65) if self.pristine == "gold" else (220, 220, 230)
                spike_dark = (180, 140, 20) if self.pristine == "gold" else (150, 150, 165)
                spike_radius = 28
                for i in range(self.spike_count):
                    a = self.spin_angle + i * (2 * math.pi / self.spike_count)
                    base_x = self.x + spike_radius * math.cos(a)
                    base_y = self.y + spike_radius * math.sin(a)
                    tip_x = self.x + (spike_radius + 12) * math.cos(a)
                    tip_y = self.y + (spike_radius + 12) * math.sin(a)
                    perp = a + math.pi / 2
                    side1 = (base_x + 4 * math.cos(perp), base_y + 4 * math.sin(perp))
                    side2 = (base_x - 4 * math.cos(perp), base_y - 4 * math.sin(perp))
                    pygame.draw.polygon(screen, spike_color,
                                        [(int(tip_x), int(tip_y)), (int(side1[0]), int(side1[1])), (int(side2[0]), int(side2[1]))])
                    pygame.draw.polygon(screen, spike_dark,
                                        [(int(tip_x), int(tip_y)), (int(side1[0]), int(side1[1])), (int(side2[0]), int(side2[1]))], 1)
        if self.type == "Valkyrie Hut":
            # Draw hut outline
            pygame.draw.circle(screen, (220, 160, 255), (self.x, self.y), 15, 2)
            # Draw valkyries
            for v in self.valkyries:
                v.draw()
            # Draw split-spawned barbarians (Pristine Gold)
            for b in getattr(self, "barbarians_spawned", []):
                b.draw()
            # If not yet built, draw scaffolding lines
            if not self.valk_built:
                for angle in [0, 60, 120, 180, 240, 300]:
                    a = math.radians(angle)
                    ex = int(self.x + 14 * math.cos(a))
                    ey = int(self.y + 14 * math.sin(a))
                    pygame.draw.line(screen, (180, 150, 80), (self.x, self.y), (ex, ey), 1)
        # Pristine Builder Hut visuals: helper hut + chimney + smoke
        if self.type == "builder_hut" and self.pristine:
            # Helper hut (small circle to the right + tool box)
            hh_x, hh_y = self.x + 30, self.y + 18
            pygame.draw.circle(screen, (200, 145, 35), (int(hh_x), int(hh_y)), 11)
            pygame.draw.circle(screen, (130, 80, 20), (int(hh_x), int(hh_y)), 11, 2)
            # Door/window (small square attached)
            pygame.draw.rect(screen, (180, 130, 40), (int(hh_x + 7), int(hh_y + 2), 10, 8))
            pygame.draw.rect(screen, (130, 80, 20), (int(hh_x + 7), int(hh_y + 2), 10, 8), 1)
            # Door on main hut
            pygame.draw.rect(screen, (160, 110, 30), (int(self.x - 4), int(self.y + 2), 8, 12))
            pygame.draw.rect(screen, (110, 70, 15), (int(self.x - 4), int(self.y + 2), 8, 12), 1)
        # Chimney (Silver+ pristine)
        if self.type == "builder_hut" and self.chimney_distractor:
            # Small grey rectangle on top-left of hut
            pygame.draw.rect(screen, (110, 110, 110), (int(self.x - 18), int(self.y - 22), 6, 10))
            pygame.draw.rect(screen, (60, 60, 60), (int(self.x - 18), int(self.y - 22), 6, 10), 1)
            # Smoke puffs
            for puff in self.chimney_smoke:
                age = puff[2]
                a = max(0, 220 - int(age * 3))
                rr = 3 + age // 8
                s = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
                pygame.draw.circle(s, (200, 200, 200, a), (rr + 1, rr + 1), rr)
                screen.blit(s, (int(puff[0]) - rr, int(puff[1]) - rr))
        for g in self.goblins:
            g.draw()
        for b in self.builders:
            b.draw()
        for h in self.helpers:
            h.draw()
        for b in self.bullets:
            b.draw()
        # Goblin loader + ammo display (airstrike pristine)
        if self.loader is not None:
            self.loader.draw()
        if self.has_loader and self.type == "airstrike":
            # Ammo dots above the tower
            for ai in range(self.max_ammo):
                ax = int(self.x - (self.max_ammo - 1) * 5 + ai * 10)
                ay = int(self.y - 30)
                if ai < self.ammo:
                    pygame.draw.circle(screen, ORANGE, (ax, ay), 4)
                    pygame.draw.circle(screen, (120, 60, 0), (ax, ay), 4, 1)
                else:
                    pygame.draw.circle(screen, (60, 60, 60), (ax, ay), 4)
                    pygame.draw.circle(screen, (30, 30, 30), (ax, ay), 4, 1)

        if self.muzzle_flash_timer > 0 and self.muzzle_flash_pos:
            fr = 10
            fs = pygame.Surface((fr * 2, fr * 2), pygame.SRCALPHA)
            pygame.draw.circle(fs, (255, 255, 100, 180), (fr, fr), fr)
            screen.blit(fs, (self.muzzle_flash_pos[0] - fr, self.muzzle_flash_pos[1] - fr))
            self.muzzle_flash_timer -= 1
            if self.muzzle_flash_timer == 0:
                self.muzzle_flash_pos = None

    def draw_health_bar(self):
        bar_x = self.x - 20
        bar_y = self.y - 25
        pygame.draw.rect(screen, RED, (bar_x, bar_y, 40, 5))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, int(40 * max(0, self.health / self.max_health)), 5))
        if self.type == "Valkyrie Hut" and not self.valk_built:
            prog = min(1.0, self.valk_kills / max(1, self.valk_kills_needed))
            pygame.draw.rect(screen, (60, 40, 10), (bar_x, bar_y - 8, 40, 4))
            pygame.draw.rect(screen, (255, 200, 50), (bar_x, bar_y - 8, int(40 * prog), 4))
            lbl = font_sm.render(f"Build {self.valk_kills}/{self.valk_kills_needed}", True, (255, 230, 120))
            screen.blit(lbl, (self.x - lbl.get_width() // 2, bar_y - 20))
        for g in self.goblins:
            g.draw_health_bar()
        for b in self.builders:
            b.draw_health_bar()
        for h in self.helpers:
            h.draw_health_bar()
        for v in self.valkyries:
            v.draw_health_bar()
        for b in getattr(self, "barbarians_spawned", []):
            b.draw_health_bar()

    def draw_range(self):
        color_map = {
            "gunner": (0, 0, 255),
            "sniper": (0, 0, 150),
            "machine_gun": DARK_GREEN,
            "airstrike": ORANGE,
            "heavy_machine_gun": (100, 50, 0),
            "frost_laser": (80, 200, 240),
            "Goblin Hut": DARK_GREEN,
            "builder_hut": (180, 140, 50),
        }
        c = color_map.get(self.type, (0, 0, 255))
        half = tuple(max(0, v // 2) for v in c)
        pygame.draw.circle(screen, half, (self.x, self.y), self.range, 1)


# ── Coin ──────────────────────────────────────────────────────────────────────
class Coin:
    def __init__(self, x, y, value):
        self.x, self.y = x, y
        self.value = value
        self.collected = False
        self.radius = 15

    def draw(self, win):
        pygame.draw.circle(win, YELLOW, (self.x, self.y), self.radius)

    def is_clicked(self, pos):
        mx, my = pos
        return (self.x - mx) ** 2 + (self.y - my) ** 2 <= self.radius**2


# ── InputBox ──────────────────────────────────────────────────────────────────
class InputBox:
    def __init__(self, x, y, w, h, text="", is_password=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.color = (200, 200, 200)
        self.text = text
        self.font = pygame.font.SysFont("verdana", 16)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.is_password = is_password
        self.backspace_held = False
        self.backspace_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Don't deactivate when the user taps the on-screen keyboard panel
            if not keyboard_panel_rect.collidepoint(event.pos):
                self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                self.backspace_held = True
                self.backspace_timer = 18
            elif event.key != pygame.K_RETURN:
                self.text += event.unicode
        elif event.type == pygame.KEYUP and event.key == pygame.K_BACKSPACE:
            self.backspace_held = False
        self.txt_surface = self.font.render("*" * len(self.text) if self.is_password else self.text, True, self.color)

    def update(self):
        if self.active and self.backspace_held and self.text:
            self.backspace_timer -= 1
            if self.backspace_timer <= 0:
                self.text = self.text[:-1]
                self.backspace_timer = 3
                self.txt_surface = self.font.render("*" * len(self.text) if self.is_password else self.text, True, self.color)

    def draw(self, screen):
        pygame.draw.rect(screen, (50, 50, 50), self.rect, border_radius=8)
        pygame.draw.rect(screen, self.color, self.rect, 2, border_radius=8)
        clip_r = pygame.Rect(self.rect.x + 4, self.rect.y + 2, self.rect.w - 8, self.rect.h - 4)
        screen.set_clip(clip_r)
        txt_x = self.rect.x + 5
        if self.txt_surface.get_width() > self.rect.w - 10:
            txt_x = self.rect.right - 5 - self.txt_surface.get_width()
        screen.blit(self.txt_surface, (txt_x, self.rect.y + (self.rect.h - self.txt_surface.get_height()) // 2))
        screen.set_clip(None)


# ── Enemy spawn data ──────────────────────────────────────────────────────────
# (color, type_id, damage, speed, reward_bonus, health_bonus, wave_intro, visible_to, shape, targets_towers)
ENEMY_TYPE_MAP = [
    (RED, "scout", 1, 1.2, 0, -20, 1, "all", "circle", False),
    (BLUE, "soldier", 2, 1.0, 10, 0, 2, "all", "circle", False),
    ((255, 80, 0), "berserker", 3, 2.2, 20, -10, 3, "all", "pentagon", False),
    (DARK_BLUE, "heavy", 3, 0.8, 20, 30, 4, "all", "circle", False),
    (DARK_RED, "ghost", 1, 1.5, 50, 0, 6, "sniper_only", "circle", False),
    (PURPLE, "runner", 2, 1.3, 30, 40, 7, "all", "square", False),
    ((90, 0, 120), "necromancer", 3, 0.8, 80, 200, 8, "all", "pentagon", False),
    (PINK, "dasher", 2, 4.0, 25, -30, 9, "all", "square", False),
    ((80, 120, 0), "tortoise", 4, 0.3, 100, 400, 10, "all", "pentagon", False),
    (CYAN, "tank", 3, 0.7, 40, 60, 12, "all", "square", False),
    ((180, 230, 255), "specter", 2, 1.4, 60, 100, 13, "sniper_only", "pentagon", False),
    (BROWN, "bruiser", 4, 0.4, 60, 80, 14, "all", "square", True),
    (ORANGE, "charger", 2, 1.4, 35, 200, 15, "all", "triangle", False),
    ((200, 255, 50), "lightning_bug", 1, 5.5, 30, -25, 16, "all", "star", False),
    (GRAY, "golem", 3, 1.0, 30, 500, 17, "all", "triangle", False),
    ((160, 160, 160), "gargoyle", 3, 0.6, 90, 300, 19, "all", "star", False),
    (BLACK, "titan", 5, 0.3, 800, 2800, 21, "all", "triangle", True),
    (GREEN, "sprinter", 1, 1.6, 115, 1000, 24, "all", "triangle", False),
    ((100, 180, 50), "plague_rat", 2, 1.8, 50, 250, 22, "all", "star", False),
    ((75, 0, 130), "wizard", 3, 1.0, 45, 800, 19, "all", "diamond", False),
    (GOLD, "paladin", 3, 0.9, 200, 750, 26, "all", "star", False),
    ((80, 0, 80), "phantom", 1, 0.2, 1200, 15000, 24, "sniper_only", "diamond", False),
    ((75, 12, 140), "shade", 4, 1.2, 300, 500, 28, "all", "diamond", False),
    ((30, 30, 120), "shadow_dancer", 4, 1.5, 300, 5000, 32, "all", "hexagon", False),
    ((80, 0, 120), "leviathan", 8, 0.2, 3000, 30000, 40, "all", "hexagon", False),
    # Blood Storm enemies (wave 35+)
    ((150, 0, 80), "vampire", 4, 2.0, 500, 1000, 35, "all", "hexagon", True),
    ((200, 200, 220), "wraith", 2, 2.5, 300, 200, 36, "sniper_only", "hexagon", False),
    ((110, 110, 110), "stone_giant", 6, 0.2, 1500, 10000, 37, "all", "hexagon", False),
    ((255, 120, 30), "fury_beast", 5, 1.5, 800, 2000, 37, "all", "pentagon", False),
    ((10, 0, 30), "void_walker", 4, 2.2, 1000, 3000, 38, "all", "diamond", False),
    ((100, 200, 255), "crystal_drake", 3, 1.0, 1200, 5000, 39, "all", "hexagon", False),
    ((30, 80, 20), "plague_bearer", 3, 0.5, 600, 3000, 38, "all", "pentagon", False),
    ((100, 180, 255), "storm_eagle", 2, 3.5, 700, 500, 40, "all", "triangle", False),
    ((100, 20, 80), "abomination", 5, 0.8, 1800, 8000, 41, "all", "hexagon", False),
    ((220, 210, 190), "bone_lord", 4, 1.2, 900, 3500, 38, "all", "pentagon", False),
    ((180, 0, 20), "blood_bat", 3, 3.0, 600, 800, 36, "all", "triangle", False),
    ((200, 180, 100), "sand_wraith", 2, 1.8, 500, 1200, 39, "sniper_only", "diamond", False),
    ((60, 60, 70), "iron_golem", 6, 0.15, 2000, 20000, 42, "all", "hexagon", False),
    ((255, 50, 255), "chaos_sprite", 3, 2.0, 400, 1000, 37, "all", "star", False),
    ((10, 10, 20), "night_terror", 5, 2.8, 900, 2000, 40, "all", "diamond", False),
    ((150, 120, 0), "elder_dragon", 8, 0.5, 5000, 50000, 44, "all", "hexagon", False),
    ((200, 200, 150), "lich", 4, 1.0, 2000, 5000, 42, "all", "pentagon", False),
    ((120, 0, 20), "doom_bringer", 6, 1.2, 2000, 6000, 43, "all", "hexagon", False),
    ((20, 20, 100), "shadow_fiend", 4, 2.0, 1500, 4000, 41, "all", "diamond", False),
    ((200, 80, 0), "molten_titan", 8, 0.3, 8000, 100000, 46, "all", "hexagon", False),
    ((80, 80, 90), "doom_knight", 3, 0.7, 60, 150, 5, "all", "square", False),
    ((180, 220, 255), "spectral_wolf", 2, 2.8, 70, -10, 11, "sniper_only", "diamond", False),
    ((50, 180, 30), "venom_crawler", 3, 0.5, 100, 500, 16, "all", "pentagon", False),
    ((200, 100, 255), "phase_shifter", 3, 1.8, 120, 200, 18, "sniper_only", "diamond", False),
    ((120, 70, 30), "war_mammoth", 5, 0.2, 300, 1500, 23, "all", "hexagon", False),
    ((20, 0, 40), "null_specter", 2, 2.5, 150, 300, 25, "sniper_only", "star", False),
    ((255, 80, 30), "flame_imp", 2, 4.5, 80, -20, 27, "all", "triangle", False),
    ((60, 160, 255), "storm_rider", 2, 3.2, 200, 500, 29, "all", "triangle", False),
    ((100, 200, 240), "frost_giant", 5, 0.1, 400, 8000, 31, "all", "hexagon", False),
    ((180, 0, 30), "blood_spawn", 3, 1.5, 200, 600, 33, "all", "circle", False),
    ((90, 0, 120), "shadow_hound", 3, 3.0, 400, 1000, 36, "sniper_only", "pentagon", False),
    ((80, 160, 30), "plague_moth", 2, 1.6, 300, 800, 38, "all", "star", False),
    ((210, 200, 180), "crypt_walker", 4, 0.8, 600, 2500, 43, "all", "pentagon", False),
    ((60, 70, 80), "dreadnought", 6, 0.25, 1000, 12000, 45, "all", "hexagon", True),
    ((15, 0, 35), "void_shade", 3, 2.5, 2000, 8000, 48, "sniper_only", "diamond", False),
    ((35, 35, 45), "obsidian_guardian", 6, 0.35, 2500, 18000, 49, "all", "hexagon", False),
    ((190, 230, 255), "mirror_wisp", 3, 2.4, 1200, 2500, 50, "all", "diamond", False),
    ((230, 70, 15), "ember_colossus", 7, 0.45, 3000, 22000, 51, "all", "hexagon", False),
    ((120, 220, 255), "frost_weaver", 4, 1.0, 1800, 7000, 52, "all", "star", False),
    ((80, 220, 150), "shield_mender", 3, 0.9, 1800, 6000, 53, "all", "pentagon", False),
    ((160, 70, 255), "blink_stalker", 4, 2.7, 2200, 5000, 54, "all", "diamond", False),
    ((60, 130, 55), "thornback_beast", 5, 0.75, 2400, 13000, 55, "all", "pentagon", False),
    ((130, 70, 170), "swarm_queen", 4, 0.7, 2600, 12000, 56, "all", "hexagon", False),
    ((230, 90, 255), "arcane_orb", 4, 1.8, 2500, 8000, 57, "all", "circle", False),
    ((120, 255, 40), "acid_spitter", 5, 1.1, 2600, 9000, 58, "all", "triangle", False),
    ((210, 210, 255), "siren_banshee", 3, 2.0, 2800, 6500, 59, "all", "star", False),
    ((70, 50, 110), "gravity_slug", 6, 0.25, 3200, 30000, 60, "all", "circle", False),
    ((50, 120, 200), "rune_giant", 7, 0.4, 3600, 28000, 61, "all", "hexagon", False),
    ((5, 5, 45), "void_reaper", 6, 2.2, 4000, 14000, 62, "sniper_only", "diamond", False),
    ((255, 230, 120), "celestial_drake", 8, 1.4, 5000, 36000, 63, "all", "hexagon", False),
    ((40, 0, 80), "shadow_priest", 4, 0.9, 4200, 10000, 64, "all", "pentagon", False),
    ((180, 60, 10), "lava_lurker", 7, 0.4, 4500, 25000, 65, "all", "hexagon", False),
    ((200, 50, 200), "psy_fiend", 5, 1.6, 4800, 12000, 66, "all", "diamond", False),
    ((80, 200, 240), "glacial_creep", 5, 0.2, 5000, 40000, 67, "all", "circle", False),
    ((200, 180, 120), "dust_devil", 4, 2.8, 5200, 8000, 68, "all", "star", False),
    ((200, 0, 40), "crimson_stalker", 5, 1.5, 5500, 15000, 69, "sniper_only", "diamond", False),
    ((150, 150, 255), "mimic", 4, 1.8, 5800, 11000, 70, "all", "star", False),
    ((50, 80, 200), "thunder_ram", 8, 1.1, 6000, 20000, 71, "all", "pentagon", False),
    ((60, 120, 30), "plague_crawler", 5, 0.6, 6500, 35000, 72, "all", "hexagon", False),
    ((20, 0, 50), "void_colossus", 6, 0.3, 8000, 80000, 73, "sniper_only", "hexagon", False),
    # ── Shadow Storm enemies (waves 75–80) ────────────────────────────────────
    ((90, 0, 140), "shadow_wraith", 7, 2.4, 9000, 18000, 75, "sniper_only", "diamond", False),
    ((30, 0, 60), "void_harbinger", 8, 1.8, 12000, 32000, 76, "all", "star", False),
    ((140, 60, 200), "umbral_stalker", 6, 2.0, 15000, 22000, 77, "sniper_only", "triangle", False),
    ((60, 20, 120), "abyssal_juggernaut", 12, 0.6, 20000, 90000, 78, "all", "hexagon", False),
    ((180, 100, 230), "phantom_warlord", 10, 1.5, 25000, 60000, 79, "all", "pentagon", False),
    ((20, 0, 30), "void_emperor", 15, 0.9, 40000, 150000, 80, "all", "circle", False),
    # ── New enemies ───────────────────────────────────────────────────────────
    ((220, 100, 60), "spike_hopper", 3, 3.5, 1500, 4000, 30, "all", "triangle", False),
    ((240, 90, 40), "ember_wolf", 4, 2.6, 2200, 8000, 45, "all", "diamond", False),
    ((160, 230, 255), "crystal_shard", 5, 1.4, 3000, 10000, 50, "all", "star", False),
    ((90, 140, 50), "blight_walker", 6, 0.4, 4000, 18000, 55, "all", "pentagon", False),
    ((100, 130, 255), "stormcaller", 4, 1.2, 3500, 12000, 60, "all", "star", False),
    ((40, 0, 70), "void_serpent", 5, 1.5, 5000, 16000, 65, "sniper_only", "diamond", False),
    ((80, 90, 110), "iron_sentinel", 8, 0.35, 6000, 30000, 50, "all", "hexagon", True),
    ((220, 60, 200), "cursed_jester", 3, 1.8, 1800, 6000, 35, "all", "square", True),
    ((140, 200, 90), "fungal_horror", 4, 0.9, 2500, 9000, 40, "all", "pentagon", False),
    ((210, 230, 255), "blade_dancer", 5, 3.0, 2800, 10000, 55, "all", "diamond", False),
    ((90, 0, 130), "nether_imp", 2, 2.4, 800, 1500, 28, "all", "triangle", False),
    ((25, 25, 35), "obsidian_titan", 12, 0.18, 10000, 70000, 70, "all", "hexagon", True),
    ((180, 40, 80), "blood_moth", 2, 4.0, 1200, 2000, 38, "all", "star", False),
    ((160, 150, 140), "ash_revenant", 5, 0.9, 3500, 13000, 60, "all", "pentagon", False),
    ((10, 0, 40), "omen_specter", 6, 1.0, 7000, 24000, 70, "sniper_only", "circle", False),
]

BOSS_TYPE_MAP = [
    ((0, 0, 0), "boss_1", 10, 0.30, 1000, 5000, BOSS_RADIUS, "circle"),
    ((50, 0, 50), "boss_2", 15, 0.25, 5000, 10000, BOSS_RADIUS, "triangle"),
    ((100, 0, 0), "boss_3", 20, 0.20, 10000, 20000, BOSS_RADIUS, "diamond"),
    ((0, 0, 100), "boss_4", 25, 0.15, 30000, 50000, BOSS_RADIUS, "square"),
    ((4, 0, 20), "boss_5", 30, 0.13, 50000, 100000, BOSS_RADIUS, "pentagon"),
    ((0, 30, 80), "boss_6", 35, 0.15, 250000, 500000, BOSS_RADIUS, "hexagon"),
    ((80, 50, 0), "boss_7", 40, 0.22, 100000, 120000, BOSS_RADIUS, "star"),
    ((0, 80, 20), "boss_8", 28, 0.18, 150000, 200000, BOSS_RADIUS, "pentagon"),
    ((100, 150, 255), "boss_9", 22, 0.55, 80000, 80000, BOSS_RADIUS, "triangle"),
    ((60, 60, 60), "boss_10", 55, 0.07, 600000, 700000, BOSS_RADIUS, "hexagon"),
    ((150, 0, 0), "boss_11", 70, 0.20, 1000000, 2500000, BOSS_RADIUS, "star"),
    ((5, 0, 30), "boss_12", 90, 0.12, 2000000, 5000000, BOSS_RADIUS, "hexagon"),
    # ── Shadow Storm bosses (cycle in past wave 75) ───────────────────────────
    ((50, 0, 100), "boss_shadow_lord", 120, 0.18, 4000000, 12000000, BOSS_RADIUS + 4, "diamond"),
    ((100, 0, 200), "boss_void_titan", 150, 0.10, 8000000, 25000000, BOSS_RADIUS + 8, "hexagon"),
    ((30, 0, 60), "boss_abyss_king", 200, 0.15, 15000000, 50000000, BOSS_RADIUS + 6, "star"),
    # ── New bosses (cycle via modulo) ─────────────────────────────────────────
    ((160, 20, 200), "boss_chaos_emperor", 240, 0.18, 30000000, 100000000, BOSS_RADIUS + 8, "star"),
    ((255, 230, 80), "boss_eternal_god", 300, 0.12, 75000000, 250000000, BOSS_RADIUS + 10, "circle"),
]

wave_spawn_sequence = sorted(set(e[6] for e in ENEMY_TYPE_MAP))


def get_bestiary_stats(type_id):
    for color, tid, dmg, spd, reward_bonus, health_bonus, intro, vis, shape, targets_towers in ENEMY_TYPE_MAP:
        if tid == type_id:
            health = max(10, 30 + intro * 5 + health_bonus)
            return health, dmg, spd, enemy_ability_text(type_id)
    for color, tid, dmg, spd, reward, health, size, shape in BOSS_TYPE_MAP:
        if tid == type_id:
            return health, dmg, spd, enemy_ability_text(type_id)
    return None, None, None, enemy_ability_text(type_id)


def enemy_ability_text(type_id):
    abilities = {
        "ghost": "Sniper-only",
        "spectral_wolf": "Sniper-only; pack howl on death",
        "specter": "Sniper-only",
        "phantom": "Sniper-only",
        "tower_raider": "Hunts towers directly",
        "titan": "Hunts and smashes towers",
        "plague_rat": "Splits into 3 rats",
        "paladin": "Regenerates health",
        "vampire": "Dashes to towers and drains HP",
        "fury_beast": "Speeds up as health drops",
        "plague_moth": "Heals enemies and releases rats",
        "phase_shifter": "Cycles invulnerability",
        "war_mammoth": "Damages nearby towers",
        "storm_rider": "Zaps nearby towers",
        "shadow_hound": "Pounces at towers",
        "crypt_walker": "Revives once",
        "dreadnought": "Hunts towers; heavy armour",
        "void_shade": "Teleports forward; sniper-only",
        "obsidian_guardian": "Heavy damage reduction",
        "mirror_wisp": "Splits into mirror fragments",
        "ember_colossus": "Burns nearby towers",
        "frost_weaver": "Slows nearby towers",
        "shield_mender": "Heals nearby enemies",
        "blink_stalker": "Blinks forward",
        "thornback_beast": "Damage reduction",
        "swarm_queen": "Summons minions",
        "arcane_orb": "Cycles invulnerability",
        "acid_spitter": "Damages towers and walls nearby",
        "siren_banshee": "Speeds nearby enemies",
        "gravity_slug": "Heavily slows nearby towers",
        "rune_giant": "Regenerates health",
        "void_reaper": "Phases; sniper-only",
        "celestial_drake": "Regenerates and zaps towers",
        "shadow_priest": "Heals nearby enemies; slows tower fire rate",
        "lava_lurker": "Burns nearby towers with lava surges",
        "psy_fiend": "Periodically reverses along path to evade fire",
        "glacial_creep": "Massively slows all nearby towers",
        "dust_devil": "Warps forward when below 40% health",
        "crimson_stalker": "Sniper-only; splits into three on death",
        "mimic": "Cycles through invulnerable shape-shift phases",
        "thunder_ram": "Charges and slams towers for heavy damage",
        "plague_crawler": "Regenerates; corrodes nearby towers with plague",
        "void_colossus": "Sniper-only; enormous health; regenerates; phases",
        "boss_12": "Revives once at 50% HP; spawns void fragments on death",
    }
    return abilities.get(type_id, "None")


def spawn_enemy(wave):
    global enemies
    # Player-created custom enemies — spawn at their designated wave (priority chance)
    _matched_custom = [d for d in custom_enemies if d.get("wave", 1) == wave and not d.get("is_boss", False)]
    if _matched_custom and random.random() < 0.35:
        _defn = random.choice(_matched_custom)
        _ce = spawn_custom_enemy_from_def(_defn)
        enemies.append(_ce)
        record_enemy_kill(_ce.type_id)
        return
    base_health = 30 + wave * 5
    base_reward = 20 + wave * 2

    # Boss (every 5 waves from wave 10) — checked FIRST so boss always spawns
    if wave >= 10 and wave % 5 == 0 and enemies_spawned == 0:
        idx = ((wave // 5) - 2) % len(BOSS_TYPE_MAP)
        color, tid, dmg, spd, reward, health, size, shape = BOSS_TYPE_MAP[idx]
        if nightmare_mode:
            health = int(health * 2)
        e = Enemy(color, dmg, spd, reward, health, radius=size, type_id=tid, shape=shape)
        e.is_boss = True
        enemies.append(e)
        record_enemy_kill(tid)
        return

    # Tower Raider (wave 30+, non-boss spawns only)
    if wave >= 30 and random.random() < 0.25:
        r_health = base_health * 2 + 500
        if nightmare_mode:
            r_health = int(r_health * 2)
        r = TowerRaider(health=r_health, reward=base_reward + 500)
        enemies.append(r)
        record_enemy_kill("tower_raider")
        return

    # Pick eligible regular enemies
    eligible = [e for e in ENEMY_TYPE_MAP if wave >= e[6]]
    if not eligible:
        eligible = [ENEMY_TYPE_MAP[0]]
    chosen = random.choice(eligible)
    color, tid, dmg, spd, r_bonus, h_bonus, _, vis, shape, tgt_towers = chosen
    health = max(10, base_health + h_bonus)
    reward = base_reward + r_bonus
    # Tower-attackers get slightly less health
    if tgt_towers:
        health = int(health * 0.75)
    # Blood Storm: all enemies are 2x health, 5x reward
    if blood_storm_active:
        health = int(health * 2)
        reward = int(reward * 5)
    # Shadow Storm (wave 75+): old enemies become brutal — 10x HP, 10x dmg,
    # +2% HP per wave past 75, 3x coin drop (stacks with blood storm 5x).
    if shadow_storm_active:
        wave_scale = 1.0 + 0.02 * max(0, wave_number - 75)
        health = int(health * 10 * wave_scale)
        dmg = int(dmg * 10)
        reward = int(reward * 3)
    if nightmare_mode:
        health = int(health * 2)
    e = Enemy(color, dmg, spd, reward, health, vis, type_id=tid, shape=shape)
    e.targets_towers = tgt_towers
    e.is_summoner = tid in ("necromancer", "swarm_queen")
    e.plague_rat = tid == "plague_rat"
    e.is_vampire = tid == "vampire"
    e.abomination = tid == "abomination"
    e.fury_beast = tid == "fury_beast"
    e.blood_spawn = tid == "blood_spawn"
    e.plague_moth = tid == "plague_moth"
    e.dreadnought = tid == "dreadnought"
    e.regen_rate = 12 if tid == "rune_giant" else (6 if tid == "celestial_drake" else (2 if tid == "paladin" else 0))
    e.zigzag = tid == "shadow_dancer"
    if e.is_vampire:
        e.vampire_timer = 0
        e.vampire_phase = 0
        e.vampire_target = None
        e.vampire_saved_x = e.x
        e.vampire_saved_y = e.y
        e.vampire_saved_idx = 0
        e.vampire_hit_timer = 0
    # ── New-enemy ability fields ───────────────────────────────────────────────
    e.damage_reduction = 0.6 if tid == "obsidian_guardian" else 0.45 if tid == "thornback_beast" else 0.5 if tid == "doom_knight" else 0.75 if tid == "dreadnought" else 0.0
    e.phase_timer = 0
    e.phase_immune = False
    e.war_tremor_timer = 0
    e.storm_timer = 0
    e.pounce_phase = 0
    e.pounce_timer = 0
    e.pounce_target = None
    e.pounce_save_x = e.x
    e.pounce_save_y = e.y
    e.pounce_save_idx = 0
    e.plague_dust_timer = 0
    e.revived = False  # crypt_walker / boss_12 one-time revival
    e.void_step_timer = 0
    e.plague_crawl_timer = 0
    e.psy_timer = 0
    e.psy_reverse = False
    e.dust_blinked = False
    if tid == "venom_crawler":
        e.regen_rate = 8
    if tid == "void_colossus":
        e.regen_rate = 10
    if tid == "plague_crawler":
        e.regen_rate = 6
    enemies.append(e)
    record_enemy_kill(tid)


# ── Draw helpers ──────────────────────────────────────────────────────────────
def draw_achievements():
    now = time.time()
    y = 10
    for msg, expire in achievement_queue:
        rem = expire - now
        if rem <= 0:
            continue
        alpha = min(255, int(rem * 100))
        w = max(420, font_lg.size(msg)[0] + 20)
        surf = pygame.Surface((w, 36), pygame.SRCALPHA)
        surf.fill((20, 20, 20, min(200, alpha)))
        pygame.draw.rect(surf, (255, 220, 0), (0, 0, w, 36), 2)
        screen.blit(font_lg.render(msg, True, (255, 220, 0)), (WIDTH // 2 - w // 2 + 8, y + 5))
        screen.blit(surf, (WIDTH // 2 - w // 2, y))
        y += 42
    achievement_queue[:] = [(m, e) for m, e in achievement_queue if e > now]


def draw_bestiary(in_arena=False):
    global bestiary_scroll
    if in_arena:
        PW, PH = min(520, WIDTH - SHOP_W - 20), HEIGHT - 90
        px = SHOP_W + 10
        py = 75
    else:
        PW, PH = 580, 520
        px = WIDTH // 2 - PW // 2
        py = HEIGHT // 2 - PH // 2

    bg = pygame.Surface((PW, PH), pygame.SRCALPHA)
    bg.fill((10, 10, 30, 245))
    screen.blit(bg, (px, py))
    pygame.draw.rect(screen, (100, 100, 200), (px, py, PW, PH), 2)

    # Title
    screen.blit(font_lg.render("BESTIARY", True, (200, 200, 255)), (px + 16, py + 10))

    # Tabs
    tab_rects = {}
    for i, (tid, tlabel) in enumerate([("enemies", "Enemies"), ("bosses", "Bosses")]):
        tr = pygame.Rect(px + 16 + i * 110, py + 38, 100, 26)
        col = (60, 60, 180) if bestiary_tab == tid else (40, 40, 80)
        pygame.draw.rect(screen, col, tr)
        pygame.draw.rect(screen, (100, 100, 200), tr, 1)
        screen.blit(font_shop_sm.render(tlabel, True, WHITE), (tr.x + 12, tr.y + 4))
        tab_rects[tid] = tr

    # Close
    close_r = pygame.Rect(px + PW - 82, py + 8, 72, 28)
    pygame.draw.rect(screen, (180, 30, 30), close_r, border_radius=6)
    screen.blit(font_shop_sm.render("Close", True, WHITE), (close_r.x + 10, close_r.y + 5))

    # List — include player-created custom enemies/bosses with their wave info
    if bestiary_tab == "enemies":
        entries = list(BESTIARY_ENEMIES)
        for ce in custom_enemies:
            entries.append({
                "id": "custom_" + ce["name"].lower().replace(" ", "_"),
                "name": f"{ce['name']}  (Wave {ce.get('wave', '?')})",
                "color": ce["color"],
                "shape": ce.get("shape", "circle"),
                "desc": (ce.get("desc") or "Custom enemy") + f"  — appears wave {ce.get('wave', '?')}",
            })
    else:
        entries = list(BESTIARY_BOSSES)
        for cb in custom_bosses:
            entries.append({
                "id": "custom_" + cb["name"].lower().replace(" ", "_"),
                "name": f"{cb['name']}  (Wave {cb.get('wave', '?')})",
                "color": cb["color"],
                "shape": cb.get("shape", "circle"),
                "desc": (cb.get("desc") or "Custom boss") + f"  — appears wave {cb.get('wave', '?')}",
            })
    # Custom entries become discoverable once the player has reached their wave
    _cur_wave = arena_wave if state == "ARENA" else wave_number
    for ce in (custom_enemies + custom_bosses):
        if _cur_wave >= ce.get("wave", 1):
            discovered_enemies.add("custom_" + ce["name"].lower().replace(" ", "_"))
    row_y = py + 72 - bestiary_scroll
    clip = pygame.Rect(px, py + 68, PW, PH - 72)
    mx, my = pygame.mouse.get_pos()
    hover_entry = None
    hover_rect = None
    screen.set_clip(clip)

    for entry in entries:
        if row_y > py + PH:
            break
        if row_y + 40 < py + 68:
            row_y += 52
            continue
        disc = entry["id"] in discovered_enemies
        sc = entry["color"] if disc else (60, 60, 60)
        draw_shape(screen, sc, px + 24, row_y + 12, 10, entry["shape"])
        if not disc:
            pygame.draw.circle(screen, GRAY, (px + 24, int(row_y + 12)), 10, 2)
        nc = WHITE if disc else DARKGRAY
        pref = "" if disc else "[?] "
        screen.blit(font_shop.render(pref + entry["name"], True, nc), (px + 42, row_y))
        if disc:
            screen.blit(font_shop_sm.render(entry["desc"], True, (180, 180, 180)), (px + 42, row_y + 22))
            info_r = pygame.Rect(px + PW - 54, row_y - 1, 22, 22)
            hov = info_r.collidepoint(mx, my)
            pygame.draw.circle(screen, (170, 190, 255) if hov else (80, 100, 190), info_r.center, 10)
            screen.blit(font_shop_sm.render("i", True, WHITE), (info_r.x + 8, info_r.y + 3))
            if hov:
                hover_entry = entry
                hover_rect = info_r
            row_y += 52
        else:
            row_y += 32

    screen.set_clip(None)
    if hover_entry and hover_rect:
        h, dmg, spd, ability = get_bestiary_stats(hover_entry["id"])
        lines = [hover_entry["name"], f"Health: {h if h is not None else '?'}", f"End damage: {dmg if dmg is not None else '?'}", f"Speed: {spd if spd is not None else '?'}", f"Ability: {ability}"]
        tw = max(font_shop_sm.size(line)[0] for line in lines) + 20
        th = 22 + len(lines) * 20
        tx = min(WIDTH - tw - 8, hover_rect.right + 10)
        ty = min(HEIGHT - th - 8, hover_rect.top)
        tip = pygame.Surface((tw, th), pygame.SRCALPHA)
        tip.fill((8, 8, 28, 245))
        screen.blit(tip, (tx, ty))
        pygame.draw.rect(screen, (150, 170, 255), (tx, ty, tw, th), 2)
        screen.blit(font_shop.render(lines[0], True, (210, 220, 255)), (tx + 10, ty + 6))
        for i, line in enumerate(lines[1:]):
            screen.blit(font_shop_sm.render(line, True, WHITE), (tx + 10, ty + 32 + i * 20))

    # Scroll arrows
    up_r = pygame.Rect(px + PW - 30, py + 68, 24, 24)
    down_r = pygame.Rect(px + PW - 30, py + PH - 34, 24, 24)
    pygame.draw.rect(screen, (60, 60, 120), up_r)
    pygame.draw.rect(screen, (60, 60, 120), down_r)
    screen.blit(font.render("▲", True, WHITE), (up_r.x + 3, up_r.y + 3))
    screen.blit(font.render("▼", True, WHITE), (down_r.x + 3, down_r.y + 3))

    return close_r, tab_rects, up_r, down_r


def draw_ui():
    """Top-bar HUD per twrdf.png — all buttons in one horizontal row."""
    global shop_button_rect, info_button_rect, nightmare_button_rect
    global start_wave_rect, twox_button_rect, blood_storm_info_rect
    # Top-bar background (dark green strip)
    pygame.draw.rect(screen, (24, 84, 36), (0, 0, WIDTH, 56))
    pygame.draw.rect(screen, (10, 50, 18), (0, 54, WIDTH, 2))

    def styled_btn(rect, fill, edge, label, lbl_col, lfont):
        pygame.draw.rect(screen, fill, rect, border_radius=8)
        pygame.draw.rect(screen, edge, rect, 2, border_radius=8)
        ls = lfont.render(label, True, lbl_col)
        screen.blit(ls, ls.get_rect(center=rect.center))

    # SHOP
    shop_button_rect = pygame.Rect(10, 8, 70, 40)
    styled_btn(shop_button_rect, (190, 190, 195), (40, 40, 45), "SHOP", BLACK, font_sm)

    # BESTIARY
    info_button_rect = pygame.Rect(88, 8, 100, 40)
    styled_btn(info_button_rect, (60, 130, 200), (20, 60, 130), "BESTIARY", WHITE, font_sm)

    # NIGHTMARE
    nightmare_button_rect = pygame.Rect(196, 8, 110, 40)
    nm_can = (not wave_active) and (not enemies) and (wave_number == 1) and (not nightmare_locked)
    if nightmare_mode:
        # Pulsing glow when ON
        _nm_pulse = int(40 + 40 * abs(math.sin(time.time() * 4)))
        nm_fill = (220 + min(35, _nm_pulse - 40), 20, 20)
        nm_edge = (255, 220, 0)
        nm_label = "NIGHTMARE ON"
        nm_lbl_font = font_tiny
    elif nm_can:
        nm_fill = (190, 30, 30)
        nm_edge = (90, 10, 10)
        nm_label = "NIGHTMARE"
        nm_lbl_font = font_sm
    else:
        nm_fill = (110, 50, 50)
        nm_edge = (90, 10, 10)
        nm_label = "NIGHTMARE"
        nm_lbl_font = font_sm
    pygame.draw.rect(screen, nm_fill, nightmare_button_rect, border_radius=8)
    pygame.draw.rect(screen, nm_edge, nightmare_button_rect, 2, border_radius=8)
    nm_lbl_font.set_bold(True)
    _nm_surf = nm_lbl_font.render(nm_label, True, BLACK)
    nm_lbl_font.set_bold(False)
    screen.blit(_nm_surf, _nm_surf.get_rect(center=nightmare_button_rect.center))
    if nightmare_mode and nm_can:
        # Outer ring glow
        pygame.draw.rect(screen, (255, 220, 0), nightmare_button_rect.inflate(6, 6), 2, border_radius=10)

    # STORM INFO  (Shadow Storm replaces Blood Storm button when active)
    global shadow_storm_info_rect
    if shadow_storm_active:
        shadow_storm_info_rect = pygame.Rect(316, 8, 70, 40)
        blood_storm_info_rect = pygame.Rect(0, 0, 0, 0)
        pygame.draw.rect(screen, (90, 30, 160), shadow_storm_info_rect, border_radius=8)
        pygame.draw.rect(screen, (40, 10, 80), shadow_storm_info_rect, 2, border_radius=8)
        l1 = font_tiny.render("SHADOW", True, WHITE)
        l2 = font_tiny.render("STORM", True, WHITE)
        l3 = font_tiny.render("INFO", True, WHITE)
        screen.blit(l1, (shadow_storm_info_rect.centerx - l1.get_width() // 2, shadow_storm_info_rect.y + 3))
        screen.blit(l2, (shadow_storm_info_rect.centerx - l2.get_width() // 2, shadow_storm_info_rect.y + 15))
        screen.blit(l3, (shadow_storm_info_rect.centerx - l3.get_width() // 2, shadow_storm_info_rect.y + 27))
    elif blood_storm_active:
        blood_storm_info_rect = pygame.Rect(316, 8, 70, 40)
        shadow_storm_info_rect = pygame.Rect(0, 0, 0, 0)
        # Two stacked tiny lines: "BLOOD" / "STORM INFO"
        pygame.draw.rect(screen, (180, 30, 30), blood_storm_info_rect, border_radius=8)
        pygame.draw.rect(screen, (90, 10, 10), blood_storm_info_rect, 2, border_radius=8)
        l1 = font_tiny.render("BLOOD", True, WHITE)
        l2 = font_tiny.render("STORM", True, WHITE)
        l3 = font_tiny.render("INFO", True, WHITE)
        screen.blit(l1, (blood_storm_info_rect.centerx - l1.get_width() // 2, blood_storm_info_rect.y + 3))
        screen.blit(l2, (blood_storm_info_rect.centerx - l2.get_width() // 2, blood_storm_info_rect.y + 15))
        screen.blit(l3, (blood_storm_info_rect.centerx - l3.get_width() // 2, blood_storm_info_rect.y + 27))
    else:
        blood_storm_info_rect = pygame.Rect(0, 0, 0, 0)
        shadow_storm_info_rect = pygame.Rect(0, 0, 0, 0)

    # START WAVE — centered horizontally in the top bar (rectangular with rounded corners)
    sw_w, sw_h = 120, 44
    sw_x = (WIDTH - sw_w) // 2
    start_wave_rect = pygame.Rect(sw_x, 6, sw_w, sw_h)
    sw_fill = (70, 70, 70) if wave_active else (40, 190, 80)
    sw_edge = (120, 120, 120) if wave_active else (20, 120, 50)
    pygame.draw.rect(screen, sw_fill, start_wave_rect, border_radius=8)
    pygame.draw.rect(screen, sw_edge, start_wave_rect, 2, border_radius=8)
    sw_lbl1 = font_sm.render("Start", True, BLACK if not wave_active else WHITE)
    sw_lbl2 = font_sm.render("Wave", True, BLACK if not wave_active else WHITE)
    screen.blit(sw_lbl1, (start_wave_rect.centerx - sw_lbl1.get_width() // 2, start_wave_rect.y + 6))
    screen.blit(sw_lbl2, (start_wave_rect.centerx - sw_lbl2.get_width() // 2, start_wave_rect.y + 24))

    # 2X — to the right of START WAVE
    twox_x = start_wave_rect.right + 8
    twox_button_rect = pygame.Rect(twox_x, 8, 56, 40)
    sc = (255, 200, 50) if speed_2x else (180, 150, 50)
    styled_btn(twox_button_rect, sc, (120, 90, 10), "2X", BLACK, font_btn)

    # Stats box: HP / Wave / Coins — to the right of the 2X button
    stats_box = pygame.Rect(twox_button_rect.right + 8, 8, 170, 40)
    pygame.draw.rect(screen, (40, 110, 50), stats_box, border_radius=6)
    pygame.draw.rect(screen, (10, 60, 20), stats_box, 2, border_radius=6)
    stats_lines = [
        f"HP: {hp}",
        f"Wave: {wave_number}",
        f"COINS: {coins:,}",
    ]
    # Clip text to stay inside the stats box
    prev_clip = screen.get_clip()
    screen.set_clip(stats_box)
    for i, txt in enumerate(stats_lines):
        srf = font_tiny.render(txt, True, WHITE)
        screen.blit(srf, (stats_box.x + 6, stats_box.y + 2 + i * 12))
    screen.set_clip(prev_clip)


SHOP_W = 170


def draw_shop():
    global _pending_shop_tooltip
    _pending_shop_tooltip = None
    # Dark gray panel background
    pygame.draw.rect(screen, (52, 52, 56), (shop_x, 0, SHOP_W, HEIGHT))
    pygame.draw.rect(screen, (28, 28, 30), (shop_x + SHOP_W - 2, 0, 2, HEIGHT))

    # Tabs (rounded-bottom look)
    tab_w = SHOP_W // 2
    for i, (tid, tlabel) in enumerate([("towers", "Towers"), ("builder", "Builder")]):
        tr = pygame.Rect(shop_x + i * tab_w, 0, tab_w, 28)
        active = shop_tab == tid
        col = (210, 210, 215) if active else (74, 74, 80)
        pygame.draw.rect(screen, col, tr)
        pygame.draw.rect(screen, (30, 30, 32), tr, 1)
        tl_col = BLACK if active else (220, 220, 220)
        screen.blit(font_shop_sm.render(tlabel, True, tl_col), (tr.x + 8, tr.y + 6))

    mx, my = pygame.mouse.get_pos()

    BTN_H = 34
    if shop_tab == "towers":
        buttons = [
            ("Gunner", "gunner", 34, "Basic tower."),
            ("Sniper", "sniper", 74, "High damage, long range."),
            ("MG", "machine_gun", 114, "Fast fire, short range."),
            ("Airstrike", "airstrike", 154, "AoE damage, slow reload."),
            ("Goblin Hut", "Goblin Hut", 194, "Spawns goblins."),
            ("Heavy MG", "heavy_machine_gun", 234, "Massive damage."),
            ("Close", "close", 274, ""),
        ]
    else:
        buttons = [
            ("Frost Laser", "frost_laser", 34, "Slows enemies in range. Blood: zap chain."),
            ("Builder Hut", "builder_hut", 74, "Repairs towers (35,000)."),
            ("Valkyrie Hut", "Valkyrie Hut", 114, "Spawns valkyries (100,000). Requires Builder Hut."),
            (f"Wall ({get_wall_cost()})", "wall", 154, "Durable barrier (500HP)."),
            (f"Bomb ({get_bomb_cost()})", "bomb", 194, "Instant kill on contact."),
            ("Close", "close", 234, ""),
        ]

    for label, tag, y, tooltip in buttons:
        rect = pygame.Rect(shop_x + 8, y + 28, SHOP_W - 16, BTN_H)
        hov = rect.collidepoint(mx, my)
        # Determine cost / affordability
        cost = 0
        if tag == "close":
            card_col = (170, 70, 70)
            edge_col = (220, 110, 110)
            text_col = WHITE
        else:
            if tag == "wall":
                cost = get_wall_cost()
            elif tag == "bomb":
                cost = get_bomb_cost()
            else:
                cost = get_tower_price(tag)
            can = coins >= cost
            card_col = (215, 215, 220) if can else (110, 110, 115)
            edge_col = (90, 90, 100)
            text_col = BLACK if can else (60, 60, 60)
        if hov:
            card_col = tuple(min(255, c + 18) for c in card_col)
        # Rounded card
        pygame.draw.rect(screen, card_col, rect, border_radius=8)
        pygame.draw.rect(screen, edge_col, rect, 1, border_radius=8)
        # Item name (left aligned)
        name_surf = font_shop_sm.render(label, True, text_col)
        screen.blit(name_surf, (rect.x + 8, rect.y + 4))
        # Cost (smaller, below name)
        if tag != "close":
            cost_surf = font_tiny.render(f"COST: {cost}", True, (60, 90, 60) if coins >= cost else (180, 60, 60))
            screen.blit(cost_surf, (rect.x + 8, rect.y + 19))
        if hov and tooltip:
            ts = font_shop_sm.render(tooltip, True, BLACK)
            tb = pygame.Surface((ts.get_width() + 10, ts.get_height() + 6))
            tb.fill((255, 255, 210))
            tb.set_alpha(230)
            _pending_shop_tooltip = (tb, ts, mx + 15, my + 15)


def draw_upgrade_menu(tower):
    global upgrade_menu_upgrade_rect, upgrade_menu_close_rect, upgrade_menu_sell_rect
    global upgrade_menu_move_rect, upgrade_menu_revive_rect
    lvl_index = tower.level - 1
    table = UPGRADE_TABLE.get(tower.type, [])
    at_max = tower.level >= tower.max_level
    info = table[lvl_index] if lvl_index < len(table) else None
    is_blood = bool(info and info.get("blood"))
    pristine_tier = info.get("pristine") if info else None
    is_pristine = bool(pristine_tier)

    mw, mh = 260, 240
    left_bound = (SHOP_W + 4) if (shop_x > -SHOP_W) else 4
    # Horizontal: right of tower, clamped to screen
    ox = min(max(tower.x + 20, left_bound), WIDTH - mw - 4)
    # Vertical: below tower when near top, above when near bottom, always on-screen
    TOP_MARGIN = 62  # clear the HUD bar
    BOT_MARGIN = 4
    if tower.y < HEIGHT // 2:
        oy_raw = tower.y + 20  # prefer below the tower
    else:
        oy_raw = tower.y - mh - 20  # prefer above the tower
    oy = max(TOP_MARGIN, min(oy_raw, HEIGHT - mh - BOT_MARGIN))

    # Background: tier-themed
    PRISTINE_BG = {"bronze": ((60, 35, 10, 230), (200, 130, 40)),
                   "silver": ((45, 45, 55, 230), (210, 210, 220)),
                   "gold":   ((70, 55, 5, 230), (255, 200, 60))}
    if is_pristine:
        fill_col, edge_col = PRISTINE_BG[pristine_tier]
        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        bg.fill(fill_col)
        screen.blit(bg, (ox, oy))
        pygame.draw.rect(screen, edge_col, (ox, oy, mw, mh), 3)
    elif is_blood:
        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        bg.fill((60, 0, 0, 220))
        screen.blit(bg, (ox, oy))
        pygame.draw.rect(screen, (200, 50, 50), (ox, oy, mw, mh), 2)
    else:
        bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
        bg.fill((15, 15, 15, 210))
        screen.blit(bg, (ox, oy))
        pygame.draw.rect(screen, GRAY, (ox, oy, mw, mh), 2)

    PRISTINE_TITLE = {"bronze": (220, 150, 60), "silver": (220, 220, 230), "gold": (255, 215, 80)}
    title_col = PRISTINE_TITLE[pristine_tier] if is_pristine else ((255, 80, 80) if is_blood else WHITE)
    screen.blit(font.render(f"Tower: {tower.type}", True, title_col), (ox + 10, oy + 10))
    screen.blit(font.render(f"Level: {tower.level}/{tower.max_level}", True, YELLOW), (ox + 10, oy + 34))
    screen.blit(font.render(f"HP: {int(tower.health)}/{tower.max_health}", True, (180, 255, 180)), (ox + 10, oy + 56))
    # Lifetime kills counter (top-right of panel)
    _kills_txt = font_sm.render(f"Kills: {getattr(tower, 'kills', 0)}", True, (255, 200, 100))
    screen.blit(_kills_txt, (ox + mw - _kills_txt.get_width() - 10, oy + 38))
    sell_val = int((tower.cost + tower.upgrade_cost_spent) * 0.7)
    upgrade_menu_sell_rect = pygame.Rect(ox + 10, oy + 73, 116, 22)
    pygame.draw.rect(screen, (110, 85, 15), upgrade_menu_sell_rect, border_radius=4)
    pygame.draw.rect(screen, (200, 170, 40), upgrade_menu_sell_rect, 1, border_radius=4)
    screen.blit(font_sm.render(f"Sell {sell_val}", True, (255, 230, 100)), (ox + 14, oy + 76))
    move_cost = max(1, int((tower.cost + tower.upgrade_cost_spent) * 0.05))
    upgrade_menu_move_rect = pygame.Rect(ox + 134, oy + 73, 116, 22)
    mv_col = (40, 90, 140) if coins >= move_cost else (60, 60, 60)
    pygame.draw.rect(screen, mv_col, upgrade_menu_move_rect, border_radius=4)
    pygame.draw.rect(screen, (120, 200, 255), upgrade_menu_move_rect, 1, border_radius=4)
    screen.blit(font_sm.render(f"Move {move_cost}", True, WHITE), (ox + 140, oy + 76))

    upgrade_menu_revive_rect = None
    if tower.type == "builder_hut" and len(tower.builders) < 1:
        rv_col = (0, 130, 0) if coins >= 10000 else (60, 60, 60)
        upgrade_menu_revive_rect = pygame.Rect(ox + 10, oy + 168, 240, 22)
        pygame.draw.rect(screen, rv_col, upgrade_menu_revive_rect, border_radius=4)
        pygame.draw.rect(screen, (120, 255, 120), upgrade_menu_revive_rect, 1, border_radius=4)
        screen.blit(font_sm.render("Revive Builder (10,000)", True, WHITE), (ox + 14, oy + 171))

    if tower.type == "Valkyrie Hut" and not tower.valk_built:
        prog = min(1.0, tower.valk_kills / max(1, tower.valk_kills_needed))
        screen.blit(font.render("Being built...", True, (255, 200, 60)), (ox + 10, oy + 96))
        screen.blit(font_sm.render(f"Kills: {tower.valk_kills}/{tower.valk_kills_needed}", True, (220, 200, 100)), (ox + 10, oy + 118))
        pygame.draw.rect(screen, (60, 40, 10), (ox + 10, oy + 138, 180, 8))
        pygame.draw.rect(screen, (255, 200, 50), (ox + 10, oy + 138, int(180 * prog), 8))
        screen.blit(font_sm.render("Upgrades locked until built", True, (180, 150, 80)), (ox + 10, oy + 152))
        upgrade_menu_upgrade_rect = None
    elif at_max:
        screen.blit(font.render("MAX LEVEL", True, YELLOW), (ox + 10, oy + 96))
        upgrade_menu_upgrade_rect = None
    elif info:
        if is_pristine and not shadow_storm_active:
            screen.blit(font.render("LOCKED: Shadow Storm", True, (200, 130, 255)), (ox + 10, oy + 96))
            screen.blit(font_sm.render("(Unlocks at wave 75)", True, (170, 110, 220)), (ox + 10, oy + 116))
            upgrade_menu_upgrade_rect = None
        elif is_blood and not blood_storm_active:
            screen.blit(font.render("LOCKED: Blood Storm", True, (255, 100, 100)), (ox + 10, oy + 96))
            screen.blit(font_sm.render("(Unlocks at wave 35)", True, (200, 100, 100)), (ox + 10, oy + 116))
            upgrade_menu_upgrade_rect = None
        else:
            desc = info.get("desc", "")
            if desc:
                desc_col = (255, 220, 120) if is_pristine else ((255, 150, 100) if is_blood else (180, 220, 255))
                screen.blit(font_tiny.render(desc, True, desc_col), (ox + 10, oy + 96))
            screen.blit(font.render(f"Cost: {info['cost']}", True, GREEN if coins >= info["cost"] else RED), (ox + 10, oy + 114))
            if info["damage"]:
                screen.blit(font.render(f"Dmg: +{info['damage']}", True, WHITE), (ox + 10, oy + 134))
            if info["range"]:
                screen.blit(font.render(f"Range: +{info['range']}", True, WHITE), (ox + 10, oy + 154))
            if info["health"]:
                screen.blit(font.render(f"HP: +{info['health']}", True, WHITE), (ox + 10, oy + 172))
            is_combine = tower.type == "Valkyrie Hut" and tower.level == 3 and not tower.valk_combined
            PRISTINE_BTN = {"bronze": (200, 130, 40), "silver": (180, 180, 200), "gold": (230, 180, 40)}
            if is_pristine and coins >= info["cost"]:
                bc = PRISTINE_BTN[pristine_tier]
            elif is_blood and coins >= info["cost"]:
                bc = (180, 0, 0)
            elif is_combine:
                bc = (120, 80, 180)
            elif coins >= info["cost"]:
                bc = (0, 180, 0)
            else:
                bc = DARKGRAY
            upgrade_menu_upgrade_rect = pygame.Rect(ox + 10, oy + 196, 105, 36)
            pygame.draw.rect(screen, bc, upgrade_menu_upgrade_rect)
            if is_combine:
                upgrade_label = "COMBINE!"
            elif is_pristine:
                upgrade_label = pristine_tier.upper()
            elif is_blood:
                upgrade_label = "BLOOD UP"
            else:
                upgrade_label = "Upgrade"
            screen.blit(font.render(upgrade_label, True, WHITE), (ox + 14, oy + 206))

    # Frost laser: show-circles toggle
    if tower.type == "frost_laser":
        global frost_show_circles_rect
        fc = (40, 100, 200) if frost_show_circles else (35, 35, 70)
        frost_show_circles_rect = pygame.Rect(ox + 10, oy + 178, 240, 16)
        pygame.draw.rect(screen, fc, frost_show_circles_rect, border_radius=3)
        screen.blit(font_tiny.render("Show Circles: ON" if frost_show_circles else "Show Circles: OFF", True, WHITE), (ox + 14, oy + 180))

    upgrade_menu_close_rect = pygame.Rect(ox + 145, oy + 196, 104, 36)
    pygame.draw.rect(screen, (100, 0, 0) if is_blood else (180, 0, 0), upgrade_menu_close_rect)
    screen.blit(font.render("Close", True, WHITE), (ox + 168, oy + 206))

    # Builder Hut: Q to instant-buy builder
    if tower.type == "builder_hut" and len(tower.builders) < 1 and wave_number < tower.builder_respawn_wave:
        rounds_left = tower.builder_respawn_wave - wave_number
        screen.blit(font_sm.render(f"Builder respawns in {rounds_left} waves", True, (255, 180, 80)), (ox + 6, oy + 200 + 10))
        screen.blit(font_sm.render("Press Q: buy now (10,000)", True, (200, 255, 150)), (ox + 6, oy + 200 + 24))


def draw_shadow_storm_splash():
    """Shadow Storm full-screen title (wave 75) + info-panel popup."""
    global shadow_storm_splash_timer, shadow_storm_info_rect, shadow_storm_info_close_rect
    font_huge = pygame.font.SysFont("verdana", 130)
    if shadow_storm_splash_timer > 0:
        alpha = min(230, int(shadow_storm_splash_timer * 2.5))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((60, 0, 100, alpha))
        screen.blit(overlay, (0, 0))
        t_surf = font_huge.render("SHADOW STORM", True, (200, 130, 255))
        t_x = WIDTH // 2 - t_surf.get_width() // 2
        t_y = HEIGHT // 2 - 80
        shadow = font_huge.render("SHADOW STORM", True, (40, 0, 60))
        screen.blit(shadow, (t_x + 4, t_y + 4))
        screen.blit(t_surf, (t_x, t_y))
        sub1 = font_lg.render("Wave 75 reached — the void descends!", True, (220, 180, 255))
        sub2 = font_lg.render("Old enemies: 10× HP & dmg, 3× coins. Pristine upgrades unlocked.", True, (230, 200, 255))
        screen.blit(sub1, (WIDTH // 2 - sub1.get_width() // 2, HEIGHT // 2 + 70))
        screen.blit(sub2, (WIDTH // 2 - sub2.get_width() // 2, HEIGHT // 2 + 100))
        shadow_storm_splash_timer -= 1

    if shadow_storm_info_open and state in ("GAME", "ARENA"):
        pw, ph = 460, 240
        px = WIDTH // 2 - pw // 2
        py = HEIGHT // 2 - ph // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((40, 0, 70, 235))
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, (160, 80, 220), (px, py, pw, ph), 3)
        lines = [
            ("SHADOW STORM", (210, 140, 255), font_lg),
            ("• Old enemies: 10× HP and 10× damage to towers", WHITE, font),
            ("• +2% HP per wave past 75", WHITE, font),
            ("• 3× coin drops (stacks with Blood Storm 5×)", WHITE, font),
            ("• Pristine Bronze / Silver / Gold tiers per tower", (220, 180, 255), font),
            ("• New shadow bosses begin appearing", WHITE, font),
            ("• Background turns purple — survive the void!", WHITE, font),
        ]
        for i, (txt, col, fnt) in enumerate(lines):
            screen.blit(fnt.render(txt, True, col), (px + 15, py + 10 + i * 32))
        shadow_storm_info_close_rect = pygame.Rect(px + pw - 90, py + ph - 40, 80, 30)
        pygame.draw.rect(screen, (110, 30, 180), shadow_storm_info_close_rect)
        screen.blit(font.render("Close", True, WHITE), (px + pw - 75, py + ph - 34))


def draw_blood_storm_splash():
    global blood_storm_splash_timer, blood_storm_info_rect, blood_storm_info_close_rect
    font_huge = pygame.font.SysFont("verdana", 130)

    if blood_storm_splash_timer > 0:
        alpha = min(230, int(blood_storm_splash_timer * 2.5))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((120, 0, 0, alpha))
        screen.blit(overlay, (0, 0))

        t_surf = font_huge.render("BLOOD STORM", True, (255, 40, 40))
        t_x = WIDTH // 2 - t_surf.get_width() // 2
        t_y = HEIGHT // 2 - 80
        shadow = font_huge.render("BLOOD STORM", True, (80, 0, 0))
        screen.blit(shadow, (t_x + 4, t_y + 4))
        screen.blit(t_surf, (t_x, t_y))

        sub1 = font_lg.render("Wave 35 reached — the storm has begun!", True, (255, 160, 160))
        sub2 = font_lg.render("Enemies: 2× health, 5× coins. New upgrades unlocked.", True, (255, 200, 200))
        screen.blit(sub1, (WIDTH // 2 - sub1.get_width() // 2, HEIGHT // 2 + 70))
        screen.blit(sub2, (WIDTH // 2 - sub2.get_width() // 2, HEIGHT // 2 + 100))
        blood_storm_splash_timer -= 1

    # Note: in state == "GAME", the Blood Storm button is drawn by draw_ui in
    # the top bar instead. Only ARENA still uses the legacy left-column button.
    if blood_storm_active and state == "ARENA":
        blood_storm_info_rect = pygame.Rect(10, 142, 130, 34)
        disabled = arena_shop_open
        fill_col = (75, 45, 45) if disabled else (160, 0, 0)
        edge_col = (120, 80, 80) if disabled else (255, 60, 60)
        text_col = (160, 140, 140) if disabled else WHITE
        pygame.draw.rect(screen, fill_col, blood_storm_info_rect, border_radius=12)
        pygame.draw.rect(screen, edge_col, blood_storm_info_rect, 2, border_radius=12)
        storm_lbl = font_sm.render("Blood Storm", True, text_col)
        screen.blit(storm_lbl, (blood_storm_info_rect.centerx - storm_lbl.get_width() // 2, blood_storm_info_rect.centery - storm_lbl.get_height() // 2))

    # Info popup pops up in BOTH game and arena states whenever requested
    if blood_storm_info_open and state in ("GAME", "ARENA"):
        pw, ph = 420, 210
        px = WIDTH // 2 - pw // 2
        py = HEIGHT // 2 - ph // 2
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((50, 0, 0, 230))
        screen.blit(panel, (px, py))
        pygame.draw.rect(screen, (220, 30, 30), (px, py, pw, ph), 3)
        lines = [
            ("BLOOD STORM", (255, 80, 80), font_lg),
            ("• All enemies spawn with 2× health", WHITE, font),
            ("• All enemies drop 5× coins on death", WHITE, font),
            ("• 3 Blood Upgrade tiers per tower now unlocked", (255, 150, 150), font),
            ("• New terrifying enemies begin appearing", WHITE, font),
            ("• Background turns red — stay vigilant!", WHITE, font),
        ]
        for i, (txt, col, fnt) in enumerate(lines):
            screen.blit(fnt.render(txt, True, col), (px + 15, py + 10 + i * 32))
        blood_storm_info_close_rect = pygame.Rect(px + pw - 90, py + ph - 40, 80, 30)
        pygame.draw.rect(screen, (140, 0, 0), blood_storm_info_close_rect)
        screen.blit(font.render("Close", True, WHITE), (px + pw - 75, py + ph - 34))


def _draw_play_menu_chrome():
    """Top-bar buttons + diagonal title for the logged-in main play menu."""
    # Background: dark with diagonal stripe pattern
    screen.fill((20, 22, 26))
    stripe_col = (28, 30, 36)
    spacing = 28
    for i in range(-HEIGHT, WIDTH + HEIGHT, spacing):
        pygame.draw.line(screen, stripe_col, (i, 0), (i + HEIGHT, HEIGHT), 4)
    # Top bar background
    pygame.draw.rect(screen, (38, 40, 46), (0, 0, WIDTH, 64))
    pygame.draw.line(screen, (12, 12, 14), (0, 64), (WIDTH, 64), 2)
    # Top-bar buttons (rects are checked verbatim in click handler)
    def btn(rect, fill, edge, label, label_col=WHITE, font_=font):
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, edge, rect, 2, border_radius=10)
        ls = font_.render(label, True, label_col)
        screen.blit(ls, (rect.centerx - ls.get_width() // 2, rect.centery - ls.get_height() // 2))
    btn(pygame.Rect(10, 10, 130, 44), (180, 30, 30), (255, 90, 90), "ARENA MODE", WHITE, font_sm)
    btn(pygame.Rect(150, 10, 200, 44), (30, 170, 60), (90, 240, 130), "PLAY", BLACK, font)
    btn(pygame.Rect(360, 10, 200, 44), (30, 90, 200), (110, 170, 255), "LEADERBOARD", WHITE, font)
    btn(pygame.Rect(WIDTH - 130, 10, 120, 44), (70, 70, 78), (160, 160, 170), "SHOP", WHITE, font)
    # Big diagonal "TOWER DEFENCE" title
    title_surf = font_lg.render("TOWER DEFENCE", True, (235, 230, 220))
    title_surf = pygame.transform.rotozoom(title_surf, 12, 1.6)
    tr = title_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
    # Subtle drop shadow
    shadow = pygame.transform.rotozoom(font_lg.render("TOWER DEFENCE", True, (5, 5, 5)), 12, 1.6)
    screen.blit(shadow, shadow.get_rect(center=(tr.centerx + 4, tr.centery + 4)))
    screen.blit(title_surf, tr)


def draw_main_menu():
    global menu_path_rects
    if logged_in_user == "admin":
        _draw_play_menu_chrome()
        user_coins = users.get(logged_in_user, {}).get("coins", 400)
        coin_surf = font_sm.render(f"Coins: {user_coins}   (Admin)", True, GOLD)
        screen.blit(coin_surf, (WIDTH // 2 - coin_surf.get_width() // 2, 80))
        if path_shop_open:
            menu_path_rects = {}
            px, py = WIDTH // 2 + 130, 80
            pw, ph = 320, 50 + len(PATHS) * 85
            pygame.draw.rect(screen, (30, 20, 50), (px, py, pw, ph), border_radius=10)
            pygame.draw.rect(screen, (120, 80, 200), (px, py, pw, ph), 2, border_radius=10)
            screen.blit(font.render("Choose a Path", True, (180, 140, 255)), (px + 10, py + 10))
            for i, pdata in enumerate(PATHS):
                ry = py + 45 + i * 85
                pid = pdata["id"]
                is_owned = pid in owned_path_ids
                is_sel = pid == selected_path_id
                bg = (50, 80, 30) if is_sel else ((40, 40, 60) if is_owned else (60, 30, 30))
                pr = pygame.Rect(px + 8, ry, pw - 16, 78)
                pygame.draw.rect(screen, bg, pr)
                pygame.draw.rect(screen, (150, 100, 255), pr, 1)
                screen.blit(font.render(pdata["name"], True, (220, 220, 255)), (px + 14, ry + 5))
                screen.blit(font_sm.render(pdata["desc"], True, (180, 180, 180)), (px + 14, ry + 27))
                if is_sel:
                    screen.blit(font_sm.render("SELECTED", True, (80, 255, 80)), (px + 14, ry + 50))
                elif is_owned:
                    sel_r = pygame.Rect(px + pw - 100, ry + 44, 85, 26)
                    pygame.draw.rect(screen, (40, 120, 40), sel_r)
                    screen.blit(font_sm.render("Select", True, WHITE), (sel_r.x + 18, sel_r.y + 5))
                    menu_path_rects[pid] = ("select", sel_r)
                else:
                    cost_str = "FREE (Admin)"
                    screen.blit(font_sm.render(cost_str, True, GOLD), (px + 14, ry + 50))
                    buy_r = pygame.Rect(px + pw - 95, ry + 44, 80, 26)
                    pygame.draw.rect(screen, (0, 130, 0), buy_r)
                    screen.blit(font_sm.render("Unlock", True, WHITE), (buy_r.x + 14, buy_r.y + 5))
                    menu_path_rects[pid] = ("buy", buy_r)
    elif logged_in_user:
        _draw_play_menu_chrome()
        # Coin display + welcome (under top bar)
        user_coins = users.get(logged_in_user, {}).get("coins", 0)
        _ws = font_sm.render(f"Welcome, {logged_in_user}  •  Coins: {user_coins:,}", True, GOLD)
        screen.blit(_ws, (WIDTH // 2 - _ws.get_width() // 2, 80))
        # Path shop panel
        if path_shop_open:
            menu_path_rects = {}
            px, py = WIDTH // 2 + 130, 80
            pw, ph = 320, 50 + len(PATHS) * 85
            pygame.draw.rect(screen, (30, 20, 50), (px, py, pw, ph), border_radius=10)
            pygame.draw.rect(screen, (120, 80, 200), (px, py, pw, ph), 2, border_radius=10)
            screen.blit(font.render("Choose a Path", True, (180, 140, 255)), (px + 10, py + 10))
            for i, pdata in enumerate(PATHS):
                ry = py + 45 + i * 85
                pid = pdata["id"]
                is_owned = pid in owned_path_ids
                is_sel = pid == selected_path_id
                bg = (50, 80, 30) if is_sel else ((40, 40, 60) if is_owned else (60, 30, 30))
                pr = pygame.Rect(px + 8, ry, pw - 16, 78)
                pygame.draw.rect(screen, bg, pr)
                pygame.draw.rect(screen, (150, 100, 255), pr, 1)
                screen.blit(font.render(pdata["name"], True, (220, 220, 255)), (px + 14, ry + 5))
                screen.blit(font_sm.render(pdata["desc"], True, (180, 180, 180)), (px + 14, ry + 27))
                if is_sel:
                    screen.blit(font_sm.render("SELECTED", True, (80, 255, 80)), (px + 14, ry + 50))
                elif is_owned:
                    sel_r = pygame.Rect(px + pw - 100, ry + 44, 85, 26)
                    pygame.draw.rect(screen, (40, 120, 40), sel_r)
                    screen.blit(font_sm.render("Select", True, WHITE), (sel_r.x + 18, sel_r.y + 5))
                    menu_path_rects[pid] = ("select", sel_r)
                else:
                    cost_str = f"{pdata['cost']:,} coins"
                    screen.blit(font_sm.render(cost_str, True, GOLD), (px + 14, ry + 50))
                    buy_r = pygame.Rect(px + pw - 95, ry + 44, 80, 26)
                    can_buy = user_coins >= pdata["cost"]
                    pygame.draw.rect(screen, (0, 130, 0) if can_buy else (80, 80, 80), buy_r)
                    screen.blit(font_sm.render("Buy", True, WHITE), (buy_r.x + 24, buy_r.y + 5))
                    menu_path_rects[pid] = ("buy", buy_r)
    else:
        # ── Startup screen (per startup.png): orange bg, big TOWER DEFENCE title,
        #    angled black-bordered box with two green LOGIN / SIGN UP buttons. ──
        screen.fill((216, 130, 40))
        # Yellow stripe at the top
        pygame.draw.rect(screen, (245, 200, 50), (0, 0, WIDTH, 18))
        pygame.draw.rect(screen, (170, 100, 25), (0, 18, WIDTH, 4))
        # Big tilted "TOWER DEFENCE" title
        title_base = font_lg.render("TOWER DEFENCE", True, (10, 10, 10))
        title_rot = pygame.transform.rotozoom(title_base, 6, 1.7)
        tr = title_rot.get_rect(center=(WIDTH // 2, 150))
        # Drop shadow
        shadow = pygame.transform.rotozoom(font_lg.render("TOWER DEFENCE", True, (140, 80, 20)), 6, 1.7)
        screen.blit(shadow, shadow.get_rect(center=(tr.centerx + 5, tr.centery + 5)))
        screen.blit(title_rot, tr)
        # Black-bordered angled box around buttons
        box = pygame.Rect(WIDTH // 2 - 130, 250, 260, 220)
        pygame.draw.rect(screen, (235, 160, 60), box, border_radius=14)
        pygame.draw.rect(screen, (10, 10, 10), box, 4, border_radius=14)
        # LOGIN button (kept in y=280..330 hit zone for click handler)
        login_r = pygame.Rect(WIDTH // 2 - 100, 280, 200, 50)
        pygame.draw.rect(screen, (40, 180, 70), login_r, border_radius=12)
        pygame.draw.rect(screen, (10, 80, 20), login_r, 4, border_radius=12)
        ls = font.render("LOGIN", True, (15, 30, 15))
        screen.blit(ls, ls.get_rect(center=login_r.center))
        # SIGN UP button (y=350..400)
        signup_r = pygame.Rect(WIDTH // 2 - 100, 350, 200, 50)
        pygame.draw.rect(screen, (40, 180, 70), signup_r, border_radius=12)
        pygame.draw.rect(screen, (10, 80, 20), signup_r, 4, border_radius=12)
        ss = font.render("SIGN UP", True, (15, 30, 15))
        screen.blit(ss, ss.get_rect(center=signup_r.center))


def draw_back_button():
    r = pygame.Rect(10, 10, 100, 40)
    pygame.draw.rect(screen, (200, 0, 0), r, border_radius=8)
    screen.blit(font.render("Back", True, WHITE), (20, 15))
    return r


def _draw_orange_form_chrome(title):
    screen.fill((216, 130, 40))
    pygame.draw.rect(screen, (245, 200, 50), (0, 0, WIDTH, 18))
    pygame.draw.rect(screen, (170, 100, 25), (0, 18, WIDTH, 4))
    t = pygame.transform.rotozoom(font_lg.render("TOWER DEFENCE", True, (10, 10, 10)), 6, 1.2)
    tr = t.get_rect(center=(WIDTH // 2, 70))
    screen.blit(t, tr)
    sub = font.render(title, True, (15, 15, 15))
    screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 130)))


def draw_login_screen(ub, pb):
    _draw_orange_form_chrome("LOGIN")
    ub.draw(screen)
    pb.draw(screen)
    r = pygame.Rect(WIDTH // 2 - 75, 300, 150, 40)
    pygame.draw.rect(screen, (40, 180, 70), r, border_radius=10)
    pygame.draw.rect(screen, (10, 80, 20), r, 3, border_radius=10)
    ls = font.render("LOGIN", True, (15, 30, 15))
    screen.blit(ls, ls.get_rect(center=r.center))
    if login_error:
        s = font.render(login_error, True, (200, 20, 20))
        screen.blit(s, (WIDTH // 2 - s.get_width() // 2, 360))


def draw_signup_screen(ub, pb):
    _draw_orange_form_chrome("SIGN UP")
    ub.draw(screen)
    pb.draw(screen)
    r = pygame.Rect(WIDTH // 2 - 75, 300, 150, 40)
    pygame.draw.rect(screen, (40, 180, 70), r, border_radius=10)
    pygame.draw.rect(screen, (10, 80, 20), r, 3, border_radius=10)
    ls = font.render("CREATE", True, (15, 30, 15))
    screen.blit(ls, ls.get_rect(center=r.center))
    if signup_error:
        s = font.render(signup_error, True, (200, 20, 20))
        screen.blit(s, (WIDTH // 2 - s.get_width() // 2, 360))


def draw_logged_in_user(bottom_right=False):
    sz = 40
    pad = 8
    x = WIDTH - sz - pad
    y = (HEIGHT - sz - pad) if bottom_right else 8
    pygame.draw.circle(screen, (0, 120, 255), (x + sz // 2, y + sz // 2), sz // 2)
    # Username label rendered to the LEFT of the icon, vertically centered, clipped
    s = font_sm.render(logged_in_user, True, WHITE)
    label_max_w = 90
    label_x = x - min(s.get_width(), label_max_w) - 6
    label_y = y + (sz - s.get_height()) // 2
    label_clip_rect = pygame.Rect(label_x, label_y, min(s.get_width(), label_max_w), s.get_height())
    prev_clip = screen.get_clip()
    screen.set_clip(label_clip_rect)
    screen.blit(s, (label_x, label_y))
    screen.set_clip(prev_clip)
    return pygame.Rect(x, y, sz, sz)


def draw_logout_menu(x, y):
    global mobile_mode_menu_rect
    mob_col = (20, 140, 60) if mobile_mode else (80, 80, 80)
    mob_label = "Mobile: ON" if mobile_mode else "Mobile: OFF"
    # Drops DOWN from the top-right user icon (or bottom-right on MENU).
    # Anchor panel so it hugs the right edge of the screen.
    # In ARENA, admin command button is hidden to keep HUD clean.
    # Always show the admin Command button (including in ARENA per user request)
    hide_command = False
    if is_admin:
        if hide_command:
            panel_w, panel_h = 130, 134
        else:
            panel_w, panel_h = 130, 176
        panel_x = max(4, x + 40 - panel_w)
        # Drop upward from the icon when it's placed at the bottom
        if y > HEIGHT // 2:
            panel_y = y - panel_h
        else:
            panel_y = y + 48
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, (20, 20, 40), panel)
        pygame.draw.rect(screen, (200, 180, 0), panel, 2)
        cmd_r = pygame.Rect(0, 0, 0, 0)
        if not hide_command:
            cmd_r = pygame.Rect(panel.x + 7, panel.y + 8, 116, 32)
            pygame.draw.rect(screen, (100, 70, 0), cmd_r)
            s = font.render("Command", True, GOLD)
            screen.blit(s, s.get_rect(center=cmd_r.center))
            btn_start_y = 50
        else:
            btn_start_y = 8
        logout_r = pygame.Rect(panel.x + 7, panel.y + btn_start_y, 116, 32)
        pygame.draw.rect(screen, (160, 20, 20), logout_r)
        s = font.render("Logout", True, WHITE)
        screen.blit(s, s.get_rect(center=logout_r.center))
        return_r = pygame.Rect(panel.x + 7, panel.y + btn_start_y + 42, 116, 32)
        pygame.draw.rect(screen, (20, 30, 140), return_r)
        s = font.render("Return", True, WHITE)
        screen.blit(s, s.get_rect(center=return_r.center))
        mob_r = pygame.Rect(panel.x + 7, panel.y + btn_start_y + 84, 116, 32)
        pygame.draw.rect(screen, mob_col, mob_r)
        s = font.render(mob_label, True, WHITE)
        screen.blit(s, s.get_rect(center=mob_r.center))
        mobile_mode_menu_rect = mob_r
        return logout_r, return_r, cmd_r, mob_r
    else:
        panel_w, panel_h = 130, 134
        panel_x = max(4, x + 40 - panel_w)
        panel_y = (y - panel_h) if y > HEIGHT // 2 else (y + 48)
        panel = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(screen, (40, 40, 50), panel)
        pygame.draw.rect(screen, (200, 0, 0), panel, 2)
        logout_r = pygame.Rect(panel.x + 7, panel.y + 8, 116, 32)
        pygame.draw.rect(screen, (160, 20, 20), logout_r)
        s = font.render("Logout", True, WHITE)
        screen.blit(s, s.get_rect(center=logout_r.center))
        return_r = pygame.Rect(panel.x + 7, panel.y + 50, 116, 32)
        pygame.draw.rect(screen, (20, 30, 140), return_r)
        s = font.render("Return", True, WHITE)
        screen.blit(s, s.get_rect(center=return_r.center))
        mob_r = pygame.Rect(panel.x + 7, panel.y + 92, 116, 32)
        pygame.draw.rect(screen, mob_col, mob_r)
        s = font.render(mob_label, True, WHITE)
        screen.blit(s, s.get_rect(center=mob_r.center))
        mobile_mode_menu_rect = mob_r
        return logout_r, return_r, None, mob_r


def draw_admin_panel():
    global admin_delete_buttons
    admin_delete_buttons = {}
    screen.fill((15, 15, 35))
    screen.blit(font.render("Admin Panel — User Accounts", True, GOLD), (WIDTH // 2 - 120, 20))
    screen.blit(font.render("Username", True, WHITE), (60, 65))
    screen.blit(font.render("Password (hashed)", True, WHITE), (260, 65))
    pygame.draw.line(screen, GRAY, (40, 90), (WIDTH - 40, 90), 1)
    ry = 105
    for uname, data in list(users.items()):
        screen.blit(font.render(uname, True, CYAN), (60, ry))
        screen.blit(font.render(data["password"][:28] + "...", True, GRAY), (260, ry))
        dr = pygame.Rect(WIDTH - 130, ry - 4, 100, 28)
        pygame.draw.rect(screen, (180, 30, 30), dr)
        screen.blit(font.render("Delete", True, WHITE), (dr.x + 18, dr.y + 5))
        admin_delete_buttons[uname] = dr
        ry += 45
        if ry > HEIGHT - 80:
            break
    br = pygame.Rect(20, 20, 100, 36)
    pygame.draw.rect(screen, DARKGRAY, br)
    screen.blit(font.render("< Back", True, WHITE), (30, 28))
    lr = pygame.Rect(WIDTH - 130, 20, 110, 36)
    pygame.draw.rect(screen, (180, 30, 30), lr)
    screen.blit(font.render("Logout", True, WHITE), (WIDTH - 110, 28))
    return br, lr


def draw_arena_vpad():
    """Draw on-screen virtual controls for mobile play in Arena mode."""
    global arena_vpad_rects, arena_vpad_fire_rect
    BTN = 68
    alpha = 160
    pad_surf = pygame.Surface((BTN, BTN), pygame.SRCALPHA)

    def _btn(rect, label, color):
        s = pygame.Surface((BTN, BTN), pygame.SRCALPHA)
        pygame.draw.rect(s, color + (alpha,), (0, 0, BTN, BTN), border_radius=12)
        pygame.draw.rect(s, (255, 255, 255, 100), (0, 0, BTN, BTN), 2, border_radius=12)
        lbl = font.render(label, True, (255, 255, 255))
        s.blit(lbl, lbl.get_rect(center=(BTN // 2, BTN // 2)))
        screen.blit(s, (rect.x, rect.y))

    bx, by = 10, HEIGHT - BTN - 10          # bottom-left anchor for LEFT btn
    up_r    = pygame.Rect(bx + BTN + 4, by - BTN - 4, BTN, BTN)
    left_r  = pygame.Rect(bx,           by,            BTN, BTN)
    down_r  = pygame.Rect(bx + BTN + 4, by,            BTN, BTN)
    right_r = pygame.Rect(bx + (BTN+4)*2, by,          BTN, BTN)

    _btn(up_r,    "^",  (30,  80,  180))
    _btn(left_r,  "<",  (30,  80,  180))
    _btn(down_r,  "v",  (30,  80,  180))
    _btn(right_r, ">",  (30,  80,  180))

    FIRE_R = 55
    fx, fy = WIDTH - FIRE_R - 15, HEIGHT - FIRE_R - 15
    fire_surf = pygame.Surface((FIRE_R*2, FIRE_R*2), pygame.SRCALPHA)
    pygame.draw.circle(fire_surf, (200, 50, 50, alpha), (FIRE_R, FIRE_R), FIRE_R)
    pygame.draw.circle(fire_surf, (255, 100, 100, 120), (FIRE_R, FIRE_R), FIRE_R, 3)
    lbl = font.render("FIRE", True, (255, 255, 200))
    fire_surf.blit(lbl, lbl.get_rect(center=(FIRE_R, FIRE_R)))
    screen.blit(fire_surf, (fx - FIRE_R, fy - FIRE_R))

    arena_vpad_rects = {"up": up_r, "down": down_r, "left": left_r, "right": right_r}
    arena_vpad_fire_rect = pygame.Rect(fx - FIRE_R, fy - FIRE_R, FIRE_R * 2, FIRE_R * 2)


def draw_onscreen_keyboard():
    global onscreen_kb_rects, keyboard_panel_rect, kb_shift
    onscreen_kb_rects = {}
    KW, KH, GAP = 44, 44, 5
    PANEL_Y = 370
    keyboard_panel_rect = pygame.Rect(0, PANEL_Y - 10, WIDTH, HEIGHT - PANEL_Y + 10)
    pygame.draw.rect(screen, (20, 20, 45), keyboard_panel_rect)
    pygame.draw.rect(screen, (80, 80, 140), keyboard_panel_rect, 2)

    def _key(label, x, y, w=KW, color=(70, 70, 130)):
        r = pygame.Rect(x, y, w, KH)
        pygame.draw.rect(screen, color, r, border_radius=7)
        pygame.draw.rect(screen, (140, 140, 200), r, 1, border_radius=7)
        disp = label.upper() if (kb_shift and len(label) == 1 and label.isalpha()) else label
        lbl = font_sm.render(disp, True, WHITE)
        screen.blit(lbl, lbl.get_rect(center=r.center))
        onscreen_kb_rects[label] = r

    # Row 0 – numbers
    row0 = "1234567890"
    rx0 = (WIDTH - (len(row0) * KW + (len(row0) - 1) * GAP)) // 2
    for i, ch in enumerate(row0):
        _key(ch, rx0 + i * (KW + GAP), PANEL_Y)

    # Row 1 – qwertyuiop
    row1 = "qwertyuiop"
    rx1 = (WIDTH - (len(row1) * KW + (len(row1) - 1) * GAP)) // 2
    for i, ch in enumerate(row1):
        _key(ch, rx1 + i * (KW + GAP), PANEL_Y + KH + GAP)

    # Row 2 – asdfghjkl
    row2 = "asdfghjkl"
    rx2 = (WIDTH - (len(row2) * KW + (len(row2) - 1) * GAP)) // 2
    for i, ch in enumerate(row2):
        _key(ch, rx2 + i * (KW + GAP), PANEL_Y + 2 * (KH + GAP))

    # Row 3 – SHIFT + zxcvbnm + BACK
    WIDE = 68
    row3 = "zxcvbnm"
    row3_w = WIDE + GAP + len(row3) * KW + (len(row3) - 1) * GAP + GAP + WIDE
    rx3 = (WIDTH - row3_w) // 2
    shift_col = (80, 140, 80) if kb_shift else (55, 80, 55)
    _key("SHIFT", rx3, PANEL_Y + 3 * (KH + GAP), w=WIDE, color=shift_col)
    for i, ch in enumerate(row3):
        _key(ch, rx3 + WIDE + GAP + i * (KW + GAP), PANEL_Y + 3 * (KH + GAP))
    _key("BACK", rx3 + WIDE + GAP + len(row3) * (KW + GAP), PANEL_Y + 3 * (KH + GAP),
         w=WIDE, color=(140, 55, 55))

    # Row 4 – SPACE + GO
    SPACE_W, GO_W = 320, 110
    row4_w = SPACE_W + GAP + GO_W
    rx4 = (WIDTH - row4_w) // 2
    _key("SPACE", rx4, PANEL_Y + 4 * (KH + GAP), w=SPACE_W, color=(60, 60, 110))
    _key("GO", rx4 + SPACE_W + GAP, PANEL_Y + 4 * (KH + GAP), w=GO_W, color=(40, 140, 70))


def draw_skip_wave_dialog():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    screen.blit(overlay, (0, 0))
    dlg = pygame.Rect(WIDTH // 2 - 140, HEIGHT // 2 - 80, 280, 160)
    pygame.draw.rect(screen, (20, 20, 40), dlg)
    pygame.draw.rect(screen, (200, 180, 0), dlg, 2)
    screen.blit(font.render("Skip to Wave (Admin)", True, GOLD), (dlg.x + 14, dlg.y + 12))
    inp_rect = pygame.Rect(dlg.x + 14, dlg.y + 50, 252, 36)
    pygame.draw.rect(screen, (40, 40, 60), inp_rect)
    pygame.draw.rect(screen, (200, 180, 0), inp_rect, 1)
    display_str = skip_wave_str if skip_wave_str else ""
    screen.blit(font.render(display_str + "|", True, WHITE), (inp_rect.x + 8, inp_rect.y + 7))
    screen.blit(font_sm.render("Type a wave number then press Enter", True, (180, 180, 180)), (dlg.x + 14, dlg.y + 96))
    screen.blit(font_sm.render("Esc to cancel", True, (140, 140, 140)), (dlg.x + 14, dlg.y + 118))


# ── Leaderboard helpers ───────────────────────────────────────────────────────
LEADERBOARD_FILE = "leaderboard.json"


def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        try:
            with open(LEADERBOARD_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"normal": [], "nightmare": [], "arena": []}


def save_leaderboard(lb):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(lb, f, indent=2)


def update_leaderboard(username, wave_val, coins_val, nightmare=False, arena=False):
    if not username:
        return
    lb = load_leaderboard()
    if "arena" not in lb:
        lb["arena"] = []
    if arena:
        tab = "arena"
    else:
        tab = "nightmare" if nightmare else "normal"
    lb[tab] = [e for e in lb[tab] if e.get("username") != username]
    lb[tab].append({"username": username, "wave": wave_val, "coins": coins_val})
    lb[tab].sort(key=lambda e: (e["wave"], e["coins"]), reverse=True)
    lb[tab] = lb[tab][:20]
    save_leaderboard(lb)


def draw_leaderboard():
    global leaderboard_close_rect, leaderboard_tab_rects, leaderboard_scroll
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (0, 0))
    pw, ph = 560, 480
    px = WIDTH // 2 - pw // 2
    py = HEIGHT // 2 - ph // 2
    pygame.draw.rect(screen, (10, 10, 30), (px, py, pw, ph), border_radius=12)
    pygame.draw.rect(screen, GOLD, (px, py, pw, ph), 2, border_radius=12)
    title_s = font_lg.render("Leaderboard", True, GOLD)
    screen.blit(title_s, (px + pw // 2 - title_s.get_width() // 2, py + 12))
    leaderboard_tab_rects = {}
    for i, (tid, tlbl) in enumerate([("normal", "Normal"), ("nightmare", "Nightmare"), ("arena", "Arena")]):
        tr = pygame.Rect(px + 14 + i * 120, py + 50, 110, 28)
        col = (0, 110, 0) if leaderboard_tab == tid else (40, 40, 60)
        pygame.draw.rect(screen, col, tr, border_radius=6)
        pygame.draw.rect(screen, GOLD if leaderboard_tab == tid else GRAY, tr, 1, border_radius=6)
        ts2 = font_sm.render(tlbl, True, WHITE)
        screen.blit(ts2, (tr.x + tr.width // 2 - ts2.get_width() // 2, tr.y + 6))
        leaderboard_tab_rects[tid] = tr
    hx = px + 14
    hy = py + 90
    for lbl3, lx3 in [("#", hx), ("Username", hx + 34), ("Wave", hx + 210), ("Coins", hx + 300)]:
        screen.blit(font_sm.render(lbl3, True, GOLD), (lx3, hy))
    pygame.draw.line(screen, GRAY, (px + 14, hy + 22), (px + pw - 14, hy + 22), 1)
    lb = load_leaderboard()
    entries = lb.get(leaderboard_tab, [])
    clip_h = ph - 130
    clip_surf = pygame.Surface((pw - 28, clip_h), pygame.SRCALPHA)
    clip_surf.fill((0, 0, 0, 0))
    for i, entry in enumerate(entries):
        ey = i * 32 - leaderboard_scroll
        if ey < -32 or ey > clip_h:
            continue
        row_col = (220, 200, 80) if i == 0 else ((200, 200, 200) if i == 1 else ((180, 130, 60) if i == 2 else WHITE))
        clip_surf.blit(font_sm.render(f"{i + 1}.", True, row_col), (0, ey))
        clip_surf.blit(font_sm.render(entry.get("username", "?"), True, row_col), (34, ey))
        clip_surf.blit(font.render(str(entry.get("wave", 0)), True, (120, 220, 255)), (210, ey))
        clip_surf.blit(font_sm.render(f"{entry.get('coins', 0):,}", True, GOLD), (300, ey))
    screen.blit(clip_surf, (px + 14, py + 120))
    if not entries:
        no_s = font.render("No scores yet!", True, GRAY)
        screen.blit(no_s, (px + pw // 2 - no_s.get_width() // 2, py + ph // 2))
    leaderboard_close_rect = pygame.Rect(px + pw - 36, py + 8, 28, 28)
    pygame.draw.rect(screen, (160, 0, 0), leaderboard_close_rect, border_radius=5)
    screen.blit(font.render("X", True, WHITE), (leaderboard_close_rect.x + 7, leaderboard_close_rect.y + 4))


# ── Admin command console ─────────────────────────────────────────────────────
def draw_cmd_console():
    global cmd_console_inp_rect
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 185))
    screen.blit(overlay, (0, 0))
    pw, ph = 660, 330
    px = WIDTH // 2 - pw // 2
    py = HEIGHT // 2 - ph // 2
    pygame.draw.rect(screen, (10, 10, 30), (px, py, pw, ph), border_radius=10)
    pygame.draw.rect(screen, GOLD, (px, py, pw, ph), 2, border_radius=10)
    title_s = font.render("Admin Command Console", True, GOLD)
    screen.blit(title_s, (px + pw // 2 - title_s.get_width() // 2, py + 10))
    if cmd_console_help_shown:
        cmds = [
            ("set wave <n>",                (160, 220, 160)),
            ("set path <name>",             (160, 220, 160)),
            ("set coins <amount/infinite>", (160, 220, 160)),
            ("set health <amount/infinite>", (160, 220, 160)),
            ("set upgrade <tower/all> <n>", (160, 220, 160)),
            ("admin_panel",                 (200, 200, 255)),
            ("create enemy",                (255, 200, 160)),
            ("create boss",                 (255, 160, 160)),
            ("list_custom",                 (180, 220, 255)),
            ("del_custom <name>",           (255, 160, 160)),
        ]
        col_w = pw // 2 - 20
        for i, (cmd_txt, col3) in enumerate(cmds):
            cx3 = px + 14 + (i % 2) * (col_w + 14)
            cy3 = py + 40 + (i // 2) * 22
            screen.blit(font_tiny.render(cmd_txt, True, col3), (cx3, cy3))
    else:
        hint_s = font_sm.render("Type  help  to show available commands.", True, (180, 180, 180))
        screen.blit(hint_s, (px + pw // 2 - hint_s.get_width() // 2, py + 50))
    inp = pygame.Rect(px + 14, py + ph - 95, pw - 110, 36)
    pygame.draw.rect(screen, (30, 30, 60), inp)
    pygame.draw.rect(screen, GOLD, inp, 1)
    screen.blit(font.render((cmd_console_str or "") + "|", True, WHITE), (inp.x + 8, inp.y + 8))
    cmd_console_inp_rect = inp
    sub_r = pygame.Rect(px + pw - 90, py + ph - 95, 76, 36)
    pygame.draw.rect(screen, (0, 140, 0), sub_r, border_radius=6)
    screen.blit(font.render("Run", True, WHITE), (sub_r.x + 18, sub_r.y + 8))
    if cmd_console_output:
        out_col = (180, 255, 180) if not cmd_console_output.startswith("Error") and not cmd_console_output.startswith("Unknown") else (255, 140, 140)
        screen.blit(font_sm.render(cmd_console_output[:90], True, out_col), (px + 14, py + ph - 50))
    close_r = pygame.Rect(px + pw - 28, py + 6, 22, 22)
    pygame.draw.rect(screen, (160, 0, 0), close_r, border_radius=4)
    screen.blit(font_sm.render("X", True, WHITE), (close_r.x + 5, close_r.y + 3))
    return inp, sub_r, close_r


def process_command(cmd_str_raw):
    global wave_number, coins, hp, selected_path_id, path, cmd_console_output
    global cmd_console_open, cmd_console_help_shown, state, create_entity_open, create_entity_type
    global arena_wave, arena_coins
    global blood_storm_active, blood_storm_splash_timer, blood_storm_info_open
    global shadow_storm_active, shadow_storm_splash_timer, shadow_storm_info_open
    global enemies_spawned, enemies_to_spawn, wave_active
    global arena_enemies_spawned, arena_enemies_to_spawn, arena_wave_active
    parts = cmd_str_raw.strip().split()
    if not parts:
        cmd_console_output = "No command entered."
        return
    verb = parts[0].lower()
    if verb == "set" and len(parts) >= 3:
        target = parts[1].lower()
        val_str = parts[2].lower()
        if target == "wave":
            try:
                n = int(parts[2])
                wave_number = n
                # Clear any in-progress wave so the new wave can be started cleanly
                enemies.clear()
                enemies_spawned = 0
                enemies_to_spawn = 0
                wave_active = False
                if state == "ARENA":
                    arena_wave = n
                    arena_enemies.clear()
                    arena_enemies_spawned = 0
                    arena_enemies_to_spawn = 0
                    arena_wave_active = False
                # Activate storms when jumping past their threshold
                if n >= 35 and not blood_storm_active:
                    blood_storm_active = True
                    blood_storm_splash_timer = 300
                    blood_storm_info_open = True
                if n >= 75 and not shadow_storm_active:
                    shadow_storm_active = True
                    shadow_storm_splash_timer = 300
                    shadow_storm_info_open = True
                cmd_console_output = f"Wave set to {n}."
            except ValueError:
                cmd_console_output = "Error: invalid wave number."
        elif target == "path":
            name_q = " ".join(parts[2:]).lower()
            pdata = next((p for p in PATHS if p["name"].lower() == name_q or p["id"].lower() == name_q), None)
            if pdata:
                selected_path_id = pdata["id"]
                path[:] = list(pdata["points"])
                cmd_console_output = f"Path set to {pdata['name']}."
            else:
                cmd_console_output = "Unknown path. Options: " + ", ".join(p["name"] for p in PATHS)
        elif target == "coins":
            if val_str == "infinite":
                coins = 999999999
                arena_coins = 999999999
                cmd_console_output = "Coins set to infinite."
            else:
                try:
                    n = int(parts[2])
                    coins = n
                    arena_coins = n
                    cmd_console_output = f"Coins set to {n:,}."
                except ValueError:
                    cmd_console_output = "Error: invalid coins amount."
        elif target == "health":
            if val_str == "infinite":
                hp = 999999999
                cmd_console_output = "Health set to infinite."
            else:
                try:
                    n = int(parts[2])
                    hp = n
                    cmd_console_output = f"Health set to {n}."
                except ValueError:
                    cmd_console_output = "Error: invalid health amount."
        elif target == "upgrade":
            tname = parts[2].lower() if len(parts) >= 3 else "all"
            try:
                amount = int(parts[3]) if len(parts) >= 4 else 1
            except ValueError:
                amount = 1
            t_list = towers if state == "GAME" else arena_towers
            upgraded = 0
            for t in t_list:
                if tname == "all" or t.type.lower().replace(" ", "_") == tname.replace(" ", "_"):
                    for _ in range(amount):
                        if t.level < t.max_level:
                            t.upgrade()
                    upgraded += 1
            cmd_console_output = f"Upgraded {upgraded} tower(s) by up to {amount} level(s)."
        else:
            cmd_console_output = f"Unknown set target: {parts[1]}."
    elif verb == "admin_panel":
        cmd_console_open = False
        if logged_in_user and logged_in_user in users:
            users[logged_in_user]["coins"] = coins
            save_users()
        state = "ADMIN_PANEL"
        cmd_console_output = ""
    elif verb == "create" and len(parts) >= 2 and parts[1].lower() in ("enemy", "boss"):
        create_entity_type = parts[1].lower()
        create_entity_open = True
        cmd_console_open = False
        cmd_console_output = ""
    elif verb == "help":
        cmd_console_help_shown = True
        cmd_console_output = "Commands revealed above."
    elif verb == "del_custom" and len(parts) >= 2:
        name_q = " ".join(parts[1:]).lower()
        before = len(custom_enemies) + len(custom_bosses)
        custom_enemies[:] = [c for c in custom_enemies if c.get("name", "").lower() != name_q]
        custom_bosses[:] = [c for c in custom_bosses if c.get("name", "").lower() != name_q]
        after = len(custom_enemies) + len(custom_bosses)
        if before != after:
            save_custom_creatures()
            cmd_console_output = f"Deleted custom creature '{name_q}'."
        else:
            cmd_console_output = f"No custom creature named '{name_q}'."
    elif verb == "list_custom":
        names = [c["name"] for c in custom_enemies] + [c["name"] + " (boss)" for c in custom_bosses]
        cmd_console_output = "Custom: " + (", ".join(names) if names else "(none)")
    else:
        cmd_console_output = f"Unknown command: {verb}. Type help to see commands."


# ── Create entity (custom enemy/boss) menu ────────────────────────────────────
_CE_FIELD_ORDER = ["name", "desc", "hp", "dmg", "spd", "reward", "wave"]
_CE_COLOR_FIELDS = ["r", "g", "b"]
_CE_LABELS = {
    "name": "Name", "desc": "Description", "hp": "HP",
    "dmg": "Damage", "spd": "Speed (0.5–5.0)", "reward": "Reward coins",
    "wave": "Intro wave", "r": "Color R", "g": "Color G", "b": "Color B",
}
_CE_SHAPES = ["circle", "square", "diamond", "triangle", "pentagon", "star", "hexagon"]
_ABILITY_NAMES = ["(none)"] + [a["name"] for a in ALL_ABILITIES]


def draw_create_entity_menu():
    global create_entity_active_field, create_entity_fields, create_entity_shape
    global create_entity_shape_idx, create_entity_ability, create_entity_ab_params
    global create_entity_help_open, create_entity_help_scroll
    screen.fill((10, 10, 25))
    pygame.draw.rect(screen, GOLD, (0, 0, WIDTH, HEIGHT), 3)
    title_txt = f"Create Custom {'Boss' if create_entity_type == 'boss' else 'Enemy'}"
    ts = font_lg.render(title_txt, True, GOLD)
    screen.blit(ts, (WIDTH // 2 - ts.get_width() // 2, 10))
    back_r = pygame.Rect(10, 10, 80, 30)
    pygame.draw.rect(screen, (160, 0, 0), back_r, border_radius=6)
    screen.blit(font_sm.render("< Back", True, WHITE), (back_r.x + 8, back_r.y + 6))
    help_r = pygame.Rect(100, 10, 140, 30)
    pygame.draw.rect(screen, (50, 80, 160), help_r, border_radius=6)
    screen.blit(font_sm.render("Help: Abilities", True, WHITE), (help_r.x + 8, help_r.y + 6))
    field_rects = {}
    col_x = 30
    for i, fkey in enumerate(_CE_FIELD_ORDER):
        fy = 50 + i * 46
        col3 = GOLD if create_entity_active_field == fkey else (180, 180, 220)
        screen.blit(font_tiny.render(_CE_LABELS[fkey] + ":", True, col3), (col_x, fy))
        fr = pygame.Rect(col_x, fy + 16, 230, 26)
        pygame.draw.rect(screen, (30, 30, 60), fr)
        pygame.draw.rect(screen, GOLD if create_entity_active_field == fkey else (80, 80, 120), fr, 1)
        val = create_entity_fields.get(fkey, "")
        screen.blit(font_sm.render(val + ("|" if create_entity_active_field == fkey else ""), True, WHITE), (fr.x + 5, fr.y + 4))
        field_rects[fkey] = fr
    col_x2 = WIDTH // 2 + 10
    for i, fkey in enumerate(_CE_COLOR_FIELDS):
        fy2 = 50 + i * 46
        col3 = GOLD if create_entity_active_field == fkey else (180, 180, 220)
        screen.blit(font_tiny.render(_CE_LABELS[fkey] + ":", True, col3), (col_x2, fy2))
        fr2 = pygame.Rect(col_x2, fy2 + 16, 80, 26)
        pygame.draw.rect(screen, (30, 30, 60), fr2)
        pygame.draw.rect(screen, GOLD if create_entity_active_field == fkey else (80, 80, 120), fr2, 1)
        val = create_entity_fields.get(fkey, "")
        screen.blit(font_sm.render(val + ("|" if create_entity_active_field == fkey else ""), True, WHITE), (fr2.x + 5, fr2.y + 4))
        field_rects[fkey] = fr2
    try:
        pr_col = (
            max(0, min(255, int(create_entity_fields.get("r", "180")))),
            max(0, min(255, int(create_entity_fields.get("g", "60")))),
            max(0, min(255, int(create_entity_fields.get("b", "60")))),
        )
    except Exception:
        pr_col = (180, 60, 60)
    preview_cx = col_x2 + 120
    preview_cy = 100
    pygame.draw.circle(screen, pr_col, (preview_cx, preview_cy), 22)
    pygame.draw.circle(screen, WHITE, (preview_cx, preview_cy), 22, 1)
    screen.blit(font_tiny.render("Color", True, GRAY), (preview_cx - 15, preview_cy + 25))
    shape_y = 195
    screen.blit(font_tiny.render("Shape:", True, (180, 180, 220)), (col_x2, shape_y))
    prev_shape_r = pygame.Rect(col_x2, shape_y + 16, 26, 26)
    pygame.draw.rect(screen, (60, 60, 120), prev_shape_r, border_radius=4)
    screen.blit(font_sm.render("<", True, WHITE), (prev_shape_r.x + 7, prev_shape_r.y + 4))
    next_shape_r = pygame.Rect(col_x2 + 160, shape_y + 16, 26, 26)
    pygame.draw.rect(screen, (60, 60, 120), next_shape_r, border_radius=4)
    screen.blit(font_sm.render(">", True, WHITE), (next_shape_r.x + 7, next_shape_r.y + 4))
    shape_display_r = pygame.Rect(col_x2 + 30, shape_y + 16, 126, 26)
    pygame.draw.rect(screen, (30, 30, 60), shape_display_r)
    pygame.draw.rect(screen, GRAY, shape_display_r, 1)
    screen.blit(font_sm.render(create_entity_shape, True, WHITE), (shape_display_r.x + 6, shape_display_r.y + 4))
    draw_shape(screen, pr_col, col_x2 + 210, shape_y + 28, 22, create_entity_shape, WHITE, 2)
    screen.blit(font_tiny.render("Entity", True, GRAY), (col_x2 + 196, shape_y + 54))
    ab_y = 240
    screen.blit(font_tiny.render("Ability (optional):", True, (180, 180, 220)), (col_x2, ab_y))
    ab_idx = _ABILITY_NAMES.index(create_entity_ability) if create_entity_ability in _ABILITY_NAMES else 0
    ab_prev_r = pygame.Rect(col_x2, ab_y + 16, 26, 26)
    ab_next_r = pygame.Rect(col_x2 + 174, ab_y + 16, 26, 26)
    pygame.draw.rect(screen, (60, 60, 120), ab_prev_r, border_radius=4)
    pygame.draw.rect(screen, (60, 60, 120), ab_next_r, border_radius=4)
    screen.blit(font_sm.render("<", True, WHITE), (ab_prev_r.x + 7, ab_prev_r.y + 4))
    screen.blit(font_sm.render(">", True, WHITE), (ab_next_r.x + 7, ab_next_r.y + 4))
    ab_display_r = pygame.Rect(col_x2 + 30, ab_y + 16, 140, 26)
    pygame.draw.rect(screen, (30, 30, 60), ab_display_r)
    pygame.draw.rect(screen, GRAY, ab_display_r, 1)
    ab_label = create_entity_ability if create_entity_ability else "(none)"
    ab_s = font_tiny.render(ab_label, True, WHITE)
    screen.blit(ab_s, (ab_display_r.x + 4, ab_display_r.y + 6))
    ab_def = next((a for a in ALL_ABILITIES if a["name"] == create_entity_ability), None)
    ab_param_rects = {}
    if ab_def and ab_def.get("params"):
        for j, param in enumerate(ab_def["params"]):
            py3 = ab_y + 52 + j * 46
            pk = "ab_" + param["key"]
            col3 = GOLD if create_entity_active_field == pk else (180, 180, 220)
            screen.blit(font_tiny.render(param["label"] + ":", True, col3), (col_x2, py3))
            fr3 = pygame.Rect(col_x2, py3 + 16, 200, 26)
            pygame.draw.rect(screen, (30, 30, 60), fr3)
            pygame.draw.rect(screen, GOLD if create_entity_active_field == pk else (80, 80, 120), fr3, 1)
            val3 = create_entity_ab_params.get(param["key"], param.get("default", ""))
            screen.blit(font_sm.render(val3 + ("|" if create_entity_active_field == pk else ""), True, WHITE), (fr3.x + 5, fr3.y + 4))
            ab_param_rects[pk] = (fr3, param)
        if create_entity_ability in ("Shielder", "Vengeance"):
            vis_key = "shield_radius" if create_entity_ability == "Shielder" else "swipe_range"
            try:
                vis_r2 = max(10, min(150, int(create_entity_ab_params.get(vis_key, "40"))))
            except Exception:
                vis_r2 = 40
            vis_cx = col_x2 + 240
            vis_cy = ab_y + 120
            vis_col3 = (80, 140, 255) if create_entity_ability == "Shielder" else (255, 150, 80)
            pygame.draw.circle(screen, vis_col3, (vis_cx, vis_cy), vis_r2, 2)
            draw_shape(screen, pr_col, vis_cx, vis_cy, 14, create_entity_shape, WHITE, 2)
            screen.blit(font_tiny.render(f"r={vis_r2}px", True, GRAY), (vis_cx - 20, vis_cy + vis_r2 + 4))
    all_filled = all(create_entity_fields.get(k, "").strip() for k in _CE_FIELD_ORDER)
    sub_r2 = pygame.Rect(WIDTH - 170, HEIGHT - 46, 160, 34)
    sub_col2 = (0, 140, 0) if all_filled else (60, 60, 60)
    pygame.draw.rect(screen, sub_col2, sub_r2, border_radius=8)
    sub_txt = f"Create {'Boss' if create_entity_type == 'boss' else 'Enemy'}"
    sub_s = font.render(sub_txt, True, WHITE)
    screen.blit(sub_s, (sub_r2.x + sub_r2.width // 2 - sub_s.get_width() // 2, sub_r2.y + 7))
    if not all_filled:
        screen.blit(font_tiny.render("Fill all fields!", True, (255, 100, 100)), (WIDTH - 175, HEIGHT - 54))
    help_close_r = None
    up_r3 = None
    dn_r3 = None
    if create_entity_help_open:
        hp2, hh2 = 540, 440
        hx2 = WIDTH // 2 - hp2 // 2
        hy2 = HEIGHT // 2 - hh2 // 2
        pygame.draw.rect(screen, (10, 10, 30), (hx2, hy2, hp2, hh2), border_radius=10)
        pygame.draw.rect(screen, (100, 100, 255), (hx2, hy2, hp2, hh2), 2, border_radius=10)
        ht_s = font.render("All Abilities", True, (200, 200, 255))
        screen.blit(ht_s, (hx2 + hp2 // 2 - ht_s.get_width() // 2, hy2 + 8))
        help_close_r = pygame.Rect(hx2 + hp2 - 30, hy2 + 6, 24, 24)
        pygame.draw.rect(screen, (160, 0, 0), help_close_r, border_radius=4)
        screen.blit(font_sm.render("X", True, WHITE), (help_close_r.x + 6, help_close_r.y + 3))
        up_r3 = pygame.Rect(hx2 + hp2 - 24, hy2 + 36, 18, 18)
        dn_r3 = pygame.Rect(hx2 + hp2 - 24, hy2 + hh2 - 28, 18, 18)
        pygame.draw.rect(screen, (60, 60, 120), up_r3, border_radius=3)
        pygame.draw.rect(screen, (60, 60, 120), dn_r3, border_radius=3)
        screen.blit(font_tiny.render("▲", True, WHITE), (up_r3.x + 2, up_r3.y + 2))
        screen.blit(font_tiny.render("▼", True, WHITE), (dn_r3.x + 2, dn_r3.y + 2))
        list_clip = pygame.Surface((hp2 - 28, hh2 - 66), pygame.SRCALPHA)
        list_clip.fill((0, 0, 0, 0))
        for j2, ab in enumerate(ALL_ABILITIES):
            item_y = j2 * 56 - create_entity_help_scroll
            if item_y < -56 or item_y > hh2 - 66:
                continue
            list_clip.blit(font_sm.render(ab["name"], True, (200, 220, 255)), (0, item_y))
            list_clip.blit(font_tiny.render(ab["desc"][:80], True, (160, 160, 185)), (0, item_y + 18))
            if ab.get("params"):
                p_lbl = "Params: " + ", ".join(p["label"] for p in ab["params"])
                list_clip.blit(font_tiny.render(p_lbl[:85], True, (120, 200, 120)), (0, item_y + 34))
            pygame.draw.line(list_clip, (50, 50, 80), (0, item_y + 52), (hp2 - 28, item_y + 52))
        screen.blit(list_clip, (hx2 + 14, hy2 + 48))
    return back_r, help_r, field_rects, shape_display_r, prev_shape_r, next_shape_r, ab_prev_r, ab_next_r, ab_param_rects, all_filled, sub_r2, help_close_r, up_r3, dn_r3


def submit_custom_entity():
    global create_entity_open, custom_enemies, custom_bosses
    try:
        defn = {
            "name": create_entity_fields.get("name", "Custom"),
            "desc": create_entity_fields.get("desc", ""),
            "color": (
                max(0, min(255, int(create_entity_fields.get("r", "180")))),
                max(0, min(255, int(create_entity_fields.get("g", "60")))),
                max(0, min(255, int(create_entity_fields.get("b", "60")))),
            ),
            "hp": int(create_entity_fields.get("hp", "100")),
            "dmg": float(create_entity_fields.get("dmg", "2")),
            "spd": float(create_entity_fields.get("spd", "1.5")),
            "reward": int(create_entity_fields.get("reward", "20")),
            "wave": int(create_entity_fields.get("wave", "1")),
            "shape": create_entity_shape,
            "ability": create_entity_ability,
            "ab_params": dict(create_entity_ab_params),
            "is_boss": create_entity_type == "boss",
        }
        if create_entity_type == "boss":
            custom_bosses.append(defn)
        else:
            custom_enemies.append(defn)
        save_custom_creatures()
        create_entity_open = False
    except Exception:
        pass


def spawn_custom_enemy_from_def(defn):
    e = Enemy(
        defn["color"], defn["dmg"], defn["spd"], defn["reward"], defn["hp"],
        radius=22 if defn["is_boss"] else 13,
        type_id="custom_" + defn["name"].lower().replace(" ", "_"),
        shape=defn["shape"],
    )
    e.is_boss = defn["is_boss"]
    ability = defn.get("ability", "")
    params = defn.get("ab_params", {})
    if ability == "Regeneration":
        try:
            e.regen_rate = float(params.get("regen_rate", 3))
        except Exception:
            e.regen_rate = 3
    elif ability == "Vampiric Dash":
        e.is_vampire = True
        e.vampire_phase = 0
        e.vampire_timer = 0
    elif ability == "Tower Raider":
        e.is_tower_raider = True
        e.targets_towers = True
    elif ability == "Distractor":
        e.is_distractor = True
    elif ability == "Rebirth":
        e.revived = False
        e._has_rebirth = True
    elif ability == "Spectral":
        e._is_spectral = True
    elif ability == "Berserker":
        e._is_berserker = True
    elif ability == "Fortified":
        e._is_fortified = True
    elif ability == "Teleportation":
        e._teleport_timer = 0
    return e


# ── Game state init ───────────────────────────────────────────────────────────
load_users()
load_custom_creatures()

username_input = InputBox(WIDTH // 2 - 100, 150, 200, 40)
password_input = InputBox(WIDTH // 2 - 100, 210, 200, 40, is_password=True)

user_rect = pygame.Rect(0, 0, 0, 0)
logout_rect_obj = pygame.Rect(0, 0, 0, 0)
admin_panel_rect_obj = pygame.Rect(0, 0, 0, 0)
back_button_rect = pygame.Rect(0, 0, 0, 0)
shop_button_rect = pygame.Rect(0, 0, 0, 0)
info_button_rect = pygame.Rect(0, 0, 0, 0)
nightmare_button_rect = pygame.Rect(0, 0, 0, 0)
start_wave_rect = pygame.Rect(0, 0, 0, 0)
twox_button_rect = pygame.Rect(0, 0, 0, 0)
blood_storm_info_rect = pygame.Rect(0, 0, 0, 0)
admin_back_rect = pygame.Rect(0, 0, 0, 0)
admin_logout_rect = pygame.Rect(0, 0, 0, 0)

running = True


def do_logout():
    global logged_in_user, is_admin, logout_menu_open, state
    global coins, hp, wave_number, wave_active, enemies_spawned, enemies_to_spawn
    global placing_tower, placing_wall, placing_bomb, selected_tower, selected_tower_object
    global shop_open, shop_x, walls, bombs, walls_placed_count, bombs_placed_count
    global blood_storm_active, blood_storm_splash_timer, blood_storm_info_open
    global nightmare_locked, leaderboard_open, cmd_console_open, create_entity_open
    nightmare_locked = False
    leaderboard_open = False
    cmd_console_open = False
    create_entity_open = False
    if logged_in_user and logged_in_user in users:
        users[logged_in_user]["coins"] = coins
        users[logged_in_user]["owned_paths"] = list(owned_path_ids)
        users[logged_in_user]["selected_path"] = selected_path_id
        save_users()
    logged_in_user = None
    is_admin = False
    logout_menu_open = False
    reset_bestiary()
    state = "MENU"
    coins = 400
    hp = 20
    wave_number = 1
    wave_active = False
    enemies.clear()
    towers.clear()
    coins_list.clear()
    walls.clear()
    bombs.clear()
    walls_placed_count = 0
    bombs_placed_count = 0
    blood_storm_active = False
    blood_storm_splash_timer = 0
    blood_storm_info_open = False
    shadow_storm_active = False
    shadow_storm_splash_timer = 0
    shadow_storm_info_open = False
    enemies_spawned = 0
    enemies_to_spawn = 0
    placing_tower = False
    placing_wall = False
    placing_bomb = False
    selected_tower = None
    selected_tower_object = None
    shop_open = False
    shop_x = -SHOP_W
    nightmare_mode = False


# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║                       A R E N A   M O D E                                 ║
# ╚═══════════════════════════════════════════════════════════════════════════╝

# ── Arena globals ─────────────────────────────────────────────────────────────
arena_cam_x = 0.0
arena_cam_y = 0.0
arena_player_hp = 100
arena_player_max_hp = 100
arena_coins = 0
arena_wave = 1
arena_wave_active = False
arena_enemies_spawned = 0
arena_enemies_to_spawn = 0
arena_enemy_timer = 0
arena_enemies = []
arena_towers = []
arena_walls = []
arena_p_bullets = []
arena_shop_open = False
arena_shop_x = -SHOP_W
arena_shop_tab = "towers"
arena_placing_tower = None
arena_placing_wall = False
arena_wall_rot = 0
arena_selected_tower_obj = None
arena_selected_wall_obj = None
arena_wall_upgrade_rect = None
arena_wall_sell_rect = None
arena_wall_close_rect = None
arena_spawn_wx = 0.0
arena_spawn_wy = -480.0
arena_player_iframes = 0  # invincibility frames after being hit
ARENA_SPAWN_R = 28
ARENA_BULLET_CD = 10  # spacebar hold fire cooldown
arena_shoot_cd = 0
ARENA_GUNS = [
    {"name": "Starter Gun", "cost": 0, "damage": 30, "cooldown": 12, "shots": 1, "spread": 0, "auto": False, "color": (255, 230, 0)},
    {"name": "Iron Gun", "cost": 12000, "damage": 55, "cooldown": 10, "shots": 1, "spread": 0, "auto": False, "color": (255, 180, 60)},
    {"name": "Repeater Gun", "cost": 75000, "damage": 95, "cooldown": 7, "shots": 3, "spread": 12, "auto": True, "color": (255, 80, 40)},
    {"name": "Frost Gun", "cost": 150000, "damage": 140, "cooldown": 8, "shots": 2, "spread": 8, "auto": True, "color": (120, 220, 255)},
]
arena_gun_level = 0
arena_wave_start_rect = pygame.Rect(0, 0, 0, 0)
arena_back_rect = pygame.Rect(0, 0, 0, 0)
arena_shop_btn_rect = pygame.Rect(0, 0, 0, 0)
bestiary_rect = pygame.Rect(0, 0, 0, 0)
arena_nightmare_rect = pygame.Rect(0, 0, 0, 0)
arena_ranges_rect = pygame.Rect(0, 0, 0, 0)
arena_keys = {pygame.K_w: False, pygame.K_s: False, pygame.K_a: False, pygame.K_d: False}
ARENA_PLAYER_SPEED = 3.0


def arena_fire_player_weapon():
    global arena_shoot_cd
    if arena_shoot_cd > 0 or arena_player_hp <= 0:
        return
    mx_s, my_s = pygame.mouse.get_pos()
    dx_b = mx_s - WIDTH // 2
    dy_b = my_s - HEIGHT // 2
    if not (dx_b or dy_b):
        return
    gun = ARENA_GUNS[arena_gun_level]
    base_angle = math.atan2(dy_b, dx_b)
    shots = gun["shots"]
    spread = math.radians(gun["spread"])
    for i in range(shots):
        if shots == 1:
            ang = base_angle
        else:
            offset = (i - (shots - 1) / 2) * spread
            ang = base_angle + offset
        arena_p_bullets.append(ArenaBullet(arena_cam_x, arena_cam_y, math.cos(ang), math.sin(ang), damage=gun["damage"], color=gun["color"]))
    arena_shoot_cd = gun["cooldown"]


def a2s(wx, wy):
    """World → screen for arena."""
    return int(wx - arena_cam_x + WIDTH // 2), int(wy - arena_cam_y + HEIGHT // 2)


def s2a(sx, sy):
    """Screen → world for arena."""
    return sx - WIDTH // 2 + arena_cam_x, sy - HEIGHT // 2 + arena_cam_y


class ArenaBullet:
    def __init__(self, wx, wy, dx, dy, spd=9, damage=30, color=(255, 230, 0)):
        self.wx = float(wx)
        self.wy = float(wy)
        d = math.hypot(dx, dy) or 1
        self.vx = dx / d * spd
        self.vy = dy / d * spd
        self.damage = damage
        self.color = color
        self.alive = True
        self.dist = 0
        self.max_dist = 650

    def update(self):
        tick = 2 if speed_2x else 1
        self.wx += self.vx * tick
        self.wy += self.vy * tick
        self.dist += math.hypot(self.vx, self.vy)
        if self.dist > self.max_dist:
            self.alive = False
            return
        for e in arena_enemies:
            if e.alive and math.hypot(e.wx - self.wx, e.wy - self.wy) < e.radius:
                if not getattr(e, "phase_immune", False):
                    dr = getattr(e, "damage_reduction", 0.0)
                    e.health -= max(1, int(self.damage * (1.0 - dr)))
                    if e.health <= 0:
                        e.alive = False
                self.alive = False
                return

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        pygame.draw.circle(screen, self.color, (sx, sy), 5)
        pygame.draw.circle(screen, WHITE, (sx, sy), 5, 1)


class ArenaTowerBullet:
    """Bullet fired by an ArenaTower — flies straight, hits first enemy in path."""

    HIT_R = 14  # collision radius against enemies
    MAX_D = 900  # max travel distance before despawn

    def __init__(self, wx, wy, target, damage, color=YELLOW, splash=False, owner=None):
        self.wx = float(wx)
        self.wy = float(wy)
        self.damage = damage
        self.color = color
        self.splash = splash
        self.splash_r = 80 if splash else 0
        self.alive = True
        self.owner = owner  # tower that fired this bullet (for kill tracking)
        self.dist = 0.0
        self.speed = 10
        dx = target.wx - wx
        dy = target.wy - wy
        d = math.hypot(dx, dy) or 1
        self.vx = dx / d * self.speed
        self.vy = dy / d * self.speed

    def update(self):
        tick = 2 if speed_2x else 1
        self.wx += self.vx * tick
        self.wy += self.vy * tick
        self.dist += self.speed * tick
        if self.dist > self.MAX_D:
            self.alive = False
            return
        # Hit detection: check all live enemies
        for _e in arena_enemies:
            if not _e.alive or _e.health <= 0:
                continue
            if getattr(_e, "visible_to", "all") == "sniper_only":
                continue
            if math.hypot(_e.wx - self.wx, _e.wy - self.wy) < self.HIT_R + _e.radius:
                if not getattr(_e, "phase_immune", False):
                    if self.splash:
                        for _se in arena_enemies:
                            if _se.alive and math.hypot(_se.wx - self.wx, _se.wy - self.wy) < self.splash_r:
                                _dr2 = getattr(_se, "damage_reduction", 0.0)
                                _was_alive_s = _se.health > 0
                                _se.health -= max(1, int(self.damage * (1.0 - _dr2)))
                                if _se.health <= 0:
                                    _se.alive = False
                                    if _was_alive_s and self.owner is not None:
                                        self.owner.kills += 1
                    else:
                        _dr = getattr(_e, "damage_reduction", 0.0)
                        _was_alive_e = _e.health > 0
                        _e.health -= max(1, int(self.damage * (1.0 - _dr)))
                        if _e.health <= 0:
                            _e.alive = False
                            if _was_alive_e and self.owner is not None:
                                self.owner.kills += 1
                self.alive = False
                return

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        if self.splash:
            pygame.draw.circle(screen, self.color, (sx, sy), 7)
            pygame.draw.circle(screen, WHITE, (sx, sy), 7, 1)
        else:
            pygame.draw.circle(screen, self.color, (sx, sy), 5)
            pygame.draw.circle(screen, WHITE, (sx, sy), 5, 1)


class ArenaGoblin:
    """Goblin minion in arena — seeks and attacks arena enemies."""

    def __init__(self, wx, wy, tier=0):
        self.wx, self.wy = float(wx), float(wy)
        self.tier = tier
        _stats = [(100, 30, 1.5), (150, 50, 3.0), (220, 80, 4.5), (400, 120, 5.0), (600, 200, 5.5), (1200, 400, 6.5)]
        t = min(tier, len(_stats) - 1)
        self.max_health = _stats[t][0]
        self.health = self.max_health
        self.attack_damage = _stats[t][1]
        self.speed = _stats[t][2]
        self.color = GOBLIN_COLORS[t]
        self.target = None
        self.attack_range = 40
        self.attack_cd = 1.0
        self.last_atk = time.time()
        self.alive = True
        self.parent_hut = None  # Goblin Hut that spawned us (for kill tracking)

    def update(self, enemies):
        if not enemies:
            return
        eff = self.speed * (2 if speed_2x else 1)
        live = [e for e in enemies if e.alive and e.health > 0]
        raiders = [e for e in live if e.is_tower_raider]
        pool = raiders if raiders else live
        if not pool:
            return
        self.target = min(pool, key=lambda e: math.hypot(e.wx - self.wx, e.wy - self.wy))
        dx = self.target.wx - self.wx
        dy = self.target.wy - self.wy
        d = math.hypot(dx, dy) or 1
        if d > self.attack_range:
            self.wx += eff * dx / d
            self.wy += eff * dy / d
        else:
            now = time.time()
            if now - self.last_atk > self.attack_cd:
                _wa_ag = self.target.health > 0
                self.target.health -= self.attack_damage
                if self.target.health <= 0:
                    self.target.alive = False
                    if _wa_ag and self.parent_hut is not None:
                        self.parent_hut.kills += 1
                self.last_atk = now
        self.health = min(self.max_health, self.health + 0.05)

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        # Barbarian look (Goblin Hut pristine bronze+): bigger body, brown helmet, sword
        if getattr(self, "barbarian", False):
            pygame.draw.circle(screen, (90, 50, 30), (sx, sy), 11)
            pygame.draw.circle(screen, (40, 20, 10), (sx, sy), 11, 2)
            pygame.draw.rect(screen, (130, 90, 40), (sx - 8, sy - 12, 16, 6))
            pygame.draw.rect(screen, (60, 30, 10), (sx - 8, sy - 12, 16, 6), 1)
            pygame.draw.line(screen, (220, 220, 230), (sx + 6, sy + 2), (sx + 16, sy - 4), 2)
            pygame.draw.line(screen, (140, 80, 30), (sx + 4, sy + 4), (sx + 8, sy), 3)
        else:
            pygame.draw.circle(screen, self.color, (sx, sy), 8)
            pygame.draw.circle(screen, WHITE, (sx, sy), 8, 1)
        bw = 20
        pygame.draw.rect(screen, RED, (sx - 10, sy - 15, bw, 4))
        pygame.draw.rect(screen, GREEN, (sx - 10, sy - 15, int(bw * max(0, self.health / self.max_health)), 4))


class ArenaBuilder:
    """Builder unit in arena — repairs arena towers and walls, throws stones at enemies."""

    def __init__(self, wx, wy, upgraded=False):
        self.wx, self.wy = float(wx), float(wy)
        self.home_wx = float(wx)
        self.home_wy = float(wy)
        self.upgraded = upgraded
        self.health = 150
        self.max_health = 150
        self.speed = 0.8
        self.repair_cd = 100
        self.repair_timer = 0
        self.repair_amt = 3
        self.stone_cd = 140
        self.stone_timer = 0
        self.stone_damage = 12
        self.stone_range = 110
        self.alive = True
        self.parent_hut = None  # Builder Hut that spawned us (for kill tracking)

    def update(self, towers_list, enemies_list):
        spd = self.speed * (2 if speed_2x else 1)
        tick = 2 if speed_2x else 1
        damaged = [t for t in towers_list if t.health < t.max_health]
        damaged_walls = [w for w in arena_walls if w.health < w.max_health] if self.upgraded else []
        if damaged:
            tgt = min(damaged, key=lambda t: math.hypot(t.wx - self.wx, t.wy - self.wy))
            dx, dy = tgt.wx - self.wx, tgt.wy - self.wy
            d = math.hypot(dx, dy) or 1
            if d > 20:
                self.wx += spd * dx / d
                self.wy += spd * dy / d
            else:
                self.repair_timer += tick
                if self.repair_timer >= self.repair_cd:
                    tgt.health = min(tgt.max_health, tgt.health + self.repair_amt)
                    self.repair_timer = 0
        elif damaged_walls:
            tgt = min(damaged_walls, key=lambda w: math.hypot(w.wx - self.wx, w.wy - self.wy))
            dx, dy = tgt.wx - self.wx, tgt.wy - self.wy
            d = math.hypot(dx, dy) or 1
            if d > 20:
                self.wx += spd * dx / d
                self.wy += spd * dy / d
            else:
                self.repair_timer += tick
                if self.repair_timer >= self.repair_cd:
                    tgt.health = min(tgt.max_health, tgt.health + self.repair_amt * 5)
                    self.repair_timer = 0
        else:
            dx, dy = self.home_wx - self.wx, self.home_wy - self.wy
            d = math.hypot(dx, dy) or 1
            if d > 5:
                self.wx += spd * dx / d
                self.wy += spd * dy / d
            else:
                self.health = min(self.max_health, self.health + 0.05 * tick)
        # Throw rocks at nearby enemies
        self.stone_timer += tick
        nearby = [e for e in enemies_list if e.alive and math.hypot(e.wx - self.wx, e.wy - self.wy) < self.stone_range]
        if nearby and self.stone_timer >= self.stone_cd:
            tgt_e = min(nearby, key=lambda e: math.hypot(e.wx - self.wx, e.wy - self.wy))
            _wa_ab = tgt_e.health > 0
            tgt_e.health -= self.stone_damage
            if tgt_e.health <= 0:
                tgt_e.alive = False
                if _wa_ab and self.parent_hut is not None:
                    self.parent_hut.kills += 1
            self.stone_timer = 0

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        col = (220, 190, 70) if self.upgraded else (180, 140, 50)
        pygame.draw.circle(screen, col, (sx, sy), 9)
        pygame.draw.circle(screen, (255, 200, 100), (sx, sy), 9, 2)
        pygame.draw.rect(screen, RED, (sx - 10, sy - 17, 20, 4))
        pygame.draw.rect(screen, GREEN, (sx - 10, sy - 17, int(20 * max(0, self.health / self.max_health)), 4))


class ArenaEnemy:
    """Enemy that seeks the player (or towers if it's a raider)."""

    def __init__(self, color, damage, speed, reward, health, radius=12, type_id="unknown", shape="circle", visible_to="all"):
        self.wx = float(arena_spawn_wx) + random.uniform(-35, 35)
        self.wy = float(arena_spawn_wy) + random.uniform(-35, 35)
        self.color = color
        self.damage = damage
        self.base_speed = speed
        self.speed = speed
        self.reward = reward
        self.health = float(health)
        self.max_health = float(health)
        self.radius = radius
        self.type_id = type_id
        self.shape = shape
        self.visible_to = visible_to
        self.alive = True
        self.is_boss = False
        self.is_tower_raider = type_id == "tower_raider"
        self.targets_towers = self.is_tower_raider or type_id in ("dreadnought", "titan", "bruiser", "vampire", "war_mammoth", "dreadnought")
        self.damage_reduction = 0.6 if type_id == "obsidian_guardian" else 0.45 if type_id == "thornback_beast" else 0.5 if type_id == "doom_knight" else 0.75 if type_id == "dreadnought" else 0.0
        self.phase_timer = 0
        self.phase_immune = False
        self.regen_rate = 12 if type_id == "rune_giant" else 6 if type_id == "celestial_drake" else 8 if type_id == "venom_crawler" else 2 if type_id == "paladin" else 0
        self.war_tremor_timer = 0
        self.storm_timer = 0
        self.plague_dust_timer = 0
        self.void_step_fake = 0
        self.revived = False
        self.atk_cd = 60
        self.atk_timer = 0
        self.bob_offset = 0
        self.bob_dir = 1
        # Shadow hound pounce
        self.pounce_phase = 0
        self.pounce_timer = 0
        self.pounce_target = None
        self.pounce_sx = self.wx
        self.pounce_sy = self.wy
        # Vampire dash
        self.is_vampire = type_id == "vampire"
        self.vampire_phase = 0
        self.vampire_timer = 0
        self.vampire_target = None
        self.vampire_saved_wx = self.wx
        self.vampire_saved_wy = self.wy
        self.vampire_hit_timer = 0
        # Wizard/necromancer summoning
        self.is_wizard = type_id == "wizard"
        self.is_summoner = type_id in ("necromancer", "swarm_queen")
        self.last_minion_time = time.time()
        self.minions = []
        # Fury beast
        self.fury_beast = type_id == "fury_beast"
        # Plague rat / blood spawn / plague moth / abomination
        self.plague_rat = type_id == "plague_rat"
        self.blood_spawn = type_id == "blood_spawn"
        self.plague_moth_flag = type_id == "plague_moth"
        self.abomination = type_id == "abomination"
        # Zigzag
        self.zigzag = type_id == "shadow_dancer"
        # Aura timer (for draw animations)
        self.summon_anim_t = 0

    def update(self):
        global arena_player_hp, arena_player_iframes
        tick = 2 if speed_2x else 1
        _fsm = getattr(self, "frost_slow_mult", 1.0)
        # Frost Laser lvl 3+: zero ability timers while in aura
        if getattr(self, "frost_disabled", False):
            self.war_tremor_timer = 0
            self.storm_timer = 0
            self.plague_dust_timer = 0
            self.last_minion_time = time.time()
            self._abilities_disabled = True
            self.frost_disabled = False
        else:
            self._abilities_disabled = False
        eff = self.base_speed * (2 if speed_2x else 1) * (3 if nightmare_mode else 1) * _fsm
        if pack_howl_frames > 0:
            eff *= 1.5
        if self.type_id == "flame_imp":
            hr = max(0, self.health / max(1, self.max_health))
            eff = self.base_speed * (1.0 + (1.0 - hr) * 1.5) * (2 if speed_2x else 1) * (3 if nightmare_mode else 1) * _fsm
        if self.type_id == "blood_spawn" and self.health < self.max_health * 0.5:
            eff *= 1.6
        if self.regen_rate > 0:
            self.health = min(self.max_health, self.health + self.regen_rate * tick * 0.016)
        # Phase shifter
        if self.type_id in ("phase_shifter", "arcane_orb", "void_reaper"):
            self.phase_timer += tick
            self.phase_immune = 300 <= self.phase_timer < 390
            if self.phase_timer >= 390:
                self.phase_timer = 0
        # Shadow hound pounce
        if self.type_id == "shadow_hound":
            if self.pounce_phase == 1:
                pt = self.pounce_target
                if not pt or pt.health <= 0:
                    self.pounce_phase = 2
                else:
                    pdx = pt.wx - self.wx
                    pdy = pt.wy - self.wy
                    pd = math.hypot(pdx, pdy) or 1
                    if pd < 20:
                        pt.take_damage(80)
                        self.pounce_phase = 2
                    else:
                        self.wx += pdx / pd * eff * 3
                        self.wy += pdy / pd * eff * 3
                return
            elif self.pounce_phase == 2:
                rdx = self.pounce_sx - self.wx
                rdy = self.pounce_sy - self.wy
                rd = math.hypot(rdx, rdy) or 1
                if rd < 10:
                    self.wx = self.pounce_sx
                    self.wy = self.pounce_sy
                    self.pounce_phase = 0
                else:
                    self.wx += rdx / rd * eff * 2.5
                    self.wy += rdy / rd * eff * 2.5
                return
        # ── Vampire dash in arena ────────────────────────────────────────────
        if self.is_vampire:
            self.vampire_timer += tick
            vphase = self.vampire_phase
            if vphase == 0:
                # Normal movement toward player
                tx, ty = arena_cam_x, arena_cam_y
                dx = tx - self.wx
                dy = ty - self.wy
                d = math.hypot(dx, dy) or 1
                if d > 30:
                    self.wx += dx / d * eff
                    self.wy += dy / d * eff
                else:
                    if arena_player_iframes <= 0:
                        arena_player_hp -= self.damage * (3 if nightmare_mode else 1)
                        arena_player_iframes = 30
                # Trigger dash toward nearest tower
                if self.vampire_timer >= 300 and arena_towers:
                    vt = min(arena_towers, key=lambda t: math.hypot(t.wx - self.wx, t.wy - self.wy))
                    self.vampire_target = vt
                    self.vampire_saved_wx = self.wx
                    self.vampire_saved_wy = self.wy
                    self.vampire_phase = 1
                    self.vampire_timer = 0
            elif vphase == 1:
                vt = self.vampire_target
                if not vt or vt.health <= 0:
                    self.vampire_phase = 3
                else:
                    dx = vt.wx - self.wx
                    dy = vt.wy - self.wy
                    d = math.hypot(dx, dy) or 1
                    if d < 24:
                        drain = max(1, int(vt.max_health * 0.20))
                        vt.take_damage(drain)
                        self.health = min(self.max_health, self.health + drain)
                        self.vampire_phase = 2
                        self.vampire_hit_timer = 22
                    else:
                        self.wx += dx / d * eff * 2.5
                        self.wy += dy / d * eff * 2.5
            elif vphase == 2:
                self.vampire_hit_timer -= 1
                if self.vampire_hit_timer <= 0:
                    self.vampire_phase = 3
            elif vphase == 3:
                dx = self.vampire_saved_wx - self.wx
                dy = self.vampire_saved_wy - self.wy
                d = math.hypot(dx, dy) or 1
                if d < 10:
                    self.wx = self.vampire_saved_wx
                    self.wy = self.vampire_saved_wy
                    self.vampire_phase = 0
                else:
                    self.wx += dx / d * eff * 2.0
                    self.wy += dy / d * eff * 2.0
            self.bob_offset += self.bob_dir * 0.5
            if abs(self.bob_offset) > 5:
                self.bob_dir *= -1
            # Wizard/necromancer summon
            if self.is_wizard or self.is_summoner:
                now = time.time()
                if now - self.last_minion_time > (5 / 3 if blood_storm_active else 5) and len(self.minions) < 3:
                    from_x, from_y = self.wx, self.wy
                    m = ArenaEnemy((150, 0, 200), 15, 1.2, 10, 60, radius=8, type_id="minion", shape="circle")
                    m.wx = from_x
                    m.wy = from_y
                    self.minions.append(m)
                    self.last_minion_time = now
                    self.summon_anim_t = 18
            return
        # ── Wizard/Necromancer in arena ────────────────────────────────────────
        if self.is_wizard or self.is_summoner:
            now = time.time()
            if now - self.last_minion_time > (5 / 3 if blood_storm_active else 5) and len(self.minions) < 3:
                m = ArenaEnemy((150, 0, 200), 15, 1.2, 10, 60, radius=8, type_id="minion", shape="circle")
                m.wx = self.wx
                m.wy = self.wy
                self.minions.append(m)
                self.last_minion_time = now
                self.summon_anim_t = 18
        # Update summon anim timer
        if self.summon_anim_t > 0:
            self.summon_anim_t -= tick
        # Update minions toward player
        for _m in self.minions[:]:
            tx_m, ty_m = arena_cam_x, arena_cam_y
            dx_m = tx_m - _m.wx
            dy_m = ty_m - _m.wy
            d_m = math.hypot(dx_m, dy_m) or 1
            _m_eff = _m.base_speed * (2 if speed_2x else 1)
            if d_m > 30:
                _m.wx += dx_m / d_m * _m_eff
                _m.wy += dy_m / d_m * _m_eff
            else:
                if arena_player_iframes <= 0:
                    arena_player_hp -= _m.damage * (3 if nightmare_mode else 1)
                    arena_player_iframes = 30  # ~0.5s damage cooldown so minions don't insta-kill
            if _m.health <= 0:
                self.minions.remove(_m)
        # ── Choose target ─────────────────────────────────────────────────────
        if self.targets_towers and arena_towers:
            nearest_tower = min(arena_towers, key=lambda t: math.hypot(t.wx - self.wx, t.wy - self.wy))
            # Tower raiders are blocked by walls near the target tower
            if self.is_tower_raider and arena_walls:
                blocking = [w for w in arena_walls if w.health > 0 and math.hypot(w.wx - nearest_tower.wx, w.wy - nearest_tower.wy) < 80]
                if blocking:
                    wall_tgt = min(blocking, key=lambda w: math.hypot(w.wx - self.wx, w.wy - self.wy))
                    dx = wall_tgt.wx - self.wx
                    dy = wall_tgt.wy - self.wy
                    d = math.hypot(dx, dy) or 1
                    ar = ArenaWall.R + self.radius
                    if d > ar:
                        self.wx += dx / d * eff
                        self.wy += dy / d * eff
                    else:
                        self.atk_timer += tick
                        if self.atk_timer >= self.atk_cd:
                            self.atk_timer = 0
                            wall_tgt.health -= self.damage * 10
                    self.bob_offset += self.bob_dir * 0.5
                    if abs(self.bob_offset) > 5:
                        self.bob_dir *= -1
                    return
            tt = nearest_tower
            tx, ty = tt.wx, tt.wy
        else:
            tx, ty = arena_cam_x, arena_cam_y  # player world pos
            tt = None
        dx = tx - self.wx
        dy = ty - self.wy
        d = math.hypot(dx, dy) or 1
        attack_range = 20 if (self.targets_towers and tt) else 30
        if d > attack_range:
            self.wx += dx / d * eff
            self.wy += dy / d * eff
        else:
            self.atk_timer += tick
            if self.atk_timer >= self.atk_cd:
                self.atk_timer = 0
                if self.targets_towers and tt:
                    tt.take_damage(self.damage)
                else:
                    if arena_player_iframes <= 0:
                        arena_player_hp -= self.damage * (3 if nightmare_mode else 1)
                        arena_player_iframes = 30
        # War mammoth tremor
        if self.type_id == "war_mammoth":
            self.war_tremor_timer += tick
            if self.war_tremor_timer >= 400:
                self.war_tremor_timer = 0
                for _t in arena_towers:
                    if math.hypot(_t.wx - self.wx, _t.wy - self.wy) < 150:
                        _t.take_damage(30)
        # Storm rider lightning
        if self.type_id in ("storm_rider", "celestial_drake"):
            self.storm_timer += tick
            if self.storm_timer >= 200:
                self.storm_timer = 0
                nt = [_t for _t in arena_towers if math.hypot(_t.wx - self.wx, _t.wy - self.wy) < 200]
                if nt:
                    min(nt, key=lambda _t: math.hypot(_t.wx - self.wx, _t.wy - self.wy)).take_damage(60)
        # Plague moth dust
        if self.type_id == "plague_moth":
            self.plague_dust_timer += tick
            if self.plague_dust_timer >= 200:
                self.plague_dust_timer = 0
                for _e in arena_enemies:
                    if _e is not self and _e.alive and math.hypot(_e.wx - self.wx, _e.wy - self.wy) < 100:
                        _e.health = min(_e.max_health, _e.health + 15)
        if self.type_id == "shield_mender":
            self.plague_dust_timer += tick
            if self.plague_dust_timer >= 160:
                self.plague_dust_timer = 0
                for _e in arena_enemies:
                    if _e is not self and _e.alive and math.hypot(_e.wx - self.wx, _e.wy - self.wy) < 130:
                        _e.health = min(_e.max_health, _e.health + 40)
        if self.type_id in ("ember_colossus", "acid_spitter"):
            self.war_tremor_timer += tick
            if self.war_tremor_timer >= 150:
                self.war_tremor_timer = 0
                dmg = 55 if self.type_id == "ember_colossus" else 75
                for _t in arena_towers:
                    if math.hypot(_t.wx - self.wx, _t.wy - self.wy) < 135:
                        _t.take_damage(dmg)
                for _w in arena_walls:
                    if math.hypot(_w.wx - self.wx, _w.wy - self.wy) < 110:
                        _w.health -= dmg
        if self.type_id in ("void_shade", "blink_stalker"):
            self.void_step_fake += tick
            if self.void_step_fake >= (220 if self.type_id == "blink_stalker" else 300):
                self.void_step_fake = 0
                dxv = arena_cam_x - self.wx
                dyv = arena_cam_y - self.wy
                dv = math.hypot(dxv, dyv) or 1
                self.wx += dxv / dv * (90 if self.type_id == "blink_stalker" else 140)
                self.wy += dyv / dv * (90 if self.type_id == "blink_stalker" else 140)
        # Shadow hound pounce idle countdown
        if self.type_id == "shadow_hound" and self.pounce_phase == 0:
            self.pounce_timer += tick
            if self.pounce_timer >= 250 and arena_towers:
                nt = [_t for _t in arena_towers if math.hypot(_t.wx - self.wx, _t.wy - self.wy) < 280]
                if nt:
                    self.pounce_target = min(nt, key=lambda _t: math.hypot(_t.wx - self.wx, _t.wy - self.wy))
                    self.pounce_sx = self.wx
                    self.pounce_sy = self.wy
                    self.pounce_phase = 1
                    self.pounce_timer = 0
        self.bob_offset += self.bob_dir * 0.5
        if abs(self.bob_offset) > 5:
            self.bob_dir *= -1

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        by = int(self.bob_offset)
        if self.phase_immune:
            s2d = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
            draw_shape(s2d, self.color + (80,), self.radius + 2, self.radius + 2 + by, self.radius, self.shape)
            screen.blit(s2d, (sx - self.radius - 2, sy - self.radius - 2 - by))
        else:
            draw_shape(screen, self.color, sx, sy + by, self.radius, self.shape, WHITE, 2)

        # Frost slow visual: glowing icy halo on slowed enemies
        _fsm_a = getattr(self, "frost_slow_mult", 1.0)
        if _fsm_a < 0.95:
            _intensity_a = max(0.0, min(1.0, (1.0 - _fsm_a) * 1.6))
            _alpha_a = int(120 * _intensity_a)
            _fr_a = self.radius + 6
            _fs_a = pygame.Surface((_fr_a * 2 + 4, _fr_a * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(_fs_a, (140, 220, 255, _alpha_a), (_fr_a + 2, _fr_a + 2), _fr_a)
            pygame.draw.circle(_fs_a, (200, 240, 255, min(220, _alpha_a + 80)), (_fr_a + 2, _fr_a + 2), _fr_a, 2)
            screen.blit(_fs_a, (sx - _fr_a - 2, sy + by - _fr_a - 2))

        # ── Ability animations ────────────────────────────────────────────────
        # Vampire hit ring
        if self.is_vampire and self.vampire_phase == 2:
            t_v = self.vampire_hit_timer
            rv = int((22 - t_v) * 3 + 12)
            avs = pygame.Surface((rv * 2 + 4, rv * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(avs, (220, 0, 80, 160), (rv + 2, rv + 2), rv, 4)
            screen.blit(avs, (sx - rv - 2, sy + by - rv - 2))
        # Wizard/Necromancer summon ring
        if (self.is_wizard or self.is_summoner) and self.summon_anim_t > 0:
            ring_r = int((18 - self.summon_anim_t) * 4 + 14)
            ring_a = max(0, int(self.summon_anim_t * 12))
            rs = pygame.Surface((ring_r * 2 + 4, ring_r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(rs, (200, 80, 255, ring_a), (ring_r + 2, ring_r + 2), ring_r, 3)
            screen.blit(rs, (sx - ring_r - 2, sy + by - ring_r - 2))
        # War mammoth tremor shockwave
        if self.type_id == "war_mammoth" and self.war_tremor_timer > 370:
            rw = int((self.war_tremor_timer - 370) * 10)
            aw_a = max(0, 200 - int((self.war_tremor_timer - 370) * 7))
            ws = pygame.Surface((rw * 2 + 4, rw * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(ws, (180, 120, 50, aw_a), (rw + 2, rw + 2), rw, 4)
            screen.blit(ws, (sx - rw - 2, sy + by - rw - 2))
        # Storm rider lightning to nearest arena tower
        if self.type_id in ("storm_rider", "celestial_drake") and self.storm_timer > 180 and arena_towers:
            near_at = [t for t in arena_towers if math.hypot(t.wx - self.wx, t.wy - self.wy) < 200]
            if near_at:
                nt = min(near_at, key=lambda t: math.hypot(t.wx - self.wx, t.wy - self.wy))
                ntsx, ntsy = a2s(nt.wx, nt.wy)
                midx = (sx + ntsx) // 2 + int(math.sin(time.time() * 20) * 18)
                midy = (sy + ntsy) // 2 + int(math.cos(time.time() * 20) * 18)
                pygame.draw.line(screen, (100, 180, 255), (sx, sy + by), (midx, midy), 2)
                pygame.draw.line(screen, (200, 230, 255), (midx, midy), (ntsx, ntsy), 2)
        # Shadow hound pounce glow trail
        if self.type_id == "shadow_hound" and self.pounce_phase == 1:
            trs = pygame.Surface((self.radius * 2 + 4, self.radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(trs, (160, 0, 255, 100), (self.radius + 2, self.radius + 2), self.radius + 4)
            screen.blit(trs, (sx - self.radius - 2, sy + by - self.radius - 2))
        # Phase shifter shimmer when immune
        if self.phase_immune:
            ph_s = pygame.Surface((self.radius * 2 + 14, self.radius * 2 + 14), pygame.SRCALPHA)
            draw_shape(ph_s, (200, 100, 255, 80), self.radius + 7, self.radius + 7, self.radius + 6, self.shape)
            screen.blit(ph_s, (sx - self.radius - 7, sy + by - self.radius - 7))
        # Fury beast rage aura when below 50% HP
        if self.fury_beast and self.health < self.max_health * 0.5:
            pulse_f = int(time.time() * 8) % 8
            rf = self.radius + 6 + pulse_f
            fbs = pygame.Surface((rf * 2 + 4, rf * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(fbs, (255, 80, 0, 110), (rf + 2, rf + 2), rf, 3)
            screen.blit(fbs, (sx - rf - 2, sy + by - rf - 2))
        # Paladin regen glow
        if self.regen_rate > 0:
            pulse_p = int(time.time() * 5) % 10
            if pulse_p < 5:
                rps = pygame.Surface((self.radius * 2 + 16, self.radius * 2 + 16), pygame.SRCALPHA)
                pygame.draw.circle(rps, (0, 220, 80, 70 + pulse_p * 10), (self.radius + 8, self.radius + 8), self.radius + 6, 3)
                screen.blit(rps, (sx - self.radius - 8, sy + by - self.radius - 8))
        # Plague moth dust cloud
        if (self.plague_moth_flag or self.type_id == "shield_mender") and self.plague_dust_timer > 120:
            for _di in range(2):
                dsx = sx + int(math.sin(time.time() * 4 + _di * 2.1) * 22)
                dsy = sy + by + int(math.cos(time.time() * 4 + _di * 2.1) * 22)
                das = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(das, ((100, 200, 50, 90) if self.type_id != "shield_mender" else (80, 255, 180, 100)), (8, 8), 6)
                screen.blit(das, (dsx - 8, dsy - 8))
        # Void shade teleport flash
        if self.type_id in ("void_shade", "blink_stalker") and self.void_step_fake > (200 if self.type_id == "blink_stalker" else 280):
            vfr = int((self.void_step_fake - (200 if self.type_id == "blink_stalker" else 280)) * 5)
            vfs = pygame.Surface((vfr * 2 + 4, vfr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(vfs, (80, 0, 160, max(0, 180 - vfr * 12)), (vfr + 2, vfr + 2), vfr, 4)
            screen.blit(vfs, (sx - vfr - 2, sy + by - vfr - 2))
        if self.type_id in ("ember_colossus", "acid_spitter", "frost_weaver", "gravity_slug", "siren_banshee"):
            pulse = int(time.time() * 6) % 18
            rr = self.radius + 12 + pulse
            tint = {
                "ember_colossus": (255, 90, 20, 80),
                "acid_spitter": (150, 255, 40, 80),
                "frost_weaver": (120, 220, 255, 75),
                "gravity_slug": (120, 80, 220, 75),
                "siren_banshee": (210, 210, 255, 70),
            }[self.type_id]
            aura = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(aura, tint, (rr + 2, rr + 2), rr, 3)
            screen.blit(aura, (sx - rr - 2, sy + by - rr - 2))
        if self.type_id in ("obsidian_guardian", "thornback_beast", "mirror_wisp"):
            rr = self.radius + 7 + (int(time.time() * 5) % 5)
            tint = (180, 180, 210, 85) if self.type_id == "obsidian_guardian" else ((80, 220, 80, 80) if self.type_id == "thornback_beast" else (200, 240, 255, 90))
            guard = pygame.Surface((rr * 2 + 4, rr * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(guard, tint, (rr + 2, rr + 2), rr, 2)
            screen.blit(guard, (sx - rr - 2, sy + by - rr - 2))
        # Draw minions
        for _m in self.minions:
            msx, msy = a2s(_m.wx, _m.wy)
            draw_shape(screen, (150, 0, 200), msx, msy, _m.radius, "circle", WHITE, 1)
            pygame.draw.rect(screen, RED, (msx - 8, msy - _m.radius - 8, 16, 3))
            pygame.draw.rect(screen, GREEN, (msx - 8, msy - _m.radius - 8, int(16 * max(0, _m.health / _m.max_health)), 3))

    def draw_health_bar(self):
        sx, sy = a2s(self.wx, self.wy)
        bw = self.radius * 2
        pygame.draw.rect(screen, RED, (sx - self.radius, sy - self.radius - 10, bw, 5))
        pygame.draw.rect(screen, GREEN, (sx - self.radius, sy - self.radius - 10, int(bw * max(0, self.health / self.max_health)), 5))


class ArenaTower:
    _color_map = {
        "gunner": (0, 0, 255),
        "sniper": (0, 0, 150),
        "machine_gun": (0, 180, 0),
        "heavy_machine_gun": (120, 60, 0),
        "airstrike": ORANGE,
        "frost_laser": (80, 200, 240),
        "Goblin Hut": (0, 200, 0),
        "builder_hut": (180, 140, 50),
        "Valkyrie Hut": (160, 80, 220),
    }

    def __init__(self, wx, wy, range_, damage, cooldown, type_, cost):
        self.wx = float(wx)
        self.wy = float(wy)
        self.range = range_
        self.damage = damage
        self.cooldown = cooldown
        self.type = type_
        self.cost = cost
        self.max_health = {"gunner": 200, "sniper": 180, "machine_gun": 200, "heavy_machine_gun": 320, "airstrike": 120, "Goblin Hut": 500, "builder_hut": 300, "Valkyrie Hut": 400}.get(type_, 200)
        self.health = self.max_health
        self.timer = 0
        self.aura_fire_mult = 1.0
        self.bullets = []
        self.kills = 0  # lifetime enemy kills attributed to this tower
        self.turret_angle = 0.0
        self.bullets_per_shot = 1
        # Upgrade system (mirrors Tower class)
        self.level = 1
        self.max_level = (11 if type_ == "gunner" else (7 if type_ == "Valkyrie Hut" else 10))
        self.upgrade_cost_spent = 0
        self.homing = False
        # Goblin Hut support
        self.goblins = []
        self.goblin_tier = 0
        self.max_goblins = 3
        self.goblin_timer = 0
        # Builder Hut support
        self.builders = []
        self.builder_timer = 0
        self.builder_upgraded = False
        self.builder_respawn_wave = 0
        # Valkyrie Hut support
        self.valk_built = False
        self.valk_kills = 0
        self.valk_kills_needed = 100
        self.valkyries = []
        self.valk_speed = 2.5
        self.valk_combined = False
        # Sniper: can see sniper_only enemies
        self.is_sniper = type_ in ("sniper", "airstrike")
        # Frost Laser visuals
        self.spin_angle = 0.0
        self.frost_zap_timer = 0
        # ── Pristine / Blood attribute parity with TD Tower ──────────────────
        self.pristine = None
        self.spray = False
        self.turret_count = 1
        self.spin_turrets = False
        self.stun_frames = 0
        self.shrap_dmg = 0
        self.pierce = 0
        self.fire_dps = 0
        self.splash_bonus = 0
        self.has_loader = False
        self.spike_count = 0
        self.frost_slow_bonus = 0
        self.frost_chain_bonus = 0
        self.chimney_distractor = False
        # Helpers, loader, ammo, healing (parity)
        self.helpers = []
        self.heal_amount = 0
        self.heal_interval = 0
        self.heal_timer = 0
        self.instant_heal_chance = 0
        self.has_loader = False
        self.max_ammo = 0
        self.ammo = 0
        self.load_speed = 1.0
        self.gob_dmg_bonus = 0
        self.barb_throw_chance = 0
        self.split_barbarians = 0
        self.barbarians_spawned = []
        self.burst_fire = False
        # Airstrike multi-turret animation
        self.assembly_angle = 0.0
        self.airstrike_turret_idx = 0
        # Muzzle flash
        self.muzzle_flash_timer = 0
        self.muzzle_flash_pos = None
        # Chimney smoke (Builder Hut Pristine Silver+)
        self.chimney_smoke = []

    def take_damage(self, amt):
        self.health = max(0, self.health - amt)

    def upgrade(self):
        global arena_coins
        if self.level >= self.max_level:
            return
        lvl_index = self.level - 1
        table = UPGRADE_TABLE.get(self.type, [])
        if lvl_index >= len(table):
            return
        info = table[lvl_index]
        if info.get("blood") and not blood_storm_active:
            return
        # Pristine upgrades require shadow storm (parity with TD)
        if info.get("pristine") and not shadow_storm_active:
            return
        if arena_coins < info["cost"]:
            return
        arena_coins -= info["cost"]
        self.upgrade_cost_spent += info["cost"]
        self.damage += info["damage"]
        self.range += info["range"]
        self.max_health += info["health"]
        self.health += info["health"]
        # ── Pristine ability application (parity with TD Tower.upgrade) ─────
        if info.get("pristine"):
            self.pristine = info["pristine"]
            if "stun" in info:
                self.stun_frames = info["stun"]
            if "shrap" in info:
                self.shrap_dmg = info["shrap"]
            if "pierce" in info:
                self.pierce = info["pierce"]
            if "spray" in info:
                self.spray = True
            if "turrets" in info:
                self.turret_count = info["turrets"]
            if "spin" in info:
                self.spin_turrets = True
            if "fire" in info:
                self.fire_dps = info["fire"]
            if "splash_bonus" in info:
                self.splash_bonus = info["splash_bonus"]
            if "spikes" in info:
                self.spike_count = info["spikes"]
            if "chimney" in info:
                self.chimney_distractor = True
            if "slow_bonus" in info:
                self.frost_slow_bonus += info["slow_bonus"]
            if "chain_bonus" in info:
                self.frost_chain_bonus += info["chain_bonus"]
            if "loader" in info:
                self.has_loader = True
                self.max_ammo = info.get("max_ammo", 3)
                self.ammo = self.max_ammo
                self.load_speed = info.get("load_speed", 1.0)
            if "burst_fire" in info:
                self.burst_fire = True
            if "gob_dmg" in info:
                self.gob_dmg_bonus = info["gob_dmg"]
                if self.type == "Goblin Hut":
                    for _g in self.goblins:
                        _g.attack_damage += info["gob_dmg"]
            if "barb_chance" in info:
                self.barb_throw_chance = info["barb_chance"]
                # Convert existing arena goblins to barbarians instantly
                if self.type == "Goblin Hut":
                    for _g in self.goblins:
                        if not getattr(_g, "barbarian", False):
                            _g.barbarian = True
                            _g.max_health = int(_g.max_health * 3)
                            _g.health = _g.max_health
            if "heal" in info:
                self.heal_amount, self.heal_interval = info["heal"]
            if "instant_chance" in info:
                self.instant_heal_chance = info["instant_chance"]
            if "split_barbs" in info:
                self.split_barbarians = info["split_barbs"]
        # ── Goblin Hut ──────────────────────────────────────────────────────
        if self.type == "Goblin Hut":
            if self.level == 1:
                self.max_goblins = 5
                self.goblin_tier = 1
                gc = GOBLIN_COLORS[1]
                for g in self.goblins:
                    g.tier = 1
                    g.max_health = 150
                    g.attack_damage = 50
                    g.color = gc
            elif self.level == 2:
                self.goblin_tier = 2
                self.max_health = max(self.max_health, 800)
                self.health = min(self.health + 650, self.max_health)
                gc = GOBLIN_COLORS[2]
                for g in self.goblins:
                    g.tier = 2
                    g.max_health = 220
                    g.attack_damage = 80
                    g.color = gc
                    g.speed = 3
            elif self.level == 3:
                self.goblin_tier = 3
                gc = GOBLIN_COLORS[3]
                for g in self.goblins:
                    g.tier = 3
                    g.max_health = 400
                    g.attack_damage = 120
                    g.speed = 5.0
                    g.color = gc
            elif self.level == 4:
                self.goblin_tier = 4
                self.max_goblins = 7
                gc = GOBLIN_COLORS[4]
                for g in self.goblins:
                    g.tier = 4
                    g.max_health = 600
                    g.attack_damage = 200
                    g.color = gc
                    g.speed = 5.5
            elif self.level == 5:
                self.goblin_tier = 5
                gc = GOBLIN_COLORS[5]
                for g in self.goblins:
                    g.tier = 5
                    g.max_health = 1200
                    g.attack_damage = 400
                    g.color = gc
                    g.speed = 6.5
            elif self.level == 6:
                self.goblin_tier = 5
                self.max_goblins = 9
                gc = GOBLIN_COLORS[5]
                for g in self.goblins:
                    g.tier = 5
                    g.max_health = 2000
                    g.attack_damage = 600
                    g.color = gc
                    g.speed = 7.0
        # ── Builder Hut ─────────────────────────────────────────────────────
        elif self.type == "builder_hut":
            if self.level == 1:
                self.builder_upgraded = True
            for b in self.builders:
                _apply_builder_level(b, self.level)
        # ── Sniper cooldown ──────────────────────────────────────────────────
        elif self.type == "sniper":
            self.cooldown = max(15, self.cooldown - 10)
        elif self.type == "airstrike":
            self.cooldown = max(30, self.cooldown - 15)
        # ── Valkyrie Hut ────────────────────────────────────────────────────
        elif self.type == "Valkyrie Hut":
            if self.level == 1:
                self.valk_speed = 3.8
                for v in self.valkyries:
                    v.speed = self.valk_speed
            elif self.level == 2:
                self.valk_speed = 5.2
                for v in self.valkyries:
                    v.speed = self.valk_speed
        # Gunner sputter bullets per shot
        if self.type == "gunner" and "bullets" in info:
            self.bullets_per_shot = info["bullets"]
        # Homing: explicit flag OR legacy Blood Tier 2 for non-gunners
        if info.get("homing"):
            self.homing = True
        elif self.level == 5 and self.type not in ("Goblin Hut", "builder_hut", "Valkyrie Hut", "gunner"):
            self.homing = True
        self.level += 1

    def shoot(self, enemies):
        tick = 2 if speed_2x else 1
        _am = self.aura_fire_mult
        # ── Frost Laser aura ──────────────────────────────────────────────────
        if self.type == "frost_laser":
            self.spin_angle = (self.spin_angle + (0.04 * tick)) % (2 * math.pi)
            slow_table = [0.55, 0.50, 0.45, 0.40, 0.35, 0.30]
            slow_mult = slow_table[min(self.level - 1, len(slow_table) - 1)]
            for _fe in enemies:
                if _fe.alive and math.hypot(_fe.wx - self.wx, _fe.wy - self.wy) <= self.range:
                    _fe.frost_slow_mult = min(getattr(_fe, "frost_slow_mult", 1.0), slow_mult)
                    if self.level >= 3:
                        _fe.frost_disabled = True
            if self.level >= 4:
                self.frost_zap_timer += tick
                zap_interval = {4: 300, 5: 240, 6: 180}.get(self.level, 300)
                if self.frost_zap_timer >= zap_interval:
                    self.frost_zap_timer = 0
                    chain_counts = {4: 3, 5: 4, 6: 5}
                    chain_ranges = {4: 80, 5: 100, 6: 120}
                    _n_chains = chain_counts.get(self.level, 3)
                    _c_range = chain_ranges.get(self.level, 80)
                    _candidates = [e for e in enemies if e.alive and math.hypot(e.wx - self.wx, e.wy - self.wy) <= self.range]
                    if _candidates:
                        _zapped = []
                        _first = min(_candidates, key=lambda e: math.hypot(e.wx - self.wx, e.wy - self.wy))
                        _zapped.append(_first)
                        _first.health -= self.damage
                        for _ in range(_n_chains - 1):
                            _last = _zapped[-1]
                            _next_c = [e for e in enemies if e.alive and e not in _zapped and math.hypot(e.wx - _last.wx, e.wy - _last.wy) <= _c_range]
                            if not _next_c:
                                break
                            _ne = min(_next_c, key=lambda e: math.hypot(e.wx - _last.wx, e.wy - _last.wy))
                            _ne.health -= self.damage
                            _zapped.append(_ne)
                        if not hasattr(self, "zap_lines"):
                            self.zap_lines = []
                        sx0, sy0 = a2s(self.wx, self.wy)
                        self.zap_lines = [(sx0, sy0)] + [a2s(e.wx, e.wy) for e in _zapped]
                        self.zap_flash = 8
            if hasattr(self, "zap_flash") and self.zap_flash > 0:
                self.zap_flash -= 1
                if hasattr(self, "zap_lines") and len(self.zap_lines) >= 2:
                    # zap_lines is a flat list of paired points: [from, to, from, to, ...]
                    _zl = self.zap_lines
                    for _zi in range(0, len(_zl) - 1, 2):
                        p1 = (int(_zl[_zi][0]), int(_zl[_zi][1]))
                        p2 = (int(_zl[_zi + 1][0]), int(_zl[_zi + 1][1]))
                        pygame.draw.line(screen, (20, 80, 255), p1, p2, 7)
                        pygame.draw.line(screen, (120, 220, 255), p1, p2, 3)
            return
        # ── Goblin Hut ────────────────────────────────────────────────────────
        if self.type == "Goblin Hut":
            self.goblin_timer += tick
            if self.goblin_timer >= 600 and len(self.goblins) < self.max_goblins:
                for _ in range(min(3, self.max_goblins - len(self.goblins))):
                    _ag = ArenaGoblin(self.wx + random.randint(-12, 12), self.wy + random.randint(-12, 12), self.goblin_tier)
                    _ag.parent_hut = self
                    self.goblins.append(_ag)
                self.goblin_timer = 0
            for _g in self.goblins[:]:
                _g.update(enemies)
                if _g.health <= 0:
                    self.goblins.remove(_g)
            return
        # ── Builder Hut ───────────────────────────────────────────────────────
        if self.type == "builder_hut":
            self.builder_timer += tick
            if len(self.builders) == 0 and self.builder_timer >= 600:
                nb = ArenaBuilder(self.wx, self.wy, self.builder_upgraded)
                nb.parent_hut = self
                for _lv in range(1, self.level + 1):
                    _apply_builder_level(nb, _lv)
                self.builders.append(nb)
                self.builder_timer = 0
            for _b in self.builders[:]:
                _b.update(arena_towers, enemies)
                if not _b.alive:
                    self.builders.remove(_b)
                    self.builder_respawn_wave = arena_wave + 5
                    self.builder_timer = 0
            # Pristine helper-hut healing aura: heal nearby towers
            if self.heal_amount > 0 and self.heal_interval > 0:
                self.heal_timer += tick
                if self.heal_timer >= self.heal_interval:
                    self.heal_timer = 0
                    for _t in arena_towers:
                        if _t is self:
                            continue
                        if math.hypot(_t.wx - self.wx, _t.wy - self.wy) <= 220:
                            amt = self.heal_amount
                            if self.instant_heal_chance > 0 and random.randint(1, 100) <= self.instant_heal_chance:
                                amt = _t.max_health  # full heal proc
                            _t.health = min(_t.max_health, _t.health + amt)
            return
        # ── Valkyrie Hut ─────────────────────────────────────────────────────
        if self.type == "Valkyrie Hut":
            return  # handled in update_valkyrie_hut()
        # ── Shooting towers ───────────────────────────────────────────────────
        # Update existing bullets
        for _b in self.bullets[:]:
            _b.update()
            if not _b.alive:
                self.bullets.remove(_b)
        # Airstrike pristine: simulated loader auto-refills ammo at load_speed
        if self.has_loader and self.type == "airstrike" and self.ammo < self.max_ammo:
            self.heal_timer += tick * self.load_speed
            if self.heal_timer >= 240:  # ~4 sec base, divided by load_speed
                self.heal_timer = 0
                self.ammo = min(self.max_ammo, self.ammo + 1)
        visible = [e for e in enemies if e.alive and not e.is_tower_raider]
        if self.timer <= 0:
            # Airstrike pristine: require ammo to fire
            if self.has_loader and self.type == "airstrike" and self.ammo <= 0:
                return
            in_range = []
            for e in visible:
                if math.hypot(e.wx - self.wx, e.wy - self.wy) >= self.range:
                    continue
                if e.visible_to == "sniper_only" and not self.is_sniper:
                    continue
                if getattr(e, "phase_immune", False):
                    continue
                in_range.append(e)
                if len(in_range) >= max(1, self.bullets_per_shot):
                    break
            if in_range:
                primary = in_range[0]
                self.turret_angle = math.atan2(primary.wy - self.wy, primary.wx - self.wx)
                # Animate airstrike 3-turret assembly to point at target
                if self.type == "airstrike" and self.turret_count >= 3:
                    self.assembly_angle = self.turret_angle - (self.airstrike_turret_idx * (2 * math.pi / 3))
                bcolors = {"gunner": (0, 100, 255), "sniper": (150, 200, 255), "machine_gun": (0, 220, 0), "heavy_machine_gun": (200, 120, 0), "airstrike": (255, 140, 0)}
                bc = bcolors.get(self.type, YELLOW)
                splh = self.type == "airstrike"
                # How many shots this volley (burst_fire=3 for airstrike pristine gold)
                shot_volleys = 3 if (self.type == "airstrike" and self.burst_fire) else 1
                for _v in range(shot_volleys):
                    for e in in_range:
                        self.bullets.append(ArenaTowerBullet(self.wx, self.wy, e, self.damage, bc, splh, owner=self))
                # Gunner Pristine Gold spray fan (parity with TD): 2 extra fans ±30°
                if self.type == "gunner" and self.spray:
                    base_ang = math.atan2(primary.wy - self.wy, primary.wx - self.wx)
                    for ang_off in (math.radians(30), math.radians(-30)):
                        for _ in range(self.bullets_per_shot):
                            sb = ArenaTowerBullet(self.wx, self.wy, primary, max(1, int(self.damage * 0.7)), YELLOW, False, owner=self)
                            ang = base_ang + ang_off
                            sb.vx = math.cos(ang) * sb.speed
                            sb.vy = math.sin(ang) * sb.speed
                            self.bullets.append(sb)
                # Consume ammo (airstrike pristine)
                if self.has_loader and self.type == "airstrike":
                    self.ammo = max(0, self.ammo - 1)
                # Cycle next airstrike turret
                if self.type == "airstrike" and self.turret_count >= 3:
                    self.airstrike_turret_idx = (self.airstrike_turret_idx + 1) % 3
                # Muzzle flash at barrel tip
                _flash_x, _flash_y = a2s(self.wx + math.cos(self.turret_angle) * 22, self.wy + math.sin(self.turret_angle) * 22)
                self.muzzle_flash_pos = (int(_flash_x), int(_flash_y))
                self.muzzle_flash_timer = 6
                self.timer = int(self.cooldown * _am)
        else:
            self.timer = max(0, self.timer - tick)

    def update_valkyrie_hut(self, arena_enemies_list):
        """Update Valkyrie Hut in arena mode."""
        if self.type != "Valkyrie Hut":
            return
        if self.valk_built:
            live_targets = [e for e in arena_enemies_list if getattr(e, "health", 0) > 0]
            for i, v in enumerate(self.valkyries[:]):
                assigned = live_targets[i % len(live_targets)] if live_targets else None
                v.update(arena_enemies_list, assigned)
                if v.health <= 0:
                    self.valkyries.remove(v)
            max_v = 5 if self.valk_combined else 3
            if len(self.valkyries) < max_v and random.random() < 0.002:
                mode = "raider_focus" if (self.valk_combined and len([x for x in self.valkyries if x.mode == "raider_focus"]) < 3) else "minion_focus"
                v = Valkyrie(self.wx + random.randint(-20, 20), self.wy + random.randint(-20, 20), mode)
                v.parent_hut = self
                v.arena_mode = True
                v.speed = self.valk_speed
                v.home_x = self.wx
                v.home_y = self.wy
                if self.valk_combined:
                    v.damage = 600
                self.valkyries.append(v)

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        c = self._color_map.get(self.type, (100, 100, 100))

        if self.type == "frost_laser":
            draw_frost_rings(sx, sy, int(self.range), self.spin_angle)

        # Spinning turret animation tick (MG / airstrike gold)
        if self.spin_turrets:
            _wave_going = arena_wave_active
            if self.type == "machine_gun":
                if _wave_going:
                    self.spin_angle = (self.spin_angle + 0.06) % (2 * math.pi)
            else:
                self.spin_angle = (self.spin_angle + 0.06) % (2 * math.pi)

        if self.type in ("gunner", "sniper", "machine_gun", "heavy_machine_gun", "airstrike"):
            # ── Pristine Gold MG: special rotating 8-barrel base ───────────
            if self.type == "machine_gun" and self.spin_turrets:
                draw_machine_gun_base(sx, sy, self.spin_angle)
            else:
                # ── Gunner: 2 small side turrets tucked UNDER the body ─────
                if self.type == "gunner":
                    g_turret_col = (60, 70, 200)
                    g_edge = (15, 25, 90)
                    g_hole = (10, 10, 30)
                    for _side_off in (math.pi / 2, -math.pi / 2):
                        a = self.turret_angle + _side_off
                        tx = sx + math.cos(a) * 11
                        ty = sy + math.sin(a) * 11
                        rect = pygame.Rect(int(tx - 6), int(ty - 6), 12, 12)
                        pygame.draw.rect(screen, g_turret_col, rect, border_radius=3)
                        pygame.draw.rect(screen, g_edge, rect, 2, border_radius=3)
                        hx = tx + math.cos(a) * 4
                        hy = ty + math.sin(a) * 4
                        pygame.draw.circle(screen, g_hole, (int(hx), int(hy)), 2)

                # ── Gold Airstrike: 3 rounded-square turrets around a circular base
                if self.type == "airstrike" and self.turret_count >= 3:
                    base_r = 16
                    body_col = (220, 110, 30)
                    edge_col = (130, 60, 0)
                    turret_col = (175, 95, 25)
                    barrel_hole = (60, 30, 0)
                    turret_size = 14
                    turret_offset_r = 22
                    for i in range(3):
                        a = self.assembly_angle + i * (2 * math.pi / 3)
                        tx = sx + math.cos(a) * turret_offset_r
                        ty = sy + math.sin(a) * turret_offset_r
                        rect = pygame.Rect(int(tx - turret_size / 2), int(ty - turret_size / 2),
                                           turret_size, turret_size)
                        pygame.draw.rect(screen, turret_col, rect, border_radius=4)
                        pygame.draw.rect(screen, edge_col, rect, 2, border_radius=4)
                        if i == self.airstrike_turret_idx:
                            hl = pygame.Rect(rect.x - 2, rect.y - 2, rect.w + 4, rect.h + 4)
                            pygame.draw.rect(screen, (255, 230, 100), hl, 2, border_radius=5)
                        hx = tx + math.cos(a) * 5
                        hy = ty + math.sin(a) * 5
                        pygame.draw.circle(screen, barrel_hole, (int(hx), int(hy)), 3)
                        pygame.draw.circle(screen, edge_col, (int(hx), int(hy)), 3, 1)
                    pygame.draw.circle(screen, body_col, (sx, sy), base_r)
                    pygame.draw.circle(screen, edge_col, (sx, sy), base_r, 3)
                    pygame.draw.circle(screen, (170, 80, 20), (sx, sy), 6)
                    pygame.draw.circle(screen, edge_col, (sx, sy), 6, 1)
                else:
                    # Gunner Pristine Gold spray-fan: 2 extra barrels at ±25° (under body)
                    if self.spray:
                        fan_col = (255, 210, 65)
                        draw_extra_barrel(sx, sy, self.turret_angle + math.radians(25), fan_col, length=24, width=7)
                        draw_extra_barrel(sx, sy, self.turret_angle - math.radians(25), fan_col, length=24, width=7)
                    draw_tower_base(sx, sy, c, self.turret_angle)
                    # HMG final upgrade: stock detail
                    if self.type == "heavy_machine_gun" and self.level >= self.max_level:
                        ba = self.turret_angle + math.pi
                        cosA, sinA = math.cos(ba), math.sin(ba)
                        cosP, sinP = math.cos(ba + math.pi / 2), math.sin(ba + math.pi / 2)
                        stock_col = (60, 35, 15)
                        edge_col = (20, 10, 0)
                        for off, w, h in ((10, 8, 14), (20, 10, 16)):
                            ccx = sx + cosA * off
                            ccy = sy + sinA * off
                            pts = []
                            for sx_o, sy_o in ((-w, -h), (w, -h), (w, h), (-w, h)):
                                px = ccx + (cosA * sy_o + cosP * sx_o) * 0.5
                                py = ccy + (sinA * sy_o + sinP * sx_o) * 0.5
                                pts.append((int(px), int(py)))
                            pygame.draw.polygon(screen, stock_col, pts)
                            pygame.draw.polygon(screen, edge_col, pts, 2)
                        for line_off in (12, 16, 20):
                            cx_l = sx + cosA * line_off
                            cy_l = sy + sinA * line_off
                            x1 = cx_l + cosP * 5
                            y1 = cy_l + sinP * 5
                            x2 = cx_l - cosP * 5
                            y2 = cy_l - sinP * 5
                            pygame.draw.line(screen, (200, 170, 60), (int(x1), int(y1)), (int(x2), int(y2)), 2)
                    # Multi-turret extras (non-airstrike): N evenly-spaced barrels
                    if self.turret_count > 1 and self.type != "airstrike":
                        barrel_col = ((255, 210, 65) if self.pristine == "gold"
                                      else ((220, 220, 230) if self.pristine == "silver"
                                      else ((205, 130, 50) if self.pristine == "bronze" else c)))
                        spin_off = self.spin_angle if self.spin_turrets else 0.0
                        for i in range(1, self.turret_count):
                            a = self.turret_angle + spin_off + (2 * math.pi * i / self.turret_count)
                            draw_extra_barrel(sx, sy, a, barrel_col,
                                              length=22 if self.type == "machine_gun" else 26,
                                              width=7 if self.type == "machine_gun" else 9)
            # Pristine ring overlay
            if self.pristine:
                draw_pristine_ring(sx, sy, self.pristine, radius=22)
        else:
            pygame.draw.rect(screen, c, (sx - 13, sy - 13, 26, 26))
            pygame.draw.rect(screen, WHITE, (sx - 13, sy - 13, 26, 26), 2)
            abbr = {"frost_laser": "FL", "Goblin Hut": "GH", "builder_hut": "BH", "Valkyrie Hut": "VH"}.get(self.type, "?")
            screen.blit(font_sm.render(abbr, True, WHITE), (sx - 8, sy - 7))
            # Pristine ring for hut-type towers
            if self.pristine and self.type in ("builder_hut", "Goblin Hut", "Valkyrie Hut", "frost_laser"):
                draw_pristine_ring(sx, sy, self.pristine, radius=22)
            # ── Frost Laser Pristine Gold: 3 concentric circles ───────────
            if self.type == "frost_laser" and self.pristine == "gold":
                for _fr, _fa in [(12, 200), (8, 180), (5, 220)]:
                    _fs = pygame.Surface((_fr * 2 + 2, _fr * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(_fs, (100, 220, 255, _fa), (_fr + 1, _fr + 1), _fr)
                    pygame.draw.circle(_fs, (20, 80, 200, 220), (_fr + 1, _fr + 1), _fr, 2)
                    screen.blit(_fs, (sx - _fr - 1, sy - _fr - 1))
            # ── Goblin Hut Pristine spinning spikes (silver=4, gold=8) ────
            if self.type == "Goblin Hut" and self.spike_count > 0:
                self.spin_angle = (self.spin_angle + 0.05) % (2 * math.pi)
                spike_color = (255, 210, 65) if self.pristine == "gold" else (220, 220, 230)
                spike_dark = (180, 140, 20) if self.pristine == "gold" else (150, 150, 165)
                spike_radius = 28
                for i in range(self.spike_count):
                    a = self.spin_angle + i * (2 * math.pi / self.spike_count)
                    base_x = sx + spike_radius * math.cos(a)
                    base_y = sy + spike_radius * math.sin(a)
                    tip_x = sx + (spike_radius + 12) * math.cos(a)
                    tip_y = sy + (spike_radius + 12) * math.sin(a)
                    perp = a + math.pi / 2
                    side1 = (base_x + 4 * math.cos(perp), base_y + 4 * math.sin(perp))
                    side2 = (base_x - 4 * math.cos(perp), base_y - 4 * math.sin(perp))
                    pygame.draw.polygon(screen, spike_color,
                                        [(int(tip_x), int(tip_y)), (int(side1[0]), int(side1[1])), (int(side2[0]), int(side2[1]))])
                    pygame.draw.polygon(screen, spike_dark,
                                        [(int(tip_x), int(tip_y)), (int(side1[0]), int(side1[1])), (int(side2[0]), int(side2[1]))], 1)
            # ── Builder Hut Pristine: helper hut + door ───────────────────
            if self.type == "builder_hut" and self.pristine:
                hh_x, hh_y = sx + 30, sy + 18
                pygame.draw.circle(screen, (200, 145, 35), (int(hh_x), int(hh_y)), 11)
                pygame.draw.circle(screen, (130, 80, 20), (int(hh_x), int(hh_y)), 11, 2)
                pygame.draw.rect(screen, (180, 130, 40), (int(hh_x + 7), int(hh_y + 2), 10, 8))
                pygame.draw.rect(screen, (130, 80, 20), (int(hh_x + 7), int(hh_y + 2), 10, 8), 1)
                pygame.draw.rect(screen, (160, 110, 30), (int(sx - 4), int(sy + 2), 8, 12))
                pygame.draw.rect(screen, (110, 70, 15), (int(sx - 4), int(sy + 2), 8, 12), 1)
            # ── Builder Hut Chimney + smoke (Silver+ pristine) ────────────
            if self.type == "builder_hut" and self.chimney_distractor:
                pygame.draw.rect(screen, (110, 110, 110), (int(sx - 18), int(sy - 22), 6, 10))
                pygame.draw.rect(screen, (60, 60, 60), (int(sx - 18), int(sy - 22), 6, 10), 1)
                # Spawn smoke puffs
                if random.random() < 0.05:
                    self.chimney_smoke.append([sx - 15, sy - 24, 0])
                # Update + draw existing puffs
                for puff in self.chimney_smoke[:]:
                    puff[1] -= 0.4
                    puff[2] += 1
                    if puff[2] > 70:
                        self.chimney_smoke.remove(puff)
                        continue
                    age = puff[2]
                    a = max(0, 220 - int(age * 3))
                    rr = 3 + age // 8
                    s = pygame.Surface((rr * 2 + 2, rr * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(s, (200, 200, 200, a), (rr + 1, rr + 1), rr)
                    screen.blit(s, (int(puff[0]) - rr, int(puff[1]) - rr))
        # Show level badge
        if self.level > 1:
            lbl = font_sm.render(f"L{self.level}", True, YELLOW)
            screen.blit(lbl, (sx + 12, sy - 22))
        # Draw goblins, builders, valkyries
        for _g in self.goblins:
            _g.draw()
        for _b in self.builders:
            _b.draw()
        for _v in self.valkyries:
            _v.draw()
        # ── Airstrike pristine ammo dots above tower ─────────────────────
        if self.has_loader and self.type == "airstrike":
            for ai in range(self.max_ammo):
                ax = int(sx - (self.max_ammo - 1) * 5 + ai * 10)
                ay = int(sy - 30)
                if ai < self.ammo:
                    pygame.draw.circle(screen, ORANGE, (ax, ay), 4)
                    pygame.draw.circle(screen, (120, 60, 0), (ax, ay), 4, 1)
                else:
                    pygame.draw.circle(screen, (60, 60, 60), (ax, ay), 4)
                    pygame.draw.circle(screen, (30, 30, 30), (ax, ay), 4, 1)
        # ── Muzzle flash ─────────────────────────────────────────────────
        if self.muzzle_flash_timer > 0 and self.muzzle_flash_pos:
            fr = 10
            fs = pygame.Surface((fr * 2, fr * 2), pygame.SRCALPHA)
            pygame.draw.circle(fs, (255, 255, 100, 180), (fr, fr), fr)
            screen.blit(fs, (self.muzzle_flash_pos[0] - fr, self.muzzle_flash_pos[1] - fr))
            self.muzzle_flash_timer -= 1
            if self.muzzle_flash_timer == 0:
                self.muzzle_flash_pos = None

    def draw_health_bar(self):
        sx, sy = a2s(self.wx, self.wy)
        pygame.draw.rect(screen, RED, (sx - 13, sy - 20, 26, 4))
        pygame.draw.rect(screen, GREEN, (sx - 13, sy - 20, int(26 * max(0, self.health / self.max_health)), 4))
        if self.type == "Valkyrie Hut" and not self.valk_built:
            prog = min(1.0, self.valk_kills / max(1, self.valk_kills_needed))
            pygame.draw.rect(screen, (60, 40, 10), (sx - 13, sy - 27, 26, 4))
            pygame.draw.rect(screen, (255, 200, 50), (sx - 13, sy - 27, int(26 * prog), 4))
        for _v in self.valkyries:
            _v.draw_health_bar()


class ArenaWall:
    W = 64  # long axis
    H = 20  # short axis
    R = 32  # collision half-diagonal (approx)

    LEVEL_STATS = {
        1: {"max_health": 1500, "cost": 0,      "edge": (220, 180, 80)},
        2: {"max_health": 4000, "cost": 50000,  "edge": (180, 220, 255)},
        3: {"max_health": 9000, "cost": 250000, "edge": (200, 100, 255)},
    }
    max_level = 3

    def __init__(self, wx, wy, angle=0):
        self.wx = float(wx)
        self.wy = float(wy)
        self.level = 1
        self.max_health = 1500
        self.health = 1500
        self.angle = angle  # degrees
        self.upgrade_cost_spent = 0

    def upgrade(self):
        if self.level >= self.max_level:
            return
        self.level += 1
        stats = self.LEVEL_STATS[self.level]
        hp_gain = stats["max_health"] - self.LEVEL_STATS[self.level - 1]["max_health"]
        self.max_health = stats["max_health"]
        self.health = min(self.max_health, self.health + hp_gain)
        self.upgrade_cost_spent += stats["cost"]

    def is_blocking(self):
        """Level 3 walls actively repel enemies (cannot be walked through)."""
        return self.level >= 3

    def half_diag(self):
        return math.hypot(self.W, self.H) / 2

    def draw(self):
        sx, sy = a2s(self.wx, self.wy)
        ratio = max(0.0, self.health / self.max_health)
        stats = self.LEVEL_STATS[self.level]
        edge_col = stats["edge"]
        if self.level == 1:
            cr = int(180 * ratio + 60 * (1 - ratio))
            cg = int(140 * ratio + 40 * (1 - ratio))
            cb = int(80 * ratio + 20 * (1 - ratio))
            fill = (cr, cg, cb)
        elif self.level == 2:
            fill = (int(40 * ratio + 20 * (1 - ratio)), int(80 * ratio + 30 * (1 - ratio)), int(160 * ratio + 60 * (1 - ratio)))
        else:
            fill = (int(60 * ratio + 20 * (1 - ratio)), int(20 * ratio + 10 * (1 - ratio)), int(90 * ratio + 30 * (1 - ratio)))
        surf = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        surf.fill(fill)
        pygame.draw.rect(surf, edge_col, (0, 0, self.W, self.H), 2)
        # Level indicator dots
        for _li in range(self.level):
            pygame.draw.circle(surf, WHITE, (6 + _li * 8, self.H // 2), 3)
        rot = pygame.transform.rotate(surf, -self.angle)
        screen.blit(rot, (sx - rot.get_width() // 2, sy - rot.get_height() // 2))
        # Health bar above
        bw = self.W
        bh = 5
        bx = sx - bw // 2
        by = sy - rot.get_height() // 2 - 8
        pygame.draw.rect(screen, RED, (bx, by, bw, bh))
        pygame.draw.rect(screen, GREEN, (bx, by, int(bw * ratio), bh))


def reset_arena():
    global arena_cam_x, arena_cam_y, arena_player_hp, arena_coins
    global arena_wave, arena_wave_active, arena_enemies_spawned, arena_enemies_to_spawn
    global arena_enemy_timer, arena_shop_open, arena_shop_x, arena_shop_tab
    global arena_placing_tower, arena_placing_wall, arena_selected_tower_obj, arena_selected_wall_obj
    global arena_shoot_cd, arena_player_iframes
    global blood_storm_active, blood_storm_splash_timer, blood_storm_info_open
    global arena_wall_rot, nightmare_mode
    global arena_gun_level
    global arena_valkyrie_combine_mode, arena_valkyrie_combine_hut, arena_combine_anim_timer, arena_combine_anim_pos
    arena_wall_rot = 0
    arena_cam_x = 0.0
    arena_cam_y = 0.0
    arena_player_hp = 100
    arena_coins = coins  # shared coin pool
    arena_wave = 1
    arena_wave_active = False
    arena_enemies_spawned = 0
    arena_enemies_to_spawn = 0
    arena_enemy_timer = 0
    arena_enemies[:] = []
    arena_towers[:] = []
    arena_walls[:] = []
    arena_p_bullets[:] = []
    arena_shop_open = False
    arena_shop_x = -SHOP_W
    arena_shop_tab = "towers"
    arena_placing_tower = None
    arena_placing_wall = False
    arena_selected_tower_obj = None
    arena_selected_wall_obj = None
    arena_shoot_cd = 0
    arena_player_iframes = 0
    arena_gun_level = 0
    arena_valkyrie_combine_mode = False
    arena_valkyrie_combine_hut = None
    arena_combine_anim_timer = 0
    arena_combine_anim_pos = None
    blood_storm_active = False
    blood_storm_splash_timer = 0
    blood_storm_info_open = False
    shadow_storm_active = False
    shadow_storm_splash_timer = 0
    shadow_storm_info_open = False
    nightmare_mode = False


def draw_arena_background():
    # Grass field: dark green base, slightly varying tile shades + tree clusters
    if shadow_storm_active:
        base_col = (35, 0, 60)
    elif blood_storm_active:
        base_col = (60, 10, 10)
    else:
        base_col = (38, 110, 55)
    screen.fill(base_col)

    tile = 80
    ox = int(arena_cam_x) % tile
    oy = int(arena_cam_y) % tile
    cam_tx = int(arena_cam_x // tile)
    cam_ty = int(arena_cam_y // tile)

    # Subtle checkerboard grass shading
    for gx in range(-1, WIDTH // tile + 2):
        for gy in range(-1, HEIGHT // tile + 2):
            wx_t = gx + cam_tx
            wy_t = gy + cam_ty
            shade = ((wx_t * 31 + wy_t * 17) % 5)
            if blood_storm_active:
                col = (50 + shade * 4, 8, 8)
            else:
                col = (32 + shade * 4, 100 + shade * 5, 48 + shade * 3)
            tx = gx * tile - ox
            ty = gy * tile - oy
            pygame.draw.rect(screen, col, (tx, ty, tile, tile))

    # Grass tufts and trees (deterministic per world tile)
    for gx in range(-1, WIDTH // tile + 2):
        for gy in range(-1, HEIGHT // tile + 2):
            wx_t = gx + cam_tx
            wy_t = gy + cam_ty
            seed = (wx_t * 73 + wy_t * 131) & 0xFFFF
            tx_c = gx * tile - ox + tile // 2
            ty_c = gy * tile - oy + tile // 2
            kind = seed % 8
            if kind == 0 or kind == 1:
                # Tree: brown trunk + dark-green canopy
                jx = ((seed >> 4) % 30) - 15
                jy = ((seed >> 8) % 30) - 15
                tx = tx_c + jx
                ty = ty_c + jy
                trunk_col = (75, 45, 25) if not blood_storm_active else (40, 15, 15)
                canopy_col = (24, 70, 32) if not blood_storm_active else (60, 12, 12)
                canopy_hi  = (40, 100, 48) if not blood_storm_active else (90, 20, 20)
                pygame.draw.rect(screen, trunk_col, (tx - 3, ty + 4, 6, 12))
                pygame.draw.circle(screen, canopy_col, (tx, ty), 14)
                pygame.draw.circle(screen, canopy_hi, (tx - 3, ty - 3), 6)
            elif kind in (2, 3, 4):
                # Grass tufts: a few short lines
                jx = ((seed >> 4) % 50) - 25
                jy = ((seed >> 8) % 50) - 25
                tx = tx_c + jx
                ty = ty_c + jy
                tuft_col = (60, 145, 70) if not blood_storm_active else (110, 25, 25)
                for _i in range(3):
                    dx = (((seed >> (10 + _i * 2)) & 7) - 3)
                    pygame.draw.line(screen, tuft_col, (tx + dx, ty + 3), (tx + dx, ty - 4), 1)
            # other seeds → empty grass


def draw_arena_spawn_hex():
    sx, sy = a2s(arena_spawn_wx, arena_spawn_wy)
    pts = [(sx + ARENA_SPAWN_R * math.cos(math.radians(i * 60)), sy + ARENA_SPAWN_R * math.sin(math.radians(i * 60))) for i in range(6)]
    pygame.draw.polygon(screen, (110, 110, 110), pts)
    pygame.draw.polygon(screen, WHITE, pts, 3)
    lbl = font_sm.render("SPAWN", True, WHITE)
    screen.blit(lbl, (sx - lbl.get_width() // 2, sy - 7))


def draw_arena_player():
    cx, cy = WIDTH // 2, HEIGHT // 2
    col = (200, 100, 255) if arena_player_iframes > 0 else (0, 200, 255)
    pygame.draw.circle(screen, col, (cx, cy), 15)
    pygame.draw.circle(screen, WHITE, (cx, cy), 15, 2)
    # Player health bar (above the player)
    PLAYER_MAX_HP = 100
    bar_w, bar_h = 50, 7
    bx = cx - bar_w // 2
    by = cy - 28
    ratio = max(0.0, min(1.0, arena_player_hp / PLAYER_MAX_HP))
    # Bar background
    pygame.draw.rect(screen, (40, 0, 0), (bx - 1, by - 1, bar_w + 2, bar_h + 2))
    pygame.draw.rect(screen, (90, 20, 20), (bx, by, bar_w, bar_h))
    # Filled portion — colour shifts red→yellow→green based on HP
    if ratio > 0.5:
        fill_col = (int(255 * (1 - (ratio - 0.5) * 2)), 220, 40)
    else:
        fill_col = (230, int(220 * (ratio * 2)), 40)
    pygame.draw.rect(screen, fill_col, (bx, by, int(bar_w * ratio), bar_h))
    pygame.draw.rect(screen, WHITE, (bx, by, bar_w, bar_h), 1)
    # HP number above the bar
    hp_lbl = font_tiny.render(f"{int(arena_player_hp)}/{PLAYER_MAX_HP}", True, WHITE)
    screen.blit(hp_lbl, (cx - hp_lbl.get_width() // 2, by - 12))


def draw_wall_upgrade_menu(wall):
    """TD wall upgrade panel — mirrors the arena wall menu."""
    global wall_upgrade_rect, wall_sell_rect, wall_close_rect
    sx, sy = int(wall.x), int(wall.y)
    mw, mh = 220, 160
    ox = min(max(sx + 20, 4), WIDTH - mw - 4)
    oy = max(62, min(sy + 20 if sy < HEIGHT // 2 else sy - mh - 20, HEIGHT - mh - 4))
    bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
    level_colors = {1: (55, 40, 15, 220), 2: (15, 30, 60, 220), 3: (35, 10, 55, 220)}
    edge_colors = {1: (220, 180, 80), 2: (100, 160, 255), 3: (180, 80, 255)}
    bg.fill(level_colors.get(wall.level, (20, 20, 20, 220)))
    screen.blit(bg, (ox, oy))
    pygame.draw.rect(screen, edge_colors.get(wall.level, GRAY), (ox, oy, mw, mh), 2)
    ec = edge_colors.get(wall.level, WHITE)
    screen.blit(font.render(f"Wall  Lv {wall.level}/{wall.max_level}", True, ec), (ox + 10, oy + 8))
    screen.blit(font_sm.render(f"HP: {int(wall.health)}/{wall.max_health}", True, (180, 255, 180)), (ox + 10, oy + 30))
    sell_val = int(wall.upgrade_cost_spent * 0.5 + get_wall_cost() * 0.5)
    wall_sell_rect = pygame.Rect(ox + 10, oy + 50, mw - 20, 20)
    pygame.draw.rect(screen, (100, 80, 15), wall_sell_rect, border_radius=4)
    pygame.draw.rect(screen, (200, 170, 40), wall_sell_rect, 1, border_radius=4)
    screen.blit(font_sm.render(f"Sell: {sell_val} coins  [click]", True, (255, 220, 80)), (ox + 14, oy + 53))
    if wall.level < wall.max_level:
        upg_cost = Wall.LEVEL_STATS[wall.level + 1]["cost"]
        can_afford = coins >= upg_cost
        bc = (0, 160, 0) if can_afford else (80, 80, 80)
        next_hp = Wall.LEVEL_STATS[wall.level + 1]["max_health"]
        if wall.level + 1 == 3:
            screen.blit(font_sm.render("Lv3: enemies repelled!", True, (200, 100, 255)), (ox + 10, oy + 78))
        else:
            screen.blit(font_sm.render(f"Next HP: {next_hp}", True, WHITE), (ox + 10, oy + 78))
        wall_upgrade_rect = pygame.Rect(ox + 10, oy + 100, 90, 32)
        pygame.draw.rect(screen, bc, wall_upgrade_rect, border_radius=6)
        screen.blit(font.render(f"Upg {upg_cost}", True, WHITE), (ox + 14, oy + 108))
    else:
        screen.blit(font.render("MAX LEVEL", True, YELLOW), (ox + 10, oy + 92))
        wall_upgrade_rect = None
    wall_close_rect = pygame.Rect(ox + mw - 92, oy + 100, 82, 32)
    pygame.draw.rect(screen, (160, 20, 20), wall_close_rect, border_radius=6)
    screen.blit(font.render("Close", True, WHITE), (ox + mw - 82, oy + 108))


def draw_arena_wall_upgrade_menu(wall):
    global arena_wall_upgrade_rect, arena_wall_sell_rect, arena_wall_close_rect
    sx, sy = a2s(wall.wx, wall.wy)
    mw, mh = 220, 160
    ox = min(max(sx + 20, 4), WIDTH - mw - 4)
    oy = max(62, min(sy + 20 if sy < HEIGHT // 2 else sy - mh - 20, HEIGHT - mh - 4))
    bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
    level_colors = {1: (55, 40, 15, 220), 2: (15, 30, 60, 220), 3: (35, 10, 55, 220)}
    edge_colors = {1: (220, 180, 80), 2: (100, 160, 255), 3: (180, 80, 255)}
    bg.fill(level_colors.get(wall.level, (20, 20, 20, 220)))
    screen.blit(bg, (ox, oy))
    pygame.draw.rect(screen, edge_colors.get(wall.level, GRAY), (ox, oy, mw, mh), 2)
    ec = edge_colors.get(wall.level, WHITE)
    screen.blit(font.render(f"Wall  Lv {wall.level}/{wall.max_level}", True, ec), (ox + 10, oy + 8))
    screen.blit(font_sm.render(f"HP: {int(wall.health)}/{wall.max_health}", True, (180, 255, 180)), (ox + 10, oy + 30))
    sell_val = int(wall.upgrade_cost_spent * 0.5 + 75)  # partial refund
    arena_wall_sell_rect = pygame.Rect(ox + 10, oy + 50, mw - 20, 20)
    pygame.draw.rect(screen, (100, 80, 15), arena_wall_sell_rect, border_radius=4)
    pygame.draw.rect(screen, (200, 170, 40), arena_wall_sell_rect, 1, border_radius=4)
    screen.blit(font_sm.render(f"Sell: {sell_val} coins  [click]", True, (255, 220, 80)), (ox + 14, oy + 53))
    if wall.level < wall.max_level:
        upg_cost = ArenaWall.LEVEL_STATS[wall.level + 1]["cost"]
        can_afford = arena_coins >= upg_cost
        bc = (0, 160, 0) if can_afford else (80, 80, 80)
        next_hp = ArenaWall.LEVEL_STATS[wall.level + 1]["max_health"]
        if wall.level + 1 == 3:
            screen.blit(font_sm.render("Lv3: enemies repelled!", True, (200, 100, 255)), (ox + 10, oy + 78))
        else:
            screen.blit(font_sm.render(f"Next HP: {next_hp}", True, WHITE), (ox + 10, oy + 78))
        arena_wall_upgrade_rect = pygame.Rect(ox + 10, oy + 100, 90, 32)
        pygame.draw.rect(screen, bc, arena_wall_upgrade_rect, border_radius=6)
        screen.blit(font.render(f"Upg {upg_cost}", True, WHITE), (ox + 14, oy + 108))
    else:
        screen.blit(font.render("MAX LEVEL", True, YELLOW), (ox + 10, oy + 92))
        arena_wall_upgrade_rect = None
    arena_wall_close_rect = pygame.Rect(ox + mw - 92, oy + 100, 82, 32)
    pygame.draw.rect(screen, (160, 20, 20), arena_wall_close_rect, border_radius=6)
    screen.blit(font.render("Close", True, WHITE), (ox + mw - 82, oy + 108))


def draw_arena_hud():
    global arena_wave_start_rect, arena_back_rect, arena_shop_btn_rect, blood_storm_info_rect, shadow_storm_info_rect
    global bestiary_rect, arena_nightmare_rect, arena_ranges_rect
    # HUD strip — dark red top bar (matches arena.png)
    pygame.draw.rect(screen, (95, 25, 25), (0, 0, WIDTH, 64))
    pygame.draw.rect(screen, (40, 10, 10), (0, 62, WIDTH, 2))

    # Buttons positioned left → right across the top bar
    btn_h = 36
    btn_y = 14
    x = 8

    # SHOP
    arena_shop_btn_rect = pygame.Rect(x, btn_y, 64, btn_h)
    pygame.draw.rect(screen, (180, 180, 180), arena_shop_btn_rect, border_radius=6)
    pygame.draw.rect(screen, (50, 50, 50), arena_shop_btn_rect, 2, border_radius=6)
    _l = font_sm.render("SHOP", True, BLACK)
    screen.blit(_l, _l.get_rect(center=arena_shop_btn_rect.center))
    x += 72

    # BESTIARY
    bestiary_rect = pygame.Rect(x, btn_y, 102, btn_h)
    pygame.draw.rect(screen, (60, 130, 145), bestiary_rect, border_radius=6)
    pygame.draw.rect(screen, (20, 60, 70), bestiary_rect, 2, border_radius=6)
    _l = font_sm.render("BESTIARY", True, BLACK)
    screen.blit(_l, _l.get_rect(center=bestiary_rect.center))
    x += 110

    # NIGHTMARE
    arena_nightmare_rect = pygame.Rect(x, btn_y, 100, btn_h)
    can_nm = not arena_wave_active and not arena_enemies
    nm_fill = (60, 30, 30) if not can_nm else ((180, 30, 30) if nightmare_mode else (110, 30, 30))
    pygame.draw.rect(screen, nm_fill, arena_nightmare_rect, border_radius=6)
    pygame.draw.rect(screen, (200, 60, 60), arena_nightmare_rect, 2, border_radius=6)
    _nm_label = "NIGHTMARE ON" if nightmare_mode else "NIGHTMARE"
    _nm_font = font_tiny if nightmare_mode else font_sm
    _nm_font.set_bold(True)
    _l = _nm_font.render(_nm_label, True, BLACK)
    _nm_font.set_bold(False)
    screen.blit(_l, _l.get_rect(center=arena_nightmare_rect.center))
    x += 108

    # ARENA MODE label + STORM INFO under it
    arena_lbl = font_sm.render("ARENA MODE", True, (255, 80, 80))
    screen.blit(arena_lbl, (x + 4, 2))
    if shadow_storm_active or blood_storm_active:
        _is_shadow = shadow_storm_active
        if _is_shadow:
            shadow_storm_info_rect = pygame.Rect(x, 22, arena_lbl.get_width() + 8, 22)
            blood_storm_info_rect = pygame.Rect(0, 0, 0, 0)
            pygame.draw.rect(screen, (60, 20, 80), shadow_storm_info_rect, border_radius=4)
            pygame.draw.rect(screen, (170, 80, 255), shadow_storm_info_rect, 2, border_radius=4)
            _sl = font_tiny.render("STORM INFO", True, (220, 180, 255))
            screen.blit(_sl, _sl.get_rect(center=shadow_storm_info_rect.center))
        else:
            blood_storm_info_rect = pygame.Rect(x, 22, arena_lbl.get_width() + 8, 22)
            shadow_storm_info_rect = pygame.Rect(0, 0, 0, 0)
            pygame.draw.rect(screen, (90, 20, 20), blood_storm_info_rect, border_radius=4)
            pygame.draw.rect(screen, (255, 80, 80), blood_storm_info_rect, 2, border_radius=4)
            _sl = font_tiny.render("STORM INFO", True, (255, 180, 180))
            screen.blit(_sl, _sl.get_rect(center=blood_storm_info_rect.center))
    else:
        shadow_storm_info_rect = pygame.Rect(0, 0, 0, 0)
        blood_storm_info_rect = pygame.Rect(0, 0, 0, 0)
    x += max(arena_lbl.get_width() + 12, 100)

    # START WAVE
    arena_wave_start_rect = pygame.Rect(x, btn_y, 116, btn_h)
    col2 = (80, 80, 80) if arena_wave_active else (90, 200, 90)
    pygame.draw.rect(screen, col2, arena_wave_start_rect, border_radius=6)
    pygame.draw.rect(screen, (20, 80, 20), arena_wave_start_rect, 2, border_radius=6)
    lbl2 = "ACTIVE..." if arena_wave_active else "START WAVE"
    wave_lbl = font_sm.render(lbl2, True, BLACK)
    screen.blit(wave_lbl, wave_lbl.get_rect(center=arena_wave_start_rect.center))
    x += 124

    # HP / WAVE / COINS info block (compact) — moved further left
    _info_x = max(x + 12, WIDTH - 220)
    screen.blit(font_tiny.render(f"HP: {arena_player_hp}", True, WHITE), (_info_x, 6))
    screen.blit(font_tiny.render(f"WAVE: {arena_wave}", True, WHITE), (_info_x, 22))
    screen.blit(font_tiny.render(f"COINS: {arena_coins}", True, GOLD), (_info_x, 38))

    # Ranges toggle (small) — placed below HUD bar so click area still works
    arena_ranges_rect = pygame.Rect(8, 70, 90, 22)
    if not arena_shop_open:
        _rg_col3 = (80, 160, 220) if show_ranges else (60, 80, 100)
        pygame.draw.rect(screen, _rg_col3, arena_ranges_rect, border_radius=6)
        screen.blit(font_tiny.render("Ranges ON" if show_ranges else "Ranges", True, WHITE), (14, arena_ranges_rect.y + 5))
    else:
        arena_ranges_rect = pygame.Rect(0, 0, 0, 0)

    # Back to menu button removed — use the user icon instead
    arena_back_rect = pygame.Rect(0, 0, 0, 0)
    return arena_back_rect


def draw_arena_shop():
    global arena_shop_x
    sx = arena_shop_x
    if sx <= -SHOP_W:
        return
    # Dark panel background per arenam.png
    pygame.draw.rect(screen, (52, 52, 56), (sx, 57, SHOP_W, HEIGHT - 57))
    pygame.draw.rect(screen, (28, 28, 30), (sx + SHOP_W - 2, 57, 2, HEIGHT - 57))
    tw = SHOP_W // 3
    for i, (tid, lbl) in enumerate([("towers", "Towers"), ("builder", "Builder"), ("guns", "Guns")]):
        active = arena_shop_tab == tid
        col = (210, 210, 215) if active else (74, 74, 80)
        pygame.draw.rect(screen, col, (sx + i * tw, 57, tw, 26))
        pygame.draw.rect(screen, (30, 30, 32), (sx + i * tw, 57, tw, 26), 1)
        tcol = BLACK if active else (220, 220, 220)
        screen.blit(font_sm.render(lbl, True, tcol), (sx + i * tw + 6, 62))
    if arena_shop_tab == "towers":
        items = [
            ("gunner", "Gunner", get_arena_tower_price("gunner"), 40),
            ("sniper", "Sniper", get_arena_tower_price("sniper"), 90),
            ("machine_gun", "MG", get_arena_tower_price("machine_gun"), 140),
            ("heavy_machine_gun", "HMG", get_arena_tower_price("heavy_machine_gun"), 190),
            ("airstrike", "Strike", get_arena_tower_price("airstrike"), 240),
            ("Goblin Hut", "Goblin Hut", get_arena_tower_price("Goblin Hut"), 290),
            ("close", "[Close]", 0, 340),
        ]
    elif arena_shop_tab == "builder":
        items = [
            ("frost_laser", "Frost Laser", get_arena_tower_price("frost_laser"), 40),
            ("builder_hut", "Builder Hut", get_arena_tower_price("builder_hut"), 90),
            ("wall", "Wall", get_wall_cost(), 140),
            ("Valkyrie Hut", "Valkyrie Hut", get_arena_tower_price("Valkyrie Hut"), 190),
            ("close", "[Close]", 0, 240),
        ]
    else:
        items = []
        y = 40
        for idx, gun in enumerate(ARENA_GUNS):
            if idx == 0:
                continue
            owned = arena_gun_level >= idx
            label = f"{gun['name']}" + (" EQUIPPED" if arena_gun_level == idx else (" OWNED" if owned else ""))
            items.append((f"gun:{idx}", label, 0 if owned else gun["cost"], y))
            y += 60
        items.append(("close", "[Close]", 0, y + 10))
    for tag, lbl, price, y in items:
        y2 = y + 57
        r = pygame.Rect(sx + 6, y2 + 24, SHOP_W - 12, 44)
        can = (tag == "close") or (arena_coins >= price)
        # Light-gray rounded card with red close
        if tag == "close":
            card_col = (170, 70, 70)
            edge_col = (220, 110, 110)
            text_col = WHITE
        elif can:
            card_col = (215, 215, 220)
            edge_col = (90, 90, 100)
            text_col = BLACK
        else:
            card_col = (110, 110, 115)
            edge_col = (60, 60, 65)
            text_col = (60, 60, 60)
        pygame.draw.rect(screen, card_col, r, border_radius=8)
        pygame.draw.rect(screen, edge_col, r, 1, border_radius=8)
        label_font = font_shop
        if tag.startswith("gun:") and ("OWNED" in lbl or "EQUIPPED" in lbl):
            label_font = font_shop_sm
        lbl_surf = label_font.render(lbl, True, text_col)
        if lbl_surf.get_width() > r.width - 12:
            lbl_surf = font_tiny.render(lbl, True, text_col)
        screen.blit(lbl_surf, (sx + 12, y2 + 28))
        if price > 0:
            cost_col = (60, 90, 60) if can else (180, 60, 60)
            screen.blit(font_tiny.render(f"COST: {price}", True, cost_col), (sx + 12, y2 + 50))
        elif tag.startswith("gun:"):
            idx = int(tag.split(":")[1])
            gun = ARENA_GUNS[idx]
            desc = f"{gun['damage']} dmg"
            if gun["auto"]:
                desc += " | hold SPACE"
            _ds = font_tiny.render(desc, True, (60, 60, 60))
            screen.blit(_ds, (sx + 12, y2 + 50))


def draw_arena_upgrade_menu(tower):
    global upgrade_menu_upgrade_rect, upgrade_menu_close_rect, upgrade_menu_sell_rect
    global upgrade_menu_move_rect, upgrade_menu_revive_rect
    sx, sy = a2s(tower.wx, tower.wy)
    lvl_index = tower.level - 1
    table = UPGRADE_TABLE.get(tower.type, [])
    at_max = tower.level >= tower.max_level
    info = table[lvl_index] if lvl_index < len(table) else None
    is_blood = bool(info and info.get("blood"))
    pristine_tier = info.get("pristine") if info else None
    is_pristine = bool(pristine_tier)
    mw, mh = 260, 240
    left_bound = (SHOP_W + 4) if arena_shop_x > -SHOP_W else 4
    ox = min(max(sx + 20, left_bound), WIDTH - mw - 4)
    oy = max(62, min(sy + 20 if sy < HEIGHT // 2 else sy - mh - 20, HEIGHT - mh - 4))
    PRISTINE_BG2 = {"bronze": ((60, 35, 10, 230), (200, 130, 40), (220, 150, 60)),
                    "silver": ((45, 45, 55, 230), (210, 210, 220), (220, 220, 230)),
                    "gold":   ((70, 55, 5, 230), (255, 200, 60), (255, 215, 80))}
    bg = pygame.Surface((mw, mh), pygame.SRCALPHA)
    if is_pristine:
        fill_col, edge_col, _t = PRISTINE_BG2[pristine_tier]
        bg.fill(fill_col)
    else:
        bg.fill((60, 0, 0, 220) if is_blood else (15, 15, 15, 220))
    screen.blit(bg, (ox, oy))
    if is_pristine:
        _f, edge_col, _t = PRISTINE_BG2[pristine_tier]
        pygame.draw.rect(screen, edge_col, (ox, oy, mw, mh), 3)
    else:
        pygame.draw.rect(screen, (200, 50, 50) if is_blood else GRAY, (ox, oy, mw, mh), 2)
    if is_pristine:
        title_col = PRISTINE_BG2[pristine_tier][2]
    else:
        title_col = (255, 80, 80) if is_blood else WHITE
    screen.blit(font.render(f"Tower: {tower.type}", True, title_col), (ox + 10, oy + 10))
    screen.blit(font.render(f"Level: {tower.level}/{tower.max_level}", True, YELLOW), (ox + 10, oy + 34))
    screen.blit(font.render(f"HP: {int(tower.health)}/{tower.max_health}", True, (180, 255, 180)), (ox + 10, oy + 56))
    # Lifetime kills counter (top-right of panel)
    _kills_txt = font_sm.render(f"Kills: {getattr(tower, 'kills', 0)}", True, (255, 200, 100))
    screen.blit(_kills_txt, (ox + mw - _kills_txt.get_width() - 10, oy + 38))
    sell_val = int((tower.cost + tower.upgrade_cost_spent) * 0.7)
    upgrade_menu_sell_rect = pygame.Rect(ox + 10, oy + 73, 116, 22)
    pygame.draw.rect(screen, (110, 85, 15), upgrade_menu_sell_rect, border_radius=4)
    pygame.draw.rect(screen, (200, 170, 40), upgrade_menu_sell_rect, 1, border_radius=4)
    screen.blit(font_sm.render(f"Sell {sell_val}", True, (255, 230, 100)), (ox + 14, oy + 76))
    move_cost = max(1, int((tower.cost + tower.upgrade_cost_spent) * 0.05))
    upgrade_menu_move_rect = pygame.Rect(ox + 134, oy + 73, 116, 22)
    mv_col = (40, 90, 140) if arena_coins >= move_cost else (60, 60, 60)
    pygame.draw.rect(screen, mv_col, upgrade_menu_move_rect, border_radius=4)
    pygame.draw.rect(screen, (120, 200, 255), upgrade_menu_move_rect, 1, border_radius=4)
    screen.blit(font_sm.render(f"Move {move_cost}", True, WHITE), (ox + 140, oy + 76))
    upgrade_menu_revive_rect = None
    if tower.type == "builder_hut" and len(getattr(tower, "builders", [])) < 1:
        rv_col = (0, 130, 0) if arena_coins >= 10000 else (60, 60, 60)
        upgrade_menu_revive_rect = pygame.Rect(ox + 10, oy + 168, 240, 22)
        pygame.draw.rect(screen, rv_col, upgrade_menu_revive_rect, border_radius=4)
        pygame.draw.rect(screen, (120, 255, 120), upgrade_menu_revive_rect, 1, border_radius=4)
        screen.blit(font_sm.render("Revive Builder (10,000)", True, WHITE), (ox + 14, oy + 171))
    if tower.type == "Valkyrie Hut" and not getattr(tower, "valk_built", True):
        prog = min(1.0, tower.valk_kills / max(1, tower.valk_kills_needed))
        screen.blit(font.render("Being built...", True, (255, 200, 60)), (ox + 10, oy + 96))
        screen.blit(font_sm.render(f"Kills: {tower.valk_kills}/{tower.valk_kills_needed}", True, (220, 200, 100)), (ox + 10, oy + 118))
        pygame.draw.rect(screen, (60, 40, 10), (ox + 10, oy + 138, 180, 8))
        pygame.draw.rect(screen, (255, 200, 50), (ox + 10, oy + 138, int(180 * prog), 8))
        screen.blit(font_sm.render("Upgrades locked until built", True, (180, 150, 80)), (ox + 10, oy + 152))
        upgrade_menu_upgrade_rect = None
    elif at_max:
        screen.blit(font.render("MAX LEVEL", True, YELLOW), (ox + 10, oy + 96))
        upgrade_menu_upgrade_rect = None
    elif info:
        if is_pristine and not shadow_storm_active:
            screen.blit(font.render("LOCKED: Shadow Storm", True, (200, 130, 255)), (ox + 10, oy + 96))
            screen.blit(font_sm.render("(Unlocks at wave 75)", True, (170, 110, 220)), (ox + 10, oy + 116))
            upgrade_menu_upgrade_rect = None
        elif is_blood and not blood_storm_active:
            screen.blit(font.render("LOCKED: Blood Storm", True, (255, 100, 100)), (ox + 10, oy + 96))
            screen.blit(font_sm.render("(Unlocks at wave 35)", True, (200, 100, 100)), (ox + 10, oy + 116))
            upgrade_menu_upgrade_rect = None
        else:
            desc = info.get("desc", "")
            if desc:
                desc_col = (255, 220, 120) if is_pristine else ((255, 150, 100) if is_blood else (180, 220, 255))
                screen.blit(font_tiny.render(desc, True, desc_col), (ox + 10, oy + 96))
            screen.blit(font.render(f"Cost: {info['cost']}", True, GREEN if arena_coins >= info["cost"] else RED), (ox + 10, oy + 114))
            if info["damage"]:
                screen.blit(font.render(f"Dmg: +{info['damage']}", True, WHITE), (ox + 10, oy + 134))
            if info["range"]:
                screen.blit(font.render(f"Range: +{info['range']}", True, WHITE), (ox + 10, oy + 154))
            if info["health"]:
                screen.blit(font.render(f"HP: +{info['health']}", True, WHITE), (ox + 10, oy + 172))
            is_combine = tower.type == "Valkyrie Hut" and tower.level == 3 and not tower.valk_combined
            PRISTINE_BTN2 = {"bronze": (200, 130, 40), "silver": (180, 180, 200), "gold": (230, 180, 40)}
            if is_pristine and arena_coins >= info["cost"]:
                bc = PRISTINE_BTN2[pristine_tier]
            elif is_blood and arena_coins >= info["cost"]:
                bc = (180, 0, 0)
            elif is_combine:
                bc = (120, 80, 180)
            elif arena_coins >= info["cost"]:
                bc = (0, 180, 0)
            else:
                bc = DARKGRAY
            upgrade_menu_upgrade_rect = pygame.Rect(ox + 10, oy + 196, 105, 36)
            pygame.draw.rect(screen, bc, upgrade_menu_upgrade_rect)
            if is_combine:
                lbl = "COMBINE!"
            elif is_pristine:
                lbl = pristine_tier.upper()
            elif is_blood:
                lbl = "BLOOD UP"
            else:
                lbl = "Upgrade"
            screen.blit(font.render(lbl, True, WHITE), (ox + 14, oy + 206))
    # Frost laser: show-circles toggle
    if tower.type == "frost_laser":
        global arena_frost_show_circles_rect
        fc = (40, 100, 200) if frost_show_circles else (35, 35, 70)
        arena_frost_show_circles_rect = pygame.Rect(ox + 10, oy + 178, 240, 16)
        pygame.draw.rect(screen, fc, arena_frost_show_circles_rect, border_radius=3)
        screen.blit(font_tiny.render("Show Circles: ON" if frost_show_circles else "Show Circles: OFF", True, WHITE), (ox + 14, oy + 180))
    upgrade_menu_close_rect = pygame.Rect(ox + 145, oy + 196, 104, 36)
    pygame.draw.rect(screen, (180, 0, 0), upgrade_menu_close_rect)
    screen.blit(font.render("Close", True, WHITE), (ox + 168, oy + 206))


def spawn_arena_enemy():
    # Boss wave: every 5 waves starting at wave 10 (same pattern as tower defense)
    if arena_wave >= 10 and arena_wave % 5 == 0 and arena_enemies_spawned == 0:
        boss_idx = ((arena_wave // 5) - 2) % len(BOSS_TYPE_MAP)
        bdata = BOSS_TYPE_MAP[boss_idx]
        b_color, b_tid, b_dmg, b_spd, b_reward, b_hp, b_sz, b_shape = bdata
        scale = 1.0 + (arena_wave - 10) * 0.05  # bosses scale with wave
        b_hp_scaled = int(b_hp * scale * (2 if nightmare_mode else 1))
        b_rew_scaled = int(b_reward * scale)
        e = ArenaEnemy(b_color, b_dmg, b_spd, b_rew_scaled, b_hp_scaled, radius=b_sz, type_id=b_tid, shape=b_shape)
        e.is_boss = True
        arena_enemies.append(e)
        _arena_discover_enemy(b_tid)
        # A boss wave also spawns normal enemies alongside
        return
    # Tower raider chance from wave 30
    if arena_wave >= 30 and random.random() < 0.25:
        h = 200 + arena_wave * 25
        if nightmare_mode:
            h *= 2
        _tr_col = random.choice(_TOWER_RAIDER_PALETTE)
        _tr_shp = random.choice(_TOWER_RAIDER_SHAPES)
        e = ArenaEnemy(_tr_col, 6, 1.6, 120 + arena_wave * 4, h, radius=14, type_id="tower_raider", shape=_tr_shp)
        arena_enemies.append(e)
        _arena_discover_enemy("tower_raider")
        return
    eligible = [e for e in ENEMY_TYPE_MAP if arena_wave >= e[6]]
    if not eligible:
        eligible = [ENEMY_TYPE_MAP[0]]
    chosen = random.choice(eligible)
    color, tid, dmg, spd, r_bonus, h_bonus, _, vis, shape, _ = chosen
    # Blood storm ramps damage and speed
    dmg_m = 2.0 if blood_storm_active else 1.0
    spd_m = 1.5 if blood_storm_active else 1.0
    health = max(10, 30 + arena_wave * 4 + h_bonus)
    if blood_storm_active:
        health = int(health * 2)
    if nightmare_mode:
        health = int(health * 2)
    reward = 20 + arena_wave * 2 + r_bonus
    e = ArenaEnemy(color, int(dmg * dmg_m), min(5.0, spd * spd_m), reward, health, radius=12, type_id=tid, shape=shape, visible_to=vis)
    arena_enemies.append(e)
    _arena_discover_enemy(tid)


def _arena_discover_enemy(tid):
    if tid not in discovered_enemies:
        discovered_enemies.add(tid)
        achievement_queue.append((f"New creature: {tid.replace('_', ' ').title()} added to Bestiary!", time.time() + 4.0))


# ── Main loop ─────────────────────────────────────────────────────────────────
while running:
    clock.tick(60)
    # Shared coin pool — TD and Arena draw from the same wallet
    if state == "GAME":
        arena_coins = coins
    elif state == "ARENA":
        coins = arena_coins
    if shadow_storm_active and state == "GAME":
        bg_color = (35, 0, 60)  # Shadow Storm purple
    elif blood_storm_active and state == "GAME":
        bg_color = (45, 0, 0)
    else:
        bg_color = DARK_BG
    screen.fill(bg_color)

    # ── State: MENU ──────────────────────────────────────────────────────────
    if state == "MENU":
        draw_main_menu()
        if logged_in_user:
            user_rect = draw_logged_in_user(bottom_right=True)
            if logout_menu_open:
                logout_rect_obj, return_rect_obj, admin_panel_rect_obj, mobile_mode_menu_rect = draw_logout_menu(user_rect.x, user_rect.y)
        if leaderboard_open:
            draw_leaderboard()

    elif state == "ADMIN_PANEL":
        admin_back_rect, admin_logout_rect = draw_admin_panel()

    elif state == "LOGIN":
        username_input.update()
        password_input.update()
        draw_login_screen(username_input, password_input)
        back_button_rect = draw_back_button()
        # Mobile Mode toggle on login screen
        _mb_col = (20, 140, 60) if mobile_mode else (70, 70, 70)
        _mb_lbl = "Mobile: ON" if mobile_mode else "Mobile: OFF"
        _mob_btn = pygame.Rect(WIDTH - 150, 12, 138, 34)
        pygame.draw.rect(screen, _mb_col, _mob_btn, border_radius=6)
        screen.blit(font_sm.render(_mb_lbl, True, WHITE), font_sm.render(_mb_lbl, True, WHITE).get_rect(center=_mob_btn.center))
        mobile_mode_menu_rect = _mob_btn
        if mobile_mode and (username_input.active or password_input.active):
            draw_onscreen_keyboard()

    elif state == "SIGNUP":
        username_input.update()
        password_input.update()
        draw_signup_screen(username_input, password_input)
        back_button_rect = draw_back_button()
        # Mobile Mode toggle on signup screen
        _mb_col = (20, 140, 60) if mobile_mode else (70, 70, 70)
        _mb_lbl = "Mobile: ON" if mobile_mode else "Mobile: OFF"
        _mob_btn = pygame.Rect(WIDTH - 150, 12, 138, 34)
        pygame.draw.rect(screen, _mb_col, _mob_btn, border_radius=6)
        screen.blit(font_sm.render(_mb_lbl, True, WHITE), font_sm.render(_mb_lbl, True, WHITE).get_rect(center=_mob_btn.center))
        mobile_mode_menu_rect = _mob_btn
        if mobile_mode and (username_input.active or password_input.active):
            draw_onscreen_keyboard()

    elif state == "ARENA":
        # ── Arena draw / update ───────────────────────────────────────────────
        draw_arena_background()

        # Virtual D-pad: poll held mouse button each frame (mobile touch support)
        _vpad_key_map = {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d}
        for _k in arena_vpad_held:
            arena_vpad_held[_k] = False
        if mobile_mode and not arena_shop_open and not skip_wave_open and arena_vpad_rects:
            _mx_v, _my_v = pygame.mouse.get_pos()
            _held = pygame.mouse.get_pressed()[0]
            if _held:
                for _vdir, _vr in arena_vpad_rects.items():
                    if _vr.collidepoint(_mx_v, _my_v):
                        arena_vpad_held[_vpad_key_map[_vdir]] = True
                if arena_vpad_fire_rect.collidepoint(_mx_v, _my_v):
                    if arena_shoot_cd <= 0 and arena_player_hp > 0:
                        arena_fire_player_weapon()

        # Move player with WASD (keyboard OR virtual D-pad)
        spd = ARENA_PLAYER_SPEED * (2 if speed_2x else 1)
        if arena_keys[pygame.K_a] or arena_vpad_held[pygame.K_a]:
            arena_cam_x -= spd
        if arena_keys[pygame.K_d] or arena_vpad_held[pygame.K_d]:
            arena_cam_x += spd
        if arena_keys[pygame.K_w] or arena_vpad_held[pygame.K_w]:
            arena_cam_y -= spd
        if arena_keys[pygame.K_s] or arena_vpad_held[pygame.K_s]:
            arena_cam_y += spd

        # Draw spawn hex
        draw_arena_spawn_hex()

        # Update / draw arena walls
        for aw in arena_walls[:]:
            aw.draw()
            if aw.health <= 0:
                arena_walls.remove(aw)

        # Enemies attack walls (all arena enemies chip at walls at damage*5/sec)
        # and slide along walls instead of getting stuck on them.
        for ae in arena_enemies:
            if not ae.alive:
                continue
            for aw in arena_walls:
                if aw.health <= 0:
                    continue
                _repel_d = math.hypot(ae.wx - aw.wx, ae.wy - aw.wy)
                _contact_thresh = ae.radius + ArenaWall.R
                if _repel_d < _contact_thresh:
                    # All arena enemies damage walls at damage*5 per second (bosses 30x)
                    _aw_mul = 30.0 if getattr(ae, "is_boss", False) else 1.0
                    aw.health -= ae.damage * 5.0 / 60.0 * _aw_mul * (2 if speed_2x else 1)
                # Level 3 walls also slide non-raider enemies along the wall (so they
                # don't bounce in place — they walk past it toward the player)
                if (not ae.is_tower_raider) and aw.level >= 3:
                    _repel_thresh = ae.radius + ArenaWall.W / 2 + 4
                    if _repel_d < _repel_thresh and _repel_d > 0.1:
                        _aw_rad = math.radians(aw.angle)
                        _wall_tx = math.cos(_aw_rad)
                        _wall_ty = math.sin(_aw_rad)
                        # Direction toward the player
                        _pdx = arena_cam_x - ae.wx
                        _pdy = arena_cam_y - ae.wy
                        _tang_sign = 1 if (_wall_tx * _pdx + _wall_ty * _pdy) >= 0 else -1
                        _perp_x = -_wall_ty
                        _perp_y = _wall_tx
                        _ex = ae.wx - aw.wx
                        _ey = ae.wy - aw.wy
                        _perp_dot = _ex * _perp_x + _ey * _perp_y
                        _push_dir = 1 if _perp_dot >= 0 else -1
                        _overlap = _repel_thresh - _repel_d
                        # Smaller perpendicular push + tangent slide toward player
                        ae.wx += _perp_x * _push_dir * _overlap * 0.35 + _wall_tx * _tang_sign * 0.8
                        ae.wy += _perp_y * _push_dir * _overlap * 0.35 + _wall_ty * _tang_sign * 0.8

        # Reset frost slow for arena enemies each frame
        for _ae2 in arena_enemies:
            _ae2.frost_slow_mult = 1.0
        # Compute aura debuffs on arena towers
        for _at in arena_towers:
            _at.aura_fire_mult = 1.0
            for _ae in arena_enemies:
                if not _ae.alive:
                    continue
                _d2 = math.hypot(_at.wx - _ae.wx, _at.wy - _ae.wy)
                if _ae.type_id == "null_specter" and _d2 < 120:
                    _at.aura_fire_mult = max(_at.aura_fire_mult, 2.0)
                if _ae.type_id == "frost_giant" and _d2 < 150:
                    _at.aura_fire_mult = max(_at.aura_fire_mult, 4.0)
                if _ae.type_id == "frost_weaver" and _d2 < 160:
                    _at.aura_fire_mult = max(_at.aura_fire_mult, 3.0)
                if _ae.type_id == "gravity_slug" and _d2 < 180:
                    _at.aura_fire_mult = max(_at.aura_fire_mult, 5.0)
                if _ae.type_id == "glacial_creep" and _d2 < 180:
                    _at.aura_fire_mult = max(_at.aura_fire_mult, 4.0)
                if _ae.type_id == "shadow_priest" and _d2 < 140:
                    _at.aura_fire_mult = max(_at.aura_fire_mult, 2.5)

        # Update / draw arena towers (draw pass only — HP bars drawn later)
        _mx_at, _my_at = pygame.mouse.get_pos()
        dead_arena_towers = []
        for at in arena_towers:
            at.update_valkyrie_hut(arena_enemies)
            at.shoot(arena_enemies)
            # Draw bullets
            for _b in at.bullets:
                _b.draw()
            at.draw()
            # Show range circle on hover or when show_ranges is on
            _sx_at, _sy_at = a2s(at.wx, at.wy)
            if show_ranges or math.hypot(_sx_at - _mx_at, _sy_at - _my_at) <= 13:
                _rc = at._color_map.get(at.type, (100, 100, 100))
                _rc2 = tuple(min(255, v + 80) for v in _rc)
                pygame.draw.circle(screen, _rc2, (_sx_at, _sy_at), at.range, 1)
            if at.health <= 0:
                dead_arena_towers.append(at)
        for at in dead_arena_towers:
            arena_towers.remove(at)

        # Update / draw arena enemies
        pending_arena = []
        for ae in arena_enemies[:]:
            ae.update()
            ae.draw()
            # Crypt walker revival
            if ae.health <= 0 and ae.type_id == "crypt_walker" and not ae.revived:
                ae.health = ae.max_health * 0.5
                ae.revived = True
                continue
            if not ae.alive or ae.health <= 0:
                # Death effects
                arena_coins += int(ae.reward * (5 if nightmare_mode else 1))
                # Track kills for Valkyrie Hut construction in arena
                for _avt in arena_towers:
                    if _avt.type == "Valkyrie Hut" and not _avt.valk_built:
                        _avt.valk_kills += 1
                        if _avt.valk_kills >= _avt.valk_kills_needed:
                            _avt.valk_built = True
                            for _i in range(3):
                                _v0 = Valkyrie(_avt.wx + random.randint(-20, 20), _avt.wy + random.randint(-20, 20), "minion_focus")
                                _v0.arena_mode = True
                                _v0.speed = _avt.valk_speed
                                _v0.home_x = _avt.wx
                                _v0.home_y = _avt.wy
                                _avt.valkyries.append(_v0)
                if ae.type_id == "spectral_wolf":
                    pack_howl_frames = 300
                if ae.type_id == "blood_spawn":
                    for _ in range(2):
                        ch = ArenaEnemy((220, 40, 50), 2, 1.8, int(ae.reward * 0.4), max(10, int(ae.max_health / 3)), radius=10, type_id="blood_spawn_child", shape="circle")
                        pending_arena.append(ch)
                if ae.type_id == "plague_moth":
                    for _ in range(3):
                        ch = ArenaEnemy((100, 180, 50), 2, 1.8, 30, max(10, int(ae.max_health / 4)), radius=9, type_id="plague_rat", shape="star")
                        pending_arena.append(ch)
                if ae.type_id == "mirror_wisp":
                    for _ in range(2):
                        ch = ArenaEnemy((210, 240, 255), 2, 2.8, int(ae.reward * 0.35), max(10, int(ae.max_health / 4)), radius=9, type_id="mirror_fragment", shape="diamond")
                        pending_arena.append(ch)
                arena_enemies.remove(ae)
        arena_enemies.extend(pending_arena)
        # HP bars for ALL entities drawn last so they appear on top of everything
        for at in arena_towers:
            at.draw_health_bar()
        for ae in arena_enemies:
            if ae.alive and ae.health > 0:
                ae.draw_health_bar()

        # Player bullets
        if arena_shoot_cd > 0:
            arena_shoot_cd -= 2 if speed_2x else 1
        if arena_player_iframes > 0:
            arena_player_iframes -= 1

        for ab in arena_p_bullets[:]:
            ab.update()
            ab.draw()
            if not ab.alive:
                arena_p_bullets.remove(ab)

        # Draw player centred
        draw_arena_player()

        if pygame.key.get_pressed()[pygame.K_SPACE] and ARENA_GUNS[arena_gun_level]["auto"]:
            arena_fire_player_weapon()

        # Place preview
        mx_p, my_p = pygame.mouse.get_pos()
        if arena_placing_tower:
            pygame.draw.circle(screen, (255, 255, 100), (mx_p, my_p), 14, 2)
        elif arena_placing_wall:
            _pw_surf = pygame.Surface((ArenaWall.W, ArenaWall.H), pygame.SRCALPHA)
            _pw_surf.fill((0, 0, 0, 0))
            pygame.draw.rect(_pw_surf, (200, 180, 80), (0, 0, ArenaWall.W, ArenaWall.H), 2)
            _pw_rot = pygame.transform.rotate(_pw_surf, -arena_wall_rot)
            screen.blit(_pw_rot, (mx_p - _pw_rot.get_width() // 2, my_p - _pw_rot.get_height() // 2))
            screen.blit(font_sm.render(f"Rot: {arena_wall_rot}deg  </>/> rotate", True, (220, 220, 80)), (mx_p + 20, my_p - 10))

        if arena_valkyrie_combine_mode:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((80, 40, 0, 120))
            screen.blit(ov, (0, 0))
            msg = font.render("Click a MAX-LEVEL Goblin Hut to COMBINE  [ESC to cancel]", True, (255, 220, 80))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 62))
            for at in arena_towers:
                if at.type == "Goblin Hut" and at.level >= at.max_level:
                    asx, asy = a2s(at.wx, at.wy)
                    pygame.draw.circle(screen, (255, 220, 80), (asx, asy), 20, 3)

        if arena_combine_anim_timer > 0 and arena_combine_anim_pos:
            prog = 1 - (arena_combine_anim_timer / 60)
            r = int(30 + 70 * prog)
            alpha = max(0, 255 - int(255 * prog))
            sx_ca, sy_ca = a2s(arena_combine_anim_pos[0], arena_combine_anim_pos[1])
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 200, 50, alpha), (r, r), r)
            screen.blit(s, (sx_ca - r, sy_ca - r))
            arena_combine_anim_timer -= 2 if speed_2x else 1

        if arena_selected_tower_obj and arena_selected_tower_obj in arena_towers and not arena_valkyrie_combine_mode:
            asx, asy = a2s(arena_selected_tower_obj.wx, arena_selected_tower_obj.wy)
            pygame.draw.circle(screen, YELLOW, (asx, asy), 18, 3)
            draw_arena_upgrade_menu(arena_selected_tower_obj)
        else:
            if not arena_valkyrie_combine_mode:
                arena_selected_tower_obj = None
            upgrade_menu_upgrade_rect = None
            upgrade_menu_close_rect = None

        if arena_selected_wall_obj and arena_selected_wall_obj in arena_walls:
            wsx, wsy = a2s(arena_selected_wall_obj.wx, arena_selected_wall_obj.wy)
            pygame.draw.circle(screen, (255, 220, 80), (wsx, wsy), 22, 3)
            draw_arena_wall_upgrade_menu(arena_selected_wall_obj)
        else:
            arena_selected_wall_obj = None
            arena_wall_upgrade_rect = None
            arena_wall_close_rect = None

        # Wave spawning
        if arena_wave_active:
            if arena_enemy_timer == 0 and arena_enemies_spawned < arena_enemies_to_spawn:
                spawn_arena_enemy()
                arena_enemies_spawned += 1
                arena_enemy_timer = 45
            else:
                arena_enemy_timer = max(0, arena_enemy_timer - (2 if speed_2x else 1))
            if arena_enemies_spawned == arena_enemies_to_spawn and not arena_enemies:
                arena_wave_active = False
                arena_wave += 1
                # Activate blood storm at wave 35 in arena
                if arena_wave == 35 and not blood_storm_active:
                    blood_storm_active = True
                    blood_storm_splash_timer = 300
                # Activate shadow storm at wave 75 in arena
                if arena_wave >= 75 and not shadow_storm_active:
                    shadow_storm_active = True
                    shadow_storm_splash_timer = 300
                    shadow_storm_info_open = True

        # Game over
        if arena_player_hp <= 0:
            arena_player_hp = 0
            blood_storm_active = False
            blood_storm_splash_timer = 0
            blood_storm_info_open = False
            shadow_storm_active = False
            shadow_storm_splash_timer = 0
            shadow_storm_info_open = False
            # Draw game over overlay
            go = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            go.fill((0, 0, 0, 170))
            screen.blit(go, (0, 0))
            lgo = font_lg.render("ARENA OVER", True, RED)
            screen.blit(lgo, (WIDTH // 2 - lgo.get_width() // 2, HEIGHT // 2 - 40))
            lw2 = font.render(f"Reached Wave {arena_wave}", True, WHITE)
            screen.blit(lw2, (WIDTH // 2 - lw2.get_width() // 2, HEIGHT // 2 + 10))
            lrt = font.render("Press R to restart  |  Menu button to exit", True, GRAY)
            screen.blit(lrt, (WIDTH // 2 - lrt.get_width() // 2, HEIGHT // 2 + 45))

        # Shop slide
        if arena_shop_open and arena_shop_x < 0:
            arena_shop_x = min(0, arena_shop_x + 15)
        elif not arena_shop_open and arena_shop_x > -SHOP_W:
            arena_shop_x = max(-SHOP_W, arena_shop_x - 15)

        # Blood / Shadow storm drawn before shop so the shop panel overlays it
        draw_blood_storm_splash()
        draw_shadow_storm_splash()
        draw_arena_shop()
        draw_arena_hud()

        # User icon + logout (arena)
        if logged_in_user:
            user_rect = draw_logged_in_user()
            if logout_menu_open:
                logout_rect_obj, return_rect_obj, admin_panel_rect_obj, mobile_mode_menu_rect = draw_logout_menu(user_rect.x, user_rect.y)

        # Virtual D-pad (only in mobile mode)
        if mobile_mode and not arena_shop_open:
            draw_arena_vpad()

        # Admin skip-wave dialog (arena)
        if skip_wave_open:
            draw_skip_wave_dialog()

        # Bestiary overlay (arena)
        if bestiary_open:
            bestiary_close_rect, bestiary_tab_rects, bestiary_up_rect, bestiary_down_rect = draw_bestiary(in_arena=True)

    elif state == "GAME":
        # Shop slide
        if shop_open and shop_x < 0:
            shop_x = min(0, shop_x + shop_slide_speed)
        elif not shop_open and shop_x > -SHOP_W:
            shop_x = max(-SHOP_W, shop_x - shop_slide_speed)

        # Path — clean thin gray line (no joint blobs)
        if len(path) >= 2:
            pygame.draw.lines(screen, (90, 90, 95), False, path, 8)
            pygame.draw.lines(screen, (160, 160, 170), False, path, 4)

        # Walls — enemies damage walls on contact AND sidestep them
        for w in walls[:]:
            w.draw()
            if w.health <= 0:
                walls.remove(w)
                continue
            for e in enemies:
                if e.health <= 0:
                    continue
                _wd = math.hypot(e.x - w.x, e.y - w.y)
                if _wd < e.radius + w.R:
                    # Chip the wall: damage*5 per second (bosses crush walls 30x faster)
                    _wall_dps_mul = 30.0 if getattr(e, "is_boss", False) else 1.0
                    w.health -= e.damage * 5.0 / 60.0 * _wall_dps_mul * (2 if speed_2x else 1)
                    # Sidestep around the wall: push perpendicular to enemy's forward dir
                    _pi = getattr(e, "path_index", 0)
                    if _pi < len(path) - 1 and _wd > 0.1:
                        _nx, _ny = path[_pi + 1]
                        _fdx = _nx - e.x
                        _fdy = _ny - e.y
                        _fl = math.hypot(_fdx, _fdy) or 1
                        _fdx /= _fl
                        _fdy /= _fl
                        _perp_x, _perp_y = -_fdy, _fdx
                        _side_dot = (e.x - w.x) * _perp_x + (e.y - w.y) * _perp_y
                        _side = 1 if _side_dot >= 0 else -1
                        _push = (e.radius + w.R - _wd) * 0.5
                        e.x += _perp_x * _side * (_push + 0.4)
                        e.y += _perp_y * _side * (_push + 0.4)
                # Level 3 walls also slide enemies along the wall toward the next path node
                if w.level >= 3:
                    _repel_thresh = e.radius + w.W / 2 + 4
                    if _wd < _repel_thresh and _wd > 0.1:
                        _w_rad = math.radians(w.angle)
                        _wall_tx = math.cos(_w_rad)
                        _wall_ty = math.sin(_w_rad)
                        _pi = getattr(e, "path_index", 0)
                        if _pi < len(path) - 1:
                            _nx, _ny = path[_pi + 1]
                            _pdx = _nx - e.x
                            _pdy = _ny - e.y
                        else:
                            _pdx, _pdy = 0, 0
                        _tang_sign = 1 if (_wall_tx * _pdx + _wall_ty * _pdy) >= 0 else -1
                        _perp_x = -_wall_ty
                        _perp_y = _wall_tx
                        _ex = e.x - w.x
                        _ey = e.y - w.y
                        _perp_dot = _ex * _perp_x + _ey * _perp_y
                        _push_dir = 1 if _perp_dot >= 0 else -1
                        _overlap = _repel_thresh - _wd
                        e.x += _perp_x * _push_dir * _overlap * 0.35 + _wall_tx * _tang_sign * 0.8
                        e.y += _perp_y * _push_dir * _overlap * 0.35 + _wall_ty * _tang_sign * 0.8

        # Bombs
        for b in bombs[:]:
            b.draw()
            if b.check(enemies):
                bombs.remove(b)

        # Placement preview
        if placing_tower and selected_tower:
            mx2, my2 = pygame.mouse.get_pos()
            r2 = {"gunner": 100, "sniper": 200, "machine_gun": 90, "heavy_machine_gun": 180, "airstrike": 350, "Goblin Hut": 0, "builder_hut": 0}.get(selected_tower, 0)
            cc = {
                "gunner": (0, 0, 255, 100),
                "sniper": (0, 0, 150, 100),
                "machine_gun": (0, 150, 0, 100),
                "heavy_machine_gun": (100, 50, 0, 100),
                "Goblin Hut": GREEN + tuple(),
                "airstrike": ORANGE + tuple(),
                "builder_hut": (180, 140, 50),
            }.get(selected_tower, (128, 128, 128))
            if r2 > 0:
                s2 = pygame.Surface((r2 * 2, r2 * 2), pygame.SRCALPHA)
                pygame.draw.circle(s2, cc[:4] if len(cc) == 4 else cc + (100,), (r2, r2), r2, 2)
                screen.blit(s2, (mx2 - r2, my2 - r2))
            pygame.draw.circle(screen, cc[:3], (mx2, my2), 15, 2)
        elif placing_wall:
            mx2, my2 = pygame.mouse.get_pos()
            _pw_surf = pygame.Surface((Wall.W, Wall.H), pygame.SRCALPHA)
            pygame.draw.rect(_pw_surf, (180, 140, 80, 120), (0, 0, Wall.W, Wall.H))
            pygame.draw.rect(_pw_surf, (220, 180, 80), (0, 0, Wall.W, Wall.H), 2)
            _pw_rot = pygame.transform.rotate(_pw_surf, -wall_rot)
            screen.blit(_pw_rot, (mx2 - _pw_rot.get_width() // 2, my2 - _pw_rot.get_height() // 2))
            screen.blit(font_sm.render(f"Rot: {wall_rot}deg  arrows rotate", True, (220, 220, 80)), (mx2 + 20, my2 - 10))
        elif placing_bomb:
            mx2, my2 = pygame.mouse.get_pos()
            pygame.draw.circle(screen, (255, 60, 0), (mx2, my2), Bomb.TRIGGER_R, 2)

        # Spawn enemies
        if wave_active:
            if enemy_timer == 0 and enemies_spawned < enemies_to_spawn:
                spawn_enemy(wave_number)
                enemies_spawned += 1
                enemy_timer = spawn_interval
            else:
                enemy_timer = max(0, enemy_timer - 1)

        # Move / draw / prune enemies
        pending_spawns = []
        for e in enemies[:]:
            e.move()
            e.draw()
            for m in e.minions[:]:
                m.update(towers, towers)
                if m.health <= 0:
                    e.minions.remove(m)
            if e.health <= 0:
                # Crypt Walker one-time revival
                if e.type_id == "crypt_walker" and not getattr(e, "revived", False):
                    e.health = int(e.max_health * 0.5)
                    e.revived = True
                    continue
                if e.is_boss:
                    hp += 5
                coins += e.reward * (5 if nightmare_mode else 1)
                # Track kills for Valkyrie Hut construction
                for _vt in towers:
                    if _vt.type == "Valkyrie Hut" and not _vt.valk_built:
                        _vt.valk_kills += 1
                        if _vt.valk_kills >= _vt.valk_kills_needed:
                            _vt.valk_built = True
                            for _i in range(3):
                                _v = Valkyrie(_vt.x + random.randint(-20, 20), _vt.y + random.randint(-20, 20), "minion_focus")
                                _v.speed = _vt.valk_speed
                                _v.home_x = _vt.x
                                _v.home_y = _vt.y
                                _vt.valkyries.append(_v)
                # Spectral Wolf pack howl on death
                if e.type_id == "spectral_wolf":
                    pack_howl_frames = 300
                if e.plague_rat:
                    for _ in range(3):
                        ch = Enemy((120, 200, 60), 1, 2.2, 5, max(10, e.max_health // 2), type_id="plague_child", shape="star")
                        ch.x = e.x + random.randint(-20, 20)
                        ch.y = e.y + random.randint(-20, 20)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                if getattr(e, "abomination", False):
                    for _ in range(2):
                        ch = Enemy((130, 30, 100), 4, 1.2, int(e.reward * 0.4), max(20, e.max_health // 3), type_id="abomination_child", shape="pentagon")
                        ch.x = e.x + random.randint(-25, 25)
                        ch.y = e.y + random.randint(-25, 25)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                if getattr(e, "type_id", "") == "boss_7":
                    for _ in range(10):
                        ch = Enemy((100, 180, 50), 2, 1.8, 50, max(10, e.max_health // 10), type_id="plague_rat", shape="star")
                        ch.plague_rat = True
                        ch.x = e.x + random.randint(-40, 40)
                        ch.y = e.y + random.randint(-40, 40)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                if getattr(e, "blood_spawn", False):
                    for _ in range(2):
                        ch = Enemy((220, 40, 50), 2, 1.8, int(e.reward * 0.4), max(10, e.max_health // 3), type_id="blood_spawn_child", shape="circle")
                        ch.x = e.x + random.randint(-20, 20)
                        ch.y = e.y + random.randint(-20, 20)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                # Crimson Stalker: splits into 3 on death
                if e.type_id == "crimson_stalker":
                    for _ in range(3):
                        ch = Enemy((230, 60, 80), 3, 2.0, int(e.reward * 0.3), max(10, e.max_health // 4), type_id="crimson_fragment", shape="circle")
                        ch.x = e.x + random.randint(-25, 25)
                        ch.y = e.y + random.randint(-25, 25)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                # Boss 12 (Abyssal Titan): revives once, spawns void fragments on final death
                if e.type_id == "boss_12":
                    if not getattr(e, "revived", False):
                        e.health = int(e.max_health * 0.5)
                        e.revived = True
                        continue
                    for _ in range(4):
                        ch = Enemy((20, 0, 50), 6, 0.5, int(e.reward * 0.15), max(100, e.max_health // 8), type_id="void_fragment", shape="diamond")
                        ch.x = e.x + random.randint(-50, 50)
                        ch.y = e.y + random.randint(-50, 50)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                if getattr(e, "plague_moth", False):
                    for _ in range(3):
                        ch = Enemy((100, 180, 50), 2, 1.8, 30, max(10, e.max_health // 4), type_id="plague_rat", shape="star")
                        ch.plague_rat = True
                        ch.x = e.x + random.randint(-25, 25)
                        ch.y = e.y + random.randint(-25, 25)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                if e.type_id == "mirror_wisp":
                    for _ in range(2):
                        ch = Enemy((210, 240, 255), 2, 2.8, int(e.reward * 0.35), max(10, e.max_health // 4), type_id="mirror_fragment", shape="diamond")
                        ch.x = e.x + random.randint(-18, 18)
                        ch.y = e.y + random.randint(-18, 18)
                        ch.path_index = e.path_index
                        pending_spawns.append(ch)
                enemies.remove(e)
            elif not e.is_tower_raider and e.reached_end():
                hp -= e.damage * (3 if nightmare_mode else 1)
                enemies.remove(e)
                if hp <= 0:
                    # Record leaderboard entry before reset
                    if not is_admin and logged_in_user:
                        update_leaderboard(logged_in_user, wave_number, coins, nightmare=nightmare_locked)
                    # Game over reset
                    blood_storm_active = False
                    blood_storm_splash_timer = 0
                    blood_storm_info_open = False
                    shadow_storm_active = False
                    shadow_storm_splash_timer = 0
                    shadow_storm_info_open = False
                    wave_active = False
                    enemies.clear()
                    towers.clear()
                    coins_list.clear()
                    walls.clear()
                    bombs.clear()
                    coins = 400
                    hp = 20
                    wave_number = 1
                    enemies_spawned = 0
                    enemies_to_spawn = 0
                    nightmare_locked = False
                    placing_tower = False
                    placing_wall = False
                    placing_bomb = False
                    selected_tower = None
                    selected_tower_object = None
                    shop_open = False
                    shop_x = -SHOP_W
                    walls_placed_count = 0
                    bombs_placed_count = 0
        enemies.extend(pending_spawns)

        # Fury beast speeds up as HP drops
        for e in enemies:
            if getattr(e, "fury_beast", False):
                ratio = e.health / max(1, e.max_health)
                e.speed = e._base_speed * (1.0 + (1.0 - ratio) * 2.0) if hasattr(e, "_base_speed") else e.speed
                if not hasattr(e, "_base_speed"):
                    e._base_speed = e.speed

        # Pack howl countdown
        if pack_howl_frames > 0:
            pack_howl_frames = max(0, pack_howl_frames - (2 if speed_2x else 1))

        if wave_active and enemies_spawned == enemies_to_spawn and not enemies:
            wave_active = False
            wave_number += 1
            # Activate Blood Storm at wave 35
            if wave_number == 35 and not blood_storm_active:
                blood_storm_active = True
                blood_storm_splash_timer = 300  # 5 seconds of full-screen title
            # Activate Shadow Storm at wave 75 (replaces Blood Storm theme)
            if wave_number == 75 and not shadow_storm_active:
                shadow_storm_active = True
                shadow_storm_splash_timer = 300  # 5 seconds of full-screen title

        # Towers — pre-compute null_specter / frost_giant aura debuffs
        for _e2 in enemies:
            _e2.frost_slow_mult = 1.0
        for _t in towers:
            _t.aura_fire_mult = 1.0
            for _e in enemies:
                if _e.health <= 0:
                    continue
                _d = math.hypot(_t.x - _e.x, _t.y - _e.y)
                if _e.type_id == "null_specter" and _d < 120:
                    _t.aura_fire_mult = max(_t.aura_fire_mult, 2.0)
                if _e.type_id == "frost_giant" and _d < 150:
                    _t.aura_fire_mult = max(_t.aura_fire_mult, 4.0)
                if _e.type_id == "frost_weaver" and _d < 160:
                    _t.aura_fire_mult = max(_t.aura_fire_mult, 3.0)
                if _e.type_id == "gravity_slug" and _d < 180:
                    _t.aura_fire_mult = max(_t.aura_fire_mult, 5.0)
                if _e.type_id == "glacial_creep" and _d < 180:
                    _t.aura_fire_mult = max(_t.aura_fire_mult, 4.0)
                if _e.type_id == "shadow_priest" and _d < 140:
                    _t.aura_fire_mult = max(_t.aura_fire_mult, 2.5)

        mouse_pos = pygame.mouse.get_pos()
        dead_towers = []
        for t in towers:
            t.shoot(enemies)
            t.draw()
            if show_ranges or math.hypot(t.x - mouse_pos[0], t.y - mouse_pos[1]) <= 15:
                t.draw_range()
            if t.health <= 0:
                coins_list.append(Coin(t.x, t.y, t.cost // 2))
                dead_towers.append(t)
        for t in dead_towers:
            towers.remove(t)

        # Coins
        for c2 in coins_list:
            if not c2.collected:
                c2.draw(screen)
        coins_list = [c2 for c2 in coins_list if not c2.collected]

        # Health bar second pass — always drawn on top of all game sprites
        for e in enemies:
            if e.health > 0:
                e.draw_health_bar()
        for t in towers:
            t.draw_health_bar()

        # ── HUD (top-bar buttons + stats) drawn last so nothing covers it ─────
        draw_ui()

        # Combine mode overlay
        if valkyrie_combine_mode:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((80, 40, 0, 120))
            screen.blit(ov, (0, 0))
            msg = font.render("Click a MAX-LEVEL Goblin Hut to COMBINE  [ESC to cancel]", True, (255, 220, 80))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, 8))
            for t in towers:
                if t.type == "Goblin Hut" and t.level >= t.max_level:
                    pygame.draw.circle(screen, (255, 220, 80), (t.x, t.y), 20, 3)

        # Combine animation
        if combine_anim_timer > 0 and combine_anim_pos:
            prog = 1 - (combine_anim_timer / 60)
            r = int(30 + 70 * prog)
            alpha = max(0, 255 - int(255 * prog))
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 200, 50, alpha), (r, r), r)
            screen.blit(s, (combine_anim_pos[0] - r, combine_anim_pos[1] - r))
            combine_anim_timer -= 2 if speed_2x else 1

        # Selected tower overlay
        if selected_tower_object and not valkyrie_combine_mode:
            pygame.draw.circle(screen, YELLOW, (selected_tower_object.x, selected_tower_object.y), 18, 3)
            draw_upgrade_menu(selected_tower_object)
        else:
            upgrade_menu_upgrade_rect = None
            upgrade_menu_close_rect = None

        # Selected wall overlay + upgrade/sell panel
        if selected_wall and selected_wall in walls:
            _wsel_surf = pygame.Surface((selected_wall.W + 6, selected_wall.H + 6), pygame.SRCALPHA)
            pygame.draw.rect(_wsel_surf, YELLOW, (0, 0, selected_wall.W + 6, selected_wall.H + 6), 2)
            _wsel_rot = pygame.transform.rotate(_wsel_surf, -selected_wall.angle)
            screen.blit(_wsel_rot, (selected_wall.x - _wsel_rot.get_width() // 2, selected_wall.y - _wsel_rot.get_height() // 2))
            draw_wall_upgrade_menu(selected_wall)
        else:
            selected_wall = None
            sell_rect_wall = None
            wall_upgrade_rect = None
            wall_sell_rect = None
            wall_close_rect = None

        # Blood / Shadow Storm splash overlay (drawn before shop so shop covers it)
        draw_blood_storm_splash()
        draw_shadow_storm_splash()

        # Shop (drawn on top of blood storm info button)
        if shop_x > -SHOP_W:
            draw_shop()

        # Bestiary overlay
        if bestiary_open:
            bestiary_close_rect, bestiary_tab_rects, bestiary_up_rect, bestiary_down_rect = draw_bestiary()

        draw_achievements()

        # User icon
        if logged_in_user:
            user_rect = draw_logged_in_user()
            if logout_menu_open:
                logout_rect_obj, return_rect_obj, admin_panel_rect_obj, mobile_mode_menu_rect = draw_logout_menu(user_rect.x, user_rect.y)

        # Admin skip-wave dialog
        if skip_wave_open:
            draw_skip_wave_dialog()

        # Shop tooltip — drawn last so it's in front of everything
        if _pending_shop_tooltip:
            tb, ts, tx, ty = _pending_shop_tooltip
            screen.blit(tb, (tx, ty))
            screen.blit(ts, (tx + 5, ty + 3))

    # Admin starts with 400 coins like a regular player. Use the
    # command console (`set coins N`) to grant more if needed.

    # ── Global overlays (draw on top of everything) ───────────────────────────
    _ci = _cr = _cc = pygame.Rect(0, 0, 0, 0)
    ce_back_r = ce_help_r = ce_sub_r = ce_help_close_r = pygame.Rect(0, 0, 0, 0)
    ce_prev_shape_r = ce_next_shape_r = ce_ab_prev_r = ce_ab_next_r = pygame.Rect(0, 0, 0, 0)
    ce_shape_disp_r = ce_help_up_r = ce_help_dn_r = pygame.Rect(0, 0, 0, 0)
    ce_field_rects = {}
    ce_ab_param_rects = {}
    ce_all_filled = False
    if cmd_console_open and is_admin:
        _ci, _cr, _cc = draw_cmd_console()

    if create_entity_open and is_admin:
        (ce_back_r, ce_help_r, ce_field_rects, ce_shape_disp_r,
         ce_prev_shape_r, ce_next_shape_r, ce_ab_prev_r, ce_ab_next_r,
         ce_ab_param_rects, ce_all_filled, ce_sub_r,
         ce_help_close_r, ce_help_up_r, ce_help_dn_r) = draw_create_entity_menu()

    pygame.display.flip()

    # ── Events ────────────────────────────────────────────────────────────────
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ── Global admin overlays (cmd console + create entity) ──────────────────
        if cmd_console_open and is_admin:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    cmd_console_open = False
                elif event.key == pygame.K_RETURN:
                    process_command(cmd_console_str)
                    cmd_console_str = ""
                elif event.key == pygame.K_BACKSPACE:
                    cmd_console_str = cmd_console_str[:-1]
                else:
                    cmd_console_str += event.unicode
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                if _cc.collidepoint(mx2, my2):
                    cmd_console_open = False
                elif _cr.collidepoint(mx2, my2):
                    process_command(cmd_console_str)
                    cmd_console_str = ""
            continue

        if create_entity_open and is_admin:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    create_entity_open = False
                elif event.key == pygame.K_BACKSPACE:
                    if create_entity_active_field and create_entity_active_field.startswith("ab_"):
                        pk = create_entity_active_field[3:]
                        create_entity_ab_params[pk] = create_entity_ab_params.get(pk, "")[:-1]
                    elif create_entity_active_field in create_entity_fields:
                        create_entity_fields[create_entity_active_field] = create_entity_fields[create_entity_active_field][:-1]
                else:
                    ch = event.unicode
                    if create_entity_active_field and create_entity_active_field.startswith("ab_"):
                        pk = create_entity_active_field[3:]
                        create_entity_ab_params[pk] = create_entity_ab_params.get(pk, "") + ch
                    elif create_entity_active_field in create_entity_fields:
                        create_entity_fields[create_entity_active_field] += ch
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                if ce_back_r.collidepoint(mx2, my2):
                    create_entity_open = False
                    cmd_console_open = True
                elif ce_help_r.collidepoint(mx2, my2):
                    create_entity_help_open = not create_entity_help_open
                    create_entity_help_scroll = 0
                elif create_entity_help_open:
                    if ce_help_close_r and ce_help_close_r.collidepoint(mx2, my2):
                        create_entity_help_open = False
                    elif ce_help_up_r and ce_help_up_r.collidepoint(mx2, my2):
                        create_entity_help_scroll = max(0, create_entity_help_scroll - 56)
                    elif ce_help_dn_r and ce_help_dn_r.collidepoint(mx2, my2):
                        create_entity_help_scroll += 56
                elif ce_sub_r.collidepoint(mx2, my2) and ce_all_filled:
                    submit_custom_entity()
                elif ce_prev_shape_r.collidepoint(mx2, my2):
                    create_entity_shape_idx = (create_entity_shape_idx - 1) % len(_CE_SHAPES)
                    create_entity_shape = _CE_SHAPES[create_entity_shape_idx]
                elif ce_next_shape_r.collidepoint(mx2, my2):
                    create_entity_shape_idx = (create_entity_shape_idx + 1) % len(_CE_SHAPES)
                    create_entity_shape = _CE_SHAPES[create_entity_shape_idx]
                elif ce_ab_prev_r.collidepoint(mx2, my2):
                    ab_idx = _ABILITY_NAMES.index(create_entity_ability) if create_entity_ability in _ABILITY_NAMES else 0
                    ab_idx = (ab_idx - 1) % len(_ABILITY_NAMES)
                    create_entity_ability = "" if _ABILITY_NAMES[ab_idx] == "(none)" else _ABILITY_NAMES[ab_idx]
                    create_entity_ab_params = {}
                elif ce_ab_next_r.collidepoint(mx2, my2):
                    ab_idx = _ABILITY_NAMES.index(create_entity_ability) if create_entity_ability in _ABILITY_NAMES else 0
                    ab_idx = (ab_idx + 1) % len(_ABILITY_NAMES)
                    create_entity_ability = "" if _ABILITY_NAMES[ab_idx] == "(none)" else _ABILITY_NAMES[ab_idx]
                    create_entity_ab_params = {}
                else:
                    create_entity_active_field = None
                    for fk, fr in ce_field_rects.items():
                        if fr.collidepoint(mx2, my2):
                            create_entity_active_field = fk
                            break
                    if create_entity_active_field is None:
                        for pk2, (fr2, _param) in ce_ab_param_rects.items():
                            if fr2.collidepoint(mx2, my2):
                                create_entity_active_field = pk2
                                break
            elif event.type == pygame.MOUSEWHEEL and create_entity_help_open:
                create_entity_help_scroll = max(0, create_entity_help_scroll - event.y * 30)
            continue

        elif state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                # User icon + logout (always handled first in menu)
                if logged_in_user and user_rect.collidepoint(mx2, my2):
                    logout_menu_open = not logout_menu_open
                elif logout_menu_open and logout_rect_obj.collidepoint(mx2, my2):
                    do_logout()
                elif logout_menu_open and admin_panel_rect_obj and admin_panel_rect_obj.collidepoint(mx2, my2):
                    # "Command" button in admin logout menu (MENU state) -> open cmd console
                    logout_menu_open = False
                    cmd_console_open = True
                    cmd_console_str = ""
                    cmd_console_output = ""
                    cmd_console_help_shown = False
                elif logout_menu_open and return_rect_obj.collidepoint(mx2, my2):
                    logout_menu_open = False
                elif logout_menu_open and mobile_mode_menu_rect.collidepoint(mx2, my2):
                    mobile_mode = not mobile_mode
                    logout_menu_open = False
                elif logout_menu_open:
                    logout_menu_open = False
                # Leaderboard overlay
                elif leaderboard_open:
                    if leaderboard_close_rect.collidepoint(mx2, my2):
                        leaderboard_open = False
                    else:
                        for tid, tr in leaderboard_tab_rects.items():
                            if tr.collidepoint(mx2, my2):
                                leaderboard_tab = tid
                                leaderboard_scroll = 0
                # Handle path shop panel clicks first
                elif path_shop_open:
                    hit_path = False
                    for pid, (action, rect) in menu_path_rects.items():
                        if rect.collidepoint(mx2, my2):
                            hit_path = True
                            pdata = next((p for p in PATHS if p["id"] == pid), None)
                            if pdata and action == "buy":
                                user_coins = users.get(logged_in_user, {}).get("coins", 0)
                                if user_coins >= pdata["cost"]:
                                    users[logged_in_user]["coins"] = user_coins - pdata["cost"]
                                    owned_path_ids.add(pid)
                                    selected_path_id = pid
                                    if logged_in_user in users:
                                        users[logged_in_user]["owned_paths"] = list(owned_path_ids)
                                        users[logged_in_user]["selected_path"] = selected_path_id
                                        save_users()
                            elif action == "select":
                                selected_path_id = pid
                                if logged_in_user in users:
                                    users[logged_in_user]["selected_path"] = selected_path_id
                                    save_users()
                            break
                    if not hit_path:
                        path_shop_open = False
                elif logged_in_user and pygame.Rect(10, 10, 130, 44).collidepoint(mx2, my2):
                    # ARENA MODE button (top-bar left) — preserves prior arena state
                    state = "ARENA"
                elif logged_in_user and pygame.Rect(150, 10, 200, 44).collidepoint(mx2, my2):
                    # PLAY button (top-bar)
                    pdata = next((p for p in PATHS if p["id"] == selected_path_id), PATHS[0])
                    path[:] = list(pdata["points"])
                    if logged_in_user == "admin":
                        coins = users.get(logged_in_user, {}).get("coins", 400)
                    state = "GAME"
                elif logged_in_user and pygame.Rect(360, 10, 200, 44).collidepoint(mx2, my2):
                    # LEADERBOARD button (top-bar)
                    leaderboard_open = True
                    leaderboard_scroll = 0
                elif logged_in_user and pygame.Rect(WIDTH - 130, 10, 120, 44).collidepoint(mx2, my2):
                    # SHOP button (top-bar) -> opens path shop
                    path_shop_open = not path_shop_open
                elif (not logged_in_user) and WIDTH // 2 - 100 <= mx2 <= WIDTH // 2 + 100:
                    if 280 <= my2 <= 330:
                        login_error = ""
                        username_input.text = ""
                        password_input.text = ""
                        state = "LOGIN"
                    elif 350 <= my2 <= 400:
                        signup_error = ""
                        username_input.text = ""
                        password_input.text = ""
                        state = "SIGNUP"
                else:
                    path_shop_open = False
            elif event.type == pygame.MOUSEWHEEL and leaderboard_open:
                leaderboard_scroll = max(0, leaderboard_scroll - event.y * 20)

        elif state == "ADMIN_PANEL":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                if admin_back_rect.collidepoint(mx2, my2):
                    state = "MENU"
                elif admin_logout_rect.collidepoint(mx2, my2):
                    do_logout()
                else:
                    for uname, rect in list(admin_delete_buttons.items()):
                        if rect.collidepoint(mx2, my2):
                            del users[uname]
                            save_users()
                            break

        elif state in ("LOGIN", "SIGNUP"):
            username_input.handle_event(event)
            password_input.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                # On-screen keyboard handling
                active_box = username_input if username_input.active else (
                             password_input if password_input.active else None)
                if active_box and onscreen_kb_rects:
                    for kb_label, kb_r in onscreen_kb_rects.items():
                        if kb_r.collidepoint(mx2, my2):
                            if kb_label == "BACK":
                                active_box.text = active_box.text[:-1]
                            elif kb_label == "SPACE":
                                active_box.text += " "
                            elif kb_label == "SHIFT":
                                kb_shift = not kb_shift
                            elif kb_label == "GO":
                                # Trigger submit — synthesise via a flag below
                                mx2, my2 = WIDTH // 2, 320  # redirect to submit button coords
                                break
                            elif len(kb_label) == 1:
                                active_box.text += kb_label.upper() if kb_shift else kb_label
                                if kb_shift:
                                    kb_shift = False   # auto-lowercase after one char
                            active_box.txt_surface = active_box.font.render(
                                "*" * len(active_box.text) if active_box.is_password else active_box.text,
                                True, active_box.color)
                            break
                if mobile_mode_menu_rect.collidepoint(mx2, my2):
                    mobile_mode = not mobile_mode
                elif back_button_rect.collidepoint(mx2, my2):
                    login_error = ""
                    signup_error = ""
                    state = "MENU"
                elif WIDTH // 2 - 75 <= mx2 <= WIDTH // 2 + 75 and 300 <= my2 <= 340:
                    uname = username_input.text.strip()
                    pw = hash_password(password_input.text)
                    if state == "LOGIN":
                        if uname == "admin" and pw == hash_password("dominous7"):
                            logged_in_user = "admin"
                            is_admin = True
                            coins = 400
                            arena_coins = 400
                            login_error = ""
                            reset_bestiary()
                            state = "MENU"
                        elif uname in users and users[uname]["password"] == pw:
                            logged_in_user = uname
                            coins = users[uname].get("coins", 400)
                            owned_path_ids.clear()
                            owned_path_ids.update(users[uname].get("owned_paths", ["default"]))
                            selected_path_id = users[uname].get("selected_path", "default")
                            is_admin = False
                            login_error = ""
                            reset_bestiary()
                            state = "MENU"
                        else:
                            login_error = "Invalid username or password."
                    else:  # SIGNUP
                        if not uname:
                            signup_error = "Username cannot be empty."
                        elif uname == "admin":
                            signup_error = "Reserved username."
                        elif uname in users:
                            signup_error = "Username taken."
                        else:
                            users[uname] = {"password": pw, "high_score": 0, "coins": 400}
                            save_users()
                            logged_in_user = uname
                            is_admin = False
                            signup_error = ""
                            reset_bestiary()
                            state = "MENU"

        elif state == "ARENA":
            if event.type == pygame.KEYDOWN:
                if skip_wave_open:
                    if event.key == pygame.K_ESCAPE:
                        skip_wave_open = False
                        skip_wave_str = ""
                    elif event.key == pygame.K_RETURN:
                        try:
                            target = max(1, int(skip_wave_str))
                            arena_wave = target
                            arena_wave_active = False
                            arena_enemies.clear()
                            arena_enemies_spawned = 0
                            arena_enemies_to_spawn = 0
                            if arena_wave >= 35 and not blood_storm_active:
                                blood_storm_active = True
                                blood_storm_splash_timer = 300
                                blood_storm_info_open = True
                            if arena_wave >= 75 and not shadow_storm_active:
                                shadow_storm_active = True
                                shadow_storm_splash_timer = 300
                                shadow_storm_info_open = True
                        except ValueError:
                            pass
                        skip_wave_open = False
                        skip_wave_str = ""
                    elif event.key == pygame.K_BACKSPACE:
                        skip_wave_str = skip_wave_str[:-1]
                    elif event.unicode.isdigit():
                        if len(skip_wave_str) < 4:
                            skip_wave_str += event.unicode
                    continue
                if event.key in arena_keys:
                    arena_keys[event.key] = True
                if event.key == pygame.K_SPACE and arena_shoot_cd <= 0 and arena_player_hp > 0:
                    arena_fire_player_weapon()
                if event.key == pygame.K_r and arena_player_hp <= 0:
                    if not is_admin and logged_in_user:
                        update_leaderboard(logged_in_user, arena_wave, arena_coins, arena=True)
                    reset_arena()
                if event.key == pygame.K_ESCAPE:
                    arena_placing_tower = None
                    arena_placing_wall = False
                    arena_valkyrie_combine_mode = False
                    arena_valkyrie_combine_hut = None
                    if bestiary_open:
                        bestiary_open = False
                if arena_selected_tower_obj:
                    if event.key == pygame.K_s:
                        sell_val = int((arena_selected_tower_obj.cost + arena_selected_tower_obj.upgrade_cost_spent) * 0.7)
                        arena_coins += sell_val
                        if arena_selected_tower_obj in arena_towers:
                            arena_towers.remove(arena_selected_tower_obj)
                        arena_selected_tower_obj = None
                    elif event.key == pygame.K_u:
                        if arena_selected_tower_obj.type == "Valkyrie Hut" and not getattr(arena_selected_tower_obj, "valk_built", True):
                            pass  # Cannot upgrade while still being built
                        elif arena_selected_tower_obj.type == "Valkyrie Hut" and arena_selected_tower_obj.level == 3 and not arena_selected_tower_obj.valk_combined:
                            arena_valkyrie_combine_mode = True
                            arena_valkyrie_combine_hut = arena_selected_tower_obj
                            arena_selected_tower_obj = None
                        else:
                            arena_selected_tower_obj.upgrade()
                # Arrow keys rotate wall during placement
                if arena_placing_wall:
                    if event.key == pygame.K_LEFT:
                        arena_wall_rot = (arena_wall_rot - 15) % 360
                    elif event.key == pygame.K_RIGHT:
                        arena_wall_rot = (arena_wall_rot + 15) % 360
                    elif event.key == pygame.K_UP:
                        arena_wall_rot = (arena_wall_rot - 45) % 360
                    elif event.key == pygame.K_DOWN:
                        arena_wall_rot = (arena_wall_rot + 45) % 360
            elif event.type == pygame.KEYUP:
                if event.key in arena_keys:
                    arena_keys[event.key] = False
            elif event.type == pygame.MOUSEWHEEL and bestiary_open:
                bestiary_scroll = max(0, bestiary_scroll - event.y * 20)
                continue
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                if arena_valkyrie_combine_mode:
                    for _at in arena_towers[:]:
                        _asx, _asy = a2s(_at.wx, _at.wy)
                        if _at.type == "Goblin Hut" and _at.level >= _at.max_level and math.hypot(_asx - mx2, _asy - my2) <= 20:
                            arena_combine_anim_pos = (_at.wx, _at.wy)
                            arena_combine_anim_timer = 60
                            arena_towers.remove(_at)
                            if arena_valkyrie_combine_hut:
                                arena_valkyrie_combine_hut.valk_combined = True
                                arena_valkyrie_combine_hut.level = min(arena_valkyrie_combine_hut.max_level, arena_valkyrie_combine_hut.level + 1)
                                arena_valkyrie_combine_hut.max_health += 800
                                arena_valkyrie_combine_hut.health += 800
                                arena_valkyrie_combine_hut.valk_speed = 6.0
                                arena_valkyrie_combine_hut.valkyries = []
                                for _i in range(5):
                                    _mode = "raider_focus" if _i >= 2 else "minion_focus"
                                    _v = Valkyrie(arena_valkyrie_combine_hut.wx + random.randint(-25, 25), arena_valkyrie_combine_hut.wy + random.randint(-25, 25), _mode)
                                    _v.arena_mode = True
                                    _v.speed = arena_valkyrie_combine_hut.valk_speed
                                    _v.damage = 600
                                    _v.max_health = 1200
                                    _v.health = 1200
                                    _v.home_x = arena_valkyrie_combine_hut.wx
                                    _v.home_y = arena_valkyrie_combine_hut.wy
                                    arena_valkyrie_combine_hut.valkyries.append(_v)
                            break
                    arena_valkyrie_combine_mode = False
                    arena_valkyrie_combine_hut = None
                    continue
                # Bestiary overlay swallows all clicks when open
                if bestiary_open:
                    if bestiary_close_rect.collidepoint(mx2, my2):
                        bestiary_open = False
                    else:
                        for _tid, _tr in bestiary_tab_rects.items():
                            if _tr.collidepoint(mx2, my2):
                                bestiary_tab = _tid
                                bestiary_scroll = 0
                        if bestiary_up_rect.collidepoint(mx2, my2):
                            bestiary_scroll = max(0, bestiary_scroll - 40)
                        if bestiary_down_rect.collidepoint(mx2, my2):
                            bestiary_scroll += 40
                    continue
                # User icon + logout (checked before all others)
                if skip_wave_open:
                    continue
                if logged_in_user and user_rect.collidepoint(mx2, my2):
                    logout_menu_open = not logout_menu_open
                    continue
                if logout_menu_open and logout_rect_obj.collidepoint(mx2, my2):
                    if logged_in_user and logged_in_user in users:
                        users[logged_in_user]["coins"] = arena_coins
                        save_users()
                    do_logout()
                    continue
                if logout_menu_open and is_admin and skip_wave_rect_obj.collidepoint(mx2, my2):
                    logout_menu_open = False
                    skip_wave_open = True
                    skip_wave_str = ""
                    continue
                if logout_menu_open and admin_panel_rect_obj and admin_panel_rect_obj.collidepoint(mx2, my2):
                    logout_menu_open = False
                    cmd_console_open = True
                    cmd_console_str = ""
                    cmd_console_output = ""
                    cmd_console_help_shown = False
                    continue
                if logout_menu_open and return_rect_obj.collidepoint(mx2, my2):
                    if logged_in_user and logged_in_user in users:
                        users[logged_in_user]["coins"] = arena_coins
                        save_users()
                    if not is_admin and logged_in_user:
                        update_leaderboard(logged_in_user, arena_wave, arena_coins, arena=True)
                    logout_menu_open = False
                    coins = arena_coins
                    state = "MENU"
                    continue
                if logout_menu_open and mobile_mode_menu_rect.collidepoint(mx2, my2):
                    mobile_mode = not mobile_mode
                    logout_menu_open = False
                    continue
                if logout_menu_open:
                    logout_menu_open = False
                    continue
                # Blood Storm info popup close button (arena)
                if blood_storm_info_open and blood_storm_info_close_rect.collidepoint(mx2, my2):
                    blood_storm_info_open = False
                    continue
                # Shadow Storm info popup close button (arena)
                if shadow_storm_info_open and shadow_storm_info_close_rect.collidepoint(mx2, my2):
                    shadow_storm_info_open = False
                    continue

                if arena_selected_tower_obj and arena_selected_tower_obj in arena_towers:
                    if upgrade_menu_close_rect and upgrade_menu_close_rect.collidepoint(mx2, my2):
                        arena_selected_tower_obj = None
                        continue
                    if upgrade_menu_sell_rect and upgrade_menu_sell_rect.collidepoint(mx2, my2):
                        _sv2 = int((arena_selected_tower_obj.cost + arena_selected_tower_obj.upgrade_cost_spent) * 0.7)
                        arena_coins += _sv2
                        if arena_selected_tower_obj in arena_towers:
                            arena_towers.remove(arena_selected_tower_obj)
                        arena_selected_tower_obj = None
                        continue
                    if upgrade_menu_move_rect and upgrade_menu_move_rect.collidepoint(mx2, my2):
                        _mv_cost = max(1, int((arena_selected_tower_obj.cost + arena_selected_tower_obj.upgrade_cost_spent) * 0.05))
                        if arena_coins >= _mv_cost:
                            arena_coins -= _mv_cost
                            arena_moving_tower_obj = arena_selected_tower_obj
                            arena_selected_tower_obj = None
                        continue
                    if upgrade_menu_revive_rect and upgrade_menu_revive_rect.collidepoint(mx2, my2):
                        _bh = arena_selected_tower_obj
                        if _bh.type == "builder_hut" and len(getattr(_bh, "builders", [])) < 1 and arena_coins >= 10000:
                            arena_coins -= 10000
                            try:
                                nb = Builder(_bh.wx, _bh.wy, getattr(_bh, "builder_upgraded", False))
                                for _lv in range(1, _bh.level + 1):
                                    _apply_builder_level(nb, _lv)
                                _bh.builders.append(nb)
                                _bh.builder_respawn_wave = 0
                            except Exception:
                                pass
                        continue
                    if arena_selected_tower_obj.type == "frost_laser" and arena_frost_show_circles_rect.collidepoint(mx2, my2):
                        frost_show_circles = not frost_show_circles
                        continue
                    if upgrade_menu_upgrade_rect and upgrade_menu_upgrade_rect.collidepoint(mx2, my2):
                        if arena_selected_tower_obj.type == "Valkyrie Hut" and not getattr(arena_selected_tower_obj, "valk_built", True):
                            pass
                        elif arena_selected_tower_obj.type == "Valkyrie Hut" and arena_selected_tower_obj.level == 3 and not arena_selected_tower_obj.valk_combined:
                            arena_valkyrie_combine_mode = True
                            arena_valkyrie_combine_hut = arena_selected_tower_obj
                            arena_selected_tower_obj = None
                        else:
                            arena_selected_tower_obj.upgrade()
                        continue
                # Back button
                if arena_back_rect.collidepoint(mx2, my2):
                    coins = arena_coins
                    if logged_in_user and logged_in_user in users:
                        users[logged_in_user]["coins"] = arena_coins
                        save_users()
                    blood_storm_active = False
                    blood_storm_splash_timer = 0
                    blood_storm_info_open = False
                    shadow_storm_active = False
                    shadow_storm_splash_timer = 0
                    shadow_storm_info_open = False
                    state = "MENU"
                # Wave start
                elif arena_wave_start_rect.collidepoint(mx2, my2) and not arena_wave_active:
                    arena_wave_active = True
                    arena_enemies_spawned = 0
                    arena_enemies_to_spawn = 5 + arena_wave * 2
                    arena_enemy_timer = 0
                # Shop button
                elif not arena_shop_open and arena_shop_btn_rect.collidepoint(mx2, my2):
                    arena_shop_open = True
                elif shadow_storm_active and not arena_shop_open and shadow_storm_info_rect.collidepoint(mx2, my2):
                    shadow_storm_info_open = not shadow_storm_info_open
                elif blood_storm_active and not shadow_storm_active and not arena_shop_open and blood_storm_info_rect.collidepoint(mx2, my2):
                    blood_storm_info_open = not blood_storm_info_open
                # Shop panel interactions
                elif arena_shop_x <= mx2 <= arena_shop_x + SHOP_W and my2 >= 57:
                    tw2 = SHOP_W // 3
                    if 57 <= my2 <= 83:
                        if mx2 < arena_shop_x + tw2:
                            arena_shop_tab = "towers"
                        elif mx2 < arena_shop_x + tw2 * 2:
                            arena_shop_tab = "builder"
                        else:
                            arena_shop_tab = "guns"
                    else:
                        if arena_shop_tab == "towers":
                            btns2 = [
                                ("gunner", 40),
                                ("sniper", 90),
                                ("machine_gun", 140),
                                ("heavy_machine_gun", 190),
                                ("airstrike", 240),
                                ("Goblin Hut", 290),
                                ("close", 340),
                            ]
                        elif arena_shop_tab == "builder":
                            btns2 = [
                                ("frost_laser", 40),
                                ("builder_hut", 90),
                                ("wall", 140),
                                ("Valkyrie Hut", 190),
                                ("close", 240),
                            ]
                        else:
                            btns2 = [(f"gun:{idx}", 40 + (idx - 1) * 60) for idx in range(1, len(ARENA_GUNS))]
                            btns2.append(("close", 40 + (len(ARENA_GUNS) - 1) * 60 + 10))
                        for tag2, y2 in btns2:
                            if y2 + 57 + 24 <= my2 <= y2 + 57 + 68:
                                if tag2 == "close":
                                    arena_shop_open = False
                                elif tag2.startswith("gun:"):
                                    idx = int(tag2.split(":")[1])
                                    gun = ARENA_GUNS[idx]
                                    if arena_gun_level >= idx or arena_coins >= gun["cost"]:
                                        if arena_gun_level < idx:
                                            arena_coins -= gun["cost"]
                                        arena_gun_level = idx
                                elif tag2 == "wall":
                                    c_wall = get_wall_cost()
                                    if arena_coins >= c_wall:
                                        arena_placing_wall = True
                                        arena_placing_tower = None
                                else:
                                    p2 = get_arena_tower_price(tag2)
                                    if arena_coins >= p2:
                                        arena_placing_tower = tag2
                                        arena_placing_wall = False
                                break
                # Place tower
                elif arena_moving_tower_obj is not None:
                    if arena_moving_tower_obj in arena_towers:
                        wx_m, wy_m = s2a(mx2, my2)
                        arena_moving_tower_obj.wx = wx_m
                        arena_moving_tower_obj.wy = wy_m
                        if hasattr(arena_moving_tower_obj, "home_wx"):
                            arena_moving_tower_obj.home_wx = wx_m
                        if hasattr(arena_moving_tower_obj, "home_wy"):
                            arena_moving_tower_obj.home_wy = wy_m
                        for _b in getattr(arena_moving_tower_obj, "builders", []):
                            if hasattr(_b, "home_wx"):
                                _b.home_wx = wx_m
                                _b.home_wy = wy_m
                    arena_moving_tower_obj = None
                elif arena_placing_tower:
                    p3 = get_arena_tower_price(arena_placing_tower)
                    if arena_coins >= p3:
                        if arena_placing_tower == "Valkyrie Hut" and not any(at.type == "builder_hut" for at in arena_towers):
                            pass  # requires builder_hut first
                        else:
                            stats2 = {
                                "gunner": (100, 10, 60),
                                "sniper": (200, 70, 120),
                                "machine_gun": (90, 20, 3),
                                "heavy_machine_gun": (180, 40, 5),
                                "airstrike": (350, 100, 200),
                                "frost_laser": (130, 0, 25),
                                "Goblin Hut": (0, 0, 600),
                                "builder_hut": (0, 0, 600),
                                "Valkyrie Hut": (0, 0, 0),
                            }
                            r4, d4, cd4 = stats2.get(arena_placing_tower, (100, 10, 60))
                            wx4, wy4 = s2a(mx2, my2)
                            arena_towers.append(ArenaTower(wx4, wy4, r4, d4, cd4, arena_placing_tower, p3))
                            arena_coins -= p3
                    arena_placing_tower = None
                # Place wall
                elif arena_placing_wall:
                    c2 = get_wall_cost()
                    if arena_coins >= c2:
                        wx5, wy5 = s2a(mx2, my2)
                        hd = ArenaWall.W / 2 + 4
                        overlap = any(math.hypot(aw.wx - wx5, aw.wy - wy5) < hd for aw in arena_walls)
                        if not overlap:
                            arena_walls.append(ArenaWall(wx5, wy5, arena_wall_rot))
                            arena_coins -= c2
                    arena_placing_wall = False
                # Bestiary toggle (top bar)
                elif not arena_shop_open and bestiary_rect.collidepoint(mx2, my2):
                    bestiary_open = not bestiary_open
                # Nightmare toggle (top bar)
                elif not arena_wave_active and not arena_enemies and arena_nightmare_rect.collidepoint(mx2, my2):
                    nightmare_mode = not nightmare_mode
                    if nightmare_mode and arena_wave <= 1:
                        arena_coins = max(arena_coins, 600)
                # Ranges toggle (below top bar, left)
                elif not arena_shop_open and arena_ranges_rect.collidepoint(mx2, my2):
                    show_ranges = not show_ranges
                else:
                    # Wall upgrade/sell panel buttons first
                    if arena_selected_wall_obj and arena_selected_wall_obj in arena_walls:
                        if arena_wall_close_rect and arena_wall_close_rect.collidepoint(mx2, my2):
                            arena_selected_wall_obj = None
                            continue
                        if arena_wall_upgrade_rect and arena_wall_upgrade_rect.collidepoint(mx2, my2):
                            _w_upg = arena_selected_wall_obj
                            if _w_upg.level < _w_upg.max_level:
                                _upg_cost = ArenaWall.LEVEL_STATS[_w_upg.level + 1]["cost"]
                                if arena_coins >= _upg_cost:
                                    arena_coins -= _upg_cost
                                    coins = arena_coins
                                    _w_upg.upgrade()
                            continue
                        if arena_wall_sell_rect and arena_wall_sell_rect.collidepoint(mx2, my2):
                            _w_sell = arena_selected_wall_obj
                            _sell_val = int(_w_sell.upgrade_cost_spent * 0.5 + 75)
                            arena_coins += _sell_val
                            coins = arena_coins
                            arena_walls.remove(_w_sell)
                            arena_selected_wall_obj = None
                            continue
                    hit_arena_tower = False
                    for at_sel in arena_towers:
                        at_sx, at_sy = a2s(at_sel.wx, at_sel.wy)
                        if math.hypot(at_sx - mx2, at_sy - my2) <= 16:
                            arena_selected_tower_obj = at_sel
                            arena_selected_wall_obj = None
                            arena_placing_tower = None
                            arena_placing_wall = False
                            hit_arena_tower = True
                            break
                    if not hit_arena_tower:
                        hit_arena_wall = False
                        for aw_sel in arena_walls:
                            aw_sx, aw_sy = a2s(aw_sel.wx, aw_sel.wy)
                            if math.hypot(aw_sx - mx2, aw_sy - my2) <= max(ArenaWall.W, ArenaWall.H) // 2 + 4:
                                arena_selected_wall_obj = aw_sel
                                arena_selected_tower_obj = None
                                hit_arena_wall = True
                                break
                        if not hit_arena_wall:
                            arena_selected_tower_obj = None
                            arena_selected_wall_obj = None

        elif state == "GAME":
            # ── Bestiary events (swallow all clicks while open) ───────────────
            if bestiary_open and event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                if bestiary_close_rect.collidepoint(mx2, my2):
                    bestiary_open = False
                else:
                    for tid, tr in bestiary_tab_rects.items():
                        if tr.collidepoint(mx2, my2):
                            bestiary_tab = tid
                            bestiary_scroll = 0
                    if bestiary_up_rect.collidepoint(mx2, my2):
                        bestiary_scroll = max(0, bestiary_scroll - 40)
                    if bestiary_down_rect.collidepoint(mx2, my2):
                        bestiary_scroll += 40
                continue

            if bestiary_open and event.type == pygame.MOUSEWHEEL:
                bestiary_scroll = max(0, bestiary_scroll - event.y * 20)
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx2, my2 = event.pos
                handled = False

                # ── Valkyrie combine mode: click a max-level Goblin Hut ───────
                if valkyrie_combine_mode:
                    for _t in towers:
                        if _t.type == "Goblin Hut" and _t.level >= _t.max_level and math.hypot(_t.x - mx2, _t.y - my2) <= 18:
                            combine_anim_pos = (_t.x, _t.y)
                            combine_anim_timer = 60
                            towers.remove(_t)
                            valkyrie_combine_hut._do_goblin_combine()
                            break
                    valkyrie_combine_mode = False
                    valkyrie_combine_hut = None
                    handled = True

                # Upgrade menu
                if selected_tower_object and not handled:
                    if upgrade_menu_close_rect and upgrade_menu_close_rect.collidepoint(mx2, my2):
                        selected_tower_object = None
                        handled = True
                    elif upgrade_menu_sell_rect and upgrade_menu_sell_rect.collidepoint(mx2, my2):
                        _sv = int((selected_tower_object.cost + selected_tower_object.upgrade_cost_spent) * 0.7)
                        coins += _sv
                        if selected_tower_object in towers:
                            towers.remove(selected_tower_object)
                        selected_tower_object = None
                        handled = True
                    elif upgrade_menu_move_rect and upgrade_menu_move_rect.collidepoint(mx2, my2):
                        _mv_cost = max(1, int((selected_tower_object.cost + selected_tower_object.upgrade_cost_spent) * 0.05))
                        if coins >= _mv_cost:
                            coins -= _mv_cost
                            moving_tower_obj = selected_tower_object
                            selected_tower_object = None
                        handled = True
                    elif upgrade_menu_revive_rect and upgrade_menu_revive_rect.collidepoint(mx2, my2):
                        _bh = selected_tower_object
                        if _bh.type == "builder_hut" and len(_bh.builders) < 1 and coins >= 10000:
                            coins -= 10000
                            nb = Builder(_bh.x, _bh.y, _bh.builder_upgraded)
                            for _lv in range(1, _bh.level + 1):
                                _apply_builder_level(nb, _lv)
                            _bh.builders.append(nb)
                            _bh.builder_respawn_wave = 0
                        handled = True
                    elif selected_tower_object.type == "frost_laser" and frost_show_circles_rect.collidepoint(mx2, my2):
                        frost_show_circles = not frost_show_circles
                        handled = True
                    elif upgrade_menu_upgrade_rect and upgrade_menu_upgrade_rect.collidepoint(mx2, my2):
                        # Special COMBINE upgrade for Valkyrie Hut at level 3
                        if selected_tower_object.type == "Valkyrie Hut" and selected_tower_object.level == 3 and not selected_tower_object.valk_combined:
                            valkyrie_combine_mode = True
                            valkyrie_combine_hut = selected_tower_object
                            selected_tower_object = None
                        else:
                            selected_tower_object.upgrade()
                        handled = True

                if not handled:
                    # 2x speed (top-bar)
                    if twox_button_rect.collidepoint(mx2, my2):
                        speed_2x = not speed_2x
                        handled = True

                if not handled:
                    # Nightmare toggle — top-bar button, wave 1 only.
                    # Single-click to ENABLE; DOUBLE-click (within 0.5s) to DISABLE.
                    if not shop_open and not wave_active and not enemies and wave_number == 1 and not nightmare_locked and nightmare_button_rect.collidepoint(mx2, my2):
                        if nightmare_mode:
                            _now = time.time()
                            if _now - nightmare_last_click < 0.5:
                                nightmare_mode = False
                                nightmare_last_click = 0.0
                            else:
                                nightmare_last_click = _now
                        else:
                            nightmare_mode = True
                            coins = max(coins, 600)
                            nightmare_last_click = 0.0
                        handled = True
                    elif not handled and wave_number > 1 and not shop_open and nightmare_button_rect.collidepoint(mx2, my2):
                        handled = True  # Locked after wave 1 started

                if not handled:
                    # Shadow Storm info button & close (replaces Blood Storm at wave 75+)
                    if shadow_storm_active and not shop_open and shadow_storm_info_rect.collidepoint(mx2, my2):
                        shadow_storm_info_open = not shadow_storm_info_open
                        handled = True
                    elif shadow_storm_info_open and shadow_storm_info_close_rect.collidepoint(mx2, my2):
                        shadow_storm_info_open = False
                        handled = True
                    # Blood Storm info button & close
                    elif blood_storm_active and not shadow_storm_active and not shop_open and blood_storm_info_rect.collidepoint(mx2, my2):
                        blood_storm_info_open = not blood_storm_info_open
                        handled = True
                    elif blood_storm_info_open and blood_storm_info_close_rect.collidepoint(mx2, my2):
                        blood_storm_info_open = False
                        handled = True

                if not handled:
                    # Bestiary button
                    if not shop_open and info_button_rect.collidepoint(mx2, my2):
                        bestiary_open = not bestiary_open
                        handled = True

                if not handled and logged_in_user:
                    if skip_wave_open:
                        handled = True
                    elif user_rect.collidepoint(mx2, my2):
                        logout_menu_open = not logout_menu_open
                        handled = True
                    elif logout_menu_open and logout_rect_obj.collidepoint(mx2, my2):
                        # Record score before logging out (logout = death for non-admin)
                        if not is_admin and logged_in_user:
                            update_leaderboard(logged_in_user, wave_number, coins, nightmare=nightmare_locked)
                        do_logout()
                        handled = True
                    elif logout_menu_open and is_admin and skip_wave_rect_obj.collidepoint(mx2, my2):
                        logout_menu_open = False
                        skip_wave_open = True
                        skip_wave_str = ""
                        handled = True
                    elif logout_menu_open and admin_panel_rect_obj and admin_panel_rect_obj.collidepoint(mx2, my2):
                        logout_menu_open = False
                        cmd_console_open = True
                        cmd_console_str = ""
                        cmd_console_output = ""
                        cmd_console_help_shown = False
                        handled = True
                    elif logout_menu_open and return_rect_obj.collidepoint(mx2, my2):
                        # Save coins and return to menu — TD state (towers/wave/enemies) is preserved
                        if logged_in_user and logged_in_user in users:
                            users[logged_in_user]["coins"] = coins
                            users[logged_in_user]["owned_paths"] = list(owned_path_ids)
                            users[logged_in_user]["selected_path"] = selected_path_id
                            save_users()
                        logout_menu_open = False
                        wave_active = False   # pause the wave
                        placing_tower = False
                        placing_wall = False
                        placing_bomb = False
                        selected_tower = None
                        selected_tower_object = None
                        shop_open = False
                        shop_x = -SHOP_W
                        state = "MENU"
                        handled = True
                    elif logout_menu_open and mobile_mode_menu_rect.collidepoint(mx2, my2):
                        mobile_mode = not mobile_mode
                        logout_menu_open = False
                        handled = True
                    elif logout_menu_open:
                        logout_menu_open = False

                if not handled:
                    # Coins
                    for c2 in coins_list:
                        if not c2.collected and c2.is_clicked((mx2, my2)):
                            coins += c2.value
                            c2.collected = True

                    # Start wave button (top-bar)
                    if start_wave_rect.collidepoint(mx2, my2):
                        if not wave_active:
                            wave_active = True
                            enemies_spawned = 0
                            enemies_to_spawn = 5 + wave_number * 2
                            if wave_number == 1 and not nightmare_locked:
                                nightmare_locked = True

                    # Shop toggle — only when closed (open shop is handled by panel below)
                    elif not shop_open and shop_button_rect.collidepoint(mx2, my2):
                        shop_open = True

                    # Shop panel clicks
                    elif shop_x <= mx2 <= shop_x + SHOP_W:
                        # Tab row (top 28px of the panel)
                        if my2 < 28:
                            tab_w2 = SHOP_W // 2
                            for i2, (tid2, _) in enumerate([("towers", "Towers"), ("builder", "Builder")]):
                                if shop_x + i2 * tab_w2 <= mx2 < shop_x + (i2 + 1) * tab_w2:
                                    shop_tab = tid2
                                    break
                        else:
                            if shop_tab == "towers":
                                btns = [("gunner", 34), ("sniper", 74), ("machine_gun", 114), ("airstrike", 154), ("Goblin Hut", 194), ("heavy_machine_gun", 234), ("close", 274)]
                            else:
                                btns = [("frost_laser", 34), ("builder_hut", 74), ("Valkyrie Hut", 114), ("wall", 154), ("bomb", 194), ("close", 234)]
                            for tag, by in btns:
                                if by + 28 <= my2 <= by + 62:
                                    if tag == "close":
                                        shop_open = False
                                    elif tag == "wall":
                                        if coins >= get_wall_cost():
                                            placing_wall = True
                                            placing_tower = False
                                            placing_bomb = False
                                    elif tag == "bomb":
                                        if coins >= get_bomb_cost():
                                            placing_bomb = True
                                            placing_tower = False
                                            placing_wall = False
                                    else:
                                        dp = get_tower_price(tag)
                                        if coins >= dp:
                                            selected_tower = tag
                                            placing_tower = True
                                            placing_wall = False
                                            placing_bomb = False
                                    break

                    # Move existing tower
                    elif moving_tower_obj is not None:
                        if moving_tower_obj in towers:
                            moving_tower_obj.x = mx2
                            moving_tower_obj.y = my2
                            if hasattr(moving_tower_obj, "home_x"):
                                moving_tower_obj.home_x = mx2
                            if hasattr(moving_tower_obj, "home_y"):
                                moving_tower_obj.home_y = my2
                            for _b in getattr(moving_tower_obj, "builders", []):
                                _b.home_x = mx2
                                _b.home_y = my2
                        moving_tower_obj = None

                    # Place items on map
                    elif placing_wall:
                        cost = get_wall_cost()
                        if coins >= cost:
                            coins -= cost
                            walls_placed_count += 1
                            walls.append(Wall(mx2, my2, wall_rot))
                        placing_wall = False

                    elif placing_bomb:
                        cost = get_bomb_cost()
                        if coins >= cost:
                            coins -= cost
                            bombs.append(Bomb(mx2, my2, get_bomb_aoe_damage(), get_bomb_boss_damage()))
                            bombs_placed_count += 1
                        placing_bomb = False

                    elif placing_tower and selected_tower:
                        cost = get_tower_price(selected_tower)
                        if coins >= cost:
                            # Valkyrie Hut requires a builder_hut to already exist
                            if selected_tower == "Valkyrie Hut" and not any(t.type == "builder_hut" for t in towers):
                                pass  # silently block — UI shows requirement
                            else:
                                stats = {
                                    "gunner": (100, 10, 60),
                                    "sniper": (200, 70, 120),
                                    "machine_gun": (90, 20, 3),
                                    "heavy_machine_gun": (180, 40, 5),
                                    "airstrike": (350, 100, 200),
                                    "frost_laser": (130, 0, 25),
                                    "Goblin Hut": (0, 0, 0),
                                    "builder_hut": (0, 0, 0),
                                    "Valkyrie Hut": (0, 0, 0),
                                }
                                r3, d3, cd3 = stats[selected_tower]
                                t3 = Tower(mx2, my2, r3, d3, cd3, selected_tower, cost)
                                towers.append(t3)
                                coins -= cost
                                placing_tower = False
                                selected_tower = None
                                selected_tower_object = None

                    elif selected_wall and wall_upgrade_rect and wall_upgrade_rect.collidepoint(mx2, my2):
                        if selected_wall.level < selected_wall.max_level:
                            upg_cost = Wall.LEVEL_STATS[selected_wall.level + 1]["cost"]
                            if coins >= upg_cost:
                                coins -= upg_cost
                                selected_wall.upgrade()

                    elif selected_wall and wall_sell_rect and wall_sell_rect.collidepoint(mx2, my2):
                        coins += int(selected_wall.upgrade_cost_spent * 0.5 + get_wall_cost() * 0.5)
                        if selected_wall in walls:
                            walls.remove(selected_wall)
                        selected_wall = None

                    elif selected_wall and wall_close_rect and wall_close_rect.collidepoint(mx2, my2):
                        selected_wall = None

                    else:
                        # Select tower or wall
                        hit = False
                        for t3 in towers:
                            if math.hypot(t3.x - mx2, t3.y - my2) <= 15:
                                selected_tower_object = t3
                                placing_tower = False
                                placing_wall = False
                                placing_bomb = False
                                selected_tower = None
                                selected_wall = None
                                hit = True
                                break
                        if not hit:
                            selected_tower_object = None
                            # Try selecting a wall (oriented bbox hit-test via rotated point)
                            for w2 in walls:
                                _ang = math.radians(-w2.angle)
                                _dx = mx2 - w2.x
                                _dy = my2 - w2.y
                                _lx =  _dx * math.cos(_ang) + _dy * math.sin(_ang)
                                _ly = -_dx * math.sin(_ang) + _dy * math.cos(_ang)
                                if abs(_lx) <= w2.W / 2 and abs(_ly) <= w2.H / 2:
                                    selected_wall = w2
                                    hit = True
                                    break
                            if not hit:
                                selected_wall = None

            elif event.type == pygame.KEYDOWN:
                # Admin skip-wave dialog intercepts all keys while open
                if skip_wave_open:
                    if event.key == pygame.K_ESCAPE:
                        skip_wave_open = False
                        skip_wave_str = ""
                    elif event.key == pygame.K_RETURN:
                        try:
                            target = max(1, int(skip_wave_str))
                            wave_number = target
                            wave_active = False
                            enemies.clear()
                            enemies_spawned = 0
                            enemies_to_spawn = 0
                            if wave_number >= 35 and not blood_storm_active:
                                blood_storm_active = True
                                blood_storm_splash_timer = 300
                                blood_storm_info_open = True
                            if wave_number >= 75 and not shadow_storm_active:
                                shadow_storm_active = True
                                shadow_storm_splash_timer = 300
                                shadow_storm_info_open = True
                        except ValueError:
                            pass
                        skip_wave_open = False
                        skip_wave_str = ""
                    elif event.key == pygame.K_BACKSPACE:
                        skip_wave_str = skip_wave_str[:-1]
                    elif event.unicode.isdigit():
                        if len(skip_wave_str) < 4:
                            skip_wave_str += event.unicode
                    continue
                if event.key == pygame.K_ESCAPE:
                    placing_tower = False
                    placing_wall = False
                    placing_bomb = False
                    selected_tower = None
                    selected_tower_object = None
                    selected_wall = None
                    valkyrie_combine_mode = False
                    valkyrie_combine_hut = None
                if placing_wall:
                    if event.key == pygame.K_LEFT:
                        wall_rot = (wall_rot - 15) % 360
                    elif event.key == pygame.K_RIGHT:
                        wall_rot = (wall_rot + 15) % 360
                    elif event.key == pygame.K_UP:
                        wall_rot = (wall_rot - 45) % 360
                    elif event.key == pygame.K_DOWN:
                        wall_rot = (wall_rot + 45) % 360
                if selected_tower_object:
                    if event.key == pygame.K_s:
                        sell_val = int((selected_tower_object.cost + selected_tower_object.upgrade_cost_spent) * 0.7)
                        coins += sell_val
                        # If selling a builder hut, any Valkyrie Hut still under
                        # construction collapses — refund 50% of its value
                        if selected_tower_object.type == "builder_hut":
                            for _vt in towers[:]:
                                if _vt.type == "Valkyrie Hut" and not _vt.valk_built:
                                    valk_refund = int((_vt.cost + _vt.upgrade_cost_spent) * 0.5)
                                    coins += valk_refund
                                    towers.remove(_vt)
                        towers.remove(selected_tower_object)
                        selected_tower_object = None
                    elif event.key == pygame.K_u:
                        selected_tower_object.upgrade()
                    elif event.key == pygame.K_q:
                        t3 = selected_tower_object
                        if t3.type == "builder_hut" and len(t3.builders) < 1 and coins >= 10000:
                            coins -= 10000
                            nb = Builder(t3.x, t3.y, t3.builder_upgraded)
                            for _lv in range(1, t3.level + 1):
                                _apply_builder_level(nb, _lv)
                            t3.builders.append(nb)
                            t3.builder_respawn_wave = 0
            elif event.type == pygame.MOUSEWHEEL and not bestiary_open:
                pass  # reserved

pygame.quit()




