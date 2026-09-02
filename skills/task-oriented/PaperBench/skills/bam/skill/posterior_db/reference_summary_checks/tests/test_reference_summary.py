import json
import tempfile
from pathlib import Path

from reference_summary import load_reference_summary


def test_loads_mean_summary_and_rejects_bad_lengths():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "summary.json"
        path.write_text(json.dumps({"names": ["a", "b"], "mean_value": [1.0, 3.0], "mcse_mean": [0.1, 0.2]}))
        report = load_reference_summary(path)
        assert report["valid"] is True
        assert report["values"] == {"a": 1.0, "b": 3.0}
        assert report["quality_flags"]["mcse_available"] is True
        path.write_text(json.dumps({"names": ["a"], "mean_value": [1.0, 2.0]}))
        bad = load_reference_summary(path)
        assert bad["valid"] is False
        assert any("lengths differ" in blocker for blocker in bad["blockers"])
