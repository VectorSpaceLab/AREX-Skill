from task_config import format_instance

def test_multiple_choice_formatting():
    cfg={'task':'toy','output_type':'multiple_choice','doc_to_text':'Q: {{question}}','doc_to_target':'gold','doc_to_choice':'choices','metric_list':['accuracy']}
    inst=format_instance(cfg, {'question':'2+2?','choices':['3','4'],'gold':'4'})
    assert inst['context']=='Q: 2+2?'
    assert inst['choices']==['3','4'] and inst['target']=='4'

def test_missing_choice_rejected():
    try:
        format_instance({'task':'x','output_type':'multiple_choice','doc_to_text':'{{x}}','doc_to_target':'y','metric_list':['accuracy']},{'x':1,'y':2})
        assert False
    except ValueError as e:
        assert 'doc_to_choice' in str(e)

def test_unresolved_placeholder_rejected():
    cfg={'task':'toy','output_type':'generate_until','doc_to_text':'{{missing}}','doc_to_target':'gold','metric_list':['exact_match']}
    try:
        format_instance(cfg, {'gold':'x'})
        assert False
    except ValueError as e:
        assert 'unresolved' in str(e)
