from candidate_generation import generate_candidates, perturb_answer


def test_generate_mixed_candidates():
    examples = [{"question": "Q?", "answer": "Step <<1+1=2>>2.\n#### 2"}]
    candidates, summaries = generate_candidates(examples, negatives_per_problem=2)
    assert len(candidates) == 3
    assert summaries[0]["positive_count"] == 1
    assert summaries[0]["negative_count"] == 2
    assert candidates[0]["source"] == "gold_solution"


def test_perturb_answer_changes_final_marker():
    changed = perturb_answer("Reasoning\n#### 72", 1)
    assert "#### 73" in changed


def test_each_problem_has_positive_and_negative_candidates():
    examples = [
        {"question": "Q1?", "answer": "Step <<1+1=2>>2.\n#### 2"},
        {"question": "Q2?", "answer": "Step <<2+3=5>>5.\n#### 5"},
    ]
    candidates, summaries = generate_candidates(examples, negatives_per_problem=3)
    assert len(candidates) == 8
    assert all(item["positive_count"] >= 1 for item in summaries)
    assert all(item["negative_count"] >= 1 for item in summaries)
