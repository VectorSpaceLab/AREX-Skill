from evaluation import evaluate_predictions


def test_evaluate_predictions_reports_solve_rate():
    result = evaluate_predictions(
        [
            {"problem_id": "0", "selected_answer": "2", "gold_answer": "2"},
            {"problem_id": "1", "selected_answer": "4", "gold_answer": "5"},
        ]
    )
    assert result["sample_count"] == 2
    assert result["correct_count"] == 1
    assert result["solve_rate"] == 0.5


def test_evaluate_predictions_handles_empty_input():
    result = evaluate_predictions([])
    assert result["sample_count"] == 0
    assert result["correct_count"] == 0
    assert result["solve_rate"] == 0.0
