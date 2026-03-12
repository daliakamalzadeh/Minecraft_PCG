import random
from typing import Optional

from gdpc import Block

def blk(block_id: str, **props):
    return Block(block_id, props) if props else Block(block_id)


B = {
    'dark_oak_log': blk('dark_oak_log'),
    'stripped_spruce_log': blk('stripped_spruce_log'),
    'dark_oak_planks': blk('dark_oak_planks'),
    'spruce_planks': blk('spruce_planks'),
    'cherry_planks': blk('cherry_planks'),
    'cherry_stairs': blk('cherry_stairs'),
    'cherry_slab': blk('cherry_slab'),
    'dark_oak_fence': blk('dark_oak_fence'),
    'paper': blk('white_stained_glass_pane'),
    'air': blk('air'),
    'stone_bricks': blk('stone_bricks'),
    'mossy_stone_bricks': blk('mossy_stone_bricks'),
    'polished_andesite': blk('polished_andesite'),
    'smooth_stone': blk('smooth_stone'),
    'dirt_path': blk('dirt_path'),
    'mossy_cobblestone': blk('mossy_cobblestone'),
    'lantern': blk('lantern'),
    'barrel': blk('barrel'),
    'potted_cherry': blk('potted_cherry_sapling'),
}

AIR    = B['air']
STONE  = B['stone_bricks']
MOSSY  = B['mossy_stone_bricks']
ANDESITE = B['polished_andesite']

WATER_IDS = {
    'minecraft:water',
    'minecraft:bubble_column',
    'minecraft:kelp',
    'minecraft:kelp_plant',
    'minecraft:seagrass',
    'minecraft:tall_seagrass',
}
AIR_IDS = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
NON_SOLID_IDS = {
    'minecraft:oak_leaves', 'minecraft:spruce_leaves', 'minecraft:birch_leaves',
    'minecraft:jungle_leaves', 'minecraft:acacia_leaves', 'minecraft:dark_oak_leaves',
    'minecraft:cherry_leaves', 'minecraft:azalea_leaves', 'minecraft:flowering_azalea_leaves',
    'minecraft:grass', 'minecraft:tall_grass', 'minecraft:fern', 'minecraft:large_fern',
    'minecraft:vine',
}
SAFE_OVERWRITE = AIR_IDS | {
    'minecraft:grass', 'minecraft:tall_grass', 'minecraft:fern', 'minecraft:large_fern',
    'minecraft:vine', 'minecraft:oak_leaves', 'minecraft:cherry_leaves',
    'minecraft:azalea_leaves', 'minecraft:flowering_azalea_leaves',
}

def facing_vectors(facing: str):
    if facing == 'south':
        return (0, -1), (1, 0)
    if facing == 'north':
        return (0, 1), (-1, 0)
    if facing == 'east':
        return (1, 0), (0, 1)
    if facing == 'west':
        return (-1, 0), (0, -1)
    raise ValueError(f'Unknown facing: {facing}')


def rot(ox: int, oz: int, fwd: tuple, right: tuple, df: int, dr: int):
    return ox + fwd[0] * df + right[0] * dr, oz + fwd[1] * df + right[1] * dr


def clamp_entrance_offset(w: int, d: int, facing: str, offset: int) -> int:
    max_shift = max(0, ((w if facing in ('south', 'north') else d) // 2) - 3)
    return max(-max_shift, min(max_shift, offset))


def front_origin(wx: int, wz: int, w: int, d: int, facing: str, entrance_offset: int = 0):
    fwd, right = facing_vectors(facing)
    entrance_offset = clamp_entrance_offset(w, d, facing, entrance_offset)
    if facing in ('south', 'north'):
        door_cx = wx + w // 2 + right[0] * entrance_offset
        door_cz = wz if facing == 'south' else wz + d - 1
    else:
        door_cz = wz + d // 2 + right[1] * entrance_offset
        door_cx = wx + w - 1 if facing == 'east' else wx
    return door_cx, door_cz, fwd, right

def make_rng(seed: Optional[int] = None):
    if seed is None:
        seed = random.randrange(1_000_000_000)
    rng = random.Random(seed)
    print(f'[PCG] Seed = {seed}')
    return rng, seed

class PCGState:
    """Holds all mutable global configuration used across modules."""

    def __init__(self):
        self.rng: random.Random = None
        self.STYLE: dict = {}
        self.FACING: str = 'south'
        self.WIDTH: int = 19
        self.DEPTH: int = 17
        self.HEIGHT: int = 5
        
    def gs_front_origin(self, wx: int, wz: int, w: int, d: int):
        offset = self.STYLE.get('entrance_offset', 0)
        return front_origin(wx, wz, w, d, self.FACING, offset)


STATE = PCGState()
