import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sbcc import diagnose

def test_support_fraction():
    out=diagnose({'true_log_probs':[-1,-3], 'posterior_sample_log_probs':[[-4,-2,-1],[-5,-4,-3]], 'threshold':-2})
    assert out['ground_truth_in_support_fraction']==0.5
    assert len(out['coverage'])==4

if __name__=='__main__': test_support_fraction()
