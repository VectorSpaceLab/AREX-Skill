import importlib.util, json, tempfile
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "check_recovery_contract.py"
spec = importlib.util.spec_from_file_location("check_recovery_contract", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "result.json"
    path.write_text(json.dumps({"is_proxy": True, "metrics": {"fid_monotonicity_and_ttur_loss_drop": 1.0}, "mechanism_checks": {"fid_statistics_computed": True, "frechet_distance_computed": True, "fid_disturbance_monotonic": True, "ttur_separate_rates": True, "optimizer_step_executed": True}}), encoding="utf-8")
    checked = mod.check_result(path)
    assert checked["ok"] is True
