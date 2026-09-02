import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from evaluate_accuracy import compute_accuracy
records=json.load(open(pathlib.Path(__file__).parent/'fixtures'/'sample.json'))['sampled']

def test_topk_and_drop():
    m=compute_accuracy(records, original_top1=0.75)
    assert m['top1'] == 0.5
    assert m['top5'] == 1.0
    assert m['top1_drop'] == 0.25
