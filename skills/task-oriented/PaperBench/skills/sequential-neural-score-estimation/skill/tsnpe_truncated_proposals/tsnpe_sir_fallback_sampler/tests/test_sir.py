import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sir import run_sir

def test_sir_weights_and_ess():
    out=run_sir({'candidate_samples':[0,1,2], 'log_prior':[0,0,0], 'log_proposal':[0,-1,-2], 'num_samples':2, 'seed':3})
    assert len(out['selected_samples'])==2
    assert abs(sum(out['normalized_weights'])-1)<1e-12
    assert out['effective_sample_size'] < 3

if __name__=='__main__': test_sir_weights_and_ess()


def test_degenerate_weights_report_low_ess():
    out=run_sir({'candidate_samples':[0,1,2], 'log_prior':[0,0,0], 'log_proposal':[0,-5,-10], 'num_samples':2, 'seed':1})
    assert out['effective_sample_size'] < 1.1
