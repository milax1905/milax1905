# Design bible — "Neige" world schematics

## The world
Screenshot reference: endless **white snow hills**, a **pink/lavender sky** with a pale sun, **lavender / purple
trees**, **blue crystal spikes** sticking out of the snow, faint glowing spores in the air. Dreamy, cold, alien.
Everything we build must sit in *that* picture: pale surfaces + lavender/pink/blue accents, with dark blocks used for
contrast (villain city, scorched wreck undersides), never for the whole build.

Story (from the players): **crashed ships**, **abandoned laboratories**, a **tech city of villains**, and
**exploration camps**. Bonus structures follow the same story (escape pods, comms arrays, drill rigs, crystal
research sites, a frozen alien skeleton, a beacon tower, a mech wreck...).

## Hard rules
1. **Vanilla 1.20.1 blocks only** (`tools/states.py` validates ids and state properties - the build fails otherwise).
2. Use the helpers in `tools/states.py` (`st.stairs`, `st.slab`, `st.log`, `st.trapdoor`, ...) - never hand-write
   states. Fences / panes / walls / iron bars are auto-connected and stair corners auto-shaped by `finalize()`.
3. Each build lives in `builds/<name>.py` and exposes `build() -> dict[name, Schematic]`. Run it with
   `python3 -m tools.build_all <name>`; it validates, writes `schematics/<name>.schem` and previews in `previews/`.
4. **Look at your render** (`Read previews/<name>_iso.png` and `_plan.png`) and iterate. Minimum 3 build/render/fix
   rounds. A build that was never looked at is not finished.
5. No magenta (unknown-colour) blocks, no floating blocks, no unfinished sides (all 4 rotations must look good).
6. Keep bounding boxes tight: end with `s = s.cropped(pad=1)` if you over-allocated (keeps ground index right).
7. `Schematic(w, h, l, ground=g)`: y = g is the **surface level**. Foundations/craters go below g, everything else
   sits on y >= g+1. WorldEdit `//paste` puts the player's feet at (w//2, g, l//2). For structures pasted onto snow
   with `//paste -a` (air skipped) put nothing below g except deliberate crater/scorch floors.

## What "ultra clean" means here
* **Silhouette first.** Read the shape from 60 blocks away: a ship is a swept hull + engines + fins, not a box.
  Use `sh.loft()` (elliptical cross-sections along an axis) for hulls, pods, tanks, domes; `sh.cylinder()` with
  `r2` for nozzles/cones; `sh.dome()` for observatories.
* **Depth on every surface.** Max ~5 blocks of flat identical wall without: an inset, a rib, a trim line, a window
  strip, a vent (iron trapdoor), a hatch, a light strip, a bevel (stairs / slabs on edges). Layer 2-3 materials.
* **Gradient texturing.** Big hull/wall surfaces: 70 % primary, 25 % a close shade, 5 % a third
  (`sh.texturize(s, "light_gray_concrete", [("light_gray_concrete", 7), ("white_concrete", 2), ("quartz_block", 1)])`).
  Keep variants *close* in colour - noise, not camouflage.
* **White on white does not read.** Snow is white, so every pale build needs a dark *structure* layer
  (polished deepslate / blackstone / iron ribs, trims, undersides, keels) that draws the silhouette, and pale
  surfaces are textured only with CLOSE shades (`MIX_WHITE`, `MIX_LIGHT_GRAY`, `MIX_DARK`... in `tools/palette.py`).
  Never checkerboard two contrasting blocks.
* **Bevel the edges.** Stairs (`half=top` under overhangs) and slabs to round hull edges, roof edges, pod tops.
* **Thin blocks are the detail language:** iron trapdoors (vents/panels), buttons (rivets/switches), walls & fences
  (railings, struts), chains (cables, axis=x/z to run horizontally), end rods & lightning rods (antennas, pins),
  iron bars (grates), glass panes (windows), pointed dripstone (spikes, icicles under overhangs), snow layers
  (weathering), candles / sea pickles (tiny lights), amethyst clusters (crystals), scaffolding (repairs), campfires
  (fires; soul_campfire = blue smoke), banners (flags), signs (lore).
* **Lighting is part of the design.** Sea lanterns / froglights / end rods set into floors and along edges; every
  interior must be lit. Hide light sources behind glass or in ceilings for "neon".
* **Story in every build.** A wreck has a crater (`sh.crater`), scorched floor, a broken-off piece 15 blocks away,
  a debris trail (`sh.scatter`), snow drift piling on the leeward side (`sh.snow_cover`), a soul_campfire smoking in
  the engine, a loot chest (`s.add_chest(..., loot_table=...)`), a sign with a last log entry (`s.add_sign`).
* **Interiors are walkable:** corridors 2 wide x 3 high min, rooms with furniture, consoles, pods, tanks.
* **Asymmetry for wrecks & ruins, symmetry for the villain city and labs** (they were engineered).

## Sizes (blocks)
| kind | footprint | height |
|---|---|---|
| escape pod / small camp | 12-20 | 8-12 |
| scout ship / lab outpost / camp base | 25-45 | 10-18 |
| big freighter wreck / main lab / crystal site | 50-90 | 18-30 |
| city module (wall, tower, hab, factory) | 15-40 | 15-70 |
| city showcase (assembled) | 120-180 | 60-90 |

## Palettes
See `tools/palette.py` (`SHIP`, `LAB`, `VILLAIN`, `CAMP`, `CRYSTAL`, `GROUND`). Signature blocks of this world:
`pearlescent_froglight` (pink-white glow), `purpur` (lavender alien tech), `amethyst` (crystal), `blue_ice` /
`light_blue_stained_glass` (crystal spikes), `cherry_planks` (pink wood), `white/light_gray concrete + quartz`
(clean hulls), `polished_blackstone_bricks + deepslate_tiles + crying_obsidian + magenta/purple glass` (villains).

