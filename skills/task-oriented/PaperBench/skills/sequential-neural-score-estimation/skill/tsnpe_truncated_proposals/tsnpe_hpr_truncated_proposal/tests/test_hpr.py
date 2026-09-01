import json, tempfile, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from hpr import truncate

def test_quantile_and_acceptance():
    out=truncate({'posterior_log_probs':[-4,-1,0,-9], 'prior_samples':[-2,-1,0,1], 'prior_log_probs_for_samples':[-5,-1,-0.5,-7], 'epsilon':0.25})
    assert out['acceptance_rate']==0.75
    assert out['accepted_samples']==[-2,-1,0]
    assert out['mechanism_checks']['proposal_prior_proportional_inside_support']

if __name__=='__main__': test_quantile_and_acceptance()


def test_rejects_empty_truncated_support():
    try:
        truncate({'posterior_log_probs':[10], 'prior_samples':[0], 'prior_log_probs_for_samples':[-10], 'epsilon':0})
    except ValueError as exc:
        assert 'accepted no samples' in str(exc)
    else:
        raise AssertionError('empty support was not rejected')
