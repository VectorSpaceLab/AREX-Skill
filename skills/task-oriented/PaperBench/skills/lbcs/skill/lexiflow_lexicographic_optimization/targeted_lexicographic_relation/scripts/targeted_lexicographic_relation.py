#!/usr/bin/env python3
"""Target-aware lexicographic relations from the LexiFlow paper."""

from __future__ import annotations

import argparse
import json
from typing import Sequence


def _same_dim(candidate: Sequence[float], incumbent: Sequence[float], targets: Sequence[float]) -> None:
    if not candidate or len(candidate) != len(incumbent) or len(candidate) != len(targets):
        raise ValueError("candidate, incumbent, and targets must have the same non-zero dimension")


def target_equal(candidate: Sequence[float], incumbent: Sequence[float], targets: Sequence[float], eps: float = 1e-12) -> bool:
    _same_dim(candidate, incumbent, targets)
    for cand, inc, target in zip(candidate, incumbent, targets):
        if abs(float(cand) - float(inc)) <= eps:
            continue
        if float(cand) <= float(target) + eps and float(inc) <= float(target) + eps:
            continue
        return False
    return True


def target_preferred(candidate: Sequence[float], incumbent: Sequence[float], targets: Sequence[float], eps: float = 1e-12) -> bool:
    _same_dim(candidate, incumbent, targets)
    for priority, (cand, inc, target) in enumerate(zip(candidate, incumbent, targets)):
        prefix_equal = target_equal(candidate[:priority], incumbent[:priority], targets[:priority], eps) if priority else True
        if prefix_equal and float(cand) < float(inc) - eps and float(inc) > float(target) + eps:
            return True
    return False


def vanilla_preferred(candidate: Sequence[float], incumbent: Sequence[float], eps: float = 1e-12) -> bool:
    if len(candidate) != len(incumbent) or not candidate:
        raise ValueError("candidate and incumbent must have the same non-zero dimension")
    for cand, inc in zip(candidate, incumbent):
        if float(cand) < float(inc) - eps:
            return True
        if float(cand) > float(inc) + eps:
            return False
    return False


def update_decision(candidate: Sequence[float], incumbent: Sequence[float], targets: Sequence[float]) -> dict:
    targeted = target_preferred(candidate, incumbent, targets)
    equal = target_equal(candidate, incumbent, targets)
    vanilla = vanilla_preferred(candidate, incumbent)
    accept = targeted or (equal and vanilla)
    return {"target_preferred": targeted, "target_equal": equal, "vanilla_preferred": vanilla, "accept": accept}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", default="")
    parser.add_argument("--incumbent", default="")
    parser.add_argument("--targets", default="")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        assert update_decision([0.11, 2.0], [0.10, 8.0], [0.12, 8.0])["accept"]
        assert not update_decision([0.20, 1.0], [0.10, 8.0], [0.12, 8.0])["accept"]
        print(json.dumps({"ok": True}, indent=2))
        return 0
    print(json.dumps(update_decision(json.loads(args.candidate), json.loads(args.incumbent), json.loads(args.targets)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
