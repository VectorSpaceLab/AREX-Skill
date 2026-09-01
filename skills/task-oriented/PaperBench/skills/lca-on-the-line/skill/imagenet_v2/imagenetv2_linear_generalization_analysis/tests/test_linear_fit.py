import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from linear_fit import analyze_pairs
pairs=json.load(open(pathlib.Path(__file__).parent/'fixtures'/'model_pairs.json'))

def test_fit_preserves_rank_and_positive_slope():
    a=analyze_pairs(pairs)
    assert a['slope'] > 1.0
    assert a['rank_agreement'] == 1.0
    assert a['mean_gap'] > 0
