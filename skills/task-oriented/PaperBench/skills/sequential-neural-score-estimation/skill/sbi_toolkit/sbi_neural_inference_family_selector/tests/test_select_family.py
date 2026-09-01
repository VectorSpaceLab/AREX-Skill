import importlib.util
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "select_family.py"
spec = importlib.util.spec_from_file_location("select_family", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_posterior_target_selects_snpe():
    result = module.select_family("posterior", direct_sampling=True)
    assert result["family"] == "SNPE"
    assert result["posterior_requires_mcmc"] is False


def test_ratio_rejects_direct_likelihood_requirement():
    try:
        module.select_family("ratio", density_eval_required=True)
    except ValueError as exc:
        assert "not direct likelihood" in str(exc)
    else:
        raise AssertionError("ratio target should reject direct likelihood requirement")
