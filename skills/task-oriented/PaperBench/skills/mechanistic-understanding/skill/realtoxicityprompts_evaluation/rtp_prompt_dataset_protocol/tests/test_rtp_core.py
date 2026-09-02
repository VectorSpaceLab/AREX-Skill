from rtp_core import *

def test_proxy_metrics_ordering():
    p,g,s,m=run_proxy_experiment(k=3)
    assert len(g)==12
    assert all(0 <= r['toxicity'] <= 1 for r in s)
    assert m['toxic']['expected_max_toxicity'] > m['non_toxic']['expected_max_toxicity']
    assert m['toxic']['toxicity_probability'] >= m['non_toxic']['toxicity_probability']

def test_threshold_boundary():
    p=normalize_prompts([{'prompt_id':'x','prompt_text':'x','prompt_toxicity':0.5}])
    assert p[0]['prompt_group']=='toxic'
