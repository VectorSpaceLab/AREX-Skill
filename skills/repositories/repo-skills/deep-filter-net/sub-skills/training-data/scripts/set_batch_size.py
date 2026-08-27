#!/usr/bin/env python3
"""Apply or record DeepFilterNet host-specific batch sizes.

The helper mirrors the small DeepFilterNet training utility without importing the
repository. It edits only the training config batch-size keys and the selected
host section in the host-batch-size config.
"""

from __future__ import annotations

import argparse
import os
from configparser import ConfigParser
from pathlib import Path
from socket import gethostname
from typing import List, Optional, Sequence, Tuple


def cast_bool(value) -> bool:
    value_s = str(value).strip().lower()
    if value_s in {"true", "yes", "y", "on", "1"}:
        return True
    if value_s in {"false", "no", "n", "off", "0", "", "none"}:
        return False
    raise ValueError(f"Cannot parse boolean value: {value!r}")


def read_parser(path: Path, create: bool = False) -> ConfigParser:
    parser = ConfigParser()
    if not path.exists():
        if create:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        else:
            raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as handle:
        parser.read_file(handle)
    return parser


def write_parser_if_changed(path: Path, parser: ConfigParser, changed: bool) -> None:
    if not changed:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        parser.write(handle)


def update_batch_size(
    host_key: str,
    config_parser: ConfigParser,
    host_bs_parser: ConfigParser,
    config_key: str,
    batchconfig_key: str,
) -> Tuple[bool, bool]:
    """Update one batch-size key.

    Returns (training_config_changed, host_config_changed).
    """
    current_bs = None
    if config_parser.has_section("train"):
        current_bs = config_parser.get("train", config_key, fallback=None)

    batchconfig_bs = None
    if host_bs_parser.has_section(host_key):
        batchconfig_bs = host_bs_parser.get(host_key, batchconfig_key, fallback=None)

    config_changed = False
    host_bs_changed = False

    if batchconfig_bs is not None:
        if current_bs is not None and batchconfig_bs != current_bs:
            print(
                f"Found host-specific {batchconfig_key}={batchconfig_bs!r} for host {host_key}. "
                f"Updating [train] {config_key}."
            )
            if not config_parser.has_section("train"):
                config_parser.add_section("train")
            config_parser.set("train", config_key, batchconfig_bs)
            config_changed = True
        elif current_bs is None:
            print(
                f"Host-specific {batchconfig_key} exists for {host_key}, but [train] {config_key} "
                "is absent; leaving training config unchanged."
            )
    elif current_bs is not None:
        print(
            f"Host-specific {batchconfig_key} not found for host {host_key}. "
            f"Recording current [train] {config_key}={current_bs!r}."
        )
        if not host_bs_parser.has_section(host_key):
            host_bs_parser.add_section(host_key)
        host_bs_parser.set(host_key, batchconfig_key, current_bs)
        host_bs_changed = True

    return config_changed, host_bs_changed


def apply_host_batch_sizes(config_path: Path, host_bs_config: Path, host_key: Optional[str] = None) -> Tuple[bool, bool]:
    if not config_path.is_file():
        raise FileNotFoundError(f"Training config not found: {config_path}")
    if host_key is None:
        host_key = gethostname()

    config_parser = read_parser(config_path)
    host_bs_parser = read_parser(host_bs_config, create=True)

    changed: List[Tuple[bool, bool]] = []
    changed.append(
        update_batch_size(
            host_key,
            config_parser,
            host_bs_parser,
            config_key="batch_size_eval",
            batchconfig_key="batch_size_eval",
        )
    )

    autocast_enabled = False
    if config_parser.has_section("train"):
        autocast_enabled = cast_bool(config_parser.get("train", "train_autocast", fallback="false"))

    if autocast_enabled:
        changed.append(
            update_batch_size(
                host_key,
                config_parser,
                host_bs_parser,
                config_key="batch_size",
                batchconfig_key="batch_size_autocast_train",
            )
        )
    else:
        changed.append(
            update_batch_size(
                host_key,
                config_parser,
                host_bs_parser,
                config_key="batch_size",
                batchconfig_key="batch_size_train",
            )
        )

    config_changed = any(item[0] for item in changed)
    host_changed = any(item[1] for item in changed)
    write_parser_if_changed(config_path, config_parser, config_changed)
    write_parser_if_changed(host_bs_config, host_bs_parser, host_changed)
    return config_changed, host_changed


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="Path to DeepFilterNet BASE_DIR/config.ini.")
    parser.add_argument(
        "--host-batch-size-config",
        required=True,
        type=Path,
        help="Path to host batch-size INI. Created if missing.",
    )
    parser.add_argument(
        "--host-key",
        default=None,
        help="Host key section to use. Defaults to socket hostname. Training commonly uses <hostname>_<model>_<fft_size>.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        config_changed, host_changed = apply_host_batch_sizes(
            config_path=args.config,
            host_bs_config=args.host_batch_size_config,
            host_key=args.host_key,
        )
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 2

    if config_changed:
        print(f"Updated training config: {args.config}")
    if host_changed:
        print(f"Updated host batch-size config: {args.host_batch_size_config}")
    if not config_changed and not host_changed:
        print("No changes needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
