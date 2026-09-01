from harness_checks import validate_result


def test_proxy_result_requires_mechanism_checks_and_metric():
    result = {'schema_version':1,'paper_id':'x','experiment':'e','is_proxy':True,'sample_count':1,'metrics':{'accuracy':1.0},'paper_target':{'metric':'accuracy','value':1.0},'commands':['python run.py'],'mechanism_checks':{'ran':True}}
    assert validate_result(result)['ok'] is True


def test_missing_mechanism_checks_fails():
    result = {'schema_version':1,'paper_id':'x','experiment':'e','is_proxy':True,'sample_count':1,'metrics':{'accuracy':1.0},'paper_target':{},'commands':['cmd'],'mechanism_checks':{}}
    assert validate_result(result)['ok'] is False
