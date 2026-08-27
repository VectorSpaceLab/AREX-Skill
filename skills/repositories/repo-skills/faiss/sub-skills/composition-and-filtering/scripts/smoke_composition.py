#!/usr/bin/env python3
"""Deterministic, CPU-only smoke for Faiss composition and filtering.

The script deliberately uses only in-memory public APIs. It does not read or
write an index, mutate inverted lists, start a server, or require the source
checkout. Run it from any working directory with the prepared faiss-cpu
package on PYTHONPATH.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate external-ID mapping/deletion, transformed refinement, "
            "selector routing, and read-only IVF inspection on tiny data."
        )
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1729,
        help="deterministic NumPy seed used for the tiny fixture (default: 1729)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the outcome as one JSON object instead of human-readable lines",
    )
    return parser.parse_args()


def fail(message: str) -> "NoReturn":
    raise AssertionError(message)


def main() -> int:
    args = parse_args()
    try:
        import numpy as np
        import faiss
    except Exception as exc:  # pragma: no cover - environment diagnostic
        print(
            "composition smoke requires an importable faiss-cpu and NumPy: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2

    rng = np.random.default_rng(args.seed)
    d = 4
    # Keep the fixture small but non-degenerate. The same rows are used by the
    # ID map and by the transformed/refined chain so row-order assumptions are
    # exercised by both paths.
    xb = rng.normal(size=(12, d)).astype("float32")
    xq = xb[:2].copy()
    # Keep enough independent training rows for the IVF smoke to avoid a
    # small-sample clustering warning while the indexed database stays tiny.
    xt = rng.normal(size=(48, d)).astype("float32")
    external_ids = (1000 + 10 * np.arange(len(xb))).astype("int64")
    np.ascontiguousarray(xb, dtype="float32")

    outcome: dict[str, Any] = {
        "faiss_version": getattr(faiss, "__version__", "unknown"),
        "compile_options": faiss.get_compile_options(),
        "seed": args.seed,
        "dimension": d,
    }

    # 1. IDMap2: labels are external IDs, selectors use that same namespace,
    # and deletion is checked without touching any persisted data.
    id_index = faiss.IndexIDMap2(faiss.IndexFlatL2(d))
    id_index.add_with_ids(xb, external_ids)
    if id_index.ntotal != len(xb):
        fail("IndexIDMap2 ntotal does not match the added rows")
    _, mapped_labels = id_index.search(xq, 3)
    if not set(mapped_labels.ravel().tolist()) & set(external_ids.tolist()):
        fail("IDMap2 search did not return external IDs")

    kept_ids = external_ids[[1, 5, 9]]
    selector = faiss.IDSelectorBatch(kept_ids)
    filtered_params = faiss.SearchParameters(sel=selector)
    _, filtered_labels = id_index.search(xq, 3, params=filtered_params)
    allowed = set(kept_ids.tolist()) | {-1}
    if not set(filtered_labels.ravel().tolist()) <= allowed:
        fail("IDMap selector was not applied in the external-ID namespace")

    removed_id = int(external_ids[3])
    removed = int(id_index.remove_ids(np.asarray([removed_id], dtype="int64")))
    if removed != 1 or id_index.ntotal != len(xb) - 1:
        fail("IDMap2 remove_ids did not remove exactly one external ID")
    try:
        id_index.reconstruct(removed_id)
    except RuntimeError:
        pass
    else:
        fail("removed ID was still reconstructable")
    outcome["id_map"] = {
        "ntotal_after_remove": int(id_index.ntotal),
        "removed": removed,
        "filtered_labels": filtered_labels.tolist(),
    }

    # 2. Transform -> refine: train and add at the outer boundary, then route
    # a refine parameter through the transform wrapper.
    base = faiss.IndexFlatL2(d)
    refined = faiss.IndexRefineFlat(base)
    transform = faiss.NormalizationTransform(d)
    composed = faiss.IndexPreTransform(transform, refined)
    composed.train(xb)
    composed.add(xb)
    if composed.ntotal != len(xb):
        fail("composed index ntotal is wrong")
    if refined.base_index.ntotal != refined.refine_index.ntotal:
        fail("refine children are not row-aligned")
    refine_params = faiss.IndexRefineSearchParameters(k_factor=2.0)
    nested_params = faiss.SearchParametersPreTransform(index_params=refine_params)
    distances, labels = composed.search(xq, 3, params=nested_params)
    if labels.shape != (len(xq), 3) or not np.isfinite(distances).all():
        fail("transformed refinement returned malformed results")
    if np.any(labels < 0) or np.any(labels >= len(xb)):
        fail("transformed refinement returned an invalid internal label")
    outcome["transformed_refine"] = {
        "ntotal": int(composed.ntotal),
        "base_ntotal": int(refined.base_index.ntotal),
        "refine_ntotal": int(refined.refine_index.ntotal),
        "labels": labels.tolist(),
    }

    # 3. IVF selector/parameter route and read-only metadata. nlist=1 keeps the
    # fixture cheap; no inverted-list mutation or persistence is performed.
    quantizer = faiss.IndexFlatL2(d)
    ivf = faiss.IndexIVFFlat(quantizer, d, 1)
    ivf.train(xt)
    ivf.add(xb)
    ivf_params = faiss.SearchParametersIVF(
        nprobe=1,
        max_codes=0,
        sel=faiss.IDSelectorRange(0, 4),
    )
    _, ivf_labels = ivf.search(xq, 3, params=ivf_params)
    ivf_allowed = {-1, 0, 1, 2, 3}
    if not set(ivf_labels.ravel().tolist()) <= ivf_allowed:
        fail("IVF selector returned an ID outside its selected range")
    ivf_view = faiss.extract_index_ivf(ivf)
    list_sizes = [int(ivf_view.invlists.list_size(i)) for i in range(ivf_view.nlist)]
    if sum(list_sizes) != int(ivf.ntotal):
        fail("read-only IVF list-size inspection disagrees with ntotal")
    outcome["ivf_inspection"] = {
        "nlist": int(ivf_view.nlist),
        "nprobe": int(ivf.nprobe),
        "list_sizes": list_sizes,
        "direct_map_type": int(ivf.direct_map.type),
        "selected_labels": ivf_labels.tolist(),
    }

    # Exercise the documented lifetime boundary: wrappers should keep their
    # constructor children alive after local variables are deleted. This is
    # intentionally a read/search check, not an ownership-flag mutation.
    del transform, base, quantizer, selector, filtered_params, refine_params, nested_params
    gc.collect()
    composed.search(xq[:1], 2)
    ivf.search(xq[:1], 2)
    outcome["lifetime_check"] = "passed"

    if args.json:
        print(json.dumps(outcome, sort_keys=True))
    else:
        print("composition smoke: PASS")
        print(f"Faiss {outcome['faiss_version']} ({outcome['compile_options']})")
        print(f"IDMap2 removed={removed}; filtered labels={filtered_labels.tolist()}")
        print(f"refine labels={labels.tolist()}")
        print(
            "IVF lists="
            f"{list_sizes}, direct_map_type={outcome['ivf_inspection']['direct_map_type']}"
        )
        print("child lifetime after local deletion: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
