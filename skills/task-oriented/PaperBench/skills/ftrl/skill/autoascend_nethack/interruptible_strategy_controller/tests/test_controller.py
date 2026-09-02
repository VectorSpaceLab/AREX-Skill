from controller import select_strategy

def test_emergency_interrupts_combat():
    memory = {'derived_flags': {'low_hp': True, 'hostile_monster_visible': True}}
    strategies = [
        {'name':'explore','priority':1,'predicate':'always','actions':[{'type':'move'}]},
        {'name':'combat','priority':5,'predicate':'hostile_monster_visible','actions':[{'type':'melee','direction':'E'}]},
        {'name':'heal','priority':9,'predicate':'low_hp','actions':[{'type':'apply','item':'healing'}]},
    ]
    result = select_strategy(memory, strategies, previous='combat')
    assert result['selected_strategy'] == 'heal'
    assert result['interrupted'] is True
    assert isinstance(result['actions'][0], dict)
