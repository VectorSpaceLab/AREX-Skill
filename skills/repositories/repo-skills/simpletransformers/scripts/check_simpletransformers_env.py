#!/usr/bin/env python3
"""Check Simple Transformers imports, versions, and optional backend availability."""
import argparse
import importlib
import sys
from importlib.metadata import PackageNotFoundError, version

MODULES = {
    "root": "simpletransformers",
    "classification": "simpletransformers.classification",
    "ner": "simpletransformers.ner",
    "qa": "simpletransformers.question_answering",
    "generation": "simpletransformers.language_generation",
    "lm": "simpletransformers.language_modeling",
    "seq2seq": "simpletransformers.seq2seq",
    "t5": "simpletransformers.t5",
    "representation": "simpletransformers.language_representation",
    "retrieval": "simpletransformers.retrieval",
    "convai": "simpletransformers.conv_ai",
}


def dist(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def main(argv=None):
    p = argparse.ArgumentParser(description="Check Simple Transformers environment health.")
    p.add_argument("--modules", nargs="*", default=["root"], choices=sorted(MODULES))
    p.add_argument("--check-cuda", action="store_true")
    args = p.parse_args(argv)

    print("simpletransformers", dist("simpletransformers"))
    print("transformers", dist("transformers"))
    print("torch", dist("torch"))
    status = 0
    for key in args.modules:
        modname = MODULES[key]
        try:
            importlib.import_module(modname)
            print(f"import {key}: OK ({modname})")
        except Exception as exc:
            status = 1
            print(f"import {key}: FAIL {type(exc).__name__}: {exc}")
    if args.check_cuda:
        try:
            import torch
            print("torch.cuda.is_available", torch.cuda.is_available())
            print("torch.cuda.device_count", torch.cuda.device_count())
            if torch.cuda.is_available():
                print("torch.cuda.device0", torch.cuda.get_device_name(0))
        except Exception as exc:
            status = 1
            print(f"cuda check: FAIL {type(exc).__name__}: {exc}")
    if status:
        print("If failures mention SequenceSummary, TransfoXLConfig, or cached_path, handle Transformers compatibility before data debugging.", file=sys.stderr)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
