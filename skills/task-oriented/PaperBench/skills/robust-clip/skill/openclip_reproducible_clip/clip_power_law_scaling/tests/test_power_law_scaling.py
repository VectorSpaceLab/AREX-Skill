from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from power_law_scaling import fit_power_law

records = []
for compute in [10, 100, 1000, 10000]:
    records.append({"total_compute": compute, "retrieval_error": 100.0 * (compute ** -0.1)})
fit = fit_power_law(records, "retrieval_error", True)
assert abs(fit["exponent"] + 0.1) < 1e-9
assert fit["log_power_law_r2"] > 0.999999
assert fit["negative_exponent"] is True
