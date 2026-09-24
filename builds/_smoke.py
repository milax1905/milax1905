from tools.schem import Schematic
from tools import shapes as sh, states as st

def build():
    s = Schematic(30, 16, 20, ground=3)
    sh.ground_slab(s, 3, "snow_block", depth=4)
    # pod hull lofted along x
    secs = [(3, 6, 10, 1, 1), (8, 6.5, 10, 3, 4), (16, 7, 10, 4, 5), (24, 7.5, 10, 3, 3.5), (27, 8, 10, 1.5, 2)]
    sh.loft(s, secs, "light_gray_concrete", axis="x")
    sh.loft(s, secs, "air", axis="x", fill_mask=sh.loft_mask(s, secs, "x", shrink=1.5))
    # windows
    sh.box(s, 12, 8, 5, 20, 9, 5, "light_blue_stained_glass")
    sh.box(s, 12, 8, 15, 20, 9, 15, "light_blue_stained_glass")
    # stairs ramp
    sh.stair_ramp(s, 10, 4, 3, 3, "north", "deepslate_tile", width=2)
    # fence + panes + wall test
    for x in range(2, 10):
        s.set(x, 4, 2, "spruce_fence")
    for z in range(2, 8):
        s.set(2, 4, z, "polished_blackstone_brick_wall")
    s.set(2, 5, 2, "polished_blackstone_brick_wall")
    for x in range(20, 28):
        s.set(x, 4, 2, "glass_pane")
    s.set(5, 4, 8, st.lantern(True))
    s.set(6, 4, 8, st.end_rod())
    s.set(7, 4, 8, st.campfire(True))
    s.set(8, 4, 8, "amethyst_cluster[facing=up]")
    s.set(9, 4, 8, st.slab("deepslate_tile", "top"))
    s.set(9, 4, 9, st.slab("deepslate_tile"))
    s.set(9, 4, 10, st.trapdoor("iron", "north", open=True))
    sh.snow_cover(s, y_min=4, prob=0.8)
    sh.scatter(s, 0, 0, 29, 19, ["cobbled_deepslate", "polished_basalt[axis=y]"], 8)
    return {"_smoke": s}
