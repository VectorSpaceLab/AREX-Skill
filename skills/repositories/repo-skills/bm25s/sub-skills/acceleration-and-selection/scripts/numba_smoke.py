#!/usr/bin/env python3
"""Run a bounded local bm25s backend/selector smoke check.

The script intentionally uses only a four-document in-memory fixture. It can be
invoked as ``python /path/to/numba_smoke.py`` from any current working
 directory when bm25s is installed in the selected Python environment.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any, List, Optional



def _probe(module_name: str) -> str:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # report optional binary/runtime failures cleanly
        return f"unavailable ({type(exc).__name__}: {exc})"
    version = getattr(module, "__version__", None)
    return f"available{f' ({version})' if version else ''}"



def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smoke-test local bm25s NumPy/Numba/JAX/SciPy choices."
    )
    parser.add_argument(
        "--backend",
        choices=("auto", "numpy", "numba"),
        default="auto",
        help="BM25 scoring/retrieval backend (default: auto)",
    )
    parser.add_argument(
        "--csc-backend",
        choices=("auto", "numpy", "scipy"),
        default="auto",
        help="CSC index-construction backend (default: auto)",
    )
    parser.add_argument(
        "--backend-selection",
        choices=("auto", "numpy", "jax", "numba"),
        default="auto",
        help="top-k selector; Numba retrieval requires numba",
    )
    parser.add_argument(
        "--k", type=int, default=2, help="top-k per query (default: 2)"
    )
    parser.add_argument(
        "--compile",
        action="store_true",
        help="explicitly activate Numba scorer/CSC builder before indexing",
    )
    parser.add_argument(
        "--warmup",
        action="store_true",
        help="run the small Numba warmup calls (implies --compile)",
    )
    return parser



def _print_status(bm25s: Any) -> None:
    selection = bm25s.selection
    print(f"bm25s version: {getattr(bm25s, '__version__', 'unknown')}")
    print(f"Numba import: {getattr(bm25s, 'NUMBA_AVAILABLE', False)}")
    print(f"SciPy import: {getattr(bm25s, 'SCIPY_AVAILABLE', False)}")
    print(f"JAX top-k import: {getattr(selection, 'JAX_IS_AVAILABLE', False)}")
    print(f"Numba package: {_probe('numba')}")
    print(f"SciPy package: {_probe('scipy')}")
    print(f"JAX package: {_probe('jax')}")



def main(argv: Optional[List[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        import bm25s
    except Exception as exc:
        print(
            f"ERROR: bm25s could not be imported ({type(exc).__name__}: {exc})",
            file=sys.stderr,
        )
        return 2

    _print_status(bm25s)
    if args.k < 1:
        print("ERROR: --k must be positive", file=sys.stderr)
        return 2

    corpus_tokens = [
        ["cat", "purr", "feline"],
        ["dog", "bark", "friend"],
        ["fish", "swim", "water"],
        ["cat", "fish", "friend"],
    ]
    documents = [
        "cat purr feline",
        "dog bark friend",
        "fish swim water",
        "cat fish friend",
    ]
    queries = [["cat", "purr"], ["fish", "water"]]

    try:
        retriever = bm25s.BM25(
            corpus=documents,
            backend=args.backend,
            csc_backend=args.csc_backend,
            auto_compile=False,
        )
        print(f"resolved BM25 backend: {retriever.backend}")
        print(f"resolved CSC backend: {retriever.csc_backend}")

        if args.compile or args.warmup:
            retriever.compile(activate_numba=True, warmup=args.warmup)
            print(f"explicit Numba compile: complete (warmup={args.warmup})")

        retriever.index(corpus_tokens, show_progress=False)
        results = retriever.retrieve(
            queries,
            k=args.k,
            sorted=True,
            backend_selection=args.backend_selection,
            show_progress=False,
        )
    except ImportError as exc:
        print(
            "OPTIONAL DEPENDENCY ERROR: "
            f"{exc}\nUse the NumPy fallback or install the explicitly requested "
            "CPU extra.",
            file=sys.stderr,
        )
        return 2
    except (ValueError, RuntimeError) as exc:
        print(
            f"BACKEND CONFIGURATION ERROR: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:
        print(
            f"SMOKE CHECK FAILED: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 1

    print(f"documents shape: {results.documents.shape}")
    print(f"scores shape: {results.scores.shape}")
    print(f"first query IDs: {results.documents[0].tolist()}")
    print(f"first query scores: {results.scores[0].tolist()}")
    print("OK: local acceleration/selection fixture completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
