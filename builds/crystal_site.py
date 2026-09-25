"""Crystal science, two structures for the Neige world.

crystal_research_site : a giant tilted blue-crystal cluster (long straight facets, sharp tips, glass veins, amethyst
                        joints, geode mini-spikes) growing out of a packed-ice apron, wrapped in a light study rig
                        (two walkway rings hugging the main spike, two scaffolding columns, ladders, sample drills),
                        three floodlights, a science tent inside the cordon, instrument boxes on overhead cables from a
                        generator, froglight beacons along the path, crates under a tarp, a campfire and a fenced cordon.
drill_rig             : an ice-core drilling rig: stepped lattice derrick (iron-bar legs, chain bracing, dark girder
                        rings, mid platform + ladder) over an open drill floor, a visible lit 3x3 borehole with a drill
                        string down to a rod tip, pale winch house (white + cherry), concrete control cabin on iron legs,
                        round coolant tank on legs with a glass band, sheltered core racks, spoil, warning lights.
"""
import math

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import CRYSTAL, CAMP, GROUND, MIX_ICE, MIX_WHITE, MIX_LIGHT_GRAY

SNOW = GROUND["snow"]
PACKED = "minecraft:packed_ice"
BLUE_ICE = "minecraft:blue_ice"
LB_GLASS = "minecraft:light_blue_stained_glass"
AMETHYST = "minecraft:amethyst_block"
IRON = "minecraft:iron_block"
DARK = "minecraft:polished_deepslate"
DARK_WALL = "minecraft:polished_deepslate_wall"
TILES = "minecraft:deepslate_tiles"
BLACK = "minecraft:polished_blackstone"
LGRAY = "minecraft:light_gray_concrete"
WHITE = "minecraft:white_concrete"
CHERRY = "minecraft:cherry_planks"
LANTERN = "minecraft:sea_lantern"
FROG = "minecraft:pearlescent_froglight"
PLANK = "minecraft:spruce_planks"
DECK = "minecraft:spruce_planks"
GRATE = "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]"
LOG = "minecraft:stripped_spruce_log"
FENCE = "minecraft:spruce_fence"
SCAFF = "minecraft:scaffolding[bottom=false,distance=0,waterlogged=false]"
BARS = "minecraft:iron_bars"
CYAN_GLASS = "minecraft:cyan_stained_glass"
CYAN = "minecraft:cyan_wool"
WOOL = "minecraft:white_wool"
TRODDEN = "minecraft:white_concrete_powder"
BARREL = "minecraft:barrel[facing=up,open=false]"
BASALT_Y = "minecraft:polished_basalt[axis=y]"
D4 = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# ----------------------------------------------------------------------------------------------- local helpers
def oct_in(dx, dz, r):
    """Chamfered-square (octagon) cross-section test."""
    return abs(dx) <= r + 1e-6 and abs(dz) <= r + 1e-6 and abs(dx) + abs(dz) <= 1.5 * r + 1e-6


def oct_metric(dx, dz):
    return max(abs(dx), abs(dz), (abs(dx) + abs(dz)) / 1.5)


def radius_at(t, r0, length):
    """Long straight facets: r0 for 45 % of the length, r0-1 for 25 %, then stepped down (never below 2) toward the
    tip; the point itself is fixed in blocks: 2 blocks at r=1 then a 2-block 1-wide cap."""
    d = (1.0 - t) * length                  # blocks left to the tip
    if d < 2.0:
        return 0
    if d < 4.0:
        return 1
    if r0 <= 2 or t < 0.45:
        return r0
    if t < 0.70:
        return r0 - 1
    u = (t - 0.70) / max(1e-6, (1.0 - 4.0 / length) - 0.70)
    return max(2, int(round((r0 - 1) - (r0 - 3) * u)))


class Spike:
    def __init__(self, base, tip, r0, main=False):
        self.base, self.tip, self.r0, self.main = base, tip, r0, main
        self.length = math.dist(base, tip)

    def axis(self, y):
        bx, by, bz = self.base
        tx, ty, tz = self.tip
        t = (y + 0.5 - by) / (ty - by)
        return bx + (tx - bx) * t, bz + (tz - bz) * t, t

    def r_at_y(self, y):
        return radius_at(self.axis(y)[2], self.r0, self.length)


def carve_spike(s, sp, G, cells):
    """Sweep a tilted octagonal prism from base to tip. `cells` collects {(x,y,z): (dx,dz,t,spike)}."""
    bx, by, bz = sp.base
    tx, ty, tz = sp.tip
    n = int(max(abs(tx - bx), abs(ty - by), abs(tz - bz)) * 3) + 1
    for i in range(n + 1):
        t = i / n
        sx, sy, sz = bx + (tx - bx) * t, by + (ty - by) * t, bz + (tz - bz) * t
        y = int(math.floor(sy))
        if not (0 <= y < s.h):
            continue
        r = radius_at(t, sp.r0, sp.length)
        for x in range(int(math.floor(sx - r - 1)), int(math.ceil(sx + r + 1)) + 1):
            for z in range(int(math.floor(sz - r - 1)), int(math.ceil(sz + r + 1)) + 1):
                dx, dz = x + 0.5 - sx, z + 0.5 - sz
                if oct_in(dx, dz, r) and s.inside(x, y, z):
                    cells[(x, y, z)] = (dx, dz, t, sp)
    # dripstone point only on the main spike (the others end on their 1-wide cap)
    if sp.main:
        tyi, txi, tzi = int(math.floor(ty)), int(math.floor(tx)), int(math.floor(tz))
        if s.inside(txi, tyi + 1, tzi):
            cells[(txi, tyi, tzi)] = (0.0, 0.0, 1.0, sp)
            s.set(txi, tyi + 1, tzi, st.pointed_dripstone("up", "tip"))


