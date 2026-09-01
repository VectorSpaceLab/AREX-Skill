from verifier_search import select_predictions


def test_top_score_and_top_k_vote_modes():
    candidates = [
        {"problem_id": "0", "candidate_id": "0_a", "extracted_answer": "10", "gold_answer": "10", "verifier_score": 0.9},
        {"problem_id": "0", "candidate_id": "0_b", "extracted_answer": "11", "gold_answer": "10", "verifier_score": 0.8},
        {"problem_id": "0", "candidate_id": "0_c", "extracted_answer": "11", "gold_answer": "10", "verifier_score": 0.7},
    ]
    assert select_predictions(candidates, mode="top_score")[0]["selected_answer"] == "10"
    assert select_predictions(candidates, mode="top_k_vote", top_k=3)[0]["selected_answer"] == "11"


def test_tie_breaking_is_deterministic_by_candidate_id():
    candidates = [
        {"problem_id": "0", "candidate_id": "0_b", "extracted_answer": "8", "gold_answer": "8", "verifier_score": 0.5},
        {"problem_id": "0", "candidate_id": "0_a", "extracted_answer": "7", "gold_answer": "8", "verifier_score": 0.5},
    ]
    pred = select_predictions(candidates, mode="top_score")[0]
    assert pred["selected_candidate_id"] == "0_a"
    assert pred["selected_answer"] == "7"
