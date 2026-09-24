"""Crystal science, two structures for the Neige world.

crystal_research_site : a giant tilted blue-crystal cluster (faceted prisms, amethyst collars, geode mini-spikes)
                        growing out of a packed-ice apron, wrapped in a light study rig (two walkway rings hugging
                        the main spike, scaffolding columns, ladders, sample drills), floodlights, a science tent,
                        instrument boxes wired to a generator, froglight beacons along the path and a fenced cordon.
drill_rig             : an ice-core drilling rig: tapered iron derrick over an open drill floor, drill string down a
                        lined borehole, pale winch house, coolant tank + raised pipes, control cabin, core racks,
                        ice-chip spoil, warning lights, on an irregular snow-plowed pad with snow banks.
"""
import math

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import CRYSTAL, CAMP, GROUND, MIX_ICE, MIX_WHITE

SNOW = GROUND["snow"]
PACKED = "minecraft:packed_ice"
BLUE_ICE = "minecraft:blue_ice"
LB_GLASS = "minecraft:light_blue_stained_glass"
PURPLE_GLASS = CRYSTAL["glass_purple"]
AMETHYST = "minecraft:amethyst_block"
BUDDING = "minecraft:budding_amethyst"
IRON = "minecraft:iron_block"
DARK = "minecraft:polished_deepslate"
DARK_WALL = "minecraft:polished_deepslate_wall"
TILES = "minecraft:deepslate_tiles"
BLACK = "minecraft:polished_blackstone"
LGRAY = "minecraft:light_gray_concrete"
WHITE = "minecraft:white_concrete"
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
MIX_LG = [(LGRAY, 7), (WHITE, 2), ("minecraft:polished_andesite", 1)]
D4 = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}


# ----------------------------------------------------------------------------------------------- local helpers
def oct_in(dx, dz, r):
    """Chamfered-square (octagon) cross-section test."""
    return abs(dx) <= r + 1e-6 and abs(dz) <= r + 1e-6 and abs(dx) + abs(dz) <= 1.5 * r + 1e-6


def oct_metric(dx, dz):
    return max(abs(dx), abs(dz), (abs(dx) + abs(dz)) / 1.5)


def radius_at(t, r0):
    """Discrete, stepped radius along the spike: straight facets, sharp tip."""
    first = min(0.6, 0.32 + 0.12 * max(0, 4 - r0))
    if t < first:
        return r0
    if t >= 0.94:
        return 0
    n = r0 - 1
    if n <= 0:
        return 0
    seg = (0.94 - first) / n
    k = int((t - first) / seg)
    return max(0, r0 - 1 - k)


def facing_to(dx, dz):
    if abs(dx) >= abs(dz):
        return "east" if dx > 0 else "west"
    return "south" if dz > 0 else "north"


class Spike:
    def __init__(self, base, tip, r0, main=False):
        self.base, self.tip, self.r0, self.main = base, tip, r0, main

    def axis(self, y):
        bx, by, bz = self.base
        tx, ty, tz = self.tip
        t = (y + 0.5 - by) / (ty - by)
        return bx + (tx - bx) * t, bz + (tz - bz) * t, t

    def r_at_y(self, y):
        return radius_at(self.axis(y)[2], self.r0)


def carve_spike(s, sp, G, cells):
    """Sweep a tilted octagonal prism from base to tip. `cells` collects {(x,y,z): (dx,dz,t)} for face texturing."""
    bx, by, bz = sp.base
    tx, ty, tz = sp.tip
    n = int(max(abs(tx - bx), abs(ty - by), abs(tz - bz)) * 3) + 1
    for i in range(n + 1):
        t = i / n
        sx, sy, sz = bx + (tx - bx) * t, by + (ty - by) * t, bz + (tz - bz) * t
        y = int(math.floor(sy))
        if not (0 <= y < s.h):
            continue
        r = radius_at(t, sp.r0)
        for x in range(int(math.floor(sx - r - 1)), int(math.ceil(sx + r + 1)) + 1):
            for z in range(int(math.floor(sz - r - 1)), int(math.ceil(sz + r + 1)) + 1):
                dx, dz = x + 0.5 - sx, z + 0.5 - sz
                if oct_in(dx, dz, r) and s.inside(x, y, z):
                    cells[(x, y, z)] = (dx, dz, t, sp)
    # sharp tip
    tyi = int(math.floor(ty))
    txi, tzi = int(math.floor(tx)), int(math.floor(tz))
    if s.inside(txi, tyi + 1, tzi):
        cells[(txi, tyi, tzi)] = (0.0, 0.0, 1.0, sp)
        s.set(txi, tyi + 1, tzi, st.pointed_dripstone("up", "tip"))


