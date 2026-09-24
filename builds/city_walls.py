"""
Villain tech-city fortification kit: four tileable schematics sharing one wall profile.

  city_wall_segment  16 x 5   (x=0..15, z=0..4)   wall line z=0..4, outer (north) face at z=0
  city_wall_corner   16 x 16  L-corner, arms on z=2..6 (east arm) and x=2..6 (south arm), 9x9 tower at x,z=0..8
  city_gate          24 x 12  twin towers + 6-wide arch; wall line z=2..6 (outer face z=2)
  city_watchtower    10 x 10  stand-alone slender tower on legs

Common vertical profile (ground = 1):
  y 0..1 foundation (polished deepslate, buried)   y 2 plinth   y 3 steel trim (polished basalt)
  y 4 plinth bevel   y 5 magenta neon band (sea lanterns behind)   y 6..8 slits / vents   y 9 steel string course
  y 10..12 body (panels, chains)   y 13 purple neon line   y 14 walkway floor (lit strip)   y 15 railings (wall top)

PLACEMENT (WorldEdit //paste puts the origin at (w//2, ground, l//2) of each file):
  * The wall line is z=0..4 in the SEGMENT but z=2..6 in the CORNER and the GATE (their towers protrude 2 blocks
    outward, toward -z). When pasting on a grid, offset the segment by +2 in z relative to a corner or a gate,
    or paste the corner/gate 2 blocks further out (toward the enemy side).
  * Seam piers: segment x=0 and x=15, corner x=15 (east arm) and z=15 (south arm), gate x=0 and x=23.
    Two butted seam piers form one 2-wide pier with a froglight lamp post on each side.
  * Corner: outer faces look north (z=0) and west (x=0); use //rotate 90/180/270 for the other corners.
  * Everything is symmetric, so //flip is safe.
"""
import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import VILLAIN, MIX_BLACK

G = 1
BASE = "minecraft:polished_deepslate"
TRIM = "minecraft:polished_basalt[axis=y]"    # lighter steel band that draws the silhouette
BODY = VILLAIN["wall"]                          # polished_blackstone_bricks (textured with MIX_BLACK at the end)
BODY_SMOOTH = "minecraft:polished_blackstone"
CHISEL = "minecraft:chiseled_polished_blackstone"
GLASS = VILLAIN["glass"]                        # purple
GLASS2 = VILLAIN["glass_alt"]                   # magenta
TINT = "minecraft:tinted_glass"
FROG = VILLAIN["light"]                         # pearlescent froglight
LANT = "minecraft:sea_lantern"
RAIL = VILLAIN["railing"]                       # polished_blackstone_brick_wall
IRON = "minecraft:iron_block"
BARS = "minecraft:iron_bars"
PIPE = VILLAIN["pipe"]                          # oxidized copper
PIPE_CUT = VILLAIN["pipe_cut"]
PURPUR = "minecraft:purpur_pillar"
BONE = st.log("minecraft:bone_block", "x")
CRYSTAL = "minecraft:amethyst_cluster[facing=up,waterlogged=false]"
SIGN = "minecraft:warped_wall_sign"
LADDER = "minecraft:ladder"

Y_PLINTH, Y_BODY0, Y_ACC, Y_COURSE, Y_NEON, Y_FLOOR, Y_RAIL = 2, 4, 5, 9, 13, 14, 15
STAIR_T = "deepslate_tile"
STAIR_B = "polished_blackstone_brick"

# stairs facing so that the sloped edge looks toward `face`
_BEVEL_DOWN = {"north": "south", "south": "north", "west": "east", "east": "west"}
_OPP = {"north": "south", "south": "north", "west": "east", "east": "west", "up": "down", "down": "up"}
_DIR = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


# --------------------------------------------------------------------------------------- helpers
def vent(s, x, y, z, face):
    """Iron trapdoor lying flat against the wall behind it (a vent / access panel). `face` = outward direction."""
    s.set(x, y, z, st.trapdoor("iron", face, "top", open=True))


def leaf(s, x, y, z, hug):
    """Open iron trapdoor standing against its neighbour in direction `hug` (blast-door leaf on a jamb)."""
    s.set(x, y, z, st.trapdoor("iron", _OPP[hug], "bottom", open=True))


