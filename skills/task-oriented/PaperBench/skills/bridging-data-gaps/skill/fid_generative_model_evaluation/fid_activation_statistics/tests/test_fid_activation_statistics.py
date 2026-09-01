import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "fid_statistics.py"
spec = importlib.util.spec_from_file_location("fid_statistics", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

result = mod.compute_activation_statistics([[1, 2], [3, 4], [5, 6]])
assert result["mu"] == [3.0, 4.0]
assert len(result["sigma"]) == 2
assert result["diagnostics"]["covariance_symmetric"] is True
one = mod.compute_activation_statistics([[1, 2]])
assert one["sigma"] == [[0.0, 0.0], [0.0, 0.0]]
assert one["diagnostics"]["warnings"]
