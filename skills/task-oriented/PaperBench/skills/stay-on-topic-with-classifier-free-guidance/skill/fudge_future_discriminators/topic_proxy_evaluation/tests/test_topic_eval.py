import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from topic_eval import evaluate_topic_proxy

def test_topic_metrics_and_mechanism_checks():
    trace={'earth': {'future_probability':0.9, 'adjusted_logit':1.0, 'probability':0.7}, 'tea': {'future_probability':0.1, 'adjusted_logit':0.0, 'probability':0.3}}
    train={'optimizer_step_executed': True, 'params_before': {'w':0.0}, 'params_after': {'w':1.0}, 'loss_before':1.0, 'loss_after':0.5}
    out=evaluate_topic_proxy(['earth','tea'], ['earth','orbit'], trace, train, prefix_examples=[1])
    assert out['metrics']['topic_token_rate'] == 0.5
    assert out['mechanism_checks']['future_probabilities_used']
    assert out['mechanism_checks']['parameters_changed']

def test_missing_trace_fails_mechanism():
    out=evaluate_topic_proxy(['earth'], ['earth'], decoder_trace={}, training_trace=None, prefix_examples=[])
    assert out['metrics']['topic_token_rate'] == 1.0
    assert not out['mechanism_checks']['future_probabilities_used']