def paint_spikes(s, cells, G):
    """Face-based texturing: blue ice mass, one whole light-blue glass face (+x), packed ice on the shaded (-x)
    face with a blue->violet gradient near the root, an amethyst vein up the shaded face of the main spike."""
    for (x, y, z), (dx, dz, t, sp) in cells.items():
        boundary = any((x + ox, y, z + oz) not in cells for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        blk = BLUE_ICE
        if boundary and y > G:
            h = (x * 7 + y * 13 + z * 5) % 10
            level = y - (G + 3)
            if dx > 0 and dx >= abs(dz):
                blk = LB_GLASS
            elif dx < 0 and -dx >= abs(dz):
                blk = PACKED
                if sp.main and y <= G + 12 and abs(dz) < 0.75:
                    blk = AMETHYST
            p = 0.7 if level <= 0 else (0.35 if level == 1 else (0.18 if level == 2 else (0.1 if t < 0.34 else 0.0)))
            if blk != LB_GLASS and blk != AMETHYST and h < p * 10:
                blk = PURPLE_GLASS
        s.set(x, y, z, blk)


def collar(s, sp, G, cells, height):
    """Amethyst collar around the root: 1 wider than the spike, clusters on the exposed faces."""
    for y in range(G + 1, G + 1 + height):
        ax, az, _ = sp.axis(y)
        r = sp.r0 + 1
        for x in range(int(math.floor(ax - r - 1)), int(math.ceil(ax + r + 1)) + 1):
            for z in range(int(math.floor(az - r - 1)), int(math.ceil(az + r + 1)) + 1):
                dx, dz = x + 0.5 - ax, z + 0.5 - az
                if oct_in(dx, dz, r) and (x, y, z) not in cells and s.inside(x, y, z):
                    s.set(x, y, z, BUDDING if (x * 3 + z * 5 + y) % 4 == 0 else AMETHYST)


def clusters_on_amethyst(s, G, y_max, density=4):
    for x in range(s.w):
        for z in range(s.l):
            for y in range(G + 1, y_max):
                if s.get(x, y, z) not in (AMETHYST, BUDDING):
                    continue
                if s.is_air(x, y + 1, z) and (x * 7 + z * 3) % density != 1:
                    s.set(x, y + 1, z, st.facing_block("amethyst_cluster", "up") if (x + z) % 3 else "minecraft:large_amethyst_bud[facing=up]")
                for d, (dx, dz) in D4.items():
                    if s.is_air(x + dx, y, z + dz) and (x * 5 + z * 11 + y) % density != 2:
                        s.set(x + dx, y, z + dz, st.facing_block("amethyst_cluster", d))


def floodlight(s, x, y0, z, height, facing):
    """Spruce-fence mast with a sea lantern head framed by iron trapdoors, tilted toward `facing`."""
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


def cable(s, pts, y):
    """Chain cable lying on the ground along a polyline of (x, z) points (axis-aligned segments)."""
    for (x1, z1), (x2, z2) in zip(pts, pts[1:]):
        if x1 == x2:
            for z in range(min(z1, z2), max(z1, z2) + 1):
                s.set_if_air(x1, y, z, st.chain("z"))
        else:
            for x in range(min(x1, x2), max(x1, x2) + 1):
                s.set_if_air(x, y, z1, st.chain("x"))


def instrument_box(s, x, y, z, facing):
    s.set(x, y, z, LGRAY)
    s.set(x, y + 1, z, "minecraft:daylight_detector")
    dx, dz = D4[facing]
    s.set(x + dx, y, z + dz, st.facing_block("observer", facing))
    s.set(x - dx, y, z - dz, IRON)
    s.set(x - dx, y + 1, z - dz, st.lightning_rod("up"))


def beacon_post(s, x, y0, z):
    s.set(x, y0, z, DARK_WALL)
    s.set(x, y0 + 1, z, DARK_WALL)
    s.set(x, y0 + 2, z, FROG)
    s.set(x, y0 + 3, z, st.end_rod("up"))


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
                s.set(x, g + top, z, CYAN)                                   # continuous cyan ridge row
            elif u in (u1, u2) or u in (u1 + 3, u2 - 3):
                s.set(x, g + top, z, CYAN if u in (u1, u2) else st.stairs("quartz", facing_in(v)))
                if u in (u1, u2):
                    pass
            else:
                s.set(x, g + top, z, st.stairs("cherry" if abs(v) == hw else "quartz", facing_in(v)))
    # cyan gable trim: the gable ends get a cyan block on top of the slope instead of a stair
    for u in (u1, u2):
        for v in range(-hw, hw + 1):
            if v != 0:
                s.set(u, g + h(v), c + v, CYAN)
    # interior + plank floor
    for u in range(u1 + 1, u2):
        for v in range(-hw + 1, hw):
            for dy in range(1, h(v) - 1):
                s.set(u, g + dy, c + v, "air")
            s.set(u, g, c + v, PLANK)
    # open front (west, u1): doorway |v| <= 1 full height of the interior, framed by stripped-log posts
    for v in (-1, 0, 1):
        for dy in range(1, h(v) - 1):
            s.set(u1, g + dy, c + v, "air")
        s.set(u1, g, c + v, PLANK if v == 0 else TRODDEN)
    for v in (-2, 2):
        for dy in range(1, h(2) - 1):
            s.set(u1, g + dy, c + v, LOG)
    s.set(u1, g + h(1) - 1, c, LOG)
    s.set(u1, g + h(1) - 2, c, st.lantern(hanging=True))
    # ridge pole ends (log) + guy lines to fence pegs at the four corners
    for uu, d in ((u1 - 1, -1), (u2 + 1, 1)):
        s.set(uu, g + h(0), c, st.log(LOG, "x"))
        for y in range(g + 1, g + h(0)):
            s.set(uu, y, c, FENCE)
    for uu in (u1 - 1, u2 + 1):
        for vv in (-(hw + 2), hw + 2):
            s.set(uu, g + 1, c + vv, FENCE)
            s.set(uu, g + 1, c + vv - (1 if vv > 0 else -1), st.chain("z"))
    # snow piling against the skirt
    for u in range(u1 - 1, u2 + 2):
        for vv, n in ((hw + 1, 3), (hw + 2, 1)):
            for sgn in (1, -1):
                if (u + vv * sgn) % 3:
                    snow_edge(s, u, g + 1, c + sgn * vv, n)


# =============================================================================================== crystal site
def build_crystal_site():
    W, H, L, G = 44, 31, 44, 3
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=4)
    cx, cz = 19, 21                                    # crystal cluster root

    # --- packed-ice apron around the root, blue ice near the centre
    sh.ground_disc(s, cx, cz, 10.5, G, PACKED, rim_block=None, seed=7, noise=0.22, depth=2)
    sh.ground_disc(s, cx, cz, 5.0, G, BLUE_ICE, seed=8, noise=0.3, depth=1)
    sh.texturize(s, PACKED, MIX_ICE, seed=21)

    # --- crystal spikes as tilted octagonal prisms with stepped radius (straight facets, sharp tips)
    main = Spike((cx + 0.5, G - 2.0, cz + 0.5), (cx - 4.5, G + 26.5, cz - 3.5), 5, main=True)
    spikes = [
        main,
        Spike((cx + 5.5, G - 2.0, cz + 4.5), (cx + 13.5, G + 16.5, cz + 9.5), 3),
        Spike((cx - 3.5, G - 1.0, cz + 4.5), (cx - 9.5, G + 12.5, cz + 11.5), 2),
        Spike((cx + 2.5, G - 1.0, cz - 3.5), (cx + 8.5, G + 11.5, cz - 10.5), 2),
        Spike((cx - 4.5, G - 1.0, cz - 1.5), (cx - 11.5, G + 7.5, cz - 6.5), 2),
    ]
    # geode look: a matching mini-spike (60 % scale) at the foot of every spike, leaning a little differently
    minis = []
    for k, sp in enumerate(spikes):
        if sp.r0 < 3:
            continue
        bx, by, bz = sp.base
        tx, ty, tz = sp.tip
        lx, lz = tx - bx, tz - bz
        ln = math.hypot(lx, lz) or 1.0
        px, pz = -lz / ln, lx / ln                     # perpendicular to the lean
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
    # amethyst collars (1 wider than each spike, 1-2 high) + root mound binding everything, then clusters
    for sp in spikes:
        collar(s, sp, G, cells, 2 if sp.main else 1)
    for sp in minis:
        collar(s, sp, G, cells, 1)
    sh.ellipsoid(s, cx, G - 1, cz, 6.0, 2.6, 5.5, AMETHYST, only_air=True)
    sh.texturize(s, AMETHYST, [(AMETHYST, 7), (BUDDING, 2)], seed=22)
    clusters_on_amethyst(s, G, G + 4, density=2)

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

    # --- study rig: two 2-wide walkway rings hugging the main spike (upper = C shape), bevelled rims, railings,
    #     sea lanterns in the inner lane, sample drills, ladders on stripped-log posts, scaffolding columns + bracing
    decks = (G + 7, G + 14)
    deck_cells = {}
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
                if i == 1 and dx > 0.5 and dz < -0.5:              # C shape: open toward the north-east
                    continue
                ring.add((x, z))
        deck_cells[dy] = ring
        inner, outer = set(), set()
        for (x, z) in ring:
            touch_spike = any((x + ox, dy, z + oz) in cells for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            touch_out = any((x + ox, z + oz) not in ring and (x + ox, dy, z + oz) not in cells
                            for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if touch_spike:
                inner.add((x, z))
            if touch_out:
                outer.add((x, z))
        # inner lane: plank walkway against the crystal; outer lane: iron-trapdoor grating (thin, light) + fence rail
        for (x, z) in ring:
            if (x, z) in inner or (x, z) not in outer:
                s.set(x, dy, z, DECK)
            else:
                s.set(x, dy, z, GRATE)
        for (x, z) in outer:
            if s.is_air(x, dy + 1, z):
                s.set(x, dy + 1, z, FENCE)
        # sea lanterns set into the inner lane (4 cardinal points)
        for d, (ddx, ddz) in D4.items():
            best = min(inner, key=lambda p: -(p[0] + 0.5 - ax) * ddx - (p[1] + 0.5 - az) * ddz, default=None)
            if best:
                s.set(best[0], dy, best[1], LANTERN)
        # sample drills: iron block + observer looking into the crystal + antenna, on the inner lane (2 per deck)
        for k, d in enumerate(("east", "west") if i == 0 else ("south", "west")):
            ddx, ddz = D4[d]
            cand = [p for p in inner if s.get(p[0], dy, p[1]) == DECK]
            best = max(cand, key=lambda p: (p[0] + 0.5 - ax) * ddx + (p[1] + 0.5 - az) * ddz, default=None)
            if best:
                x, z = best
                s.set(x, dy + 1, z, IRON)
                s.set(x, dy + 2, z, st.facing_block("observer", {"east": "west", "west": "east", "south": "north", "north": "south"}[d]))
                s.set(x, dy + 3, z, st.lightning_rod("up"))
                # drill bit: a lightning rod stuck into the crystal face next to the iron block
                for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if (x + ox, dy + 1, z + oz) in cells:
                        s.set(x + ox, dy + 1, z + oz, st.lightning_rod({(1, 0): "west", (-1, 0): "east", (0, 1): "north", (0, -1): "south"}[(ox, oz)]))
                        break
        # ladder post: stripped-log column on the south outer lane, ladder on its south face
        south = [p for p in outer if abs(p[0] + 0.5 - ax) <= 1.5 and p[1] > az]
        px, pz = max(south, key=lambda p: p[1])
        y_from = G + 1 if i == 0 else decks[0] + 1
        for y in range(y_from, dy):
            s.set(px, y, pz, LOG)
            s.set(px, y, pz + 1, "minecraft:ladder[facing=south]")
        s.set(px, dy, pz + 1, "minecraft:ladder[facing=south]")
        s.set(px, dy, pz, DECK)
        s.set(px, dy + 1, pz, "air")                                      # railing gap where the ladder arrives
        if i == 1:
            s.set_if_air(px, decks[0], pz, DECK)
        ladder_posts.append((px, pz))
        # tool crates + sign on the lower deck
        if i == 0:
            spots = sorted(p for p in inner if s.get(p[0], dy, p[1]) == DECK and s.is_air(p[0], dy + 1, p[1]) and p[0] < ax - 1)
            for (x, z) in spots[:2]:
                s.set(x, dy + 1, z, BARREL)
            s.add_sign(px + 1, dy - 1, pz, "minecraft:spruce_wall_sign[facing=east]", ["ECHAFAUDAGE", "max 3 pers.", "casque !", ""])
    # scaffolding columns (2 wide) at three points around the rig, from the ground to above the upper deck,
    # diagonal iron-bar bracing between them at mid height
    axu, azu, _ = main.axis(decks[1])
    ru = main.r_at_y(decks[1])
    cols = []
    for (sx, sz) in ((1, 1), (-1, 1), (-1, -1)):
        x, z = int(math.floor(axu + sx * (ru + 4.5))), int(math.floor(azu + sz * (ru + 4.5)))
        cols.append((x, z))
        for (ox, oz) in ((0, 0), (1, 0) if sz > 0 else (0, 1)):
            top = s.top_y(x + ox, z + oz)
            for y in range(G + 1, decks[1] + 3):
                b = s.get(x + ox, y, z + oz)
                if b == "minecraft:air" or b == DECK or b == GRATE or "fence" in b:
                    s.set(x + ox, y, z + oz, SCAFF)
        s.set(x, decks[1] + 3, z, st.lantern(soul=True, hanging=False))
    for (a, b) in ((cols[0], cols[1]), (cols[1], cols[2])):
        p1 = (a[0], G + 8, a[1])
        p2 = (b[0], decks[1] - 1, b[1])
        n = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), abs(p2[2] - p1[2]))
        for k in range(n + 1):
            t = k / n
            x, y, z = round(p1[0] + (p2[0] - p1[0]) * t), round(p1[1] + (p2[1] - p1[1]) * t), round(p1[2] + (p2[2] - p1[2]) * t)
            s.set_if_air(x, y, z, BARS)
    # hanging cables from the upper ring down to the ground (sample lines)
    for (hx, hz) in ((int(axu - ru - 3), int(azu + 1)), (int(axu - 1), int(azu + ru + 4))):
        if s.get(hx, decks[1], hz) == DECK:
            for y in range(G + 1, decks[1]):
                s.set_if_air(hx, y, hz, st.chain("y"))

    # --- floodlights on the corners of the apron, pointing at the crystal
    for (x, z, f, h) in ((cx - 14, cz - 12, "east", 5), (cx + 9, cz - 14, "south", 6), (cx - 13, cz + 10, "north", 5),
                         (cx + 14, cz + 12, "west", 5)):
        floodlight(s, x, G + 1, z, h, f)

    # --- generator + instrument boxes + cables
    gx, gz = cx + 16, cz - 5
    s.set(gx, G + 1, gz, st.facing_block("blast_furnace", "west"))
    s.set(gx, G + 1, gz + 1, IRON)
    s.set(gx, G + 2, gz, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
    s.set(gx, G + 2, gz + 1, st.lightning_rod("up"))
    s.set(gx, G + 3, gz + 1, st.lightning_rod("up"))
    s.set(gx + 1, G + 1, gz, st.campfire(soul=True, facing="west"))
    s.set(gx - 1, G + 1, gz, "minecraft:cyan_shulker_box")
    instrument_box(s, cx - 13, G + 1, cz + 1, "east")
    instrument_box(s, cx + 7, G + 1, cz + 12, "north")
    instrument_box(s, cx + 3, G + 1, cz - 13, "south")
    cable(s, [(gx, gz + 2), (gx, cz + 14), (cx + 9, cz + 14)], G + 1)
    cable(s, [(gx - 2, gz), (cx + 10, gz), (cx + 10, cz - 13), (cx + 5, cz - 13)], G + 1)
    cable(s, [(gx, gz - 2), (gx, cz - 15), (cx - 14, cz - 15), (cx - 14, cz - 11)], G + 1)
    cable(s, [(cx - 15, cz + 1), (cx - 16, cz + 1), (cx - 16, cz + 13), (cx - 13, cz + 13), (cx - 13, cz + 11)], G + 1)

    # --- science tent (south-east), open to the west toward the crystal
    tx1, tx2, tz = cx + 9, cx + 18, cz + 16
    science_tent(s, tx1, tx2, tz, G)
    # interior: desk, map table, bed, crates, lanterns, journal sign, loot chest, carpets
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
    s.set(tx2 - 1, G + 2, tz - 1, "minecraft:light_blue_stained_glass_pane") if False else None

    # --- sample crates + sample table near the tent entrance
    for (x, z) in ((tx1 - 3, tz - 4), (tx1 - 4, tz - 4), (tx1 - 3, tz - 5)):
        s.set(x, G + 1, z, BARREL)
    s.set(tx1 - 4, G + 2, tz - 4, "minecraft:cyan_shulker_box")
    s.set(tx1 - 3, G + 1, tz + 3, PLANK)
    s.set(tx1 - 4, G + 1, tz + 3, PLANK)
    s.set(tx1 - 3, G + 2, tz + 3, st.facing_block("amethyst_cluster", "up"))
    s.set(tx1 - 4, G + 2, tz + 3, "minecraft:medium_amethyst_bud[facing=up]")

    # --- trodden path (2 wide) from the tent door to the deck ladder, snow-layer edges, froglight beacons
    lpx, lpz = ladder_posts[0]
    path = [(tx1 - 1, tz), (tx1 - 5, tz - 1), (lpx + 4, lpz + 5), (lpx, lpz + 3)]
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
    for (x, z) in ((tx1 - 3, tz - 2), (tx1 - 8, tz - 5), (cx + 9, cz + 7), (cx - 2, cz + 13)):
        if s.is_air(x, G + 1, z):
            beacon_post(s, x, G + 1, z)

    # --- cordon: spruce fence square around the apron with log corner posts and cyan banners
    cx1, cz1, cx2, cz2 = cx - 15, cz - 14, cx + 12, cz + 13
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

    # --- weathering: light snow on exposed tops
    sh.snow_cover(s, y_min=G + 1, prob=0.16, seed=5,
                  skip=["glass", "ice", "amethyst", "lantern", "froglight", "wool", "iron", "scaffold", "observer", "detector",
                        "barrel", "shulker", "concrete", "log"])
    return s.cropped(pad=1)


# =============================================================================================== drill rig
def hut(s, x1, y0, z1, x2, z2, height, G):
    """Pale prefab module: light-gray body (texturized later), dark plinth row / corner posts / roof rim, bevelled
    overhang (stairs half=top), roof vents + sea-lantern strip, cyan glass window strips on every wall."""
    yr = y0 + height                                    # roof slab level
    sh.box(s, x1, y0, z1, x2, yr, z2, LGRAY)
    sh.box(s, x1 + 1, y0 + 1, z1 + 1, x2 - 1, yr - 1, z2 - 1, "air")
    sh.box(s, x1 + 1, y0, z1 + 1, x2 - 1, y0, z2 - 1, PLANK)                                      # floor
    sh.hollow_box(s, x1, y0, z1, x2, y0, z2, DARK, floor=False, ceiling=False)                    # plinth row
    for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        sh.box(s, x, y0, z, x, yr - 1, z, DARK)                                                   # corner posts
    sh.box_edge_stairs(s, x1, yr, z1, x2, z2, "polished_andesite", half="top")                   # bevelled overhang (pale)
    sh.outline_top(s, x1, yr + 1, z1, x2, z2, st.slab("polished_deepslate", "bottom"))            # parapet rim
    wy = y0 + 2                                                                                    # window row
    for x in range(x1 + 2, x2 - 1):
        s.set(x, wy, z1, CYAN_GLASS); s.set(x, wy, z2, CYAN_GLASS)
    for z in range(z1 + 2, z2 - 1):
        s.set(x1, wy, z, CYAN_GLASS); s.set(x2, wy, z, CYAN_GLASS)
    # roof furniture: two vents, a sea-lantern strip along the middle, one end rod
    mx, mz = (x1 + x2) // 2, (z1 + z2) // 2
    for x in range(x1 + 2, x2 - 1):
        if (x - x1) % 2 == 0:
            s.set(x, yr + 1, mz, LANTERN)
    s.set(x1 + 1, yr + 1, z1 + 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
    s.set(x2 - 1, yr + 1, z2 - 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
    s.set(x2 - 1, yr + 1, z1 + 1, "minecraft:iron_trapdoor[facing=north,half=bottom,open=false]")
    return yr


def build_drill_rig():
    W, H, L, G = 28, 32, 28, 3
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, SNOW, depth=4)
    dx, dz = 10, 11                                     # derrick centre
    # --- plowed pad: irregular polygon of trodden snow following the buildings (snow left between them)
    pad = [(2, 1), (14, 1), (25, 2), (26, 8), (24, 11), (26, 14), (26, 25), (16, 26), (9, 25), (2, 24), (1, 17), (3, 13), (1, 7)]
    sh.polygon_prism(s, pad, G, G, TRODDEN)
    sh.polygon_prism(s, [(2, 7), (7, 7), (7, 9), (2, 9)], G, G, SNOW)      # untouched snow tongue (west)
    # snow banks pushed by the plow on the leeward (west + south) side: 1-2 high with layers on top
    for (x1, z1, x2, z2) in ((0, 4, 1, 22), (3, 25, 14, 26), (0, 23, 3, 26)):
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                n = sh.value_noise2(x, z, 9, 4.0)
                if n > 0.35:
                    s.set(x, G + 1, z, SNOW)
                if n > 0.7:
                    s.set(x, G + 2, z, SNOW)
    for x in range(1, W - 1):                                              # thin bank on the far edges
        for z in (1, L - 2):
            snow_edge(s, x, G + 1, z, 2 if (x + z) % 2 else 1)
    for z in range(1, L - 1):
        snow_edge(s, W - 2, G + 1, z, 2 if z % 2 else 1)

    # --- borehole: lined shaft down to y=0, collar + blue-ice ring standing above the pad
    sh.cylinder(s, dx, 0, dz, 2.2, G, TILES, axis="y")
    sh.cylinder(s, dx, 0, dz, 1.4, G, BLUE_ICE, axis="y")
    sh.cylinder(s, dx, 0, dz, 0.6, G, "air", axis="y")
    sh.ring(s, dx, G + 1, dz, 2.4, TILES, thickness=1.0)
    sh.ring(s, dx, G + 1, dz, 1.4, BLUE_ICE, thickness=1.0)
    sh.cylinder(s, dx, G, dz, 1.4, 0, BLUE_ICE, axis="y", hollow=True, thickness=1.0)
    for d, (ddx, ddz) in D4.items():
        s.set(dx + 3 * ddx, G + 1, dz + 3 * ddz, "minecraft:iron_trapdoor[facing=%s,half=bottom,open=false]" % d)

    # --- derrick: 4 tapered legs, dark girder rings every 4 blocks, iron-bar bracing, crown block on top
    top_y = G + 24
    half0, half1 = 4.0, 1.0

    def leg_xy(sx, sz, y):
        t = (y - (G + 1)) / (top_y - (G + 1))
        h = half0 + (half1 - half0) * t
        return round(dx + sx * h), round(dz + sz * h)
    corners = ((-1, -1), (1, -1), (-1, 1), (1, 1))
    for (sx, sz) in corners:
        x0, z0 = leg_xy(sx, sz, G + 1)
        sh.box(s, x0, G - 1, z0, x0, G, z0, BLACK)                       # footing
        for y in range(G + 1, top_y + 1):
            x, z = leg_xy(sx, sz, y)
            s.set(x, y, z, IRON)
    for y in range(G + 1, top_y + 1, 4):
        ring_y = y + 3 if y + 3 <= top_y else top_y
        (xa, za), (xb, zb) = leg_xy(-1, -1, ring_y), leg_xy(1, 1, ring_y)
        for x in range(xa, xb + 1):
            for z in range(za, zb + 1):
                if (x in (xa, xb) or z in (za, zb)) and s.is_air(x, ring_y, z):
                    s.set(x, ring_y, z, DARK)
        for by in range(y, ring_y):
            (xa2, za2), (xb2, zb2) = leg_xy(-1, -1, by), leg_xy(1, 1, by)
            mids = {(dx, za2), (dx, zb2), (xa2, dz), (xb2, dz)}
            if xb2 - xa2 >= 6:
                mids |= {(xa2 + 2, za2), (xb2 - 2, za2), (xa2 + 2, zb2), (xb2 - 2, zb2),
                         (xa2, za2 + 2), (xa2, zb2 - 2), (xb2, za2 + 2), (xb2, zb2 - 2)}
            for (x, z) in mids:
                if s.is_air(x, by, z):
                    s.set(x, by, z, BARS)
    (xa, za), (xb, zb) = leg_xy(-1, -1, top_y), leg_xy(1, 1, top_y)
    sh.box(s, xa, top_y + 1, za, xb, top_y + 1, zb, IRON)
    sh.box(s, xa, top_y + 2, za, xb, top_y + 2, zb, DARK)
    s.set(dx, top_y + 3, dz, st.redstone_lamp(True))
    s.set(dx, top_y + 4, dz, "minecraft:red_stained_glass")
    s.set(dx, top_y + 5, dz, st.lightning_rod("up"))
    for (sx, sz) in corners:
        x, z = leg_xy(sx, sz, top_y)
        s.set(x, top_y + 3, z, st.end_rod("up"))
    # drill string: chain from the crown down into the hole, kelly (iron) + swivel + top drive
    for y in range(0, top_y + 1):
        s.set(dx, y, dz, st.chain("y"))
    s.set(dx, G + 9, dz, IRON)
    s.set(dx, G + 10, dz, "minecraft:cauldron")
    sh.box(s, dx, G + 1, dz, dx, G + 4, dz, IRON)
    s.set(dx, G + 5, dz, st.facing_block("piston", "up"))

    # --- drill floor: raised deck at G+4 with an OPEN 3x3 well around the string (iron-bar safety rail),
    #     dark rim, outer railing, stairs, lit underside
    (xa, za), (xb, zb) = leg_xy(-1, -1, G + 4), leg_xy(1, 1, G + 4)
    for x in range(xa - 1, xb + 2):
        for z in range(za - 1, zb + 2):
            if abs(x - dx) <= 1 and abs(z - dz) <= 1:
                continue                                                  # open well
            if s.is_air(x, G + 4, z):
                edge = x in (xa - 1, xb + 1) or z in (za - 1, zb + 1)
                s.set(x, G + 4, z, DARK if edge else PLANK)
    for x in range(dx - 2, dx + 3):
        for z in range(dz - 2, dz + 3):
            if (abs(x - dx) == 2 or abs(z - dz) == 2) and s.is_air(x, G + 5, z):
                s.set(x, G + 5, z, BARS)                                  # well guard rail
    for x in range(xa - 1, xb + 2):
        for z in range(za - 1, zb + 2):
            if (x in (xa - 1, xb + 1) or z in (za - 1, zb + 1)) and s.get(x, G + 4, z) == DARK and s.is_air(x, G + 5, z):
                s.set(x, G + 5, z, BARS)
    sh.stair_ramp(s, dx + 2, G + 1, zb + 5, 4, "north", "polished_deepslate", width=1)
    for i in range(1, 4):
        s.set_if_air(dx + 2, G + i, zb + 5 - i, DARK)
    s.set(dx + 2, G + 5, zb + 1, "air")                                   # gap in the railing at the stair top
    for (x, z) in ((xa, za), (xb, za), (xa, zb), (xb, zb)):
        s.set_if_air(x, G + 3, z, LANTERN)                                # lights under the deck

    # --- winch house (north-east): pale module, open west face toward the derrick, drum + line up to the crown
    wx1, wz1, wx2, wz2 = 17, 2, 23, 7
    wyr = hut(s, wx1, G + 1, wz1, wx2, wz2, 4, G)
    sh.box(s, wx1, G + 2, wz1 + 2, wx1, G + 4, wz2 - 2, "air")            # west opening
    sh.box(s, wx1, G + 2, wz1 + 1, wx1, G + 4, wz1 + 1, IRON)
    sh.box(s, wx1, G + 2, wz2 - 1, wx1, G + 4, wz2 - 1, IRON)
    s.set(wx1, G + 1, wz1 + 3, DARK); s.set(wx1, G + 1, wz1 + 4, DARK)    # threshold stays dark
    # interior: winch drum (iron cheeks + basalt axle), motor, control lever, lantern, barrel, cauldron, loot, sign
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
    # winch line: up from the drum through the roof to an iron fairlead, across to the derrick, up to the crown
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

    # --- coolant / mud tank (south-west): pale cylinder, cyan glass level band, dark rims, raised pipes to the hole
    tx, tz = 4, 20
    sh.cylinder(s, tx, G + 1, tz, 2.4, 5, LGRAY, axis="y")
    sh.cylinder(s, tx, G + 3, tz, 2.4, 0, CYAN_GLASS, axis="y", hollow=True, thickness=1.0)
    sh.cylinder(s, tx, G + 1, tz, 2.4, 0, DARK, axis="y", hollow=True, thickness=1.0)
    sh.ring(s, tx, G + 6, tz, 2.4, DARK, thickness=1.0)
    sh.ring_stairs(s, tx, G + 7, tz, 2.0, "polished_deepslate", half="bottom")
    s.set(tx, G + 7, tz, IRON); s.set(tx, G + 8, tz, st.lightning_rod("up"))
    s.set(tx + 3, G + 3, tz, st.log("minecraft:polished_basalt", "x"))       # outlet at the glass band
    pipe_y = G + 2
    s.set(tx + 3, pipe_y, tz, st.log("minecraft:polished_basalt", "y"))
    for x in range(tx + 3, dx - 2):                                           # east along z=tz-1... on posts
        s.set_if_air(x, pipe_y, tz - 2, st.log("minecraft:polished_basalt", "x"))
    s.set(tx + 3, pipe_y, tz - 1, st.log("minecraft:polished_basalt", "z"))
    for z in range(dz + 3, tz - 2):
        s.set_if_air(dx - 2, pipe_y, z, st.log("minecraft:polished_basalt", "z"))
    s.set(dx - 2, pipe_y, tz - 2, st.log("minecraft:polished_basalt", "y"))
    s.set(dx - 2, pipe_y, dz + 3, st.log("minecraft:polished_basalt", "y"))
    s.set(dx - 2, pipe_y + 1, dz + 3, st.log("minecraft:polished_basalt", "x"))
    s.set(dx - 1, pipe_y + 1, dz + 3, st.log("minecraft:polished_basalt", "x"))
    s.set(dx - 1, pipe_y + 1, dz + 2, st.log("minecraft:polished_basalt", "z"))
    s.set(dx - 1, pipe_y, dz + 2, st.log("minecraft:polished_basalt", "y"))
    for (x, z) in ((tx + 5, tz - 2), (dx - 2, tz - 4), (dx - 2, dz + 5)):      # chain hangers / posts under the pipe
        s.set_if_air(x, G + 1, z, st.chain("y"))
    s.set(tx + 4, G + 1, tz - 2, DARK_WALL)
    s.set(tx + 1, G + 2, tz - 3, "minecraft:lever[face=wall,facing=north]")
    s.set(tx - 3, G + 1, tz, "minecraft:cauldron")                                 # overflow drums
    s.set(tx - 3, G + 1, tz + 1, "minecraft:water_cauldron[level=3]")

    # --- ice-chip spoil pile beside the well + soul lantern on a fence post
    sh.ellipsoid(s, 4, G, 11, 2.3, 1.7, 2.1, PACKED, only_air=True)
    sh.ellipsoid(s, 4, G, 11, 1.2, 1.3, 1.0, BLUE_ICE, only_air=False)
    sh.scatter(s, 2, 8, 6, 14, [BLUE_ICE, PACKED, st.slab("smooth_quartz")], 6, seed=13)
    for y in (G + 1, G + 2):
        s.set(7, y, 8, FENCE)
    s.set(7, G + 3, 8, st.lantern(soul=True, hanging=False))
    s.set(3, G + 1, 14, st.slab("polished_deepslate"))                             # dropped plate

    # --- core racks (south, east of the tank): spruce frame, ice cores stacked like logs
    rx1, rz = 10, 20
    for x in range(rx1, rx1 + 6):
        for y in range(G + 1, G + 4):
            s.set(x, y, rz, FENCE); s.set(x, y, rz + 3, FENCE)
        for z in range(rz + 1, rz + 3):
            s.set(x, G + 1, z, st.slab("spruce", "top"))
            s.set(x, G + 3, z, st.slab("spruce", "top"))
    for x in range(rx1 - 1, rx1 + 7):
        s.set(x, G + 4, rz, st.slab("spruce", "bottom")); s.set(x, G + 4, rz + 3, st.slab("spruce", "bottom"))
    for y in (G + 2, G + 4):
        for z in (rz + 1, rz + 2):
            for x in range(rx1, rx1 + 6):
                s.set(x, y, z, PACKED if (x + z + y) % 3 else BLUE_ICE)
    s.set(rx1 + 6, G + 2, rz + 1, "minecraft:iron_trapdoor[facing=west,half=bottom,open=true]")
    s.set(rx1 + 6, G + 4, rz + 1, "minecraft:iron_trapdoor[facing=west,half=bottom,open=true]")
    s.add_sign(rx1 + 2, G + 4, rz - 1, "minecraft:spruce_wall_sign[facing=north]", ["CAROTTES", "-40 m a -120 m", "glace bleue", "ne pas fondre"])

    # --- control cabin (south-east): pale module on iron legs, cyan glass front toward the derrick, consoles
    kx1, kz1, kx2, kz2 = 17, 14, 23, 20
    for (x, z) in ((kx1 + 1, kz1 + 1), (kx2 - 1, kz1 + 1), (kx1 + 1, kz2 - 1), (kx2 - 1, kz2 - 1)):
        sh.box(s, x, G + 1, z, x, G + 2, z, IRON)
    kyr = hut(s, kx1, G + 3, kz1, kx2, kz2, 4, G)
    sh.box(s, kx1, G + 5, kz1 + 1, kx1, G + 6, kz2 - 1, CYAN_GLASS)                    # tall glass front (west)
    sh.box(s, kx1, G + 3, kz1 + 1, kx1, G + 3, kz2 - 1, DARK)
    sh.box(s, kx2, G + 4, kz1 + 3, kx2, G + 6, kz1 + 3, "air")                          # door (east)
    s.set(kx2, G + 4, kz1 + 3, DARK)
    s.set(kx2, G + 5, kz1 + 3, "air"); s.set(kx2, G + 6, kz1 + 3, "air")
    s.set(kx2 + 1, G + 4, kz1 + 3, DARK)
    sh.stair_ramp(s, kx2 + 1, G + 1, kz1 + 6, 3, "north", "polished_deepslate", width=1)
    s.set_if_air(kx2 + 1, G + 3, kz1 + 4, DARK)
    s.set_if_air(kx2 + 1, G + 2, kz1 + 4, DARK)
    s.set_if_air(kx2 + 1, G + 1, kz1 + 4, DARK)
    s.set_if_air(kx2 + 1, G + 3, kz1 + 3, DARK)
    s.set_if_air(kx2 + 1, G + 2, kz1 + 3, DARK); s.set_if_air(kx2 + 1, G + 1, kz1 + 3, DARK)
    # consoles along the glass front + lamps + lights
    for z in range(kz1 + 1, kz2):
        s.set(kx1 + 1, G + 4, z, "minecraft:daylight_detector" if z % 2 else st.facing_block("observer", "east"))
    s.set(kx1 + 2, G + 4, kz1 + 1, st.redstone_lamp(True))
    s.set(kx1 + 2, G + 4, kz2 - 1, st.redstone_lamp(True))
    s.set(kx1 + 3, G + 4, kz1 + 3, st.stairs("polished_deepslate", "west"))
    s.set(kx2 - 1, G + 4, kz2 - 1, st.facing_block("lectern", "west"))
    s.set(kx2 - 1, G + 4, kz1 + 1, BARREL)
    s.set(kx2 - 2, G + 4, kz1 + 1, "minecraft:cyan_shulker_box")
    s.set((kx1 + kx2) // 2, G + 6, (kz1 + kz2) // 2, LANTERN)
    s.set(kx1 + 1, G + 6, kz1 + 1, LANTERN); s.set(kx2 - 1, G + 6, kz2 - 1, LANTERN)
    s.add_sign(kx2 - 1, G + 5, kz2 - 1, "minecraft:spruce_wall_sign[facing=west]", ["FORAGE J+31", "-118 m", "vibrations", "arret auto"])
    s.set(kx1 + 2, kyr + 1, kz1 + 2, IRON)
    s.set(kx1 + 2, kyr + 2, kz1 + 2, st.lightning_rod("up"))
    s.set(kx1 + 2, kyr + 3, kz1 + 2, st.lightning_rod("up"))
    for x in range(kx2 - 4, kx2 - 1):
        s.set(x, kyr + 1, kz2 - 2, "minecraft:daylight_detector")                     # solar panels
    s.set(kx1 + 2, kyr + 1, kz2 - 2, st.redstone_lamp(True))
    for x in range(dx + 5, kx1):                                                       # cable to the derrick
        s.set_if_air(x, G + 1, kz1 + 2, st.chain("x"))

    # --- warning lights on posts (offset from the corners) + generator by the winch house
    for (x, z) in ((4, 3), (23, 24), (2, 21)):
        sh.box(s, x, G + 1, z, x, G + 3, z, DARK_WALL)
        s.set(x, G + 4, z, st.redstone_lamp(True))
        s.set(x, G + 5, z, "minecraft:red_stained_glass")
    s.set(wx2 + 1, G + 1, wz2 - 2, st.facing_block("blast_furnace", "north"))
    s.set(wx2 + 1, G + 2, wz2 - 2, st.lightning_rod("up"))
    s.set(wx2 + 1, G + 1, wz2 - 1, IRON)
    s.set(wx2 + 1, G + 1, wz2, st.campfire(soul=True))
    s.set(wx2 + 2, G + 1, wz2 - 1, "minecraft:cyan_shulker_box")
    s.add_sign(14, G + 1, 25, "minecraft:spruce_sign[rotation=13]", ["FORAGE F-2", "zone bruyante", "casque", "prudence"])
    s.set(14, G, 25, TRODDEN)

    sh.texturize(s, LGRAY, MIX_LG, seed=31)
    sh.snow_cover(s, y_min=G + 2, prob=0.15, seed=6,
                  skip=["glass", "ice", "lantern", "iron", "lamp", "chain", "bars", "fence", "slab", "stairs", "detector", "observer",
                        "barrel", "shulker", "cauldron", "concrete", "andesite", "deepslate"])
    return s.cropped(pad=1)


def build():
    return {"crystal_research_site": build_crystal_site(), "drill_rig": build_drill_rig()}
