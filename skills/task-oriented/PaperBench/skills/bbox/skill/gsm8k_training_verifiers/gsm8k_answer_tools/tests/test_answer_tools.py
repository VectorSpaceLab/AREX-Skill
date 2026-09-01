from answer_tools import (
    INVALID_ANSWER,
    canonicalize_answer,
    extract_answer,
    label_candidate,
    validate_calculator_annotations,
)


def test_extract_and_canonicalize_answers():
    assert canonicalize_answer("1,234.0") == "1234"
    assert canonicalize_answer("-7.50") == "-7.5"
    assert extract_answer("Reasoning\n#### 1,234") == "1234"
    assert extract_answer("Reasoning only") == INVALID_ANSWER


def test_calculator_validation_and_labeling():
    checks = validate_calculator_annotations("Natalia sold 48/2 = <<48/2=24>>24.")
    assert len(checks) == 1
    assert checks[0]["ok"] is True
    bad = validate_calculator_annotations("Broken <<48/2=25>>")
    assert bad[0]["ok"] is False
    label = label_candidate("Candidate\n#### 72", "Gold\n#### 72")
    assert label["correct"] is True


def test_edge_case_numeric_and_unsafe_annotation_regression():
    assert extract_answer("Work\n#### 1,200.0") == "1200"
    assert extract_answer("Work\n#### -3.50") == "-3.5"
    assert canonicalize_answer("0.00") == "0"
    unsafe = validate_calculator_annotations('Bad <<__import__("os")=1>>')
    assert all(item["ok"] is False for item in unsafe)
    assert validate_calculator_annotations("Good <<(2+3)*4=20>>")[0]["ok"] is True
