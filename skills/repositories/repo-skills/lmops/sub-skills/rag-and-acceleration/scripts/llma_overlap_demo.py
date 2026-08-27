#!/usr/bin/env python3
"""CPU-only LLMA overlap demo.

This toy script demonstrates the proposal/verification idea behind LLMA using
whitespace tokenization and an oracle target sequence. It does not import or
load repository code, model weights, or GPU dependencies.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from typing import List, Sequence


@dataclass
class StepTrace:
    step: int
    mode: str
    prefix: str
    proposal: List[str]
    accepted: List[str]
    emitted: List[str]
    reason: str


def tokenize(text: str) -> List[str]:
    return [tok for tok in text.strip().split() if tok]


def detokenize(tokens: Sequence[str]) -> str:
    return " ".join(tokens).strip()


def find_overlap_prefix(generated: List[str], references: List[List[str]], n: int) -> tuple[int, int] | None:
    if n <= 0 or len(generated) < n:
        return None
    suffix = generated[-n:]
    for ref_idx, ref in enumerate(references):
        for start in range(0, max(len(ref) - n + 1, 0)):
            if ref[start : start + n] == suffix and start + n < len(ref):
                return ref_idx, start
    return None


def llma_demo(
    prompt: str,
    references: List[str],
    target: str,
    n: int,
    k: int,
    max_steps: int,
) -> dict:
    prompt_tokens = tokenize(prompt)
    reference_tokens = [tokenize(ref) for ref in references]
    target_tokens = tokenize(target)

    generated = list(prompt_tokens)
    traces: List[StepTrace] = []
    model_calls = 0
    baseline_calls = 0

    while len(generated) < len(target_tokens) and len(traces) < max_steps:
        overlap = find_overlap_prefix(generated, reference_tokens, n)
        current_pos = len(generated)
        if overlap is None:
            baseline_calls += 1
            next_token = target_tokens[current_pos]
            generated.append(next_token)
            traces.append(
                StepTrace(
                    step=len(traces),
                    mode="baseline",
                    prefix=detokenize(generated[:-1][-n:]),
                    proposal=[next_token],
                    accepted=[next_token],
                    emitted=[next_token],
                    reason="no reference n-gram match yet",
                )
            )
            continue

        ref_idx, start = overlap
        ref = reference_tokens[ref_idx]
        proposal = ref[start + n : start + n + max(k - 1, 0)]
        if not proposal:
            baseline_calls += 1
            next_token = target_tokens[current_pos]
            generated.append(next_token)
            traces.append(
                StepTrace(
                    step=len(traces),
                    mode="fallback",
                    prefix=detokenize(generated[:-1][-n:]),
                    proposal=[],
                    accepted=[next_token],
                    emitted=[next_token],
                    reason="reference match existed but no copy span was available",
                )
            )
            continue

        model_calls += 1
        target_slice = target_tokens[current_pos : current_pos + len(proposal)]
        accepted_len = 0
        for candidate_token, oracle_token in zip(proposal, target_slice):
            if candidate_token != oracle_token:
                break
            accepted_len += 1

        if accepted_len == 0:
            baseline_calls += 1
            next_token = target_tokens[current_pos]
            generated.append(next_token)
            traces.append(
                StepTrace(
                    step=len(traces),
                    mode="verify-failed",
                    prefix=detokenize(generated[:-1][-n:]),
                    proposal=proposal,
                    accepted=[next_token],
                    emitted=[next_token],
                    reason="oracle token did not match the proposed copy span",
                )
            )
            continue

        accepted = proposal[:accepted_len]
        generated.extend(accepted)
        traces.append(
            StepTrace(
                step=len(traces),
                mode="copy-verified",
                prefix=detokenize(generated[:-accepted_len][-n:]) if accepted_len else detokenize(generated[-n:]),
                proposal=proposal,
                accepted=accepted,
                emitted=accepted,
                reason="all accepted tokens matched the oracle target prefix",
            )
        )

    baseline_cost = max(len(target_tokens) - len(prompt_tokens), 0)
    accelerated_cost = model_calls + baseline_calls
    speedup = None
    if accelerated_cost > 0:
        speedup = round(baseline_cost / accelerated_cost, 3)

    return {
        "prompt": prompt,
        "references": references,
        "target": target,
        "settings": {
            "n": n,
            "k": k,
            "max_steps": max_steps,
        },
        "prompt_tokens": prompt_tokens,
        "target_tokens": target_tokens,
        "final_output": detokenize(generated),
        "exact_match_with_target": generated == target_tokens,
        "baseline_cost_tokens": baseline_cost,
        "proposal_model_calls": model_calls,
        "fallback_model_calls": baseline_calls,
        "total_steps": len(traces),
        "estimated_relative_speedup": speedup,
        "traces": [asdict(trace) for trace in traces],
    }


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Demonstrate LLMA overlap proposal/verification on CPU.")
    parser.add_argument("--prompt", default="The answer is", help="Seed prompt before generation starts.")
    parser.add_argument(
        "--reference",
        action="append",
        default=["The answer is Microsoft Research because CoRAG uses retrieval over evidence."],
        help="Reference text. May be passed multiple times.",
    )
    parser.add_argument(
        "--target",
        default="The answer is Microsoft Research because CoRAG uses retrieval over evidence and LLMA can copy it.",
        help="Oracle target sequence used for verification.",
    )
    parser.add_argument("--n", type=int, default=2, help="Overlap trigger length.")
    parser.add_argument("--k", type=int, default=6, help="Maximum copied block length.")
    parser.add_argument("--max-steps", type=int, default=32, help="Maximum generation steps for the toy demo.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return parser


def print_markdown(result: dict) -> None:
    print("# LLMA overlap demo")
    print()
    print(f"- Prompt: `{result['prompt']}`")
    print(f"- Settings: `n={result['settings']['n']}`, `k={result['settings']['k']}`, `max_steps={result['settings']['max_steps']}`")
    print(f"- Final output: `{result['final_output']}`")
    print(f"- Exact match with target: `{result['exact_match_with_target']}`")
    print(f"- Baseline cost tokens: `{result['baseline_cost_tokens']}`")
    print(f"- Proposal model calls: `{result['proposal_model_calls']}`")
    print(f"- Fallback model calls: `{result['fallback_model_calls']}`")
    print(f"- Estimated relative speedup: `{result['estimated_relative_speedup']}`")
    print()
    print("## Trace")
    for step in result["traces"]:
        print(f"### Step {step['step']} - {step['mode']}")
        print(f"- Prefix: `{step['prefix']}`")
        print(f"- Proposal: `{detokenize(step['proposal'])}`")
        print(f"- Accepted: `{detokenize(step['accepted'])}`")
        print(f"- Reason: {step['reason']}")
        print()


def main(argv: List[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)
    if args.n < 1:
        parser.error("--n must be >= 1")
    if args.k < 1:
        parser.error("--k must be >= 1")
    if args.max_steps < 1:
        parser.error("--max-steps must be >= 1")

    result = llma_demo(
        prompt=args.prompt,
        references=args.reference,
        target=args.target,
        n=args.n,
        k=args.k,
        max_steps=args.max_steps,
    )
    if args.format == "json":
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_markdown(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
