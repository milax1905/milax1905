# Schematics « Neige » — vaisseaux écrasés, labos abandonnés, ville tech, camps

Un pack de schematics Minecraft (format **Sponge `.schem`**, blocs **vanilla 1.20.1**, compatible 1.20+ /
1.21) conçu pour le monde enneigé au ciel rose : vaisseaux écrasés, laboratoires abandonnés, la ville tech des
« salopards », des camps d'exploration, et des structures bonus dans la même histoire.

* `schematics/` — les fichiers `.schem` prêts à coller
* `previews/` — rendus isométriques (4 angles) + vue de dessus de chaque structure, et `index.html` (galerie)
* `builds/` — le code Python qui génère chaque structure (modifiable : palette, taille, détails)
* `tools/` — la boîte à outils (écriture `.schem`, formes, rendu, validation)

Le catalogue détaillé (taille, description, conseils de placement) est dans **`CATALOGUE.md`**.

## Installation (WorldEdit / FAWE)

1. Copier les `.schem` dans `plugins/WorldEdit/schematics/` (serveur Bukkit/Paper) ou
   `plugins/FastAsyncWorldEdit/schematics/` (FAWE), ou `config/worldedit/schematics/` (Forge/Fabric).
2. En jeu : `//schem load <nom>` puis se placer **au niveau du sol** à l'endroit voulu.
3. Coller :
   * structures posées sur la neige (labos, camps, tours, ville…) : `//paste -a` (l'air n'écrase pas le terrain)
   * sites de crash avec cratère (`ship_crash_*`, `escape_pod`, `orbital_debris`, `mech_wreck`…) : `//paste`
     **sans** `-a` sur un endroit à peu près plat, pour que le cratère et le sol brûlé remplacent la neige.
     Ces schematics contiennent une dalle de sol en `snow_block` : si votre terrain utilise un autre bloc,
     faites `//replace snow_block <votre_bloc>` sur la sélection collée.
4. Le point de collage est le centre horizontal de la structure, au niveau du sol (pieds du joueur = surface).
   `//rotate 90` avant de coller pour orienter ; `//undo` si besoin.

**Litematica** (client) : les `.schem` se chargent directement (Load Schematics → choisir le fichier ; Litematica
lit le format Sponge) ou via conversion dans le Schematic Manager.

## Ville des salopards

La ville est fournie en **modules** (`city_wall_segment`, `city_wall_corner`, `city_gate`, `city_watchtower`,
`city_spire`, `city_factory`, `city_hab_block`, `city_hangar`, `city_landing_pad`, `villain_ship`) **et** en
version assemblée (`city_showcase`, 156×149, ~119 000 blocs).

Pour monter une muraille soi-même, les trois pièces de mur ont un point de collage spécial : le joueur se place
**sur la ligne de la face extérieure** (côté ennemi), à l'**extrémité ouest** de la pièce, pieds sur la neige.
* `city_wall_segment` : s'étend sur 16 blocs vers l'est ; le mur est sur la rangée du joueur et 4 blocs vers le sud.
* `city_gate` : 24 blocs vers l'est ; les tours dépassent de 2 blocs vers le nord.
* `city_wall_corner` : le joueur est au croisement des deux faces extérieures (nord et ouest) ; les joints sont
  14 blocs à l'est et 14 blocs au sud. `//rotate 90/180/270` pour les autres angles.

Un mur nord droit = se placer sur la ligne extérieure, coller, avancer de 16 (segment) ou 24 (porte) vers l'est,
coller, etc. Les autres modules (tours, bâtiments, flèche, aire) se collent normalement par leur centre.

## Régénérer / modifier

```bash
pip install pillow numpy nbtlib
python3 -m tools.build_all                # tout reconstruire + valider + rendre
python3 -m tools.build_all camps          # un seul module
python3 -m tools.gallery                  # galerie previews/index.html + planche contact
```
Chaque `builds/<module>.py` expose `build()` qui renvoie un ou plusieurs `Schematic`. Voir `STYLE.md` pour les
règles de design et la palette du monde.
