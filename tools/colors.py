"""Approximate average colours of vanilla blocks for the preview renderer (RGB 0-255)."""
from __future__ import annotations

from functools import lru_cache
from typing import Tuple

_C = {
    # stone-ish
    "stone": (125, 125, 125), "cobblestone": (120, 120, 120), "andesite": (136, 136, 136), "polished_andesite": (132, 135, 134),
    "diorite": (188, 188, 190), "polished_diorite": (192, 193, 194), "granite": (149, 103, 85), "polished_granite": (154, 107, 89),
    "deepslate": (80, 80, 82), "cobbled_deepslate": (77, 77, 80), "polished_deepslate": (72, 72, 75), "deepslate_brick": (70, 70, 72),
    "deepslate_tile": (54, 54, 57), "chiseled_deepslate": (60, 60, 62), "cracked_deepslate_tile": (52, 52, 55),
    "cracked_deepslate_brick": (66, 66, 68), "reinforced_deepslate": (76, 82, 74), "tuff": (108, 109, 102), "calcite": (223, 224, 220),
    "dripstone_block": (134, 107, 92), "smooth_stone": (159, 159, 159), "stone_brick": (122, 122, 122), "mossy_stone_brick": (115, 121, 105),
    "cracked_stone_brick": (118, 117, 117), "chiseled_stone_brick": (120, 120, 120), "blackstone": (42, 36, 41), "polished_blackstone": (53, 48, 56),
    "polished_blackstone_brick": (48, 42, 49), "cracked_polished_blackstone_brick": (44, 38, 45), "chiseled_polished_blackstone": (54, 49, 57),
    "gilded_blackstone": (55, 42, 38), "basalt": (80, 81, 86), "polished_basalt": (99, 99, 103), "smooth_basalt": (72, 72, 78),
    "obsidian": (15, 10, 24), "crying_obsidian": (32, 10, 60), "end_stone": (219, 222, 158), "end_stone_brick": (218, 224, 162),
    "purpur_block": (169, 125, 169), "purpur_pillar": (171, 129, 171), "netherrack": (97, 38, 38), "nether_brick": (44, 21, 26),
    "red_nether_brick": (70, 7, 9), "quartz_block": (236, 230, 223), "smooth_quartz": (236, 230, 223), "quartz_pillar": (235, 229, 222),
    "chiseled_quartz_block": (232, 226, 218), "quartz_brick": (234, 228, 221), "prismarine": (99, 156, 151), "prismarine_brick": (99, 171, 158),
    "dark_prismarine": (51, 91, 75), "sea_lantern": (172, 199, 190), "sandstone": (216, 203, 155), "smooth_sandstone": (223, 214, 170),
    "cut_sandstone": (217, 206, 160), "red_sandstone": (186, 99, 29), "brick": (150, 97, 83), "mud_brick": (137, 104, 79), "packed_mud": (142, 106, 79),
    "bedrock": (85, 85, 85), "gravel": (131, 127, 126), "sand": (219, 207, 163), "clay": (160, 166, 179), "dirt": (134, 96, 67),
    "coarse_dirt": (119, 85, 59), "grass_block": (106, 152, 80), "mycelium": (111, 99, 105), "podzol": (91, 63, 24),
    "coal_block": (16, 16, 16), "iron_block": (196, 198, 202), "gold_block": (247, 205, 57), "diamond_block": (98, 219, 208),
    "emerald_block": (42, 203, 87), "lapis_block": (30, 67, 140), "redstone_block": (171, 27, 9), "netherite_block": (66, 61, 63),
    "copper_block": (192, 107, 79), "exposed_copper": (161, 125, 103), "weathered_copper": (108, 153, 110), "oxidized_copper": (82, 162, 132),
    "cut_copper": (191, 106, 80), "exposed_cut_copper": (154, 121, 101), "weathered_cut_copper": (109, 145, 107), "oxidized_cut_copper": (79, 153, 126),
    "raw_iron_block": (166, 141, 117), "raw_copper_block": (154, 105, 78), "amethyst_block": (133, 97, 191), "budding_amethyst": (132, 96, 186),
    "amethyst_cluster": (163, 126, 220), "large_amethyst_bud": (160, 122, 215), "medium_amethyst_bud": (156, 118, 210), "small_amethyst_bud": (150, 112, 205),
    "ancient_debris": (94, 65, 58), "magma_block": (142, 63, 31), "glowstone": (171, 131, 84), "shroomlight": (240, 146, 70),
    "bone_block": (229, 225, 207), "hay_block": (166, 139, 12), "sponge": (195, 192, 74), "honeycomb_block": (229, 148, 30),
    "honey_block": (251, 185, 52), "slime_block": (111, 192, 91), "sculk": (12, 29, 36), "sculk_catalyst": (15, 35, 42), "sculk_sensor": (7, 70, 84),
    "sculk_shrieker": (30, 60, 65), "sculk_vein": (10, 50, 60), "moss_block": (89, 110, 45), "moss_carpet": (89, 110, 45),
    "ice": (145, 183, 253), "packed_ice": (141, 180, 250), "blue_ice": (116, 167, 253), "snow_block": (249, 254, 254), "snow": (249, 254, 254),
    "powder_snow": (248, 253, 253), "frosted_ice": (140, 180, 250), "glass": (200, 230, 240), "tinted_glass": (40, 35, 45),
    "water": (63, 118, 228), "lava": (207, 85, 16), "fire": (230, 140, 40), "soul_fire": (60, 140, 210), "soul_sand": (81, 62, 50), "soul_soil": (75, 57, 46),
    "nether_wart_block": (114, 2, 2), "warped_wart_block": (22, 119, 121), "warped_nylium": (43, 114, 101), "crimson_nylium": (130, 31, 31),
    "target": (226, 170, 158), "bookshelf": (117, 94, 57), "chiseled_bookshelf": (130, 105, 66), "crafting_table": (120, 82, 50),
    "furnace": (110, 110, 110), "blast_furnace": (80, 80, 82), "smoker": (95, 90, 84), "barrel": (110, 84, 51), "chest": (155, 110, 45),
    "trapped_chest": (155, 110, 45), "ender_chest": (35, 55, 55), "observer": (90, 90, 90), "dispenser": (110, 110, 110), "dropper": (110, 110, 110),
    "piston": (110, 100, 90), "sticky_piston": (110, 110, 90), "piston_head": (150, 120, 80), "hopper": (70, 70, 70), "cauldron": (60, 60, 60),
    "water_cauldron": (70, 90, 130), "powder_snow_cauldron": (150, 160, 170), "anvil": (65, 65, 65), "chipped_anvil": (65, 65, 65), "damaged_anvil": (65, 65, 65),
    "grindstone": (120, 120, 120), "stonecutter": (110, 110, 110), "lectern": (160, 120, 70), "loom": (150, 110, 70), "smithing_table": (60, 60, 70),
    "fletching_table": (190, 160, 110), "cartography_table": (120, 90, 60), "enchanting_table": (60, 40, 70), "brewing_stand": (110, 100, 90),
    "beacon": (120, 200, 210), "conduit": (150, 140, 120), "bell": (230, 180, 60), "lantern": (250, 200, 100), "soul_lantern": (70, 150, 210),
    "torch": (255, 210, 120), "wall_torch": (255, 210, 120), "soul_torch": (70, 150, 210), "soul_wall_torch": (70, 150, 210),
    "redstone_torch": (255, 90, 60), "redstone_wall_torch": (255, 90, 60), "end_rod": (240, 240, 235), "lightning_rod": (200, 120, 90),
    "chain": (60, 62, 70), "iron_bars": (120, 122, 128), "ladder": (150, 115, 70), "scaffolding": (200, 170, 100), "campfire": (250, 160, 50),
    "soul_campfire": (60, 130, 200), "cake": (230, 220, 210), "redstone_lamp": (255, 200, 120), "daylight_detector": (140, 120, 90),
    "note_block": (100, 70, 45), "jukebox": (100, 70, 45), "tnt": (200, 60, 50), "spawner": (30, 40, 50), "structure_block": (90, 70, 100),
    "barrier": (255, 0, 0), "structure_void": (200, 150, 250), "light": (255, 255, 200), "flower_pot": (120, 70, 50), "decorated_pot": (150, 100, 70),
    "cobweb": (230, 230, 230), "dead_bush": (120, 90, 40), "short_grass": (90, 160, 70), "grass": (90, 160, 70), "fern": (90, 150, 70), "tall_grass": (90, 160, 70),
    "large_fern": (90, 150, 70), "cactus": (90, 130, 50), "sugar_cane": (140, 190, 100), "bamboo": (110, 150, 50), "bamboo_block": (140, 150, 60), "stripped_bamboo_block": (190, 170, 80),
    "bamboo_mosaic": (190, 170, 90), "lily_pad": (40, 110, 40), "vine": (60, 110, 40), "glow_lichen": (110, 150, 140), "hanging_roots": (150, 110, 80),
    "pointed_dripstone": (134, 107, 92), "big_dripleaf": (90, 140, 60), "small_dripleaf": (90, 140, 60), "spore_blossom": (220, 120, 150),
    "azalea": (100, 140, 60), "flowering_azalea": (130, 130, 90), "pink_petals": (240, 170, 200), "cherry_leaves": (240, 170, 200),
    "cherry_log": (60, 40, 40), "stripped_cherry_log": (220, 170, 160), "cherry_wood": (60, 40, 40), "stripped_cherry_wood": (220, 170, 160),
    "cherry_planks": (230, 180, 170), "cherry_sapling": (220, 160, 190), "dragon_egg": (20, 10, 30), "end_portal_frame": (90, 110, 90),
    "respawn_anchor": (40, 20, 60), "lodestone": (120, 120, 125), "chorus_plant": (90, 60, 90), "chorus_flower": (150, 110, 150),
    "sea_pickle": (90, 100, 50), "kelp": (60, 100, 50), "seagrass": (60, 120, 50), "dried_kelp_block": (40, 50, 30), "melon": (110, 160, 50),
    "pumpkin": (200, 120, 30), "carved_pumpkin": (200, 120, 30), "jack_o_lantern": (220, 140, 40), "mushroom_stem": (200, 190, 170),
    "brown_mushroom_block": (150, 110, 80), "red_mushroom_block": (200, 40, 40), "brown_mushroom": (150, 110, 80), "red_mushroom": (200, 40, 40),
    "crimson_fungus": (160, 40, 40), "warped_fungus": (40, 140, 130), "crimson_roots": (150, 30, 40), "warped_roots": (30, 130, 120),
    "nether_sprouts": (30, 130, 120), "weeping_vines": (140, 30, 30), "twisting_vines": (30, 140, 130), "crimson_stem": (100, 40, 60),
    "warped_stem": (50, 100, 100), "stripped_crimson_stem": (140, 60, 90), "stripped_warped_stem": (60, 140, 130), "crimson_planks": (110, 50, 75),
    "warped_planks": (45, 105, 105), "crimson_hyphae": (100, 40, 60), "warped_hyphae": (50, 100, 100), "ochre_froglight": (250, 240, 200),
    "verdant_froglight": (220, 245, 220), "pearlescent_froglight": (245, 230, 240), "mangrove_roots": (90, 70, 50), "muddy_mangrove_roots": (80, 65, 55),
    "mud": (60, 57, 60), "rooted_dirt": (140, 100, 70), "dirt_path": (150, 120, 70), "farmland": (110, 75, 45), "wheat": (200, 170, 70),
    "nether_wart": (130, 30, 30), "suspicious_sand": (215, 200, 160), "suspicious_gravel": (125, 120, 118), "tripwire_hook": (120, 110, 100),
    "lever": (110, 100, 90), "rail": (140, 120, 100), "powered_rail": (150, 120, 90), "detector_rail": (130, 120, 100), "activator_rail": (140, 110, 100),
    "repeater": (150, 140, 140), "comparator": (150, 140, 140), "redstone_wire": (200, 20, 20), "skeleton_skull": (220, 220, 210),
    "wither_skeleton_skull": (40, 40, 40), "zombie_head": (70, 120, 60), "creeper_head": (80, 160, 70), "player_head": (150, 120, 90),
    "dragon_head": (30, 30, 30), "piglin_head": (220, 150, 140), "sniffer_egg": (150, 60, 40), "torchflower": (230, 150, 40), "pitcher_plant": (100, 130, 180),
    "wither_rose": (40, 40, 40), "cornflower": (80, 110, 200), "lily_of_the_valley": (230, 240, 230), "azure_bluet": (220, 220, 230),
    "oxeye_daisy": (230, 230, 220), "allium": (200, 130, 220), "blue_orchid": (60, 160, 220), "poppy": (220, 40, 40), "dandelion": (240, 220, 60),
    "red_tulip": (220, 50, 50), "orange_tulip": (230, 140, 60), "white_tulip": (240, 240, 240), "pink_tulip": (240, 170, 200),
    "sunflower": (240, 210, 60), "lilac": (200, 150, 210), "rose_bush": (220, 50, 50), "peony": (230, 180, 210), "sweet_berry_bush": (80, 120, 60),
    "cave_vines": (80, 120, 50), "nether_brick_fence": (44, 21, 26), "infested_stone": (125, 125, 125), "cracked_nether_brick": (40, 19, 24),
    "chiseled_nether_brick": (44, 21, 26), "polished_blackstone_button": (53, 48, 56), "polished_blackstone_pressure_plate": (53, 48, 56),
    "stone_button": (125, 125, 125), "stone_pressure_plate": (125, 125, 125), "light_weighted_pressure_plate": (247, 205, 57),
    "heavy_weighted_pressure_plate": (220, 220, 220), "iron_trapdoor": (170, 172, 178), "iron_door": (180, 182, 188),
    "petrified_oak_slab": (160, 130, 80), "cut_red_sandstone": (186, 99, 29), "smooth_red_sandstone": (186, 99, 29), "chiseled_red_sandstone": (186, 99, 29),
    "chiseled_sandstone": (216, 203, 155), "end_gateway": (10, 10, 20), "end_portal": (10, 10, 20), "nether_portal": (120, 40, 200),
    "bubble_column": (63, 118, 228), "kelp_plant": (60, 100, 50), "tall_seagrass": (60, 120, 50), "frogspawn": (150, 140, 120),
    "mangrove_propagule": (90, 140, 60), "shulker_box": (140, 100, 140), "composter": (110, 80, 50), "bee_nest": (200, 160, 80), "beehive": (180, 140, 80),
    "candle": (230, 220, 200), "moving_piston": (110, 100, 90), "command_block": (170, 120, 90), "chain_command_block": (110, 160, 140),
    "repeating_command_block": (100, 80, 160), "jigsaw": (80, 70, 90), "cave_air": (0, 0, 0), "void_air": (0, 0, 0), "air": (0, 0, 0),
    "trapdoor": (150, 115, 70), "tube_coral_block": (50, 80, 200), "brain_coral_block": (200, 80, 160), "bubble_coral_block": (160, 40, 160),
    "fire_coral_block": (160, 40, 60), "horn_coral_block": (200, 180, 60), "dead_tube_coral_block": (130, 125, 120), "dead_brain_coral_block": (130, 125, 120),
    "dead_bubble_coral_block": (130, 125, 120), "dead_fire_coral_block": (130, 125, 120), "dead_horn_coral_block": (130, 125, 120),
    "wet_sponge": (170, 170, 70), "coal_ore": (110, 110, 110), "iron_ore": (135, 130, 125), "copper_ore": (125, 125, 115), "gold_ore": (140, 135, 110),
    "diamond_ore": (125, 140, 140), "emerald_ore": (120, 140, 125), "lapis_ore": (110, 120, 140), "redstone_ore": (140, 110, 110),
    "deepslate_coal_ore": (75, 75, 77), "deepslate_iron_ore": (95, 90, 85), "deepslate_copper_ore": (90, 92, 85), "deepslate_gold_ore": (100, 95, 75),
    "deepslate_diamond_ore": (85, 100, 100), "deepslate_emerald_ore": (80, 100, 85), "deepslate_lapis_ore": (75, 82, 100), "deepslate_redstone_ore": (100, 75, 75),
    "nether_gold_ore": (110, 60, 50), "nether_quartz_ore": (110, 70, 65), "budding": (132, 96, 186), "calibrated_sculk_sensor": (10, 75, 90),
    "torchflower_crop": (100, 140, 60), "pitcher_crop": (100, 130, 120), "carrots": (100, 150, 60), "potatoes": (100, 150, 60), "beetroots": (100, 130, 60),
    "attached_melon_stem": (100, 130, 60), "attached_pumpkin_stem": (100, 130, 60), "melon_stem": (100, 130, 60), "pumpkin_stem": (100, 130, 60),
    "cocoa": (150, 100, 50), "chorus": (90, 60, 90), "moss": (89, 110, 45), "tripwire": (200, 200, 200), "sculk_sensor_": (7, 70, 84),
    "bamboo_sapling": (110, 150, 50), "oak_sapling": (80, 120, 50), "spruce_sapling": (50, 80, 40), "birch_sapling": (110, 150, 70),
    "jungle_sapling": (60, 110, 40), "acacia_sapling": (100, 130, 50), "dark_oak_sapling": (50, 80, 40), "candle_cake": (230, 220, 210),
}
_COLOR_NAMES = {
    "white": (233, 236, 236), "orange": (240, 118, 19), "magenta": (189, 68, 179), "light_blue": (58, 175, 217), "yellow": (248, 197, 39),
    "lime": (112, 185, 25), "pink": (237, 141, 172), "gray": (62, 68, 71), "light_gray": (142, 142, 134), "cyan": (21, 137, 145),
    "purple": (121, 42, 172), "blue": (53, 57, 157), "brown": (114, 71, 40), "green": (84, 109, 27), "red": (161, 39, 34), "black": (20, 21, 25),
}
_TERRACOTTA = {
    "white": (209, 178, 161), "orange": (161, 83, 37), "magenta": (149, 88, 108), "light_blue": (113, 108, 137), "yellow": (186, 133, 35),
    "lime": (103, 117, 52), "pink": (161, 78, 78), "gray": (57, 42, 35), "light_gray": (135, 106, 97), "cyan": (86, 91, 91),
    "purple": (118, 70, 86), "blue": (74, 59, 91), "brown": (77, 51, 35), "green": (76, 83, 42), "red": (143, 61, 46), "black": (37, 22, 16),
    "terracotta": (152, 94, 67),
}
_WOOD = {
    "oak": ((162, 130, 78), (109, 85, 50)), "spruce": ((114, 84, 48), (58, 37, 16)), "birch": ((192, 175, 121), (215, 210, 200)),
    "jungle": ((160, 115, 80), (85, 67, 25)), "acacia": ((168, 90, 50), (103, 96, 86)), "dark_oak": ((66, 43, 20), (50, 35, 20)),
    "mangrove": ((117, 54, 48), (80, 60, 50)), "cherry": ((230, 180, 170), (60, 40, 40)), "bamboo": ((205, 185, 90), (140, 150, 60)),
    "crimson": ((110, 50, 75), (100, 40, 60)), "warped": ((45, 105, 105), (50, 100, 100)),
}
_LEAVES = {"oak": (60, 120, 40), "spruce": (50, 90, 50), "birch": (90, 140, 60), "jungle": (50, 120, 40), "acacia": (80, 130, 40),
           "dark_oak": (50, 100, 40), "mangrove": (60, 110, 40), "azalea": (90, 130, 60), "flowering_azalea": (110, 130, 90), "cherry": (240, 170, 200)}


