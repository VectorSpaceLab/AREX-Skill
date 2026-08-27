#!/usr/bin/env python3
"""Safe signature and config probe for OpenAlphaTensor.

Example:
  python scripts/open_alpha_tensor_probe.py --config config.json
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="Optional config JSON path to validate")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report = {"import": None, "config": None}
    try:
        import open_alpha_tensor
        from open_alpha_tensor import train_alpha_tensor

        report["import"] = {
            "status": "ok",
            "file": getattr(open_alpha_tensor, "__file__", None),
            "signature": str(inspect.signature(train_alpha_tensor)),
        }
    except Exception as exc:
        report["import"] = {"status": "missing", "error": f"{type(exc).__name__}: {exc}"}

    if args.config:
        config_path = Path(args.config)
        try:
            data = json.loads(config_path.read_text())
            required = [
                "batch_size",
                "max_epochs",
                "action_memory",
                "optimizer",
                "weight_decay",
                "lr",
                "lr_decay_factor",
                "lr_decay_steps",
                "device",
                "len_data",
                "pct_synth",
                "n_synth_data",
                "limit_rank",
                "alpha",
                "beta",
                "matrix_size",
                "embed_dim",
                "actions_sampled",
                "n_actors",
                "mc_n_sim",
                "n_cob",
                "cob_prob",
                "cardinality_vector",
                "n_bar",
            ]
            report["config"] = {
                "status": "ok",
                "path": str(config_path),
                "missing_keys": [key for key in required if key not in data],
            }
        except Exception as exc:
            report["config"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
