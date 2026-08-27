#!/usr/bin/env python3
"""Validate a proposed Frustum PointNets training configuration without running it."""
import argparse
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", choices=("frustum_pointnets_v1", "frustum_pointnets_v2"), default="frustum_pointnets_v1")
    p.add_argument("--num-point", type=int, default=1024)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--max-epoch", type=int, default=201)
    p.add_argument("--optimizer", choices=("adam", "momentum"), default="adam")
    p.add_argument("--no-intensity", action="store_true")
    p.add_argument("--train-pickle", type=Path)
    p.add_argument("--val-pickle", type=Path)
    p.add_argument("--restore-prefix", type=Path)
    p.add_argument("--custom-ops-ready", action="store_true")
    a = p.parse_args()
    errors = []
    for name, value in (("num-point", a.num_point), ("batch-size", a.batch_size), ("max-epoch", a.max_epoch)):
        if value <= 0:
            errors.append("%s must be positive" % name)
    for label, path in (("train pickle", a.train_pickle), ("val pickle", a.val_pickle)):
        if path is not None and not path.is_file():
            errors.append("%s does not exist: %s" % (label, path))
    if a.restore_prefix is not None:
        if not (Path(str(a.restore_prefix) + ".index").is_file() or a.restore_prefix.is_file()):
            errors.append("checkpoint prefix/index not found: %s" % a.restore_prefix)
    if a.model.endswith("v2") and not a.custom_ops_ready:
        errors.append("v2 requires separately verified sampling/grouping/interpolation custom ops")
    if errors:
        for error in errors:
            print("ERROR:", error, file=sys.stderr)
        return 1
    print("configuration OK: model=%s points=%d batch=%d channels=%d epochs=%d optimizer=%s" %
          (a.model, a.num_point, a.batch_size, 3 if a.no_intensity else 4, a.max_epoch, a.optimizer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
