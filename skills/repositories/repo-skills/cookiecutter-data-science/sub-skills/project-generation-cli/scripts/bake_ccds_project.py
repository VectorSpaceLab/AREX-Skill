#!/usr/bin/env python3
"""Bake a Cookiecutter Data Science project through the installed CCDS package.

The script is intentionally self-contained for generated repo-skill runtime use.
It imports the installed ``ccds`` package, uses the public CCDS template by
default, writes into a user-supplied or temporary parent output directory, and
prints the generated project path on success.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_TEMPLATE = "https://github.com/drivendataorg/cookiecutter-data-science"


class UserError(Exception):
    """An expected user-facing error with a concise message."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Safely run a noninteractive Cookiecutter Data Science project bake "
            "using the installed cookiecutter-data-science package."
        )
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Parent directory where the generated project directory will be "
            "created. Defaults to a new temporary directory that is kept on "
            "success so the printed project path remains usable."
        ),
    )
    parser.add_argument(
        "--config-json",
        type=Path,
        default=None,
        help=(
            "Path to a JSON object of Cookiecutter extra_context values. Use "
            "this for complete or nested CCDS configs."
        ),
    )
    parser.add_argument(
        "--extra-context",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Additional scalar extra_context value. May be repeated. Values "
            "override keys from --config-json."
        ),
    )
    parser.add_argument(
        "--template",
        default=None,
        help=(
            "Optional Cookiecutter template path or URL. If omitted, uses the "
            "public Cookiecutter Data Science template."
        ),
    )
    parser.add_argument(
        "--checkout",
        default=None,
        help=(
            "Optional branch, tag, or commit to check out. For the default CCDS "
            "template, omission means v<installed ccds version>, matching the "
            "ccds CLI default."
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help=(
            "Allow Cookiecutter to overwrite an existing output project "
            "directory. Omitted by default to avoid destructive writes."
        ),
    )
    parser.add_argument(
        "--keep-on-failure",
        action="store_true",
        help=(
            "Ask Cookiecutter to keep a failed partial project and do not remove "
            "the temporary output directory after failure."
        ),
    )
    parser.add_argument(
        "--accept-hooks",
        choices=("yes", "ask", "no"),
        default="yes",
        help=(
            "Cookiecutter hook policy. The default 'yes' matches normal CCDS "
            "generation; use 'no' only when intentionally inspecting raw templates."
        ),
    )
    return parser


def _load_json_object(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise UserError(f"Config JSON not found: {path}") from exc
    except OSError as exc:
        raise UserError(f"Could not read config JSON {path}: {exc}") from exc

    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as exc:
        raise UserError(
            f"Invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc

    if not isinstance(loaded, dict):
        raise UserError(f"Config JSON must contain an object at top level: {path}")
    return loaded


def _parse_extra_context(items: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise UserError(
                f"Invalid --extra-context value {item!r}; expected KEY=VALUE."
            )
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise UserError(
                f"Invalid --extra-context value {item!r}; KEY must not be empty."
            )
        parsed[key] = value
    return parsed


def _import_ccds_api():
    try:
        import ccds  # type: ignore
        from ccds.__main__ import api_main  # type: ignore
    except ModuleNotFoundError as exc:
        missing = exc.name or "unknown module"
        raise UserError(
            "Could not import the installed cookiecutter-data-science package "
            f"or one of its dependencies (missing: {missing}). Install it with "
            "`pipx install cookiecutter-data-science` or "
            "`python -m pip install cookiecutter-data-science`, then retry."
        ) from exc
    except Exception as exc:  # noqa: BLE001 - convert import-time failures to CLI text
        raise UserError(
            "Importing cookiecutter-data-science failed before project bake: "
            f"{type(exc).__name__}: {exc}"
        ) from exc
    return ccds, api_main


def _default_checkout(ccds_module: Any, template: str, user_checkout: str | None) -> str | None:
    if user_checkout:
        return user_checkout
    if template != DEFAULT_TEMPLATE:
        return None
    version = getattr(ccds_module, "__version__", None)
    if not version:
        raise UserError(
            "Installed ccds package did not expose __version__; pass --checkout "
            "explicitly or reinstall cookiecutter-data-science."
        )
    return f"v{version}"


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    try:
        config = _load_json_object(args.config_json)
        config.update(_parse_extra_context(args.extra_context))

        ccds_module, api_main = _import_ccds_api()
        template = args.template or DEFAULT_TEMPLATE
        checkout = _default_checkout(ccds_module, template, args.checkout)

        created_temp_output = False
        if args.output_dir is None:
            output_dir = Path(tempfile.mkdtemp(prefix="ccds-bake-"))
            created_temp_output = True
        else:
            output_dir = args.output_dir.expanduser().resolve()
            if output_dir.exists() and not output_dir.is_dir():
                raise UserError(f"--output-dir exists but is not a directory: {output_dir}")
            output_dir.mkdir(parents=True, exist_ok=True)

        try:
            generated_path = api_main.cookiecutter(
                template,
                checkout=checkout,
                no_input=True,
                extra_context=config or None,
                output_dir=str(output_dir),
                overwrite_if_exists=args.overwrite,
                keep_project_on_failure=args.keep_on_failure,
                accept_hooks=args.accept_hooks,
            )
        except Exception:
            if created_temp_output and not args.keep_on_failure:
                shutil.rmtree(output_dir, ignore_errors=True)
            raise

        generated = Path(generated_path).expanduser().resolve()
        print(f"CCDS_TEMPLATE={template}")
        print(f"CCDS_CHECKOUT={checkout or ''}")
        print(f"OUTPUT_PARENT={output_dir}")
        print(f"GENERATED_PROJECT_PATH={generated}")
        return 0

    except UserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("error: interrupted by user", file=sys.stderr)
        return 130
    except Exception as exc:  # noqa: BLE001 - provide clear CLI failure text
        print(
            "error: CCDS project bake failed: "
            f"{type(exc).__name__}: {exc}\n"
            "hint: retry with a clean output directory, explicit --config-json, "
            "or --keep-on-failure for inspection.",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