## Tool cheat-sheet
```python
from tools.schem import Schematic
from tools import shapes as sh, states as st
from tools.palette import SHIP, LAB, VILLAIN, CAMP, CRYSTAL, GROUND

s = Schematic(60, 24, 40, ground=4)                      # x=60 (east), y=24 (up), z=40 (south); surface at y=4
sh.ground_slab(s, 4, GROUND["snow"], depth=5)            # snow ground (only for crash sites / craters)
sh.crater(s, cx=30, cz=20, r=14, ground_y=4, floor=SHIP["scorch"], rim=GROUND["snow"], ejecta="minecraft:tuff", depth=2)
secs = [(6, 10, 20, 2, 3), (20, 11, 20, 5, 7), (40, 12, 20, 5, 6), (54, 13, 20, 2, 2)]   # (x, cy, cz, ry, rz)
hull = sh.loft(s, secs, SHIP["hull"], axis="x")           # solid hull (returns mask)
sh.fill_mask(s, sh.loft_mask(s, secs, "x", shrink=2), "air")   # carve a 2-thick shell
sh.box(s, 20, 12, 13, 40, 13, 13, SHIP["glass"])          # window strip
s.set(30, 18, 20, st.end_rod("up")); s.set(31, 9, 20, st.stairs(SHIP["hull_stairs"], "west", "top"))
s.set(10, 5, 8, st.log("minecraft:chain", "x"))           # horizontal chain
sh.texturize(s, SHIP["hull"], [(SHIP["hull"], 7), (SHIP["hull_light"], 2), (SHIP["hull_alt"], 1)])
sh.erode(s, 40, 8, 10, 56, 18, 30, prob=0.35, only=["concrete", "quartz"])   # damage the tail
sh.snow_cover(s, y_min=5, prob=0.7)                       # snow layers on exposed tops
sh.scatter(s, 0, 0, 59, 39, [SHIP["damage_fill"], "minecraft:iron_block"], 25)   # debris
s.add_chest(12, 5, 20, "north", "minecraft:chests/shipwreck_supply")
s.add_sign(13, 6, 20, "minecraft:warped_wall_sign[facing=south]", ["LOG 47", "hull breach", "deck 2", ""])
s.set(30, 6, 20, st.campfire(soul=True))                  # blue smoke
return {"ship_crash_freighter": s}
```
Other helpers: `sh.hollow_box`, `sh.room`, `sh.ellipsoid`, `sh.sphere`, `sh.dome`, `sh.cylinder(axis, r2)`,
`sh.elliptic_cylinder`, `sh.torus`, `sh.line(p1, p2, block, radius)`, `sh.polygon_prism`, `sh.ring`,
`sh.outline_top`, `sh.pillars`, `sh.stair_ramp`, `sh.roof_gable`, `sh.light_strip`, `sh.surface_mask`,
`sh.blocks_mask`, `sh.replace_in_region`, `s.paste(other, ox, oy, oz)`, `s.rotated(k)`, `s.mirrored_x()`,
`s.cropped(pad)`, `s.top_y(x, z)`, `s.get/set/set_if_air/is_air`.

## Self-review checklist (before you return)
- [ ] All 4 iso views + plan look intentional; no accidental holes, no magenta, no floating cubes, no z-fighting
      double blocks (e.g. a slab inside a full block).
- [ ] The build reads at a glance as what it is (ship / lab / camp / city).
- [ ] Palette: 1 dominant, 1 secondary, accents + light. Big surfaces textured. Edges bevelled.
- [ ] Story details: damage, snow, debris, lights, signs, loot chest(s), smoke/fire where it makes sense.
- [ ] Interior exists, is lit, walkable, furnished (for anything with a door/breach).
- [ ] Ground integration: the base sits *in* the snow (bury 1-2 blocks / crater), not on a floating slab of snow.
- [ ] `python3 -m tools.build_all <name>` prints OK with no warnings you can fix.

## Lessons from round 1 (read before revising)
* The renderer camera: rot 0 = from the south-east (east face right, south face left), rot 1 = from the north-east,
  rot 2 = north-west, rot 3 = south-west. Use the plan view (north up, east right) to place things.
* A lofted hull's *interior* is much narrower at floor level than the section radius suggests: plan furniture
  from the carved mask, not the radii. Decks/floors inside lofts: fill the mask below a y level.
* "Popcorn" hulls: stair bevels on every loft ring + a 3-shade texture + dense snow layers make a lumpy mess.
  Bevel only true silhouette edges, use slabs on top surfaces, 2 close shades, snow only on the leeward ridge.
* Chains for cables: horizontal chain (axis x/z) reads as a cable; a staircase of alternating chain segments
  reads as floating dashes. Run cables straight, on crossbar arms, or as a single vertical drop.
* Big single dark/coloured cubes on white snow read as debris/mistakes (yellow cubes, black blobs, cyan
  lanterns). Every accent block needs a frame, a post or a purpose.
* Sea lanterns must never show a bare face on a dark build: cap them with purple/tinted glass or sink them.
* Diagonal lines of thin blocks (chains, bars) are only corner-adjacent: they render (and read) as dotted lines.
* `Schematic.paste/rotated/cropped/load` now carry block entities (signs, loot chests). `st.door()` validates.
* `sh.snow_cover` now covers snow_block (not snow layers); it never covers stairs/slabs (vanilla rule).
* Doors: `st.door("iron", facing, half="lower"/"upper", ...)`; trapdoors use half top/bottom.
