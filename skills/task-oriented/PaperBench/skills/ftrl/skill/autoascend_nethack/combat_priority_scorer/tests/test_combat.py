from combat import rank_actions

def test_floating_eye_and_low_hp_rules():
    hero={'hp':2,'max_hp':20}
    monsters=[{'name':'floating eye','hostile':True,'adjacent':True,'hazard':'floating_eye'}]
    actions=[{'type':'melee'},{'type':'heal'},{'type':'elbereth'}]
    result=rank_actions(hero, monsters, actions)
    assert result['selected_action']['type'] == 'heal'
    melee = [r for r in result['ranked_actions'] if r['action']['type']=='melee'][0]
    assert 'avoid_contact_hazard' in melee['reasons']

def test_peaceful_blocker_penalizes_ranged():
    result=rank_actions({'hp':10,'max_hp':20}, [{'hostile':True},{'peaceful':True,'line_of_fire':True}], [{'type':'ranged'},{'type':'melee'}])
    assert result['selected_action']['type'] == 'melee'
