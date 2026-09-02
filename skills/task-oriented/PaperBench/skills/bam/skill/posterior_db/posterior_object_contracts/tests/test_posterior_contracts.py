import json
import tempfile
from pathlib import Path

from posterior_contracts import normalize_contract


def test_normalizes_valid_contract_and_reports_missing_link():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "posteriors").mkdir()
        (root / "models" / "info").mkdir(parents=True)
        (root / "data" / "info").mkdir(parents=True)
        (root / "reference_posteriors" / "info").mkdir(parents=True)
        (root / "reference_posteriors" / "summary_statistics" / "mean_value" / "info").mkdir(parents=True)
        (root / "posteriors" / "demo.json").write_text(json.dumps({
            "name": "demo",
            "model_name": "m",
            "data_name": "d",
            "reference_posterior_name": "r",
            "dimensions": {"alpha": 1, "beta": [2]}
        }))
        (root / "models" / "info" / "m.info.json").write_text("{}")
        (root / "data" / "info" / "d.info.json").write_text("{}")
        (root / "reference_posteriors" / "summary_statistics" / "mean_value" / "info" / "r.info.json").write_text("{}")
        result = normalize_contract(root, "demo")
        assert result["valid"] is True
        assert result["total_dimension"] == 3
        assert result["linked_paths"]["reference_info_kind"] == "summary_statistics_mean_value"
        (root / "data" / "info" / "d.info.json").unlink()
        missing = normalize_contract(root, "demo")
        assert missing["valid"] is False
        assert any("data_info" in error for error in missing["errors"])
