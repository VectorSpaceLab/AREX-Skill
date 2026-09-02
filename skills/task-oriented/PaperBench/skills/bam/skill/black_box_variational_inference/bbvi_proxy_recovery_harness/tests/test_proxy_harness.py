import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_proxy_recovery.py"
spec = importlib.util.spec_from_file_location("run_proxy_recovery", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_proxy_item_has_matching_sample_fields():
    item = module.build_proxy_item(17)
    sample_count = len(item["samples"])
    assert sample_count == len(item["score"])
    assert sample_count == len(item["logp"])
    assert sample_count == len(item["logq"])
    assert sample_count == len(item["local_signal"])
    assert item["source"].startswith("synthetic")


def test_normal_logpdf_is_finite():
    value = module.normal_logpdf(0.0, 0.0, 1.0)
    assert value < 0.0
    assert value > -2.0
