import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from train_gaussian import train

def test_training_reduces_loss_and_changes_params():
    out=train({'theta':[0.1,0.2,0.3], 'x':[0.2,0.25,0.35], 'observation':0.25, 'mean':0.0, 'log_std':0.0, 'steps':25, 'lr':0.05})
    assert out['loss_after'] < out['loss_before']
    assert out['params_before'] != out['params_after']

if __name__=='__main__': test_training_reduces_loss_and_changes_params()
