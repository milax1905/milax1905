"""
Curated block palettes that match the target world: white snow, pink/lavender sky, lavender trees, blue crystals.
Use them as a starting point; mix 2-3 close shades on big surfaces (see shapes.texturize).
Every block here is vanilla 1.20.1.
"""

# ---- the world itself (for ground / integration)
GROUND = {
    "snow": "minecraft:snow_block",
    "snow_alt": "minecraft:powder_snow",           # careful: entities sink in it - use only decoratively, never on paths
    "ice": "minecraft:packed_ice",
    "ice_light": "minecraft:blue_ice",
    "ice_glass": "minecraft:light_blue_stained_glass",
    "crystal": "minecraft:amethyst_block",
    "crystal_tip": "minecraft:amethyst_cluster",
    "crystal_bud": "minecraft:large_amethyst_bud",
    "rock": "minecraft:calcite",
    "rock_dark": "minecraft:tuff",
}

# ---- gradient mixes: CLOSE shades only (use with shapes.texturize). Never mix white with light_gray: it reads as noise.
MIX_WHITE = [("minecraft:white_concrete", 6), ("minecraft:quartz_block", 2), ("minecraft:smooth_quartz", 1), ("minecraft:calcite", 1)]
MIX_LIGHT_GRAY = [("minecraft:light_gray_concrete", 6), ("minecraft:light_gray_concrete_powder", 2), ("minecraft:polished_andesite", 1), ("minecraft:cyan_terracotta", 0)]
MIX_DARK = [("minecraft:polished_deepslate", 5), ("minecraft:deepslate_tiles", 2), ("minecraft:polished_basalt[axis=y]", 1)]
MIX_BLACK = [("minecraft:polished_blackstone_bricks", 6), ("minecraft:polished_blackstone", 2), ("minecraft:cracked_polished_blackstone_bricks", 1), ("minecraft:deepslate_tiles", 1)]
MIX_SCORCH = [("minecraft:blackstone", 5), ("minecraft:basalt", 2), ("minecraft:coal_block", 1), ("minecraft:polished_basalt", 1)]
MIX_SNOW = [("minecraft:snow_block", 8), ("minecraft:white_concrete_powder", 1)]
MIX_ICE = [("minecraft:packed_ice", 5), ("minecraft:blue_ice", 2), ("minecraft:ice", 1)]

# ---- crashed / derelict human-tech ships (clean white-grey hull, cyan glass, dark underside)
SHIP = {
    "hull": "minecraft:light_gray_concrete",
    "hull_light": "minecraft:white_concrete",
    "hull_alt": "minecraft:quartz_block",
    "hull_smooth": "minecraft:smooth_quartz",
    "hull_dark": "minecraft:polished_deepslate",
    "hull_underside": "minecraft:deepslate_tiles",
    "hull_stairs": "deepslate_tile",              # material for stairs/slabs (bevels)
    "hull_stairs_light": "quartz",                # quartz_stairs / quartz_slab
    "frame": "minecraft:iron_block",
    "frame_dark": "minecraft:polished_blackstone",
    "panel": "minecraft:iron_trapdoor",            # vents, hatches
    "pipe": "minecraft:chain",                     # cables (use axis)
    "pipe_thick": "minecraft:oxidized_copper",     # damaged pipework
    "pipe_new": "minecraft:copper_block",
    "glass": "minecraft:light_blue_stained_glass",
    "glass_dark": "minecraft:tinted_glass",
    "glass_pane": "minecraft:light_blue_stained_glass_pane",
    "light": "minecraft:sea_lantern",
    "light_warm": "minecraft:pearlescent_froglight",
    "light_rod": "minecraft:end_rod",
    "engine_glow": "minecraft:cyan_stained_glass",
    "engine_core": "minecraft:sea_lantern",
    "scorch": "minecraft:blackstone",
    "scorch_alt": "minecraft:basalt",
    "scorch_light": "minecraft:coal_block",
    "burnt": "minecraft:polished_basalt",
    "damage_fill": "minecraft:cobbled_deepslate",  # broken panels
    "smoke": "minecraft:soul_campfire",            # blue smoke rising from wreckage
    "fire": "minecraft:campfire",
    "antenna": "minecraft:lightning_rod",
    "bars": "minecraft:iron_bars",
    "crate": "minecraft:barrel",
    "container": "minecraft:cyan_shulker_box",
}

# ---- abandoned labs (clinical white, quartz, cold light, icy contamination)
LAB = {
    "wall": "minecraft:white_concrete",
    "wall_alt": "minecraft:quartz_bricks",
    "wall_smooth": "minecraft:smooth_quartz",
    "wall_stairs": "quartz",
    "wall_slab": "smooth_quartz",
    "floor": "minecraft:light_gray_concrete",
    "floor_alt": "minecraft:polished_diorite",
    "floor_grate": "minecraft:iron_trapdoor",
    "floor_light": "minecraft:sea_lantern",
    "trim": "minecraft:iron_block",
    "trim_dark": "minecraft:polished_deepslate",
    "glass": "minecraft:glass",
    "glass_tint": "minecraft:light_blue_stained_glass",
    "glass_pane": "minecraft:glass_pane",
    "pod": "minecraft:purpur_pillar",              # cryo pod body (lavender)
    "pod_glass": "minecraft:tinted_glass",
    "pod_light": "minecraft:pearlescent_froglight",
    "machine": "minecraft:observer",
    "machine_alt": "minecraft:dispenser",
    "machine_dark": "minecraft:blast_furnace",
    "console": "minecraft:daylight_detector",
    "console_lamp": "minecraft:redstone_lamp[lit=true]",
    "cable": "minecraft:chain",
    "pipe": "minecraft:polished_basalt",
    "tank": "minecraft:cauldron",
    "tank_glow": "minecraft:cyan_stained_glass",
    "specimen": "minecraft:slime_block",
    "specimen_alt": "minecraft:honey_block",
    "lamp": "minecraft:end_rod",
    "lamp_ceiling": "minecraft:sea_lantern",
    "ice_creep": "minecraft:packed_ice",           # frost creeping in through breaches
    "ice_creep_alt": "minecraft:blue_ice",
    "snow": "minecraft:snow_block",
    "sign": "minecraft:warped_sign",
    "door": "iron",
    "desk": "minecraft:lectern",
    "book": "minecraft:chiseled_bookshelf",
    "shelf": "minecraft:bookshelf",
    "brewing": "minecraft:brewing_stand",
}

