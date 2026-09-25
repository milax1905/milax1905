"""Laboratoire HELIX - the main abandoned research facility of the snow world.

Layout (ground = 3, floor slab at y=4, players walk on y=5):
  * central rotunda (cylinder r=10) with a clerestory, a ribbed glass dome and a crystal core in the middle
  * CRYO wing (west): two rows of purpur / tinted-glass cryo pods lit by pearlescent froglight, one pod broken,
    two cryogenic tanks outside the end wall
  * CONTROL wing (east): console rows, screen wall, library, server racks, solar array on the roof
  * CONTAINMENT wing (south): glass cells with specimens, one breached; the far end of the wing has collapsed:
    caved roof, frost creeping over floor and walls, snow drifts, icicles
  * entrance porch (north) with retracted iron doors, antenna mast (NW), generator with pipes (NE)
Clean white concrete + quartz walls, polished deepslate base band and pilasters, iron trims, cold lights.
"""
import math
import random

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import LAB, MIX_DARK, MIX_ICE

G = 3                 # snow surface
YB = 3                # buried base band (replaces the surface snow block)
YF = 4                # floor slab
Y1, Y2 = 5, 8         # interior air (4 high)
YC = 9                # ceiling / roof top of the wings
YR = 10               # roof detailing level

WALL = LAB["wall"]                       # white concrete (textured at the end)
WALL_IN = "minecraft:smooth_quartz"      # inner partitions
ROOF = "minecraft:light_gray_concrete"   # roof / ceiling slab (textured)
FLOOR = "minecraft:light_gray_terracotta"   # placeholder id for floors, fully retextured at the end (never gravity)
BASE = LAB["trim_dark"]                  # polished deepslate
IRON = LAB["trim"]
GLASS = LAB["glass"]
GLASS_T = LAB["glass_tint"]              # light blue
LANT = LAB["floor_light"]
FROG = LAB["pod_light"]
TINT = LAB["pod_glass"]
PURPUR = "minecraft:purpur_block"
PURPUR_P = LAB["pod"]
BASALT = "minecraft:polished_basalt"
ICE = LAB["ice_creep"]
BICE = LAB["ice_creep_alt"]
SNOW = LAB["snow"]
BARS = "minecraft:iron_bars"
SIGN = "minecraft:warped_wall_sign"
MIX_WALL = [("minecraft:white_concrete", 7), ("minecraft:quartz_block", 2), ("minecraft:smooth_quartz", 1)]
MIX_FLOOR = [("minecraft:light_gray_concrete", 7), ("minecraft:polished_diorite", 2), ("minecraft:polished_andesite", 1)]
# roof mix WITHOUT concrete powder (tools.palette.MIX_LIGHT_GRAY contains light_gray_concrete_powder, a gravity block
# that would fall into the rooms from the ceilings on the first block update)
MIX_ROOF = [("minecraft:light_gray_concrete", 7), ("minecraft:polished_andesite", 2), ("minecraft:smooth_stone", 1)]
PIPE = "minecraft:weathered_copper"
PIPE_OLD = "minecraft:oxidized_copper"
PIPE_JOINT = "minecraft:copper_block"

# Toolkit workaround: tools/states.py registers iron_door in the generic "facing block" schema, which overrides the
# door schema and only allows half=top/bottom. Vanilla doors use half=upper/lower; putting top/bottom in the .schem
# would make the game drop the doors. Restore the vanilla values in memory (files under tools/ are untouched).
st._PROPS.setdefault("iron_door", {})["half"] = {"upper", "lower"}

OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}
DIRV = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
FACE_OF = {(0, 1): "south", (0, -1): "north", (1, 0): "east", (-1, 0): "west"}


# ------------------------------------------------------------------------------------------------ small helpers
def vent(s, x, y, z, face):
    """Iron trapdoor lying flat against a wall (panel / vent). `face` = direction it looks toward."""
    s.set(x, y, z, st.trapdoor("iron", face, "top", open=True))


def sign(s, x, y, z, face, lines):
    s.add_sign(x, y, z, f"{SIGN}[facing={face}]", lines)


def console(s, x, y, z):
    """A desk block (deepslate) with a daylight-detector console on top."""
    s.set(x, y, z, BASE)
    s.set(x, y + 1, z, LAB["console"])


def screen(s, x, y, z, w, h, face):
    """Wall screen: light blue glass with sea lanterns behind (in the wall). (x,y,z) = first cell of the glass."""
    dx, dz = DIRV[face]
    for i in range(w):
        for j in range(h):
            if face in ("north", "south"):
                s.set(x + i, y + j, z, GLASS_T)
                s.set(x + i, y + j, z - dz, LANT)
            else:
                s.set(x, y + j, z + i, GLASS_T)
                s.set(x - dx, y + j, z + i, LANT)


def floor_light(s, x, z):
    s.set(x, YF, z, LANT)


# ------------------------------------------------------------------------------------------------ wing shell
HAZARD = ("minecraft:yellow_terracotta", "minecraft:black_concrete")


def wing(s, x1, z1, x2, z2, pil_every=4, pil_offset=1, kind="cryo"):
    """Rectangular lab wing: buried deepslate band, proud deepslate plinth, floor, white walls with proud deepslate
    pilasters, blue window strips, a floor-level light band (sea lantern in the wall behind proud light-blue glass),
    a quartz cornice bevel under the roof edge, iron top trim, gray roof with a quartz slab parapet.
    Interior air y5..y8. `kind` gives each wing its exterior signature:
      cryo  - purpur pillar columns and a pearlescent froglight in every window bay (pink glow)
      ctrl  - plain white (the 9-wide screen band on the east wall is added by screen_band())
      cont  - yellow / black hazard stripe instead of the light band, iron bar grates over every window"""
    sh.box(s, x1, YB, z1, x2, YB, z2, BASE)
    sh.box(s, x1, YF, z1, x2, YF, z2, BASE)
    sh.outline_top(s, x1 - 1, YB, z1 - 1, x2 + 1, z2 + 1, BASE)          # proud plinth (1 block outside the wall)
    sh.outline_top(s, x1 - 1, YF, z1 - 1, x2 + 1, z2 + 1, BASE)
    sh.box(s, x1 + 1, YF, z1 + 1, x2 - 1, YF, z2 - 1, FLOOR)
    sh.box(s, x1, Y1, z1, x2, YC, z2, WALL)
    sh.box(s, x1 + 1, Y1, z1 + 1, x2 - 1, Y2, z2 - 1, "air")
    sh.box(s, x1 + 1, YC, z1 + 1, x2 - 1, YC, z2 - 1, ROOF)
    sh.outline_top(s, x1, YC, z1, x2, z2, IRON)
    sh.outline_top(s, x1, YR, z1, x2, z2, st.slab("smooth_quartz"))

    def side(fixed, lo, hi, axis, out):
        pos = list(range(lo, hi + 1))
        pil = [p for p in pos if (p - lo) % pil_every == pil_offset]
        for p in pos:
            x, z = (p, fixed) if axis == "x" else (fixed, p)
            ox, oz = (0, out) if axis == "x" else (out, 0)
            face = FACE_OF[(ox, oz)]
            if p in pil:
                sh.box(s, x + ox, YB, z + oz, x + ox, YC, z + oz, BASE)
                if kind == "cryo":
                    sh.box(s, x + ox, 6, z + oz, x + ox, Y2, z + oz, PURPUR_P)
                s.set(x + ox, YR, z + oz, st.slab("polished_deepslate"))
                s.set(x, YC, z, BASE)
                if pil.index(p) % 2 == 1:
                    s.set(x + ox * 2, Y2, z + oz * 2, st.end_rod(face))       # lamp sticking out of the pilaster
            else:
                dist = min(abs(p - q) for q in pil)
                s.set(x, 6, z, GLASS_T)
                s.set(x, 7, z, GLASS_T)
                s.set(x + ox, YC, z + oz, st.stairs("quartz", OPP[face], "top"))   # cornice bevel under the roof edge
                if kind == "cont":
                    s.set(x + ox, Y1, z + oz, HAZARD[(p - lo) % 2])
                    s.set(x + ox, 6, z + oz, BARS)
                    s.set(x + ox, 7, z + oz, BARS)
                elif dist == 1:
                    s.set(x, Y1, z, LANT)                                   # floor-level light band
                    s.set(x + ox, Y1, z + oz, GLASS_T)
                if dist == 2:
                    if kind != "cont":
                        vent(s, x + ox, Y1, z + oz, face)
                    if kind == "cryo":
                        s.set(x, 7, z, FROG)
                    s.set(x, Y2, z, "minecraft:quartz_bricks")
    side(z1, x1 + 1, x2 - 1, "x", -1)
    side(z2, x1 + 1, x2 - 1, "x", 1)
    side(x1, z1 + 1, z2 - 1, "z", -1)
    side(x2, z1 + 1, z2 - 1, "z", 1)
    for (x, z) in ((x1, z1), (x1, z2), (x2, z1), (x2, z2)):
        sh.box(s, x, YB, z, x, YC, z, BASE)
        s.set(x, YR, z, IRON)
    # ceiling lights: two rows across the wing, every lantern is capped by a raised roof strip (see roof_details)
    # so the roof reads as a solid plate with ribs from above, not as scattered glowing dots
    for x in (x1 + 4, x2 - 4):
        for z in range(z1 + 3, z2 - 2, 4):
            s.set(x, YC, z, LANT)


