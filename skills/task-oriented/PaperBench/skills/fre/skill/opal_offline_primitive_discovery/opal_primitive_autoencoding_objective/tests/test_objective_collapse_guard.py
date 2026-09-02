from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from primitive_objective import train_reduced_objective


def test_decoder_does_not_remain_latent_collapsed():
    payload = {'segments': [
        {'actions': [-2, -2, -2], 'initial_state': -2},
        {'actions': [2, 2, 2], 'initial_state': 2},
    ]}
    result = train_reduced_objective(payload, steps=3)
    assert result['params_before'] != result['params_after']
    assert abs(result['params_after']['1'] - result['params_after']['0']) > 1.0


if __name__ == '__main__':
    test_decoder_does_not_remain_latent_collapsed()
