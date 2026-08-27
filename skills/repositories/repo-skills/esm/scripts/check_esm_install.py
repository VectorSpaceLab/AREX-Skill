#!/usr/bin/env python3
"""Safely check a fair-esm installation without downloading model weights."""

from __future__ import annotations

import importlib
import importlib.metadata as metadata
import inspect
import sys


def check(label: str, func) -> bool:
    try:
        value = func()
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        print(f"FAIL {label}: {type(exc).__name__}: {exc}")
        return False
    print(f"OK {label}: {value}")
    return True


def main() -> int:
    ok = True
    ok &= check("import esm", lambda: importlib.import_module("esm").__name__)

    try:
        esm = importlib.import_module("esm")
    except Exception:
        return 1

    ok &= check("distribution fair-esm", lambda: metadata.version("fair-esm"))
    ok &= check("esm version", lambda: getattr(esm, "__version__", "unknown"))
    ok &= check("Alphabet.from_architecture", lambda: esm.Alphabet.from_architecture("ESM-1b").mask_idx)
    ok &= check(
        "FastaBatchedDataset.get_batch_indices signature",
        lambda: str(inspect.signature(esm.FastaBatchedDataset.get_batch_indices)),
    )
    ok &= check("pretrained loaders", lambda: hasattr(esm.pretrained, "load_model_and_alphabet"))

    def inverse_import() -> str:
        import esm.inverse_folding.util as util
        import esm.inverse_folding.multichain_util as multichain_util

        return f"{util.load_structure.__name__}, {multichain_util.extract_coords_from_complex.__name__}"

    check("optional inverse_folding imports", inverse_import)

    def esmfold_import() -> str:
        from esm.esmfold.v1 import pretrained

        return pretrained.esmfold_v1.__name__

    check("optional esmfold import", esmfold_import)

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
