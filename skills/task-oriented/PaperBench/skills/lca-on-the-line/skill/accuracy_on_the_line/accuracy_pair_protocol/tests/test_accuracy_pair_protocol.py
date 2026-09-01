import json, tempfile
from pathlib import Path
from accuracy_pairs import validate_records

def test_valid_records_are_sorted_and_ranged():
    result=validate_records([
        {"model_id":"b","id_accuracy":0.8,"ood_accuracy":0.7},
        {"model_id":"a","id_accuracy":0.6,"ood_accuracy":0.5},
    ], "unit")
    assert [r["model_id"] for r in result["records"]] == ["a", "b"]
    assert result["id_range"] == [0.6, 0.8]
    assert result["provenance"] == "unit"

def test_invalid_accuracy_rejected():
    try:
        validate_records([{"model_id":"a","id_accuracy":1.2,"ood_accuracy":0.5},{"model_id":"b","id_accuracy":0.8,"ood_accuracy":0.6}])
    except ValueError as exc:
        assert "[0, 1]" in str(exc)
    else:
        raise AssertionError("invalid accuracy accepted")


def test_duplicate_model_id_rejected():
    try:
        validate_records([
            {"model_id":"a","id_accuracy":0.7,"ood_accuracy":0.6},
            {"model_id":"a","id_accuracy":0.8,"ood_accuracy":0.7},
        ])
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate model id accepted")
