#!/usr/bin/env python3
"""Optional smoke test for DGL sparse constructors and softmax."""

from __future__ import annotations

import argparse
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic tiny dgl.sparse API smoke. Reports a clear skip "
            "when the optional sparse native extension is unavailable."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable JSON summary instead of a text summary",
    )
    return parser.parse_args()


def emit(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, sort_keys=True))
        return
    status = payload.get("status", "unknown").upper()
    print(f"{status}: {payload.get('message', '')}")
    for key, value in payload.get("checks", {}).items():
        print(f"{key}: {value}")


def main() -> int:
    args = parse_args()

    try:
        import torch
    except Exception as exc:  # pragma: no cover - environment dependent
        emit(
            {
                "ok": False,
                "status": "error",
                "message": f"failed to import PyTorch: {exc}",
                "checks": {},
            },
            args.json,
        )
        return 2

    try:
        import dgl.sparse as dglsp
    except Exception as exc:  # pragma: no cover - environment dependent
        emit(
            {
                "ok": True,
                "status": "skip",
                "message": f"dgl.sparse is unavailable: {exc}",
                "checks": {},
            },
            args.json,
        )
        return 0

    try:
        row = torch.tensor([0, 0, 1, 2], dtype=torch.int64)
        col = torch.tensor([1, 2, 2, 0], dtype=torch.int64)
        val = torch.tensor([0.0, 1.0, 2.0, 3.0], dtype=torch.float32)
        matrix = dglsp.from_coo(row, col, val, shape=(3, 3))
        dense = torch.arange(12, dtype=torch.float32).reshape(3, 4)
        product = matrix @ dense
        softmax_matrix = dglsp.softmax(matrix, dim=1)

        indices = torch.stack([row, col])
        matrix_from_indices = dglsp.spmatrix(indices, val, shape=(3, 3))

        indptr = torch.tensor([0, 2, 3, 4], dtype=torch.int64)
        csr_indices = torch.tensor([1, 2, 2, 0], dtype=torch.int64)
        matrix_from_csr = dglsp.from_csr(indptr, csr_indices, val, shape=(3, 3))

        checks = {
            "shape": tuple(matrix.shape),
            "nnz": int(matrix.nnz),
            "product_shape": tuple(product.shape),
            "softmax_nnz": int(softmax_matrix.nnz),
            "spmatrix_nnz": int(matrix_from_indices.nnz),
            "csr_nnz": int(matrix_from_csr.nnz),
            "softmax_row0_sum": float(softmax_matrix.val[:2].sum()),
        }
    except Exception as exc:  # pragma: no cover - environment dependent
        emit(
            {
                "ok": False,
                "status": "error",
                "message": f"dgl.sparse operation failed: {exc}",
                "checks": {},
            },
            args.json,
        )
        return 1

    if checks["shape"] != (3, 3) or checks["nnz"] != 4 or checks["product_shape"] != (3, 4):
        emit(
            {
                "ok": False,
                "status": "error",
                "message": "unexpected sparse smoke shapes",
                "checks": checks,
            },
            args.json,
        )
        return 1
    if abs(checks["softmax_row0_sum"] - 1.0) > 1e-5:
        emit(
            {
                "ok": False,
                "status": "error",
                "message": "row-wise sparse softmax did not sum to 1 for row 0",
                "checks": checks,
            },
            args.json,
        )
        return 1

    emit(
        {
            "ok": True,
            "status": "ok",
            "message": "DGL sparse API smoke passed",
            "checks": checks,
        },
        args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
