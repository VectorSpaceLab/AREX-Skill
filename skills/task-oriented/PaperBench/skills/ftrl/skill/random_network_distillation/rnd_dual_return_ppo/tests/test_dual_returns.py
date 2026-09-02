import importlib.util
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "dual_returns.py"
spec = importlib.util.spec_from_file_location("dual_returns", script)
dual_returns = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dual_returns)


def test_intrinsic_can_continue_across_done_while_extrinsic_resets():
    result = dual_returns.combine_advantages(
        extrinsic_rewards=[1.0, 1.0, 1.0],
        intrinsic_rewards=[1.0, 1.0, 1.0],
        dones=[False, True, False],
        gamma_e=0.9,
        gamma_i=0.9,
        intrinsic_non_episodic=True,
    )
    assert result["extrinsic_returns"] == [1.9, 1.0, 1.0]
    assert result["intrinsic_returns"][0] > result["extrinsic_returns"][0]
    assert result["combined_advantages"][0] == result["extrinsic_advantages"][0] + result["intrinsic_advantages"][0]
