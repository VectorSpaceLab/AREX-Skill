from scienceqa_style_evaluation import canonicalize, evaluate_predictions

def test_extracts_option_letter_from_sentence():
    assert canonicalize("The answer is B.", {"A":"rock", "B":"plant"}) == "B"

def test_evaluates_accuracy():
    out = evaluate_predictions([{"id":"1", "raw_answer":"plant", "choices":{"A":"animal", "B":"plant"}, "label":"B"}])
    assert out["accuracy"] == 1.0
