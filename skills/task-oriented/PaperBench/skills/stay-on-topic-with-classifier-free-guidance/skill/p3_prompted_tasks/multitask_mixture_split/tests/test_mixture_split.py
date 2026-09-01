from mixture_split import make_split


def test_heldout_never_in_train():
    rec=[{'dataset_id':'a','task_family':'sentiment','template_id':'t1'}, {'dataset_id':'b','task_family':'topic','template_id':'t2'}]
    s=make_split(rec, heldout_dataset_ids=['b'])
    assert [r['dataset_id'] for r in s['train']]==['a']
    assert [r['dataset_id'] for r in s['eval']]==['b']
    assert s['diagnostics']['leaked_heldout_dataset_ids']==[]


def test_template_counts_recorded():
    rec=[{'dataset_id':'a','task_family':'x','template_id':'t1'}, {'dataset_id':'a','task_family':'x','template_id':'t2'}]
    assert set(make_split(rec)['diagnostics']['template_counts']['a'])=={'t1','t2'}
