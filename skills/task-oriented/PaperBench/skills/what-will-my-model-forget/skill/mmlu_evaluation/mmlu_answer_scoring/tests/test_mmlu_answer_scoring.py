from mmlu_answer_scoring import extract_label, score_predictions
def test_sentence_prediction_and_gap():
    assert extract_label("The answer is (C).") == "C"
    res=score_predictions(["A","Answer: B"],["A","C"],[0.8,0.6])
    assert res["accuracy"]==0.5 and abs(res["calibration_gap"]-0.2)<1e-9
