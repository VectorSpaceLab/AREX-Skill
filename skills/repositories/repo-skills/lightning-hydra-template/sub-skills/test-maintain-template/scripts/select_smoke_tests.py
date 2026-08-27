#!/usr/bin/env python3
"""Print recommended Lightning-Hydra-Template pytest profiles."""

from __future__ import annotations

import argparse

PROFILES = {
    "offline": [
        ("pytest tests/test_configs.py -q", "Required no-training config/instantiation smoke; no MNIST download."),
    ],
    "quick": [
        ("pytest -k 'not slow' -q", "Template Makefile quick suite; may still download MNIST via fast-dev training."),
    ],
    "full": [
        ("pytest -q", "Full suite; requires data/cache/network and may run slow tests."),
    ],
    "gpu": [
        ("pytest tests/test_train.py::test_train_fast_dev_run_gpu -q", "GPU fast-dev train smoke; requires CUDA and MNIST data/cache/network."),
        ("pytest tests/test_train.py::test_train_epoch_gpu_amp -q", "GPU AMP one-epoch slow test; optional hardware gate."),
    ],
    "sweep": [
        ("pytest tests/test_sweeps.py -q", "Hydra/Optuna sweep tests; require sh on Linux/macOS and data/cache/network."),
    ],
    "rename": [
        ("python <skill>/sub-skills/customize-data-model/scripts/check_hydra_targets.py --repo-root .", "Find stale _target_ strings after package rename."),
        ("pytest tests/test_configs.py -q", "Verify renamed targets instantiate."),
        ("python -c \"from importlib.metadata import entry_points; print([e for e in entry_points(group='console_scripts') if e.name in {'train_command','eval_command'}])\"", "Verify console scripts point to renamed modules."),
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=sorted(PROFILES) + ["all"], default="offline")
    args = parser.parse_args()
    names = sorted(PROFILES) if args.profile == "all" else [args.profile]
    for name in names:
        print(f"\n[{name}]")
        for command, note in PROFILES[name]:
            print(command)
            print(f"  # {note}")
    print("\nNotes:")
    print("- Use logger=null or logger=csv for smoke tests that should not require online credentials.")
    print("- Do not treat GPU, sweep, or MNIST-download tests as required unless the user/environment explicitly needs them.")


if __name__ == "__main__":
    main()
