"""Crashed escape pod: a small lofted capsule nose-down in a crater, parachute cloth spread on the snow."""
from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, GROUND, MIX_WHITE, MIX_SCORCH
import math


def build():
    W, H, L, G = 34, 16, 28, 4
    s = Schematic(W, H, L, ground=G)
    sh.ground_slab(s, G, GROUND["snow"], depth=5)
    cx, cz = 13, 14
    sh.crater(s, cx, cz, 7, G, SHIP["scorch"], GROUND["snow"], "minecraft:snow_block", depth=2, rim_height=1, seed=9)
    sh.texturize(s, SHIP["scorch"], MIX_SCORCH, seed=3)

    # capsule hull lofted along x, tilted look: nose (west) buried, tail raised
    # sections: (x, cy, cz, ry, rz)
    secs = [(6, 4.0, cz, 1.5, 1.5), (9, 5.0, cz, 3.0, 3.0), (14, 6.5, cz, 3.8, 3.8), (19, 8.0, cz, 3.2, 3.2), (22, 9.0, cz, 1.8, 1.8)]
    hull = sh.loft(s, secs, SHIP["hull"], axis="x")
    # dark heat-shield belly: lower third of the hull in polished deepslate, with a blackstone keel line
    belly = hull.copy()
    ys = __import__("numpy").arange(s.h)[None, :, None]
    belly &= ys <= 5
    sh.fill_mask(s, belly, SHIP["hull_dark"])
    keel = hull & (ys <= 3)
    sh.fill_mask(s, keel, SHIP["scorch"])
    sh.fill_mask(s, sh.loft_mask(s, secs, "x", shrink=1.6), "air")
    # trim line along the widest part of the hull (both sides) in dark blocks
    for x in range(9, 22):
        for zz in (cz - 4, cz + 4):
            if s.get(x, 7, zz) != "minecraft:air":
                s.set(x, 7, zz, SHIP["frame_dark"])
    # keep crater floor under the pod
    # engine ring at the tail
    sh.cylinder(s, 22, 8.5, cz, 2.2, 1, SHIP["frame_dark"], axis="x", hollow=True, thickness=1.2)
    sh.cylinder(s, 23, 8.5, cz, 1.4, 1, SHIP["engine_core"], axis="x")
    s.set(24, 9, cz, st.campfire(soul=True, facing="west"))
    # ribs
    for x in (10, 15, 19):
        m = sh.loft_mask(s, secs, "x", shrink=-0.6) & ~sh.loft_mask(s, secs, "x", shrink=0.4)
        m[:x, :, :] = False
        m[x + 1:, :, :] = False
        sh.fill_mask(s, m, SHIP["frame"])
    # window strip + hatch (top side, blown open)
    sh.box(s, 12, 8, cz - 3, 16, 8, cz - 3, SHIP["glass"])
    sh.box(s, 12, 8, cz + 3, 16, 8, cz + 3, SHIP["glass"])
    sh.box(s, 12, 9, cz - 1, 15, 11, cz + 1, "air")  # hatch opening
    s.set(16, 11, cz, st.trapdoor("iron", "west", "top", open=True))
    # interior: seat, light, chest
    s.set(13, 5, cz, st.stairs("polished_deepslate", "west"))
    s.set(15, 6, cz - 1, SHIP["light_rod"])
    s.add_chest(17, 6, cz + 1, "west", "minecraft:chests/shipwreck_supply")
    # hull texture + bevels on the mid-belly
    s.replace({SHIP["hull"]: SHIP["hull_light"]})
    sh.texturize(s, SHIP["hull_light"], MIX_WHITE, seed=5)
    sh.erode(s, 6, 3, cz - 4, 11, 9, cz + 4, prob=0.5, only=["concrete", "quartz"], seed=8)  # crushed nose
    # thrown-off hatch panel + debris trail heading east (direction of travel was west)
    sh.box(s, 24, G + 1, 6, 26, G + 1, 7, SHIP["hull"])
    s.set(25, G + 2, 6, st.stairs(SHIP["hull_stairs"], "north", "top"))
    sh.scatter(s, 16, 2, 32, 26, [SHIP["damage_fill"], SHIP["frame"], "minecraft:polished_basalt[axis=y]", SHIP["scorch_light"]], 18, seed=4)
    # parachute: white/light-gray wool cloth draped on the snow, lines (chains) to the tail
    for dx in range(0, 12):
        for dz in range(-6, 7):
            x, z = 21 + dx, cz + 9 + dz
            r = (dx / 11.0) ** 2 + (dz / 6.0) ** 2
            if r <= 1.0 and s.inside(x, G + 1, z):
                ang = math.atan2(dz, dx + 0.01)
                s.set(x, G + 1, z, "minecraft:light_gray_wool" if int((ang + math.pi) / (math.pi / 4)) % 2 else "minecraft:white_wool")
    for i in range(1, 6):
        s.set(21, 8 - i + 1, cz + 1 + i, st.log("minecraft:chain", "z"))
    s.set(21, 9, cz, "minecraft:iron_bars")
    # antenna + blinking light on the tail
    s.set(22, 11, cz, st.lightning_rod("up"))
    s.set(22, 10, cz, SHIP["light"])
    # signage: distress
    s.add_sign(17, 7, cz - 3, "minecraft:warped_wall_sign[facing=north]", ["POD 7", "MAYDAY", "ejected T+3s", ""])
    sh.snow_cover(s, y_min=G + 1, prob=0.3, seed=2, skip=["wool"])
    return {"escape_pod": s}