def roof_details(s, x1, z1, x2, z2, seed=1, solar=False, rod=True, far="west"):
    """Structured flat roof (y9 top, y10 details): two raised strips over the lantern rows, framed skylight with
    capped lanterns, AC unit with a duct run to the parapet, a straight vent row, edge lights, lightning rod."""
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    # raised strips (light gray slabs) across the wing, over the ceiling lantern rows
    for x in (x1 + 4, x2 - 4):
        for z in range(z1 + 1, z2):
            s.set(x, YR, z, st.slab("polished_andesite" if (z - z1) % 4 else "smooth_stone"))
    # skylight: 3x3 glass framed by a deepslate slab ring; two lanterns hidden under the ring's E/W sides
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            s.set(cx + dx, YC, cz + dz, GLASS)
    sh.outline_top(s, cx - 2, YR, cz - 2, cx + 2, cz + 2, st.slab("polished_deepslate"))
    s.set(cx - 2, YC, cz, LANT)
    s.set(cx + 2, YC, cz, LANT)
    # AC unit (basalt, bars on top) and a duct running from it along the north strip to the far parapet
    ux, uz = x1 + 2, z1 + 2
    sh.box(s, ux, YR, uz, ux + 1, YR + 1, uz + 1, BASALT)
    s.set(ux, YR + 2, uz, BARS); s.set(ux + 1, YR + 2, uz, BARS)
    s.set(ux, YR + 2, uz + 1, BARS); s.set(ux + 1, YR + 2, uz + 1, BARS)
    vent(s, ux - 1, YR, uz, "west"); vent(s, ux - 1, YR, uz + 1, "west")
    for x in range(ux + 2, x2 - 1):
        s.set(x, YR, uz, PIPE_OLD if x in (ux + 2, x2 - 2) else st.log(BASALT, "x"))
    s.set(x2 - 2, YR + 1, uz, st.trapdoor("iron", "north", "top", open=False))
    # vent row: a straight line of iron trapdoors along the south edge
    for x in range(x1 + 6, x2 - 5):
        if s.is_air(x, YR, z2 - 2) and s.get(x, YC, z2 - 2) == ROOF:
            s.set(x, YR, z2 - 2, st.trapdoor("iron", "south", "bottom", open=False))
    # low light strip along the far (short) edge of the wing: lanterns set into the parapet every 4
    xe = x1 if far == "west" else x2
    for z in range(z1 + 2, z2 - 1, 4):
        s.set(xe, YR, z, LANT)
    if rod:
        s.set(x2 - 2, YR, z2 - 3, IRON)
        s.set(x2 - 2, YR + 1, z2 - 3, st.lightning_rod("up"))
    # wind-blown snow on the roof: a thin contiguous lick along the inner south and east parapet (leeward side)
    for x in range(x1 + 1, x2):
        n = sh.value_noise2(x, z2, seed + 5, 4.0)
        if n > 0.3 and s.is_air(x, YR, z2 - 1) and s.get(x, YC, z2 - 1) == ROOF:
            s.set(x, YR, z2 - 1, st.snow_layer(1 + int(n * 2.5)))
    for z in range(z1 + 1, z2):
        n = sh.value_noise2(x2, z, seed + 5, 4.0)
        if n > 0.3 and s.is_air(x2 - 1, YR, z) and s.get(x2 - 1, YC, z) == ROOF:
            s.set(x2 - 1, YR, z, st.snow_layer(1 + int(n * 2.5)))
    if solar:
        # exterior ladder up the east wall, roof hatch, and a dish on a pole
        zl = z1 + 4
        for y in range(Y1, YC + 1):
            s.set(x2 + 1, y, zl, "minecraft:ladder[facing=east]")
        s.set(x2, YR, zl, st.trapdoor("iron", "east", "bottom", open=True))
        s.set(x2 - 1, YR, zl, st.trapdoor("iron", "west", "bottom", open=False))
        dx_, dz_ = x2 - 2, z2 - 5
        sh.box(s, dx_, YR, dz_, dx_, YR + 3, dz_, BASE)
        s.set(dx_, YR + 4, dz_, IRON)
        for ddx, ddz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            f = FACE_OF[(ddx, ddz)]
            s.set(dx_ + ddx, YR + 4, dz_ + ddz, st.trapdoor("iron", OPP[f], "bottom", open=True))
        s.set(dx_ + 1, YR + 4, dz_ + 1, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(dx_ - 1, YR + 4, dz_ - 1, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(dx_ + 1, YR + 4, dz_ - 1, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(dx_ - 1, YR + 4, dz_ + 1, st.trapdoor("iron", "north", "bottom", open=False))
        s.set(dx_, YR + 5, dz_, st.lightning_rod("up"))
        for z in (z1 + 3, z2 - 3):
            for x in range(cx - 4, cx + 5):
                s.set(x, YR, z, st.slab("polished_deepslate"))
                s.set(x, YR + 1, z, "minecraft:daylight_detector")
            s.set(cx - 5, YR, z, IRON)
            s.set(cx + 5, YR, z, IRON)


def opening(s, x1, y1, z1, x2, y2, z2):
    sh.box(s, x1, y1, z1, x2, y2, z2, "air")


def corridor(s, x1, z1, x2, z2, axis):
    """Glass corridor (3 wide) between two openings: floor y4, glass walls y5..y7, glass roof y8, iron ribs."""
    sh.box(s, x1, YB, z1, x2, YB, z2, BASE)
    sh.box(s, x1, YF, z1, x2, YF, z2, BASE)
    if axis == "x":
        sh.box(s, x1, YF, z1 + 1, x2, YF, z2 - 1, FLOOR)
        sh.box(s, x1, Y1, z1, x2, 8, z1, GLASS)
        sh.box(s, x1, Y1, z2, x2, 8, z2, GLASS)
        sh.box(s, x1, 8, z1 + 1, x2, 8, z2 - 1, GLASS)
        sh.box(s, x1, 9, z1 + 1, x2, 9, z2 - 1, "air")        # no wing cornice left over the corridor roof
        ribs = list(range(x1, x2 + 1, 2))
        zm = (z1 + z2) // 2
        for x in ribs:
            sh.box(s, x, Y1, z1, x, 8, z1, IRON)
            sh.box(s, x, Y1, z2, x, 8, z2, IRON)
            sh.box(s, x, 8, z1, x, 8, z2, IRON)
            s.set(x, 9, z1, st.slab("polished_deepslate")); s.set(x, 9, z2, st.slab("polished_deepslate"))
        for x in range(x1 + 1, x2, 2):
            s.set(x, YF, zm, LANT)
            s.set(x, 7, zm, st.end_rod("down"))                      # ceiling lamp hanging from the glass roof
        for x in (x1 + 1, x2 - 1):
            s.set(x, 9, zm, st.trapdoor("iron", "north", "bottom", open=False))   # roof vents
    else:
        sh.box(s, x1 + 1, 9, z1, x2 - 1, 9, z2, "air")
        sh.box(s, x1 + 1, YF, z1, x2 - 1, YF, z2, FLOOR)
        sh.box(s, x1, Y1, z1, x1, 8, z2, GLASS)
        sh.box(s, x2, Y1, z1, x2, 8, z2, GLASS)
        sh.box(s, x1 + 1, 8, z1, x2 - 1, 8, z2, GLASS)
        xm = (x1 + x2) // 2
        for z in range(z1, z2 + 1, 2):
            sh.box(s, x1, Y1, z, x1, 8, z, IRON)
            sh.box(s, x2, Y1, z, x2, 8, z, IRON)
            sh.box(s, x1, 8, z, x2, 8, z, IRON)
            s.set(x1, 9, z, st.slab("polished_deepslate")); s.set(x2, 9, z, st.slab("polished_deepslate"))
        for z in range(z1 + 1, z2, 2):
            s.set(xm, YF, z, LANT)
            s.set(xm, 7, z, st.end_rod("down"))
        for z in (z1 + 1, z2 - 1):
            s.set(xm, 9, z, st.trapdoor("iron", "north", "bottom", open=False))


# ------------------------------------------------------------------------------------------------ rotunda
def rotunda(s, cx, cz, r=10):
    ytop = 10                   # last white wall row; y11 dark band, y12 iron ring, y13 clerestory glass, dome y14+
    sh.cylinder(s, cx, YB, cz, r + 0.3, 1, BASE, axis="y")
    sh.cylinder(s, cx, YF, cz, r - 1.2, 0, FLOOR, axis="y")
    sh.cylinder(s, cx, Y1, cz, r, ytop - Y1, WALL, axis="y", hollow=True, thickness=1.3)
    sh.cylinder(s, cx, ytop + 1, cz, r, 0, BASE, axis="y", hollow=True, thickness=1.3)
    sh.cylinder(s, cx, ytop + 2, cz, r + 0.4, 0, IRON, axis="y", hollow=True, thickness=1.5)
    sh.ring_stairs(s, cx, ytop + 2, cz, r + 1.4, "polished_deepslate", half="top")     # bevel under the ring
    # clerestory: ring of glass with iron mullions, then the dome
    sh.cylinder(s, cx, ytop + 3, cz, r - 0.6, 0, GLASS, axis="y", hollow=True, thickness=1.3)
    yd = ytop + 4
    ry = 6
    sh.dome(s, cx, yd, cz, r - 0.6, GLASS, hollow=True, thickness=1.4, ry=ry)
    sh.cylinder(s, cx, yd, cz, r - 0.6, 0, IRON, axis="y", hollow=True, thickness=1.3)   # dome base ring
    rd = r - 0.6
    # one thin continuous lattice ring at mid-height: exactly the outermost cells of that dome layer
    yring = yd + 3
    rl = (rd + 0.5) * math.sqrt(max(0.0, 1 - ((yring - yd) / (ry + 0.5)) ** 2))   # dome radius at this layer
    sh.cylinder(s, cx, yring, cz, rl - 0.5, 0, IRON, axis="y", hollow=True, thickness=1.0)
    # 8 continuous ribs: dense parametric sweep along the quarter-ellipse, 6-connected (no diagonal gaps)
    for k in range(8):
        a = k * math.pi / 4
        cells = []
        for i in range(0, 121):
            phi = (i / 120) * (math.pi / 2)
            rr = rd * math.cos(phi)
            c = (round(cx + rr * math.cos(a)), round(yd + ry * math.sin(phi)), round(cz + rr * math.sin(a)))
            if c[1] >= yd + ry - 1 and rr < 1.8:
                break
            if not cells or c != cells[-1]:
                cells.append(c)
        prev = None
        for c in cells:
            if prev is not None:
                steps = [c[0] - prev[0], c[1] - prev[1], c[2] - prev[2]]
                cur = list(prev)
                for axis in (1, 0, 2):            # climb first, then step sideways
                    if steps[axis]:
                        cur[axis] += steps[axis]
                        s.set(cur[0], cur[1], cur[2], BASE)
            else:
                s.set(*c, BASE)
            prev = c
        s.set(round(cx + rd * math.cos(a)), ytop + 3, round(cz + rd * math.sin(a)), IRON)
    sh.cylinder(s, cx, yd + ry, cz, 1.6, 0, BASE, axis="y")
    sh.ring_stairs(s, cx, yd + ry, cz, 2.4, "polished_deepslate", half="bottom")
    s.set(cx, yd + ry + 1, cz, IRON)
    s.set(cx, yd + ry + 2, cz, st.lightning_rod("up"))
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        s.set(cx + dx, yd + ry + 1, cz + dz, st.end_rod("up"))
    # pilasters (8) two blocks proud, windows between them (y6..y9)
    for k in range(8):
        a = k * math.pi / 4 + math.pi / 8
        cells = []
        for rr in (r - 0.3, r + 0.7, r + 1.7):
            x, z = round(cx + rr * math.cos(a)), round(cz + rr * math.sin(a))
            if (x, z) not in cells:
                cells.append((x, z))
        for (x, z) in cells:
            sh.box(s, x, YB, z, x, ytop + 1, z, BASE)
            s.set(x, ytop + 2, z, IRON)
        ox, oz = cells[-1]
        f = sh._facing_to_center(-(ox - cx), -(oz - cz))
        dx, dz = DIRV[f]
        s.set(ox + dx, Y2, oz + dz, st.end_rod(f))
    for x in range(s.w):
        for z in range(s.l):
            d = math.hypot(x - cx, z - cz)
            if r - 1.3 <= d <= r + 0.5:
                a = (math.atan2(z - cz, x - cx) + 2 * math.pi) % (math.pi / 4)
                if 0.10 * math.pi < a < 0.40 * math.pi:
                    for y in (6, 7, 8, 9):
                        if s.get(x, y, z) == WALL:
                            s.set(x, y, z, GLASS_T)
                    if s.get(x, Y1, z) == WALL:
                        s.set(x, Y1, z, "minecraft:quartz_bricks")
    # interior: crystal core on a plinth, console ring, floor light ring
    sh.cylinder(s, cx, YF, cz, 6.5, 0, LANT, axis="y", hollow=True, thickness=1.0)
    sh.cylinder(s, cx, YF, cz, 3.5, 0, BASE, axis="y")
    sh.cylinder(s, cx, Y1, cz, 3.2, 0, BASE, axis="y")
    sh.ring_stairs(s, cx, Y1, cz, 4.0, "polished_deepslate", half="bottom", outward=True)
    sh.cylinder(s, cx, Y1, cz, 2.2, 5, GLASS_T, axis="y", hollow=True, thickness=1.0)
    sh.box(s, cx, Y1, cz, cx, Y1 + 4, cz, "minecraft:amethyst_block")
    s.set(cx, Y1 + 5, cz, "minecraft:amethyst_cluster[facing=up]")
    s.set(cx, Y1, cz, LANT)
    sh.cylinder(s, cx, Y1 + 5, cz, 2.2, 0, IRON, axis="y")
    sh.cylinder(s, cx, Y1 + 6, cz, 1.2, 0, LANT, axis="y")
    for dx, dz in ((3, 0), (-3, 0), (0, 3), (0, -3)):
        s.set(cx + dx, Y1 + 1, cz + dz, st.end_rod("up"))
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        x, z = round(cx + 6 * math.cos(a)), round(cz + 6 * math.sin(a))
        console(s, x, Y1, z)
        s.set(round(cx + 7 * math.cos(a)), Y1, round(cz + 7 * math.sin(a)),
              st.stairs("polished_deepslate", sh._facing_to_center(x - cx, z - cz)))
    # hanging light ring under the dome (iron ring with sea lanterns, hung by 4 chains from the dome)
    ring_y = ytop
    for x in range(s.w):
        for z in range(s.l):
            d = math.hypot(x + 0.5 - (cx + 0.5), z + 0.5 - (cz + 0.5))
            if 4.2 <= d <= 5.6:
                a = math.atan2(z - cz, x - cx)
                near = min(abs(((a - k * math.pi / 4) + math.pi) % (2 * math.pi) - math.pi) for k in range(8))
                s.set(x, ring_y, z, LANT if near < 0.12 else IRON)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        x, z = round(cx + 3.5 * math.cos(a)), round(cz + 3.5 * math.sin(a))
        y = ring_y + 1
        while s.is_air(x, y, z) and y < s.h - 1:
            s.set(x, y, z, st.chain("y"))
            y += 1
    sign(s, cx + 1, Y1 + 1, cz - 3, "north", ["NOYAU HELIX", "cristal source", "ne pas toucher", ""])
    s.add_chest(cx - 6, Y1, cz - 3, "east", "minecraft:chests/ancient_city")


# ------------------------------------------------------------------------------------------------ wings' furniture
def cryo_wing(s, x1, z1, x2, z2):
    """Two rows of pods against the north and south walls, aisle with floor lights in the middle."""
    pods = []
    zc = (z1 + z2) // 2
    for back in (z1 + 1, z2 - 1):
        front = back + (1 if back < zc else -1)
        for x in range(x1 + 3, x2 - 2, 3):
            pods.append((x, front, back))
            s.set(x, Y1, back, PURPUR_P)
            s.set(x, Y1 + 1, back, FROG)
            s.set(x, Y1 + 2, back, FROG)
            s.set(x, Y1 + 3, back, PURPUR_P)
            s.set(x, Y1, front, PURPUR_P)
            s.set(x, Y1 + 1, front, TINT)
            s.set(x, Y1 + 2, front, TINT)
            s.set(x, Y1 + 3, front, PURPUR_P)
            for dx in (-1, 1):
                s.set(x + dx, Y1, back, BASE)
                s.set(x + dx, Y1 + 3, back, st.slab("purpur", "top"))
                s.set(x + dx, Y1, front, st.slab("polished_deepslate"))
    for x in range(x1 + 2, x2 - 1, 2):
        floor_light(s, x, zc)
    for x in range(x1 + 4, x2 - 3, 6):
        console(s, x, Y1, zc - 2)
        s.set(x, Y1 + 2, zc - 2, st.redstone_lamp(True))
        s.set(x, Y1 + 1, zc + 2, st.facing_block("minecraft:observer", "north"))
        s.set(x, Y1, zc + 2, BASE)
    sh.box(s, x1 + 2, Y2, zc, x2 - 2, Y2, zc, st.chain("x"))
    # broken pod: 3rd pod of the north row - glass burst, frost inside, snow, hatch on the floor, a sign
    bx, bf, bb = pods[2]
    s.set(bx, Y1 + 1, bf, "air")
    s.set(bx, Y1 + 2, bf, st.glass_pane())
    s.set(bx, Y1 + 1, bb, ICE)
    s.set(bx, Y1 + 2, bb, BICE)
    s.set(bx, Y1, bf + 1, st.snow_layer(2))
    s.set(bx + 1, Y1, bf + 1, st.snow_layer(1))
    s.set(bx - 1, Y1, bf + 1, st.stairs("purpur", "east"))
    sign(s, bx + 1, Y1 + 2, bf, "south", ["POD 03", "sujet: absent", "porte forcee", "de l interieur"])
    s.set(bx + 1, Y1 + 1, bf, PURPUR_P)
    # end wall: status screen, lockers, loot chest
    screen(s, x1 + 1, Y1 + 1, zc - 2, 5, 2, "east")
    s.add_chest(x1 + 1, Y1, zc + 3, "east", "minecraft:chests/ancient_city")
    s.set(x1 + 1, Y1, zc - 3, "minecraft:barrel[facing=up,open=false]")
    s.set(x1 + 1, Y1, zc + 4, "minecraft:cauldron")
    sign(s, x1 + 1, Y1 + 2, zc + 3, "east", ["CRYO - AILE OUEST", "12 sujets", "T = -196 C", ""])
    sign(s, x1 + 1, Y1 + 2, zc + 4, "east", ["JOURNAL 12", "pods 1-11 OK", "pod 03 vide", "alarme coupee"])


def cryo_tanks(s, x_wall, zc):
    """Two horizontal cryogenic tanks outside the west end wall, on deepslate cradles, piped into the wall."""
    for dz in (-4, 4):
        z = zc + dz
        x0, x1_ = x_wall - 8, x_wall - 1
        sh.box(s, x0, YB, z - 2, x1_, YB, z + 2, BASE)
        sh.box(s, x0 + 1, YF, z - 1, x1_ - 1, YF, z + 1, BASE)
        for x in (x0 + 1, x1_ - 1):
            s.set(x, Y1, z - 2, st.stairs("polished_deepslate", "south"))
            s.set(x, Y1, z + 2, st.stairs("polished_deepslate", "north"))
        sh.cylinder(s, x0 + 1, Y1 + 2, z, 2.0, x1_ - x0 - 2, IRON, axis="x")
        sh.cylinder(s, x0 + 2, Y1 + 2, z, 1.6, x1_ - x0 - 4, "minecraft:white_concrete", axis="x")
        sh.cylinder(s, x0 + 1, Y1 + 2, z, 1.6, 0, IRON, axis="x")
        sh.cylinder(s, x1_ - 1, Y1 + 2, z, 1.6, 0, IRON, axis="x")
        s.set(x0, Y1 + 2, z, st.slab("polished_deepslate", "top"))
        sh.box(s, x0 + 3, Y1 + 2, z, x0 + 5, Y1 + 2, z, GLASS_T)          # level window
        s.set(x0 + 4, Y1 + 5, z, st.end_rod("up"))
        sh.line(s, (x1_, Y1 + 2, z), (x_wall, Y1 + 2, z), PIPE)
        sh.line(s, (x1_, Y1 + 3, z), (x_wall, Y1 + 3, z), PIPE_OLD)
        s.set(x1_, Y1 + 2, z, PIPE_JOINT)
        s.set(x_wall, Y1 + 2, z, "minecraft:cut_copper")
        s.set(x_wall, Y1 + 3, z, "minecraft:cut_copper")
    sign(s, x_wall - 5, Y1, zc, "west", ["AZOTE LIQUIDE", "danger", "", ""])
    s.set(x_wall - 4, Y1, zc, BASE); s.set(x_wall - 4, YF, zc, BASE); s.set(x_wall - 4, YB, zc, BASE)


def control_wing(s, x1, z1, x2, z2):
    zc = (z1 + z2) // 2
    for z in (zc - 3, zc + 3):
        for x in range(x1 + 4, x2 - 6, 2):
            console(s, x, Y1, z)
            if x % 4 == 0:
                s.set(x, Y1 + 2, z, st.redstone_lamp(True))
                s.set(x, Y1 + 3, z, st.chain("y"))
            s.set(x - 1, Y1, z, st.stairs("polished_deepslate", "east"))
            s.set(x + 1, Y1, z, BASE)
            s.set(x + 1, Y1 + 1, z, st.facing_block("minecraft:observer", "west"))
    # 9-wide screen band through the east wall: light-blue glass inside AND outside, sea lanterns in between, iron
    # frame columns - the CONTROL wing's exterior signature (a glowing blue band on the east face)
    for z in range(zc - 4, zc + 5):
        for y in (6, 7, 8):
            s.set(x2 - 2, y, z, GLASS_T)
            s.set(x2 - 1, y, z, LANT)
            s.set(x2, y, z, GLASS_T)
    for z in (zc - 5, zc + 5):
        sh.box(s, x2 - 2, Y1, z, x2 + 1, Y2, z, IRON)
    sh.box(s, x2 - 2, Y1, zc - 4, x2 - 2, Y1, zc + 4, BASE)
    for x in range(x1 + 2, x2 - 3):
        blk = "minecraft:bookshelf" if x % 3 else "minecraft:chiseled_bookshelf[facing=south]"
        s.set(x, Y1, z1 + 1, blk)
        s.set(x, Y1 + 1, z1 + 1, blk if x % 2 else "minecraft:bookshelf")
    for x in (x1 + 4, x1 + 9, x1 + 14):
        s.set(x, Y1, z1 + 3, st.facing_block("minecraft:lectern", "south"))
    for x in range(x1 + 2, x2 - 3):
        s.set(x, Y1, z2 - 1, st.facing_block("minecraft:blast_furnace", "north") if x % 4 == 0
              else st.facing_block("minecraft:observer", "north"))
        s.set(x, Y1 + 1, z2 - 1, st.facing_block("minecraft:observer", "north") if x % 4 else "minecraft:dispenser[facing=north]")
        s.set(x, Y1 + 2, z2 - 1, BARS)
    sh.box(s, x1 + 2, Y1 + 3, z2 - 1, x2 - 3, Y1 + 3, z2 - 1, st.chain("x"))
    for x in range(x1 + 2, x2 - 3, 2):
        floor_light(s, x, zc)
    # loot + signs on the west wall, away from the corridor opening (zc-1..zc+1)
    s.add_chest(x1 + 1, Y1, zc - 4, "east", "minecraft:chests/stronghold_library")
    s.set(x1 + 1, Y1, zc + 4, "minecraft:barrel[facing=up,open=false]")
    sign(s, x1 + 1, Y1 + 2, zc - 4, "east", ["SALLE DE CONTROLE", "acces niveau 4", "", ""])
    sign(s, x1 + 1, Y1 + 2, zc + 4, "east", ["JOURNAL 31", "aile sud isolee", "le sujet est", "dehors"])


def containment_wing(s, x1, z1, x2, z2):
    """Cells on both sides of a central aisle; the far end collapses (see ruin())."""
    xc = (x1 + x2) // 2
    cell_z = [(z1 + 2, z1 + 5), (z1 + 7, z1 + 10), (z1 + 12, z1 + 15)]
    breached = (1, "west")
    for side in ("west", "east"):
        if side == "west":
            ix1, ix2, gx = x1 + 1, x1 + 5, x1 + 6
        else:
            ix1, ix2, gx = x2 - 5, x2 - 1, x2 - 6
        for i, (za, zb) in enumerate(cell_z):
            sh.box(s, ix1, Y1, za - 1, gx, Y2, za - 1, WALL_IN)
            sh.box(s, ix1, Y1, zb + 1, gx, Y2, zb + 1, WALL_IN)
            sh.box(s, gx, Y1, za, gx, 7, zb, GLASS)
            sh.box(s, gx, Y2, za, gx, Y2, zb, IRON)
            zm = (za + zb) // 2
            s.set(gx, Y1, zm, BARS); s.set(gx, Y1 + 1, zm, BARS)
            sx = ix1 + 2
            s.set(sx, Y1, zm, PURPUR)
            s.set(sx, Y1 + 1, zm, LAB["specimen"] if (i + (side == "east")) % 2 else LAB["specimen_alt"])
            s.set(sx, Y2, zm, st.end_rod("down"))
            s.set(ix1 if side == "west" else ix2, Y1, za, "minecraft:cauldron")
            s.set(ix1 if side == "west" else ix2, YF, zb, st.trapdoor("iron", "north", "top", open=False))
            s.set(ix2 if side == "west" else ix1, Y1, zb, st.facing_block("minecraft:observer", "up"))
            if (i, side) == breached:
                sh.box(s, gx, Y1, za + 1, gx, Y1 + 2, zb - 1, "air")
                s.set(gx, Y1 + 2, za + 1, st.glass_pane())
                s.set(gx, Y1, zb - 1, st.glass_pane())
                s.set(gx + 1, Y1, zm, LAB["specimen"])
                s.set(gx + 2, Y1, zm + 1, LAB["specimen"])
                s.set(gx + 1, Y1, zm - 1, st.slab("polished_deepslate"))
                s.set(sx, Y1 + 1, zm, "air")
                s.set(sx + 1, Y1, zm, LAB["specimen"])
                sign(s, gx + 1, Y1 + 2, za - 1, "south", ["CELLULE C-2", "SUJET: ECHAPPE", "ne pas entrer", ""])
    for z in range(z1 + 2, z2 - 1, 2):
        floor_light(s, xc, z)
    console(s, xc - 2, Y1, z1 + 1)
    console(s, xc + 2, Y1, z1 + 1)
    s.set(xc - 2, Y1 + 2, z1 + 1, st.redstone_lamp(True))
    s.set(xc + 2, Y1 + 2, z1 + 1, st.redstone_lamp(True))
    sign(s, xc - 2, Y1 + 3, z1 + 1, "south", ["ZONE 3", "CONTAMINEE", "combinaison", "obligatoire"])
    sign(s, xc + 2, Y1 + 3, z1 + 1, "south", ["JOURNAL 40", "toit effondre", "gel partout", "on remonte"])
    s.add_chest(x1 + 1, Y1, z1 + 1, "south", "minecraft:chests/ancient_city")


def ruin(s, x1, z1, x2, z2, zc0, seed=7):
    """Collapse the far (south) end of a wing: caved roof, rubble, frost creep, snow drifts, icicles."""
    rng = random.Random(seed)
    xc = (x1 + x2) // 2
    # --- roof crater: a big ragged ellipse over the south half (it eats the south half of the skylight frame) plus
    # a smaller secondary hole to the north-west of it
    hole = np.zeros((s.w, s.l), dtype=bool)
    hx, hz, rx, rz = xc + 1, z2 - 4, 6.5, 5.0
    for x in range(x1 + 1, x2):
        for z in range(zc0 - 4, z2 + 1):
            n = sh.value_noise2(x, z, seed, 4.0)
            if math.hypot((x - hx) / rx, (z - hz) / rz) < 0.72 + 0.6 * n:
                hole[x, z] = True
            if math.hypot((x - (xc - 5)) / 2.6, (z - (zc0 - 2)) / 2.0) < 0.6 + 0.5 * n:
                hole[x, z] = True
    for x in range(s.w):
        for z in range(s.l):
            if hole[x, z]:
                for y in range(YC, YR + 4):
                    s.set(x, y, z, "air")
    # --- fallen roof plating: a bent plate of stairs hanging from the crater's north edge down onto a rubble heap
    # (in the aisle, east half, leaving the west half of the aisle walkable)
    for px in (xc + 1, xc + 2):
        zs = [z for z in range(zc0 - 4, z2) if hole[px, z]]
        if not zs:
            continue
        zn = zs[0] - 1
        if zn <= zc0 - 5 or not s.is_air(px, Y2, zn) or s.is_air(px, YC, zn):
            continue
        s.set(px, Y2, zn, st.stairs("polished_andesite", "north"))
        s.set(px, Y2 - 1, zn + 1, st.stairs("polished_andesite", "north"))
        s.set(px, Y1 + 1, zn + 2, st.stairs("polished_andesite", "north"))
        s.set(px, Y1, zn + 3, st.slab("smooth_stone"))
        s.set(px, Y1, zn + 1, "minecraft:cobbled_deepslate")
        s.set(px, Y1 + 1, zn + 1, "minecraft:cobbled_deepslate")
        s.set(px, Y1, zn + 2, "minecraft:cobbled_deepslate")
    # --- south-east corner blown out: the corner column goes completely, the far wall east of the aisle and the
    # east wall's last blocks keep only ragged stubs; a clean 4-wide breach in the south wall lets the snow in
    for x in range(x1 - 1, x2 + 2):
        for z in range(z2 - 9, z2 + 2):
            for y in range(Y1, YR + 2):
                if s.is_air(x, y, z):
                    continue
                b = s.get(x, y, z)
                if not (b in (WALL, WALL_IN, IRON, BASE, ROOF, GLASS_T, GLASS, LANT, "minecraft:quartz_bricks", FROG)
                        or any(k in b for k in ("slab", "glass", "trapdoor", "stairs", "end_rod", "terracotta",
                                                "black_concrete", "iron_bars", "purpur", "ladder"))):
                    continue
                corner = max(0.0, 1.0 - math.hypot((x - (x2 + 1)) / 9.0, (z - (z2 + 1)) / 7.0))
                p = corner * 1.6 - 0.2 + 0.12 * (y - Y1)
                n = sh.value_noise2(x + 7 * y, z, seed + 1, 3.0)
                if p * (0.5 + n) > 0.5:
                    s.set(x, y, z, "air")
    sh.box(s, xc + 1, Y1, z2, xc + 4, Y2, z2 + 1, "air")                      # the breach
    s.set(xc + 4, Y2, z2, WALL); s.set(xc + 1, Y2 - 1, z2, "air")
    # hanging bits: iron bars under the remaining wall tops, pane fragments in the broken window rows
    for x in range(x1, x2 + 2):
        for z in (z2, z2 + 1):
            for y in (Y1, Y1 + 1, Y1 + 2):
                if s.is_air(x, y, z) and not s.is_air(x, y + 1, z) and rng.random() < 0.5:
                    s.set(x, y, z, BARS if rng.random() < 0.6 else st.glass_pane("light_blue"))
    for z in range(z2 - 9, z2 + 1):
        for y in (Y1, Y1 + 1, Y1 + 2):
            if s.is_air(x2, y, z) and not s.is_air(x2, y + 1, z) and rng.random() < 0.5:
                s.set(x2, y, z, BARS if rng.random() < 0.6 else st.glass_pane("light_blue"))
    # ceiling lanterns whose roof cap was blown away: frozen over (no bare glowing dots on the ruined roof)
    for x in range(x1, x2 + 1):
        for z in range(zc0 - 6, z2 + 1):
            if s.get(x, YC, z) == LANT and s.is_air(x, YR, z):
                s.set(x, YC, z, ICE)
    rub = ["minecraft:cobbled_deepslate", WALL, "minecraft:quartz_bricks", st.slab("smooth_quartz"),
           st.stairs("quartz", "north"), st.stairs("quartz", "east", "top"), st.slab("polished_deepslate"),
           BASE, "minecraft:calcite", st.slab("polished_andesite"), st.stairs("polished_andesite", "west", "top")]
    cells = [(x, z) for x in range(x1 + 1, x2) for z in range(zc0 - 4, z2) if hole[x, z] and s.is_air(x, Y1, z)]
    rng.shuffle(cells)
    for (x, z) in cells[: len(cells) // 3]:
        s.set(x, Y1, z, rng.choice(rub))
        if rng.random() < 0.25:
            s.set(x, Y1 + 1, z, rng.choice(rub[:3]))
    # a dense rubble heap in the blown-out corner (inside) and debris thrown outside the breach onto the snow
    for x in range(x2 - 4, x2 + 1):
        for z in range(z2 - 4, z2 + 1):
            if s.is_air(x, Y1, z) and not s.is_air(x, YF, z) and rng.random() < 0.55:
                s.set(x, Y1, z, rng.choice(rub[:3] + [BASE]))
                if rng.random() < 0.35 and s.is_air(x, Y1 + 1, z):
                    s.set(x, Y1 + 1, z, rng.choice(rub[3:7]))
    for _ in range(26):
        x, z = xc + rng.randint(0, 9), z2 + rng.randint(2, 6)
        if s.inside(x, YF, z) and s.is_air(x, YF, z) and s.is_air(x, Y1, z):
            b = rng.choice(rub)
            s.set(x, YF, z, b)
            if "slab" not in b and "stairs" not in b and rng.random() < 0.3:
                s.set(x, Y1, z, rng.choice(rub[3:7]))
    # frost creep: floor first, then the lower walls, with a gradient toward the far end; the EXTERIOR faces of
    # the south wall and the east wall's end get frozen 2-3 blocks up so the damage reads from outside
    frost_ok = (WALL, WALL_IN, FLOOR, BASE, "minecraft:cobbled_deepslate", IRON, ROOF, GLASS_T,
                "minecraft:quartz_bricks") + HAZARD
    for x in range(x1 - 1, x2 + 2):
        for z in range(zc0 - 6, z2 + 2):
            t = (z - (zc0 - 6)) / max(1, z2 - zc0 + 6)
            exterior = z >= z2 or (x >= x2 and z >= z2 - 9)      # south face + east face near the blown corner
            west_face = x <= x1
            for y in range(YB, YR + 1):
                b = s.get(x, y, z)
                if b in frost_ok:
                    n = sh.value_noise2(x + y * 3, z, seed + 2, 4.0)
                    if exterior:
                        k = {YB: 1.0, YF: 1.0, Y1: 0.8, Y1 + 1: 0.5, Y1 + 2: 0.28, Y2: 0.1}.get(y, 0.04)
                        p = (0.35 + 0.65 * t) * (0.5 + n) * k
                    else:
                        k = 1.0 if y <= YF else (0.55 if y == Y1 else 0.25 if y <= Y1 + 1 else 0.08)
                        p = (t * 1.2 - 0.15) * (0.4 + n) * k
                        if west_face:
                            p *= 0.35 if y <= YF else 0.15
                    if rng.random() < p:
                        s.set(x, y, z, BICE if rng.random() < 0.25 else ICE)
    # snow drifts inside under the hole and against the far wall
    for x in range(x1 + 1, x2):
        for z in range(zc0, z2):
            if hole[x, z] or z >= z2 - 3:
                h = sh.value_noise2(x, z, seed + 3, 4.0) * 2.4 + (z - zc0) / (z2 - zc0) * 1.2
                if s.is_air(x, Y1, z):
                    if h > 1.7:
                        s.set(x, Y1, z, SNOW)
                        s.set(x, Y1 + 1, z, st.snow_layer(int(1 + (h - 1.7) * 4)))
                    elif h > 0.8:
                        s.set(x, Y1, z, st.snow_layer(int(1 + (h - 0.8) * 6)))
    # icicles under the remaining roof edge around the hole
    for x in range(x1 + 1, x2):
        for z in range(zc0 - 1, z2 + 1):
            if not s.is_air(x, YC, z) and s.is_air(x, Y2, z):
                near = any(hole[x + dx, z + dz] for dx in (-1, 0, 1) for dz in (-1, 0, 1) if s.inside(x + dx, 0, z + dz))
                if near and rng.random() < 0.6:
                    if rng.random() < 0.5 and s.is_air(x, Y2 - 1, z):
                        s.set(x, Y2, z, st.pointed_dripstone("down", "frustum"))
                        s.set(x, Y2 - 1, z, st.pointed_dripstone("down", "tip"))
                    else:
                        s.set(x, Y2, z, st.pointed_dripstone("down", "tip"))
    # icicles hanging off the outer broken edge
    for x in range(x1 - 1, x2 + 2):
        for z in (z2, z2 + 1):
            if not s.is_air(x, YC, z) and s.is_air(x, Y2, z) and rng.random() < 0.3:
                s.set(x, Y2, z, st.pointed_dripstone("down", "tip"))
    return hole


def cleanup_isolated(s, x1, z1, x2, z2, y_min):
    """Remove blocks in a region that have no 6-neighbour (loose leftovers of the ruin pass)."""
    for _ in range(2):
        for x in range(max(0, x1), min(s.w, x2 + 1)):
            for z in range(max(0, z1), min(s.l, z2 + 1)):
                for y in range(y_min, s.h):
                    if s.is_air(x, y, z):
                        continue
                    if all(s.is_air(x + dx, y + dy, z + dz) for dx, dy, dz in
                           ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))):
                        s.set(x, y, z, "air")


def snow_drifts(s, seed=4):
    """Wind-blown snow drifts: the wind comes from the north-west, so the south and east faces of every wall get
    deep wedge-shaped drifts (full block + layers against the wall, stepping down over 5 blocks with a ragged noisy
    edge) while the north / west faces only get a thin lick of 1-2 layers."""
    solid = s.data != 0
    wall = solid[:, Y1, :] & (solid[:, YF, :] | solid[:, YB, :])
    snow = np.zeros((s.w, s.l), dtype=bool)
    N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
    info = {}
    for x in range(s.w):
        for z in range(s.l):
            if solid[x, YF, z] or solid[x, Y1, z]:
                continue
            best, lee = 9, False
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    xx, zz = x + dx, z + dz
                    if s.inside(xx, Y1, zz) and wall[xx, zz]:
                        d = max(abs(dx), abs(dz))
                        l = dx <= 0 and dz <= 0                     # wall lies to the NW of this cell: leeward
                        if d < best or (d == best and l):
                            best, lee = d, l
            if best <= 3:
                info[(x, z)] = (best, lee)
    # grow the drift outward from the walls, one distance ring at a time: a cell only gets snow when a 4-neighbour
    # is the wall itself (ring 1) or already carries snow from a nearer ring -> every drift is one attached wedge
    for d in (1, 2, 3):
        for _ in range(2):
            for (x, z), (dd, lee) in info.items():
                if dd != d or snow[x, z]:
                    continue
                n = sh.value_noise2(x, z, seed, 5.0)
                if lee:
                    if d == 1:
                        n1 = sh.value_noise2(x + 50, z + 50, seed + 1, 3.0)
                        layers = 4 + int(n * 3 + n1 * 3)            # 4..9 (9 = snow block + 1 layer)
                    elif d == 2:
                        if n < 0.15:
                            continue
                        layers = 3 + int(n * 3)
                    else:
                        if n < 0.45:
                            continue
                        layers = 1 + int(n * 2)
                else:
                    if d > 1 or n < 0.5:
                        continue
                    layers = 1 + int(n * 2)
                attached = False
                for dx, dz in N4:
                    xx, zz = x + dx, z + dz
                    if not s.inside(xx, Y1, zz):
                        continue
                    if (d == 1 and wall[xx, zz]) or (snow[xx, zz] and info[(xx, zz)][0] < d):
                        attached = True
                        break
                if not attached:
                    continue
                snow[x, z] = True
                if layers >= 9:
                    s.set(x, YF, z, SNOW)
                    s.set(x, Y1, z, st.snow_layer(max(1, min(8, layers - 8))))
                else:
                    s.set(x, YF, z, st.snow_layer(max(1, min(8, layers))))


def specimen_trail(s, x2, z2, seed=5):
    """The escaped specimen crystallises what it touches: ice patches and amethyst buds trailing away from the
    blown-out corner of the containment wing, out into the snow."""
    rng = random.Random(seed)
    pts = [(x2 - 2, z2 - 2), (x2 + 1, z2 + 1), (x2 + 4, z2 + 1), (x2 + 7, z2 - 1), (x2 + 10, z2 - 4)]
    for i, (px, pz) in enumerate(pts):
        for dx in range(-2, 3):
            for dz in range(-2, 3):
                x, z = px + dx, pz + dz
                if not s.inside(x, YF, z) or math.hypot(dx, dz) > 2.2 or rng.random() < 0.35:
                    continue
                if i == 0:
                    if s.is_air(x, Y1, z) and not s.is_air(x, YF, z):
                        s.set(x, Y1, z, ICE if rng.random() < 0.6 else "minecraft:amethyst_block")
                elif s.is_air(x, YF, z):
                    s.set(x, YB, z, BICE if rng.random() < 0.3 else ICE)
                    if rng.random() < 0.3:
                        s.set(x, YF, z, rng.choice(["minecraft:amethyst_cluster[facing=up]",
                                                    "minecraft:large_amethyst_bud[facing=up]",
                                                    "minecraft:medium_amethyst_bud[facing=up]"]))
    # a few big crystals at the end of the trail
    ex, ez = pts[-1]
    sh.box(s, ex, YB, ez, ex, Y1 + 1, ez, "minecraft:amethyst_block")
    s.set(ex, Y1 + 2, ez, "minecraft:amethyst_cluster[facing=up]")
    s.set(ex + 1, YB, ez, "minecraft:amethyst_block"); s.set(ex + 1, YF, ez, "minecraft:amethyst_block")
    s.set(ex + 1, Y1, ez, "minecraft:amethyst_cluster[facing=up]")
    s.set(ex - 1, YB, ez + 1, "minecraft:amethyst_block")
    s.set(ex - 1, YF, ez + 1, "minecraft:medium_amethyst_bud[facing=up]")
    # amethyst growing inside the ruin too
    for _ in range(10):
        x, z = rng.randint(x2 - 14, x2 - 1), rng.randint(z2 - 9, z2 - 1)
        if s.is_air(x, Y1, z) and not s.is_air(x, YF, z) and "ice" in s.get(x, YF, z):
            s.set(x, Y1, z, rng.choice(["minecraft:amethyst_cluster[facing=up]", "minecraft:large_amethyst_bud[facing=up]"]))


# ------------------------------------------------------------------------------------------------ exterior props
def porch(s, cx, z_wall, z_out):
    """Entrance corridor + canopy going north from the rotunda wall at z_wall down to the snow at z_out."""
    x1, x2 = cx - 2, cx + 2
    sh.box(s, x1, YB, z_out + 1, x2, YB, z_wall, BASE)
    sh.box(s, x1, YF, z_out + 1, x2, YF, z_wall, BASE)
    sh.box(s, x1 + 1, YF, z_out + 1, x2 - 1, YF, z_wall, FLOOR)
    sh.box(s, x1, Y1, z_out + 1, x2, 8, z_wall, WALL)
    sh.box(s, x1 + 1, Y1, z_out + 1, x2 - 1, 7, z_wall, "air")
    sh.box(s, x1, 8, z_out + 1, x2, 8, z_wall, IRON)
    sh.box(s, x1 + 1, 8, z_out + 2, x2 - 1, 8, z_wall, ROOF)
    sh.outline_top(s, x1, 9, z_out + 1, x2, z_wall, st.slab("smooth_quartz"))
    for z in range(z_out + 3, z_wall - 1, 2):
        s.set(x1, 6, z, GLASS_T); s.set(x2, 6, z, GLASS_T)
        s.set(x1 - 1, Y1, z + 1, BASE); s.set(x1 - 1, YF, z + 1, BASE)
        s.set(x2 + 1, Y1, z + 1, BASE); s.set(x2 + 1, YF, z + 1, BASE)
        s.set(x1 - 1, Y1 + 1, z + 1, st.end_rod("up")); s.set(x2 + 1, Y1 + 1, z + 1, st.end_rod("up"))
    # airlock: outer leaves = iron trapdoors swung open against the jambs, then a real double iron door 2 blocks
    # further in (2 wide, iron jamb column with the call button), sea lanterns over both
    zd = z_out + 1
    for y in (Y1, Y1 + 1):
        s.set(x1 + 1, y, zd, st.trapdoor("iron", "east", "top" if y == Y1 else "bottom", open=True))
        s.set(x2 - 1, y, zd, st.trapdoor("iron", "west", "top" if y == Y1 else "bottom", open=True))
    s.set(cx + 2, Y1 + 1, zd - 1, st.button("stone", "wall", "north"))
    s.set(cx - 2, Y1 + 1, zd - 1, st.button("stone", "wall", "north"))
    sh.box(s, x1 + 1, Y1 + 2, zd, x2 - 1, Y1 + 2, zd, LANT)
    zi = zd + 3
    s.set(cx - 1, Y1, zi, st.door("iron", "north", "lower", "left"))
    s.set(cx - 1, Y1 + 1, zi, st.door("iron", "north", "upper", "left"))
    s.set(cx, Y1, zi, st.door("iron", "north", "lower", "right"))
    s.set(cx, Y1 + 1, zi, st.door("iron", "north", "upper", "right"))
    sh.box(s, cx + 1, Y1, zi, cx + 1, Y1 + 1, zi, IRON)
    s.set(cx + 1, Y1 + 1, zi - 1, st.button("stone", "wall", "north"))
    s.set(cx + 1, Y1 + 1, zi + 1, st.button("stone", "wall", "south"))
    sh.box(s, cx - 1, Y1 + 2, zi, cx + 1, Y1 + 2, zi, LANT)
    # canopy: 2 deepslate pillars + slab roof with end rods
    for x in (x1 - 1, x2 + 1):
        sh.box(s, x, YB, z_out - 3, x, 8, z_out - 3, BASE)
        s.set(x, 9, z_out - 3, IRON)
    sh.box(s, x1 - 1, 9, z_out - 4, x2 + 1, 9, z_out, st.slab("smooth_quartz", "top"))
    sh.box(s, x1 - 1, 9, z_out - 3, x2 + 1, 9, z_out, IRON)
    sh.box(s, x1, 9, z_out - 2, x2, 9, z_out, ROOF)
    sh.box(s, x1 - 1, 9, z_out - 4, x2 + 1, 9, z_out - 4, st.stairs("quartz", "south", "top"))
    for x in (x1, x2):
        s.set(x, 8, z_out - 1, st.end_rod("down"))
    sh.box(s, x1 - 1, YF, z_out - 3, x2 + 1, YF, z_out, BASE)
    sh.box(s, x1, YF, z_out - 3, x2, YF, z_out, FLOOR)
    sh.box(s, x1 - 1, YF, z_out - 4, x2 + 1, YF, z_out - 4, st.stairs("polished_deepslate", "south"))
    for x in range(x1, x2 + 1):
        for z in range(z_out - 9, z_out - 4):
            if s.is_air(x, YB, z):
                s.set(x, YB, z, FLOOR)
    sign(s, cx + 1, Y1 + 1, zd - 1, "north", ["LABORATOIRE", "HELIX", "site 3 - nord", ""])
    sign(s, cx - 1, Y1 + 1, zd - 1, "north", ["ACCES", "RESTREINT", "badge requis", ""])
    for x in (x1 - 2, x2 + 2):
        s.set(x, YB, z_out - 6, BASE)
        s.set(x, YF, z_out - 6, BASE)
        s.set(x, Y1, z_out - 6, LANT)
        s.set(x, Y1 + 1, z_out - 6, st.trapdoor("iron", "north", "top", open=False))


def chain_line(s, p1, p2, block="minecraft:chain"):
    """6-connected line of chain blocks whose axis follows the local direction (guy wires, hanging cables)."""
    x1, y1, z1 = p1; x2, y2, z2 = p2
    n = max(abs(x2 - x1), abs(y2 - y1), abs(z2 - z1), 1) * 3
    prev = None
    for i in range(n + 1):
        t = i / n
        c = (round(x1 + (x2 - x1) * t), round(y1 + (y2 - y1) * t), round(z1 + (z2 - z1) * t))
        if c == prev:
            continue
        if prev is None:
            s.set(*c, st.log(block, "y"))
        else:
            cur = list(prev)
            for axis in (1, 0, 2):
                d = c[axis] - prev[axis]
                if d:
                    cur[axis] += d
                    s.set(cur[0], cur[1], cur[2], st.log(block, "xyz"[axis]))
        prev = c


def antenna_mast(s, x, z, h=14):
    """2x2 lattice mast (iron bars with an iron core every 4 blocks) on a deepslate pad, 4 chain guy wires to
    anchor posts, a horizontal 3x3 dish with an end-rod feed, red beacon lamps and a lightning rod on top."""
    # pad: 6x6 buried band, 4x4 deepslate top with slab / stair skirt
    sh.box(s, x - 2, YB, z - 2, x + 3, YB, z + 3, BASE)
    sh.box(s, x - 2, YF, z - 2, x + 3, YF, z + 3, st.slab("polished_deepslate"))
    sh.box(s, x - 1, YF, z - 1, x + 2, YF, z + 2, BASE)
    for dx, dz, f in ((-2, 0, "east"), (3, 0, "west"), (0, -2, "south"), (0, 3, "north")):
        for k in (0, 1):
            xx = x + dx if dx else x + k
            zz = z + dz if dz else z + k
            s.set(xx, YF, zz, BASE)
            s.set(xx, Y1, zz, st.stairs("polished_deepslate", f))
    # mast body
    core = [(x, z), (x + 1, z), (x, z + 1), (x + 1, z + 1)]
    for (px, pz) in core:
        sh.box(s, px, Y1, pz, px, Y1 + 1, pz, IRON)
        for y in range(Y1 + 2, YF + h):
            s.set(px, y, pz, IRON if (y - Y1) % 4 == 0 else BARS)
        s.set(px, YF + h, pz, st.redstone_lamp(True))
        s.set(px, YF + h + 1, pz, IRON)
    s.set(x, YF + h + 2, z, st.lightning_rod("up"))
    s.set(x + 1, YF + h + 2, z + 1, st.end_rod("up"))
    for (px, py_, pz, f) in ((x - 1, YF + h + 1, z, "west"), (x + 2, YF + h + 1, z + 1, "east"),
                             (x, YF + h + 1, z - 1, "north"), (x + 1, YF + h + 1, z + 2, "south")):
        s.set(px, py_, pz, st.end_rod(f))
    # cables: a 4-way crossarm at y+10 (iron root + thin deepslate-wall arms) and one straight VERTICAL chain drop
    # from every arm tip to a buried anchor post (no diagonal dotted lines - cables are straight or vertical)
    ya = YF + 10
    arms = (((x - 1, z), (x - 2, z), (x - 3, z), (x - 4, z)),
            ((x + 2, z + 1), (x + 3, z + 1), (x + 4, z + 1), (x + 5, z + 1)),
            ((x, z - 1), (x, z - 2), (x, z - 3), (x, z - 4)),
            ((x + 1, z + 2), (x + 1, z + 3), (x + 1, z + 4), (x + 1, z + 5)))
    for arm in arms:
        for i, (ax, az) in enumerate(arm):
            s.set(ax, ya, az, IRON if i == 0 else "minecraft:polished_deepslate_wall")
        ax, az = arm[-1]
        s.set(ax, ya + 1, az, st.end_rod("up"))
        s.set(ax, YB, az, BASE)
        s.set(ax, YF, az, BASE)
        s.set(ax, Y1, az, "minecraft:polished_deepslate_wall")
        s.set(ax, Y1 + 1, az, IRON)
        for y in range(Y1 + 2, ya):
            s.set(ax, y, az, st.chain("y"))
    for y in (Y1, Y1 + 1):
        s.set(x - 1, y, z + 1, "minecraft:ladder[facing=west]")
    # dish: iron arm to the east, hub + light gray slab petals + iron trapdoor corners, end rod feed
    yd_ = YF + 7
    hx, hz = x + 3, z
    s.set(x + 2, yd_, z, IRON)
    s.set(hx, yd_, hz, IRON)
    for (dx, dz) in ((1, 0), (0, 1), (0, -1)):
        s.set(hx + dx, yd_, hz + dz, st.slab("polished_andesite"))
    for (dx, dz) in ((-1, 1), (-1, -1), (1, 1), (1, -1)):
        s.set(hx + dx, yd_, hz + dz, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(hx, yd_ + 1, hz, st.end_rod("up"))
    s.set(hx, yd_ + 2, hz, "minecraft:daylight_detector")
    # equipment box + barrel at the foot
    s.set(x - 1, Y1, z + 2, st.facing_block("minecraft:observer", "south"))
    s.set(x + 2, Y1, z - 1, "minecraft:barrel[facing=up,open=false]")
    sign(s, x + 2, Y1 + 1, z + 1, "east", ["RELAIS RADIO", "portee 40 km", "pas de reponse", ""])   # on the iron core


def generator(s, x, z, pipe_to):
    """Generator block outside: basalt body on a deepslate pad, copper pipes running to the wall at pipe_to."""
    sh.box(s, x - 3, YB, z - 2, x + 3, YB, z + 2, BASE)
    sh.box(s, x - 3, YF, z - 2, x + 3, YF, z + 2, BASE)
    sh.box(s, x - 2, YF, z - 1, x + 2, YF, z + 1, "minecraft:deepslate_tiles")
    sh.box(s, x - 2, Y1, z - 1, x + 2, Y1 + 2, z + 1, BASALT)
    sh.box(s, x - 1, Y1 + 1, z - 2, x + 1, Y1 + 1, z + 2, IRON)
    sh.box(s, x - 2, Y1 + 3, z - 1, x + 2, Y1 + 3, z + 1, st.slab("polished_deepslate"))
    s.set(x, Y1 + 3, z, PIPE_JOINT)
    s.set(x, Y1 + 4, z, st.campfire(soul=True))
    for dx, f in ((-3, "west"), (3, "east")):
        vent(s, x + dx, Y1, z, f)
        vent(s, x + dx, Y1 + 2, z, f)
    s.set(x - 2, Y1 + 1, z - 2, st.redstone_lamp(True))
    s.set(x + 2, Y1 + 1, z - 2, "minecraft:daylight_detector")
    s.set(x + 3, Y1, z + 1, st.facing_block("minecraft:blast_furnace", "east"))
    s.set(x - 3, Y1, z + 1, "minecraft:barrel[facing=up,open=false]")
    # two pipes (weathered / oxidized copper) to the control wing wall, raw copper only at the generator joints,
    # carried on deepslate-wall supports every 3 blocks
    px, pz = pipe_to
    sh.line(s, (x, Y1, z + 2), (x, Y1, pz - 1), PIPE)
    sh.line(s, (x - 1, Y1 + 1, z + 2), (x - 1, Y1 + 1, pz - 1), PIPE_OLD)
    s.set(x, Y1, z + 2, PIPE_JOINT)
    s.set(x - 1, Y1 + 1, z + 2, PIPE_JOINT)
    s.set(x, Y1, pz - 1, "minecraft:cut_copper")
    s.set(x - 1, Y1 + 1, pz - 1, "minecraft:cut_copper")
    for zz in range(z + 4, pz - 1, 3):
        s.set(x, YF, zz, "minecraft:polished_deepslate_wall")
        s.set(x - 1, YF, zz, BASE)
        s.set(x - 1, YB, zz, BASE)
        s.set(x, YB, zz, BASE)
        s.set(x - 1, Y1, zz, "minecraft:polished_deepslate_wall")
    for zz in range(z + 3, pz - 1):
        s.set_if_air(x - 1, Y1, zz, st.chain("z"))
    sign(s, x + 3, Y1 + 1, z - 1, "east", ["GENERATEUR 2", "carburant: 4%", "", ""])


# ------------------------------------------------------------------------------------------------ main
def build():
    W, H, L = 84, 24, 66
    s = Schematic(W, H, L, ground=G)
    cx, cz = 44, 29                  # rotunda centre
    R = 10
    # wings x1,z1,x2,z2 - kept 8 blocks away from the rotunda wall (x=34 / x=54, z=39): real glass corridors
    cryo = (8, 21, 26, 37)            # west (the cryo tanks stand at x=0..7)
    ctrl = (62, 21, 80, 37)           # east
    cont = (35, 46, 53, 62)           # south
    wing(s, *cryo, pil_offset=1, kind="cryo")
    wing(s, *ctrl, pil_offset=1, kind="ctrl")
    wing(s, *cont, pil_offset=2, kind="cont")
    roof_details(s, *cryo, seed=1, far="west")
    roof_details(s, *ctrl, seed=2, solar=True, far="east")
    roof_details(s, *cont, seed=3, rod=False, far="west")
    rotunda(s, cx, cz, R)
    opening(s, cryo[2], Y1, cz - 1, cx - 9, 7, cz + 1)
    corridor(s, cryo[2] + 1, cz - 2, cx - 10, cz + 2, "x")
    opening(s, cx + 9, Y1, cz - 1, ctrl[0], 7, cz + 1)
    corridor(s, cx + 10, cz - 2, ctrl[0] - 1, cz + 2, "x")
    opening(s, cx - 1, Y1, cz + 8, cx + 1, 7, cont[1])
    corridor(s, cx - 2, cz + 9, cx + 2, cont[1] - 1, "z")
    opening(s, cx - 1, Y1, 12, cx + 1, 7, 20)
    porch(s, cx, 19, 11)
    cryo_wing(s, *cryo)
    cryo_tanks(s, cryo[0], (cryo[1] + cryo[3]) // 2)
    control_wing(s, *ctrl)
    containment_wing(s, *cont)
    antenna_mast(s, 23, 9)
    generator(s, 73, 11, pipe_to=(73, 21))
    sign(s, cx + 11, Y1 + 1, cz + 9, "north", ["ZONE 3", "CONTAMINEE", "acces interdit", "->"])
    sh.box(s, cx + 11, YB, cz + 9, cx + 11, Y1, cz + 9, BASE)
    hole = ruin(s, cont[0], cont[1], cont[2], cont[3], zc0=cont[1] + 8, seed=7)
    cleanup_isolated(s, cont[0] - 2, cont[1] + 6, cont[2] + 2, cont[3] + 2, Y1)
    # textures + weathering
    sh.texturize(s, WALL, MIX_WALL, seed=5)
    sh.texturize(s, FLOOR, MIX_FLOOR, seed=6)
    sh.texturize(s, ROOF, MIX_ROOF, seed=7)
    sh.texturize(s, BASE, MIX_DARK, seed=8)
    sh.texturize(s, ICE, MIX_ICE, seed=9)
    snow_drifts(s, seed=4)
    specimen_trail(s, cont[2], cont[3], seed=5)
    # (no random snow_cover pass: ground snow is only the attached drifts, roof snow only the leeward parapet lick)
    self_check(s)
    return {"lab_main": s.cropped(pad=1)}


def self_check(s):
    """Structural sanity: no gravity block (concrete powder / sand / gravel) above air anywhere above the snow
    surface, no placeholder floor id left, every ceiling lantern capped."""
    bad = []
    for x in range(s.w):
        for z in range(s.l):
            for y in range(G + 1, s.h):
                b = s.get(x, y, z)
                if ("concrete_powder" in b or b.endswith("sand") or b.endswith("gravel")) and s.is_air(x, y - 1, z):
                    bad.append((x, y, z, b))
    assert not bad, f"gravity blocks over air: {bad[:8]} (+{max(0, len(bad) - 8)} more)"
    assert FLOOR not in s.palette or int((s.data == s.palette[FLOOR]).sum()) == 0, "floor placeholder left"
    uncapped = [(x, z) for x in range(s.w) for z in range(s.l)
                if s.get(x, YC, z) == LANT and s.is_air(x, YR, z) and s.is_air(x, YR + 1, z)]
    assert not uncapped, f"uncapped ceiling lanterns: {uncapped[:8]}"
