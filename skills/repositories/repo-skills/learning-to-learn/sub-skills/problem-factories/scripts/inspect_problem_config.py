#!/usr/bin/env python3
"""Inspect problem factories and safe util.get_config mappings.

The script prints the requested problem summary without downloading MNIST/CIFAR
by default. It only calls util.get_config for the non-data-backed safe keys.
"""

from __future__ import annotations

import argparse
import json
import pprint
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

SAFE_UTIL_KEYS = {"simple", "simple-multi", "quadratic"}

STATIC_CATALOG: Dict[str, Dict[str, Any]] = {
    "simple": {
        "display_name": "simple",
        "source_factory": "problems.simple()",
        "readme_name": "simple",
        "util_key": "simple",
        "data_backed": False,
        "summary": "One-variable quadratic f(x)=x^2.",
        "notes": ["Pure graph construction."],
    },
    "simple-multi": {
        "display_name": "simple-multi",
        "source_factory": "problems.simple_multi_optimizer(num_dims=2)",
        "readme_name": "simple-multi",
        "util_key": "simple-multi",
        "aliases": ["simple_multi_optimizer"],
        "data_backed": False,
        "summary": "Independent scalar quadratics over x_0, x_1, ...",
        "notes": ["Default num_dims is 2.", "Use matching variable names if you change num_dims."],
    },
    "quadratic": {
        "display_name": "quadratic",
        "source_factory": "problems.quadratic(batch_size=128, num_dims=10)",
        "readme_name": "quadratic",
        "util_key": "quadratic",
        "data_backed": False,
        "summary": "Batched linear-quadratic loss with trainable x and fixed w, y.",
        "notes": ["Pure graph construction."],
    },
    "ensemble": {
        "display_name": "ensemble",
        "source_factory": "problems.ensemble(problems, weights=None)",
        "readme_name": None,
        "util_key": None,
        "data_backed": False,
        "summary": "Weighted sum of subproblem losses.",
        "notes": [
            "Not a util.get_config key.",
            "weights must match the problems list length when provided.",
        ],
    },
    "mnist": {
        "display_name": "mnist",
        "source_factory": 'problems.mnist(layers=(20,), activation="sigmoid", batch_size=128, mode=...)',
        "readme_name": "mnist",
        "util_key": "mnist",
        "data_backed": True,
        "summary": "MNIST classifier with a small MLP.",
        "notes": [
            "Factory loads the dataset during setup.",
            "activation only accepts sigmoid or relu.",
        ],
    },
    "cifar": {
        "display_name": "cifar",
        "source_factory": 'problems.cifar10("cifar10", conv_channels=(16, 16, 16), linear_layers=(32,), mode=...)',
        "readme_name": "cifar",
        "util_key": "cifar",
        "data_backed": True,
        "summary": "CIFAR-10 classifier with a shared coordinatewise optimizer net.",
        "notes": [
            "Factory may download/extract CIFAR-10 and register queue runners.",
            "mode only accepts train or test.",
        ],
    },
    "cifar-multi": {
        "display_name": "cifar-multi",
        "source_factory": 'problems.cifar10("cifar10", conv_channels=(16, 16, 16), linear_layers=(32,), mode=...)',
        "readme_name": "cifar-multi",
        "util_key": "cifar-multi",
        "data_backed": True,
        "summary": "CIFAR-10 classifier split across conv and fc optimizer nets.",
        "notes": [
            "Factory may download/extract CIFAR-10 and register queue runners.",
            "mode only accepts train or test.",
        ],
    },
    "cifar10": {
        "display_name": "cifar10",
        "source_factory": "problems.cifar10(path, conv_channels=(16, 16, 16), linear_layers=(32,), mode=...)",
        "readme_name": None,
        "util_key": None,
        "data_backed": True,
        "summary": "Source factory behind the README's CIFAR-10 entries.",
        "notes": [
            "This source factory underlies both util.get_config keys: cifar and cifar-multi.",
            "It is data-backed, so the script uses a static summary instead of calling it.",
        ],
    },
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect learning-to-learn problem factories and safe config mappings.",
    )
    parser.add_argument(
        "--problem",
        help=(
            "Problem name or source-factory alias to inspect. "
            "If omitted, the script lists the catalog."
        ),
    )
    parser.add_argument(
        "--path",
        help="Optional path used for checkpoint names or static dataset-cache rendering.",
    )
    parser.add_argument(
        "--repo-root",
        help="Path to the source checkout that contains util.py and problems.py.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable summary.",
    )
    return parser.parse_args()


