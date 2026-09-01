#!/usr/bin/env python3
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from gpi import encoding_key, gpi_select


def test_gpi_selects_mixed_candidate_explore_action():
    candidates = [[1.0, 0.0], [0.0, 1.0], [0.70710678, 0.70710678]]
    table = {"s1": {}}
    for action, values in {
        "coffee": [[1, 0], [1, 0], [1, 0]],
        "food": [[0, 1], [0, 1], [0, 1]],
        "explore": [[0.8, 0.1], [0.1, 0.8], [0.95, 0.95]],
    }.items():
        table["s1"][action] = {encoding_key(z): psi for z, psi in zip(candidates, values)}
    result = gpi_select(table, "s1", ["coffee", "food", "explore"], [0.70710678, 0.70710678], candidates)
    assert result["action"] == "explore"
    assert result["candidate_count"] == 3
    assert result["winning_candidate"] == candidates[2]


def test_empty_candidates_rejected():
    try:
        gpi_select({}, "s", ["a"], [1.0], [])
    except ValueError as exc:
        assert "candidates" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_gpi_selects_mixed_candidate_explore_action()
    test_empty_candidates_rejected()


def test_single_candidate_preserves_uvfa_style_case():
    candidate = [[0.6, 0.8]]
    table = {"s": {"left": {encoding_key(candidate[0]): [0.7, 0.0]}, "right": {encoding_key(candidate[0]): [0.0, 0.9]}}}
    result = gpi_select(table, "s", ["left", "right"], [0.6, 0.8], candidate)
    assert result["action"] == "right"
    assert result["candidate_count"] == 1
