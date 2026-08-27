#!/usr/bin/env python3
"""No-download sentence splitting smoke test for HanLP rule utilities."""
from __future__ import annotations
import argparse
from hanlp.utils.rules import split_sentence

def main():
    ap = argparse.ArgumentParser(description="Split text with hanlp.utils.rules.split_sentence.")
    ap.add_argument("text", nargs="?", default="他说：“加油。”谢谢 Go to hankcs.com. Yes.")
    ap.add_argument("--not-best", action="store_true")
    args = ap.parse_args()
    sents = list(split_sentence(args.text, best=not args.not_best))
    assert sents
    print("\n".join(sents))
    return 0
if __name__ == "__main__": raise SystemExit(main())
