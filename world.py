from typing import Dict, Optional, Tuple

import numpy as np
from gdpc import Editor
from gdpc import geometry as GEO

from helper import AIR_IDS, WATER_IDS, NON_SOLID_IDS, blk

editor = Editor(buffering=False)
BUILD_AREA = editor.getBuildArea()
STARTX, _, STARTZ = BUILD_AREA.begin
WORLDSLICE = editor.loadWorldSlice(BUILD_AREA.toRect(), cache=True)
heights = WORLDSLICE.heightmaps['MOTION_BLOCKING_NO_LEAVES']
SEA_LEVEL = 63

def cub(p1, p2, block):
    GEO.placeCuboid(editor, p1, p2, block)

class Terrain:
    def __init__(self, heights_arr: np.ndarray, startx: int, startz: int, sea_level: int):
        self.H = heights_arr
        self.SX = startx
        self.SZ = startz
        self.SEA = sea_level
        self._seabed_cache: Dict[Tuple[int, int], int] = {}

    def in_slice(self, wx: int, wz: int) -> bool:
        lx, lz = wx - self.SX, wz - self.SZ
        return 0 <= lx < self.H.shape[0] and 0 <= lz < self.H.shape[1]

    def local_coords(self, wx: int, wz: int) -> Optional[Tuple[int, int]]:
        lx, lz = wx - self.SX, wz - self.SZ
        if 0 <= lx < self.H.shape[0] and 0 <= lz < self.H.shape[1]:
            return lx, lz
        return None

    def surface_y(self, wx: int, wz: int) -> Optional[int]:
        lc = self.local_coords(wx, wz)
        if lc is None:
            return None
        lx, lz = lc
        return int(self.H[lx, lz])

    def block_id_at(self, wx: int, wy: int, wz: int) -> str:
        block = editor.getBlock((wx, wy, wz))
        return getattr(block, 'id', str(block))

    def seabed_y(self, wx: int, wz: int, y_start: Optional[int] = None, max_depth: int = 60) -> int:
        key = (wx, wz)
        if key in self._seabed_cache:
            return self._seabed_cache[key]
        if y_start is None:
            y_start = self.SEA + 8
        y_min = max(1, y_start - max_depth)
        for y in range(y_start, y_min - 1, -1):
            bid = self.block_id_at(wx, y, wz)
            if bid not in WATER_IDS and bid not in AIR_IDS and bid not in NON_SOLID_IDS:
                self._seabed_cache[key] = y
                return y
        self._seabed_cache[key] = y_min
        return y_min

    def support_base_y(self, wx: int, wz: int) -> int:
        sy = self.surface_y(wx, wz)
        if sy is not None and sy > self.SEA:
            return sy
        return self.seabed_y(wx, wz)


TERR = Terrain(heights, STARTX, STARTZ, SEA_LEVEL)
