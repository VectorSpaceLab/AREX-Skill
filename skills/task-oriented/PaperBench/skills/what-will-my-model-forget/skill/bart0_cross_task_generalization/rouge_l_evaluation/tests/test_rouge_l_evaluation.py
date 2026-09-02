from rouge_l import rouge_l_f1, evaluate_pairs

def test_exact_match_scores_one():
    assert rouge_l_f1('What is cold?', 'what is cold') == 1.0

def test_partial_overlap_between_zero_and_one():
    score=rouge_l_f1('cold ice', 'what is cold')
    assert 0 < score < 1

def test_aggregate_percentage():
    out=evaluate_pairs([{'prediction':'a b','reference':'a b'},{'prediction':'x','reference':'a'}])
    assert out['score'] == 50.0
