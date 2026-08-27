from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from dataclasses import asdict, dataclass

from mlx_audio.version import __version__


CHECK_CMDS = [
    ["-m", "mlx_audio.tts.generate", "--help"],
    ["-m", "mlx_audio.stt.generate", "--help"],
    ["-m", "mlx_audio.sts.generate", "--help"],
    ["-m", "mlx_audio.server", "--help"],
    ["-m", "mlx_audio.convert", "--help"],
    ["-m", "mlx_audio.stt.eval", "--help"],
]


@dataclass
class CheckResult:
    package_version: str | None
    registry_kinds: list[str]
    core_imports: dict[str, bool]
    cli_help: dict[str, int] | None = None


def _import_ok(name: str) -> bool:
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


def _run_help(module_args: list[str]) -> int:
    proc = subprocess.run(
        [sys.executable, *module_args],
        capture_output=True,
        text=True,
    )
    return proc.returncode


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check MLX Audio installation")
    parser.add_argument("--check-cli", action="store_true", help="Run `--help` checks for the bundled CLIs")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from mlx_audio.registry import kinds

    core_imports = {
        "mlx_audio": True,
        "mlx_audio.audio_io": _import_ok("mlx_audio.audio_io"),
        "mlx_audio.tts.generate": _import_ok("mlx_audio.tts.generate"),
        "mlx_audio.stt.generate": _import_ok("mlx_audio.stt.generate"),
        "mlx_audio.sts.generate": _import_ok("mlx_audio.sts.generate"),
        "mlx_audio.server": _import_ok("mlx_audio.server"),
        "mlx_audio.convert": _import_ok("mlx_audio.convert"),
    }

    cli_help = None
    if args.check_cli:
        cli_help = {}
        for cmd in CHECK_CMDS:
            cli_help[" ".join(cmd)] = _run_help(cmd)

    result = CheckResult(
        package_version=__version__,
        registry_kinds=list(kinds()),
        core_imports=core_imports,
        cli_help=cli_help,
    )
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
