#!/usr/bin/env python3
"""Static PocketFlow checkout checker for the generated repo skill.

This helper is safe by default: it does not train, download, convert, or mutate
models. Provide --check-tensorflow to also probe the current Python runtime.
"""

import argparse
import json
from pathlib import Path

REQUIRED_DIRS = ["learners", "nets", "datasets", "utils"]
REQUIRED_FILES = ["README.md", "requirement.txt", "path.conf.template"]


def inspect_repo(repo):
    result = {
        "repo": str(repo),
        "required_dirs": {},
        "required_files": {},
        "learner_modules": {},
        "warnings": [],
    }
    warnings = result["warnings"]
    for name in REQUIRED_DIRS:
        result["required_dirs"][name] = (repo / name).is_dir()
    for name in REQUIRED_FILES:
        result["required_files"][name] = (repo / name).is_file()
    learner_root = repo / "learners"
    for rel in [
        "learner_utils.py",
        "full_precision/learner.py",
        "channel_pruning/learner.py",
        "channel_pruning_rmt/learner.py",
        "discr_channel_pruning/learner.py",
        "weight_sparsification/learner.py",
        "uniform_quantization/learner.py",
        "uniform_quantization_tf/learner.py",
        "nonuniform_quantization/learner.py",
    ]:
        result["learner_modules"][rel] = (learner_root / rel).is_file()
    if not all(result["required_dirs"].values()):
        warnings.append("missing one or more core source directories")
    if not all(result["required_files"].values()):
        warnings.append("missing one or more core root files")
    return result


def check_tensorflow():
    out = {}
    try:
        import tensorflow as tf  # type: ignore
        out["tensorflow_version"] = getattr(tf, "__version__", "unknown")
        out["is_tf1"] = str(out["tensorflow_version"]).startswith("1.")
        out["has_tf_app_flags"] = hasattr(tf, "app") and hasattr(tf.app, "flags")
        try:
            from tensorflow.contrib.lite.python import lite_constants  # noqa: F401
            out["has_contrib_lite_constants"] = True
        except Exception as exc:
            out["has_contrib_lite_constants"] = False
            out["contrib_lite_error"] = str(exc)
    except Exception as exc:
        out["tensorflow_error"] = str(exc)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--check-tensorflow", action="store_true")
    args = parser.parse_args(argv)
    result = inspect_repo(args.repo_root)
    if args.check_tensorflow:
        result["tensorflow"] = check_tensorflow()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not result.get("warnings") else 2


if __name__ == "__main__":
    raise SystemExit(main())
