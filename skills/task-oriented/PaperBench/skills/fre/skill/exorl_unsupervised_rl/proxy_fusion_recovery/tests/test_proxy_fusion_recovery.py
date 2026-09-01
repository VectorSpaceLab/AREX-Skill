import tempfile, os
from proxy_train import run

def test_proxy_training_changes_parameter():
    root=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
    with tempfile.TemporaryDirectory() as d:
        res=run(root,d)
        assert res['mechanism_checks']['reduced_training_executed'] is True
        assert res['trace']['params_before'] != res['trace']['params_after']
        assert res['metrics']['fusion_proxy_score'] > 0
