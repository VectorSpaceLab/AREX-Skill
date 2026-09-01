import importlib.util, math
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "parameter_transforms.py"
spec = importlib.util.spec_from_file_location("parameter_transforms", SCRIPT); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_roundtrip_and_support():
    contract = {"name": "theta", "lower": 0.0, "upper": 1.0}
    result = mod.roundtrip(0.2, contract)
    assert result["valid"] and result["abs_error"] < 1e-12
    assert math.isfinite(result["unconstrained"]["log_abs_jacobian"])
    assert not mod.unconstrain(-0.1, contract)["valid"]
    assert abs(mod.constrain(0.0, contract)["value"] - 0.5) < 1e-12
if __name__ == "__main__": test_roundtrip_and_support()