def infer_repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "util.py").exists() and (parent / "problems.py").exists():
            return parent
    return Path.cwd().resolve()


def resolve_repo_root(raw: Optional[str]) -> Path:
    if raw:
        return Path(raw).expanduser().resolve()
    return infer_repo_root()


def load_util(repo_root: Path) -> Tuple[Optional[Any], Optional[str]]:
    sys.path.insert(0, str(repo_root))
    try:
        import util  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        return None, f"{type(exc).__name__}: {exc}"
    return util, None


def normalize_problem_name(name: str) -> str:
    aliases = {
        "simple_multi_optimizer": "simple-multi",
    }
    return aliases.get(name, name)


def render_path(path_text: Optional[str]) -> Optional[str]:
    if path_text is None:
        return None
    return str(Path(path_text).expanduser())


def to_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [to_jsonable(v) for v in value]
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    return value


def static_default_net(name: str, path: Optional[str]) -> Dict[str, Any]:
    config = {
        "net": "CoordinateWiseDeepLSTM",
        "net_options": {
            "layers": (20, 20),
            "preprocess_name": "LogAndSign",
            "preprocess_options": {"k": 5},
            "scale": 0.01,
        },
    }
    if path is None:
        config["net_path"] = None
    else:
        config["net_path"] = str(Path(path) / f"{name}.l2l")
    return config


def static_cifar_variants(path: Optional[str]) -> Dict[str, Any]:
    mode = "train" if path is None else "test"
    return {
        "cifar": {
            "problem_factory": 'problems.cifar10("cifar10", conv_channels=(16, 16, 16), linear_layers=(32,), mode=...)',
            "net_config": {"cw": static_default_net("cw", path)},
            "net_assignments": None,
            "mode": mode,
        },
        "cifar-multi": {
            "problem_factory": 'problems.cifar10("cifar10", conv_channels=(16, 16, 16), linear_layers=(32,), mode=...)',
            "net_config": {
                "conv": static_default_net("conv", path),
                "fc": static_default_net("fc", path),
            },
            "net_assignments": [
                (
                    "conv",
                    [
                        "conv_net_2d/conv_2d_0/w",
                        "conv_net_2d/conv_2d_1/w",
                        "conv_net_2d/conv_2d_2/w",
                    ],
                ),
                (
                    "fc",
                    [
                        "conv_net_2d/conv_2d_0/b",
                        "conv_net_2d/conv_2d_1/b",
                        "conv_net_2d/conv_2d_2/b",
                        "conv_net_2d/batch_norm_0/beta",
                        "conv_net_2d/batch_norm_1/beta",
                        "conv_net_2d/batch_norm_2/beta",
                        "mlp/linear_0/w",
                        "mlp/linear_1/w",
                        "mlp/linear_0/b",
                        "mlp/linear_1/b",
                        "mlp/batch_norm/beta",
                    ],
                ),
            ],
            "mode": mode,
        },
    }


def safe_util_summary(util_mod: Any, problem_name: str, path: Optional[str]) -> Dict[str, Any]:
    problem, net_config, net_assignments = util_mod.get_config(problem_name, path)
    entry = STATIC_CATALOG[problem_name]
    return {
        "requested_problem": problem_name,
        "display_problem": entry["display_name"],
        "source_factory": entry["source_factory"],
        "derived_from": "util.get_config",
        "path": path,
        "problem_callable": entry["source_factory"],
        "net_config": net_config,
        "net_assignments": net_assignments,
        "notes": entry.get("notes", []),
    }


