#!/usr/bin/env python3
"""Safely probe Graphify assistant platform install artifacts.

This helper is safe by default: it creates a temporary HOME and a temporary
project, runs Graphify there, summarizes files relative to those temp roots, and
then deletes the temp tree unless --keep-temp is set. It never points Graphify at
the caller's real HOME by default. If the optional --temp-parent output location
is supplied, obviously dangerous paths such as /, the real HOME, the current
project, and system/config directories are refused.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PREFIX = "graphify-install-probe-"
SUPPORTED_PLATFORMS = {
    "agents", "aider", "amp", "antigravity", "antigravity-windows", "claude",
    "claw", "codebuddy", "codex", "copilot", "cursor", "devin", "droid",
    "gemini", "hermes", "kilo", "kimi", "kiro", "opencode", "pi", "skills",
    "trae", "trae-cn", "vscode", "windows",
}
DEDICATED_TOP_LEVEL = {"vscode"}


class ProbeError(RuntimeError):
    def __init__(self, message: str, code: int = 1) -> None:
        super().__init__(message)
        self.code = code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run graphify install in an isolated temporary HOME/project and summarize artifacts."
    )
    parser.add_argument("--platform", default="codex", help="assistant platform or alias to probe")
    parser.add_argument("--scope", choices=("user", "project"), default="project", help="scope to exercise")
    parser.add_argument("--keep-temp", action="store_true", help="keep the temp root for manual inspection")
    parser.add_argument("--json", action="store_true", help="emit a machine-readable JSON summary")
    parser.add_argument("--graphify-cmd", help="explicit command, e.g. 'graphify' or 'python -m graphify'")
    parser.add_argument("--mode", choices=("top-level", "subcommand"), default="top-level", help="top-level uses install --platform; subcommand uses <platform> install")
    parser.add_argument("--strict", action="store_true", help="add strict mode for Claude/Windows project hook probes")
    parser.add_argument("--skip-uninstall", action="store_true", help="do not run matching uninstall before cleanup")
    parser.add_argument("--git-hooks", action="store_true", help="also probe graphify hook install/status/uninstall")
    parser.add_argument("--temp-parent", type=Path, help="parent for the temp root; dangerous output paths are refused")
    return parser.parse_args()


def rel_to(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


def resolved(path: Path) -> Path:
    return path.expanduser().resolve(strict=False)


def dangerous_output_path(path: Path) -> str | None:
    p = resolved(path)
    home = resolved(Path.home())
    cwd = resolved(Path.cwd())
    exact_bad = {Path("/"), home, cwd, Path("/etc"), Path("/bin"), Path("/sbin"), Path("/usr"), Path("/boot"), Path("/dev"), Path("/proc"), Path("/sys")}
    if p in exact_bad:
        return f"{p} is a real HOME/project/system directory"
    for prefix in (Path("/etc"), Path("/bin"), Path("/sbin"), Path("/usr"), Path("/boot"), Path("/dev"), Path("/proc"), Path("/sys")):
        if rel_to(p, prefix):
            return f"{p} is under system directory {prefix}"
    config_names = {".claude", ".codex", ".agents", ".config", ".gemini", ".cursor", ".kiro", ".aider", ".trae", ".trae-cn", ".factory", ".openclaw", ".opencode"}
    if p.name in config_names and (rel_to(p, home) or rel_to(p, cwd)):
        return f"{p} looks like a real assistant configuration directory"
    return None


def choose_temp_parent(explicit: Path | None) -> Path:
    if explicit is not None:
        parent = resolved(explicit)
        reason = dangerous_output_path(parent)
        if reason:
            raise ProbeError(f"refusing dangerous --temp-parent output path: {reason}", 2)
        if parent.exists() and not parent.is_dir():
            raise ProbeError(f"--temp-parent is not a directory: {parent}", 2)
        parent.mkdir(parents=True, exist_ok=True)
        return parent
    candidate = resolved(Path(tempfile.gettempdir()))
    if not dangerous_output_path(candidate) and candidate.exists() and os.access(candidate, os.W_OK | os.X_OK):
        return candidate
    for fallback in (Path("/tmp"), Path("/var/tmp")):
        fb = resolved(fallback)
        if fb.exists() and fb.is_dir() and os.access(fb, os.W_OK | os.X_OK):
            return fb
    raise ProbeError("could not find a safe writable temp parent", 2)


def ensure_safe_temp_root(root: Path, parent: Path) -> None:
    r = resolved(root)
    p = resolved(parent)
    if not r.name.startswith(PREFIX):
        raise ProbeError(f"refusing temp root without {PREFIX!r} prefix: {r}", 2)
    if not rel_to(r, p):
        raise ProbeError(f"refusing temp root outside selected parent: {r}", 2)
    for name in ("home", "project"):
        child = r / name
        if child.exists() and child.is_symlink():
            raise ProbeError(f"refusing symlinked temp child: {child}", 2)


def resolve_graphify_cmd(explicit: str | None) -> tuple[list[str], str | None, str]:
    if explicit:
        argv = shlex.split(explicit)
        if not argv:
            raise ProbeError("--graphify-cmd parsed to an empty command", 2)
        return argv, None, "explicit"
    found = shutil.which("graphify")
    if found:
        return [found], None, "path"
    try:
        import graphify  # type: ignore
    except Exception as exc:
        # When this helper is run from a source checkout instead of an installed
        # wheel, the script directory is not the package root. Walk the current
        # directory and this file's parents looking for a local graphify package,
        # then pass that parent through PYTHONPATH to the subprocess.
        candidates = [resolved(Path.cwd()), *[resolved(p) for p in Path(__file__).resolve().parents]]
        for candidate in candidates:
            if (candidate / "graphify" / "__init__.py").is_file():
                return [sys.executable, "-m", "graphify"], str(candidate), "python-module-local"
        raise ProbeError("could not find `graphify` on PATH and `python -m graphify` is not importable; install `graphifyy` or pass --graphify-cmd", 2) from exc
    module_file = getattr(graphify, "__file__", None)
    pyroot = str(Path(module_file).resolve().parent.parent) if module_file else None
    return [sys.executable, "-m", "graphify"], pyroot, "python-module"


def probe_env(home: Path, pyroot: str | None) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "HOME": str(home),
        "USERPROFILE": str(home),
        "APPDATA": str(home / "AppData" / "Roaming"),
        "LOCALAPPDATA": str(home / "AppData" / "Local"),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "GIT_CONFIG_GLOBAL": str(home / ".gitconfig"),
        "TMPDIR": str(home / "tmp"),
    })
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    if pyroot:
        old = env.get("PYTHONPATH")
        env["PYTHONPATH"] = pyroot if not old else pyroot + os.pathsep + old
    return env


def install_cmd(base: list[str], platform: str, scope: str, mode: str, strict: bool) -> list[str]:
    if mode == "subcommand" and platform not in {"windows", "antigravity-windows"}:
        cmd = [*base, platform, "install"]
        if scope == "project":
            cmd.append("--project")
        if strict:
            cmd.append("--strict")
        return cmd
    if platform in DEDICATED_TOP_LEVEL:
        return [*base, platform, "install"]
    cmd = [*base, "install"]
    if scope == "project":
        cmd.append("--project")
    if strict:
        cmd.append("--strict")
    return [*cmd, "--platform", platform]


def uninstall_cmd(base: list[str], platform: str, scope: str, mode: str) -> list[str]:
    if mode == "subcommand" and platform not in {"windows", "antigravity-windows"}:
        cmd = [*base, platform, "uninstall"]
        if scope == "project":
            cmd.append("--project")
        return cmd
    if platform in DEDICATED_TOP_LEVEL:
        return [*base, platform, "uninstall"]
    cmd = [*base, "uninstall"]
    if scope == "project":
        cmd.append("--project")
    return [*cmd, "--platform", platform]


def snapshot(root: Path) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    if not root.exists():
        return files
    for path in sorted(root.rglob("*")):
        if path.is_file():
            try:
                rel = path.relative_to(root).as_posix()
                size = path.stat().st_size
            except OSError:
                continue
            files.append({"path": rel, "bytes": size})
    return files


def print_snapshot(label: str, files: list[dict[str, Any]]) -> None:
    print(f"\n[{label}]")
    if not files:
        print("  (no files)")
        return
    for item in files:
        print(f"  {item['path']} ({item['bytes']} bytes)")


def contains_graphify(root: Path) -> bool:
    if not root.exists():
        return False
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            if "graphify" in path.read_text(encoding="utf-8", errors="ignore"):
                return True
        except OSError:
            pass
    return False


def run_cmd(argv: list[str], *, cwd: Path, env: dict[str, str], label: str, records: list[dict[str, Any]], quiet: bool) -> None:
    if not quiet:
        print(f"\n$ ({label}) " + " ".join(shlex.quote(x) for x in argv))
    cp = subprocess.run(argv, cwd=str(cwd), env=env, text=True, capture_output=True)
    records.append({"label": label, "argv": argv, "cwd": "project", "returncode": cp.returncode, "stdout": cp.stdout, "stderr": cp.stderr})
    if not quiet:
        if cp.stdout:
            print(cp.stdout.rstrip())
        if cp.stderr:
            print(cp.stderr.rstrip(), file=sys.stderr)
    if cp.returncode != 0:
        raise ProbeError(f"{label} exited {cp.returncode}", cp.returncode)


def main() -> int:
    args = parse_args()
    platform = args.platform.strip().lower()
    records: list[dict[str, Any]] = []
    result: dict[str, Any] = {"ok": False, "platform": platform, "scope": args.scope, "mode": args.mode, "strict": bool(args.strict), "git_hooks": bool(args.git_hooks), "commands": records, "files": {}, "kept_temp": bool(args.keep_temp)}
    temp_root: Path | None = None
    temp_parent: Path | None = None
    code = 0
    try:
        if platform not in SUPPORTED_PLATFORMS:
            raise ProbeError(f"unsupported platform {args.platform!r}; known: {', '.join(sorted(SUPPORTED_PLATFORMS))}", 2)
        warnings: list[str] = []
        if args.strict and platform not in {"claude", "windows"}:
            warnings.append("--strict is meaningful only for Claude/Windows project hooks")
        if args.mode == "subcommand" and platform in {"windows", "antigravity-windows"}:
            warnings.append(f"{platform} is a packaging variant; using top-level install --platform")
        if platform in DEDICATED_TOP_LEVEL and args.scope == "user":
            warnings.append(f"{platform} uses a current-project integration command; user scope is simulated in the temp project")
        if warnings:
            result["warnings"] = warnings
            if not args.json:
                for warning in warnings:
                    print(f"WARNING: {warning}", file=sys.stderr)

        base, pyroot, source = resolve_graphify_cmd(args.graphify_cmd)
        result["graphify_command_source"] = source
        result["graphify_command"] = base
        temp_parent = choose_temp_parent(args.temp_parent)
        temp_root = Path(tempfile.mkdtemp(prefix=PREFIX, dir=str(temp_parent))).resolve()
        home = temp_root / "home"
        project = temp_root / "project"
        home.mkdir(parents=True, exist_ok=True)
        project.mkdir(parents=True, exist_ok=True)
        ensure_safe_temp_root(temp_root, temp_parent)
        env = probe_env(home, pyroot)
        result["temp_root"] = str(temp_root) if args.keep_temp else None
        result["temp_dirs"] = {"home": "home/", "project": "project/"}

        if not args.json:
            print("Graphify install probe")
            print(f"platform: {platform}")
            print(f"scope: {args.scope}")
            print(f"mode: {args.mode}")
            print(f"graphify command source: {source}")
            print("temporary HOME and project are isolated from real user config")

        run_cmd(install_cmd(base, platform, args.scope, args.mode, bool(args.strict)), cwd=project, env=env, label="install", records=records, quiet=bool(args.json))
        result["files"]["project_after_install"] = snapshot(project)
        result["files"]["home_after_install"] = snapshot(home)
        if not args.json:
            print_snapshot("project files after install (relative to temp project)", result["files"]["project_after_install"])
            print_snapshot("HOME files after install (relative to temp HOME)", result["files"]["home_after_install"])

        if args.git_hooks:
            run_cmd(["git", "init", "-q"], cwd=project, env=env, label="git init", records=records, quiet=bool(args.json))
            run_cmd([*base, "hook", "status"], cwd=project, env=env, label="hook status before", records=records, quiet=bool(args.json))
            run_cmd([*base, "hook", "install"], cwd=project, env=env, label="hook install", records=records, quiet=bool(args.json))
            run_cmd([*base, "hook", "status"], cwd=project, env=env, label="hook status after", records=records, quiet=bool(args.json))
            result["files"]["project_after_hook_install"] = snapshot(project)
            result["files"]["home_after_hook_install"] = snapshot(home)

        if not args.skip_uninstall:
            run_cmd(uninstall_cmd(base, platform, args.scope, args.mode), cwd=project, env=env, label="uninstall", records=records, quiet=bool(args.json))
            if args.git_hooks:
                run_cmd([*base, "hook", "uninstall"], cwd=project, env=env, label="hook uninstall", records=records, quiet=bool(args.json))
                run_cmd([*base, "hook", "status"], cwd=project, env=env, label="hook status final", records=records, quiet=bool(args.json))
            result["files"]["project_after_uninstall"] = snapshot(project)
            result["files"]["home_after_uninstall"] = snapshot(home)
            result["graphify_marker_remaining"] = {"project": contains_graphify(project), "home": contains_graphify(home)}
            if not args.json:
                print_snapshot("project files after uninstall (relative to temp project)", result["files"]["project_after_uninstall"])
                print_snapshot("HOME files after uninstall (relative to temp HOME)", result["files"]["home_after_uninstall"])
                print(f"graphify marker remains in project files: {result['graphify_marker_remaining']['project']}")
                print(f"graphify marker remains in HOME files: {result['graphify_marker_remaining']['home']}")

        result["ok"] = True
    except ProbeError as exc:
        result["error"] = str(exc)
        code = exc.code
        if not args.json:
            print(f"ERROR: {exc}", file=sys.stderr)
    finally:
        if temp_root is not None and temp_parent is not None:
            if args.keep_temp:
                result["temp_deleted"] = False
                result["temp_root"] = str(temp_root)
                if not args.json:
                    print(f"\nKept temp directory: {temp_root}")
            else:
                try:
                    ensure_safe_temp_root(temp_root, temp_parent)
                    shutil.rmtree(temp_root, ignore_errors=True)
                    result["temp_deleted"] = True
                    if not args.json:
                        print("\nDeleted temp directory.")
                except ProbeError as exc:
                    result["temp_deleted"] = False
                    result["cleanup_error"] = str(exc)
                    code = code or exc.code
                    if not args.json:
                        print(f"ERROR: cleanup refused: {exc}", file=sys.stderr)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
