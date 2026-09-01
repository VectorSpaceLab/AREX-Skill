import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from recovery_evaluation import hit_rate, mechanism_ok

def test_hit_rate_and_mechanism_ok():
    assert hit_rate([{'tokens':['space','ship'], 'target_words':['space']}])==1.0
    assert mechanism_ok({'attribute_model_used':1,'latent_perturbation_executed':1,'kl_regularization_used':1,'candidate_reranking_executed':1,'base_model_frozen':1})

def test_mechanism_missing_required_flag_fails():
    assert not mechanism_ok({'attribute_model_used':1})
