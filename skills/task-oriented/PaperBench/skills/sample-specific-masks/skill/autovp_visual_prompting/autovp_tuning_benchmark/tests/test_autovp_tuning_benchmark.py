from autovp_tuning_benchmark import select_best, summarize

def test_select_and_summary():
    best=select_best([{'name':'b','score':0.7},{'name':'a','score':0.7},{'name':'c','score':0.6}])
    assert best['name']=='a'
    s=summarize('synthetic','accuracy',0.806,best,True)
    assert s['proxy'] and s['paper_value']==0.806
