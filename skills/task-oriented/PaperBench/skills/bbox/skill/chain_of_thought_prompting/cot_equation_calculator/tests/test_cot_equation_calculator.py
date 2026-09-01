from cot_equation_calculator import check_equations, safe_eval_expression


def test_safe_eval_expression():
    assert safe_eval_expression("2 * (3 + 4)") == 14


def test_detects_correct_and_incorrect_equations():
    result = check_equations("2 * 3 = 6. 5 + 6 = 10.")
    assert len(result["checks"]) == 2
    assert result["checks"][0]["is_correct"] is True
    assert result["checks"][1]["is_correct"] is False
    assert result["all_equations_correct"] is False


def test_repair_changes_only_stated_result():
    result = check_equations("5 + 6 = 10. The answer is 10.", repair=True)
    assert "5 + 6 = 11" in result["repaired_text"]
    assert "The answer is 10" in result["repaired_text"]


def test_negative_result_equation_is_checked():
    result = check_equations("A refund leaves 3 - 5 = -2 dollars.")
    assert len(result["checks"]) == 1
    assert result["checks"][0]["computed_result"] == -2
    assert result["checks"][0]["is_correct"] is True


def test_unsafe_expression_is_ignored():
    result = check_equations("__import__('os').system('id') = 0")
    assert result["checks"] == []