def frame_light(s, x, y, z):
    """Searchlight: sea lantern in a frame of iron trapdoors (4 sides + lid)."""
    s.set(x, y, z, LANT)
    s.set(x, y, z - 1, st.trapdoor("iron", "north", "bottom", open=True))
    s.set(x, y, z + 1, st.trapdoor("iron", "south", "bottom", open=True))
    s.set(x - 1, y, z, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(x + 1, y, z, st.trapdoor("iron", "east", "bottom", open=True))
    s.set(x, y + 1, z, st.trapdoor("iron", "north", "bottom", open=False))


def crystal_spike(s, x, y, z, post=2):
    """Crown spike in the world's crystal motif: a wall post topped by an amethyst cluster."""
    for i in range(post):
        s.set(x, y + i, z, RAIL)
    s.set(x, y + post, z, CRYSTAL)


def lamp_post(s, x, y, z):
    s.set(x, y, z, FROG)
    s.set(x, y + 1, z, st.trapdoor("iron", "north", "top", open=False))


def neon(s, x, y, z, glass=GLASS):
    """Glass on the face with a sea lantern behind it (only if the cell behind is free to take one)."""
    s.set(x, y, z, glass)


def wall_run(s, x0, x1, z0, piers, details=True):
    """Straight wall along x from x0..x1 (inclusive) occupying z0..z0+4. `piers` = x positions with the full
    5-thick profile; everything else is the recessed 3-thick body with two neon lines, a string course, slits,
    vents, panels and the bevels. The outer face is at z0 (north), the city side at z0+4."""
    za, zb = z0, z0 + 4
    for x in range(x0, x1 + 1):
        full = x in piers
        sh.box(s, x, 0, za, x, Y_PLINTH, zb, BASE)                              # foundation + plinth
        sh.box(s, x, Y_PLINTH + 1, za, x, Y_PLINTH + 1, zb, TRIM)              # steel band
        if full:
            sh.box(s, x, Y_BODY0, za, x, Y_FLOOR, zb, BODY)
            s.set(x, Y_RAIL, za, BODY)
            s.set(x, Y_RAIL, zb, BODY)
        else:
            sh.box(s, x, Y_BODY0, za + 1, x, Y_NEON - 1, zb - 1, BODY)
            s.set(x, Y_BODY0, za, st.stairs(STAIR_T, "south"))                   # plinth bevel
            s.set(x, Y_BODY0, zb, st.stairs(STAIR_T, "north"))
            s.set(x, Y_ACC, za + 1, GLASS2)                                     # magenta band at eye height
            s.set(x, Y_ACC, za + 2, LANT)
            s.set(x, Y_ACC, zb - 1, GLASS2)
            s.set(x, Y_COURSE, za + 1, TRIM)                                    # steel string course
            s.set(x, Y_COURSE, zb - 1, TRIM)
            s.set(x, Y_NEON, za + 1, GLASS)                                     # purple neon line
            s.set(x, Y_NEON, za + 2, LANT)
            s.set(x, Y_NEON, zb - 1, GLASS)
            s.set(x, Y_FLOOR, za, st.stairs(STAIR_T, "south", "top"))            # overhang bevel
            s.set(x, Y_FLOOR, zb, st.stairs(STAIR_T, "north", "top"))
            s.set(x, Y_FLOOR, za + 1, BASE)
            s.set(x, Y_FLOOR, za + 2, GLASS)                                    # lit floor strip
            s.set(x, Y_FLOOR, zb - 1, BASE)
            s.set(x, Y_RAIL, za, RAIL)
            s.set(x, Y_RAIL, zb, RAIL)
    if not details:
        return
    xs = sorted(piers)
    gaps = [(a + 1, b - 1) for a, b in zip(xs, xs[1:]) if b - a > 2]
    for (ga, gb) in gaps:
        n = gb - ga + 1
        cx = ga + n // 2 - 1                      # left cell of the central pair
        if n >= 6:
            # 2x2 iron-bar vent over a dark void, flanked by two 1x3 magenta arrow slits (lit from behind)
            sh.box(s, cx, 7, za + 1, cx + 1, 8, za + 1, BARS)
            sh.box(s, cx, 6, za + 2, cx + 1, 8, za + 2, TINT)
            for sx in (cx - 1, cx + 2):
                for y in (6, 7, 8):
                    s.set(sx, y, za + 1, GLASS2)
                    s.set(sx, y, za + 2, LANT)
            # rivets at the plinth bevel level and iron panels under the neon line, next to each pier
            s.set(ga, 7, za, st.button("polished_blackstone", "wall", "north"))
            s.set(gb, 7, za, st.button("polished_blackstone", "wall", "north"))
            vent(s, ga, 11, za, "north")
            vent(s, gb, 11, za, "north")
            vent(s, ga, 10, za, "north")
            vent(s, gb, 10, za, "north")
        # chains hanging from the overhang with a soul lantern, next to each pier
        for x in (ga + 1, gb - 1):
            s.set(x, Y_NEON, za, st.chain("y"))
            s.set(x, Y_NEON - 1, za, st.chain("y"))
            s.set(x, Y_NEON - 2, za, st.lantern(soul=True, hanging=True))
        # copper drainage pipe on the inner face (city side): joint under the lip, column, spout bracket
        px = ga + 1 if n < 7 else cx + 2
        s.set(px, Y_FLOOR, zb, PIPE_CUT)
        for y in range(Y_BODY0 + 1, Y_FLOOR):
            s.set(px, y, zb, PIPE)
        s.set(px, Y_COURSE, zb, PIPE_CUT)
        s.set(px, Y_BODY0, zb, st.stairs("oxidized_cut_copper", "south", "top"))
        # inner face: access panels + a purple wall banner
        vent(s, cx - 1, 8, zb, "south")
        vent(s, cx - 1, 7, zb, "south")
        s.set(cx + 1, 11, zb, st.wall_banner("purple", "south"))
    for x in xs:
        for z in (za, zb):
            lamp_post(s, x, Y_RAIL + 1, z)
            s.set(x, Y_COURSE, z, CHISEL)                                       # rib ornament on the course line
            s.set(x, Y_NEON, z, FROG)                                           # lamp under the overhang


def sculk_patch(s, cells, seed=0):
    """cells = list of (x, y, z): sculk blob with a catalyst, veins on top and a sensor on the first cell."""
    import random
    rng = random.Random(seed)
    for (x, y, z) in cells:
        s.set(x, y, z, "minecraft:sculk")
    x, y, z = cells[len(cells) // 2]
    s.set(x, y, z, "minecraft:sculk_catalyst")
    for (x, y, z) in cells:
        if s.is_air(x, y + 1, z) and rng.random() < 0.5:
            s.set(x, y + 1, z, "minecraft:sculk_vein[down=true]")
    x, y, z = cells[0]
    if s.is_air(x, y + 1, z) or "vein" in s.get(x, y + 1, z):
        s.set(x, y + 1, z, "minecraft:sculk_sensor")


def tower(s, x0, z0, sx, sz, top, ladder_xz, flat_faces=()):
    """Rectangular tower with 2x2 corner piers and recessed faces, 3 interior levels
    (ground y2..8, mid y10..13, top y15..roof-1), a ladder through every floor, parapet + crystal crown + searchlight.
    x0,z0 = min corner; top = y of the parapet (roof floor = top-1). flat_faces get no recess (use it for faces
    hidden behind an abutting wall or forming a flat flank)."""
    x1, z1 = x0 + sx - 1, z0 + sz - 1
    ix0, ix1, iz0, iz1 = x0 + 2, x1 - 2, z0 + 2, z1 - 2
    roof = top - 1
    sh.box(s, x0, 0, z0, x1, Y_PLINTH, z1, BASE)
    sh.box(s, x0, Y_PLINTH + 1, z0, x1, Y_PLINTH + 1, z1, TRIM)
    sh.box(s, x0, Y_BODY0, z0, x1, roof, z1, BODY)
    # interior levels (carved before the faces so the lanterns behind the neon lines survive as wall lights)
    sh.box(s, ix0, G + 1, iz0, ix1, roof - 1, iz1, "air")
    sh.box(s, ix0, G, iz0, ix1, G, iz1, BASE)
    sh.box(s, ix0, 9, iz0, ix1, 9, iz1, BASE)
    sh.box(s, ix0, Y_FLOOR, iz0, ix1, Y_FLOOR, iz1, BASE)
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for y in (9, Y_FLOOR):
        s.set(cx, y, cz, LANT)
    # recessed faces (1 deep) between the corner piers, bevels top and bottom, neon lines at y=5 and y=13
    for face in ("north", "south", "east", "west"):
        if face in flat_faces:
            continue
        stair = st.stairs(STAIR_T, _BEVEL_DOWN[face])
        stair_top = st.stairs(STAIR_T, _BEVEL_DOWN[face], "top")
        if face in ("north", "south"):
            zp = z0 if face == "north" else z1
            zw = zp + 1 if face == "north" else zp - 1
            zi = zw + 1 if face == "north" else zw - 1
            sh.box(s, x0 + 2, Y_BODY0, zp, x1 - 2, roof - 1, zp, "air")
            for x in range(x0 + 2, x1 - 1):
                s.set(x, Y_BODY0, zp, stair)
                s.set(x, roof, zp, stair_top)
                s.set(x, Y_NEON, zw, GLASS)
                s.set(x, Y_ACC, zw, GLASS2)
                s.set(x, Y_COURSE, zw, TRIM)
                if (x - x0) % 2 == 0:
                    s.set(x, Y_NEON, zi, LANT)
                    s.set(x, Y_ACC, zi, LANT)
        else:
            xp = x0 if face == "west" else x1
            xw = xp + 1 if face == "west" else xp - 1
            xi = xw + 1 if face == "west" else xw - 1
            sh.box(s, xp, Y_BODY0, z0 + 2, xp, roof - 1, z1 - 2, "air")
            for z in range(z0 + 2, z1 - 1):
                s.set(xp, Y_BODY0, z, stair)
                s.set(xp, roof, z, stair_top)
                s.set(xw, Y_NEON, z, GLASS)
                s.set(xw, Y_ACC, z, GLASS2)
                s.set(xw, Y_COURSE, z, TRIM)
                if (z - z0) % 2 == 0:
                    s.set(xi, Y_NEON, z, LANT)
                    s.set(xi, Y_ACC, z, LANT)
    # roof deck, parapet railing, corner piers with purpur caps and the crystal crown, searchlight
    sh.box(s, x0, roof, z0, x1, roof, z1, BASE)
    s.set(cx, roof, cz, LANT)
    for x in range(x0, x1 + 1):
        s.set(x, top, z0, RAIL)
        s.set(x, top, z1, RAIL)
    for z in range(z0, z1 + 1):
        s.set(x0, top, z, RAIL)
        s.set(x1, top, z, RAIL)
    for (px, pz, ox, oz) in ((x0, z0, 1, 1), (x1, z0, -1, 1), (x0, z1, 1, -1), (x1, z1, -1, -1)):
        sh.box(s, min(px, px + ox), roof, min(pz, pz + oz), max(px, px + ox), top - 1, max(pz, pz + oz), BODY)
        sh.box(s, min(px, px + ox), top, min(pz, pz + oz), max(px, px + ox), top, max(pz, pz + oz), PURPUR)
        crystal_spike(s, px, top + 1, pz, post=2)
        for (ax, az) in ((px + ox, pz), (px, pz + oz)):
            s.set(ax, top + 1, az, RAIL)
            s.set(ax, top + 2, az, st.lightning_rod("up"))
        lamp_post(s, px + ox, top + 1, pz + oz)
    s.set(cx, top, cz, TRIM)
    frame_light(s, cx, top + 1, cz)
    # ladder through every floor and the roof hatch
    lx, lz = ladder_xz
    lfacing = "east" if lx == ix0 else "west" if lx == ix1 else "south" if lz == iz0 else "north"
    for y in range(G + 1, roof + 1):
        s.set(lx, y, lz, st.facing_block(LADDER, lfacing))


def door(s, face, x0, z0, sx, sz, y0, y1, a0, a1):
    """Cut an opening through the 2-thick wall of a tower on `face`, add blast-door leaves + a froglight lintel."""
    x1, z1 = x0 + sx - 1, z0 + sz - 1
    if face in ("north", "south"):
        zz = (z0, z0 + 1) if face == "north" else (z1 - 1, z1)
        sh.box(s, a0, y0, zz[0], a1, y1, zz[1], "air")
        zl = zz[1] if face == "north" else zz[0]
        leaf(s, a0, y0 + 1, zl, "west")
        leaf(s, a1, y0 + 1, zl, "east")
        s.set((a0 + a1) // 2, y1 + 1, zl, FROG)
    else:
        xx = (x0, x0 + 1) if face == "west" else (x1 - 1, x1)
        sh.box(s, xx[0], y0, a0, xx[1], y1, a1, "air")
        xl = xx[1] if face == "west" else xx[0]
        leaf(s, xl, y0 + 1, a0, "north")
        leaf(s, xl, y0 + 1, a1, "south")
        s.set(xl, y1 + 1, (a0 + a1) // 2, FROG)


def face_details(s, face, x0, z0, sx, sz, lo=None, hi=None, banners=True, slit=True, window=True):
    """Vents, arrow slit, banners, window strip on one face of a tower (recessed or flat)."""
    x1, z1 = x0 + sx - 1, z0 + sz - 1
    if face in ("north", "south"):
        plane = z0 if face == "north" else z1
        wall = plane + 1 if face == "north" else plane - 1
        cells = lambda a, y: (a, y, plane)
        wcells = lambda a, y: (a, y, wall)
        lo = x0 + 2 if lo is None else lo
        hi = x1 - 2 if hi is None else hi
    else:
        plane = x0 if face == "west" else x1
        wall = plane + 1 if face == "west" else plane - 1
        cells = lambda a, y: (plane, y, a)
        wcells = lambda a, y: (wall, y, a)
        lo = z0 + 2 if lo is None else lo
        hi = z1 - 2 if hi is None else hi
    c = (lo + hi) // 2
    for a in (lo, hi):
        vent(s, *cells(a, 7), face)
        vent(s, *cells(a, 6), face)
    if slit:
        for y in (10, 11, 12):
            s.set(*wcells(c, y), GLASS)
    if window:
        for a in range(c - 1, c + 2):
            s.set(*wcells(a, 16), GLASS2)
            s.set(*wcells(a, 17), GLASS2)
        s.set(*cells(c - 1, 15), st.button("polished_blackstone", "wall", face))
        s.set(*cells(c + 1, 15), st.button("polished_blackstone", "wall", face))
    if banners:
        s.set(*cells(c - 1, 12), st.wall_banner("purple", face))
        s.set(*cells(c + 1, 12), st.wall_banner("purple", face))


# --------------------------------------------------------------------------------------- QA helpers
def _props(block):
    _, p = st.parse(block)
    return p


def check_support(s, name):
    """Every wall sign / wall banner / ladder / button / lever / open trapdoor must have a block to hang on;
    closed trapdoors and hanging lanterns need a neighbour too. Raises AssertionError with the offenders."""
    bad = []
    for bid, block in enumerate(s.blocks_by_id):
        if bid == 0:
            continue
        short = block.split("[")[0].replace("minecraft:", "")
        p = _props(block)
        need = None                      # direction of the supporting neighbour
        if short.endswith("wall_sign") or short.endswith("wall_banner") or short == "ladder" \
                or (short.endswith("_button") and p.get("face", "wall") == "wall") \
                or (short == "lever" and p.get("face", "wall") == "wall"):
            need = _OPP[p["facing"]]
        elif short.endswith("_button") or short == "lever":
            need = "down" if p.get("face") == "floor" else "up"
        elif short.endswith("_trapdoor"):
            if p.get("open") == "true":
                need = _OPP[p["facing"]]
            else:
                need = "any"
        elif short in ("lantern", "soul_lantern") and p.get("hanging") == "true":
            need = "up"
        elif short == "chain" and p.get("axis", "y") == "y":
            need = "any"
        if need is None:
            continue
        for (x, y, z) in zip(*np.nonzero(s.data == bid)):
            x, y, z = int(x), int(y), int(z)
            dirs = list(_DIR.values()) if need == "any" else [_DIR[need]]
            ok = False
            for (dx, dy, dz) in dirs:
                nx, ny, nz = x + dx, y + dy, z + dz
                if s.inside(nx, ny, nz) and not s.is_air(nx, ny, nz):
                    ok = True
                    break
            if not ok:
                bad.append((x, y, z, block))
    assert not bad, f"{name}: unsupported blocks: {bad[:8]}"


def accent_share(s):
    """Share of accent blocks (glass, lights, purpur, amethyst) among the visible surface blocks."""
    solid = s.data != 0
    surf = sh.surface_mask(s, solid)
    ids = [i for i, b in enumerate(s.blocks_by_id)
           if any(k in b for k in ("stained_glass", "froglight", "sea_lantern", "purpur", "amethyst", "end_rod",
                                    "magenta_concrete", "redstone_lamp"))]
    acc = np.isin(s.data, ids) & surf
    return float(acc.sum()) / max(1, int(surf.sum()))


def finish(s, seed, name):
    sh.texturize(s, BODY, MIX_BLACK, seed=seed)
    sh.snow_cover(s, y_min=Y_FLOOR, prob=0.09, seed=seed, layers=(1, 1),
                  skip=["glass", "froglight", "sea_lantern", "sculk", "ladder", "basalt", "copper", "bone", "purpur",
                        "amethyst", "chiseled"])
    check_support(s, name)
    print(f"    [{name}] accent share of surface blocks: {accent_share(s):.1%}")
    return s


# --------------------------------------------------------------------------------------- 1. segment
def build_segment():
    s = Schematic(16, 18, 5, ground=G)
    wall_run(s, 0, 15, 0, piers={0, 7, 8, 15})
    # sculk infestation creeping up the plinth at the base of the outer face
    sculk_patch(s, [(9, 2, 0), (10, 2, 0), (11, 2, 0), (12, 2, 0), (10, 3, 0), (11, 3, 0), (13, 2, 0)], seed=1)
    # inner-face signage (city side)
    s.add_sign(5, 6, 4, SIGN + "[facing=south]", ["SECTEUR 7", "MUR NORD", "PATROUILLE", "TOUTES LES 2H"])
    s.add_sign(12, 6, 4, SIGN + "[facing=south]", ["DANGER", "HAUTE", "TENSION", ""])
    # a supply barrel on the walkway against the middle buttress post
    s.add_chest(9, Y_RAIL, 3, "north", "minecraft:chests/pillager_outpost", kind="barrel")
    return finish(s, 11, "city_wall_segment")


# --------------------------------------------------------------------------------------- 2. corner
def build_corner():
    s = Schematic(16, 23, 16, ground=G)
    T, TOP = 9, 19                          # 9x9 tower at x,z=0..8; parapet y=19 (18 above ground)
    # east arm (along x) z=2..6, piers at 8 (against the tower) and 15 (seam)
    wall_run(s, 8, 15, 2, piers={8, 15})
    # south arm: built along x then rotated 90 degrees counter-clockwise so its outer face looks west
    arm = Schematic(8, 18, 5, ground=G)
    wall_run(arm, 0, 7, 0, piers={0, 7})
    s.paste(arm.rotated(3), 2, 0, 8)
    # the tower's east and south faces are hidden behind the arms -> flat (no recess carving into the arm piers)
    tower(s, 0, 0, T, T, TOP, ladder_xz=(2, 4), flat_faces=("east", "south"))
    face_details(s, "north", 0, 0, T, T)
    face_details(s, "west", 0, 0, T, T)
    # walkway doors (2 high) from both arms into the top room; lintel lights + side lights above
    door(s, "east", 0, 0, T, T, Y_RAIL, Y_RAIL + 1, 3, 5)
    door(s, "south", 0, 0, T, T, Y_RAIL, Y_RAIL + 1, 3, 5)
    for a in (3, 5):
        s.set(7, 17, a, GLASS2)
        s.set(a, 17, 7, GLASS2)
    # interiors -------------------------------------------------------------------------------
    # ground room (y2..8): generator, tank, reactor cell, loot
    s.set(5, 2, 2, st.facing_block("minecraft:blast_furnace", "south"))
    s.set(6, 2, 2, "minecraft:cauldron")
    s.set(6, 3, 2, st.chain("y"))
    s.set(6, 4, 2, st.chain("y"))
    s.set(5, 3, 2, st.log("minecraft:polished_basalt", "x"))
    s.add_chest(6, 2, 6, "west", "minecraft:chests/bastion_other")
    s.set(5, 2, 6, "minecraft:barrel[facing=up]")
    s.set(3, 2, 6, "minecraft:crying_obsidian")
    s.set(3, 3, 6, TINT)
    s.add_sign(4, 4, 6, SIGN + "[facing=north]", ["RESERVE", "TOUR NORD-OUEST", "NE PAS", "TOUCHER"])
    s.set(4, 8, 4, LANT)
    # mid room (y10..13): control consoles, log
    for x in (3, 4, 5):
        s.set(x, 10, 2, st.facing_block("minecraft:observer", "north"))
        s.set(x, 11, 2, "minecraft:daylight_detector")
    s.set(6, 10, 3, st.redstone_lamp(True))
    s.set(6, 10, 5, st.redstone_lamp(True))
    s.set(3, 10, 6, st.facing_block("minecraft:lectern", "north"))
    s.add_sign(6, 11, 4, SIGN + "[facing=west]", ["JOURNAL 12", "cible detectee", "secteur nord", "RAS"])
    # top room (walkway level y15..17): bench, barrel, light
    s.set(2, Y_RAIL, 6, "minecraft:barrel[facing=up]")
    s.set(3, Y_RAIL, 2, st.stairs("polished_deepslate", "south"))
    s.set(4, Y_RAIL, 2, st.stairs("polished_deepslate", "south"))
    s.set(4, 17, 4, FROG)
    # sculk on the outer plinth corner, outer signage
    sculk_patch(s, [(0, 2, 3), (0, 2, 4), (0, 2, 5), (0, 3, 4), (1, 2, 0), (2, 2, 0), (3, 2, 0), (2, 3, 0)], seed=2)
    s.add_sign(4, 8, 0, SIGN + "[facing=north]", ["TOUR", "NORD-OUEST", "ZONE", "INTERDITE"])
    # walkway continuity: the arm piers must survive under both blast doors (no pit at the junctions)
    for a in (3, 4, 5):
        assert not s.is_air(8, Y_FLOOR, a) and not s.is_air(7, Y_FLOOR, a), f"corner: east walkway pit at z={a}"
        assert not s.is_air(a, Y_FLOOR, 8) and not s.is_air(a, Y_FLOOR, 7), f"corner: south walkway pit at x={a}"
    return finish(s, 12, "city_wall_corner")


# --------------------------------------------------------------------------------------- 3. gate
# 8 wide x 7 high, rows y17..y11, x=8..15. '#' bone, 'E' eye socket (tinted glass, froglight behind),
# 'b' dark tooth gap (blackstone, proud), '.' open (recessed wall shows through)
SKULL = [
    "..####..",
    ".######.",
    "########",
    "#EE##EE#",
    "#EE##EE#",
    ".##..##.",
    ".#b##b#.",
]


def build_gate():
    s = Schematic(24, 24, 12, ground=G)
    SX, SZ, TOP = 9, 12, 20                  # twin towers 9 x 12, parapet y=20; arch x=9..14
    # outer flanks (x=0 / x=23) are flat 2-thick faces so the abutting wall segment butts on a clean plane
    tower(s, 0, 0, SX, SZ, TOP, ladder_xz=(2, 9), flat_faces=("east", "west"))
    tower(s, 15, 0, SX, SZ, TOP, ladder_xz=(17, 9), flat_faces=("west", "east"))
    # --- archway x=9..14, y=2..8, full depth; road with a magenta centre band
    sh.box(s, 9, 0, 0, 14, 0, 11, BASE)
    sh.box(s, 9, 1, 0, 14, 1, 11, TRIM)
    sh.box(s, 11, 1, 0, 12, 1, 11, VILLAIN["road_line"])
    sh.box(s, 9, 2, 0, 14, 8, 11, "air")
    # --- gatehouse over the arch: x=9..14, y=9..18, z=0..11 (north/south walls 2 thick: z=0..1 and z=10..11)
    sh.box(s, 9, 9, 0, 14, 18, 11, BODY)
    sh.box(s, 9, 9, 0, 14, 9, 11, BASE)                                   # arch ceiling
    for z in range(0, 12):
        s.set(9, 8, z, st.stairs(STAIR_B, "west", "top"))                # arch shoulders
        s.set(14, 8, z, st.stairs(STAIR_B, "east", "top"))
    for z in (2, 5, 8):
        for x in (10, 13):
            s.set(x, 9, z, LANT)
    # interior: winch room y10..13 (z=2..9), floor y14, walkway hall y15..17, roof y18, railing y19
    sh.box(s, 9, 10, 2, 14, 13, 9, "air")
    sh.box(s, 9, 14, 2, 14, 14, 9, BASE)
    sh.box(s, 9, 15, 2, 14, 17, 9, "air")
    sh.box(s, 9, 18, 0, 14, 18, 11, BASE)
    for x in range(9, 15):
        s.set(x, 19, 0, RAIL)
        s.set(x, 19, 11, RAIL)
        s.set(x, 14, 4, GLASS)                                           # lit strip through the hall
        s.set(x, 13, 4, LANT)
    s.set(9, 19, 0, BODY); s.set(14, 19, 0, BODY); s.set(9, 19, 11, BODY); s.set(14, 19, 11, BODY)
    for x in (9, 14):
        s.set(x, 20, 0, st.lightning_rod("up"))
        s.set(x, 20, 11, st.lightning_rod("up"))
    # portcullis: iron bars, half lowered, spiked lower edge; winch beam + chains in the room above
    sh.box(s, 9, 6, 5, 14, 8, 5, BARS)
    for x in range(9, 15):
        s.set(x, 5, 5, st.pointed_dripstone("down", "tip"))
    sh.box(s, 9, 12, 5, 14, 12, 5, st.log("minecraft:polished_basalt", "x"))
    for x in (10, 13):
        s.set(x, 11, 5, st.chain("y"))
        s.set(x, 10, 5, st.chain("y"))
    s.set(11, 10, 2, "minecraft:cauldron")
    s.set(12, 10, 2, st.facing_block("minecraft:blast_furnace", "south"))
    s.set(10, 10, 2, st.facing_block("minecraft:observer", "south"))
    s.set(10, 11, 2, st.redstone_lamp(True))
    s.set(13, 11, 2, "minecraft:lever[face=wall,facing=south,powered=false]")
    s.add_chest(13, 10, 9, "north", "minecraft:chests/bastion_other")
    s.add_sign(12, 11, 9, SIGN + "[facing=north]", ["TREUIL HERSE", "ne pas lever", "sans ordre", "du commandant"])
    s.set(11, 13, 8, LANT)
    s.set(11, 17, 5, FROG)
    s.set(12, 17, 8, FROG)
    # --- skull over the arch (north face): recess the face 1 block (x=8..15, y=11..17), chiseled frame,
    #     neon underline at y=10, bone skull standing proud at z=0 with dark hollow eyes glowing from behind
    sh.box(s, 8, 11, 0, 15, 17, 0, "air")
    for y in range(10, 19):
        s.set(7, y, 0, CHISEL)
        s.set(16, y, 0, CHISEL)
    for x in range(8, 16):
        s.set(x, 18, 0, CHISEL)
        s.set(x, 10, 0, GLASS)
        s.set(x, 10, 1, LANT)
    for r, row in enumerate(SKULL):
        y = 17 - r
        for i, ch in enumerate(row):
            x = 8 + i
            if ch == "#":
                s.set(x, y, 0, BONE)
            elif ch == "E":
                s.set(x, y, 0, TINT)
                s.set(x, y, 1, FROG)
            elif ch == "b":
                s.set(x, y, 0, BODY_SMOOTH)
    # south face of the gatehouse: neon lines + window strip
    for x in range(9, 15):
        s.set(x, Y_NEON, 11, GLASS)
        s.set(x, 10, 11, GLASS2)
        if x % 2 == 0:
            s.set(x, Y_NEON, 10, LANT)
            s.set(x, 10, 10, LANT)
    for x in (10, 11, 12, 13):
        s.set(x, 16, 11, GLASS2)
    # --- tower faces: details, banners, signs; magenta band on the flat flanks beside the seam
    face_details(s, "north", 0, 0, SX, SZ)
    face_details(s, "north", 15, 0, SX, SZ)
    face_details(s, "south", 0, 0, SX, SZ)
    face_details(s, "south", 15, 0, SX, SZ)
    face_details(s, "west", 0, 0, SX, SZ, lo=8, hi=9, slit=False, window=False, banners=False)
    face_details(s, "east", 15, 0, SX, SZ, lo=8, hi=9, slit=False, window=False, banners=False)
    for z in range(7, 11):
        s.set(0, Y_ACC, z, GLASS2); s.set(1, Y_ACC, z, LANT)
        s.set(23, Y_ACC, z, GLASS2); s.set(22, Y_ACC, z, LANT)
        s.set(0, Y_COURSE, z, TRIM); s.set(23, Y_COURSE, z, TRIM)
    s.set(0, 12, 8, st.wall_banner("purple", "west"))
    s.set(23, 12, 8, st.wall_banner("purple", "east"))
    s.add_sign(9, 4, 2, SIGN + "[facing=east]", ["ZONE", "INTERDITE", "CONTROLE", "OBLIGATOIRE"])
    s.add_sign(14, 4, 9, SIGN + "[facing=west]", ["PORTE NORD", "SECTEUR 7", "ACCES", "REFUSE"])
    s.add_sign(3, 8, 0, SIGN + "[facing=north]", ["ZONE", "INTERDITE", "TIR A VUE", ""])
    s.add_sign(20, 8, 0, SIGN + "[facing=north]", ["ZONE", "INTERDITE", "DEMI-TOUR", ""])
    sculk_patch(s, [(2, 2, 0), (3, 2, 0), (4, 2, 0), (3, 3, 0), (5, 2, 0)], seed=4)
    sculk_patch(s, [(17, 2, 0), (18, 2, 0), (19, 2, 0), (18, 3, 0)], seed=5)
    # --- doors (cut last so nothing fills them back): wall -> tower, tower <-> gatehouse, passage -> tower
    door(s, "west", 0, 0, SX, SZ, Y_RAIL, Y_RAIL + 1, 3, 5)
    door(s, "east", 15, 0, SX, SZ, Y_RAIL, Y_RAIL + 1, 3, 5)
    for (xa, xb) in ((7, 8), (15, 16)):
        sh.box(s, xa, 15, 3, xb, 16, 5, "air")
        sh.box(s, xa, 10, 3, xb, 12, 5, "air")
    for (xa, xb, hug) in ((7, 8, "west"), (15, 16, "east")):
        sh.box(s, xa, 2, 7, xb, 4, 8, "air")
        xl = xb if hug == "west" else xa
        leaf(s, xl, 3, 7, "north")
        leaf(s, xl, 3, 8, "south")
        s.set(xl, 5, 7, LANT)
        s.set(xl, 5, 8, LANT)
    # interiors of the towers -----------------------------------------------------------------
    for tx in (0, 15):
        s.set(tx + 3, 2, 2, st.facing_block("minecraft:blast_furnace", "south"))
        s.set(tx + 4, 2, 2, "minecraft:cauldron")
        s.set(tx + 5, 2, 2, "minecraft:barrel[facing=up]")
        s.set(tx + 6, 2, 2, "minecraft:barrel[facing=up]")
        s.set(tx + 6, 3, 2, "minecraft:barrel[facing=up]")
        s.add_chest(tx + 6, 2, 9, "west", "minecraft:chests/pillager_outpost")
        s.set(tx + 3, 2, 9, st.stairs("polished_deepslate", "north"))
        s.set(tx + 4, 2, 9, st.stairs("polished_deepslate", "north"))
        s.set(tx + 4, 8, 5, LANT)
        s.add_sign(tx + 3, 4, 2, SIGN + "[facing=south]", ["POSTE DE", "GARDE", "OUEST" if tx == 0 else "EST", ""])
        for z in (7, 8, 9):
            s.set(tx + 6, 10, z, BARS)
            s.set(tx + 6, 11, z, BARS)
        s.set(tx + 3, 10, 2, st.facing_block("minecraft:observer", "north"))
        s.set(tx + 4, 10, 2, st.facing_block("minecraft:observer", "north"))
        s.set(tx + 3, 11, 2, "minecraft:daylight_detector")
        s.set(tx + 4, 11, 2, "minecraft:daylight_detector")
        s.set(tx + 5, 10, 2, st.redstone_lamp(True))
        s.set(tx + 4, 13, 5, LANT)
        s.set(tx + 5, 15, 9, st.stairs("polished_deepslate", "north"))
        s.set(tx + 4, 15, 9, st.stairs("polished_deepslate", "north"))
        s.set(tx + 4, 18, 5, FROG)
        s.set(tx + 3, 15, 2, "minecraft:barrel[facing=up]")
    return finish(s, 13, "city_gate")


# --------------------------------------------------------------------------------------- 4. watchtower
def build_watchtower():
    s = Schematic(10, 29, 10, ground=G)
    # base: buried foundation (y0..1), four 3x3 leg pads and the core pad standing in the snow (y2..3)
    sh.box(s, 0, 0, 0, 9, 1, 9, BASE)
    for (a0, a1, b0, b1) in ((3, 6, 0, 1), (3, 6, 8, 9), (0, 1, 3, 6), (8, 9, 3, 6)):   # surface stays snow between the pads
        sh.box(s, a0, 1, b0, a1, 1, b1, "minecraft:snow_block")
    for (px, pz) in ((0, 0), (7, 0), (0, 7), (7, 7)):
        sh.box(s, px, 2, pz, px + 2, 2, pz + 2, BASE)
        s.set(px + 1, 3, pz + 1, TRIM)                                     # steel foot under the leg
        for (ax, az) in ((px, pz + 1), (px + 2, pz + 1), (px + 1, pz), (px + 1, pz + 2),
                         (px, pz), (px + 2, pz), (px, pz + 2), (px + 2, pz + 2)):
            fx = "east" if ax < px + 1 else "west" if ax > px + 1 else None
            fz = "south" if az < pz + 1 else "north" if az > pz + 1 else None
            s.set(ax, 3, az, st.stairs("polished_deepslate", fx or fz))    # bevelled pad top (corners auto-shaped)
    sh.box(s, 3, 2, 3, 6, 2, 6, BASE)
    sh.box(s, 3, 3, 3, 6, 3, 6, TRIM)                                      # core plinth band
    for (x, z) in ((3, 0), (5, 1), (6, 0), (0, 4), (1, 6), (9, 3), (8, 5), (4, 9), (6, 8)):   # snow drifting between the pads
        s.set(x, 2, z, st.snow_layer(2 if (x + z) % 2 else 3))
    sculk_patch(s, [(3, 1, 8), (4, 1, 8), (3, 1, 9), (4, 1, 9), (5, 1, 9)], seed=6)
    # legs: 4 corner columns y4..15 with iron joints and real struts leg -> core at y=6 and y=12
    for (x, z) in ((1, 1), (8, 1), (1, 8), (8, 8)):
        sh.box(s, x, 4, z, x, 15, z, BODY_SMOOTH)
        for y in (7, 11):
            s.set(x, y, z, IRON)
        dx = 1 if x == 1 else -1
        dz = 1 if z == 1 else -1
        for y in (6, 12):
            s.set(x + dx, y, z, RAIL)
            s.set(x + dx, y, z + dz, RAIL)
            s.set(x + 2 * dx, y, z + dz, RAIL)                             # touches the core face
    for a in range(2, 8):                                                  # chain ties between the legs
        s.set(a, 9, 1, st.chain("x"))
        s.set(a, 9, 8, st.chain("x"))
        s.set(1, 9, a, st.chain("z"))
        s.set(8, 9, a, st.chain("z"))
    # core column 4x4 (x,z=3..6), hollow 2x2 shaft, ladder on the west wall, blast door on the south face
    sh.box(s, 3, 4, 3, 6, 15, 6, BODY)
    sh.box(s, 4, 4, 4, 5, 16, 5, "air")
    for a in (3, 4, 5, 6):                                                 # magenta band + purple neon ring
        s.set(a, Y_ACC, 3, GLASS2); s.set(a, Y_ACC, 6, GLASS2)
        s.set(3, Y_ACC, a, GLASS2); s.set(6, Y_ACC, a, GLASS2)
        s.set(a, Y_NEON, 3, GLASS); s.set(a, Y_NEON, 6, GLASS)
        s.set(3, Y_NEON, a, GLASS); s.set(6, Y_NEON, a, GLASS)
    for a in (3, 6):                                                       # string course ring
        for b in range(3, 7):
            s.set(a, Y_COURSE, b, TRIM); s.set(b, Y_COURSE, a, TRIM)
    sh.box(s, 4, 4, 6, 5, 6, 6, "air")
    leaf(s, 4, 5, 6, "west")
    leaf(s, 5, 5, 6, "east")
    for y in (5, 7, 13):
        s.set(5, y, 5, LANT)
    vent(s, 4, 10, 2, "north"); vent(s, 5, 10, 2, "north")
    vent(s, 4, 10, 7, "south"); vent(s, 5, 10, 7, "south")
    vent(s, 2, 10, 4, "west"); vent(s, 2, 10, 5, "west")
    vent(s, 7, 10, 4, "east"); vent(s, 7, 10, 5, "east")
    s.add_sign(4, 8, 7, SIGN + "[facing=south]", ["VIGIE 3", "ZONE", "INTERDITE", ""])
    # cabin: floor y16 (x,z=1..8) with bevelled underside, glass walls y17..19, roof y20
    sh.box(s, 1, 16, 1, 8, 16, 8, BASE)
    for a in range(2, 8):
        s.set(a, 16, 1, st.stairs(STAIR_T, "south", "top"))
        s.set(a, 16, 8, st.stairs(STAIR_T, "north", "top"))
        s.set(1, 16, a, st.stairs(STAIR_T, "east", "top"))
        s.set(8, 16, a, st.stairs(STAIR_T, "west", "top"))
    for (x, z) in ((2, 2), (7, 2), (2, 7), (7, 7)):
        s.set(x, 16, z, FROG)
    sh.box(s, 1, 17, 1, 8, 19, 8, GLASS)
    sh.box(s, 2, 17, 2, 7, 19, 7, "air")
    sh.box(s, 1, 17, 1, 8, 17, 8, BODY)                                    # knee wall
    sh.box(s, 2, 17, 2, 7, 17, 7, "air")
    for (x, z) in ((1, 1), (8, 1), (1, 8), (8, 8)):
        sh.box(s, x, 17, z, x, 19, z, BODY)
        s.set(x, 20, z, PURPUR)
    for y in range(4, 17):                                                 # ladder up to the floor hatch (y16)
        s.set(4, y, 4, st.facing_block(LADDER, "east"))
    # roof y20 with bevelled rim, light mast with end rods (rotating beacon look), antenna, dish
    sh.box(s, 2, 20, 1, 7, 20, 8, BASE)
    sh.box(s, 1, 20, 2, 8, 20, 7, BASE)
    for a in range(2, 8):
        s.set(a, 20, 1, st.stairs(STAIR_B, "south"))
        s.set(a, 20, 8, st.stairs(STAIR_B, "north"))
        s.set(1, 20, a, st.stairs(STAIR_B, "east"))
        s.set(8, 20, a, st.stairs(STAIR_B, "west"))
    s.set(4, 20, 4, LANT)
    s.set(5, 20, 5, LANT)
    sh.box(s, 4, 21, 4, 5, 22, 5, BODY)
    sh.box(s, 4, 23, 4, 5, 23, 5, LANT)
    s.set(3, 23, 4, st.end_rod("west"))
    s.set(6, 23, 5, st.end_rod("east"))
    s.set(4, 23, 3, st.end_rod("north"))
    s.set(5, 23, 6, st.end_rod("south"))
    sh.box(s, 4, 24, 4, 5, 24, 5, GLASS2)
    s.set(4, 25, 4, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(5, 25, 5, st.trapdoor("iron", "north", "bottom", open=False))
    s.set(5, 25, 4, st.lightning_rod("up"))
    s.set(5, 26, 4, st.lightning_rod("up"))
    s.set(5, 27, 4, st.end_rod("up"))
    s.set(4, 25, 5, st.lightning_rod("up"))
    s.set(7, 21, 2, IRON)
    s.set(7, 22, 2, st.lightning_rod("up"))
    leaf(s, 6, 22, 2, "east"); leaf(s, 8, 22, 2, "west")
    leaf(s, 7, 22, 1, "south"); leaf(s, 7, 22, 3, "north")
    for (x, z) in ((3, 1), (6, 8), (1, 6), (8, 3), (5, 1), (8, 6)):       # icicles under the overhang
        s.set(x, 15, z, st.pointed_dripstone("down", "tip"))
    # cabin interior: console, log, chest, candle
    s.set(6, 17, 2, st.facing_block("minecraft:observer", "north"))
    s.set(6, 18, 2, "minecraft:daylight_detector")
    s.set(7, 17, 2, st.redstone_lamp(True))
    s.set(2, 17, 6, st.facing_block("minecraft:lectern", "east"))
    s.add_chest(7, 17, 7, "west", "minecraft:chests/pillager_outpost")
    s.set(2, 17, 2, st.stairs("polished_deepslate", "south"))
    s.set(6, 17, 6, st.candle("purple", 2))
    s.add_sign(7, 18, 6, SIGN + "[facing=west]", ["JOURNAL 12", "rien a l'ouest", "sauf la neige", "et les spores"])
    return finish(s, 14, "city_watchtower")


def build():
    return {
        "city_wall_segment": build_segment(),
        "city_wall_corner": build_corner(),
        "city_gate": build_gate(),
        "city_watchtower": build_watchtower(),
    }
