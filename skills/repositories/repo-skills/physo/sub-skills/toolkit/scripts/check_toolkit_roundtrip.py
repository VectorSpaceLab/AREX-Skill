#!/usr/bin/env python3
"""Deterministic CPU-only toolkit encoding/decoding check.

This helper intentionally does not plot, access the network, or run SR.
"""

from __future__ import annotations

import sys
import warnings

warnings.filterwarnings("ignore", message="Latex display is not available.*")

import numpy as np
import torch

from physo.toolkit import get_library


def main() -> int:
    np.random.seed(0)
    torch.manual_seed(0)

    library = get_library(
        X_names=["x"],
        y_name="y",
        fixed_consts=[1.0],
        free_consts_names=["c"],
        free_consts_init_val=[1.0],
        op_names=["add", "mul"],
        warn_about_units=False,
        device="cpu",
    )
    source = [["mul", "c", "x"], ["add", "x", "x"]]
    encoded = library.encode(source)
    if [library.names[i] for i in encoded[0]] != source[0]:
        raise AssertionError("integer encoding does not map back to token names")

    one_hot = library.encode(source, one_hot=True)
    if one_hot[0].shape != (3, library.n_choices):
        raise AssertionError("unexpected one-hot encoding shape")

    # decode is intentionally strict about integer scalar types.
    decoded = library.decode([[int(value) for value in row] for row in encoded])
    if decoded.status()[0, :3].tolist() != source[0]:
        raise AssertionError("decoded status does not match the source prefix")
    if "c" not in decoded.get_infix_str(0):
        raise AssertionError("decoded program has the wrong infix representation")
    if str(decoded.get_prog(0).get_infix_sympy()) != "c*x":
        raise AssertionError("decoded SymPy expression is unexpected")

    try:
        library.encode([["mul", "not_in_library", "x"]])
    except ValueError as exc:
        if "not_in_library" not in str(exc):
            raise AssertionError("unknown-token error omitted the offending name") from exc
    else:
        raise AssertionError("an unknown token was accepted")

    print(
        "PASS: toolkit round-trip, one-hot shape, plain representations, "
        "and unknown-token validation"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # clear failure signal for a shell smoke check
        print(f"FAIL: toolkit round-trip check: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
