import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "agreement_line_fit.py"
spec = importlib.util.spec_from_file_location("agreement_line_fit", script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_exact_line_fit():
    stats = {
        "pairwise_probit": {
            "a::b": {"id_agreement": -1.0, "ood_agreement": -1.5},
            "a::c": {"id_agreement": 0.0, "ood_agreement": 0.5},
            "b::c": {"id_agreement": 1.0, "ood_agreement": 2.5},
        }
    }
    fit = mod.fit_line_from_stats(stats)
    assert abs(fit["slope"] - 2.0) < 1e-9
    assert abs(fit["intercept"] - 0.5) < 1e-9
    assert fit["r2"] == 1.0
    assert fit["on_line"] is True
