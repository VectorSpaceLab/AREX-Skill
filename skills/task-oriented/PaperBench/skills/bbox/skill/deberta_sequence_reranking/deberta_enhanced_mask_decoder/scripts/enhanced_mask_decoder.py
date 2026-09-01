#!/usr/bin/env python3
"""Enhanced Mask Decoder scoring helpers for DeBERTa proxy recovery."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def emd_position_score(position: int, target_position: int, scale: float = 1.0) -> float:
    return scale / (1.0 + abs(float(position) - float(target_position)))


def score_candidates(
    candidates: list[dict],
    relative_scores: dict[str, float],
    target_position: int,
    emd_weight: float = 1.0,
) -> dict:
    scored = []
    for candidate in candidates:
        label = str(candidate["label"])
        position = int(candidate.get("absolute_position", 0))
        relative_score = float(relative_scores.get(label, 0.0))
        emd_score = emd_position_score(position, target_position, emd_weight)
        logit = relative_score + emd_score
        scored.append(
            {
                "label": label,
                "relative_score": relative_score,
                "absolute_position": position,
                "emd_score": emd_score,
                "logit": logit,
            }
        )
    predicted = max(scored, key=lambda item: item["logit"])["label"] if scored else ""
    no_emd = [
        {**item, "emd_score": 0.0, "logit": item["relative_score"]}
        for item in scored
    ]
    predicted_without_emd = max(no_emd, key=lambda item: item["logit"])["label"] if no_emd else ""
    return {
        "target_position": target_position,
        "emd_weight": emd_weight,
        "scores": scored,
        "predicted_label": predicted,
        "without_emd_scores": no_emd,
        "predicted_without_emd": predicted_without_emd,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates-json", required=True)
    parser.add_argument("--relative-scores-json", required=True)
    parser.add_argument("--target-position", type=int, required=True)
    parser.add_argument("--emd-weight", type=float, default=1.0)
    args = parser.parse_args()
    candidates = json.loads(Path(args.candidates_json).read_text(encoding="utf-8"))
    relative_scores = json.loads(Path(args.relative_scores_json).read_text(encoding="utf-8"))
    result = score_candidates(candidates, relative_scores, args.target_position, args.emd_weight)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
