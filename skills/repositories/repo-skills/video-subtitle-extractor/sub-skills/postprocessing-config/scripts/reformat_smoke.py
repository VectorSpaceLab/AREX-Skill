#!/usr/bin/env python3
"""Safely smoke-test VSE typo replacement rules on sample text."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

def apply_rules(text: str, rules: dict[str,str]) -> str:
    for pattern, repl in rules.items():
        text = re.sub(re.compile(pattern, re.I), repl, text)
    return text

def main() -> int:
    ap=argparse.ArgumentParser(description='Apply typoMap-style regex replacements to sample text without modifying files.')
    ap.add_argument('--typo-map', required=True)
    ap.add_argument('--sample-text', default="Iife isgood")
    args=ap.parse_args()
    rules=json.loads(Path(args.typo_map).read_text(encoding='utf-8'))
    if not isinstance(rules, dict):
        raise SystemExit('typo map must be a JSON object')
    out=apply_rules(args.sample_text, {str(k):str(v) for k,v in rules.items()})
    print('INPUT :', args.sample_text)
    print('OUTPUT:', out)
    return 0
if __name__=='__main__':
    raise SystemExit(main())
