#!/usr/bin/env python3
"""Small smoke for reasoning-tag and cache-determinism helpers."""

from __future__ import annotations

import argparse
import json

from lmms_eval.api.reasoning import parse_reasoning_tags_config, strip_reasoning_tags
from lmms_eval.caching.response_cache import canonicalize_gen_kwargs, is_deterministic


def main() -> int:
    parser = argparse.ArgumentParser(description="Exercise reasoning and cache helper functions.")
    parser.add_argument("--json", action="store_true", help="Print structured JSON output.")
    args = parser.parse_args()

    sample = "before <think>hidden</think> answer"
    result = {
        "reasoning": {
            "sample": sample,
            "stripped": strip_reasoning_tags(sample, [["<think>", "</think>"]]),
            "parsed_default": parse_reasoning_tags_config('[ ["<think>", "</think>"] ]'.replace(" ", "")),
            "parsed_disabled": parse_reasoning_tags_config("none"),
        },
        "cache": {
            "canonical": canonicalize_gen_kwargs({"temperature": 0.0, "do_sample": False, "max_new_tokens": 8}),
            "deterministic": is_deterministic("generate_until", {"temperature": 0, "do_sample": False}),
            "non_deterministic": is_deterministic("generate_until", {"temperature": 0.7, "do_sample": False}),
            "loglikelihood_deterministic": is_deterministic("loglikelihood", {}),
        },
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"reasoning stripped: {result['reasoning']['stripped']}")
        print(f"canonical gen_kwargs: {result['cache']['canonical']}")
        print(f"deterministic generate_until: {result['cache']['deterministic']}")
        print(f"loglikelihood deterministic: {result['cache']['loglikelihood_deterministic']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
