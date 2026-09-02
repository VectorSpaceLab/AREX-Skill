from state_memory import update_memory

def test_memory_persists_and_flags():
    first = {'level_id':'1','hero':{'hp':10,'max_hp':20,'hunger':'normal'},'traps':[{'pos':[1,2],'type':'pit'}]}
    mem = update_memory(first)
    second = {'level_id':'2','hero':{'hp':2,'max_hp':20,'hunger':'Hungry'},'monsters':[{'name':'jackal','hostile':True,'pos':[3,3]}]}
    mem = update_memory(second, mem)
    assert '1' in mem['levels'] and '2' in mem['levels']
    assert mem['derived_flags']['low_hp'] is True
    assert mem['derived_flags']['hungry_or_worse'] is True
    assert mem['derived_flags']['hostile_monster_visible'] is True
