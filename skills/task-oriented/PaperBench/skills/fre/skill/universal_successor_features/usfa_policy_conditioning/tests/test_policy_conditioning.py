#!/usr/bin/env python3
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from policy_conditioning import build_candidate_set, encoding_key, greedy_action_for_encoding


def test_candidate_set_deduplicates_encodings():
    candidates = build_candidate_set([[1, 0], [0, 1]], [[1.0, 0.0], [0.5, 0.5]])
    assert candidates == [(1.0, 0.0), (0.0, 1.0), (0.5, 0.5)]


def test_greedy_action_for_encoding():
    z = [1.0, 0.0]
    key = encoding_key(z)
    table = {"s1": {"coffee": {key: [1.0, 0.0]}, "food": {key: [0.0, 1.0]}}}
    result = greedy_action_for_encoding(table, "s1", ["coffee", "food"], z)
    assert result["action"] == "coffee"
    assert result["scores"]["coffee"] == 1.0


def test_missing_encoding_is_clear():
    try:
        greedy_action_for_encoding({"s1": {"a": {}}}, "s1", ["a"], [0.2, 0.8])
    except KeyError as exc:
        assert "missing psi" in str(exc)
    else:
        raise AssertionError("expected KeyError")


if __name__ == "__main__":
    test_candidate_set_deduplicates_encodings()
    test_greedy_action_for_encoding()
    test_missing_encoding_is_clear()
