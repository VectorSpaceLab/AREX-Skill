#!/usr/bin/env python3
"""Self-contained HiFi-GAN training entrypoint bundled with the repo skill.

This wrapper runs the copied HiFi-GAN `train.py` from the skill's bundled
runtime source and resolves `--config v1|v2|v3|config_v*.json` to the bundled
configuration files. User data and checkpoint directories may live anywhere;
core source/config files do not require a separate repository checkout.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = SKILL_ROOT / "scripts" / "hifigan_runtime"
CONFIG_DIR = RUNTIME_DIR / "configs"
TRAIN_PY = RUNTIME_DIR / "train.py"

CONFIG_ALIASES = {
    "1": "config_v1.json",
    "v1": "config_v1.json",
    "config-v1": "config_v1.json",
    "config_v1": "config_v1.json",
    "config_v1.json": "config_v1.json",
    "2": "config_v2.json",
    "v2": "config_v2.json",
    "config-v2": "config_v2.json",
    "config_v2": "config_v2.json",
    "config_v2.json": "config_v2.json",
    "3": "config_v3.json",
    "v3": "config_v3.json",
    "config-v3": "config_v3.json",
    "config_v3": "config_v3.json",
    "config_v3.json": "config_v3.json",
}


def resolve_config(raw: str) -> str:
    alias = CONFIG_ALIASES.get(raw.lower())
    if alias:
        return str(CONFIG_DIR / alias)

    candidate = Path(raw).expanduser()
    if candidate.exists():
        return str(candidate.resolve())

    bundled = CONFIG_DIR / raw
    if bundled.exists():
        return str(bundled.resolve())

    raise SystemExit(
        f"Could not resolve --config {raw!r}. Use v1, v2, v3, a bundled config filename, or an existing JSON path."
    )


def normalize_argv(argv: list[str]) -> tuple[list[str], bool]:
    compat = True
    normalized: list[str] = []
    saw_config = False
    i = 0
    while i < len(argv):
        item = argv[i]
        if item == "--no-compat-shims":
            compat = False
            i += 1
            continue
        if item == "--config":
            if i + 1 >= len(argv):
                raise SystemExit("--config requires a value")
            normalized.extend(["--config", resolve_config(argv[i + 1])])
            saw_config = True
            i += 2
            continue
        if item.startswith("--config="):
            normalized.append("--config=" + resolve_config(item.split("=", 1)[1]))
            saw_config = True
            i += 1
            continue
        normalized.append(item)
        i += 1

    if not saw_config and not any(arg in {"-h", "--help"} for arg in normalized):
        normalized.extend(["--config", str(CONFIG_DIR / "config_v1.json")])

    return normalized, compat


def main() -> None:
    if not TRAIN_PY.is_file():
        raise SystemExit(f"Bundled train.py is missing: {TRAIN_PY}")
    if str(RUNTIME_DIR) not in sys.path:
        sys.path.insert(0, str(RUNTIME_DIR))

    argv, compat = normalize_argv(sys.argv[1:])
    if compat:
        from compat import apply_compat_shims

        apply_compat_shims(training=True)

    sys.argv = [str(TRAIN_PY), *argv]
    runpy.run_path(str(TRAIN_PY), run_name="__main__")


if __name__ == "__main__":
    main()
