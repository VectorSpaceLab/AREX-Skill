#!/usr/bin/env python3
"""Plan a ModelScope Hub download without performing network or file writes.

The script prints a modern `modelscope download` command and a Python Hub API
snippet. It is deterministic and safe by default: no imports from `modelscope`,
no network access, no cache mutation, and no credential reads beyond checking
whether a named token environment variable is set.
"""
from __future__ import annotations

import argparse
import os
import re
import shlex
import sys
from typing import Iterable, List, Sequence

_REPO_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
_SAFE_ENV_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _flatten(values: Sequence[Sequence[str]] | None) -> List[str]:
    if not values:
        return []
    out: List[str] = []
    for group in values:
        out.extend(group)
    return out


def _quote_cmd(parts: Iterable[str]) -> str:
    return " ".join(shlex.quote(str(p)) for p in parts)


def _py(value: object) -> str:
    return repr(value)


def _add_kw(lines: List[str], name: str, value: object, *, omit_none: bool = True) -> None:
    if omit_none and value is None:
        return
    lines.append(f"    {name}={_py(value)},")


def validate_repo_id(repo_id: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not repo_id:
        errors.append("repo id is empty")
        return errors, warnings
    if "://" in repo_id or repo_id.startswith(("http:", "https:")):
        errors.append("repo id must be owner/name, not a URL; pass endpoint separately")
    if repo_id.startswith(("/", "~/", "./", "../")) or "\\" in repo_id:
        errors.append("repo id must be a Hub id, not a local filesystem path")
    if repo_id.startswith("-"):
        errors.append("repo id cannot start with '-' because it will be parsed as an option")
    if any(ch.isspace() for ch in repo_id):
        errors.append("repo id cannot contain whitespace")
    if ".." in repo_id.split("/"):
        errors.append("repo id cannot contain '..' path segments")

    slash_count = repo_id.count("/")
    if slash_count != 1:
        if slash_count == 0:
            errors.append("repo id should include an owner/namespace and a name separated by '/'")
        else:
            warnings.append("repo id contains more than one '/'; most ModelScope Hub ids are owner/name")
    if slash_count >= 1:
        owner, name = repo_id.split("/", 1)
        if not owner or not name:
            errors.append("repo id owner and name must both be non-empty")

    if not errors and not _REPO_ID_RE.match(repo_id):
        warnings.append(
            "repo id contains characters outside the conservative ASCII owner/name pattern; "
            "verify the exact id with ModelScope before executing"
        )
    return errors, warnings


def validate_repo_files(files: Sequence[str]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    for file_path in files:
        if not file_path:
            errors.append("file path cannot be empty")
            continue
        if file_path.startswith(("/", "~/", "./", "../")) or "\\" in file_path:
            errors.append(f"file path {file_path!r} must be a repository-relative POSIX path")
        if any(part == ".." for part in file_path.split("/")):
            errors.append(f"file path {file_path!r} cannot contain '..' segments")
        if file_path.endswith("/"):
            warnings.append(f"file path {file_path!r} ends with '/'; use include patterns for directories")
    return errors, warnings


def build_cli(args: argparse.Namespace, include: Sequence[str], exclude: Sequence[str]) -> tuple[str, list[str]]:
    notes: list[str] = []
    if args.command == "python -m modelscope.cli.cli":
        parts: list[str] = ["python", "-m", "modelscope.cli.cli"]
    else:
        parts = [args.command]
    parts += ["download", args.repo_id, "--repo-type", args.repo_type]
    if args.revision:
        parts += ["--revision", args.revision]
    if args.cache_dir:
        parts += ["--cache-dir", args.cache_dir]
    if args.local_dir:
        parts += ["--local-dir", args.local_dir]
    if include:
        parts.append("--include")
        parts.extend(include)
    if exclude:
        parts.append("--exclude")
        parts.extend(exclude)
    if args.force:
        parts.append("--force")
    parts.extend(args.files)

    if args.local_files_only:
        notes.append(
            "No CLI local-files-only flag is assumed by this planner. Use the Python snippet "
            "for offline/cache-only execution, or check `modelscope download --help` in the target environment."
        )
    if args.endpoint:
        notes.append(
            "Endpoint was not inserted into the CLI command because endpoint flag support varies by "
            "modelscope_hub version. If `modelscope download --help` lists `--endpoint`, append it; "
            "otherwise use Python `endpoint=` or a documented domain environment variable."
        )
    if args.private:
        notes.append(
            f"For private/gated repos, avoid literal tokens in shell history. If help lists `--token`, "
            f"append `--token \"${args.token_env}\"`; otherwise run `modelscope login --token \"${args.token_env}\"` "
            "after confirming credential persistence is acceptable."
        )
    return _quote_cmd(parts), notes


def build_python(args: argparse.Namespace, include: Sequence[str], exclude: Sequence[str]) -> str:
    token_line = f"token = os.environ.get({_py(args.token_env)})"
    if args.private:
        token_line += f"\nif not token:\n    raise RuntimeError('Set {args.token_env} for private/gated repositories')"

    if args.files:
        if args.repo_type == "model":
            import_line = "from modelscope.hub.file_download import model_file_download"
            func_name = "model_file_download"
            id_name = "model_id"
        else:
            import_line = "from modelscope.hub.file_download import dataset_file_download"
            func_name = "dataset_file_download"
            id_name = "dataset_id"

        lines = [
            "import os",
            import_line,
            "",
            token_line,
            f"files = {_py(list(args.files))}",
            "downloaded_paths = []",
            "for file_path in files:",
            f"    downloaded_paths.append({func_name}(",
            f"        {_py(args.repo_id)},",
            "        file_path,",
        ]
        # model_file_download accepts revision as the third positional or keyword; keyword is clearer.
        if args.revision:
            lines.append(f"        revision={_py(args.revision)},")
        if args.cache_dir:
            lines.append(f"        cache_dir={_py(args.cache_dir)},")
        if args.local_dir:
            lines.append(f"        local_dir={_py(args.local_dir)},")
        if args.local_files_only:
            lines.append("        local_files_only=True,")
        if args.endpoint:
            lines.append(f"        endpoint={_py(args.endpoint)},")
        lines.append("        token=token,")
        lines.append("    ))")
        lines.append("print(downloaded_paths)")
        return "\n".join(lines)

    if args.repo_type == "model":
        lines = [
            "import os",
            "from modelscope.hub.snapshot_download import snapshot_download",
            "",
            token_line,
            "path = snapshot_download(",
            f"    repo_id={_py(args.repo_id)},",
            "    repo_type='model',",
        ]
    elif args.local_files_only:
        lines = [
            "import os",
            "from modelscope.hub.snapshot_download import snapshot_download",
            "",
            token_line,
            "# dataset_snapshot_download in this ModelScope compatibility layer does not expose local_files_only.",
            "# Use generic snapshot_download with repo_type='dataset' for cache-only dataset snapshots.",
            "path = snapshot_download(",
            f"    repo_id={_py(args.repo_id)},",
            "    repo_type='dataset',",
        ]
    else:
        lines = [
            "import os",
            "from modelscope.hub.snapshot_download import dataset_snapshot_download",
            "",
            token_line,
            "path = dataset_snapshot_download(",
            f"    repo_id={_py(args.repo_id)},",
        ]

    _add_kw(lines, "revision", args.revision)
    _add_kw(lines, "cache_dir", args.cache_dir)
    _add_kw(lines, "local_dir", args.local_dir)
    if include:
        lines.append(f"    allow_patterns={_py(list(include))},")
    if exclude:
        lines.append(f"    ignore_patterns={_py(list(exclude))},")
    if args.local_files_only:
        lines.append("    local_files_only=True,")
    if args.endpoint:
        lines.append(f"    endpoint={_py(args.endpoint)},")
    lines.append("    token=token,")
    lines.append(")")
    lines.append("print(path)")
    return "\n".join(lines)


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a dry-run ModelScope download plan: a CLI command and a Python Hub API snippet. "
            "The planner performs no network calls and writes no files."
        )
    )
    parser.add_argument("repo_id", help="ModelScope Hub id in owner/name form, not a URL or local path.")
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional repository-relative file paths. If supplied, Python output uses single-file APIs.",
    )
    parser.add_argument("--repo-type", choices=("model", "dataset"), default="model", help="Hub repository type. Default: model.")
    parser.add_argument("--revision", help="Branch/tag/revision to download. Pass explicitly for reproducible runs.")
    parser.add_argument("--cache-dir", help="Cache root for reusable ModelScope/modelscope_hub storage.")
    parser.add_argument("--local-dir", help="User-visible local directory for the downloaded files/snapshot.")
    parser.add_argument(
        "--include",
        nargs="+",
        action="append",
        metavar="PATTERN",
        help="Glob pattern(s) to include. Quote shell globs. Can be repeated.",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        action="append",
        metavar="PATTERN",
        help="Glob pattern(s) to exclude. Quote shell globs. Can be repeated.",
    )
    parser.add_argument("--local-files-only", action="store_true", help="Plan an offline/cache-only Python call.")
    parser.add_argument("--force", action="store_true", help="Include CLI --force for an online refresh when supported.")
    parser.add_argument("--endpoint", help="Endpoint URL for the Python snippet; CLI endpoint support varies by version.")
    parser.add_argument(
        "--token-env",
        default="MODELSCOPE_API_TOKEN",
        help="Environment variable name to read for Python token guidance. Default: MODELSCOPE_API_TOKEN.",
    )
    parser.add_argument(
        "--private",
        action="store_true",
        help="Require token presence in the Python snippet and print stricter credential guidance.",
    )
    parser.add_argument(
        "--command",
        default="modelscope",
        choices=("modelscope", "ms", "python -m modelscope.cli.cli"),
        help="CLI entry point to show in the planned command. Default: modelscope.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    include = _flatten(args.include)
    exclude = _flatten(args.exclude)

    errors, warnings = validate_repo_id(args.repo_id)
    file_errors, file_warnings = validate_repo_files(args.files)
    errors.extend(file_errors)
    warnings.extend(file_warnings)

    if args.token_env and not _SAFE_ENV_RE.match(args.token_env):
        errors.append("--token-env must be a shell-safe environment variable name")
    if args.local_dir and args.cache_dir:
        warnings.append("both --local-dir and --cache-dir were supplied; local-dir output usually takes precedence")
    if args.files and (include or exclude):
        warnings.append("explicit file paths and include/exclude patterns were both supplied; patterns may be ignored for explicit files")
    if args.force and args.local_files_only:
        warnings.append("--force implies an online refresh, while --local-files-only forbids network; do not use both in one real command")
    if args.endpoint and not args.endpoint.startswith(("http://", "https://")):
        warnings.append("endpoint has no scheme; Python helpers may normalize some endpoints, but explicit https:// is clearer")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    cli_command, cli_notes = build_cli(args, include, exclude)
    py_snippet = build_python(args, include, exclude)

    token_present = bool(os.environ.get(args.token_env)) if args.token_env else False

    print("# ModelScope download dry-run plan")
    print()
    print(f"Repo id: {args.repo_id}")
    print(f"Repo type: {args.repo_type}")
    print(f"Revision: {args.revision or '<default>'}")
    print(f"Files: {', '.join(args.files) if args.files else '<snapshot>'}")
    print(f"Include patterns: {', '.join(include) if include else '<none>'}")
    print(f"Exclude patterns: {', '.join(exclude) if exclude else '<none>'}")
    print(f"Cache dir: {args.cache_dir or '<default>'}")
    print(f"Local dir: {args.local_dir or '<none>'}")
    print(f"Local files only: {args.local_files_only}")
    print(f"Endpoint: {args.endpoint or '<default>'}")
    print(f"Token env {args.token_env}: {'set' if token_present else 'not set'} (value not printed)")
    print()

    if warnings or cli_notes:
        print("## Warnings and handling notes")
        for warning in warnings + cli_notes:
            print(f"- {warning}")
        print()

    print("## CLI command")
    print(cli_command)
    print()
    print("## Python API snippet")
    print(py_snippet)
    print()
    print("## Safety notes")
    print("- This planner did not import modelscope, contact the network, create directories, or download files.")
    print("- Check `modelscope download --help` in the execution environment before relying on version-specific CLI flags.")
    print("- Route pipeline inference to ../../pipelines-and-models/SKILL.md and dataset loading to ../../datasets-config/SKILL.md after download.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
