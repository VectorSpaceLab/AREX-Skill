import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from candidate_pool import normalize_records

def test_normalize_sorts_and_validates():
    records=json.load(open(pathlib.Path(__file__).parent/'fixtures'/'candidates.json'))
    out=normalize_records(records)
    assert [r['candidate_id'] for r in out] == ['c1','c2']
    assert out[0]['selection_frequency'] == 0.7

def test_reject_bad_frequency():
    try:
        normalize_records([{'candidate_id':'x','class_id':'a','label':'a','selection_frequency':1.2,'predictions':['a']}])
    except ValueError as exc:
        assert 'outside' in str(exc)
    else:
        raise AssertionError('expected ValueError')


def test_reject_missing_predictions():
    try:
        normalize_records([{'candidate_id':'x','class_id':'a','label':'a','selection_frequency':0.5}])
    except ValueError as exc:
        assert 'missing' in str(exc)
    else:
        raise AssertionError('expected ValueError')
