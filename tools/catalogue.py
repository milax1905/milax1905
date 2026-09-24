"""Generate CATALOGUE.md (French) from catalog.json + previews/_summary.json."""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    cat = json.load(open(os.path.join(ROOT, "catalog.json")))
    summ = json.load(open(os.path.join(ROOT, "previews", "_summary.json")))
    order = ["Vaisseaux écrasés", "Labos abandonnés", "Ville tech des salopards", "Camps d'exploration", "Bonus"]
    out = ["# Catalogue des schematics", "",
           "Toutes les tailles sont en blocs (largeur x × hauteur y × longueur z). Le point de collage WorldEdit est le",
           "centre horizontal, au niveau du sol. `-a` = `//paste -a` (l'air ne remplace pas le terrain).", ""]
    for c in order:
        out.append(f"## {c}")
        out.append("")
        out.append("| Fichier | Structure | Taille | Blocs | Collage | Description |")
        out.append("|---|---|---|---|---|---|")
        for name, m in cat.items():
            if m["category"] != c:
                continue
            st = summ.get(name, {}).get("stats", {})
            size = "×".join(str(v) for v in st.get("size", [])) if st else "?"
            blocks = f"{st.get('blocks', 0):,}".replace(",", " ") if st else "?"
            out.append(f"| `{name}.schem` | **{m['title']}** | {size} | {blocks} | {m['paste']} | {m['fr']} |")
        out.append("")
    out += ["## Aperçus", "", "Chaque structure a deux images dans `previews/` : `<nom>_iso.png` (4 angles) et `<nom>_plan.png` (vue de dessus).",
            "La galerie complète est dans `previews/index.html`.", ""]
    with open(os.path.join(ROOT, "CATALOGUE.md"), "w") as f:
        f.write("\n".join(out))
    print("CATALOGUE.md written")


if __name__ == "__main__":
    main()
