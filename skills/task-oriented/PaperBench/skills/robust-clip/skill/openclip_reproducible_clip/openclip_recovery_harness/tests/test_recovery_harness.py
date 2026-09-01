import tempfile
import json
import shutil
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from recovery_harness import run_recovery

source_root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory() as tmp:
    attempt = Path(tmp) / "attempt"
    skills = Path(tmp) / "skills"
    attempt.mkdir()
    skills.mkdir()
    for child in source_root.iterdir():
        if child.is_dir():
            shutil.copytree(child, skills / child.name)
    target = {"dataset": "synthetic_clip_scale_frontier", "split": "tiny_proxy_v1", "metric": "log_power_law_r2", "paper_value": 0.95, "proxy": True, "rationale": "test"}
    (attempt / "module_plan.json").write_text(json.dumps({"fast_recovery_target": target}), encoding="utf-8")
    result = run_recovery(attempt, skills)
    assert result["is_proxy"] is True
    assert result["paper_target"] == target
    assert result["metrics"]["log_power_law_r2"] >= 0.95
    assert all(result["mechanism_checks"].values()) is False
    assert result["mechanism_checks"]["power_law_fit_executed"] is True
