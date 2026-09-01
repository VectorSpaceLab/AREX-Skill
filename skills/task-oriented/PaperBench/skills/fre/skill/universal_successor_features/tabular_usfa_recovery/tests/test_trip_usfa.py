#!/usr/bin/env python3
import pathlib
import tempfile
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT.parents[0]
sys.path.insert(0, str(ROOT / "scripts"))

from trip_usfa_recovery import run


def test_trip_usfa_proxy_runs_and_passes_mechanism_checks():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run(SKILL_ROOT, pathlib.Path(tmpdir))
        assert result["is_proxy"] is True
        assert result["sample_count"] == 51
        assert result["metrics"]["mean_normalized_return"] >= 0.95
        checks = result["mechanism_checks"]
        assert checks["linear_reward_dot_product_used"] is True
        assert checks["successor_feature_td_update_executed"] is True
        assert checks["gpi_candidate_search_executed"] is True
        assert checks["optimizer_step_executed"] is True
        assert checks["loss_decreased"] is True


if __name__ == "__main__":
    test_trip_usfa_proxy_runs_and_passes_mechanism_checks()
