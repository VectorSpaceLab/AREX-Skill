#!/usr/bin/env python3
"""Report optional PyHealth dependencies without downloads or corpus/model access."""
import argparse
import importlib


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="return non-zero if any module is absent")
    args = parser.parse_args()
    names = ["torch_geometric", "nltk", "rapidfuzz", "rouge_score", "mne", "torchvision", "transformers"]
    missing = []
    for name in names:
        try:
            module = importlib.import_module(name)
            print(f"{name}: available {getattr(module, '__version__', '')}".rstrip())
        except Exception as exc:
            missing.append(name)
            print(f"{name}: unavailable ({type(exc).__name__}: {exc})")
    return 1 if args.strict and missing else 0

if __name__ == "__main__":
    raise SystemExit(main())
