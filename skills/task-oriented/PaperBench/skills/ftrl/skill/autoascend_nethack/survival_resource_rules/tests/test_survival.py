from survival import choose_survival_action

def test_safe_corpse_before_ration():
    mem={'hero':{'hunger':'Hungry'}, 'visible_corpses':[{'name':'jackal','safe':True,'age':10}], 'inventory':[{'name':'ration','category':'food'}]}
    assert choose_survival_action(mem)['action']['type'] == 'eat_corpse'

def test_stale_corpse_rejected_and_prayer_cooldown():
    mem={'hero':{'hunger':'Fainting','turn':700}, 'visible_corpses':[{'safe':True,'age':100}], 'last_prayer_turn':100}
    assert choose_survival_action(mem)['action']['type'] == 'pray'
