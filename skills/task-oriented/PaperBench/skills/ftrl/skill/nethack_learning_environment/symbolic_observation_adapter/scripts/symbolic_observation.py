from __future__ import annotations

def parse_grid(grid, message='', blstats=None, inventory=None):
    if isinstance(grid, str):
        rows = [line.rstrip('\n') for line in grid.strip('\n').splitlines() if line]
    else:
        rows = list(grid)
    if not rows:
        raise ValueError('grid is empty')
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError('grid rows must have equal width')
    agent = None
    stairs = []
    walls = set()
    walkable = []
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == '@': agent = [x, y]
            if ch == '>': stairs.append([x, y])
            if ch in '|-': walls.add((x, y))
            if ch not in '|-': walkable.append([x, y])
    if agent is None:
        raise ValueError('missing NetHack hero @')
    return {'height': len(rows), 'width': width, 'agent': agent, 'stairs': stairs,
            'walkable_count': len(walkable), 'message': message, 'blstats': blstats or {},
            'inventory': inventory or [], 'raw_rows': rows}

def manhattan_to_stairs(obs):
    if not obs.get('stairs'):
        return None
    ax, ay = obs['agent']
    return min(abs(ax-sx)+abs(ay-sy) for sx, sy in obs['stairs'])
