"""Two remote-science structures for the Neige world.

lab_outpost_dome : a tall glass observatory dome (3-row tinted drum + hemisphere) with thin iron meridians and a
                   single quartz apex, on a low white platform with a dark skirt: airlock corridor, antenna mast,
                   generator shed (chimney stack, blue exhaust), stepped solar arrays with a junction box, a deep
                   westward snow drift lapping the glass.
bunker_entrance  : a soft snow hill with a blast-door portal set into it, an excavated ramp trench with rails, a short
                   lit corridor ending in a sealed second door, capped vents, antenna, pipe + hatch, crystals with
                   bevelled deepslate outcrops, an intact and a knocked-over barrier (end-rod marker lights).

Both schematics carry NO ground slab: only buried, tapered foundations below the ground index.
Paste them with //paste -a (air skipped) so the world snow stays around the foundation.
"""
import math

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import GROUND, MIX_WHITE, MIX_DARK, MIX_SNOW, MIX_LIGHT_GRAY

SNOW = GROUND["snow"]
DARK = "minecraft:polished_deepslate"
DARK_TILE = "minecraft:deepslate_tiles"
DARK_WALL = "minecraft:polished_deepslate_wall"
IRON = "minecraft:iron_block"
WHITE = "minecraft:white_concrete"
LGRAY = "minecraft:light_gray_concrete"
QUARTZ = "minecraft:quartz_block"
GLASS = "minecraft:glass"
GLASS_BLUE = "minecraft:light_blue_stained_glass"
LANTERN = "minecraft:sea_lantern"
FROG = "minecraft:pearlescent_froglight"
YELLOW = "minecraft:yellow_concrete"
BLACK = "minecraft:black_concrete"
BASALT = "minecraft:polished_basalt"
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}

# Toolkit workaround: tools/states.py lists iron_door in the generic "facing" schema (after the door schema), so
# the validator only accepts half=top/bottom for it. Vanilla 1.20.1 doors use half=upper/lower; restore that here.
st._PROPS.setdefault("iron_door", {}).update(half={"upper", "lower"}, facing={"north", "east", "south", "west"})


# ----------------------------------------------------------------------------------------------- local helpers
def snow_mound(s, cx, cz, rx, rz, h, base_y, p=1.0, noise=0.0, seed=1, floor=False, min_layer=1):
    """Smooth snow bump (paraboloid-ish, exponent p) with a low-frequency noise term so the contour rings break
    up; the top is finished with snow layers so the profile has no 1-block steps. Full blocks from base_y+1 up,
    only into air. floor=True also stamps snow at base_y (the surface block) under the mound."""
    for x in range(s.w):
        for z in range(s.l):
            t = 1.0 - ((x - cx) / rx) ** 2 - ((z - cz) / rz) ** 2
            if t <= 0:
                continue
            hh = h * (t ** p)
            if noise:
                hh += (sh.value_noise2(x, z, seed, 5.0) - 0.5) * 2 * noise * min(1.0, t * 3)
            hh = max(0.0, hh)
            full = int(math.floor(hh))
            frac = hh - full
            if floor:
                s.set_if_air(x, base_y, z, SNOW)
            for y in range(base_y + 1, base_y + 1 + full):
                s.set_if_air(x, y, z, SNOW)
            n = int(round(frac * 8))
            if n >= min_layer:
                y = base_y + 1 + full
                if s.is_air(x, y, z) and not s.is_air(x, y - 1, z):
                    s.set(x, y, z, st.snow_layer(n))


def ellipsoid_mask(s, cx, cy, cz, rx, ry, rz):
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 + ((zs - cz) / rz) ** 2 <= 1.0


def cylinder_mask(s, cx, cz, r, y1, y2):
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    return ((xs - cx) ** 2 + (zs - cz) ** 2 <= r * r) & (ys >= y1) & (ys <= y2)


def wall_panel(s, x, y, z, wall_side):
    """Open iron trapdoor lying flat against the wall that is on `wall_side` of cell (x,y,z)."""
    s.set(x, y, z, st.trapdoor("iron", OPP[wall_side], "top", open=True))


def surface_y(s, x, z, g):
    """y of the first free cell above the ground column (never below g+1); a snow layer on top is removed."""
    ty = s.top_y(x, z)
    if ty >= 0 and s.get(x, ty, z).startswith("minecraft:snow["):
        s.set(x, ty, z, "air")
        ty -= 1
    return max(ty + 1, g + 1)


def stripe(s, x, y, z, k):
    s.set(x, y, z, YELLOW if k % 2 == 0 else BLACK)


