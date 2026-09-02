import json
URGENT = {'hungry','weak','fainting','starved'}

def choose_survival_action(memory):
    hero = memory.get('hero', {})
    hunger = str(hero.get('hunger','normal')).lower()
    turn = int(hero.get('turn', memory.get('turn', 0)) or 0)
    if hunger not in URGENT:
        return {'action': {'type':'none'}, 'reason':'no_survival_pressure'}
    for corpse in memory.get('visible_corpses', []):
        if corpse.get('safe') and int(corpse.get('age', 999)) <= 50:
            return {'action': {'type':'eat_corpse', 'target': corpse.get('name','corpse')}, 'reason':'safe_fresh_corpse'}
    for item in memory.get('inventory', []):
        if item.get('category') == 'food' or item.get('food'):
            return {'action': {'type':'eat_inventory', 'target': item.get('name','food')}, 'reason':'inventory_food'}
    last_prayer = int(memory.get('last_prayer_turn', -9999))
    if hunger in {'fainting','starved'} and turn - last_prayer >= 500:
        return {'action': {'type':'pray'}, 'reason':'starvation_prayer_cooldown_ready'}
    return {'action': {'type':'none'}, 'reason':'no_safe_resource'}

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('memory'); p.add_argument('--output', required=True)
    a=p.parse_args(); json.dump(choose_survival_action(json.load(open(a.memory))), open(a.output,'w'), indent=2)
if __name__ == '__main__': main()
