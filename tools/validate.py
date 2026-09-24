"""Quality checks for a Schematic: valid block ids/states, size, floating debris, palette variety."""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from .schem import Schematic, AIR
from .states import validate_block
from .colors import block_color

MAX_DIM = 320


def validate(s: Schematic, name: str = "") -> Dict[str, object]:
    """Return a report dict: {'ok': bool, 'errors': [...], 'warnings': [...], 'stats': {...}}"""
    errors: List[str] = []
    warnings: List[str] = []
    s.compact_palette()
    for b in s.blocks_by_id:
        if b == AIR:
            continue
        err = validate_block(b)
        if err:
            errors.append(err)
        if block_color(b) == (255, 0, 255):
            warnings.append(f"no preview colour for {b} (renders magenta)")
    if max(s.w, s.h, s.l) > MAX_DIM:
        errors.append(f"too large: {s.w}x{s.h}x{s.l} (max {MAX_DIM} per axis)")
    n = s.count()
    if n == 0:
        errors.append("schematic is empty")
    b = s.bounds()
    stats = {"size": [s.w, s.h, s.l], "blocks": n, "palette": len(s.palette) - 1, "ground": s.ground, "bounds": b}
    if b:
        x0, y0, z0, x1, y1, z1 = b
        if y0 < s.ground:
            stats["below_ground"] = int((s.data[:, :s.ground, :] != 0).sum())
        # unused margin
        if x0 > 3 or z0 > 3 or s.w - 1 - x1 > 3 or s.l - 1 - z1 > 3 or s.h - 1 - y1 > 3:
            warnings.append(f"large empty margin around content (bounds {b} in {s.w}x{s.h}x{s.l}); call .cropped(pad=1)")
    # floating single blocks (no 6-neighbour) above ground
    nz = s.data != 0
    pad = np.zeros((s.w + 2, s.h + 2, s.l + 2), dtype=bool)
    pad[1:-1, 1:-1, 1:-1] = nz
    neigh = (pad[:-2, 1:-1, 1:-1] | pad[2:, 1:-1, 1:-1] | pad[1:-1, :-2, 1:-1] | pad[1:-1, 2:, 1:-1]
             | pad[1:-1, 1:-1, :-2] | pad[1:-1, 1:-1, 2:])
    floating = nz & ~neigh
    floating[:, : s.ground + 1, :] = False
    fl = np.argwhere(floating)
    if len(fl):
        stats["floating_blocks"] = int(len(fl))
        if len(fl) > 12:
            warnings.append(f"{len(fl)} isolated floating blocks (no neighbour); e.g. {[tuple(int(v) for v in p) for p in fl[:5]]}")
    if len(s.palette) - 1 < 4 and n > 200:
        warnings.append("very small palette (<4 block types): builds look flat; add trim/detail blocks")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "stats": stats, "name": name}


def print_report(rep: Dict[str, object]) -> None:
    st = rep["stats"]
    print(f"[{rep.get('name','')}] {'OK' if rep['ok'] else 'FAIL'} size={st['size']} blocks={st['blocks']} palette={st['palette']} ground={st['ground']}")
    for e in rep["errors"]:
        print("  ERROR:", e)
    for w in rep["warnings"]:
        print("  warn :", w)