def static_summary(problem_name: str, path: Optional[str]) -> Dict[str, Any]:
    entry = STATIC_CATALOG[problem_name]
    result: Dict[str, Any] = {
        "requested_problem": problem_name,
        "display_problem": entry["display_name"],
        "source_factory": entry["source_factory"],
        "derived_from": "static_catalog",
        "path": path,
        "data_backed": entry.get("data_backed", False),
        "summary": entry.get("summary"),
        "notes": entry.get("notes", []),
    }
    if problem_name == "mnist":
        mode = "train" if path is None else "test"
        result["problem_factory"] = 'problems.mnist(layers=(20,), activation="sigmoid", batch_size=128, mode=...)'
        result["net_config"] = {"cw": static_default_net("cw", path)}
        result["mode"] = mode
        result["net_assignments"] = None
    elif problem_name in {"cifar", "cifar-multi"}:
        result.update(static_cifar_variants(path)[problem_name])
    elif problem_name == "cifar10":
        result["variants"] = static_cifar_variants(path)
    elif problem_name == "simple":
        result["problem_factory"] = "problems.simple()"
        result["net_config"] = {
            "cw": {
                "net": "CoordinateWiseDeepLSTM",
                "net_options": {"layers": (), "initializer": "zeros"},
                "net_path": None if path is None else str(Path(path) / "cw.l2l"),
            }
        }
        result["net_assignments"] = None
    elif problem_name == "simple-multi":
        result["problem_factory"] = "problems.simple_multi_optimizer(num_dims=2)"
        result["net_config"] = {
            "cw": {
                "net": "CoordinateWiseDeepLSTM",
                "net_options": {"layers": (), "initializer": "zeros"},
                "net_path": None if path is None else str(Path(path) / "cw.l2l"),
            },
            "adam": {
                "net": "Adam",
                "net_options": {"learning_rate": 0.1},
            },
        }
        result["net_assignments"] = [("cw", ["x_0"]), ("adam", ["x_1"])]
    elif problem_name == "quadratic":
        result["problem_factory"] = "problems.quadratic(batch_size=128, num_dims=10)"
        result["net_config"] = {
            "cw": {
                "net": "CoordinateWiseDeepLSTM",
                "net_options": {"layers": (20, 20)},
                "net_path": None if path is None else str(Path(path) / "cw.l2l"),
            }
        }
        result["net_assignments"] = None
    elif problem_name == "ensemble":
        result["problem_factory"] = "problems.ensemble(problems, weights=None)"
        result["net_config"] = None
        result["net_assignments"] = None
    return result


def catalog_listing() -> Dict[str, Any]:
    rows = []
    for key in ["simple", "simple-multi", "quadratic", "ensemble", "mnist", "cifar", "cifar-multi", "cifar10"]:
        entry = STATIC_CATALOG[key]
        rows.append(
            {
                "problem": key,
                "summary": entry.get("summary"),
                "source_factory": entry.get("source_factory"),
                "data_backed": entry.get("data_backed", False),
            }
        )
    return {"catalog": rows}


def format_text(result: Dict[str, Any]) -> str:
    return pprint.pformat(result, sort_dicts=True, width=100)


def main() -> int:
    args = parse_args()
    repo_root = resolve_repo_root(args.repo_root)
    path = render_path(args.path)
    problem_name = normalize_problem_name(args.problem) if args.problem else None

    util_mod = None
    util_error = None
    if problem_name in SAFE_UTIL_KEYS:
        util_mod, util_error = load_util(repo_root)

    if problem_name is None:
        payload: Dict[str, Any] = catalog_listing()
        if util_error:
            payload["util_import_error"] = util_error
    else:
        if problem_name in SAFE_UTIL_KEYS and util_mod is not None:
            payload = safe_util_summary(util_mod, problem_name, path)
        else:
            payload = static_summary(problem_name, path)
            if util_error:
                payload["util_import_error"] = util_error
            elif problem_name in SAFE_UTIL_KEYS and util_mod is None:
                payload["util_import_error"] = "util import unavailable"
        payload["input_problem"] = args.problem
        if args.problem != problem_name:
            payload["normalized_problem"] = problem_name

    if args.json:
        print(json.dumps(to_jsonable(payload), indent=2, sort_keys=True))
    else:
        if problem_name is None:
            for row in payload["catalog"]:
                print(f"{row['problem']}: {row['summary']}")
            if "util_import_error" in payload:
                print(f"util_import_error: {payload['util_import_error']}")
        else:
            print(format_text(to_jsonable(payload)))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
