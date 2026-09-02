import json

def rank_actions(hero, monsters, actions, weights=None):
    weights = {'damage': 5, 'survival': 8, 'hazard_penalty': 20, 'blocker_penalty': 15, **(weights or {})}
    low_hp = (hero.get('hp', 1) / max(hero.get('max_hp', 1), 1)) <= 0.35
    hostile = [m for m in monsters if m.get('hostile') and not m.get('peaceful')]
    hazardous_adjacent = any(m.get('adjacent') and m.get('hazard') in ('floating_eye','gas_spore') for m in hostile)
    peaceful_blocker = any(m.get('peaceful') and m.get('line_of_fire') for m in monsters)
    ranked=[]
    for action in actions:
        kind = action.get('type')
        score=0; reasons=[]
        if low_hp and kind in ('heal','flee'):
            score += weights['survival']; reasons.append('low_hp_survival')
        if hostile and kind in ('melee','ranged','zap'):
            score += weights['damage']; reasons.append('hostile_damage')
        if hazardous_adjacent and kind == 'melee':
            score -= weights['hazard_penalty']; reasons.append('avoid_contact_hazard')
        if peaceful_blocker and kind in ('ranged','zap'):
            score -= weights['blocker_penalty']; reasons.append('peaceful_line_of_fire_blocker')
        if kind == 'elbereth' and hostile:
            score += 2; reasons.append('defensive_option')
        ranked.append({'action': action, 'score': score, 'reasons': reasons})
    ranked.sort(key=lambda r: (-r['score'], str(r['action'].get('type','')), str(r['action'].get('name',''))))
    return {'ranked_actions': ranked, 'selected_action': ranked[0]['action'] if ranked else {'type':'wait'}}

def main():
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('scenario'); p.add_argument('--output', required=True)
    a=p.parse_args(); s=json.load(open(a.scenario)); res=rank_actions(s.get('hero',{}), s.get('monsters',[]), s.get('actions',[]), s.get('weights')) ; json.dump(res, open(a.output,'w'), indent=2)
if __name__ == '__main__': main()
