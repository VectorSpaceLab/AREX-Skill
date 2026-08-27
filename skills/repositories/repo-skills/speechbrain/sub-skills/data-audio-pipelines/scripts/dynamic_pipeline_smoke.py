#!/usr/bin/env python3
"""Exercise SpeechBrain DataPipeline lazy dependency behavior."""

from __future__ import annotations

import argparse
import json


def run() -> dict:
    from speechbrain.utils.data_pipeline import DataPipeline, provides, takes

    calls = {"lower": 0, "reverse": 0}

    @takes("text")
    @provides("lower")
    def lower(text):
        calls["lower"] += 1
        return text.lower()

    @takes("lower")
    @provides("reversed")
    def reverse(lower_text):
        calls["reverse"] += 1
        return lower_text[::-1]

    pipeline = DataPipeline(["text"], dynamic_items=[reverse, lower])
    pipeline.set_output_keys(["reversed"])
    full = pipeline({"text": "SpeechBrain"})

    calls_after_full = dict(calls)
    pipeline.set_output_keys(["text"])
    only_static = pipeline({"text": "SpeechBrain"})
    calls_after_static = dict(calls)

    specific = pipeline.compute_specific(["reversed"], {"text": "ABC"})

    return {
        "full_output": full,
        "calls_after_full": calls_after_full,
        "only_static_output": only_static,
        "calls_after_static": calls_after_static,
        "compute_specific": specific,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(result)


if __name__ == "__main__":
    main()
