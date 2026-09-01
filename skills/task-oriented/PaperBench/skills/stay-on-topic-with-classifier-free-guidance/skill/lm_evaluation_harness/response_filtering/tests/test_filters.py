from filters import apply_pipeline

def test_regex_majority():
    preds, tr=apply_pipeline([['The answer is 4','The answer is 4','The answer is 3']], [{'function':'regex','regex_pattern':r'The answer is (\d+)'},{'function':'majority_vote'},{'function':'take_first'}])
    assert preds==['4'] and tr[0][-1]['values']==['4']

def test_no_regex_match_returns_empty_string():
    preds, _=apply_pipeline([['no answer here']], [{'function':'regex','regex_pattern':r'Answer: ([A-Z])'},{'function':'take_first'}])
    assert preds==['']
