"""
Build runner. Each builds/<name>.py must define `build() -> dict[str, Schematic]` (one or more named schematics).

    python3 -m tools.build_all                 # build + validate + render everything
    python3 -m tools.build_all ship_freighter  # only that module
    python3 -m tools.build_all --no-render x   # skip previews
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tools.validate import validate, print_report  # noqa: E402
from tools.render import render_views  # noqa: E402
from tools.shapes import finalize  # noqa: E402


def run(modules, render=True, tw=16):
    out_dir = os.path.join(ROOT, "schematics")
    prev_dir = os.path.join(ROOT, "previews")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(prev_dir, exist_ok=True)
    summary = {}
    ok_all = True
    for mod_name in modules:
        t0 = time.time()
        mod = importlib.import_module(f"builds.{mod_name}")
        result = mod.build()
        if not isinstance(result, dict):
            result = {mod_name: result}
        for name, s in result.items():
            finalize(s)
            rep = validate(s, name)
            print_report(rep)
            ok_all &= rep["ok"]
            if rep["ok"]:
                path = s.save(os.path.join(out_dir, name + ".schem"))
                paths = render_views(s, os.path.join(prev_dir, name), tw=tw) if render else []
                rep["files"] = [path] + paths
            summary[name] = rep
        print(f"  ({mod_name}: {time.time() - t0:.1f}s)")
    path = os.path.join(ROOT, "previews", "_summary.json")
    merged = {}
    try:
        with open(path) as f:
            merged = json.load(f)
    except Exception:
        merged = {}
    merged.update(summary)
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(merged, f, indent=1, default=str)
    os.replace(tmp, path)
    return ok_all, summary


def all_modules():
    d = os.path.join(ROOT, "builds")
    return sorted(f[:-3] for f in os.listdir(d) if f.endswith(".py") and not f.startswith("_"))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    render = "--no-render" not in sys.argv
    mods = args or all_modules()
    ok, _ = run(mods, render=render)
    sys.exit(0 if ok else 1)
