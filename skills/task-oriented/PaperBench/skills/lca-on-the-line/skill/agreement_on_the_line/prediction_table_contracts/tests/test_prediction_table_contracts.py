import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "prediction_table_contracts.py"
spec = importlib.util.spec_from_file_location("prediction_table_contracts", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample_table():
    return {
        "models": ["a", "b", "c"],
        "id_labels": [0, 1, 1, 0],
        "id_predictions": {"a": [0, 1, 1, 0], "b": [0, 1, 0, 0], "c": [1, 1, 1, 0]},
        "ood_predictions": {"a": [0, 1, 0], "b": [0, 0, 0], "c": [1, 1, 0]},
        "ood_labels": [0, 1, 0],
    }


def test_valid_table_separates_ood_labels():
    normalized = mod.validate_prediction_table(sample_table(), require_ood_labels=True)
    assert normalized["metadata"]["model_count"] == 3
    assert normalized["metadata"]["ood_labels_allowed_for_estimator"] is False
    assert normalized["evaluation_only"]["ood_labels"] == [0, 1, 0]


def test_rejects_length_mismatch():
    table = sample_table()
    table["ood_predictions"]["c"] = [1]
    try:
        mod.validate_prediction_table(table)
    except ValueError as exc:
        assert "OOD prediction length mismatch" in str(exc)
    else:
        raise AssertionError("expected mismatch failure")
