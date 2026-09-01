import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_recovery import REQUIRED_MECHANISMS, evaluate_recovery


def _plan():
    return {"fast_recovery_target": {"dataset": "d", "split": "s", "metric": "m", "paper_value": 0.85, "proxy": True}}


def _result():
    return {
        "is_proxy": True,
        "metrics": {"m": 0.1},
        "paper_target": {"dataset": "d", "split": "s", "metric": "m", "paper_value": 0.85, "proxy": True},
        "mechanism_checks": {name: True for name in REQUIRED_MECHANISMS},
    }


def test_valid_proxy_recovery_passes():
    result = evaluate_recovery(_plan(), _result(), {"sources": ["paper_profile.md"]}, {"invocations": [{"evidence_type": "called script"}]})
    assert result["ok"] is True


def test_missing_mechanism_fails():
    recovery = _result()
    recovery["mechanism_checks"]["clipped_surrogate_computed"] = False
    result = evaluate_recovery(_plan(), recovery)
    assert result["ok"] is False
    assert any("clipped_surrogate_computed" in error for error in result["errors"])


def test_original_repo_source_fails():
    result = evaluate_recovery(_plan(), _result(), {"sources": ["/tmp/original_repo/file.py"]}, None, "/tmp/original_repo")
    assert result["ok"] is False


if __name__ == "__main__":
    test_valid_proxy_recovery_passes()
    test_missing_mechanism_fails()
    test_original_repo_source_fails()
