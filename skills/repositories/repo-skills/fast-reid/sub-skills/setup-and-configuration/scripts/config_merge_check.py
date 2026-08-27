#!/usr/bin/env python3
"""Validate a FastReID config merge without training or downloads.

This helper is safe by default. It only:
- adds a repository root to sys.path
- imports FastReID's config factory
- loads one config file
- applies optional KEY VALUE overrides
- optionally freezes the config
- prints selected merged keys as JSON

Examples
--------
python scripts/config_merge_check.py \
  --repo-root /path/to/fast-reid \
  --config-file configs/Market1501/bagtricks_R50.yml \
  --opts MODEL.DEVICE cpu

python scripts/config_merge_check.py \
  --repo-root /path/to/fast-reid \
  --config-file configs/DukeMTMC/sbs_R50.yml \
  --freeze \
  --show MODEL.DEVICE \
  --show MODEL.BACKBONE.NAME \
  --show DATASETS.NAMES \
  --show OUTPUT_DIR
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Iterable

DEFAULT_SHOW_KEYS = [
    "MODEL.DEVICE",
    "MODEL.META_ARCHITECTURE",
    "MODEL.BACKBONE.NAME",
    "MODEL.BACKBONE.DEPTH",
    "MODEL.BACKBONE.PRETRAIN",
    "MODEL.BACKBONE.PRETRAIN_PATH",
    "MODEL.WEIGHTS",
    "DATASETS.NAMES",
    "DATASETS.TESTS",
    "SOLVER.IMS_PER_BATCH",
    "TEST.IMS_PER_BATCH",
    "OUTPUT_DIR",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge a FastReID config and print selected keys without training.",
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        type=Path,
        help="Path to the FastReID repository root to add to sys.path.",
    )
    parser.add_argument(
        "--config-file",
        required=True,
        type=Path,
        help="Config file to merge. Relative paths are resolved against the current working directory first, then repo root.",
    )
    parser.add_argument(
        "--allow-unsafe",
        action="store_true",
        help="Opt in to yaml.unsafe_load for trusted configs only.",
    )
    parser.add_argument(
        "--freeze",
        action="store_true",
        help="Freeze the merged config before printing selected keys.",
    )
    parser.add_argument(
        "--show",
        dest="show_keys",
        action="append",
        default=[],
        metavar="KEY",
        help="Config key to print. Repeat to print more than one. Defaults to a setup-oriented key set when omitted.",
    )
    parser.add_argument(
        "--opts",
        nargs=argparse.REMAINDER,
        default=[],
        metavar="KEY VALUE",
        help="Command-line overrides as KEY VALUE pairs. Put --opts last.",
    )
    return parser


def resolve_config_path(repo_root: Path, raw_path: Path) -> Path:
    if raw_path.is_absolute():
        return raw_path

    cwd_candidate = (Path.cwd() / raw_path).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    repo_candidate = (repo_root / raw_path).resolve()
    if repo_candidate.exists():
        return repo_candidate

    return cwd_candidate


def add_repo_root_to_path(repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))


def to_builtin(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [to_builtin(v) for v in value]
    if isinstance(value, list):
        return [to_builtin(v) for v in value]
    if isinstance(value, set):
        return sorted(to_builtin(v) for v in value)
    if isinstance(value, Path):
        return str(value)
    return value


def get_by_dotted(config: Any, dotted_key: str) -> Any:
    current = config
    for part in dotted_key.split("."):
        if isinstance(current, Mapping):
            if part not in current:
                raise KeyError(dotted_key)
            current = current[part]
        else:
            try:
                current = getattr(current, part)
            except AttributeError as exc:
                raise KeyError(dotted_key) from exc
    return current


def print_selected_keys(config: Any, keys: Iterable[str]) -> dict[str, Any]:
    selected: dict[str, Any] = {}
    missing: list[str] = []
    for key in keys:
        try:
            selected[key] = to_builtin(get_by_dotted(config, key))
        except KeyError:
            missing.append(key)
    if missing:
        raise KeyError(
            "Missing config keys: {}".format(", ".join(missing))
        )
    return selected


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    repo_root = args.repo_root.expanduser().resolve()
    if not repo_root.is_dir():
        parser.error(f"--repo-root is not a directory: {repo_root}")

    add_repo_root_to_path(repo_root)

    try:
        from fastreid import __version__ as fastreid_version
        from fastreid.config import get_cfg
    except ModuleNotFoundError as exc:
        missing = exc.name or "an imported dependency"
        raise SystemExit(
            "FastReID config import failed because '{}' is missing. "
            "Install the FastReID runtime dependencies before running this check."
            .format(missing)
        ) from exc
    except ImportError as exc:
        message = str(exc)
        if "collections.Mapping" in message or "collections" in message:
            raise SystemExit(
                "FastReID config import failed on a Python 3.10+ "
                "collections.Mapping compatibility issue. Use Python 3.9 or "
                "patch the import sites before retrying."
            ) from exc
        raise SystemExit(f"FastReID config import failed: {exc}") from exc

    config_path = resolve_config_path(repo_root, args.config_file.expanduser())
    if not config_path.exists():
        parser.error(f"--config-file does not exist: {config_path}")

    opts = list(args.opts)
    if opts[:1] == ["--"]:
        opts = opts[1:]
    if len(opts) % 2 != 0:
        parser.error("--opts must contain an even number of KEY VALUE tokens")

    cfg = get_cfg()
    cfg.merge_from_file(str(config_path), allow_unsafe=args.allow_unsafe)
    if opts:
        cfg.merge_from_list(opts)
    if args.freeze:
        cfg.freeze()

    show_keys = args.show_keys or list(DEFAULT_SHOW_KEYS)
    payload = {
        "fastreid_version": fastreid_version,
        "repo_root": str(repo_root),
        "config_file": str(config_path),
        "allow_unsafe": bool(args.allow_unsafe),
        "frozen": bool(cfg.is_frozen()),
        "selected_keys": print_selected_keys(cfg, show_keys),
    }
    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
