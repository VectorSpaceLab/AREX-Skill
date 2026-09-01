import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "check_recovery_contract.py"
spec = importlib.util.spec_from_file_location("check_recovery_contract", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def valid_result():
    return {
        "is_proxy": True,
        "mechanism_checks": {
            "prior_sampling_executed": True,
            "simulator_executed": True,
            "conditional_posterior_depends_on_x": True,
            "posterior_samples_drawn": True,
            "diagnostics_executed": True,
        },
        "metrics": {"posterior_mean_abs_error": 0.1},
        "acceptance_thresholds": {"max_posterior_mean_abs_error": 0.5},
        "source_paths_read": [],
    }


def test_soft_proxy_contract_passes():
    assert module.validate_contract(valid_result())["ok"] is True


def test_hard_proxy_contract_fails():
    result = module.validate_contract(valid_result(), hard_mode=True)
    assert result["ok"] is False
    assert "hard mode" in result["errors"][0]


def test_forbidden_source_path_fails():
    data = valid_result()
    data["source_paths_read"] = ["/tmp/original_repo/file.py"]
    result = module.validate_contract(data, forbidden_path="/tmp/original_repo")
    assert result["ok"] is False
    assert "forbidden source path" in result["errors"][0]
