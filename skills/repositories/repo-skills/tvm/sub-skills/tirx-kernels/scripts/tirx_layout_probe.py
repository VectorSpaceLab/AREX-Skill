#!/usr/bin/env python3
"""Run CPU-safe TIRx layout API probes."""
from __future__ import annotations

import argparse
import json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args(argv)

    from tvm.tirx.layout import R, S, TileLayout, laneid, m, warpid, wg_local_layout

    layouts = {
        "memory_3d": TileLayout(S[(2, 3, 4) : (12 @ m, 4 @ m, 1 @ m)]),
        "lane_shard": TileLayout(S[8 : 4 @ laneid]),
        "lane_shard_replica": TileLayout(S[8 : 4 @ laneid] + R[4 : 1 @ laneid]),
        "multi_offset": TileLayout(S[8 : 4 @ laneid] + 1 @ laneid + 2 @ warpid + 64),
        "wg_local": wg_local_layout(16),
    }
    result = {}
    for name, layout in layouts.items():
        canonical = layout.canonicalize()
        result[name] = {
            "text": str(layout),
            "canonical": str(canonical),
            "well_formed": bool(canonical.verify_well_formed()),
            "scope": tuple(x.name for x in canonical.get_scope()) if canonical.get_scope() else None,
        }
    if not all(item["well_formed"] for item in result.values()):
        raise SystemExit("one or more baseline layouts were not well formed")
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for name, item in result.items():
            print(f"{name}: well_formed={item['well_formed']} scope={item['scope']} canonical={item['canonical']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
