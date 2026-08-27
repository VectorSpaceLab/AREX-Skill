#!/usr/bin/env python3
"""Check a Python environment for BayesianOptimization repo-skill usage.

This helper verifies package metadata, imports, key API signatures, and a tiny
core optimization smoke. With --run-subskill-smokes it also runs the bundled
sub-skill diagnostics. It performs no network access and writes only temporary
files unless a sub-skill helper is explicitly configured otherwise.
"""

from __future__ import annotations

import argparse
import inspect
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def require_distribution() -> str:
    try:
        return version("bayesian-optimization")
    except PackageNotFoundError as exc:
        raise SystemExit(
            "ERROR: distribution 'bayesian-optimization' is not installed in this Python. "
            "Install with `python -m pip install bayesian-optimization`."
        ) from exc


def import_and_inspect() -> None:
    try:
        import numpy
        import scipy
        import sklearn
        import bayes_opt
        from bayes_opt import BayesianOptimization, acquisition
        from bayes_opt.constraint import ConstraintModel
        from bayes_opt.domain_reduction import SequentialDomainReductionTransformer
        from bayes_opt.parameter import CategoricalParameter, FloatParameter, IntParameter
    except ImportError as exc:
        raise SystemExit(f"ERROR: import failed: {exc}") from exc

    objects = [
        BayesianOptimization,
        BayesianOptimization.maximize,
        BayesianOptimization.predict,
        BayesianOptimization.register,
        BayesianOptimization.probe,
        BayesianOptimization.suggest,
        BayesianOptimization.save_state,
        BayesianOptimization.load_state,
        acquisition.UpperConfidenceBound,
        acquisition.ExpectedImprovement,
        acquisition.ProbabilityOfImprovement,
        acquisition.ConstantLiar,
        acquisition.GPHedge,
        ConstraintModel,
        SequentialDomainReductionTransformer,
        FloatParameter,
        IntParameter,
        CategoricalParameter,
    ]
    for obj in objects:
        inspect.signature(obj)

    print(
        "PASS imports "
        f"bayes_opt={bayes_opt.__version__} "
        f"numpy={numpy.__version__} scipy={scipy.__version__} sklearn={sklearn.__version__}"
    )


def tiny_core_smoke(seed: int) -> None:
    from bayes_opt import BayesianOptimization

    def objective(x: float, y: float) -> float:
        return 1.0 - (x - 0.25) ** 2 - (y + 0.5) ** 2

    pbounds = {"x": (-1.0, 1.0), "y": (-1.0, 1.0)}
    optimizer = BayesianOptimization(f=objective, pbounds=pbounds, random_state=seed, verbose=0)
    optimizer.maximize(init_points=1, n_iter=1)
    if optimizer.max is None:
        raise SystemExit("ERROR: optimizer.max is None after tiny smoke")
    if set(optimizer.max["params"]) != set(pbounds):
        raise SystemExit(f"ERROR: unexpected best params keys: {optimizer.max!r}")
    print(f"PASS core_smoke observations={len(optimizer.res)} best_target={float(optimizer.max['target']):.6f}")


def run_subskill_smokes(skill_root: Path) -> None:
    commands = [
        [
            sys.executable,
            str(skill_root / "sub-skills/optimizer-workflows/scripts/bo_core_smoke.py"),
            "--init-points",
            "1",
            "--n-iter",
            "1",
            "--no-state",
        ],
        [
            sys.executable,
            str(skill_root / "sub-skills/optimizer-workflows/scripts/sklearn_hpo_smoke.py"),
            "--samples",
            "60",
            "--init-points",
            "1",
            "--n-iter",
            "1",
            "--skip-loss-demo",
        ],
        [
            sys.executable,
            str(skill_root / "sub-skills/acquisition-control/scripts/acquisition_probe.py"),
            "--include-constant-liar",
            "--n-random",
            "64",
            "--n-smart",
            "6",
        ],
        [
            sys.executable,
            str(skill_root / "sub-skills/advanced-domain-features/scripts/advanced_features_smoke.py"),
            "--check",
            "all",
        ],
        [
            sys.executable,
            str(skill_root / "sub-skills/repo-maintenance/scripts/select_native_checks.py"),
            "bayes_opt/acquisition.py",
        ],
    ]
    for command in commands:
        result = subprocess.run(command, text=True, capture_output=True, check=False, timeout=120)
        name = Path(command[1]).name
        if result.returncode != 0:
            print(result.stdout, end="")
            print(result.stderr, end="", file=sys.stderr)
            raise SystemExit(f"ERROR: sub-skill smoke failed for {name} with exit code {result.returncode}")
        first_line = result.stdout.strip().splitlines()[0] if result.stdout.strip() else "no output"
        print(f"PASS subskill_smoke {name}: {first_line}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify a Python environment for BayesianOptimization skill usage.")
    parser.add_argument("--seed", type=int, default=5, help="Random seed for the tiny core smoke.")
    parser.add_argument(
        "--run-subskill-smokes",
        action="store_true",
        help="Also execute bundled sub-skill smoke helpers with tiny budgets.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    dist_version = require_distribution()
    print(f"PASS distribution bayesian-optimization={dist_version}")
    import_and_inspect()
    tiny_core_smoke(seed=args.seed)
    if args.run_subskill_smokes:
        run_subskill_smokes(Path(__file__).resolve().parents[1])
    print("PASS check_env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