# ---- villain tech city: dark, sharp, neon purple/magenta, sculk glow. Menacing but readable.
VILLAIN = {
    "wall": "minecraft:polished_blackstone_bricks",
    "wall_alt": "minecraft:deepslate_tiles",
    "wall_smooth": "minecraft:polished_deepslate",
    "wall_stairs": "polished_blackstone_brick",
    "wall_stairs_alt": "deepslate_tile",
    "wall_slab": "polished_deepslate",
    "core": "minecraft:obsidian",
    "core_glow": "minecraft:crying_obsidian",
    "metal": "minecraft:polished_basalt",
    "metal_light": "minecraft:iron_block",
    "metal_dark": "minecraft:netherite_block",
    "accent": "minecraft:purple_concrete",
    "accent_alt": "minecraft:magenta_concrete",
    "accent_glazed": "minecraft:purple_glazed_terracotta",
    "glass": "minecraft:purple_stained_glass",
    "glass_alt": "minecraft:magenta_stained_glass",
    "glass_dark": "minecraft:tinted_glass",
    "glass_pane": "minecraft:purple_stained_glass_pane",
    "light": "minecraft:pearlescent_froglight",
    "light_purple": "minecraft:amethyst_block",
    "light_rod": "minecraft:end_rod",
    "neon": "minecraft:magenta_stained_glass",     # put a light source behind it
    "sculk": "minecraft:sculk",
    "sculk_glow": "minecraft:sculk_catalyst",
    "sculk_sensor": "minecraft:sculk_sensor",
    "chain": "minecraft:chain",
    "bars": "minecraft:iron_bars",
    "railing": "minecraft:polished_blackstone_brick_wall",
    "pipe": "minecraft:oxidized_copper",
    "pipe_cut": "minecraft:oxidized_cut_copper",
    "banner": "minecraft:purple_banner",
    "banner_wall": "minecraft:purple_wall_banner",
    "spike": "minecraft:pointed_dripstone",
    "smoke": "minecraft:soul_campfire",
    "floor": "minecraft:polished_deepslate",
    "floor_alt": "minecraft:deepslate_tiles",
    "floor_light": "minecraft:sea_lantern",
    "road": "minecraft:polished_basalt",
    "road_line": "minecraft:magenta_concrete",
}

# ---- exploration camps (fabric, wood, warm light, practical gear)
CAMP = {
    "tent": "minecraft:white_wool",
    "tent_alt": "minecraft:light_gray_wool",
    "tent_accent": "minecraft:cyan_wool",
    "tent_orange": "minecraft:orange_wool",        # classic polar expedition orange - use sparingly
    "tent_stairs": "spruce",                       # no wool stairs exist: use spruce/cherry stairs for tent edges
    "pole": "minecraft:spruce_fence",
    "pole_log": "minecraft:stripped_spruce_log",
    "plank": "minecraft:spruce_planks",
    "plank_light": "minecraft:cherry_planks",       # pinkish wood fits the world
    "crate": "minecraft:barrel",
    "chest": "minecraft:chest",
    "fire": "minecraft:campfire",
    "lantern": "minecraft:lantern",
    "lantern_soul": "minecraft:soul_lantern",
    "table": "minecraft:cartography_table",
    "bed": "cyan",                                 # bed colour
    "banner": "minecraft:cyan_banner",
    "flag_pole": "minecraft:iron_bars",
    "antenna": "minecraft:lightning_rod",
    "rope": "minecraft:chain",
    "scaffold": "minecraft:scaffolding",
    "metal": "minecraft:iron_block",
    "metal_light": "minecraft:light_gray_concrete",
    "generator": "minecraft:blast_furnace",
    "radio": "minecraft:observer",
    "solar": "minecraft:daylight_detector",
    "snow": "minecraft:snow_block",
    "trodden_snow": "minecraft:white_concrete_powder",
    "ice": "minecraft:packed_ice",
}

# ---- crystal / alien science (things that glow lavender-blue)
CRYSTAL = {
    "crystal": "minecraft:amethyst_block",
    "budding": "minecraft:budding_amethyst",
    "cluster": "minecraft:amethyst_cluster",
    "bud": "minecraft:medium_amethyst_bud",
    "ice": "minecraft:blue_ice",
    "ice_alt": "minecraft:packed_ice",
    "glass": "minecraft:light_blue_stained_glass",
    "glass_purple": "minecraft:purple_stained_glass",
    "glow": "minecraft:pearlescent_froglight",
    "glow_cold": "minecraft:sea_lantern",
    "spike": "minecraft:pointed_dripstone",
    "alien": "minecraft:purpur_block",
    "alien_pillar": "minecraft:purpur_pillar",
    "alien_stairs": "purpur",
    "alien_dark": "minecraft:end_stone_bricks",
    "bone": "minecraft:bone_block",
}
