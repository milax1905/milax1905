"""Escape pod: a conical re-entry capsule that landed hard in the snow. Sunk in its own crater, scorched heat shield,
landing legs out, hatch open, parachute spread downwind, distress beacon blinking. Clean and readable."""
import math

import numpy as np

from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, GROUND, MIX_WHITE, MIX_SCORCH


def build():
    W, H, L, G = 40, 22, 34, 4
    s = Schematic(W, H, L, ground=G)
    cx, cz = 14, 15
    sh.ground_slab(s, G, GROUND["snow"], depth=5)
    sh.crater(s, cx, cz, 8, G, SHIP["scorch"], GROUND["snow"], "minecraft:snow_block", depth=2, rim_height=1, seed=9)
    sh.texturize(s, SHIP["scorch"], MIX_SCORCH, seed=3)

    base = G - 1                      # capsule bottom sits on the crater floor (G-2) + 1
    # --- heat shield (dark, wide) and its bevelled rim
    sh.cylinder(s, cx, base, cz, 5.5, 0, SHIP["hull_dark"], axis="y")
    sh.cylinder(s, cx, base, cz, 4.5, 0, "minecraft:blackstone", axis="y")
    sh.ring_stairs(s, cx, base, cz, 6.3, SHIP["hull_stairs"], half="top")          # rim bevel under the edge
    # --- body: frustum widening from the shield to the shoulder, then the nose cone
    sh.cylinder(s, cx, base + 1, cz, 5.5, 5, SHIP["hull_light"], axis="y", r2=4.6)      # y base+1 .. base+6
    sh.cylinder(s, cx, base + 7, cz, 4.2, 4, SHIP["hull_light"], axis="y", r2=1.6)      # nose cone base+7..base+11
    sh.cylinder(s, cx, base + 6, cz, 4.8, 0, SHIP["hull_dark"], axis="y")                # dark shoulder band
    sh.ring_stairs(s, cx, base + 6, cz, 5.3, SHIP["hull_stairs"], half="top")            # thin lip under the shoulder
    sh.ring_stairs(s, cx, base + 12, cz, 1.8, "quartz", half="bottom")                   # nose tip bevel
    s.set(cx, base + 12, cz, "minecraft:iron_block")
    # lavender accent band + iron ribs on the body
    sh.cylinder(s, cx, base + 3, cz, 5.2, 0, "minecraft:purpur_block", axis="y", hollow=True, thickness=1.2)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        for y in range(base + 1, base + 7):
            r = 5.5 - (y - base - 1) * 0.18
            x, z = round(cx + r * math.cos(a)), round(cz + r * math.sin(a))
            s.set(x, y, z, "minecraft:iron_block")
    # hollow interior + floor
    sh.cylinder(s, cx, base + 2, cz, 3.8, 4, "air", axis="y", r2=3.0)
    sh.cylinder(s, cx, base + 7, cz, 2.6, 2, "air", axis="y", r2=1.0)
    sh.cylinder(s, cx, base + 1, cz, 3.8, 0, "minecraft:light_gray_concrete", axis="y")
    # windows (3 round-ish ports on the north side, tinted)
    for dx in (-2, 0, 2):
        for y in (base + 4,):
            z = cz - 5 + (1 if dx else 0)
            s.set(cx + dx, y, z, SHIP["glass"])
    # hatch on the south side, blown open: opening 2 wide x 3 high + door lying as an open trapdoor + step
    sh.box(s, cx - 1, base + 2, cz + 4, cx, base + 4, cz + 6, "air")
    s.set(cx - 1, base + 2, cz + 6, st.stairs(SHIP["hull_stairs"], "north"))
    s.set(cx, base + 2, cz + 6, st.stairs(SHIP["hull_stairs"], "north"))
    s.set(cx + 1, base + 3, cz + 5, st.trapdoor("iron", "west", "top", open=True))
    s.set(cx - 2, base + 3, cz + 5, st.trapdoor("iron", "east", "top", open=True))
    # interior: 2 seats, console, light, supplies
    s.set(cx - 2, base + 2, cz - 1, st.stairs("polished_deepslate", "east"))
    s.set(cx + 2, base + 2, cz - 1, st.stairs("polished_deepslate", "west"))
    s.set(cx, base + 2, cz - 3, "minecraft:daylight_detector")
    s.set(cx, base + 3, cz - 3, st.redstone_lamp(True))
    s.set(cx, base + 6, cz, SHIP["light"])
    s.add_chest(cx + 2, base + 2, cz + 2, "west", "minecraft:chests/shipwreck_supply")
    s.set(cx - 2, base + 2, cz + 2, "minecraft:barrel[facing=up,open=false]")
    # docking collar + antennas on top
    sh.cylinder(s, cx, base + 11, cz, 1.6, 0, SHIP["frame_dark"], axis="y", hollow=True, thickness=1.0)
    s.set(cx, base + 13, cz, st.lightning_rod("up"))
    s.set(cx, base + 14, cz, st.lightning_rod("up"))
    for dx, dz in ((3, 0), (-3, 0)):
        s.set(cx + dx, base + 9, cz + dz, st.end_rod("up"))
    s.set(cx, base + 8, cz - 3, SHIP["light"])                       # beacon
    s.set(cx, base + 8, cz - 4, "minecraft:red_stained_glass")
    # --- landing legs (3, at 120 degrees) - one buried under a snow drift
    for k in range(3):
        a = math.pi / 2 + k * 2 * math.pi / 3 + 0.35
        p1 = (round(cx + 5.0 * math.cos(a)), base + 2, round(cz + 5.0 * math.sin(a)))
        p2 = (round(cx + 8.5 * math.cos(a)), base - 1, round(cz + 8.5 * math.sin(a)))
        sh.line(s, p1, p2, SHIP["frame_dark"])
        s.set(p2[0], p2[1], p2[2], st.slab("polished_deepslate"))
        sh.sphere(s, p2[0], p2[1] - 1, p2[2], 1.2, "minecraft:blackstone")
    # --- parachute downwind (east), lines from the docking collar
    pc_x, pc_z = cx + 17, cz + 3
    for dx in range(-7, 8):
        for dz in range(-9, 10):
            x, z = pc_x + dx, pc_z + dz
            r = (dx / 7.0) ** 2 + (dz / 9.0) ** 2
            if r <= 1.0 and s.inside(x, G + 1, z):
                sector = int((math.atan2(dz, dx) + math.pi) / (math.pi / 4)) % 8
                blk = "minecraft:white_wool" if sector % 2 == 0 else "minecraft:light_gray_wool"
                if 0.7 < r <= 1.0 and sector % 2 == 0:
                    blk = "minecraft:cyan_wool" if (dx + dz) % 4 == 0 else blk
                s.set(x, G + 1, z, blk)
    # fabric folds: a few slabs on top of the canopy
    for (dx, dz) in ((-3, -4), (1, 2), (3, -1), (-1, 5), (4, 4)):
        s.set(pc_x + dx, G + 2, pc_z + dz, st.slab("smooth_quartz"))
    for i in range(1, 8):                                   # shroud lines: chains from the collar to the canopy
        y = base + 11 - i
        s.set(cx + i, max(G + 1, y), cz + (i // 3), st.log("minecraft:chain", "x"))
    # --- debris: heat-shield fragments and a dropped panel, footprints away from the hatch
    sh.scatter(s, 2, 2, W - 3, L - 3, ["minecraft:blackstone", SHIP["hull_dark"], "minecraft:iron_block",
                                       st.slab("polished_deepslate")], 14, seed=4)
    for i in range(1, 9):
        x, z = cx - 1 + (i % 2), cz + 7 + i
        if s.inside(x, G, z) and s.get(x, G, z) == GROUND["snow"]:
            s.set(x, G, z, "minecraft:white_concrete_powder")
    # texture + weathering
    sh.texturize(s, SHIP["hull_light"], MIX_WHITE, seed=5)
    sh.snow_cover(s, y_min=G + 1, prob=0.2, seed=2, skip=["wool", "glass", "iron", "purpur", "lamp", "quartz", "calcite", "white_concrete"])
    s.add_sign(cx + 2, base + 3, cz + 6, "minecraft:warped_wall_sign[facing=south]", ["CAPSULE 7", "MAYDAY", "2 survivants", "partis vers N"])
    s.set(cx + 6, G + 1, cz - 6, st.campfire(soul=True))       # last fire the survivors lit
    return {"escape_pod": s.cropped(pad=1)}
