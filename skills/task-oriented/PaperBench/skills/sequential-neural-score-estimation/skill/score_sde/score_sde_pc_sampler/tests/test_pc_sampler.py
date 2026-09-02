import importlib.util
import pathlib

MODULE = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "pc_sampler.py"
spec = importlib.util.spec_from_file_location("pc_sampler", MODULE)
pc_sampler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pc_sampler)


def test_pc_sampler_runs_predictor_and_corrector():
    result = pc_sampler.run_pc_sampler(2.0, steps=5, corrector_steps=2, seed=0)
    assert result["finite"] is True
    assert result["predictor_count"] == 5
    assert result["corrector_count"] == 10
    assert result["moved_toward_zero"] is True
    assert len(result["trajectory"]) == 5
