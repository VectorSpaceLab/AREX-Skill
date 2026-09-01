import json
from copy import deepcopy

HUNGER_LEVELS = {'hungry', 'weak', 'fainting', 'starved'}

def _by_key(items):
    out = {}
    for idx, item in enumerate(items or []):
        key = item.get('pos') or item.get('coord') or item.get('id') or item.get('name') or str(idx)
        out[str(key)] = dict(item)
    return out

def update_memory(observation, memory=None):
    memory = deepcopy(memory) if memory else {'levels': {}}
    level_id = str(observation.get('level_id', 'unknown'))
    memory['current_level'] = level_id
    level = deepcopy(memory.get('levels', {}).get(level_id, {}))
    for field in ('monsters', 'traps', 'stairs', 'items'):
        level[field] = _by_key(observation.get(field, []))
    level['last_turn'] = observation.get('turn', level.get('last_turn', 0))
    level['message'] = observation.get('message', '')
    memory.setdefault('levels', {})[level_id] = level
    hero = dict(observation.get('hero', {}))
    memory['hero'] = hero
    memory['inventory'] = [dict(x) for x in observation.get('inventory', [])]
    monsters = list(level.get('monsters', {}).values())
    hunger = str(hero.get('hunger', '')).lower()
    hp = float(hero.get('hp', hero.get('max_hp', 1)) or 0)
    max_hp = float(hero.get('max_hp', 1) or 1)
    memory['derived_flags'] = {
        'low_hp': hp / max_hp <= 0.35,
        'hungry_or_worse': hunger in HUNGER_LEVELS,
        'fainting': hunger in {'fainting', 'starved'},
        'hostile_monster_visible': any(m.get('hostile') and not m.get('peaceful') for m in monsters),
    }
    return memory

def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('observation')
    p.add_argument('--memory')
    p.add_argument('--output', required=True)
    a = p.parse_args()
    obs = json.load(open(a.observation))
    mem = json.load(open(a.memory)) if a.memory else None
    res = update_memory(obs, mem)
    json.dump(res, open(a.output, 'w'), indent=2, sort_keys=True)
if __name__ == '__main__': main()