def crystal_spike(s, x, y, z, h, seed=0):
    """Blue crystal spike as the world grows them: 2x2 icy base, tapering blue column, amethyst tips."""
    for dx, dz in ((0, 0), (1, 0), (0, 1), (1, 1)):
        s.set(x + dx, y, z + dz, "minecraft:packed_ice")
    s.set(x, y + 1, z, "minecraft:blue_ice")
    s.set(x + 1, y + 1, z + 1, "minecraft:blue_ice")
    s.set(x + 1, y + 1, z, GLASS_BLUE)
    s.set(x, y + 1, z + 1, st.facing_block("minecraft:medium_amethyst_bud", "up"))
    for i in range(2, h):
        s.set(x, y + i, z, GLASS_BLUE if (i + seed) % 2 else "minecraft:blue_ice")
    s.set(x, y + h, z, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(x + 1, y + 2, z + 1, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(x + 1, y + 2, z, st.facing_block("minecraft:large_amethyst_bud", "up"))


def outcrop(s, cx, cz, core, rim, g):
    """Deepslate showing through the snow: full tiles on the core cells, tile stairs bevelled outward on the rim
    cells (tall side toward the cluster centre), one buried course under each cell so nothing floats."""
    for dx, dz in list(core) + list(rim):
        y = surface_y(s, cx + dx, cz + dz, g)
        s.set(cx + dx, y - 1, cz + dz, DARK_TILE)
        if (dx, dz) in core:
            s.set(cx + dx, y, cz + dz, DARK_TILE)
        else:
            s.set(cx + dx, y, cz + dz, st.stairs("deepslate_tile", sh._facing_to_center(dx, dz)))


def vent_cap(s, x, y, z):
    """Chimney head: soul campfire on the stack, four open iron-trapdoor louvres around it (panels against the
    fire cell), a closed iron trapdoor grille on top (smoke rises through it, the fire only glows through slats)."""
    s.set(x, y, z, st.campfire(soul=True))
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        s.set(x + dx, y, z + dz, st.trapdoor("iron", sh._facing_to_center(dx, dz), "bottom", open=True))
    s.set(x, y + 1, z, st.trapdoor("iron", "north", "bottom"))


def flat_roof(s, x1, z1, x2, z2, y, seed):
    """Dark 1-block trim ring with a light-gray textured centre, stair bevel under the overhang, snow on top."""
    sh.box(s, x1, y, z1, x2, y, z2, DARK)
    sh.box(s, x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1, LGRAY)
    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=seed, region=(x1 + 1, y, z1 + 1, x2 - 1, y, z2 - 1))
    sh.box_edge_stairs(s, x1, y, z1, x2, z2, "deepslate_tile", half="top")
    sh.snow_cover(s, x1 + 1, z1 + 1, x2 - 1, z2 - 1, y_min=y, prob=0.55, seed=seed, layers=(1, 2),
                  skip=["polished_deepslate", "basalt"])


# =============================================================================================== 1. THE DOME
def build_dome():
    W, H, L, G = 30, 20, 32, 3
    s = Schematic(W, H, L, ground=G)
    cx, cz = 14, 15
    R = 8.0                                   # dome radius
    PT = G + 1                                # platform top y
    CY = PT + 4                               # dome centre = top of the 3-row drum (PT+1 dark band, PT+2..3 tint)
    APEX = CY + 8

    # ---- platform: buried foundation, white textured top, dark deepslate skirt at ground + dark stair bevel
    sh.cylinder(s, cx, G - 1, cz, 9.5, 1, LGRAY, axis="y")
    sh.cylinder(s, cx, PT, cz, 9.5, 0, WHITE, axis="y")
    sh.cylinder(s, cx, G, cz, 10.6, 0, DARK_TILE, axis="y", hollow=True, thickness=1.2)   # skirt ring at ground
    sh.ring_stairs(s, cx, PT, cz, 10.4, "deepslate_tile", half="bottom")                 # skirt bevel
    # corridor floor strip to the east (x=20..27), foundation 2 deep
    sh.box(s, 20, G - 1, 13, 27, PT, 16, LGRAY)
    sh.box(s, 20, PT, 13, 27, PT, 16, DARK)
    sh.box(s, 21, PT, 14, 27, PT, 15, LGRAY)

    # ---- airlock corridor (interior 2 wide x 3 high, x=21..27, z=14..15)
    for z in (13, 16):
        sh.box(s, 21, PT + 1, z, 27, PT + 3, z, WHITE)
        for x in (22, 25):
            sh.box(s, x, PT + 1, z, x, PT + 3, z, IRON)
        s.set(24, PT + 2, z, "minecraft:light_blue_stained_glass_pane")   # portholes
        s.set(26, PT + 2, z, "minecraft:light_blue_stained_glass_pane")
    flat_roof(s, 21, 13, 27, 16, PT + 4, seed=61)
    for x in (22, 25):
        s.set(x, PT + 4, 13, IRON)
        s.set(x, PT + 4, 16, IRON)
    wall_panel(s, 23, PT + 3, 12, "south")                                  # outside vents under the overhang
    wall_panel(s, 23, PT + 3, 17, "north")
    wall_panel(s, 26, PT + 1, 12, "south")
    wall_panel(s, 26, PT + 1, 17, "north")
    s.set(26, PT + 4, 14, FROG)
    s.set(26, PT + 4, 15, FROG)
    sh.box(s, 27, PT + 1, 13, 27, PT + 3, 16, WHITE)                       # end wall
    s.set(27, PT + 3, 14, IRON)
    s.set(27, PT + 3, 15, IRON)
    s.set(27, PT + 1, 14, st.door("iron", "east", "lower", "right", open=True))
    s.set(27, PT + 2, 14, st.door("iron", "east", "upper", "right", open=True))
    s.set(27, PT + 1, 15, st.door("iron", "east", "lower", "left"))
    s.set(27, PT + 2, 15, st.door("iron", "east", "upper", "left"))
    s.set(28, PT, 14, st.stairs("deepslate_tile", "west"))
    s.set(28, PT, 15, st.stairs("deepslate_tile", "west"))
    s.set(28, PT + 3, 14, st.end_rod("east"))
    s.set(28, PT + 3, 15, st.end_rod("east"))
    s.add_sign(28, PT + 2, 13, "minecraft:warped_wall_sign[facing=east]", ["AVANT-POSTE 4", "station", "cryo-labo", "acces reserve"])
    s.set(28, PT + 2, 16, st.wall_banner("light_blue", "east"))
    for k in range(4):                                                       # rim lights sunk into the platform edge
        a = math.pi / 4 + k * math.pi / 2
        x, z = round(cx + 9.0 * math.cos(a)), round(cz + 9.0 * math.sin(a))
        s.set(x, G, z, LANTERN)
        s.set(x, PT, z, GLASS_BLUE)
    s.set(26, PT, 21, "minecraft:barrel[facing=up,open=false]")             # supplies dropped by the shed
    s.set(27, PT, 21, "minecraft:barrel[facing=east,open=false]")
    s.set(26, PT + 1, 21, st.snow_layer(2))
    wall_panel(s, 23, PT + 1, 14, "north")                                  # interior panels + lights
    wall_panel(s, 23, PT + 1, 15, "south")
    s.set(22, PT + 3, 14, LANTERN)
    s.set(22, PT + 3, 15, LANTERN)

    # ---- antenna mast (north): cable runs level, drops down a chain to a junction box by the platform
    mx, mz = 10, 3
    s.set(mx, PT, mz, IRON)
    sh.box(s, mx, PT + 1, mz, mx, PT + 7, mz, DARK_WALL)
    s.set(mx, PT + 8, mz, IRON)
    for y in (PT + 9, PT + 10, PT + 11):
        s.set(mx, y, mz, st.lightning_rod("up"))
    s.set(mx - 1, PT + 6, mz, st.end_rod("west"))
    s.set(mx + 1, PT + 6, mz, st.end_rod("east"))
    s.set(mx, PT + 5, mz - 1, "minecraft:daylight_detector")                # dish
    sh.box(s, mx, PT + 1, mz - 1, mx, PT + 4, mz - 1, DARK_WALL)
    s.set(mx, PT, mz - 1, IRON)
    for dx, dz in ((-1, 0), (1, 0), (0, 1)):
        s.set(mx + dx, PT, mz + dz, st.trapdoor("iron", "north", "bottom"))
    for z in range(mz + 1, mz + 4):
        s.set(mx, PT + 7, z, st.chain("z"))
    for y in range(PT + 1, PT + 7):
        s.set(mx, y, mz + 3, st.chain("y"))
    s.set(mx, PT, mz + 3, DARK)                                             # junction block on the snow
    s.set(mx + 1, PT, mz + 3, "minecraft:lever[face=floor,facing=east,powered=false]")

    # ---- generator shed (south-east): chimney stack with blue exhaust, meter box, wall light, cable to the dome
    sx1, sz1, sx2, sz2 = 22, 22, 25, 25
    sh.box(s, sx1, G - 1, sz1, sx2, PT, sz2, LGRAY)
    sh.box(s, sx1, PT + 1, sz1, sx2, PT + 3, sz2, LGRAY)
    sh.box(s, sx1 + 1, PT + 1, sz1 + 1, sx2 - 1, PT + 3, sz2 - 1, "air")
    for x, z in ((sx1, sz1), (sx1, sz2), (sx2, sz1), (sx2, sz2)):
        sh.box(s, x, PT + 1, z, x, PT + 3, z, DARK)
    flat_roof(s, sx1, sz1, sx2, sz2, PT + 4, seed=62)
    s.set(sx1 + 1, PT + 1, sz1, st.door("iron", "north", "lower", "left", open=True))
    s.set(sx1 + 1, PT + 2, sz1, st.door("iron", "north", "upper", "left", open=True))
    wall_panel(s, sx1 + 2, PT + 2, sz1 - 1, "south")                        # meter box beside the door
    s.set(sx1 + 2, PT + 1, sz1 - 1, st.button("polished_blackstone", "wall", "north"))
    s.set(sx1 + 1, PT + 3, sz1 - 1, st.end_rod("north"))                    # light over the door
    wall_panel(s, sx2 + 1, PT + 2, sz1 + 1, "west")
    wall_panel(s, sx1 + 2, PT + 2, sz2 + 1, "north")
    wall_panel(s, sx1 - 1, PT + 2, sz2 - 1, "east")
    s.set(sx2, PT + 2, sz2 - 1, GLASS_BLUE)                                 # wall light: lantern behind tinted glass
    s.set(sx2 - 1, PT + 2, sz2 - 1, LANTERN)
    s.set(sx2 - 1, PT + 1, sz2 - 1, st.facing_block("minecraft:blast_furnace", "west"))
    s.set(sx2 - 1, PT + 3, sz2 - 1, st.facing_block("minecraft:observer", "west"))
    s.set(sx1 + 1, PT + 1, sz2 - 1, "minecraft:barrel[facing=up,open=false]")
    s.set(sx1 + 1, PT + 3, sz1 + 1, st.end_rod("down"))
    s.set(sx2 - 1, PT + 4, sz2 - 1, st.log(BASALT, "y"))                    # chimney stack through the roof
    s.set(sx2 - 1, PT + 5, sz2 - 1, st.log(BASALT, "y"))
    s.set(sx2 - 1, PT + 6, sz2 - 1, IRON)
    vent_cap(s, sx2 - 1, PT + 7, sz2 - 1)
    s.set(sx2 + 1, PT + 1, sz2 - 1, st.trapdoor("iron", "west", "bottom", open=True))   # exhaust vent on the side
    for x in (sx1 - 1, sx1 - 2):                                            # 2-block cable into the dome band
        s.set(x, PT + 3, sz1 - 1, st.chain("x"))

    # ---- solar arrays (south): two stepped 10-long panels in a dark frame, junction box, cable on the snow
    for z0 in (27, 30):
        for x in range(5, 15):
            s.set(x, PT + 1, z0, "minecraft:daylight_detector")                 # low (north) row
            s.set(x, PT + 2, z0 + 1, "minecraft:daylight_detector")             # high (south) row
            s.set(x, PT, z0, st.slab("polished_deepslate", "top"))              # dark edge line under the panels
            s.set(x, PT + 1, z0 + 1, st.slab("polished_deepslate", "top"))      # riser
            wall_panel(s, x, PT + 1, z0 - 1, "south")                           # bezel along the north edge
        for x in (5, 8, 11, 14):
            s.set(x, PT, z0, DARK_WALL)
            s.set(x, PT, z0 + 1, DARK_WALL)
            s.set(x, PT + 1, z0 + 1, DARK_WALL)
    s.set(15, PT + 1, 28, DARK)                                             # junction box
    s.set(15, PT + 2, 28, DARK)
    s.set(15, PT + 1, 29, DARK)
    s.set(16, PT + 2, 28, "minecraft:lever[face=wall,facing=east,powered=false]")
    s.set(16, PT + 1, 28, "minecraft:polished_blackstone_button[face=wall,facing=east]")
    for x in range(16, 24):                                                  # cable lying on the snow to the shed
        s.set(x, PT, 28, st.chain("x"))
    s.set(23, PT, 27, st.chain("z"))
    s.set(23, PT, 26, st.chain("z"))

    # ---- snow drift piled against the west side (built before the shell, carved out of the interior after)
    snow_mound(s, cx - 6, cz, 7.8, 10.0, 8.5, G, p=1.0, noise=0.3, seed=5, floor=True)
    snow_mound(s, cx - 9, cz + 3, 5.0, 6.0, 2.0, G, p=1.0, noise=0.2, seed=6, floor=True)

    # ---- texture + weathering of everything built so far (the shell is added afterwards and stays clean)
    sh.texturize(s, WHITE, MIX_WHITE, seed=21)
    sh.texturize(s, SNOW, MIX_SNOW, seed=22)
    sh.snow_cover(s, y_min=PT, prob=0.25, seed=24, layers=(1, 2),
                  skip=["glass", "iron", "lamp", "froglight", "daylight", "lantern", "pane", "purpur", "observer",
                        "bookshelf", "ice", "detector", "polished_deepslate", "concrete", "quartz", "calcite"])

    # ---- shell masks: drum (cylinder, PT+1..CY) + hemisphere (CY..APEX); corridor cut-out kept intact
    xs = np.arange(s.w)[:, None, None]
    ys = np.arange(s.h)[None, :, None]
    zs = np.arange(s.l)[None, None, :]
    drum_out = cylinder_mask(s, cx, cz, R + 0.5, PT + 1, CY - 1)
    drum_in = cylinder_mask(s, cx, cz, R - 0.5, PT + 1, CY - 1)
    sph_out = ellipsoid_mask(s, cx, CY, cz, R + 0.5, R + 0.5, R + 0.5) & (ys >= CY)
    sph_in = ellipsoid_mask(s, cx, CY, cz, R - 0.5, R - 0.5, R - 0.5) & (ys >= CY)
    corridor = (xs >= 21) & (zs >= 13) & (zs <= 16) & (ys <= PT + 4)
    shell = ((drum_out & ~drum_in) | (sph_out & ~sph_in)) & ~corridor
    interior = (drum_in | sph_in) & ~corridor

    def on_rib(dx, dz, n):
        """n one-wide meridians (4 on the dome: continuous cardinal lines; 8 pilasters on the vertical drum)."""
        for k in range(n):
            a = k * 2 * math.pi / n
            ux, uz = math.cos(a), math.sin(a)
            along = dx * ux + dz * uz
            perp = abs(-uz * dx + ux * dz)
            if along > 0.5 and perp < (0.5 if k % 2 == 0 or n == 4 else 0.72):
                return True
        return False

    for (x, y, z) in np.argwhere(shell):
        x, y, z = int(x), int(y), int(z)
        dx, dz = x - cx, z - cz
        if y == PT + 1:
            blk = DARK                                                      # dark base band on the white platform
        elif y < CY:
            blk = IRON if on_rib(dx, dz, 8) else GLASS_BLUE                 # tinted skirt with 8 iron pilasters
        elif y == CY or y == CY + 4:
            blk = IRON                                                      # belts: drum top + mid-dome
        elif y == APEX:
            blk = QUARTZ if (dx, dz) == (0, 0) else (IRON if (dx == 0 or dz == 0) else GLASS)
        else:
            blk = IRON if on_rib(dx, dz, 4) else GLASS                      # 4 cardinal meridians to the apex
        s.set(x, y, z, blk)
    sh.fill_mask(s, interior, "air")
    s.set(cx, APEX + 1, cz, st.lightning_rod("up"))
    s.set(cx, APEX - 1, cz, FROG)                                            # apex glow under the cap
    for k in range(4):                                                       # end rods on the inside of the belt
        a = k * math.pi / 2
        ux, uz = round(math.cos(a)), round(math.sin(a))
        for rr in range(5, 9):
            x, z = cx + ux * rr, cz + uz * rr
            if s.is_air(x, CY, z) and not s.is_air(x + ux, CY, z + uz):
                s.set(x, CY, z, st.end_rod({(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(ux, uz)]))
                break
    # ---- interior floor
    for x in range(cx - 8, cx + 9):
        for z in range(cz - 8, cz + 9):
            d = math.hypot(x - cx, z - cz)
            if d <= 7.6:
                s.set(x, PT, z, LGRAY)
            if d <= 2.4:
                s.set(x, PT, z, "minecraft:polished_diorite")
    s.set(cx, PT, cz, LANTERN)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        s.set(round(cx + 5 * math.cos(a)), PT, round(cz + 5 * math.sin(a)), LANTERN)
    # ---- workstations (north side): consoles on desks, screens above
    for x0 in (cx - 4, cx + 2):
        for i in range(3):
            x = x0 + i
            s.set(x, PT + 1, cz - 6, st.facing_block("minecraft:chiseled_bookshelf", "south"))
            s.set(x, PT + 1, cz - 5, "minecraft:daylight_detector")
            s.set(x, PT + 2, cz - 6, st.facing_block("minecraft:observer", "south") if i != 1 else st.redstone_lamp(True))
        s.set(x0 + 1, PT + 3, cz - 6, st.end_rod("down"))
    s.add_chest(cx, PT + 1, cz - 6, "south", "minecraft:chests/stronghold_library")
    s.set(cx, PT + 2, cz - 6, "minecraft:lectern[facing=south,has_book=true,powered=false]")
    s.add_sign(cx + 5, PT + 2, cz - 5, "minecraft:warped_wall_sign[facing=south]", ["JOURNAL 12", "givre dans", "le sas est", "tout evacuer"])
    # ---- cryo sample fridge (west): blue ice core under tinted glass, dark lid, cold light
    for z in (cz - 1, cz, cz + 1):
        for x in (cx - 6, cx - 5):
            s.set(x, PT + 1, z, "minecraft:blue_ice")
            s.set(x, PT + 2, z, "minecraft:tinted_glass")
            s.set(x, PT + 3, z, st.slab("polished_deepslate"))
    s.set(cx - 5, PT + 1, cz, LANTERN)
    s.set(cx - 4, PT + 1, cz - 1, "minecraft:cauldron")
    s.set(cx - 4, PT + 1, cz + 1, "minecraft:brewing_stand")
    # crystal sample rack (south-west)
    s.set(cx - 4, PT + 1, cz + 4, DARK)
    s.set(cx - 4, PT + 2, cz + 4, st.facing_block("minecraft:amethyst_cluster", "up"))
    s.set(cx - 3, PT + 1, cz + 4, DARK)
    s.set(cx - 3, PT + 2, cz + 4, st.facing_block("minecraft:medium_amethyst_bud", "up"))
    # ---- bunks (south), a barrel and candles between them
    for x in (cx - 3, cx + 3):
        s.set(x, PT + 1, cz + 4, st.bed("white", "south", "foot"))
        s.set(x, PT + 1, cz + 5, st.bed("white", "south", "head"))
    s.set(cx, PT + 1, cz + 5, "minecraft:barrel[facing=up,open=false]")
    s.set(cx, PT + 2, cz + 5, st.candle("light_blue", 3))
    s.set(cx + 4, PT + 1, cz + 3, "minecraft:barrel[facing=up,open=false]")
    # ---- frost creeping in through a cracked pane (north-east, first two dome rows)
    for (x, y, z) in np.argwhere(shell):
        x, y, z = int(x), int(y), int(z)
        a = math.degrees(math.atan2(z - cz, x - cx))
        if CY + 1 <= y <= CY + 2 and -62 < a < -48 and s.get(x, y, z) == GLASS:
            s.set(x, y, z, "minecraft:glass_pane")
    fx, fz = cx + 4, cz - 4
    for dx, dz in ((0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, -1), (-1, 1)):
        s.set(fx + dx, PT, fz + dz, "minecraft:packed_ice")
    s.set(fx + 1, PT, fz - 1, "minecraft:blue_ice")
    s.set(fx, PT + 1, fz, st.snow_layer(2))
    s.set(fx + 1, PT + 1, fz - 1, st.snow_layer(3))
    s.set(fx - 1, PT + 1, fz + 1, st.snow_layer(1))
    # ---- wind crust: one contiguous wedge of snow layers on the lower west rows of the dome (windward side),
    #      thick at the drift, thinning upward, edge broken by noise only on its top row
    for (x, y, z) in np.argwhere(shell):
        x, y, z = int(x), int(y), int(z)
        dx, dz = x - cx, z - cz
        if not (CY + 1 <= y <= CY + 5 and dx <= -3 and abs(dz) <= -dx * 0.9 and s.is_air(x, y + 1, z)):
            continue
        if y == CY + 5 and sh.value_noise2(x, z, 9, 4.0) > 0.55:
            continue
        s.set(x, y + 1, z, st.snow_layer({CY + 1: 4, CY + 2: 3, CY + 3: 2, CY + 4: 2, CY + 5: 1}[y]))
    return s.cropped(pad=1)


# =============================================================================================== 2. THE BUNKER
def build_bunker():
    W, H, L, G = 24, 16, 26, 6
    s = Schematic(W, H, L, ground=G)
    hx, hz = 12, 14
    RX, RZ = 11.0, 9.5
    # ---- ground: only under the hill footprint and the trench, tapered downward (no square slab, no plateau)
    xs = np.arange(W)[:, None, None]
    ys = np.arange(H)[None, :, None]
    zs = np.arange(L)[None, None, :]
    wob = np.array([[sh.value_noise2(x, z, 41, 6.0) for z in range(L)] for x in range(W)])[:, None, :]
    for y, k, x1, x2 in ((G, 1.0, 7, 17), (G - 1, 0.82, 8, 16), (G - 2, 0.62, 8, 16)):
        foot = (((xs - hx) / ((RX + 0.5 + wob) * k)) ** 2 + ((zs - hz) / ((RZ + 0.5 + wob) * k)) ** 2) <= 1.0
        foot |= (xs >= x1) & (xs <= x2) & (zs <= 7)                       # just what the trench walls need
        s.data[foot & (ys == y)] = s.pid(SNOW)
    # ---- the hill: soft profile with low-frequency noise, layered finish
    snow_mound(s, hx, hz, RX, RZ, 8.6, G, p=1.1, noise=0.6, seed=7)
    # ---- excavated trench + ramp (x=10..14, z=0..5), floor y=G-2
    FZ = 6                                                                   # front face of the portal
    sh.box(s, 8, G - 1, 1, 16, H - 1, FZ - 1, "air")
    sh.box(s, 8, G + 1, 0, 16, H - 1, 0, "air")
    sh.box(s, 9, G - 2, 1, 15, G - 2, FZ - 1, DARK)                         # trench floor
    sh.box(s, 10, G - 2, 3, 14, G - 2, FZ - 1, LGRAY)
    sh.box(s, 9, G - 1, 1, 9, G, FZ - 1, DARK)                              # trench walls
    sh.box(s, 15, G - 1, 1, 15, G, FZ - 1, DARK)
    sh.box(s, 8, G - 2, 1, 8, G, FZ - 1, SNOW)
    sh.box(s, 16, G - 2, 1, 16, G, FZ - 1, SNOW)
    sh.box(s, 10, G - 1, 1, 14, G - 1, 1, DARK)                             # ramp: z=1 high step, z=2 low step
    for x in range(10, 15):
        s.set(x, G, 1, st.stairs("polished_deepslate", "north"))
        s.set(x, G - 1, 2, st.stairs("polished_deepslate", "north"))
    for x in (9, 15):
        sh.box(s, x, G + 1, 0, x, G + 1, FZ - 1, DARK_WALL)                 # guard rails
        s.set(x, G + 2, 0, st.end_rod("up"))                                # lamp posts at the top of the ramp
        s.set(x, G - 1, 3, LANTERN)
    sh.box(s, 10, G, 0, 14, G, 0, "minecraft:white_concrete_powder")        # trodden snow at the top of the ramp
    # ---- blast-door portal (x=8..16, y=G-2..G+5, z=6..10) + encased corridor behind it (to z=20)
    sh.box(s, 8, G - 2, FZ, 16, G + 5, 10, DARK)
    sh.box(s, 9, G - 2, 11, 15, G + 3, 20, DARK)
    sh.box(s, 9, G - 1, FZ, 15, G + 4, 10, WHITE)                           # inner white band of the portal
    sh.box(s, 11, G - 1, FZ, 13, G + 2, 10, "air")                          # opening 3 wide x 4 high
    sh.box(s, 10, G - 2, FZ, 14, G - 2, 10, DARK)                           # threshold floor
    sh.box(s, 10, G - 1, 11, 14, G + 1, 18, WHITE)                          # corridor inner walls
    sh.box(s, 11, G - 1, 11, 13, G + 1, 18, "air")                          # corridor 3x3
    for z in (12, 15, 18):
        sh.box(s, 10, G - 1, z, 10, G + 1, z, DARK)
        sh.box(s, 14, G - 1, z, 14, G + 1, z, DARK)
    sh.box(s, 12, G - 2, 11, 12, G - 2, 18, LGRAY)                          # floor centre line
    for x in range(11, 14):
        stripe(s, x, G - 2, 10, x)
    for x in range(10, 15):
        stripe(s, x, G - 2, FZ - 1, x)
    for k in range(4):                                                       # warning stripes on the door jambs
        stripe(s, 10, G - 1 + k, FZ, k)
        stripe(s, 14, G - 1 + k, FZ, k + 1)
    for x in (10, 14):                                                       # lit lintel row
        s.set(x, G + 3, FZ, LANTERN)
        s.set(x, G + 3, FZ - 1, st.end_rod("north"))
    s.set(12, G + 3, FZ, st.facing_block("minecraft:observer", "north"))
    s.set(11, G + 3, FZ, GLASS_BLUE)
    s.set(13, G + 3, FZ, GLASS_BLUE)
    s.set(11, G + 3, FZ + 1, LANTERN)
    s.set(13, G + 3, FZ + 1, LANTERN)
    sh.box(s, 9, G + 4, FZ, 15, G + 4, FZ, IRON)                            # iron band under the cornice
    for x in range(8, 17):                                                   # cornice bevel
        s.set(x, G + 6, FZ, st.stairs("polished_deepslate", "south"))
        s.set(x, G + 6, 10, st.stairs("polished_deepslate", "north"))
    for z in range(FZ + 1, 10):
        s.set(8, G + 6, z, st.stairs("polished_deepslate", "east"))
        s.set(16, G + 6, z, st.stairs("polished_deepslate", "west"))
    sh.box(s, 9, G + 6, FZ + 1, 15, G + 6, 9, SNOW)
    s.set(8, G + 5, FZ - 1, st.stairs("polished_deepslate", "east", "top"))
    s.set(16, G + 5, FZ - 1, st.stairs("polished_deepslate", "west", "top"))
    wall_panel(s, 9, G, FZ - 1, "south")                                    # vents on the buttresses
    wall_panel(s, 15, G, FZ - 1, "south")
    wall_panel(s, 9, G + 1, FZ - 1, "south")
    wall_panel(s, 15, G + 1, FZ - 1, "south")
    # outer blast door (z=8, recessed): two closed leaves, middle leaf open, panels above
    DZ = 8
    for x, hinge, opn in ((11, "left", False), (12, "left", True), (13, "right", False)):
        s.set(x, G - 1, DZ, st.door("iron", "north", "lower", hinge, open=opn))
        s.set(x, G, DZ, st.door("iron", "north", "upper", hinge, open=opn))
    for x in (11, 13):
        s.set(x, G + 1, DZ, st.trapdoor("iron", "south", "top", open=True))
    for x in (11, 12, 13):
        s.set(x, G + 2, DZ, st.trapdoor("iron", "south", "top", open=True))
    s.set(11, G + 2, DZ - 1, LANTERN)                                        # lights in the door reveal
    s.set(13, G + 2, DZ - 1, LANTERN)
    s.add_sign(10, G + 1, FZ - 1, "minecraft:warped_wall_sign[facing=north]", ["LABO 3", "niveau -2", "porte 1", "ouverte"])
    # corridor furniture + lights + cables + vents
    s.set(12, G + 2, 12, LANTERN)
    s.set(12, G + 2, 16, LANTERN)
    s.set(10, G - 1, 14, LANTERN)
    s.set(14, G - 1, 17, LANTERN)
    for z in range(11, 19):
        s.set(13, G + 1, z, st.chain("z"))
    wall_panel(s, 11, G, 13, "west")
    wall_panel(s, 13, G, 16, "east")
    s.add_chest(13, G - 1, 17, "west", "minecraft:chests/ancient_city")
    s.set(11, G - 1, 17, "minecraft:barrel[facing=up,open=false]")
    s.set(11, G - 1, 12, "minecraft:packed_ice")
    s.set(11, G, 12, st.snow_layer(2))
    # sealed second door (z=19) with a red light
    for x, hinge in ((11, "left"), (12, "left"), (13, "right")):
        s.set(x, G - 1, 19, st.door("iron", "north", "lower", hinge))
        s.set(x, G, 19, st.door("iron", "north", "upper", hinge))
    sh.box(s, 11, G + 1, 19, 13, G + 1, 19, IRON)
    s.set(12, G + 1, 19, "minecraft:red_stained_glass")
    s.set(12, G + 1, 20, LANTERN)
    s.add_sign(11, G, 18, "minecraft:warped_wall_sign[facing=east]", ["SAS 2", "SCELLE", "danger", "code requis"])
    # ---- main vent stack with blue smoke (west shoulder of the hill): basalt stack, capped grille
    vx, vz = 5, 13
    vy = surface_y(s, vx, vz, G)
    for y in range(vy - 1, vy + 2):
        s.set(vx, y, vz, st.log(BASALT, "y"))
    s.set(vx, vy + 2, vz, DARK)
    for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        s.set(vx + dx, vy + 2, vz + dz, st.trapdoor("iron", "north", "top"))
    vent_cap(s, vx, vy + 3, vz)
    # ---- second, shorter vent on the south slope: basalt stub with an iron grille on top
    vx2, vz2 = 15, 22
    vy2 = surface_y(s, vx2, vz2, G)
    s.set(vx2, vy2 - 1, vz2, st.log(BASALT, "y"))
    s.set(vx2, vy2, vz2, st.log(BASALT, "y"))
    s.set(vx2, vy2 + 1, vz2, st.trapdoor("iron", "north", "bottom"))
    s.set(vx2 + 1, vy2, vz2, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(vx2, vy2, vz2 + 1, st.trapdoor("iron", "north", "bottom", open=True))
    # ---- antenna (east shoulder)
    ax, az = 19, 15
    ay = surface_y(s, ax, az, G)
    s.set(ax, ay - 1, az, IRON)
    s.set(ax, ay, az, IRON)
    sh.box(s, ax, ay + 1, az, ax, ay + 3, az, DARK_WALL)
    s.set(ax, ay + 4, az, IRON)
    s.set(ax, ay + 5, az, st.lightning_rod("up"))
    s.set(ax, ay + 6, az, st.lightning_rod("up"))
    s.set(ax - 1, ay + 3, az, st.end_rod("west"))
    s.set(ax + 1, ay + 3, az, st.end_rod("east"))
    s.set(ax, ay + 2, az + 1, "minecraft:daylight_detector")
    s.set(ax, ay + 1, az + 1, DARK_WALL)
    s.set(ax, ay, az + 1, IRON)
    # ---- half-buried pipe lying on the snow out of the south-east flank, ending in a low iron inspection hatch
    for x in range(13, 22):
        for z in (21, 22):
            s.set(x, G + 1, z, st.log(BASALT, "x"))
    for x in (15, 19):                                                       # pipe collars
        s.set(x, G + 2, 21, st.slab("polished_deepslate"))
        s.set(x, G + 2, 22, st.slab("polished_deepslate"))
    s.set(22, G + 1, 21, IRON)                                               # hatch flange
    s.set(22, G + 1, 22, IRON)
    s.set(22, G + 2, 21, st.trapdoor("iron", "north", "bottom"))
    s.set(22, G + 2, 22, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(23, G + 1, 22, "minecraft:lever[face=wall,facing=east,powered=false]")
    s.set(23, G + 1, 21, st.button("polished_blackstone", "wall", "east"))
    # ---- blue crystal spikes growing out of the flanks (asymmetric)
    for (x, z, h, sd) in ((2, 17, 5, 0), (20, 9, 4, 1), (8, 22, 3, 0)):
        y = surface_y(s, x, z, G)
        crystal_spike(s, x, y - 1, z, h, sd)
    crystal_spike(s, 1, G, 6, 5, 1)                                          # the big one beside the intact barrier
    s.set(3, G + 1, 7, "minecraft:blue_ice")
    s.set(3, G + 2, 7, st.facing_block("minecraft:medium_amethyst_bud", "up"))
    # ---- bevelled deepslate outcrops clustered at the crystals: the structure showing through the snow
    outcrop(s, 5, 19, ((0, 0), (1, 0)), ((-1, 0), (2, 0), (0, 1)), G)               # between the two SW spikes
    outcrop(s, 18, 11, ((0, 0),), ((-1, 0), (0, 1)), G)                             # below the NE spike
    outcrop(s, 4, 9, ((0, 0), (0, 1)), ((-1, 0), (1, 1), (0, -1)), G)               # beside the big spike
    # ---- barriers in front of the ramp: one intact (west), one knocked over (east); end-rod marker lights
    bz = 3
    for x in range(1, 8):
        y = surface_y(s, x, bz, G)
        if (x - 1) % 3 == 0:
            s.set(x, y, bz, DARK_WALL)
            s.set(x, y + 1, bz, st.end_rod("up"))
        else:
            s.set(x, y, bz, "minecraft:iron_bars")
    bz = 4
    py = surface_y(s, 17, bz, G)
    s.set(17, py, bz, DARK_WALL)                                             # one post still standing
    s.set(17, py + 1, bz, st.end_rod("up"))
    s.set(18, G + 1, bz, "minecraft:iron_bars")
    s.set(19, G + 1, bz, "minecraft:iron_bars")
    s.set(20, G + 1, bz, DARK_WALL)                                          # second post, light knocked off
    for x in (20, 21, 22):                                                    # fallen section lying flat
        s.set(x, G + 1, bz + 1, st.trapdoor("iron", "north", "bottom"))
    s.set(22, G + 1, bz + 2, DARK_WALL)                                       # toppled post with its light
    s.set(23, G + 1, bz + 2, st.end_rod("east"))
    sh.scatter(s, 17, 1, 23, 8, [st.snow_layer(2), st.snow_layer(3), st.slab("cobbled_deepslate")], 4, seed=44, y_offset=1)
    # ---- texture + weathering
    sh.texturize(s, DARK, MIX_DARK, seed=31)
    sh.texturize(s, WHITE, MIX_WHITE, seed=32)
    sh.texturize(s, SNOW, MIX_SNOW, seed=33)
    sh.snow_cover(s, y_min=G + 1, prob=0.3, seed=34, layers=(1, 2),
                  skip=["iron", "lantern", "glass", "ice", "concrete", "observer", "daylight", "basalt"])
    return s.cropped(pad=1)


def build():
    return {"lab_outpost_dome": build_dome(), "bunker_entrance": build_bunker()}
