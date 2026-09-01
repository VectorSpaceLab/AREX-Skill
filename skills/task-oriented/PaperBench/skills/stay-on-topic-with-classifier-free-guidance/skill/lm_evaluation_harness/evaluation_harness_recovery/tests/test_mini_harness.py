from mini_harness import run_eval

def test_two_item_eval():
    cfg={'task':'toy','output_type':'multiple_choice','doc_to_text':'Q: {{question}}','doc_to_target':'gold','doc_to_choice':'choices','metric_list':['accuracy'],'choice_scores':{'A':0.0,'B':1.0}}
    res=run_eval(cfg,[{'question':'x','choices':['A','B'],'gold':'B'}])
    assert res['metrics']['accuracy']==1.0 and res['sample_count']==1
