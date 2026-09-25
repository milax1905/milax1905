"""Villain city command spire: tapered octagonal blackstone tower on a sculk plaza, 2 wide cantilevered ring decks
with corner turrets, a 4-arm cross landing runway on struts, glass command deck and a crown of 4 thin sloped fins
around a tall obsidian needle antenna.
Full interior (lobby/throne, prison, servers, armoury, quarters, hangar, reactor, command deck) linked by an
open lift shaft with a ladder."""
from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import VILLAIN as V
import numpy as np

W, H, L, G = 34, 97, 34, 2
C = 16.5                      # centre between x=16 and x=17 (symmetric even footprint)
CHAMFER = 1.5                 # octagon: dx + dz <= hw * CHAMFER (wide flat faces for the neon strips)

PBB = V["wall"]               # polished blackstone bricks
DT = V["wall_alt"]            # deepslate tiles
PD = V["wall_smooth"]         # polished deepslate
OBS = V["core"]
CRY = V["core_glow"]
LANT = V["floor_light"]       # sea lantern
GLASS = V["glass"]            # purple stained glass
NEON = V["neon"]              # magenta stained glass
AME = V["light_purple"]
IRON = V["metal_light"]
BASALT = V["metal"]
WALL = V["railing"]           # polished blackstone brick wall
SIGN = "minecraft:warped_wall_sign"
MIX_BODY = [(PBB, 7), (PD, 2), ("minecraft:deepslate_bricks", 1)]     # visible close-shade gradient
BARS = V["bars"]

# ---- vertical programme (floor y of every level) --------------------------------------------------------------
FLOORS = [5, 13, 20, 27, 35, 41, 47, 53, 61]
DECKS = {27: 5, 41: 6, 53: 4}          # deck floor y -> cantilever width (41 = cross runway)
SETBACKS = (13, 20, 35, 47)            # floors where the body steps in by one block
PAD = 41
CMD = 61                               # command deck floor
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
DIRS = {"east": (1, 0), "west": (-1, 0), "south": (0, 1), "north": (0, -1)}


def hw_at(y):
    """Half-width of the octagonal body at height y (values end in .5 so faces are even-sized)."""
    if y < 13:
        return 9.5
    if y < 20:
        return 8.5
    if y < 35:
        return 7.5
    if y < 47:
        return 6.5
    if y < 61:
        return 5.5
    return 8.5  # command deck


# ---- 2D octagon masks -------------------------------------------------------------------------------------------
_xs = np.arange(W)[:, None].astype(float)
_zs = np.arange(L)[None, :].astype(float)
DX = np.abs(_xs - C)
DZ = np.abs(_zs - C)


def octa(hw, chamfer=CHAMFER):
    return (DX <= hw) & (DZ <= hw) & (DX + DZ <= hw * chamfer)


def ring(a, b, chamfer=CHAMFER):
    """Octagonal ring between half-widths a (inner, excluded) and b (outer, included)."""
    return octa(b, chamfer) & ~octa(a, chamfer)


def inner(hw):
    """Interior (air) mask of a body section of half-width hw: 2-thick walls."""
    return octa(hw - 2)


def cross(a, b, half=3.5):
    """4-arm cross between half-widths a and b (arms 2*half wide)."""
    return ring(a, b) & ((DX <= half) | (DZ <= half))


def fill2d(s, mask, y, block):
    for x, z in zip(*np.nonzero(mask)):
        s.set(int(x), y, int(z), block)


def toward_centre(x, z):
    """Facing of a stair whose raised half points at the tower axis."""
    dx, dz = x - C, z - C
    if abs(dx) > abs(dz):
        return "west" if dx > 0 else "east"
    return "north" if dz > 0 else "south"


def outward(x, z):
    return OPP[toward_centre(x, z)]


def stair_ring(s, mask, y, material, half="bottom"):
    for x, z in zip(*np.nonzero(mask)):
        s.set(int(x), y, int(z), st.stairs(material, toward_centre(x, z), half))


def edge_cells(mask, support=None):
    """Cells of `mask` with at least one 4-neighbour outside mask|support -> list of (x, z, [outside dirs])."""
    full = mask if support is None else (mask | support)
    out = []
    for x, z in zip(*np.nonzero(mask)):
        x, z = int(x), int(z)
        dirs = [d for d, (dx, dz) in DIRS.items()
                if not (0 <= x + dx < W and 0 <= z + dz < L and full[x + dx, z + dz])]
        if dirs:
            out.append((x, z, dirs))
    return out


def bevel(s, mask, y, material, half, support=None, fill=None):
    """Fill `mask` at y with `fill` then bevel its free edges with stairs (raised half toward the inside)."""
    if fill:
        fill2d(s, mask, y, fill)
    for x, z, dirs in edge_cells(mask, support):
        facing = OPP[dirs[0]] if len(dirs) == 1 else toward_centre(x, z)
        s.set(x, y, z, st.stairs(material, facing, half))


def arm_xz(arm, u, v):
    """Arm coordinates -> world: u across the arm (+-), v along the arm (outward from the axis)."""
    if arm == "south":
        return int(C + u), int(C + v)
    if arm == "north":
        return int(C + u), int(C - v)
    if arm == "east":
        return int(C + v), int(C + u)
    return int(C - v), int(C + u)