@lru_cache(maxsize=4096)
def block_color(block: str) -> Tuple[int, int, int]:
    """Best-effort colour for a block state string."""
    name = block.split("[")[0]
    short = name.split(":", 1)[-1]
    if short in _C:
        return _C[short]
    if short in ("glass_pane", "tinted_glass_pane"):
        return _C["glass"]
    # coloured families
    for c in sorted(_COLOR_NAMES, key=len, reverse=True):
        if short.startswith(c + "_"):
            rest = short[len(c) + 1:]
            base = _COLOR_NAMES[c]
            if rest in ("terracotta", "glazed_terracotta"):
                return _TERRACOTTA[c]
            if rest in ("stained_glass", "stained_glass_pane"):
                return tuple(int(v * 0.8 + 50) for v in base)
            if rest == "concrete_powder":
                return tuple(int(v * 0.9 + 20) for v in base)
            if rest in ("candle", "candle_cake"):
                return tuple(int(v * 0.7 + 60) for v in base)
            return base  # wool, concrete, carpet, bed, banner, shulker_box, ...
    if short == "terracotta":
        return _TERRACOTTA["terracotta"]
    # wood families
    for w in sorted(_WOOD, key=len, reverse=True):
        if short.startswith(w + "_") or short.startswith("stripped_" + w + "_"):
            planks, bark = _WOOD[w]
            if short.endswith("_leaves"):
                return _LEAVES.get(w, (60, 120, 40))
            if short.startswith("stripped_"):
                return tuple(int(v * 0.95 + 10) for v in planks)
            if short.endswith("_log") or short.endswith("_wood") or short.endswith("_stem") or short.endswith("_hyphae"):
                return bark
            return planks
    if short.endswith("_leaves"):
        for k, v in _LEAVES.items():
            if short.startswith(k):
                return v
    # derived materials (stairs / slab / wall / bricks / tiles / pillar / smooth / cut ...)
    for suf in ("_stairs", "_slab", "_wall", "_fence_gate", "_fence", "_button", "_pressure_plate", "_trapdoor", "_door",
                "_wall_hanging_sign", "_hanging_sign", "_wall_sign", "_sign", "_tiles", "_bricks", "_block", "s"):
        if short.endswith(suf):
            base = short[: -len(suf)]
            for cand in (base, base + "_block", base + "s", base + "_bricks", base + "_tiles"):
                if cand in _C:
                    return _C[cand]
    for pre in ("waxed_", "stripped_", "cracked_", "chiseled_", "mossy_", "smooth_", "cut_", "polished_", "infested_", "dead_"):
        if short.startswith(pre):
            return block_color(short[len(pre):])
    if short.endswith("s") and short[:-1] in _C:
        return _C[short[:-1]]
    return (255, 0, 255)  # magenta = unknown (shows up clearly in previews)


def is_transparent(block: str) -> bool:
    short = block.split("[")[0].split(":", 1)[-1]
    return "glass" in short or short in ("ice", "frosted_ice", "water", "barrier", "light", "structure_void", "honey_block", "slime_block")


def is_emissive(block: str) -> bool:
    short = block.split("[")[0].split(":", 1)[-1]
    return any(k in short for k in ("lantern", "torch", "glowstone", "sea_lantern", "end_rod", "shroomlight", "campfire", "froglight",
                                    "lamp", "magma", "fire", "lava", "beacon", "crying_obsidian", "amethyst_cluster", "candle",
                                    "jack_o", "conduit", "respawn_anchor", "sculk_catalyst", "glow_lichen"))
