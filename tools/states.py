"""
Block-state helpers, rotation/mirroring of states, and a validator for vanilla 1.20.1 block ids
and block-state properties. Builders should use these helpers instead of hand-writing states.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

# ----------------------------------------------------------------------------- parsing
_STATE_RE = re.compile(r"^([a-z0-9_:.\-]+)(?:\[(.*)\])?$")


def parse(block: str) -> Tuple[str, Dict[str, str]]:
    m = _STATE_RE.match(block.strip())
    if not m:
        raise ValueError(f"bad block string: {block!r}")
    name, props = m.group(1), m.group(2)
    if ":" not in name:
        name = "minecraft:" + name
    d: Dict[str, str] = {}
    if props:
        for kv in props.split(","):
            if not kv:
                continue
            k, v = kv.split("=", 1)
            d[k.strip()] = v.strip()
    return name, d


def unparse(name: str, props: Dict[str, str]) -> str:
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={props[k]}" for k in sorted(props)) + "]"


def with_props(block: str, **props) -> str:
    name, d = parse(block)
    d.update({k: str(v).lower() for k, v in props.items()})
    return unparse(name, d)


# ----------------------------------------------------------------------------- helpers
def stairs(material: str, facing: str, half: str = "bottom", shape: str = "straight") -> str:
    """material e.g. 'deepslate_tile' -> minecraft:deepslate_tile_stairs[...]"""
    name = material if material.endswith("_stairs") else material + "_stairs"
    return with_props(name, facing=facing, half=half, shape=shape)


def slab(material: str, type: str = "bottom") -> str:
    name = material if material.endswith("_slab") else material + "_slab"
    return with_props(name, type=type)


def log(material: str, axis: str = "y") -> str:
    """Any pillar block: oak_log, stripped_oak_log, quartz_pillar, purpur_pillar, basalt, bone_block, deepslate, hay_block, ..."""
    return with_props(material, axis=axis)


def trapdoor(material: str, facing: str, half: str = "bottom", open: bool = False) -> str:
    name = material if material.endswith("_trapdoor") else material + "_trapdoor"
    return with_props(name, facing=facing, half=half, open=open)


def door(material: str, facing: str, half: str = "lower", hinge: str = "left", open: bool = False) -> str:
    name = material if material.endswith("_door") else material + "_door"
    return with_props(name, facing=facing, half=half, hinge=hinge, open=open)


def fence_gate(material: str, facing: str, open: bool = False) -> str:
    name = material if material.endswith("_fence_gate") else material + "_fence_gate"
    return with_props(name, facing=facing, open=open)


def button(material: str, face: str = "wall", facing: str = "north") -> str:
    name = material if material.endswith("_button") else material + "_button"
    return with_props(name, face=face, facing=facing)


def lantern(soul: bool = False, hanging: bool = False) -> str:
    return with_props("soul_lantern" if soul else "lantern", hanging=hanging)


def chain(axis: str = "y") -> str:
    return with_props("chain", axis=axis)


def end_rod(facing: str = "up") -> str:
    return with_props("end_rod", facing=facing)


def lightning_rod(facing: str = "up") -> str:
    return with_props("lightning_rod", facing=facing)


def campfire(soul: bool = False, lit: bool = True, facing: str = "north") -> str:
    return with_props("soul_campfire" if soul else "campfire", lit=lit, facing=facing)


def wall_torch(facing: str, soul: bool = False) -> str:
    return with_props("soul_wall_torch" if soul else "wall_torch", facing=facing)


def torch(soul: bool = False) -> str:
    return "minecraft:soul_torch" if soul else "minecraft:torch"


def facing_block(name: str, facing: str) -> str:
    """observer, dispenser, dropper, piston, hopper, barrel, furnace, lectern, anvil, stonecutter,
    loom, ladder, chest, ender_chest, amethyst_cluster, wall_sign, wall_banner, ..."""
    return with_props(name, facing=facing)


def snow_layer(layers: int = 1) -> str:
    return with_props("snow", layers=max(1, min(8, layers)))


def candle(color: Optional[str] = None, count: int = 1, lit: bool = True) -> str:
    return with_props((color + "_candle") if color else "candle", candles=max(1, min(4, count)), lit=lit)


def glass_pane(color: Optional[str] = None, **conn) -> str:
    return with_props((color + "_stained_glass_pane") if color else "glass_pane", **conn)


def banner(color: str, rotation: int = 0) -> str:
    return with_props(color + "_banner", rotation=rotation % 16)


def wall_banner(color: str, facing: str) -> str:
    return with_props(color + "_wall_banner", facing=facing)


def pointed_dripstone(direction: str = "up", thickness: str = "tip") -> str:
    return with_props("pointed_dripstone", vertical_direction=direction, thickness=thickness)


def redstone_lamp(lit: bool = True) -> str:
    return with_props("redstone_lamp", lit=lit)


def bed(color: str, facing: str, part: str) -> str:
    return with_props(color + "_bed", facing=facing, part=part)


# ----------------------------------------------------------------------------- rotation / mirror
_FACING_CW = {"north": "east", "east": "south", "south": "west", "west": "north", "up": "up", "down": "down"}
_AXIS_ROT = {"x": "z", "z": "x", "y": "y"}
_DIRS = ["north", "east", "south", "west"]
_RAIL_ROT = {"north_south": "east_west", "east_west": "north_south",
             "ascending_north": "ascending_east", "ascending_east": "ascending_south",
             "ascending_south": "ascending_west", "ascending_west": "ascending_north",
             "south_east": "south_west", "south_west": "north_west", "north_west": "north_east", "north_east": "south_east"}


def rotate_state(block: str, k: int) -> str:
    """Rotate a block state k*90 degrees clockwise seen from above."""
    k %= 4
    if k == 0 or "[" not in block:
        return block
    name, p = parse(block)
    for _ in range(k):
        if "facing" in p:
            p["facing"] = _FACING_CW.get(p["facing"], p["facing"])
        if "axis" in p:
            p["axis"] = _AXIS_ROT.get(p["axis"], p["axis"])
        if "rotation" in p:
            p["rotation"] = str((int(p["rotation"]) + 4) % 16)
        if "shape" in p and p["shape"] in _RAIL_ROT:
            p["shape"] = _RAIL_ROT[p["shape"]]
        if all(d in p for d in _DIRS):  # connection properties (fence/pane/wall/glow_lichen/vine)
            n, e, s, w = p["north"], p["east"], p["south"], p["west"]
            p["north"], p["east"], p["south"], p["west"] = w, n, e, s
    return unparse(name, p)


_MIRROR_X = {"east": "west", "west": "east"}
_MIRROR_Z = {"north": "south", "south": "north"}
_SHAPE_MIRROR = {"inner_left": "inner_right", "inner_right": "inner_left", "outer_left": "outer_right", "outer_right": "outer_left"}


def mirror_state(block: str, axis: str = "x") -> str:
    """Mirror a state across the x axis (east<->west) or z axis (north<->south)."""
    if "[" not in block:
        return block
    name, p = parse(block)
    table = _MIRROR_X if axis == "x" else _MIRROR_Z
    if "facing" in p:
        p["facing"] = table.get(p["facing"], p["facing"])
    if "shape" in p and p["shape"] in _SHAPE_MIRROR:
        p["shape"] = _SHAPE_MIRROR[p["shape"]]
    if "hinge" in p:
        p["hinge"] = "right" if p["hinge"] == "left" else "left"
    if "rotation" in p:
        r = int(p["rotation"])
        p["rotation"] = str((16 - r) % 16 if axis == "x" else (8 - r) % 16)
    if all(d in p for d in _DIRS):
        if axis == "x":
            p["east"], p["west"] = p["west"], p["east"]
        else:
            p["north"], p["south"] = p["south"], p["north"]
    return unparse(name, p)


# ----------------------------------------------------------------------------- valid block list (1.20.1)
COLORS = ["white", "orange", "magenta", "light_blue", "yellow", "lime", "pink", "gray", "light_gray",
          "cyan", "purple", "blue", "brown", "green", "red", "black"]
WOODS = ["oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "bamboo", "crimson", "warped"]
_STONE_SETS = [  # (base, has_stairs, has_slab, has_wall)
    "stone", "cobblestone", "mossy_cobblestone", "stone_brick", "mossy_stone_brick", "granite", "polished_granite",
    "diorite", "polished_diorite", "andesite", "polished_andesite", "sandstone", "smooth_sandstone", "cut_sandstone",
    "red_sandstone", "smooth_red_sandstone", "cut_red_sandstone", "brick", "prismarine", "prismarine_brick",
    "dark_prismarine", "nether_brick", "red_nether_brick", "quartz", "smooth_quartz", "purpur", "end_stone_brick",
    "blackstone", "polished_blackstone", "polished_blackstone_brick", "cobbled_deepslate", "polished_deepslate",
    "deepslate_brick", "deepslate_tile", "mud_brick", "smooth_stone", "cut_copper", "exposed_cut_copper",
    "weathered_cut_copper", "oxidized_cut_copper", "waxed_cut_copper", "waxed_exposed_cut_copper",
    "waxed_weathered_cut_copper", "waxed_oxidized_cut_copper",
]
_NO_WALL = {"stone", "smooth_sandstone", "cut_sandstone", "smooth_red_sandstone", "cut_red_sandstone",
            "dark_prismarine", "prismarine_brick", "quartz", "smooth_quartz", "purpur", "polished_andesite",
            "polished_granite", "polished_diorite", "smooth_stone", "cut_copper", "exposed_cut_copper",
            "weathered_cut_copper", "oxidized_cut_copper", "waxed_cut_copper", "waxed_exposed_cut_copper",
            "waxed_weathered_cut_copper", "waxed_oxidized_cut_copper"}
_NO_STAIRS = {"smooth_stone"}
_MISC = """
air cave_air void_air stone granite polished_granite diorite polished_diorite andesite polished_andesite deepslate
cobbled_deepslate polished_deepslate calcite tuff dripstone_block grass_block dirt coarse_dirt podzol rooted_dirt mud
crimson_nylium warped_nylium cobblestone oak_planks bedrock sand red_sand gravel coal_ore deepslate_coal_ore iron_ore
deepslate_iron_ore copper_ore deepslate_copper_ore gold_ore deepslate_gold_ore redstone_ore deepslate_redstone_ore
emerald_ore deepslate_emerald_ore lapis_ore deepslate_lapis_ore diamond_ore deepslate_diamond_ore nether_gold_ore
nether_quartz_ore ancient_debris coal_block raw_iron_block raw_copper_block raw_gold_block amethyst_block
budding_amethyst iron_block copper_block gold_block diamond_block netherite_block exposed_copper weathered_copper
oxidized_copper cut_copper exposed_cut_copper weathered_cut_copper oxidized_cut_copper waxed_copper_block
waxed_exposed_copper waxed_weathered_copper waxed_oxidized_copper waxed_cut_copper waxed_exposed_cut_copper
waxed_weathered_cut_copper waxed_oxidized_cut_copper mangrove_roots muddy_mangrove_roots sponge wet_sponge glass
tinted_glass lapis_block sandstone chiseled_sandstone cut_sandstone cobweb short_grass grass fern dead_bush seagrass
tall_seagrass sea_pickle azalea flowering_azalea dandelion poppy blue_orchid allium azure_bluet red_tulip orange_tulip
white_tulip pink_tulip oxeye_daisy cornflower lily_of_the_valley wither_rose torchflower spore_blossom brown_mushroom
red_mushroom crimson_fungus warped_fungus crimson_roots warped_roots nether_sprouts weeping_vines twisting_vines
sugar_cane kelp kelp_plant moss_carpet pink_petals moss_block hanging_roots big_dripleaf small_dripleaf bamboo
bamboo_sapling bricks bookshelf chiseled_bookshelf mossy_cobblestone obsidian torch wall_torch fire soul_fire spawner
chest redstone_wire crafting_table furnace ladder rail powered_rail detector_rail activator_rail lever
stone_pressure_plate polished_blackstone_pressure_plate light_weighted_pressure_plate heavy_weighted_pressure_plate
redstone_torch redstone_wall_torch stone_button snow ice snow_block cactus clay jukebox pumpkin carved_pumpkin
jack_o_lantern netherrack soul_sand soul_soil basalt polished_basalt smooth_basalt soul_torch soul_wall_torch
glowstone nether_portal repeater comparator stone_bricks mossy_stone_bricks cracked_stone_bricks chiseled_stone_bricks
packed_mud mud_bricks infested_stone mushroom_stem brown_mushroom_block red_mushroom_block iron_bars chain melon
vine glow_lichen mycelium lily_pad nether_bricks nether_brick_fence enchanting_table brewing_stand cauldron
water_cauldron lava_cauldron powder_snow_cauldron end_portal end_portal_frame end_stone dragon_egg redstone_lamp
cocoa ender_chest tripwire_hook tripwire emerald_block beacon cobblestone_wall mossy_cobblestone_wall flower_pot
skeleton_skull wither_skeleton_skull zombie_head player_head creeper_head dragon_head piglin_head anvil chipped_anvil
damaged_anvil trapped_chest daylight_detector redstone_block nether_quartz_ore hopper quartz_block chiseled_quartz_block
quartz_pillar quartz_bricks smooth_quartz dropper dispenser observer piston sticky_piston piston_head slime_block
honey_block honeycomb_block barrier light iron_trapdoor prismarine prismarine_bricks dark_prismarine sea_lantern
hay_block terracotta coal_block packed_ice blue_ice sunflower lilac rose_bush peony tall_grass large_fern
chorus_plant chorus_flower purpur_block purpur_pillar end_stone_bricks grass_path dirt_path end_gateway
repeating_command_block chain_command_block command_block frosted_ice magma_block nether_wart_block warped_wart_block
red_nether_bricks bone_block structure_void structure_block jigsaw shulker_box dead_tube_coral_block
dead_brain_coral_block dead_bubble_coral_block dead_fire_coral_block dead_horn_coral_block tube_coral_block
brain_coral_block bubble_coral_block fire_coral_block horn_coral_block tube_coral brain_coral bubble_coral fire_coral
horn_coral dead_tube_coral dead_brain_coral dead_bubble_coral dead_fire_coral dead_horn_coral tube_coral_fan
brain_coral_fan bubble_coral_fan fire_coral_fan horn_coral_fan blue_ice conduit bamboo_block stripped_bamboo_block
scaffolding loom barrel smoker blast_furnace cartography_table fletching_table grindstone lectern smithing_table
stonecutter bell lantern soul_lantern campfire soul_campfire sweet_berry_bush warped_stem stripped_warped_stem
warped_hyphae stripped_warped_hyphae crimson_stem stripped_crimson_stem crimson_hyphae stripped_crimson_hyphae
shroomlight weeping_vines_plant twisting_vines_plant structure_void respawn_anchor lodestone blackstone
polished_blackstone polished_blackstone_bricks cracked_polished_blackstone_bricks chiseled_polished_blackstone
gilded_blackstone cracked_nether_bricks chiseled_nether_bricks quartz_bricks candle candle_cake target
crying_obsidian netherite_block ancient_debris chiseled_deepslate cracked_deepslate_bricks cracked_deepslate_tiles
deepslate_bricks deepslate_tiles reinforced_deepslate smooth_basalt raw_iron_block amethyst_cluster
large_amethyst_bud medium_amethyst_bud small_amethyst_bud pointed_dripstone powder_snow sculk sculk_vein
sculk_catalyst sculk_shrieker sculk_sensor lightning_rod ochre_froglight verdant_froglight pearlescent_froglight
frogspawn mangrove_propagule cherry_sapling cherry_leaves cherry_log stripped_cherry_log cherry_wood
stripped_cherry_wood cherry_planks decorated_pot suspicious_sand suspicious_gravel calibrated_sculk_sensor
pitcher_plant pitcher_crop torchflower_crop sniffer_egg wheat carrots potatoes beetroots nether_wart cake
smooth_sandstone smooth_red_sandstone red_sandstone chiseled_red_sandstone cut_red_sandstone
smooth_stone end_rod glass_pane oak_leaves spruce_leaves birch_leaves jungle_leaves acacia_leaves dark_oak_leaves
mangrove_leaves azalea_leaves flowering_azalea_leaves oak_sapling spruce_sapling birch_sapling jungle_sapling
acacia_sapling dark_oak_sapling moving_piston bubble_column water lava kelp dried_kelp_block dead_bush
netherite_block cracked_nether_bricks iron_door oak_door
"""
_BLOCKS = set()
for w_ in _MISC.split():
    _BLOCKS.add(w_)
for c in COLORS:
    for suf in ["wool", "concrete", "concrete_powder", "terracotta", "glazed_terracotta", "stained_glass",
                "stained_glass_pane", "carpet", "bed", "banner", "wall_banner", "candle", "candle_cake", "shulker_box"]:
        _BLOCKS.add(f"{c}_{suf}")
for w_ in WOODS:
    is_fungus = w_ in ("crimson", "warped")
    is_bamboo = w_ == "bamboo"
    for suf in ["planks", "stairs", "slab", "fence", "fence_gate", "door", "trapdoor", "button", "pressure_plate",
                "sign", "wall_sign", "hanging_sign", "wall_hanging_sign"]:
        _BLOCKS.add(f"{w_}_{suf}")
    if not is_fungus and not is_bamboo:
        for suf in ["log", "wood", "stripped_log", "stripped_wood", "leaves", "sapling"]:
            if suf.startswith("stripped_"):
                _BLOCKS.add(f"stripped_{w_}_{suf[9:]}")
            else:
                _BLOCKS.add(f"{w_}_{suf}")
    if is_bamboo:
        _BLOCKS.update(["bamboo_mosaic", "bamboo_mosaic_stairs", "bamboo_mosaic_slab"])
for base in _STONE_SETS:
    if base not in _NO_STAIRS:
        _BLOCKS.add(base + "_stairs")
    _BLOCKS.add(base + "_slab")
    if base not in _NO_WALL:
        _BLOCKS.add(base + "_wall")
_BLOCKS.update(["polished_blackstone_button", "polished_blackstone_pressure_plate", "petrified_oak_slab",
                "end_stone_brick_wall", "sandstone_wall", "red_sandstone_wall", "brick_wall", "prismarine_wall",
                "nether_brick_wall", "red_nether_brick_wall", "granite_wall", "diorite_wall", "andesite_wall",
                "stone_brick_wall", "mossy_stone_brick_wall", "blackstone_wall", "polished_blackstone_wall",
                "polished_blackstone_brick_wall", "cobbled_deepslate_wall", "polished_deepslate_wall",
                "deepslate_brick_wall", "deepslate_tile_wall", "mud_brick_wall", "tuff_wall"])
# 1.20.1 has no tuff variants (they arrived in 1.21) - remove to stay safe
_BLOCKS.discard("tuff_wall")
VALID_BLOCKS = frozenset("minecraft:" + b for b in _BLOCKS)

# ----------------------------------------------------------------------------- property schemas
_D4 = {"north", "east", "south", "west"}
_D6 = _D4 | {"up", "down"}
_BOOL = {"true", "false"}
_WALL_SIDE = {"none", "low", "tall"}
_PROPS: Dict[str, Dict[str, set]] = {}


def _schema(names: List[str], **props):
    for n in names:
        _PROPS.setdefault(n, {}).update(props)


_all = sorted(_BLOCKS)
_schema([b for b in _all if b.endswith("_stairs")], facing=_D4, half={"top", "bottom"},
        shape={"straight", "inner_left", "inner_right", "outer_left", "outer_right"}, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_slab")], type={"top", "bottom", "double"}, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_wall")], north=_WALL_SIDE, east=_WALL_SIDE, south=_WALL_SIDE, west=_WALL_SIDE,
        up=_BOOL, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_fence") or b in ("iron_bars", "glass_pane") or b.endswith("_stained_glass_pane")],
        north=_BOOL, east=_BOOL, south=_BOOL, west=_BOOL, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_fence_gate")], facing=_D4, open=_BOOL, powered=_BOOL, in_wall=_BOOL)
_schema([b for b in _all if b.endswith("_door")], facing=_D4, half={"upper", "lower"}, hinge={"left", "right"},
        open=_BOOL, powered=_BOOL)
_schema([b for b in _all if b.endswith("_trapdoor")], facing=_D4, half={"top", "bottom"}, open=_BOOL, powered=_BOOL,
        waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_button")], face={"floor", "wall", "ceiling"}, facing=_D4, powered=_BOOL)
_schema([b for b in _all if b.endswith("_pressure_plate")], powered=_BOOL, power={str(i) for i in range(16)})
_schema([b for b in _all if b.endswith("_log") or b.endswith("_wood") or b.endswith("_stem") or b.endswith("_hyphae")
         or b in ("quartz_pillar", "purpur_pillar", "basalt", "polished_basalt", "bone_block", "hay_block", "deepslate",
                  "chain", "bamboo_block", "stripped_bamboo_block", "ochre_froglight", "verdant_froglight",
                  "pearlescent_froglight", "muddy_mangrove_roots", "infested_deepslate")], axis={"x", "y", "z"},
        waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_leaves")], distance={str(i) for i in range(1, 8)}, persistent=_BOOL, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_sign") and "wall" not in b and "hanging" not in b] + [b for b in _all if b.endswith("_banner") and "wall" not in b],
        rotation={str(i) for i in range(16)}, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_wall_sign") or b.endswith("_wall_banner") or b.endswith("_wall_hanging_sign")],
        facing=_D4, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_hanging_sign") and "wall" not in b], rotation={str(i) for i in range(16)},
        attached=_BOOL, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_bed")], facing=_D4, part={"head", "foot"}, occupied=_BOOL)
_schema([b for b in _all if b.endswith("_candle") or b == "candle"], candles={"1", "2", "3", "4"}, lit=_BOOL, waterlogged=_BOOL)
_schema([b for b in _all if b.endswith("_shulker_box") or b == "shulker_box"], facing=_D6)
_schema([b for b in _all if b.endswith("_glazed_terracotta")], facing=_D4)
_schema(["observer", "dispenser", "dropper", "piston", "sticky_piston", "piston_head", "hopper", "barrel", "end_rod",
         "lightning_rod", "amethyst_cluster", "large_amethyst_bud", "medium_amethyst_bud", "small_amethyst_bud",
         "ladder", "furnace", "smoker", "blast_furnace", "lectern", "anvil", "chipped_anvil", "damaged_anvil",
         "stonecutter", "loom", "chest", "trapped_chest", "ender_chest", "wall_torch", "soul_wall_torch",
         "redstone_wall_torch", "campfire", "soul_campfire", "carved_pumpkin", "jack_o_lantern", "bell", "grindstone",
         "lever", "repeater", "comparator", "cocoa", "tripwire_hook", "skeleton_skull", "beehive", "bee_nest",
         "big_dripleaf", "small_dripleaf", "chiseled_bookshelf", "decorated_pot", "wither_skeleton_skull",
         "zombie_head", "player_head", "creeper_head", "dragon_head", "piglin_head", "end_portal_frame", "loom",
         "smithing_table", "fletching_table", "cartography_table", "calibrated_sculk_sensor", "attached_melon_stem",
         "attached_pumpkin_stem", "iron_trapdoor", "iron_door"],
        facing=_D6, powered=_BOOL, lit=_BOOL, extended=_BOOL, enabled=_BOOL, open=_BOOL, waterlogged=_BOOL,
        signal_fire=_BOOL, attachment={"floor", "ceiling", "single_wall", "double_wall"},
        face={"floor", "wall", "ceiling"}, delay={"1", "2", "3", "4"}, locked=_BOOL, mode={"compare", "subtract"},
        has_book=_BOOL, type={"single", "left", "right", "normal", "sticky"}, hanging=_BOOL, half={"top", "bottom"},
        hinge={"left", "right"}, honey_level={"0", "1", "2", "3", "4", "5"}, eye=_BOOL, tilt={"none", "unstable", "partial", "full"},
        cracked=_BOOL, power={str(i) for i in range(16)}, age={str(i) for i in range(3)},
        sculk_sensor_phase={"inactive", "active", "cooldown"}, attached=_BOOL, short=_BOOL,
        slot_0_occupied=_BOOL, slot_1_occupied=_BOOL, slot_2_occupied=_BOOL, slot_3_occupied=_BOOL,
        slot_4_occupied=_BOOL, slot_5_occupied=_BOOL)
_schema(["lantern", "soul_lantern"], hanging=_BOOL, waterlogged=_BOOL)
_schema(["snow"], layers={str(i) for i in range(1, 9)})
_schema(["redstone_lamp", "furnace", "smoker", "blast_furnace", "campfire", "soul_campfire", "candle", "redstone_torch",
         "redstone_wall_torch", "redstone_ore", "deepslate_redstone_ore"], lit=_BOOL)
_schema(["pointed_dripstone"], vertical_direction={"up", "down"}, thickness={"tip", "tip_merge", "frustum", "middle", "base"},
        waterlogged=_BOOL)
_schema(["scaffolding"], bottom=_BOOL, distance={str(i) for i in range(8)}, waterlogged=_BOOL)
_schema(["composter"], level={str(i) for i in range(9)})
_schema(["water_cauldron", "powder_snow_cauldron"], level={"1", "2", "3"})
_schema(["sea_pickle"], pickles={"1", "2", "3", "4"}, waterlogged=_BOOL)
_schema(["respawn_anchor"], charges={"0", "1", "2", "3", "4"})
_schema(["cake"], bites={str(i) for i in range(7)})
_schema(["daylight_detector"], inverted=_BOOL, power={str(i) for i in range(16)})
_schema(["sculk_sensor", "sculk_shrieker", "sculk_catalyst", "sculk_vein", "glow_lichen", "vine", "tripwire",
         "brewing_stand", "note_block", "jukebox", "tnt", "structure_block", "command_block", "target", "bamboo",
         "sweet_berry_bush", "sugar_cane", "cactus", "kelp", "nether_wart", "wheat", "carrots", "potatoes", "beetroots",
         "frosted_ice", "chorus_flower", "chorus_plant", "bubble_column", "brown_mushroom_block", "red_mushroom_block",
         "mushroom_stem", "fire", "soul_fire", "light", "water", "lava", "rail", "powered_rail", "detector_rail",
         "activator_rail", "redstone_wire", "mangrove_propagule", "pitcher_crop", "torchflower_crop", "sniffer_egg",
         "hanging_roots", "tall_seagrass", "seagrass", "spore_blossom", "moss_carpet", "pink_petals", "flower_pot",
         "sunflower", "lilac", "rose_bush", "peony", "tall_grass", "large_fern", "kelp_plant", "weeping_vines",
         "twisting_vines", "weeping_vines_plant", "twisting_vines_plant", "cave_vines", "cave_vines_plant",
         "nether_portal", "end_portal", "end_gateway", "structure_void", "jigsaw", "lodestone", "beacon", "conduit",
         "dragon_egg", "spawner", "enchanting_table", "crafting_table", "bookshelf", "barrier", "chain_command_block",
         "repeating_command_block", "moving_piston", "tube_coral", "brain_coral", "bubble_coral", "fire_coral",
         "horn_coral", "tube_coral_fan", "brain_coral_fan", "bubble_coral_fan", "fire_coral_fan", "horn_coral_fan",
         "dead_tube_coral", "dead_brain_coral", "dead_bubble_coral", "dead_fire_coral", "dead_horn_coral",
         "azalea", "flowering_azalea", "sculk", "suspicious_sand", "suspicious_gravel", "frogspawn", "cobweb"],
        north=_BOOL | _WALL_SIDE, east=_BOOL | _WALL_SIDE, south=_BOOL | _WALL_SIDE, west=_BOOL | _WALL_SIDE, up=_BOOL,
        down=_BOOL, waterlogged=_BOOL, power={str(i) for i in range(16)}, sculk_sensor_phase={"inactive", "active", "cooldown"},
        can_summon=_BOOL, shrieking=_BOOL, bloom=_BOOL, has_bottle_0=_BOOL, has_bottle_1=_BOOL, has_bottle_2=_BOOL,
        note={str(i) for i in range(25)}, instrument={"harp", "basedrum", "snare", "hat", "bass", "flute", "bell",
        "guitar", "chime", "xylophone", "iron_xylophone", "cow_bell", "didgeridoo", "bit", "banjo", "pling", "zombie",
        "skeleton", "creeper", "dragon", "wither_skeleton", "piglin", "custom_head"}, has_record=_BOOL, unstable=_BOOL,
        mode={"save", "load", "corner", "data"}, conditional=_BOOL, age={str(i) for i in range(26)},
        level={str(i) for i in range(16)}, half={"upper", "lower"}, hatch={"0", "1", "2"}, eggs={"1", "2", "3", "4"},
        flower_amount={"1", "2", "3", "4"}, berries=_BOOL, leaves={"none", "small", "large"}, stage={"0", "1"},
        shape={"north_south", "east_west", "ascending_east", "ascending_west", "ascending_north", "ascending_south",
               "south_east", "south_west", "north_west", "north_east"}, powered=_BOOL, attached=_BOOL, disarmed=_BOOL,
        drag=_BOOL, pickles={"1", "2", "3", "4"}, dusted={"0", "1", "2", "3"}, lit=_BOOL, triggered=_BOOL,
        facing=_D6, axis={"x", "y", "z"}, snowy=_BOOL, hanging=_BOOL, moisture={str(i) for i in range(8)})
_schema(["grass_block", "podzol", "mycelium"], snowy=_BOOL)
_schema(["tnt"], unstable=_BOOL)
_schema(["note_block"], instrument=_PROPS["jukebox"]["instrument"], note={str(i) for i in range(25)}, powered=_BOOL)
_schema(["farmland"], moisture={str(i) for i in range(8)})
_schema(["copper_bulb"], lit=_BOOL, powered=_BOOL)


def validate_block(block: str) -> Optional[str]:
    """Return an error string if the block id / state is not valid vanilla 1.20.1, else None."""
    try:
        name, props = parse(block)
    except ValueError as e:
        return str(e)
    if name not in VALID_BLOCKS:
        return f"unknown block id {name}"
    short = name.split(":", 1)[1]
    schema = _PROPS.get(short, {})
    for k, v in props.items():
        if k not in schema:
            return f"{name}: unknown property '{k}'"
        if v not in schema[k]:
            return f"{name}: bad value '{v}' for '{k}' (allowed: {sorted(schema[k])})"
    return None
