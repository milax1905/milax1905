"""
Minimal, fast Sponge Schematic (v2, .schem) writer/reader built on numpy + nbtlib.

Coordinates: (x, y, z) with y = up. Blocks are full state strings such as
"minecraft:stone" or "minecraft:oak_stairs[facing=north,half=bottom]".

Usage:
    s = Schematic(40, 20, 40)          # width (x), height (y), length (z)
    s.set(1, 0, 1, "minecraft:snow_block")
    s.save("out.schem")
"""
from __future__ import annotations

import gzip
import io
import os
from typing import Dict, Iterable, Optional, Tuple

import numpy as np
import nbtlib
from nbtlib import tag

AIR = "minecraft:air"
DATA_VERSION_1_20_1 = 3465


def norm_block(block: str) -> str:
    """Normalise a block string: add the minecraft: namespace, strip spaces."""
    b = block.strip().replace(" ", "")
    if not b:
        return AIR
    if ":" not in b.split("[", 1)[0]:
        b = "minecraft:" + b
    return b


class Schematic:
    """A dense block grid. Index 0 is always air."""

    def __init__(self, width: int, height: int, length: int, ground: int = 0, fill: str = AIR):
        assert width > 0 and height > 0 and length > 0, "dimensions must be positive"
        self.w, self.h, self.l = int(width), int(height), int(length)
        self.palette: Dict[str, int] = {AIR: 0}
        self.blocks_by_id = [AIR]
        self.data = np.zeros((self.w, self.h, self.l), dtype=np.int32)
        # 'ground' = y index of the ground plane. When pasted with WorldEdit the paste
        # point (player position) lands on (w//2, ground, l//2), so the build sits on the floor.
        self.ground = int(ground)
        self.block_entities = []  # list of dicts (Pos, Id, extra)
        if fill != AIR:
            self.data[:] = self.pid(fill)

    # ------------------------------------------------------------------ palette
    def pid(self, block: str) -> int:
        block = norm_block(block)
        i = self.palette.get(block)
        if i is None:
            i = len(self.blocks_by_id)
            self.palette[block] = i
            self.blocks_by_id.append(block)
        return i

    # ------------------------------------------------------------------ access
    def inside(self, x: int, y: int, z: int) -> bool:
        return 0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.l

    def set(self, x: int, y: int, z: int, block: str) -> None:
        """Set a block; silently ignores out-of-bounds coordinates."""
        x, y, z = int(x), int(y), int(z)
        if 0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.l:
            self.data[x, y, z] = self.pid(block)

    def set_if_air(self, x: int, y: int, z: int, block: str) -> None:
        x, y, z = int(x), int(y), int(z)
        if 0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.l and self.data[x, y, z] == 0:
            self.data[x, y, z] = self.pid(block)

    def get(self, x: int, y: int, z: int) -> str:
        x, y, z = int(x), int(y), int(z)
        if not (0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.l):
            return AIR
        return self.blocks_by_id[self.data[x, y, z]]

    def is_air(self, x: int, y: int, z: int) -> bool:
        x, y, z = int(x), int(y), int(z)
        if not (0 <= x < self.w and 0 <= y < self.h and 0 <= z < self.l):
            return True
        return self.data[x, y, z] == 0

    def count(self) -> int:
        return int(np.count_nonzero(self.data))

    def bounds(self) -> Optional[Tuple[int, int, int, int, int, int]]:
        """(x0,y0,z0,x1,y1,z1) inclusive bounds of non-air blocks, or None."""
        nz = np.argwhere(self.data != 0)
        if len(nz) == 0:
            return None
        mn = nz.min(axis=0)
        mx = nz.max(axis=0)
        return int(mn[0]), int(mn[1]), int(mn[2]), int(mx[0]), int(mx[1]), int(mx[2])

    def top_y(self, x: int, z: int) -> int:
        """Highest non-air y in column (x,z), or -1."""
        x, z = int(x), int(z)
        if not (0 <= x < self.w and 0 <= z < self.l):
            return -1
        col = self.data[x, :, z]
        nz = np.nonzero(col)[0]
        return int(nz[-1]) if len(nz) else -1

    # ------------------------------------------------------------------ bulk ops
    def replace(self, mapping: Dict[str, str]) -> None:
        """Replace blocks by exact state string."""
        for src, dst in mapping.items():
            src_n, dst_n = norm_block(src), norm_block(dst)
            if src_n in self.palette:
                self.data[self.data == self.palette[src_n]] = self.pid(dst_n)

    def paste(self, other: "Schematic", ox: int, oy: int, oz: int, skip_air: bool = True) -> None:
        """Paste another schematic at offset (ox,oy,oz) (other's (0,0,0) lands there)."""
        for i, b in enumerate(other.blocks_by_id):
            if i == 0 and skip_air:
                continue
            pid = self.pid(b)
            xs, ys, zs = np.nonzero(other.data == i) if i else np.nonzero(other.data == 0)
            xs, ys, zs = xs + ox, ys + oy, zs + oz
            m = (xs >= 0) & (xs < self.w) & (ys >= 0) & (ys < self.h) & (zs >= 0) & (zs < self.l)
            self.data[xs[m], ys[m], zs[m]] = pid

    def rotated(self, k: int) -> "Schematic":
        """Return a copy rotated k*90 degrees clockwise (seen from above) around Y.
        Block-state 'facing'/'axis'/'rotation' properties are rotated accordingly."""
        from .states import rotate_state  # local import to avoid cycle
        k %= 4
        out = Schematic(self.l if k % 2 else self.w, self.h, self.w if k % 2 else self.l, ground=self.ground)
        d = self.data
        # one clockwise step seen from above (+x east, +z south): (x, z) -> (L-1-z, x)
        for _ in range(k):
            d = np.transpose(d, (2, 1, 0))[::-1, :, :]
        out.data = np.ascontiguousarray(d)
        out.palette = {}
        out.blocks_by_id = []
        for b in self.blocks_by_id:
            nb = rotate_state(b, k)
            out.blocks_by_id.append(nb)
            out.palette[nb] = len(out.blocks_by_id) - 1
        return out

    def mirrored_x(self) -> "Schematic":
        from .states import mirror_state
        out = Schematic(self.w, self.h, self.l, ground=self.ground)
        out.data = self.data[::-1, :, :].copy()
        out.palette, out.blocks_by_id = {}, []
        for b in self.blocks_by_id:
            nb = mirror_state(b, "x")
            out.blocks_by_id.append(nb)
            out.palette[nb] = len(out.blocks_by_id) - 1
        return out

    def cropped(self, pad: int = 0, keep_ground: bool = True) -> "Schematic":
        """Return a copy cropped to the non-air bounds (+pad). Keeps the ground plane index valid."""
        b = self.bounds()
        if b is None:
            return self
        x0, y0, z0, x1, y1, z1 = b
        x0, z0 = max(0, x0 - pad), max(0, z0 - pad)
        x1, z1 = min(self.w - 1, x1 + pad), min(self.l - 1, z1 + pad)
        if keep_ground:
            y0 = min(y0, self.ground)
        out = Schematic(x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1, ground=self.ground - y0)
        out.data = self.data[x0:x1 + 1, y0:y1 + 1, z0:z1 + 1].copy()
        out.palette = dict(self.palette)
        out.blocks_by_id = list(self.blocks_by_id)
        out.block_entities = [dict(e, Pos=[e["Pos"][0] - x0, e["Pos"][1] - y0, e["Pos"][2] - z0]) for e in self.block_entities
                              if x0 <= e["Pos"][0] <= x1 and y0 <= e["Pos"][1] <= y1 and z0 <= e["Pos"][2] <= z1]
        return out

    def compact_palette(self) -> None:
        """Drop unused palette entries (keeps air at 0)."""
        used = np.unique(self.data)
        remap = {0: 0}
        new_ids = [AIR]
        for i in used:
            i = int(i)
            if i == 0:
                continue
            remap[i] = len(new_ids)
            new_ids.append(self.blocks_by_id[i])
        lut = np.zeros(len(self.blocks_by_id), dtype=np.int32)
        for k, v in remap.items():
            lut[k] = v
        self.data = lut[self.data]
        self.blocks_by_id = new_ids
        self.palette = {b: i for i, b in enumerate(new_ids)}

    # ------------------------------------------------------------------ block entities
    def add_sign(self, x: int, y: int, z: int, block: str, lines: Iterable[str]) -> None:
        """Place a sign block with up to 4 lines of text (1.20 format)."""
        self.set(x, y, z, block)
        lines = list(lines)[:4]
        while len(lines) < 4:
            lines.append("")
        self.block_entities.append({
            "Pos": [int(x), int(y), int(z)],
            "Id": "minecraft:sign",
            "front_text": {"messages": ['{"text":"%s"}' % l.replace('"', '\\"') for l in lines],
                            "color": "black", "has_glowing_text": False},
            "back_text": {"messages": ['{"text":""}'] * 4, "color": "black", "has_glowing_text": False},
            "is_waxed": True,
        })

    def add_chest(self, x: int, y: int, z: int, facing: str = "north", loot_table: str = "minecraft:chests/abandoned_mineshaft",
                  kind: str = "chest") -> None:
        """Place a chest/barrel that fills itself from a vanilla loot table when first opened.
        Good tables: chests/abandoned_mineshaft, chests/ancient_city, chests/end_city_treasure, chests/igloo_chest,
        chests/stronghold_library, chests/simple_dungeon, chests/bastion_other, chests/shipwreck_supply,
        chests/shipwreck_treasure, chests/buried_treasure, chests/woodland_mansion, chests/pillager_outpost."""
        if kind == "barrel":
            self.set(x, y, z, f"minecraft:barrel[facing={facing},open=false]")
        else:
            self.set(x, y, z, f"minecraft:chest[facing={facing},type=single,waterlogged=false]")
        self.block_entities.append({"Pos": [int(x), int(y), int(z)], "Id": f"minecraft:{kind}",
                                    "LootTable": loot_table})

    # ------------------------------------------------------------------ io
    def _encode_blockdata(self) -> bytes:
        # Sponge order: index = x + z*Width + y*Width*Length  -> iterate y, z, x
        flat = np.transpose(self.data, (1, 2, 0)).reshape(-1)  # (y, z, x) order
        out = bytearray()
        if len(self.blocks_by_id) <= 128:
            out = bytearray(flat.astype(np.uint8).tobytes())
        else:
            for v in flat:
                v = int(v)
                while True:
                    b = v & 0x7F
                    v >>= 7
                    if v:
                        out.append(b | 0x80)
                    else:
                        out.append(b)
                        break
        return bytes(out)

    def to_nbt(self, data_version: int = DATA_VERSION_1_20_1) -> nbtlib.File:
        self.compact_palette()
        pal = tag.Compound({b: tag.Int(i) for b, i in self.palette.items()})
        bes = tag.List[tag.Compound]()
        for e in self.block_entities:
            c = tag.Compound({"Pos": tag.IntArray(e["Pos"]), "Id": tag.String(e["Id"])})
            for k, v in e.items():
                if k in ("Pos", "Id"):
                    continue
                c[k] = _to_tag(v)
            bes.append(c)
        root = tag.Compound({
            "Version": tag.Int(2),
            "DataVersion": tag.Int(data_version),
            "Width": tag.Short(self.w),
            "Height": tag.Short(self.h),
            "Length": tag.Short(self.l),
            "Offset": tag.IntArray([0, 0, 0]),
            "PaletteMax": tag.Int(len(self.palette)),
            "Palette": pal,
            "BlockData": tag.ByteArray(np.frombuffer(self._encode_blockdata(), dtype=np.int8)),
            "BlockEntities": bes,
            "Metadata": tag.Compound({
                "WEOffsetX": tag.Int(-(self.w // 2)),
                "WEOffsetY": tag.Int(-self.ground),
                "WEOffsetZ": tag.Int(-(self.l // 2)),
            }),
        })
        return nbtlib.File(root, gzipped=True, root_name="Schematic")

    def save(self, path: str, data_version: int = DATA_VERSION_1_20_1) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        f = self.to_nbt(data_version)
        f.save(path, gzipped=True)
        return path

    @classmethod
    def load(cls, path: str) -> "Schematic":
        f = nbtlib.load(path, gzipped=True)
        root = f
        if "Schematic" in root and isinstance(root["Schematic"], tag.Compound):  # v3 nesting
            root = root["Schematic"]
        w, h, l = int(root["Width"]), int(root["Height"]), int(root["Length"])
        s = cls(w, h, l)
        pal = root["Palette"]
        by_id = {int(v): str(k) for k, v in pal.items()}
        raw = bytes(np.array(root["BlockData"], dtype=np.int8).astype(np.uint8))
        vals = []
        i = 0
        n = len(raw)
        while i < n:
            v, shift = 0, 0
            while True:
                b = raw[i]
                i += 1
                v |= (b & 0x7F) << shift
                if not (b & 0x80):
                    break
                shift += 7
            vals.append(v)
        arr = np.array(vals, dtype=np.int32).reshape(h, l, w)
        s.palette, s.blocks_by_id = {AIR: 0}, [AIR]
        lut = np.zeros(max(by_id) + 1, dtype=np.int32)
        for i_, b in by_id.items():
            lut[i_] = s.pid(b)
        s.data = np.transpose(lut[arr], (2, 0, 1)).copy()
        meta = root.get("Metadata")
        if meta is not None and "WEOffsetY" in meta:
            s.ground = -int(meta["WEOffsetY"])
        return s

    def __repr__(self) -> str:
        return f"Schematic({self.w}x{self.h}x{self.l}, blocks={self.count()}, palette={len(self.palette)})"


def _to_tag(v):
    if isinstance(v, bool):
        return tag.Byte(int(v))
    if isinstance(v, int):
        return tag.Int(v)
    if isinstance(v, float):
        return tag.Float(v)
    if isinstance(v, str):
        return tag.String(v)
    if isinstance(v, dict):
        return tag.Compound({k: _to_tag(x) for k, x in v.items()})
    if isinstance(v, (list, tuple)):
        if all(isinstance(x, str) for x in v):
            return tag.List[tag.String]([tag.String(x) for x in v])
        if all(isinstance(x, dict) for x in v):
            return tag.List[tag.Compound]([_to_tag(x) for x in v])
        return tag.List[tag.Int]([tag.Int(x) for x in v])
    raise TypeError(f"unsupported NBT value {v!r}")
