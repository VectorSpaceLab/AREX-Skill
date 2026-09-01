import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "online_stream_memory" / "scripts"))
sys.path.insert(0, str(ROOT / "virtual_update_interference" / "scripts"))
sys.path.insert(0, str(ROOT / "generative_latent_mir" / "scripts"))

from recovery_eval import accuracy, build_proxy_stream, run_latent_cross_check, run_selector


def test_proxy_stream_and_accuracy():
    stream = build_proxy_stream()
    assert len(stream) == 12
    params = {"weights": [1.0, 0.0], "bias": 0.0}
    assert 0.0 <= accuracy(params, stream) <= 1.0


def test_run_selector_emits_trace_and_metrics():
    result = run_selector("mir")
    assert len(result["trace"]) == len(build_proxy_stream())
    assert 0.0 <= result["final_accuracy"] <= 1.0
    assert "average_forgetting" in result["forgetting"]
    assert any(step["scores"] for step in result["trace"])


def test_latent_cross_check_available():
    result = run_latent_cross_check()
    assert result["available"] is True
    assert result["selected_ids"] == ["far_interfered"]
