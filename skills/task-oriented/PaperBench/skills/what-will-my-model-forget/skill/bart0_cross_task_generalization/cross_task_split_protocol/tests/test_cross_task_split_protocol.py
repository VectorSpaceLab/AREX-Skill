from split_protocol import make_split

def records():
    return [{'task_id':'t1','category':'qg','dataset':'a'},{'task_id':'t2','category':'qa','dataset':'b'},{'task_id':'t3','category':'qg','dataset':'c'}]

def test_leave_one_task_has_no_leakage():
    out=make_split(records(), 'leave_one_task', 't2')
    assert out['unseen_tasks'] == ['t2']
    assert 't2' not in out['seen_tasks']
    assert out['ok']

def test_leave_one_category_excludes_all_category_tasks():
    out=make_split(records(), 'leave_one_category', 'qg')
    assert out['unseen_tasks'] == ['t1','t3']
    assert out['seen_tasks'] == ['t2']
