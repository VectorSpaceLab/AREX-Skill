import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "snpe_proxy.py"
spec = importlib.util.spec_from_file_location("snpe_proxy", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_proxy_conditions_on_observation():
    low = module.run_proxy(num_simulations=256, observation=-1.0, seed=4)
    high = module.run_proxy(num_simulations=256, observation=1.0, seed=4)
    assert low["posterior_summary"]["mean"] < high["posterior_summary"]["mean"]
    assert high["mechanism_checks"]["conditional_posterior_depends_on_x"] is True


def test_proxy_mean_error_is_bounded():
    result = module.run_proxy(num_simulations=512, observation=1.25, seed=2)
    assert result["posterior_summary"]["posterior_mean_abs_error"] < 0.45
    assert result["posterior_summary"]["std"] > 0.05
