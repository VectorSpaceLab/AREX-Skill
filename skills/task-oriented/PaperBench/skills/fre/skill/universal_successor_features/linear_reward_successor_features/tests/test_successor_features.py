#!/usr/bin/env python3
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from successor_features import linear_reward, q_value, sf_target, td_error


def test_linear_reward_and_q_value():
    assert linear_reward([1.0, 0.25], [0.5, 2.0]) == 1.0
    assert q_value([2.0, 3.0], [0.25, 0.5]) == 2.0


def test_sf_target_and_td_error():
    target = sf_target([1.0, 0.0], [0.5, 0.5], gamma=0.8)
    assert target == [1.4, 0.4]
    assert td_error([1.0, 0.5], target) == [0.3999999999999999, -0.09999999999999998]
    assert sf_target([0.0, 1.0], [9.0, 9.0], gamma=0.9, terminal=True) == [0.0, 1.0]


def test_dimension_mismatch_raises():
    try:
        linear_reward([1.0], [1.0, 2.0])
    except ValueError as exc:
        assert "dimension mismatch" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_linear_reward_and_q_value()
    test_sf_target_and_td_error()
    test_dimension_mismatch_raises()


def test_terminal_target_ignores_bootstrap_even_with_nonzero_gamma():
    assert sf_target([0.25, 0.75], [100.0, 100.0], gamma=0.99, terminal=True) == [0.25, 0.75]
