#!/usr/bin/env python3
"""Run a deterministic, no-network Faiss codec and binary smoke.

The script intentionally uses only tiny generated data.  It also contains a
small, conservative code-size parser for common factory forms; the installed
index's ``sa_code_size()`` remains authoritative for unusual wrappers/codecs.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from typing import Iterable


class SmokeError(ValueError):
    """A user configuration or supported smoke invariant is invalid."""


_FLOAT_FACTORIES = (
    "PQ2x4",
    "SQ4",
    "IVF4,PQ2x4",
    "IVF4,SQ4",
    "PQ4x4fs_32",
)
_BINARY_FACTORIES = ("BFlat", "BIVF4")


def _ceil_bits(bits: int) -> int:
    return (bits + 7) // 8


def _strip_idmap(description: str) -> str:
    if description.startswith("IDMap2,") or description.startswith("IDMap,"):
        return description.split(",", 1)[1]
    if description.endswith(",IDMap2") or description.endswith(",IDMap"):
        return description.rsplit(",", 1)[0]
    return description


def _float_code_size(d: int, description: str) -> int:
    """Return a conservative payload estimate for a small safe subset."""
    description = _strip_idmap(description)

    # The helper mirrors the useful, non-destructive portion of Faiss's
    # factory_tools: refinement stores both representations.
    match = re.fullmatch(r"(.+),Refine\(([^()]+)\)", description)
    if match:
        return _float_code_size(d, match.group(1)) + _float_code_size(
            d, match.group(2)
        )

    # An IVF prefix changes candidate routing, not the codec payload.
    match = re.fullmatch(r"IVF\d+(?:_HNSW\d+)?(?:\([^()]+\))?,(.+)", description)
    if match:
        return _float_code_size(d, match.group(1))

    if description == "Flat":
        return d * 4

    match = re.fullmatch(r"PQ(\d+)(?:x(\d+))?(np)?", description)
    if match:
        m = int(match.group(1))
        nbits = int(match.group(2) or 8)
        _validate_pq_shape(d, m, nbits)
        return _ceil_bits(m * nbits)

    match = re.fullmatch(r"PQ(\d+)x4fs(?:r)?(?:_(\d+))?", description)
    if match:
        m = int(match.group(1))
        bbs = int(match.group(2) or 32)
        _validate_pq_shape(d, m, 4)
        if bbs <= 0 or bbs % 32:
            raise SmokeError("fast-scan block size must be a positive multiple of 32")
        return _ceil_bits(m * 4)

    if description in {"SQ8", "SQ8_direct", "SQ8_direct_signed"}:
        return d
    if description == "SQ4":
        return _ceil_bits(4 * d)
    if description == "SQ6":
        return _ceil_bits(6 * d)
    if description in {"SQfp16", "SQbf16"}:
        return d * 2

    raise SmokeError(
        f"unsupported safe float factory {description!r}; use one of "
        f"{', '.join(_FLOAT_FACTORIES)} or --code-size-only with a supported form"
    )


def _validate_pq_shape(d: int, m: int, nbits: int) -> None:
    if m <= 0:
        raise SmokeError("PQ M must be positive")
    if d <= 0 or d % m:
        raise SmokeError(f"PQ requires d % M == 0, got d={d}, M={m}")
    if nbits <= 0 or nbits > 24:
        raise SmokeError("PQ nbits must be in the practical range 1..24")


def _binary_code_size(d: int, description: str) -> int:
    description = _strip_idmap(description)
    if d <= 0 or d % 8:
        raise SmokeError(f"binary dimension must be a positive multiple of 8, got {d}")
    if description in {"BFlat"}:
        return d // 8
    if re.fullmatch(r"BIVF\d+(?:_BHNSW\d+)?", description):
        return d // 8
    if re.fullmatch(r"BHNSW\d+", description):
        return d // 8
    if re.fullmatch(r"BHash\d+(?:x\d+)?", description):
        return d // 8
    raise SmokeError(f"unsupported safe binary factory {description!r}")


def _is_binary(description: str) -> bool:
    return _strip_idmap(description).startswith(("BFlat", "BIVF", "BHNSW", "BHash"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke tiny deterministic PQ/SQ/IVF and packed binary Faiss "
            "workflows; downloads nothing."
        )
    )
    parser.add_argument(
        "--factory",
        help="one supported factory; omit to run the complete tiny smoke",
    )
    parser.add_argument(
        "--dimension",
        type=int,
        default=16,
        help="vector dimension (default: 16; binary dimensions must be divisible by 8)",
    )
    parser.add_argument(
        "--metric",
        choices=("l2", "ip"),
        default="l2",
        help="float metric for the selected workflow (default: l2)",
    )
    parser.add_argument(
        "--code-size-only",
        action="store_true",
        help="validate and print conservative payload sizes without importing Faiss",
    )
    return parser


def _selected_factories(factory: str | None) -> list[str]:
    if factory is None:
        return [*_FLOAT_FACTORIES, *_BINARY_FACTORIES]
    if not factory.strip() or factory.strip().lower() == "all":
        raise SmokeError("--factory must be a non-empty single factory, not 'all'")
    return [factory.strip()]


def _payload_size(d: int, factory: str) -> int:
    return _binary_code_size(d, factory) if _is_binary(factory) else _float_code_size(d, factory)


def _make_float_data(d: int):
    import numpy as np

    rs = np.random.RandomState(1234)
    xtrain = rs.normal(size=(1024, d)).astype("float32")
    xb = rs.normal(size=(160, d)).astype("float32")
    xq = rs.normal(size=(8, d)).astype("float32")
    return tuple(np.ascontiguousarray(x) for x in (xtrain, xb, xq))


def _make_binary_data(d: int):
    import numpy as np

    if d % 8:
        raise SmokeError("binary dimension must be divisible by 8")
    rs = np.random.RandomState(1234)
    bits = rs.randint(0, 2, size=(1192, d)).astype("uint8")
    packed = np.packbits(bits, axis=1, bitorder="little")
    return tuple(
        np.ascontiguousarray(x, dtype="uint8")
        for x in (packed[:1024], packed[1024:1184], packed[1184:])
    )


def _run_float(factory: str, d: int, metric_name: str) -> dict:
    import faiss
    import numpy as np

    expected_payload = _float_code_size(d, factory)
    metric = faiss.METRIC_L2 if metric_name == "l2" else faiss.METRIC_INNER_PRODUCT
    xtrain, xb, xq = _make_float_data(d)

    try:
        index = faiss.index_factory(d, factory, metric)
    except Exception as exc:  # Faiss uses RuntimeError for parser/constraints.
        raise SmokeError(f"Faiss rejected {factory!r} for d={d}: {exc}") from exc

    if not index.is_trained:
        index.train(xtrain)
    if not index.is_trained:
        raise SmokeError(f"{factory!r} remained untrained after train()")
    index.add(xb)
    k = min(4, len(xb))
    distances, labels = index.search(xq, k)
    if distances.shape != (len(xq), k) or labels.shape != (len(xq), k):
        raise SmokeError(f"unexpected search shapes for {factory!r}")
    if not np.isfinite(distances).all() or (labels < 0).any():
        raise SmokeError(f"invalid search result for {factory!r}")

    actual_code_size = int(index.sa_code_size())
    if actual_code_size < expected_payload:
        raise SmokeError(
            f"{factory!r} reports sa_code_size={actual_code_size}, "
            f"below payload estimate {expected_payload}"
        )
    codes = index.sa_encode(xb[:4])
    if codes.dtype != np.uint8 or codes.shape != (4, actual_code_size):
        raise SmokeError(f"unexpected standalone code shape for {factory!r}: {codes.shape}")
    decoded = index.sa_decode(codes)
    if decoded.shape != (4, d) or decoded.dtype != np.float32:
        raise SmokeError(f"unexpected decoded shape/type for {factory!r}")
    # IVF reconstruction uses a direct map. Building one is explicit and
    # bounded for this tiny smoke; production ownership/lifecycle belongs to
    # the composition sibling.
    if factory.startswith("IVF") and hasattr(index, "make_direct_map"):
        index.make_direct_map()
    # Exercise reconstruction without asserting lossy equality.
    reconstruction = index.reconstruct(0)
    if reconstruction.shape != (d,) or reconstruction.dtype != np.float32:
        raise SmokeError(f"unexpected reconstruct result for {factory!r}")

    return {
        "factory": factory,
        "kind": "float",
        "dimension": d,
        "metric": metric_name,
        "ntotal": int(index.ntotal),
        "payload_bytes_estimate": expected_payload,
        "sa_code_size": actual_code_size,
        "status": "ok",
    }


def _run_binary(factory: str, d: int) -> dict:
    import faiss
    import numpy as np

    expected_code_size = _binary_code_size(d, factory)
    xtrain, xb, xq = _make_binary_data(d)
    try:
        index = faiss.index_binary_factory(d, factory)
    except Exception as exc:
        raise SmokeError(f"Faiss rejected binary factory {factory!r}: {exc}") from exc

    if not index.is_trained:
        index.train(xtrain)
    if not index.is_trained:
        raise SmokeError(f"binary {factory!r} remained untrained after train()")
    index.add(xb)
    k = min(4, len(xb))
    distances, labels = index.search(xq, k)
    if distances.shape != (len(xq), k) or labels.shape != (len(xq), k):
        raise SmokeError(f"unexpected binary search shapes for {factory!r}")
    if distances.dtype != np.int32 or (labels < 0).any():
        raise SmokeError(f"invalid binary search result for {factory!r}")
    if int(index.code_size) != expected_code_size:
        raise SmokeError(
            f"binary code_size={index.code_size}, expected {expected_code_size}"
        )
    if factory.startswith("BIVF") and hasattr(index, "make_direct_map"):
        index.make_direct_map()
    reconstructed = index.reconstruct(0)
    if reconstructed.dtype != np.uint8 or reconstructed.shape != (expected_code_size,):
        raise SmokeError(f"unexpected binary reconstruction for {factory!r}")

    return {
        "factory": factory,
        "kind": "binary",
        "dimension": d,
        "code_size": expected_code_size,
        "ntotal": int(index.ntotal),
        "status": "ok",
    }


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.dimension <= 0:
            raise SmokeError("--dimension must be positive")
        factories = _selected_factories(args.factory)
        sizes = [{"factory": f, "bytes": _payload_size(args.dimension, f)} for f in factories]
        if args.code_size_only:
            print(json.dumps({"dimension": args.dimension, "code_sizes": sizes}, sort_keys=True))
            return 0

        results = []
        for factory in factories:
            if _is_binary(factory):
                results.append(_run_binary(factory, args.dimension))
            else:
                results.append(_run_float(factory, args.dimension, args.metric))
        print(json.dumps({"results": results}, sort_keys=True))
        return 0
    except (SmokeError, ImportError, RuntimeError, AssertionError) as exc:
        print(f"smoke_codecs.py: error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