def paint_spikes(s, cells, G):
    """Close shades only: ~78 % blue ice, ~20 % packed ice, plus 1-wide light-blue glass veins running base->tip on
    the +x face (and the -z face of the big spikes); a short amethyst vein at the root of the main spike."""
    for (x, y, z), (dx, dz, t, sp) in cells.items():
        h = (x * 7 + y * 13 + z * 5) % 20
        blk = PACKED if h < 4 else BLUE_ICE
        boundary = any((x + ox, y, z + oz) not in cells for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        if boundary and y > G and t < 0.9:
            vein = dx > 0.4 and abs(dz) < 0.5
            if sp.r0 >= 3 and dz < -0.4 and abs(dx) < 0.5:
                vein = True
            if vein:
                blk = LB_GLASS
            elif sp.main and dx < 0 and -dx >= abs(dz) and abs(dz) < 0.75 and y <= G + 5:
                blk = AMETHYST
        s.set(x, y, z, blk)


def collar(s, sp, G, cells):
    """One-high amethyst collar around the root, 1 wider than the spike (the 'joint')."""
    y = G + 1
    ax, az, _ = sp.axis(y)
    r = sp.r0 + 1
    for x in range(int(math.floor(ax - r - 1)), int(math.ceil(ax + r + 1)) + 1):
        for z in range(int(math.floor(az - r - 1)), int(math.ceil(az + r + 1)) + 1):
            dx, dz = x + 0.5 - ax, z + 0.5 - az
            if oct_in(dx, dz, r) and (x, y, z) not in cells and s.inside(x, y, z):
                s.set(x, y, z, AMETHYST)


def clusters_on_collars(s, G):
    """Amethyst clusters / buds only on the exposed top face of the collars (about 2 in 5)."""
    y = G + 1
    for x in range(s.w):
        for z in range(s.l):
            if s.get(x, y, z) == AMETHYST and s.is_air(x, y + 1, z) and (x * 7 + z * 3) % 5 < 2:
                s.set(x, y + 1, z, st.facing_block("amethyst_cluster", "up") if (x + z) % 3 else "minecraft:large_amethyst_bud[facing=up]")


def floodlight(s, x, y0, z, facing, height=6):
    """Spruce-fence mast with a sea lantern head framed by iron trapdoors on 3 sides, open toward `facing`."""
    for y in range(y0, y0 + height):
        s.set(x, y, z, FENCE)
    top = y0 + height
    s.set(x, top, z, IRON)
    s.set(x, top + 1, z, LANTERN)
    for d, (dx, dz) in D4.items():
        if d == facing:
            continue
        s.set(x + dx, top + 1, z + dz, st.trapdoor("iron", d, "bottom", open=True))
    s.set(x, top + 2, z, st.trapdoor("iron", facing, "top", open=False))


def overhead_cable(s, pts, G):
    """Chain line at G+2 along an axis-aligned polyline, carried by spruce fence posts every 4 blocks."""
    cells = []
    for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
        n = max(abs(x2 - x1), abs(z2 - z1))
        sx = 0 if n == 0 else (x2 - x1) // n
        sz = 0 if n == 0 else (z2 - z1) // n
        axis = "x" if x1 != x2 else "z"
        for i in range(0 if not cells else 1, n + 1):
            cells.append((x1 + sx * i, z1 + sz * i, axis))
    verts = set(pts)
    for i, (x, z, axis) in enumerate(cells):
        s.set_if_air(x, G + 2, z, st.chain(axis))
        if (i % 4 == 0 or i == len(cells) - 1 or (x, z) in verts) and s.is_air(x, G + 1, z) and not s.is_air(x, G, z):
            s.set(x, G + 1, z, FENCE)


def instrument_box(s, x, y, z, facing):
    """Sensor box: pale body + solar panel on top, observer 'lens' toward the crystal, iron junction + antenna behind."""
    s.set(x, y, z, LGRAY)
    s.set(x, y + 1, z, "minecraft:daylight_detector")
    dx, dz = D4[facing]
    s.set(x + dx, y, z + dz, st.facing_block("observer", facing))
    s.set(x - dx, y, z - dz, IRON)
    s.set(x - dx, y + 1, z - dz, st.lightning_rod("up"))


def beacon_post(s, x, y0, z):
    s.set(x, y0, z, DARK_WALL)
    s.set(x, y0 + 1, z, FROG)
    s.set(x, y0 + 2, z, st.end_rod("up"))


def snow_edge(s, x, y, z, n):
    if s.inside(x, y, z) and s.is_air(x, y, z) and s.get(x, y - 1, z) == SNOW:
        s.set(x, y, z, st.snow_layer(n))


def science_tent(s, u1, u2, c, g, hw=3, wall=2):
    """Wall tent, ridge along x from u1..u2 at z=c: 2-high white wool walls, smooth quartz-stair slope with a cherry
    hem, one continuous cyan ridge row + cyan gable trim, open front (west) with stripped-log posts and a lantern."""
    def h(v):
        return wall + hw + 1 - abs(v)

    def facing_in(v):
        return "north" if v > 0 else "south"

    for u in range(u1, u2 + 1):
        for v in range(-hw, hw + 1):
            x, z = u, c + v
            top = h(v)
            for dy in range(1, top):
                s.set(x, g + dy, z, WOOL)
            if v == 0:
                s.set(x, g + top, z, CYAN)
            elif u in (u1, u2):
                s.set(x, g + top, z, CYAN)
            else:
                s.set(x, g + top, z, st.stairs("cherry" if abs(v) == hw else "quartz", facing_in(v)))
    for u in range(u1 + 1, u2):
        for v in range(-hw + 1, hw):
            for dy in range(1, h(v) - 1):
                s.set(u, g + dy, c + v, "air")
            s.set(u, g, c + v, PLANK)
    for v in (-1, 0, 1):
        for dy in range(1, h(v) - 1):
            s.set(u1, g + dy, c + v, "air")
        s.set(u1, g, c + v, PLANK if v == 0 else TRODDEN)
    for v in (-2, 2):
        for dy in range(1, h(2) - 1):
            s.set(u1, g + dy, c + v, LOG)
    s.set(u1, g + h(1) - 1, c, LOG)
    s.set(u1, g + h(1) - 2, c, st.lantern(hanging=True))
    for uu in (u1 - 1, u2 + 1):
        s.set(uu, g + h(0), c, st.log(LOG, "x"))
        for y in range(g + 1, g + h(0)):
            s.set(uu, y, c, FENCE)
    for uu in (u1 - 1, u2 + 1):
        for vv in (-(hw + 2), hw + 2):
            s.set(uu, g + 1, c + vv, FENCE)
            s.set(uu, g + 1, c + vv - (1 if vv > 0 else -1), st.chain("z"))
    for u in range(u1 - 1, u2 + 2):
        for vv, n in ((hw + 1, 3), (hw + 2, 1)):
            for sgn in (1, -1):
                if (u + vv * sgn) % 3:
                    snow_edge(s, u, g + 1, c + sgn * vv, n)


def sample_table(s, x, y, z):
    s.set(x, y, z, PLANK); s.set(x + 1, y, z, PLANK)
    s.set(x, y + 1, z, st.facing_block("amethyst_cluster", "up"))
    s.set(x + 1, y + 1, z, "minecraft:medium_amethyst_bud[facing=up]")


# =============================================================================================== crystal site
def build_crystal_site():
    W, H, L, G = 36, 31, 38, 3
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=4)
    cx, cz = 16, 15                                    # crystal cluster root

    # --- packed-ice apron around the root, blue ice near the centre
    sh.ground_disc(s, cx, cz, 10.5, G, PACKED, rim_block=None, seed=7, noise=0.22, depth=2)
    sh.ground_disc(s, cx, cz, 5.0, G, BLUE_ICE, seed=8, noise=0.3, depth=1)
    sh.texturize(s, PACKED, MIX_ICE, seed=21)

    # --- crystal spikes: tilted octagonal prisms with long straight facets and sharp tips
    main = Spike((cx + 0.5, G - 2.0, cz + 0.5), (cx - 4.5, G + 26.5, cz - 3.5), 5, main=True)
    spikes = [
        main,
        Spike((cx + 5.5, G - 2.0, cz + 4.5), (cx + 13.5, G + 16.5, cz + 9.5), 3),
        Spike((cx - 3.5, G - 1.0, cz + 4.5), (cx - 9.5, G + 12.5, cz + 11.5), 2),
        Spike((cx + 2.5, G - 1.0, cz - 3.5), (cx + 8.5, G + 11.5, cz - 10.5), 2),
        Spike((cx - 4.5, G - 1.0, cz - 1.5), (cx - 11.5, G + 7.5, cz - 6.5), 2),
    ]
    # geode look: a mini-spike (60 % scale) at the foot of the two big spikes, leaning a little differently
    minis = []
    for k, sp in enumerate(spikes):
        if sp.r0 < 3:
            continue
        bx, by, bz = sp.base
        tx, ty, tz = sp.tip
        lx, lz = tx - bx, tz - bz
        ln = math.hypot(lx, lz) or 1.0
        px, pz = -lz / ln, lx / ln
        sgn = 1 if k % 2 == 0 else -1
        off = sp.r0 + 1.5
        mb = (bx + px * off * sgn, by + 1, bz + pz * off * sgn)
        ang = 0.6 * sgn
        rlx, rlz = lx * math.cos(ang) - lz * math.sin(ang), lx * math.sin(ang) + lz * math.cos(ang)
        mt = (mb[0] + 0.6 * rlx + px * sgn * 1.5, mb[1] + 0.6 * (ty - by), mb[2] + 0.6 * rlz + pz * sgn * 1.5)
        minis.append(Spike(mb, mt, max(2, int(round(sp.r0 * 0.6)))))
    cells = {}
    for sp in minis + spikes:
        carve_spike(s, sp, G, cells)
    paint_spikes(s, cells, G)
    # amethyst joints: 1-high collars on the 5 real spikes only, a small root mound, clusters on the collar tops
    for sp in spikes:
        collar(s, sp, G, cells)
    sh.ellipsoid(s, cx, G, cz, 3.5, 1.5, 3.0, AMETHYST, only_air=True)
    clusters_on_collars(s, G)

    # --- ground detail on the apron: small ice shards and amethyst buds growing out of the packed ice
    for (ox, oz, h) in ((-9, 3, 2), (8, -7, 1), (-3, -9, 2), (9, 5, 1), (-8, -6, 1), (6, 9, 2), (2, -10, 1), (-10, -2, 1), (10, 0, 2)):
        x, z = cx + ox, cz + oz
        if s.get(x, G, z) in (PACKED, BLUE_ICE, "minecraft:ice") and s.is_air(x, G + 1, z):
            for k in range(h):
                s.set(x, G + 1 + k, z, st.pointed_dripstone("up", "tip" if k == h - 1 else "frustum"))
    for (ox, oz) in ((-7, 5), (7, -4), (-1, 8), (4, -8), (-6, -7), (9, 3)):
        x, z = cx + ox, cz + oz
        if s.get(x, G, z) in (PACKED, BLUE_ICE, "minecraft:ice") and s.is_air(x, G + 1, z):
            s.set(x, G + 1, z, "minecraft:medium_amethyst_bud[facing=up]")

    # --- study rig: two 2-wide walkway rings hugging the main spike (upper = C shape), railings, lanterns in the
    #     inner lane, sample drills, ladders on stripped-log posts, two scaffolding columns
    decks = (G + 7, G + 14)
    ladder_posts = []
    for i, dy in enumerate(decks):
        ax, az, _ = main.axis(dy)
        r = main.r_at_y(dy)
        ring = set()
        for x in range(int(ax - r - 4), int(ax + r + 5)):
            for z in range(int(az - r - 4), int(az + r + 5)):
                dx, dz = x + 0.5 - ax, z + 0.5 - az
                m = oct_metric(dx, dz)
                if m > r + 2 or (x, dy, z) in cells or not s.is_air(x, dy, z):
                    continue
                if i == 1 and dx > 0.5 and dz < -0.5:
                    continue
                ring.add((x, z))
        inner, outer = set(), set()
        for (x, z) in ring:
            touch_spike = any((x + ox, dy, z + oz) in cells for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            touch_out = any((x + ox, z + oz) not in ring and (x + ox, dy, z + oz) not in cells
                            for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if touch_spike:
                inner.add((x, z))
            if touch_out:
                outer.add((x, z))
        for (x, z) in ring:
            if (x, z) in inner or (x, z) not in outer:
                s.set(x, dy, z, DECK)
            else:
                s.set(x, dy, z, GRATE)
        for (x, z) in outer:
            if s.is_air(x, dy + 1, z):
                s.set(x, dy + 1, z, FENCE)
        for d, (ddx, ddz) in D4.items():
            best = min(inner, key=lambda p: -(p[0] + 0.5 - ax) * ddx - (p[1] + 0.5 - az) * ddz, default=None)
            if best:
                s.set(best[0], dy, best[1], LANTERN)
        for k, d in enumerate(("east", "west") if i == 0 else ("south", "west")):
            ddx, ddz = D4[d]
            cand = [p for p in inner if s.get(p[0], dy, p[1]) == DECK]
            best = max(cand, key=lambda p: (p[0] + 0.5 - ax) * ddx + (p[1] + 0.5 - az) * ddz, default=None)
            if best:
                x, z = best
                s.set(x, dy + 1, z, IRON)
                s.set(x, dy + 2, z, st.facing_block("observer", OPP[d]))
                s.set(x, dy + 3, z, st.lightning_rod("up"))
                for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + ox, dy + 1, z + oz) in cells:
                        s.set(x + ox, dy + 1, z + oz, st.lightning_rod({(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(ox, oz)]))
                        break
        south = [p for p in outer if abs(p[0] + 0.5 - ax) <= 1.5 and p[1] > az]
        px, pz = max(south, key=lambda p: p[1])
        y_from = G + 1 if i == 0 else decks[0] + 1
        for y in range(y_from, dy):
            s.set(px, y, pz, LOG)
            s.set(px, y, pz + 1, "minecraft:ladder[facing=south]")
        s.set(px, dy, pz + 1, "minecraft:ladder[facing=south]")
        s.set(px, dy, pz, DECK)
        s.set(px, dy + 1, pz, "air")
        if i == 1:
            s.set_if_air(px, decks[0], pz, DECK)
        ladder_posts.append((px, pz))
        if i == 0:
            spots = sorted(p for p in inner if s.get(p[0], dy, p[1]) == DECK and s.is_air(p[0], dy + 1, p[1]) and p[0] < ax - 1)
            for (x, z) in spots[:2]:
                s.set(x, dy + 1, z, BARREL)
            s.add_sign(px + 1, dy - 1, pz, "minecraft:spruce_wall_sign[facing=east]", ["ECHAFAUDAGE", "max 3 pers.", "casque !", ""])
    # two scaffolding columns (2 wide) on the south side, ground to just above the upper deck, soul lantern on top
    axu, azu, _ = main.axis(decks[1])
    ru = main.r_at_y(decks[1])
    for (sx, sz) in ((1, 1), (-1, 1)):
        x, z = int(math.floor(axu + sx * (ru + 4.5))), int(math.floor(azu + sz * (ru + 4.5)))
        for (ox, oz) in ((0, 0), (1, 0)):
            for y in range(G + 1, decks[1] + 2):
                b = s.get(x + ox, y, z + oz)
                if b == "minecraft:air" or b == DECK or b == GRATE or "fence" in b:
                    s.set(x + ox, y, z + oz, SCAFF)
        s.set(x, decks[1] + 2, z, st.lantern(soul=True, hanging=False))

    # --- cordon rectangle (tent included) and the three floodlights just inside its corners
    cx1, cz1, cx2, cz2 = cx - 13, cz - 13, cx + 16, cz + 20
    for (x, z, f) in ((cx1 + 1, cz1 + 1, "east"), (cx2 - 3, cz1 + 1, "west"), (cx1 + 1, cz2 - 7, "east")):
        floodlight(s, x, G + 1, z, f)

    # --- generator (east) + instrument boxes + overhead cables on fence posts
    gx, gz = cx + 14, cz - 6
    s.set(gx, G + 1, gz, st.facing_block("blast_furnace", "west"))
    s.set(gx, G + 1, gz + 1, IRON)
    s.set(gx, G + 2, gz, GRATE)
    s.set(gx, G + 2, gz + 1, st.lightning_rod("up"))
    s.set(gx, G + 3, gz + 1, st.lightning_rod("up"))
    s.set(gx + 1, G + 1, gz, st.campfire(soul=True, facing="west"))
    s.set(gx - 1, G + 1, gz, "minecraft:cyan_shulker_box")
    instrument_box(s, cx - 11, G + 1, cz + 2, "east")        # solar only (west)
    instrument_box(s, cx + 4, G + 1, cz - 11, "south")       # north
    instrument_box(s, cx + 12, G + 1, cz + 4, "west")        # east
    overhead_cable(s, [(gx, gz + 2), (gx, cz + 3), (cx + 13, cz + 3)], G)
    overhead_cable(s, [(gx - 1, gz - 1), (gx - 1, cz - 10), (cx + 5, cz - 10)], G)

    # --- science tent (south-east, inside the cordon), open to the west toward the deck ladder
    tx1, tx2, tz = cx + 5, cx + 14, cz + 14
    science_tent(s, tx1, tx2, tz, G)
    s.set(tx2 - 1, G + 1, tz - 1, st.bed("cyan", "east", "head"))
    s.set(tx2 - 2, G + 1, tz - 1, st.bed("cyan", "east", "foot"))
    s.set(tx2 - 1, G + 1, tz + 1, st.facing_block("lectern", "west"))
    s.set(tx2 - 3, G + 1, tz + 2, "minecraft:cartography_table")
    s.set(tx1 + 1, G + 1, tz - 2, BARREL)
    s.set(tx1 + 1, G + 2, tz - 2, BARREL)
    s.set(tx1 + 2, G + 1, tz - 2, BARREL)
    s.set(tx1 + 2, G + 1, tz + 2, "minecraft:cyan_shulker_box")
    s.add_chest(tx1 + 1, G + 1, tz + 2, "north", "minecraft:chests/igloo_chest")
    s.set(tx1 + 3, G + 4, tz, st.lantern(hanging=True))
    s.set(tx2 - 2, G + 4, tz, st.lantern(hanging=True))
    s.add_sign(tx2 - 1, G + 2, tz + 2, "minecraft:spruce_wall_sign[facing=west]", ["JOURNAL 12", "le cristal", "chante la nuit", "4.2 Hz"])
    s.set(tx1 + 4, G + 1, tz + 1, "minecraft:cyan_carpet")
    s.set(tx1 + 5, G + 1, tz - 1, "minecraft:cyan_carpet")

    # --- camp life outside the tent: sample table, campfire with a log bench, crate stack under a tarp
    sample_table(s, tx1 - 4, G + 1, tz + 3)
    s.set(tx1 - 3, G + 1, tz - 3, st.campfire(soul=False))
    s.set(tx1 - 5, G + 1, tz - 3, st.log(LOG, "z"))
    s.set(tx1 - 5, G + 1, tz - 2, st.log(LOG, "z"))
    for (x, z) in ((tx1 - 2, tz - 5), (tx1 - 3, tz - 5)):
        s.set(x, G + 1, z, BARREL)
    s.set(tx1 - 3, G + 2, tz - 5, BARREL)
    s.set(tx1 - 3, G + 3, tz - 5, "minecraft:white_carpet")
    s.set(tx1 - 2, G + 2, tz - 5, "minecraft:white_carpet")

    # --- north-west inside the cordon: second sample table, crates under a tarp, spare drill parts
    bx, bz = cx - 10, cz - 9
    for (x, z) in ((bx, bz), (bx + 1, bz), (bx, bz + 1), (bx + 1, bz + 1)):
        s.set(x, G + 1, z, BARREL)
    s.set(bx, G + 2, bz, BARREL); s.set(bx + 1, G + 2, bz, BARREL)
    s.set(bx, G + 3, bz, "minecraft:white_carpet"); s.set(bx + 1, G + 3, bz, "minecraft:white_carpet")
    s.set(bx, G + 2, bz + 1, "minecraft:white_carpet"); s.set(bx + 1, G + 2, bz + 1, "minecraft:white_carpet")
    s.set(bx + 2, G + 1, bz + 1, "minecraft:cyan_shulker_box")
    sample_table(s, cx - 11, G + 1, cz + 6)
    s.set(cx - 9, G + 1, cz + 6, st.lantern(hanging=False))
    s.set(cx - 9, G + 1, cz - 4, IRON)
    s.set(cx - 9, G + 2, cz - 4, st.lightning_rod("up"))
    s.set(cx - 8, G + 1, cz - 4, st.log(LOG, "x"))

    # --- trodden path (2 wide) from the tent door to the deck ladder, snow-layer edges, froglight beacons
    lpx, lpz = ladder_posts[0]
    path = [(tx1 - 1, tz), (tx1 - 5, tz - 2), (lpx + 3, lpz + 5), (lpx, lpz + 3)]
    path_cells = set()
    for (x1, z1), (x2, z2) in zip(path, path[1:]):
        n = max(abs(x2 - x1), abs(z2 - z1))
        for i in range(n + 1):
            x, z = round(x1 + (x2 - x1) * i / n), round(z1 + (z2 - z1) * i / n)
            for (ddx, ddz) in ((0, 0), (1, 0), (0, 1)) if abs(x2 - x1) >= abs(z2 - z1) else ((0, 0), (1, 0)):
                if s.get(x + ddx, G, z + ddz) == SNOW:
                    s.set(x + ddx, G, z + ddz, TRODDEN)
                    path_cells.add((x + ddx, z + ddz))
    for (x, z) in list(path_cells):
        for (ox, oz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + ox, z + oz) not in path_cells and (x * 3 + z * 5 + ox) % 3:
                snow_edge(s, x + ox, G + 1, z + oz, 1 + (x + z) % 2)
    for (x, z) in ((tx1 - 1, tz + 2), (tx1 - 7, tz - 4), (cx + 9, cz + 6), (cx - 3, cz + 12)):
        if s.is_air(x, G + 1, z):
            beacon_post(s, x, G + 1, z)

    # --- cordon: spruce fence with log corner posts and cyan banners, gates, signs
    gaps = {(cx2, cz + 4), (cx2, cz + 5), (cx, cz2), (cx + 1, cz2), (cx1, cz - 2), (cx1, cz - 3)}
    for x in range(cx1, cx2 + 1):
        for z in (cz1, cz2):
            if (x, z) not in gaps and s.is_air(x, G + 1, z) and not s.is_air(x, G, z):
                s.set(x, G + 1, z, FENCE)
    for z in range(cz1, cz2 + 1):
        for x in (cx1, cx2):
            if (x, z) not in gaps and s.is_air(x, G + 1, z) and not s.is_air(x, G, z):
                s.set(x, G + 1, z, FENCE)
    for (x, z, rot) in ((cx1, cz1, 6), (cx2, cz1, 10), (cx1, cz2, 2), (cx2, cz2, 14)):
        s.set(x, G + 1, z, LOG)
        s.set(x, G + 2, z, LOG)
        s.set(x, G + 3, z, st.banner("cyan", rot))
    s.add_sign(cx2, G + 2, cz + 3, "minecraft:spruce_sign[rotation=4]", ["SITE CRISTAL 3", "zone d etude", "ne pas toucher", "resonance !"])
    s.add_sign(cx - 1, G + 2, cz2, "minecraft:spruce_sign[rotation=8]", ["ACCES", "equipe 2", "casque oblig.", ""])

    # --- weathering: snow drift on the leeward (west) side of the cordon, light snow on exposed tops
    skip = ["glass", "ice", "amethyst", "lantern", "froglight", "wool", "iron", "scaffold", "observer", "detector",
            "barrel", "shulker", "concrete", "log", "carpet"]
    sh.snow_cover(s, x1=cx1, z1=cz1, x2=cx - 8, z2=cz2, y_min=G, prob=0.5, seed=9, layers=(1, 4), skip=skip)
    sh.snow_cover(s, y_min=G + 1, prob=0.16, seed=5, skip=skip)
    return s.cropped(pad=1)


# =============================================================================================== drill rig
def hut(s, x1, y0, z1, x2, z2, height, wall=LGRAY, post=DARK, trim="polished_deepslate", stair="polished_andesite"):
    """Pale prefab module: `wall` body (texturized later), `post` corner posts + window-strip frames, bevelled overhang
    (stairs half=top in `stair`), slab parapet rim in `trim`, roof vents + sea-lantern strip, cyan window strips."""
    yr = y0 + height
    sh.box(s, x1, y0, z1, x2, yr, z2, wall)
    sh.box(s, x1 + 1, y0 + 1, z1 + 1, x2 - 1, yr - 1, z2 - 1, "air")
    sh.box(s, x1 + 1, y0, z1 + 1, x2 - 1, y0, z2 - 1, PLANK)
    for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        sh.box(s, x, y0, z, x, yr, z, post)
    sh.box_edge_stairs(s, x1, yr, z1, x2, z2, stair, half="top")
    sh.outline_top(s, x1, yr + 1, z1, x2, z2, st.slab(trim, "bottom"))
    wy = y0 + 2
    for x in range(x1 + 2, x2 - 1):
        s.set(x, wy, z1, CYAN_GLASS); s.set(x, wy, z2, CYAN_GLASS)
    for z in range(z1 + 2, z2 - 1):
        s.set(x1, wy, z, CYAN_GLASS); s.set(x2, wy, z, CYAN_GLASS)
    for (x, z) in ((x1 + 1, z1), (x2 - 1, z1), (x1 + 1, z2), (x2 - 1, z2), (x1, z1 + 1), (x1, z2 - 1), (x2, z1 + 1), (x2, z2 - 1)):
        s.set(x, wy, z, post)
    mz = (z1 + z2) // 2
    for x in range(x1 + 2, x2 - 1):
        if (x - x1) % 2 == 0:
            s.set(x, yr + 1, mz, LANTERN)
    s.set(x1 + 1, yr + 1, z1 + 1, GRATE)
    s.set(x2 - 1, yr + 1, z2 - 1, GRATE)
    s.set(x2 - 1, yr + 1, z1 + 1, GRATE)
    return yr


def core_rack(s, rx1, rz, G, full=True, roof=True):
    """Spruce rack: fence posts, two slab shelves, ice cores stacked like logs, optional slab roof + trapdoor eave."""
    for (x, z) in ((rx1, rz), (rx1 + 5, rz), (rx1, rz + 3), (rx1 + 5, rz + 3)):
        for y in range(G + 1, G + 6 if roof else G + 4):
            s.set(x, y, z, FENCE)
        if not roof:
            s.set(x, G + 4, z, st.slab("spruce", "bottom"))
    for x in range(rx1, rx1 + 6):
        for z in (rz + 1, rz + 2):
            s.set(x, G + 1, z, st.slab("spruce", "top"))
            s.set(x, G + 3, z, st.slab("spruce", "top"))
    for y in (G + 2, G + 4):
        for z in (rz + 1, rz + 2):
            for x in range(rx1, rx1 + 6):
                if full or (y == G + 2 and x < rx1 + 3):
                    s.set(x, y, z, PACKED if (x + z + y) % 3 else BLUE_ICE)
    if roof:
        for x in range(rx1, rx1 + 6):
            for z in range(rz, rz + 4):
                s.set(x, G + 6, z, st.slab("spruce", "bottom"))
            s.set(x, G + 6, rz - 1, st.trapdoor("iron", "south", "top", open=False))
    s.set(rx1 + 6, G + 2, rz + 1, st.trapdoor("iron", "west", "bottom", open=True))
    s.set(rx1 + 6, G + 4, rz + 1, st.trapdoor("iron", "west", "bottom", open=True))


def build_drill_rig():
    W, H, L, G = 28, 34, 28, 3
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=4)
    dx, dz = 10, 11                                     # derrick centre
    # --- plowed pad: irregular polygon of trodden snow following the buildings (snow left between them)
    pad = [(2, 1), (14, 1), (25, 2), (26, 8), (24, 11), (26, 14), (26, 26), (16, 26), (9, 26), (2, 24), (1, 17), (3, 13), (1, 7)]
    sh.polygon_prism(s, pad, G, G, TRODDEN)
    sh.polygon_prism(s, [(2, 7), (7, 7), (7, 9), (2, 9)], G, G, SNOW)
    for (x1, z1, x2, z2) in ((0, 4, 1, 15), (0, 24, 3, 26)):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                n = sh.value_noise2(x, z, 9, 4.0)
                if n > 0.35:
                    s.set(x, G + 1, z, SNOW)
                if n > 0.7:
                    s.set(x, G + 2, z, SNOW)
    for x in range(1, W - 1):
        for z in (1, L - 2):
            snow_edge(s, x, G + 1, z, 2 if (x + z) % 2 else 1)
    for z in range(1, L - 1):
        snow_edge(s, W - 2, G + 1, z, 2 if z % 2 else 1)

    # --- borehole: 3x3 air core down to y=0, deepslate-tile / blue-ice lining lit by sea lanterns, blue-ice collar
    sh.cylinder(s, dx, 0, dz, 2.2, G, TILES, axis="y")
    sh.cylinder(s, dx, 0, dz, 1.6, G, BLUE_ICE, axis="y")
    sh.cylinder(s, dx, 0, dz, 1.2, G, "air", axis="y")
    for (ox, oz) in ((2, 0), (-2, 0), (0, 2), (0, -2)):
        s.set(dx + ox, 1, dz + oz, LANTERN)
        s.set(dx + ox, G - 1, dz + oz, LANTERN)
    sh.ring(s, dx, G + 1, dz, 2.4, BLUE_ICE, thickness=1.0)
    for y in range(1, G + 2):
        s.set(dx, y, dz - 1, "minecraft:ladder[facing=south]")
    s.set(dx, G + 2, dz - 2, st.trapdoor("iron", "south", "bottom", open=True))
    for d, (ddx, ddz) in D4.items():
        if d != "north":
            s.set(dx + 3 * ddx, G + 1, dz + 3 * ddz, "minecraft:iron_trapdoor[facing=%s,half=bottom,open=false]" % d)

    # --- derrick: stepped lattice, 6 sections of 4: iron-bar legs, chain bracing at mid height, dark girder ring
    #     (iron, dark corners) at the top of each section, crown block, mid catwalk ring + ladder
    corners = ((-1, -1), (1, -1), (-1, 1), (1, 1))
    secs = [(G + 1, 4), (G + 5, 4), (G + 9, 3), (G + 13, 3), (G + 17, 2), (G + 21, 1)]
    for i, (y0, h) in enumerate(secs):
        ring_y = y0 + 3
        for (sx, sz) in corners:
            for y in range(y0, ring_y):
                s.set(dx + sx * h, y, dz + sz * h, BARS)
        ym = y0 + 1
        for x in range(dx - h + 1, dx + h):
            s.set(x, ym, dz - h, st.chain("x")); s.set(x, ym, dz + h, st.chain("x"))
        for z in range(dz - h + 1, dz + h):
            s.set(dx - h, ym, z, st.chain("z")); s.set(dx + h, ym, z, st.chain("z"))
        sh.outline_top(s, dx - h, ring_y, dz - h, dx + h, dz + h, IRON)
        for (sx, sz) in corners:
            s.set(dx + sx * h, ring_y, dz + sz * h, DARK)
            if i + 1 < len(secs):
                h2 = secs[i + 1][1]
                s.set(dx + sx * h2, ring_y, dz + sz * h2, DARK)
    for (sx, sz) in corners:
        sh.box(s, dx + sx * 4, G - 1, dz + sz * 4, dx + sx * 4, G, dz + sz * 4, BLACK)      # footings
    top_y = secs[-1][0] + 3                                                              # G+24
    sh.box(s, dx - 1, top_y + 1, dz - 1, dx + 1, top_y + 1, dz + 1, DARK)
    sh.box(s, dx - 1, top_y + 2, dz - 1, dx + 1, top_y + 2, dz + 1, IRON)
    s.set(dx, top_y + 3, dz, st.redstone_lamp(True))
    s.set(dx, top_y + 4, dz, "minecraft:red_stained_glass")
    s.set(dx, top_y + 5, dz, st.lightning_rod("up"))
    for (sx, sz) in corners:
        s.set(dx + sx, top_y + 3, dz + sz, st.end_rod("up"))
    # mid platform at the top of section 1 (G+8): iron-trapdoor floor, bar railing, ladder up the solid SE leg
    py = G + 8
    for x in range(dx - 3, dx + 4):
        for z in range(dz - 3, dz + 4):
            if max(abs(x - dx), abs(z - dz)) == 3:
                s.set(x, py, z, GRATE)
    for x in range(dx - 4, dx + 5):
        for z in range(dz - 4, dz + 5):
            if (x in (dx - 4, dx + 4) or z in (dz - 4, dz + 4)) and s.is_air(x, py + 1, z) and (x, z) != (dx + 4, dz + 4):
                s.set(x, py + 1, z, BARS)
    for y in range(G + 5, G + 8):
        s.set(dx + 4, y, dz + 4, IRON)
    for y in range(G + 5, G + 9):
        s.set(dx + 4, y, dz + 5, "minecraft:ladder[facing=south]")
    s.set(dx + 1, py + 1, dz + 1, st.lantern(soul=False, hanging=False))
    # drill string: chain from the crown to the bottom of the hole, basalt pipe joints, kelly + top drive, rod bit
    for y in range(1, top_y + 2):
        s.set(dx, y, dz, BASALT_Y if y % 5 == 0 else st.chain("y"))
    s.set(dx, 0, dz, st.lightning_rod("down"))
    s.set(dx, G + 5, dz, IRON); s.set(dx, G + 6, dz, IRON)
    s.set(dx, G + 7, dz, st.facing_block("piston", "up"))
    s.set(dx, G + 11, dz, "minecraft:cauldron")

    # --- drill floor: deck at G+4 with an OPEN 3x3 well around the string (iron-bar guard), dark rim, railing, stairs
    xa, za, xb, zb = dx - 4, dz - 4, dx + 4, dz + 4
    for x in range(xa - 1, xb + 2):
        for z in range(za - 1, zb + 2):
            if abs(x - dx) <= 1 and abs(z - dz) <= 1:
                continue
            if s.get(x, G + 4, z) != IRON:
                edge = x in (xa - 1, xb + 1) or z in (za - 1, zb + 1)
                s.set(x, G + 4, z, DARK if edge else PLANK)
    for x in range(dx - 2, dx + 3):
        for z in range(dz - 2, dz + 3):
            if (abs(x - dx) == 2 or abs(z - dz) == 2) and s.is_air(x, G + 5, z):
                s.set(x, G + 5, z, BARS)
    for x in range(xa - 1, xb + 2):
        for z in range(za - 1, zb + 2):
            if (x in (xa - 1, xb + 1) or z in (za - 1, zb + 1)) and s.get(x, G + 4, z) == DARK and s.is_air(x, G + 5, z):
                s.set(x, G + 5, z, BARS)
    sh.stair_ramp(s, dx + 2, G + 1, zb + 5, 4, "north", "polished_deepslate", width=1)
    for i in range(1, 4):
        s.set_if_air(dx + 2, G + i, zb + 5 - i, DARK)
    s.set(dx + 2, G + 5, zb + 1, "air")
    for (x, z) in ((xa, za), (xb, za), (xa, zb), (xb, zb)):
        s.set_if_air(x, G + 3, z, LANTERN)

    # --- winch house (north-east): white + cherry camp module, open west face toward the derrick, drum + line
    wx1, wz1, wx2, wz2 = 17, 2, 23, 7
    wyr = hut(s, wx1, G + 1, wz1, wx2, wz2, 4, wall=WHITE, post=CHERRY, trim="cherry", stair="cherry")
    sh.box(s, wx1, G + 2, wz1 + 2, wx1, G + 4, wz2 - 2, "air")
    sh.box(s, wx1, G + 2, wz1 + 1, wx1, G + 4, wz1 + 1, CHERRY)
    sh.box(s, wx1, G + 2, wz2 - 1, wx1, G + 4, wz2 - 1, CHERRY)
    s.set(wx1, G + 1, wz1 + 3, DARK); s.set(wx1, G + 1, wz1 + 4, DARK)
    s.set(wx1 + 2, G + 2, wz1 + 3, st.log("minecraft:polished_basalt", "z"))
    s.set(wx1 + 2, G + 2, wz1 + 2, IRON); s.set(wx1 + 2, G + 2, wz1 + 4, IRON)
    s.set(wx1 + 3, G + 2, wz1 + 3, st.facing_block("blast_furnace", "west"))
    s.set(wx1 + 4, G + 2, wz1 + 3, st.facing_block("observer", "west"))
    s.set(wx1 + 4, G + 2, wz1 + 1, "minecraft:lever[face=wall,facing=south]")
    s.set(wx1 + 5, G + 2, wz1 + 2, BARREL)
    s.set(wx1 + 5, G + 2, wz1 + 4, "minecraft:cauldron")
    s.set(wx1 + 3, G + 4, wz1 + 3, LANTERN)
    s.set(wx1 + 5, G + 4, wz1 + 2, LANTERN)
    s.add_chest(wx1 + 5, G + 2, wz2 - 1, "north", "minecraft:chests/abandoned_mineshaft")
    s.add_sign(wx2 - 1, G + 3, wz1 + 1, "minecraft:spruce_wall_sign[facing=south]", ["TREUIL 2", "cable 40 m", "carotte 7", "gelee"])
    for y in range(G + 3, wyr + 1):
        s.set(wx1 + 2, y, wz1 + 3, st.chain("y"))
    s.set(wx1 + 1, wyr + 1, wz1 + 3, IRON)
    s.set(wx1 + 2, wyr + 1, wz1 + 3, st.chain("x"))
    for x in range(dx + 2, wx1 + 1):
        s.set_if_air(x, wyr + 1, wz1 + 3, st.chain("x"))
    for z in range(wz1 + 3, dz - 1):
        s.set_if_air(dx + 1, wyr + 1, z, st.chain("z"))
    for y in range(wyr + 1, top_y + 1):
        s.set_if_air(dx + 1, y, dz - 1, st.chain("y"))

    # --- coolant tank (south-west): round r=3 on deepslate-wall legs, full-height cyan glass band showing the blue
    #     coolant, pale top with a quartz-slab bevel, sea lantern underneath, valve lever, raised pipe to the hole
    tx, tz = 4, 20
    for (ox, oz) in ((2, 2), (-2, 2), (2, -2), (-2, -2)):
        sh.box(s, tx + ox, G + 1, tz + oz, tx + ox, G + 2, tz + oz, DARK_WALL)
    s.set(tx, G + 1, tz, LANTERN)
    sh.cylinder(s, tx, G + 3, tz, 3.0, 0, DARK, axis="y")
    sh.cylinder(s, tx, G + 4, tz, 3.0, 2, BLUE_ICE, axis="y")
    sh.cylinder(s, tx, G + 4, tz, 3.0, 2, CYAN_GLASS, axis="y", hollow=True, thickness=1.0)
    sh.cylinder(s, tx, G + 7, tz, 3.0, 0, LGRAY, axis="y")
    sh.cylinder(s, tx, G + 8, tz, 2.0, 0, st.slab("smooth_quartz", "bottom"), axis="y")
    s.set(tx, G + 8, tz, IRON); s.set(tx, G + 9, tz, st.lightning_rod("up"))
    s.set(tx + 2, G + 8, tz - 1, GRATE)
    s.set(tx + 4, G + 3, tz, "minecraft:lever[face=wall,facing=east]")
    pipe_y = G + 2
    s.set(tx, G + 4, tz - 4, st.log("minecraft:polished_basalt", "z"))
    for y in (G + 1, G + 2, G + 3):
        s.set(tx, y, tz - 4, BASALT_Y)
    for x in range(tx + 1, dx - 2):
        s.set_if_air(x, pipe_y, tz - 4, st.log("minecraft:polished_basalt", "x"))
    s.set(dx - 3, pipe_y + 1, tz - 4, BASALT_Y)
    s.set(tx + 3, G + 1, tz - 4, DARK_WALL)
    s.set(dx - 3, G + 1, tz - 4, DARK_WALL)
    s.set(tx - 4, G + 1, tz, "minecraft:cauldron")
    s.set(tx - 4, G + 1, tz + 1, "minecraft:water_cauldron[level=3]")

    # --- ice-chip spoil pile beside the well + soul lantern on a fence post
    sh.ellipsoid(s, 4, G, 11, 2.3, 1.7, 2.1, PACKED, only_air=True)
    sh.ellipsoid(s, 4, G, 11, 1.2, 1.3, 1.0, BLUE_ICE, only_air=False)
    sh.scatter(s, 2, 8, 6, 14, [BLUE_ICE, PACKED, st.slab("smooth_quartz")], 6, seed=13)
    for y in (G + 1, G + 2):
        s.set(7, y, 8, FENCE)
    s.set(7, G + 3, 8, st.lantern(soul=True, hanging=False))
    s.set(3, G + 1, 14, st.slab("polished_deepslate"))

    # --- core racks (south): a full rack and a half-full rack under slab lean-to roofs
    core_rack(s, 9, 22, G, full=True)
    core_rack(s, 17, 22, G, full=False, roof=False)
    s.add_sign(11, G + 4, 21, "minecraft:spruce_wall_sign[facing=north]", ["CAROTTES", "-40 m a -120 m", "glace bleue", "ne pas fondre"])

    # --- control cabin (south-east): concrete module on visible iron legs, tall cyan glass front, consoles, ramp
    kx1, kz1, kx2, kz2 = 17, 13, 23, 19
    ky = G + 4
    for (x, z) in ((kx1, kz1), (kx2, kz1), (kx1, kz2), (kx2, kz2)):
        sh.box(s, x, G + 1, z, x, ky - 1, z, IRON)
    s.set(kx1, G + 2, (kz1 + kz2) // 2, LANTERN)
    kyr = hut(s, kx1, ky, kz1, kx2, kz2, 4, wall=WHITE, trim="smooth_quartz", stair="quartz")
    sh.box(s, kx1, ky + 1, kz1 + 1, kx1, ky + 2, kz2 - 1, CYAN_GLASS)
    sh.box(s, kx2, ky + 1, kz1 + 3, kx2, ky + 2, kz1 + 3, "air")                        # door (east)
    s.set(kx2, ky, kz1 + 3, DARK)
    s.set(kx2 + 1, ky, kz1 + 3, DARK)
    sh.box(s, kx2 + 1, G + 1, kz1 + 3, kx2 + 1, ky - 1, kz1 + 3, DARK_WALL)
    sh.stair_ramp(s, kx2 + 1, G + 1, kz1 + 6, 3, "north", "polished_deepslate", width=1)
    for i in range(1, 3):
        sh.box(s, kx2 + 1, G + 1, kz1 + 6 - i, kx2 + 1, G + i, kz1 + 6 - i, DARK_WALL)
    for z in range(kz1 + 1, kz2):
        s.set(kx1 + 1, ky + 1, z, "minecraft:daylight_detector" if z % 2 else st.facing_block("observer", "east"))
    s.set(kx1 + 2, ky + 1, kz1 + 1, st.redstone_lamp(True))
    s.set(kx1 + 2, ky + 1, kz2 - 1, st.redstone_lamp(True))
    s.set(kx1 + 3, ky + 1, kz1 + 3, st.stairs("polished_deepslate", "west"))
    s.set(kx2 - 1, ky + 1, kz2 - 1, st.facing_block("lectern", "west"))
    s.set(kx2 - 1, ky + 1, kz1 + 1, BARREL)
    s.set(kx2 - 2, ky + 1, kz1 + 1, "minecraft:cyan_shulker_box")
    s.set((kx1 + kx2) // 2, ky + 3, (kz1 + kz2) // 2, LANTERN)
    s.set(kx1 + 1, ky + 3, kz1 + 1, LANTERN); s.set(kx2 - 1, ky + 3, kz2 - 1, LANTERN)
    s.add_sign(kx2 - 1, ky + 2, kz2 - 1, "minecraft:spruce_wall_sign[facing=west]", ["FORAGE J+31", "-118 m", "vibrations", "arret auto"])
    s.set(kx1 + 2, kyr + 1, kz1 + 2, IRON)
    s.set(kx1 + 2, kyr + 2, kz1 + 2, st.lightning_rod("up"))
    s.set(kx1 + 2, kyr + 3, kz1 + 2, st.lightning_rod("up"))
    for x in range(kx2 - 4, kx2 - 1):
        s.set(x, kyr + 1, kz2 - 2, "minecraft:daylight_detector")
    s.set(kx1 + 2, kyr + 1, kz2 - 2, st.redstone_lamp(True))
    overhead_cable(s, [(kx1 - 1, kz1 + 2), (dx + 6, kz1 + 2)], G)

    # --- warning lights on posts + generator by the winch house + entrance sign
    for (x, z) in ((4, 3), (24, 24), (25, 11)):
        sh.box(s, x, G + 1, z, x, G + 3, z, DARK_WALL)
        s.set(x, G + 4, z, st.redstone_lamp(True))
        s.set(x, G + 5, z, "minecraft:red_stained_glass")
    s.set(wx2 + 1, G + 1, wz2 - 2, st.facing_block("blast_furnace", "north"))
    s.set(wx2 + 1, G + 2, wz2 - 2, st.lightning_rod("up"))
    s.set(wx2 + 1, G + 1, wz2 - 1, IRON)
    s.set(wx2 + 1, G + 1, wz2, st.campfire(soul=True))
    s.set(wx2 + 2, G + 1, wz2 - 1, "minecraft:cyan_shulker_box")
    s.add_sign(14, G + 1, 26, "minecraft:spruce_sign[rotation=13]", ["FORAGE F-2", "zone bruyante", "casque", "prudence"])
    s.set(14, G, 26, TRODDEN)

    sh.texturize(s, LGRAY, MIX_LIGHT_GRAY, seed=31)
    sh.texturize(s, WHITE, MIX_WHITE, seed=32)
    sh.snow_cover(s, y_min=G + 2, prob=0.15, seed=6,
                  skip=["glass", "ice", "lantern", "iron", "lamp", "chain", "bars", "fence", "slab", "stairs", "detector", "observer",
                        "barrel", "shulker", "cauldron", "concrete", "andesite", "deepslate", "quartz", "calcite", "cherry"])
    return s.cropped(pad=1)


def build():
    return {"crystal_research_site": build_crystal_site(), "drill_rig": build_drill_rig()}
