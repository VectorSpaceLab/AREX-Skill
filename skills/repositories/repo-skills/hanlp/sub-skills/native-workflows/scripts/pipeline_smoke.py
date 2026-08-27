#!/usr/bin/env python3
"""No-download smoke test for HanLP pipeline composition."""
from __future__ import annotations
import argparse, hanlp
from hanlp.utils.rules import split_sentence

def main():
    ap = argparse.ArgumentParser(description="Run a no-download hanlp.pipeline smoke test.")
    ap.add_argument("text", nargs="?", default="今天天气真好。我要去散步。")
    args = ap.parse_args()
    pipe = hanlp.pipeline().append(split_sentence, output_key="sentences")
    copied = pipe.copy()
    copied.append(lambda sent: ["".join(sent)], input_key="sentences", output_key="joined")
    original = pipe(args.text); changed = copied(args.text)
    assert pipe is not copied and "sentences" in original and "joined" in changed
    print("pipeline smoke passed")
    print(original.to_json())
    return 0
if __name__ == "__main__": raise SystemExit(main())
