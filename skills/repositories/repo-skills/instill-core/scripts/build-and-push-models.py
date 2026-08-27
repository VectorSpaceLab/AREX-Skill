#!/usr/bin/env python3
"""Build and push Instill Core dummy models from a model inventory.

Safe by default: the helper starts in dry-run mode and only performs networked
build/push actions when --execute is supplied.

Examples:
  python scripts/build-and-push-models.py --inventory-dir integration-test/models --registry-url localhost:5001
  python scripts/build-and-push-models.py --inventory-dir integration-test/models --registry-url localhost:5001 --execute
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", required=True, help="Directory that contains inventory.json and model subdirectories")
    parser.add_argument("--registry-url", required=True, help="Registry URL passed to instill push")
    parser.add_argument("--instill-bin", default="instill", help="Path to the instill CLI (default: instill on PATH)")
    parser.add_argument("--sdk-path", help="Explicit path passed to instill build -e; inferred from the installed instill module when omitted")
    parser.add_argument("--execute", action="store_true", help="Actually run build and push commands instead of dry-run")
    return parser.parse_args()


def load_inventory(inventory_dir: Path) -> list[dict[str, object]]:
    inventory_file = inventory_dir / "inventory.json"
    if not inventory_file.is_file():
        raise FileNotFoundError(f"inventory file not found: {inventory_file}")
    with inventory_file.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError("inventory.json must contain a JSON array")
    return data


def infer_sdk_path(explicit: str | None) -> str:
    if explicit:
        return explicit
    try:
        import instill  # type: ignore
    except Exception as exc:  # pragma: no cover - only used when execution is requested
        raise RuntimeError(
            "could not import the instill module; pass --sdk-path explicitly or install the Instill SDK environment"
        ) from exc
    return str(Path(instill.__file__).resolve().parent.parent)


def run_command(cmd: list[str], cwd: Path, execute: bool) -> None:
    print("  ", " ".join(cmd), f"(cwd={cwd})")
    if execute:
        subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> int:
    args = parse_args()
    inventory_dir = Path(args.inventory_dir).expanduser().resolve()
    if not inventory_dir.is_dir():
        raise SystemExit(f"inventory directory not found: {inventory_dir}")

    instill_bin = args.instill_bin
    if args.execute:
        if os.path.isabs(args.instill_bin):
            if not Path(args.instill_bin).exists():
                raise SystemExit(
                    f"instill CLI not found: {args.instill_bin}. Install the SDK or pass --instill-bin explicitly."
                )
        else:
            resolved = shutil.which(args.instill_bin)
            if not resolved:
                raise SystemExit(
                    f"instill CLI not found: {args.instill_bin}. Install the SDK or pass --instill-bin explicitly."
                )
            instill_bin = resolved

    inventory = load_inventory(inventory_dir)
    sdk_path = args.sdk_path
    if args.execute:
        sdk_path = infer_sdk_path(args.sdk_path)

    missing_dirs: list[str] = []
    for entry in inventory:
        model_id = entry.get("id")
        if not isinstance(model_id, str) or not model_id:
            raise SystemExit(f"invalid inventory entry without a string id: {entry!r}")
        model_dir = inventory_dir / model_id
        if not model_dir.is_dir():
            print(f"  [skip] missing model directory for {model_id}: {model_dir}", file=sys.stderr)
            missing_dirs.append(model_id)
            continue
        image_ref = f"admin/{model_id}:dev"
        print(f"Model {model_id}")
        build_cmd = [instill_bin, "build", image_ref]
        if sdk_path:
            build_cmd.extend(["-e", sdk_path])
        push_cmd = [instill_bin, "push", image_ref, "-u", args.registry_url]
        run_command(build_cmd, model_dir, args.execute)
        run_command(push_cmd, model_dir, args.execute)

    if missing_dirs:
        raise SystemExit(f"missing model directories for: {', '.join(sorted(missing_dirs))}")

    if not args.execute:
        print("\nDry run completed. Re-run with --execute when you want to build and push the models.")
    else:
        print("\nModel build and push completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