# =================================================================================================================
def build():
    s = Schematic(W, H, L, ground=G)

    # ---------------------------------------------------------------- plaza (flush with the snow at y = G)
    plaza = (DX <= 14.5) & (DZ <= 14.5)
    fill2d(s, plaza, G - 1, DT)                                 # buried foundation row (sits IN the snow)
    fill2d(s, plaza, G, PD)
    fill2d(s, plaza & ~octa(13.5), G, DT)                       # border strip + corner triangles
    # sculk gardens in the four corner triangles, with 1-2 blocks of relief
    garden = plaza & ~octa(13.5) & (DX + DZ > 20.5)
    rng = np.random.default_rng(7)
    for x, z in zip(*np.nonzero(garden)):
        x, z = int(x), int(z)
        s.set(x, G, z, V["sculk_glow"] if rng.random() < 0.10 else V["sculk"])
        r = rng.random()
        if r < 0.22:                                            # raised sculk mound with something on top
            s.set(x, G + 1, z, V["sculk"])
            r2 = rng.random()
            if r2 < 0.30:
                s.set(x, G + 2, z, V["sculk_sensor"])
            elif r2 < 0.45:
                s.set(x, G + 2, z, V["sculk_glow"])
            elif r2 < 0.60:
                s.set(x, G + 2, z, st.facing_block("minecraft:medium_amethyst_bud", "up"))
        elif r < 0.32:                                          # crystal: budding amethyst + cluster
            s.set(x, G + 1, z, "minecraft:budding_amethyst")
            s.set(x, G + 2, z, st.facing_block("minecraft:amethyst_cluster", "up"))
        elif r < 0.42:                                          # polished deepslate slab step
            s.set(x, G + 1, z, st.slab(V["wall_slab"]))
        elif r < 0.56:
            s.set(x, G + 1, z, V["sculk_sensor"])
        elif r < 0.64:
            s.set(x, G + 1, z, st.facing_block("minecraft:amethyst_cluster", "up"))
        elif r < 0.70:
            s.set(x, G + 1, z, st.facing_block("minecraft:large_amethyst_bud", "up"))
    for (x, z) in ((4, 8), (8, 4), (6, 6), (29, 8), (25, 4), (27, 6), (4, 25), (8, 29), (6, 27),
                   (29, 25), (25, 29), (27, 27)):
        s.set(x, G, z, V["sculk_glow"])
        s.set(x, G + 1, z, "minecraft:sculk_shrieker")
    # light strip: sea lanterns sunk under purple glass in the outermost plaza ring every 3 blocks (no bare cyan)
    for x in range(2, 32):
        for z in (2, 31):
            if (x - 2) % 3 == 0:
                s.set(x, G - 1, z, LANT)
                s.set(x, G, z, GLASS)
    for z in range(2, 32):
        for x in (2, 31):
            if (z - 2) % 3 == 0:
                s.set(x, G - 1, z, LANT)
                s.set(x, G, z, GLASS)
    # kerb bevel around the plaza (y = G+1, outside the plaza)
    for x in range(1, 33):
        s.set(x, G + 1, 1, st.stairs(V["wall_stairs_alt"], "south"))
        s.set(x, G + 1, 32, st.stairs(V["wall_stairs_alt"], "north"))
    for z in range(1, 33):
        s.set(1, G + 1, z, st.stairs(V["wall_stairs_alt"], "east"))
        s.set(32, G + 1, z, st.stairs(V["wall_stairs_alt"], "west"))
    for (x, z) in ((1, 1), (32, 1), (1, 32), (32, 32)):
        s.set(x, G + 1, z, DT)
    # corner pylons: 3x3 obsidian towers, crying-obsidian band, recessed soul campfire inside a wall crown
    for (x0, z0) in ((2, 2), (29, 2), (2, 29), (29, 29)):
        x1, z1 = x0 + 2, z0 + 2
        sh.box(s, x0, G, z0, x1, G + 1, z1, PBB)
        sh.box(s, x0, G + 2, z0, x1, G + 5, z1, OBS)
        sh.box(s, x0, G + 4, z0, x1, G + 4, z1, CRY)
        for x in range(x0, x1 + 1):
            for z in range(z0, z1 + 1):
                if x in (x0, x1) or z in (z0, z1):
                    s.set(x, G + 6, z, WALL)
        s.set(x0 + 1, G + 6, z0 + 1, st.campfire(soul=True))
        for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
            s.set(x, G + 7, z, WALL)
            s.set(x, G + 8, z, st.lightning_rod("up"))
        # small stair skirt on the plaza side of the pylon
        for x in range(x0, x1 + 1):
            for z in (z0 - 1, z1 + 1):
                if 2 <= z <= 31:
                    s.set(x, G + 1, z, st.stairs(V["wall_stairs"], "south" if z < z0 else "north"))
        for z in range(z0, z1 + 1):
            for x in (x0 - 1, x1 + 1):
                if 2 <= x <= 31:
                    s.set(x, G + 1, z, st.stairs(V["wall_stairs"], "east" if x < x0 else "west"))
    # approach paths (purple concrete lines) on S, E, W with lit end markers
    for z in range(29, 32):
        for x in (16, 17):
            s.set(x, G, z, V["accent"])
    for x in list(range(2, 5)) + list(range(29, 32)):
        for z in (16, 17):
            s.set(x, G, z, V["accent"])
    for (x, z) in ((16, 31), (17, 31), (2, 16), (2, 17), (31, 16), (31, 17)):
        s.set(x, G - 1, z, LANT)
        s.set(x, G, z, NEON)

    # ---------------------------------------------------------------- pedestal: two stepped octagons (2 high, 27 wide)
    # step 1 (G+1): blackstone plinth with a deepslate-tile trim row and a stair run all round
    fill2d(s, octa(11.5), G + 1, PBB)
    fill2d(s, ring(11.5, 12.5), G + 1, DT)
    stair_ring(s, ring(12.5, 13.5), G + 1, V["wall_stairs"])
    # step 2 (G+2): polished deepslate terrace, second stair run -> continuous 2-run ramp on every face
    fill2d(s, octa(10.5), G + 2, PD)
    fill2d(s, ring(10.5, 11.5), G + 2, DT)
    stair_ring(s, ring(11.5, 12.5), G + 2, V["wall_stairs"])
    # glowing ring at the foot of the tower: sea lantern sunk in the plinth under flush purple glass
    fill2d(s, ring(9.5, 10.5), G + 1, LANT)
    fill2d(s, ring(9.5, 10.5), G + 2, GLASS)
    # amethyst accents framed in the trim row on the diagonal faces of the lower step
    fill2d(s, ring(11.5, 12.5) & (np.abs(DX - DZ) <= 1.0), G + 1, AME)
    # ramp landings: a 2-wide deepslate-tile runner on the 4 faces (aligned with the approach paths)
    for y, hw_ in ((G + 1, 13.5), (G + 2, 12.5)):
        stair_ring(s, ring(hw_ - 1, hw_) & ((DX <= 1.5) | (DZ <= 1.5)), y, V["wall_stairs_alt"])

    # ---------------------------------------------------------------- body shell y=5..60
    for y in range(5, CMD):
        hw = hw_at(y)
        fill2d(s, octa(hw), y, PBB)
        fill2d(s, inner(hw), y, "air")
    # setbacks: 2-row moulded chamfer instead of a flat shelf - an upside-down stair ring on the wider section's
    # top row (undercut) and a stair ring sloping into the narrower wall above it
    for y in SETBACKS:
        hw, hwb = hw_at(y), hw_at(y - 1)
        stair_ring(s, ring(hwb - 1, hwb), y - 1, V["wall_stairs"], "top")
        stair_ring(s, ring(hw, hwb), y, V["wall_stairs"])

    # ---------------------------------------------------------------- lift shaft core (obsidian pillars)
    for y in range(5, CMD + 7):
        for (x, z) in ((15, 15), (18, 15), (15, 18), (18, 18)):
            s.set(x, y, z, CRY if y % 6 == 0 else OBS)
        for x in (16, 17):
            s.set(x, y, 15, CRY if y % 6 == 3 else OBS)     # solid back wall for the ladder

    # ---------------------------------------------------------------- floors, neon bands, trim lines
    for f in FLOORS:
        hw = hw_at(f)
        if f < CMD:
            fill2d(s, inner(hw), f, PD)                         # interior floor
            fill2d(s, ring(hw - 1, hw), f, DT)                  # outer trim line at floor level
        if f > 5:
            hwb = hw_at(f - 1)                                  # neon band = top row of the level below
            yb = f - 2 if f in SETBACKS else f - 1              # (one row lower under the moulded setbacks)
            fill2d(s, ring(hwb - 1, hwb), yb, GLASS)
            fill2d(s, octa(hwb - 1) & ~inner(hwb), yb, LANT)
    # vertical neon strips (2 wide: magenta outer / purple inner, one colour per strip, continuous between the
    # floor bands) + inset deepslate rib between them, on the 4 faces
    for y in range(6, CMD):
        hw = hw_at(y)
        body = octa(hw)
        panel = (y not in FLOORS) and (y + 1 not in FLOORS)
        for a in (14, 15, 16, 17, 18, 19):
            strip = a in (14, 15, 18, 19)
            col = NEON if a in (14, 19) else GLASS
            zs = np.nonzero(body[a, :])[0]
            zmin, zmax = int(zs.min()), int(zs.max())
            xs_ = np.nonzero(body[:, a])[0]
            xmin, xmax = int(xs_.min()), int(xs_.max())
            for (xo, zo, xi, zi) in ((a, zmax, a, zmax - 1), (a, zmin, a, zmin + 1),
                                     (xmax, a, xmax - 1, a), (xmin, a, xmin + 1, a)):
                if not panel:
                    continue                                    # floor trim rows / bands stay continuous
                if strip:
                    s.set(xo, y, zo, col)
                    s.set(xi, y, zi, LANT)
                else:
                    s.set(xo, y, zo, "air")                     # 1-block inset
                    s.set(xi, y, zi, DT)
    # iron trapdoor vent rows at mid-height of each wall section, on the diagonal faces
    for i in range(1, len(FLOORS)):
        y = (FLOORS[i - 1] + FLOORS[i]) // 2
        hw = hw_at(y)
        diag = ring(hw - 1, hw) & (DX + DZ > hw * CHAMFER - 1) & (np.abs(DX - DZ) <= 1.0)
        for x, z in zip(*np.nonzero(diag)):
            x, z = int(x), int(z)
            o = outward(x, z)
            dx, dz = DIRS[o]
            if s.is_air(x + dx, y, z + dz):
                s.set(x + dx, y, z + dz, st.trapdoor("iron", o, "top", open=True))

    # ---------------------------------------------------------------- decks (ring decks + cross runway)
    for d, ext in DECKS.items():
        hw = hw_at(d)
        hwb = hw_at(d - 1)
        outer = hw + ext
        body = octa(hw)
        if d == PAD:
            arm = cross(hw, outer)
            # floor: polished deepslate with a deepslate-tile edge all round
            fill2d(s, arm, d, PD)
            for x, z, _ in edge_cells(arm, body):
                s.set(x, d, z, DT)
            # underside: lantern + neon rings near the body, blackstone plate, bevelled free edges, 2-step corbel
            bevel(s, arm, d - 1, V["wall_stairs"], "top", support=body, fill=PBB)
            fill2d(s, ring(hwb, hwb + 1) & arm, d - 1, LANT)
            fill2d(s, ring(hwb, hwb + 1) & arm & ((DX == 3.5) | (DZ == 3.5)), d - 1, NEON)   # no bare side faces
            fill2d(s, ring(hwb + 1, hwb + 2) & arm, d - 1, NEON)
            bevel(s, cross(hwb, hwb + 3), d - 2, V["wall_stairs"], "top", support=body, fill=PBB)
            stair_ring(s, cross(hwb, hwb + 1), d - 3, V["wall_stairs"], "top")
            # runway markings: purple centreline, lit side lines (sea lantern under purple glass), magenta thresholds
            centre = cross(hw + 1, outer - 2, 0.5) & ~cross(hw, outer, 0.0)
            fill2d(s, centre, d, V["accent"])
            side = ring(hw, outer - 2) & (((DX == 2.5) & (DZ > 3.5)) | ((DZ == 2.5) & (DX > 3.5)))
            fill2d(s, side, d - 1, LANT)
            fill2d(s, side, d, GLASS)
            thr = ring(outer - 2, outer - 1) & arm & ((DX <= 2.5) | (DZ <= 2.5))
            fill2d(s, thr, d - 1, LANT)
            fill2d(s, thr, d, NEON)
            for x, z in zip(*np.nonzero(side | thr)):           # cap the underside faces with purple glass
                s.set_if_air(int(x), d - 2, int(z), GLASS)
            # railing along the arm sides (tips stay open for approach), end rods at the ends
            rail = ring(hw, outer - 1) & (((DX == 3.5) & (DZ > 3.5)) | ((DZ == 3.5) & (DX > 3.5)))
            fill2d(s, rail, d + 1, WALL)
            rail_end = rail & ((DX == outer - 1) | (DZ == outer - 1))
            fill2d(s, rail_end, d + 2, st.end_rod("up"))
            # crystal beacons on the tip corners (wall post + amethyst cluster: purple, not cyan)
            fill2d(s, arm & (DX + DZ == outer + 3.5), d + 1, WALL)
            fill2d(s, arm & (DX + DZ == outer + 3.5), d + 2, st.facing_block("minecraft:amethyst_cluster", "up"))
            # angled struts from the body to the arm tips (2 per arm, polished basalt)
            for a in ("north", "south", "east", "west"):
                for u in (-3.5, 3.5):
                    p1 = arm_xz(a, u, hw - 1.0) + (d - 5,)
                    p2 = arm_xz(a, u, outer - 1.5) + (d - 2,)
                    sh.line(s, (p1[0], p1[2], p1[1]), (p2[0], p2[2], p2[1]), st.log(BASALT, "y"))
                # a wall-pin under the strut tip
                for u in (-3.5, 3.5):
                    x, z = arm_xz(a, u, outer - 0.5)
                    s.set(x, d - 2, z, WALL)
            s.add_sign(19, d + 2, 24, SIGN + "[facing=south]", ["PISTE 7", "atterrissage", "autorise", "code violet"])
            chain_mask = ring(hwb + 1, hwb + 2) & ((DX == 0.5) | (DZ == 0.5))
        else:
            # walkway (ext-1 wide) with a deepslate-tile edge row and 4 corner turrets filling the octagon notches
            t = outer - 3.0 if d == 27 else outer - 2.0        # turret half-width (DX == DZ == t is just outside)
            turret = (DX == t) & (DZ == t)
            fill2d(s, ring(hw, outer - 1), d, PD)
            fill2d(s, ring(outer - 1, outer) | turret, d, DT)
            # underside: lantern collar (capped by glass below), neon ring, 2-step corbel with bevelled edges
            fill2d(s, ring(hwb, hwb + 1), d - 1, LANT)
            fill2d(s, ring(hwb + 1, hwb + 2), d - 1, NEON)
            fill2d(s, ring(hwb + 2, outer - 1) | turret, d - 1, PBB)
            stair_ring(s, ring(outer - 1, outer), d - 1, V["wall_stairs"], "top")
            fill2d(s, ring(hwb, hwb + 1), d - 2, GLASS)
            fill2d(s, ring(hwb + 1, outer - 2), d - 2, PBB)
            stair_ring(s, ring(outer - 2, outer - 1), d - 2, V["wall_stairs"], "top")
            # railing on the edge row; turret posts with end rods and purple banners give the silhouette teeth
            rail = ring(outer - 1, outer)
            fill2d(s, rail, d + 1, WALL)
            fill2d(s, rail & ((DX == 0.5) | (DZ == 0.5)), d + 2, st.end_rod("up"))
            for x, z in zip(*np.nonzero(turret)):
                x, z = int(x), int(z)
                s.set(x, d + 1, z, WALL)
                s.set(x, d + 2, z, WALL)
                s.set(x, d + 3, z, st.end_rod("up"))
                bx = x + (1 if x > C else -1)                   # banner hung on the turret post, outward (x side)
                s.set(bx, d + 2, z, st.wall_banner("purple", "east" if x > C else "west"))
            chain_mask = ring(hwb + 2, hwb + 3) & ((DX == DZ) | (DX == 0.5) | (DZ == 0.5))
        # chains hanging from the underside, ending in amethyst-cluster pendants (purple crystal lights)
        for x, z in zip(*np.nonzero(chain_mask)):
            for k in range(3, 5):
                s.set(int(x), d - k, int(z), st.chain("y"))
            s.set(int(x), d - 5, int(z), st.facing_block("minecraft:amethyst_cluster", "down"))
        # doorways through the wall on the 4 faces + crying obsidian frames
        wall_m = body & ~inner(hw)
        for (x1, x2, z1, z2) in ((16, 17, 0, 15), (16, 17, 18, 33), (0, 15, 16, 17), (18, 33, 16, 17)):
            m2 = np.zeros_like(wall_m)
            m2[x1:x2 + 1, z1:z2 + 1] = True
            for x, z in zip(*np.nonzero(wall_m & m2)):
                for y in range(d + 1, d + 4):
                    s.set(int(x), y, int(z), "air")
            m3 = np.zeros_like(wall_m)
            if z1 == 0 or z1 == 18:
                m3[15:19, z1:z2 + 1] = True
            else:
                m3[x1:x2 + 1, 15:19] = True
            for x, z in zip(*np.nonzero(wall_m & m3)):
                x, z = int(x), int(z)
                if x in (15, 18) and z in (15, 18):
                    continue
                if x in (15, 18) or z in (15, 18):
                    for y in range(d + 1, d + 4):
                        s.set(x, y, z, CRY)
                if ring(hw - 1, hw)[x, z]:
                    s.set(x, d + 4, z, CRY)

    # ---------------------------------------------------------------- command deck (glass, 360 view)
    fill2d(s, octa(8.5), CMD, PD)
    fill2d(s, ring(7.5, 8.5), CMD, DT)
    fill2d(s, ring(5.5, 6.5), CMD - 1, LANT)
    fill2d(s, ring(5.5, 6.5), CMD - 2, GLASS)                                # glass collar caps the lantern ring
    fill2d(s, ring(6.5, 7.5), CMD - 1, NEON)
    stair_ring(s, ring(7.5, 8.5), CMD - 1, V["wall_stairs"], "top")
    wall = ring(7.5, 8.5)
    pillar = wall & (np.abs(DX - DZ) <= 1.0)
    for y in range(CMD + 1, CMD + 6):
        fill2d(s, wall, y, GLASS if y not in (CMD + 1, CMD + 5) else PBB)
        fill2d(s, pillar, y, PBB)
    fill2d(s, wall & (DX == 0.5), CMD + 3, NEON)
    fill2d(s, wall & (DZ == 0.5), CMD + 3, NEON)
    # ceiling, roof plate and rim
    fill2d(s, octa(8.5), CMD + 6, PBB)
    fill2d(s, octa(6.5), CMD + 6, PD)
    for x, z in zip(*np.nonzero(octa(7.5) & ((DX + DZ) % 3 == 1))):
        s.set(int(x), CMD + 6, int(z), LANT)                                  # interior ceiling lights
    fill2d(s, ring(4.5, 5.5), CMD + 6, LANT)
    fill2d(s, octa(6.5), CMD + 7, PBB)
    fill2d(s, ring(4.5, 5.5), CMD + 7, GLASS)                                 # glowing roof ring
    stair_ring(s, ring(6.5, 7.5), CMD + 7, V["wall_stairs"])
    fill2d(s, ring(7.5, 8.5), CMD + 7, st.slab(V["wall_slab"]))
    fill2d(s, ring(7.5, 8.5) & (np.abs(DX - DZ) == 1.0), CMD + 8, st.end_rod("up"))
    # command furniture: console ring, command chair, loot
    for (x, z, f) in ((11, 16, "east"), (11, 17, "east"), (22, 16, "west"), (22, 17, "west"),
                      (16, 22, "north"), (17, 22, "north")):
        s.set(x, CMD + 1, z, st.facing_block("minecraft:observer", "up"))
        s.set(x, CMD + 2, z, "minecraft:daylight_detector")
    for (x, z) in ((12, 14), (12, 19), (21, 14), (21, 19), (14, 21), (19, 21)):
        s.set(x, CMD, z, st.redstone_lamp(True))
    sh.box(s, 15, CMD, 11, 18, CMD, 12, DT)
    for x in (16, 17):
        s.set(x, CMD + 1, 12, st.stairs(V["wall_stairs"], "north"))
        s.set(x, CMD + 2, 11, CRY)
        s.set(x, CMD + 3, 11, OBS)
    s.set(15, CMD + 1, 11, AME); s.set(18, CMD + 1, 11, AME)
    s.set(15, CMD + 2, 11, st.end_rod("up")); s.set(18, CMD + 2, 11, st.end_rod("up"))
    s.add_chest(13, CMD + 1, 12, "south", "minecraft:chests/end_city_treasure")
    s.add_sign(20, CMD + 2, 12, SIGN + "[facing=south]", ["PONT DE", "COMMANDEMENT", "acces niveau 5", "seulement"])

    # ---------------------------------------------------------------- crown: 4 thin sloped fins + tall needle antenna
    base = CMD + 7                                                     # roof plate level
    sh.box(s, 15, base, 15, 18, base + 7, 18, OBS)                    # 4x4 core, 8 high
    for y in (base + 2, base + 5):
        sh.box(s, 15, y, 15, 18, y, 18, CRY)
    NEEDLE_TOP = base + 26
    sh.box(s, 16, base + 8, 16, 17, NEEDLE_TOP, 17, OBS)              # 2x2 needle: the tallest, thinnest element
    for y in range(base + 10, NEEDLE_TOP, 3):
        sh.box(s, 16, y, 16, 17, y, 17, CRY)
    for (x, z) in ((16, 16), (17, 16), (16, 17), (17, 17)):
        s.set(x, NEEDLE_TOP + 1, z, st.pointed_dripstone("up", "frustum"))
        s.set(x, NEEDLE_TOP + 2, z, st.pointed_dripstone("up", "tip"))
    # fins: 1 block thick, pinwheel (4-fold rotational symmetry) around the even 2x2 needle; each fin is a sloped
    # strip (stair / crying-obsidian glow line / brick / upside-down stair) with AIR beneath it, rooted in an
    # obsidian column fused to the needle and propped by thin basalt struts at d = 4 and 7
    FINS = {"north": lambda d: (16, 16 - d), "east": lambda d: (17 + d, 16),
            "south": lambda d: (17, 17 + d), "west": lambda d: (16 - d, 17)}

    def fin_top(d):
        return base + 15 - 2 * (d - 2)                                 # d=2 -> +15 ... d=8 -> +3

    roots = {f(1) for f in FINS.values()}
    for fin in FINS.values():
        x, z = fin(1)                                                  # root column against the needle
        sh.box(s, x, base + 8, z, x, fin_top(2), z, OBS)
        s.set(x, base + 12, z, CRY)
        for d in range(2, 9):
            x, z = fin(d)
            top = fin_top(d)
            if d == 8:                                                 # tip: deepslate cap + lightning rod
                sh.box(s, x, base + 1, z, x, top - 1, z, PBB)
                s.set(x, top, z, DT)
                s.set(x, top + 1, z, st.lightning_rod("up"))
                continue
            s.set(x, top, z, st.stairs(V["wall_stairs"], toward_centre(x, z)))      # sloped top edge
            s.set(x, top - 1, z, CRY)                                                 # glow line under the edge
            s.set(x, top - 2, z, PBB)
            under = top - 3 if d <= 4 else top - 2                                   # fin tapers toward the tip
            if d <= 4:
                s.set(x, under, z, st.stairs(V["wall_stairs"], outward(x, z), "top"))  # bevelled underside
            if d in (4, 7):
                for y in range(base + 1, under):
                    s.set(x, y, z, st.log(BASALT, "y"))                               # thin strut
    # antenna collar: iron bars ring around the needle foot, lightning rods on the 4 corners
    for y in (base + 8, base + 9):
        for x, z in zip(*np.nonzero(ring(0.5, 1.5))):
            if (int(x), int(z)) not in roots:
                s.set(int(x), y, int(z), BARS)
    for (x, z) in ((15, 15), (18, 15), (15, 18), (18, 18)):
        s.set(x, base + 10, z, st.lightning_rod("up"))

    # ---------------------------------------------------------------- lift shaft interior: ladder + bars + doors
    for y in range(6, CMD + 6):
        for x in (16, 17):
            s.set(x, y, 16, "minecraft:ladder[facing=south]")
            s.set(x, y, 17, "air")
    for y in range(6, CMD + 3):
        if y in FLOORS:
            continue
        for z in (16, 17):
            s.set(15, y, z, V["bars"]); s.set(18, y, z, V["bars"])
        for x in (16, 17):
            s.set(x, y, 18, V["bars"])
    for f in FLOORS:
        for x in (16, 17):
            s.set(x, f, 16, "minecraft:ladder[facing=south]")   # hole for the ladder
            s.set(x, f, 17, PD)                                    # landing
            for y in (f + 1, f + 2):
                s.set(x, y, 18, "air")                             # shaft doorway
        for (x, z) in ((14, 14), (19, 14), (14, 19), (19, 19)):
            s.set(x, f, z, st.redstone_lamp(True) if f == CMD else LANT)   # no cyan behind the command glass
    for y in range(8, CMD, 6):
        s.set(15, y, 16, st.end_rod("east")); s.set(18, y, 17, st.end_rod("west"))

    # ---------------------------------------------------------------- lobby (y 6..12) + throne + entrances
    y0 = 5
    for (xs_, zs_) in (((16, 17), range(24, 28)), (range(6, 10), (16, 17)), (range(24, 28), (16, 17))):
        for x in xs_:
            for z in zs_:
                for y in range(6, 10):
                    s.set(x, y, z, "air")
    for (x, z) in ((15, 26), (18, 26), (26, 15), (26, 18), (7, 15), (7, 18),
                   (15, 25), (18, 25), (25, 15), (25, 18), (8, 15), (8, 18)):
        for y in range(6, 10):
            s.set(x, y, z, CRY)
    for (x, z) in ((16, 26), (17, 26), (26, 16), (26, 17), (7, 16), (7, 17),
                   (16, 25), (17, 25), (25, 16), (25, 17), (8, 16), (8, 17)):
        s.set(x, 10, z, CRY)
    for (x, z, f) in ((13, 27, "south"), (20, 27, "south"), (27, 13, "east"), (27, 20, "east"), (6, 13, "west"), (6, 20, "west")):
        for y in (11, 10):
            s.set(x, y, z, st.wall_banner("purple", f))
    s.add_sign(14, 8, 27, SIGN + "[facing=south]", ["TOUR NOIRE", "acces restreint", "intrus =", "cellule"])
    for z in range(11, 24):
        for x in (16, 17):
            s.set(x, y0, z, V["accent"])
    for x in list(range(9, 15)) + list(range(19, 25)):
        for z in (16, 17):
            s.set(x, y0, z, V["accent"])
    for (x, z) in ((12, 12), (21, 12), (12, 21), (21, 21)):
        s.set(x, y0, z, LANT)
    sh.box(s, 13, 6, 9, 20, 6, 11, DT)
    for x in range(13, 21):
        s.set(x, 6, 12, st.stairs(V["wall_stairs_alt"], "north"))
    for x in (16, 17):
        s.set(x, 7, 10, st.stairs(V["wall_stairs"], "north"))
        sh.box(s, x, 7, 9, x, 11, 9, OBS)
        s.set(x, 9, 9, CRY)
    for x in (15, 18):
        sh.box(s, x, 7, 9, x, 10, 9, OBS)
        s.set(x, 8, 9, CRY)
    for x in (14, 19):
        s.set(x, 7, 10, AME); s.set(x, 8, 10, st.end_rod("up"))
    for x in (12, 21):
        s.set(x, 10, 9, st.wall_banner("purple", "south"))
    s.add_chest(13, 7, 10, "south", "minecraft:chests/bastion_other")
    s.add_sign(20, 8, 10, SIGN + "[facing=south]", ["TRONE", "du Directeur", "ne pas", "s asseoir"])
    for x, z in zip(*np.nonzero(octa(7.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), 13, int(z), LANT)

    # ---------------------------------------------------------------- prison (y 14..19): 4 cells around the shaft
    f = 13
    for (bars, door, sign_pos, sign_f, name) in (
            (((13, 21), (12, 12)), (16, 12), (14, 12), "south", "CELLULE N"),
            (((13, 21), (21, 21)), (16, 21), (14, 21), "north", "CELLULE S"),
            (((12, 12), (13, 21)), (12, 16), (12, 14), "east", "CELLULE O"),
            (((21, 21), (13, 21)), (21, 16), (21, 14), "west", "CELLULE E")):
        (bx1, bx2), (bz1, bz2) = bars
        for x in range(bx1, bx2 + 1):
            for z in range(bz1, bz2 + 1):
                for y in range(f + 1, f + 5):
                    if octa(6.5)[x, z]:
                        s.set(x, y, z, V["bars"])
        dx_, dz_ = door
        gate_f = {"south": "east", "north": "east", "east": "south", "west": "south"}[sign_f]
        s.set(dx_, f + 1, dz_, st.trapdoor("iron", gate_f, "bottom", open=True))
        s.set(dx_, f + 2, dz_, st.trapdoor("iron", gate_f, "top", open=True))
        s.add_sign(sign_pos[0], f + 3, sign_pos[1], SIGN + f"[facing={sign_f}]", [name, "detenu 0" + name[-1], "ration : 1", ""])
    for (x, z) in ((14, 10), (19, 10), (14, 23), (19, 23)):
        s.set(x, f + 1, z, st.slab(V["wall_slab"]))
        s.set(x, f + 4, z, st.chain("y"))
    for (x, z) in ((10, 15), (10, 18)):
        s.set(x, f + 1, z, V["sculk"]); s.set(x, f + 2, z, V["sculk_sensor"])
    s.set(23, f + 1, 15, st.slab(V["wall_slab"])); s.set(23, f + 1, 18, "minecraft:cauldron")
    s.add_chest(13, f + 1, 13, "east", "minecraft:chests/simple_dungeon")
    for x, z in zip(*np.nonzero(octa(6.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), f + 7, int(z), st.redstone_lamp(True))
    s.add_sign(14, f + 3, 18, SIGN + "[facing=west]", ["BLOC CELLULES", "6 detenus", "0 evades", ""])

    # ---------------------------------------------------------------- server room (y 21..26)
    f = 20
    for x in (12, 21):
        for z in range(13, 21):
            if octa(5.5)[x, z]:
                s.set(x, f + 1, z, st.facing_block("minecraft:observer", "east" if x == 12 else "west"))
                s.set(x, f + 2, z, st.redstone_lamp(True) if z % 2 else "minecraft:tinted_glass")
                s.set(x, f + 3, z, st.facing_block("minecraft:observer", "east" if x == 12 else "west"))
                s.set(x, f + 4, z, st.trapdoor("iron", "east" if x == 12 else "west", "top"))
                s.set(x, f + 5, z, st.chain("y"))
    for z in (12, 21):
        for x in range(13, 21):
            if octa(5.5)[x, z]:
                s.set(x, f + 1, z, st.facing_block("minecraft:observer", "south" if z == 12 else "north"))
                s.set(x, f + 2, z, st.redstone_lamp(True) if x % 2 else "minecraft:tinted_glass")
                s.set(x, f + 3, z, st.facing_block("minecraft:observer", "south" if z == 12 else "north"))
                s.set(x, f + 4, z, st.trapdoor("iron", "south" if z == 12 else "north", "top"))
    s.set(13, f + 1, 19, st.facing_block("minecraft:lectern", "east"))
    s.set(20, f + 1, 14, "minecraft:daylight_detector")
    s.add_chest(20, f + 1, 19, "west", "minecraft:chests/ancient_city")
    s.add_sign(16, f + 3, 22, SIGN + "[facing=north]", ["SALLE SERVEURS", "temp 4 C", "ne pas", "eteindre"])
    for x, z in zip(*np.nonzero(octa(5.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), f + 7, int(z), LANT)

    # ---------------------------------------------------------------- armoury (y 28..34, deck 1)
    f = 27
    for (x, z) in ((12, 14), (12, 19), (21, 14), (21, 19)):
        s.set(x, f + 1, z, "minecraft:blast_furnace[facing=" + ("east" if x == 12 else "west") + ",lit=true]")
    for z in (15, 18):
        s.set(11, f + 1, z, IRON); s.set(11, f + 2, z, V["bars"])
        s.set(22, f + 1, z, IRON); s.set(22, f + 2, z, V["bars"])
    s.set(13, f + 1, 13, "minecraft:anvil[facing=north]")
    s.add_chest(20, f + 1, 13, "south", "minecraft:chests/bastion_other")
    s.add_chest(20, f + 1, 20, "north", "minecraft:chests/pillager_outpost")
    s.add_sign(16, f + 3, 11, SIGN + "[facing=south]", ["ARMURERIE", "inventaire", "signe :", "capitaine V"])
    for x, z in zip(*np.nonzero(octa(5.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), f + 8, int(z), LANT)

    # ---------------------------------------------------------------- quarters (y 36..40)
    f = 35
    s.set(13, f + 1, 14, st.bed("purple", "north", "head")); s.set(13, f + 1, 15, st.bed("purple", "north", "foot"))
    s.set(20, f + 1, 14, st.bed("purple", "north", "head")); s.set(20, f + 1, 15, st.bed("purple", "north", "foot"))
    s.set(13, f + 1, 19, st.bed("purple", "south", "head")); s.set(13, f + 1, 18, st.bed("purple", "south", "foot"))
    s.set(20, f + 1, 19, st.bed("purple", "south", "head")); s.set(20, f + 1, 18, st.bed("purple", "south", "foot"))
    s.set(15, f + 1, 12, st.facing_block("minecraft:lectern", "south"))
    s.set(18, f + 1, 21, st.facing_block("minecraft:barrel", "up"))
    s.add_chest(15, f + 1, 21, "north", "minecraft:chests/stronghold_library")
    s.add_sign(17, f + 3, 12, SIGN + "[facing=south]", ["QUARTIERS", "officiers", "couvre-feu", "22h"])
    for x, z in zip(*np.nonzero(octa(5.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), f + 6, int(z), LANT)

    # ---------------------------------------------------------------- hangar level (y 42..46, runway)
    f = 41
    for (x, z) in ((13, 14), (13, 19), (20, 14), (20, 19)):
        s.set(x, f + 1, z, st.facing_block("minecraft:barrel", "up"))
        s.set(x, f + 2, z, st.facing_block("minecraft:barrel", "up"))
    s.add_chest(15, f + 1, 21, "north", "minecraft:chests/shipwreck_supply")
    s.add_sign(17, f + 3, 21, SIGN + "[facing=north]", ["HANGAR", "navette 3", "en mission", ""])
    for x, z in zip(*np.nonzero(octa(4.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), f + 6, int(z), LANT)

    # ---------------------------------------------------------------- reactor (y 48..52)
    f = 47
    for (x, z) in ((13, 16), (13, 17), (20, 16), (20, 17), (16, 13), (17, 13), (16, 20), (17, 20)):
        s.set(x, f + 1, z, st.log(BASALT, "y"))
        s.set(x, f + 2, z, CRY)
        s.set(x, f + 3, z, AME)
        s.set(x, f + 4, z, st.end_rod("up"))
    s.add_sign(14, f + 3, 14, SIGN + "[facing=south]", ["REACTEUR", "cristal bleu", "instable", "!!!"])
    for x, z in zip(*np.nonzero(inner(5.5) & ((DX + DZ) % 4 == 1))):
        s.set(int(x), f + 6, int(z), LANT)

    # ---------------------------------------------------------------- airlock ring (y 54..60, deck 3)
    f = 53
    s.add_sign(14, f + 3, 14, SIGN + "[facing=south]", ["SAS", "pont 3", "vent fort", "attache-toi"])
    for x, z in zip(*np.nonzero(inner(5.5) & ((DX + DZ) % 3 == 1))):
        s.set(int(x), f + 8, int(z), LANT)

    # ---------------------------------------------------------------- textures
    sh.texturize(s, PBB, MIX_BODY, seed=21)
    return {"city_spire": s}
