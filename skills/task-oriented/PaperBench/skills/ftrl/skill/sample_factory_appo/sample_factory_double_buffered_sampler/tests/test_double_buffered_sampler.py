import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "double_buffered_sampler.py"
spec = importlib.util.spec_from_file_location("double_buffered_sampler", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_schedule_alternates_groups():
    result = module.analyze(4, 5.0, 1.0, 3)
    assert result["front_buffer"] == [0, 1]
    assert result["back_buffer"] == [2, 3]
    assert result["schedule"][0]["simulate_envs"] == [0, 1]
    assert result["schedule"][1]["simulate_envs"] == [2, 3]


def test_idle_reduction_is_positive_when_half_buffer_masks_part_of_latency():
    estimates = module.idle_estimates(4, 5.0, 1.0)
    assert estimates["synchronous_idle_time"] == 5.0
    assert estimates["double_buffered_idle_time"] == 3.0
    assert estimates["idle_time_reduction_ratio"] == 0.4
    assert estimates["minimum_half_buffer_size"] == 5


def test_invalid_odd_env_count_fails():
    try:
        module.split_buffers(3)
    except ValueError as exc:
        assert "even" in str(exc)
    else:
        raise AssertionError("expected odd env count to fail")
