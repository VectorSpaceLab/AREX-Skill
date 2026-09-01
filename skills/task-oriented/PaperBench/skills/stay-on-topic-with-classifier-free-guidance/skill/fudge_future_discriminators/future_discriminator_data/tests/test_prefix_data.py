import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from prefix_data import build_prefix_examples

def test_future_suffix_labels_and_no_decode_leakage():
    out = build_prefix_examples([['ship','earth','orbit']], 'future_suffix', target='earth')
    labels = [e['label'] for e in out['examples']]
    assert labels == [1,1,0], labels
    assert all('selected_token' not in e and 'final_answer' not in e for e in out['examples'])

def test_whole_sequence_labels():
    out2 = build_prefix_examples([['a','b'], ['c']], 'whole_sequence', labels=[1,0])
    assert [e['label'] for e in out2['examples']] == [1,1,0]
