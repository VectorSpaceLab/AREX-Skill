#!/usr/bin/env python3
"""Check that bert_pytorch imports, exports, metadata, and CLIs are available."""

from __future__ import annotations

import argparse
import importlib
import inspect
import shutil
import subprocess
from importlib import metadata

DEFAULT_COMMANDS = ["bert", "bert-vocab"]


def check_distribution(name: str) -> bool:
    try:
        version = metadata.version(name)
    except Exception as error:  # pragma: no cover - defensive reporting.
        print(f"FAIL distribution {name}: {type(error).__name__}: {error}")
        return False
    print(f"OK distribution {name} {version}")
    return True


def check_imports() -> bool:
    ok = True
    import_specs = [
        ("bert_pytorch", None),
        ("bert_pytorch.dataset", "BERTDataset"),
        ("bert_pytorch.dataset", "WordVocab"),
        ("bert_pytorch.trainer", "BERTTrainer"),
        ("bert_pytorch.model", "BERTLM"),
    ]
    for module_name, symbol_name in import_specs:
        try:
            module = importlib.import_module(module_name)
            if symbol_name is None:
                print(f"OK import {module_name} -> {getattr(module, '__file__', 'namespace')}")
            else:
                getattr(module, symbol_name)
                print(f"OK export {module_name}.{symbol_name}")
        except Exception as error:
            target = module_name if symbol_name is None else f"{module_name}.{symbol_name}"
            print(f"FAIL import/export {target}: {type(error).__name__}: {error}")
            ok = False
    return ok


def check_cli(command: str) -> bool:
    executable = shutil.which(command)
    if executable is None:
        print(f"FAIL command {command}: not on PATH")
        return False
    result = subprocess.run([executable, "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"FAIL command {command}: -h exited {result.returncode}")
        if result.stderr:
            print(result.stderr.strip().splitlines()[-1])
        return False
    print(f"OK command {command}")
    return True


def check_signatures() -> bool:
    try:
        from bert_pytorch import BERT
        from bert_pytorch.dataset import BERTDataset, WordVocab
        from bert_pytorch.model import BERTLM
        from bert_pytorch.trainer import BERTTrainer
    except Exception as error:
        print(f"FAIL signatures: {type(error).__name__}: {error}")
        return False

    items = [
        ("BERT", BERT),
        ("BERTDataset", BERTDataset),
        ("WordVocab.to_seq", WordVocab.to_seq),
        ("WordVocab.from_seq", WordVocab.from_seq),
        ("BERTLM", BERTLM),
        ("BERTTrainer", BERTTrainer),
    ]
    for label, obj in items:
        try:
            print(f"{label}: {inspect.signature(obj)}")
        except Exception as error:
            print(f"FAIL signature {label}: {type(error).__name__}: {error}")
            return False
    return True


def check_torch() -> bool:
    try:
        import torch
    except Exception as error:
        print(f"FAIL import torch: {type(error).__name__}: {error}")
        return False
    print(f"OK torch {torch.__version__}")
    print(f"torch.version.cuda={getattr(torch.version, 'cuda', None)}")
    print(f"torch.cuda.is_available={torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"torch.cuda.device_count={torch.cuda.device_count()}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check bert_pytorch imports, signatures, metadata, and console commands.")
    parser.add_argument("--distribution", default="bert_pytorch", help="Distribution name to inspect.")
    parser.add_argument("--commands", nargs="*", default=DEFAULT_COMMANDS, help="Console commands to verify with -h.")
    parser.add_argument("--show-signatures", action="store_true", help="Print signatures for the main exported APIs.")
    parser.add_argument("--check-torch", action="store_true", help="Print torch and CUDA backend facts.")
    args = parser.parse_args()

    ok = True
    ok &= check_distribution(args.distribution)
    ok &= check_imports()
    if args.show_signatures:
        ok &= check_signatures()
    for command in args.commands:
        ok &= check_cli(command)
    if args.check_torch:
        ok &= check_torch()
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
