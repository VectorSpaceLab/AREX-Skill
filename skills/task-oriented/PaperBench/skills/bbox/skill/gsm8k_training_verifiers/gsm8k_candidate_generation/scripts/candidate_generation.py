#!/usr/bin/env python3
"""Create deterministic GSM8K candidate records for verifier recovery."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    from answer_tools import extract_answer, label_candidate
except ImportError:  # pragma: no cover
    import sys

    sys.path.append(str(Path(__file__).resolve().parents[2] / "gsm8k_answer_tools" / "scripts"))
    from answer_tools import extract_answer, label_candidate


FINAL_RE = re.compile(r"(####\s*)([-+]?[0-9][0-9,]*(?:\.[0-9]+)?)")


def load_jsonl(path: str | Path, limit: int | None = None) -> list[dict]:
    rows = []
    with Path(path).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
                if limit is not None and len(rows) >= limit:
                    break
    return rows


def perturb_answer(answer: str, delta: int = 1) -> str:
    canonical = extract_answer(answer)
    try:
        if "." in canonical:
            new_value = str(float(canonical) + delta)
        else:
            new_value = str(int(canonical) + delta)
    except Exception:
        new_value = "0"
    if FINAL_RE.search(answer):
        return FINAL_RE.sub(rf"\g<1>{new_value}", answer, count=1)
    return answer.rstrip() + f"\n#### {new_value}"


def generate_candidates(examples: list[dict], negatives_per_problem: int = 1) -> tuple[list[dict], list[dict]]:
    candidates = []
    summaries = []
    for idx, example in enumerate(examples):
        problem_id = str(example.get("id", idx))
        question = example["question"]
        gold_solution = example["answer"]
        problem_candidates = []
        raw_solutions = [("gold_solution", gold_solution)]
        for neg_idx in range(negatives_per_problem):
            raw_solutions.append((f"perturbed_final_answer_{neg_idx + 1}", perturb_answer(gold_solution, neg_idx + 1)))
        for cand_idx, (source, solution) in enumerate(raw_solutions):
            label = label_candidate(solution, gold_solution)
            record = {
                "problem_id": problem_id,
                "candidate_id": f"{problem_id}_{cand_idx}",
                "question": question,
                "solution": solution,
                "extracted_answer": label["extracted_answer"],
                "gold_answer": label["gold_answer"],
                "label": 1 if label["correct"] else 0,
                "source": source,
                "calculator_checks": label["calculator_checks"],
            }
            candidates.append(record)
            problem_candidates.append(record)
        summaries.append(
            {
                "problem_id": problem_id,
                "candidate_count": len(problem_candidates),
                "positive_count": sum(item["label"] for item in problem_candidates),
                "negative_count": sum(1 - item["label"] for item in problem_candidates),
            }
        )
    return candidates, summaries


def write_generation(examples_path: str, output_path: str, summary_path: str, limit: int, negatives: int) -> dict:
    examples = load_jsonl(examples_path, limit=limit)
    candidates, summaries = generate_candidates(examples, negatives_per_problem=negatives)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(candidates, indent=2) + "\n", encoding="utf-8")
    Path(summary_path).write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    return {"candidate_count": len(candidates), "problem_count": len(examples), "summary_path": summary_path}


def self_test() -> None:
    examples = [{"question": "Q?", "answer": "A 1+1 = <<1+1=2>>2.\n#### 2"}]
    candidates, summaries = generate_candidates(examples, negatives_per_problem=1)
    assert len(candidates) == 2
    assert {item["label"] for item in candidates} == {0, 1}
    assert summaries[0]["positive_count"] == 1
    assert summaries[0]["negative_count"] == 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_generate = sub.add_parser("generate")
    p_generate.add_argument("--examples", required=True)
    p_generate.add_argument("--output", required=True)
    p_generate.add_argument("--summary", required=True)
    p_generate.add_argument("--limit", type=int, default=2)
    p_generate.add_argument("--negatives", type=int, default=1)
    sub.add_parser("self-test")
    args = parser.parse_args(argv)
    if args.cmd == "generate":
        result = write_generation(args.examples, args.output, args.summary, args.limit, args.negatives)
        print(json.dumps(result, indent=2))
    elif args.cmd == "self-test":
        self_test()
        print(json.dumps({"ok": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
