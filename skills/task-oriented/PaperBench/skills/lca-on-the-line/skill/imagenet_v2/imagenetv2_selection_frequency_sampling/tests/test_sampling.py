import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'scripts'))
from sample_by_frequency import sample_records
records=json.load(open(pathlib.Path(__file__).parent/'fixtures'/'normalized.json'))['records']

def test_top_images_picks_highest():
    res=sample_records(records, 'top_images', 1)
    assert [r['candidate_id'] for r in res['sampled']] == ['a2','b2']
    assert abs(res['stats']['average_selection_frequency'] - 0.85) < 1e-12

def test_threshold_filters():
    res=sample_records(records, 'threshold_0_7', 1)
    assert {r['candidate_id'] for r in res['sampled']} == {'a2','b2'}

def test_matched_frequency_uses_mid_or_bins():
    res=sample_records(records, 'matched_frequency', 1)
    assert len(res['sampled']) == 2
