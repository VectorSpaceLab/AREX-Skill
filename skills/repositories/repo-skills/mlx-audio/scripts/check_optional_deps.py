from __future__ import annotations

import argparse
import importlib.util
import json


OPTIONAL_MODULES = [
    "sentencepiece",
    "mistral_common",
    "fastapi",
    "uvicorn",
    "multipart",
    "webrtcvad",
    "sounddevice",
    "mlx_lm",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MLX Audio optional dependencies")
    parser.add_argument("--json", action="store_true", help="Ignored; output is always JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    _ = parse_args(argv)
    status = {
        module: importlib.util.find_spec(module) is not None for module in OPTIONAL_MODULES
    }
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
