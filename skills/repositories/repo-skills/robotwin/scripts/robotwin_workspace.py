#!/usr/bin/env python3
"""Self-contained RoboTwin workspace entry point for the generated skill.

This script lets a future agent work from the generated skill alone. It can
materialize a pinned public RoboTwin workspace, initialize XPolicyLab, download
public assets/data, validate prerequisites, and dispatch collection/evaluation
commands through one bundled entry point. Network or mutating operations require
--execute; otherwise commands are printed as a dry run.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import shlex
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any, Iterable, Sequence

DEFAULT_REMOTE = "https://github.com/RoboTwin-Platform/RoboTwin.git"
DEFAULT_REVISION = "266f3aadf505a4f7fe9af0faa41a20f5f47cd123"
DEFAULT_BRANCH = "main"
XPOLICYLAB_PATH = "XPolicyLab"
XPOLICYLAB_REMOTE = "https://github.com/XPolicyLab/XPolicyLab.git"
XPOLICYLAB_REVISION = "c37109c500be67d0dea6b36bf7337bbd26e763cd"
HF_REPO_ID = "TianxingChen/RoboTwin2.0"
HF_REVISION = "main"
ASSET_ARCHIVES = ["background_texture.zip", "embodiments.zip", "objects.zip"]
DEFAULT_EMBODIMENT = "aloha_agilex"

SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*[A-Za-z0-9]$")
EPISODE_FILE_RE = re.compile(r"episode_?(\d+)(\.(?:hdf5|h5|mp4|json))$", re.IGNORECASE)
DIRECTORY_ALIASES = {"videos": "video", "instructions": "instruction"}


class UserError(RuntimeError):
    pass


def quote(cmd: Sequence[str]) -> str:
    return shlex.join(str(part) for part in cmd)


def run(cmd: Sequence[str], *, cwd: Path | None = None, execute: bool = False, env: dict[str, str] | None = None) -> int:
    prefix = f"(cd {cwd} &&) " if cwd else ""
    print(f"$ {prefix}{quote(cmd)}")
    if not execute:
        return 0
    completed = subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, env=env)
    return int(completed.returncode)


def require_executable(name: str) -> None:
    if shutil.which(name) is None:
        raise UserError(f"Required executable is not on PATH: {name}")


def safe_name(value: str, label: str) -> str:
    if not SAFE_NAME_RE.fullmatch(value):
        raise UserError(f"Unsafe {label}: {value!r}. Use letters, numbers, dot, underscore, or hyphen.")
    return value


def workspace_root(path: Path) -> Path:
    return path.expanduser().resolve()


def assert_workspace(path: Path) -> None:
    missing = [rel for rel in ["README.md", "envs", "env_cfg", "scripts", "description"] if not (path / rel).exists()]
    if missing:
        raise UserError(f"Not a RoboTwin workspace or incomplete checkout: {path} (missing {', '.join(missing)})")


def git_dirty(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "status", "--short"], cwd=path, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    return bool(completed.stdout.strip())


def bootstrap(args: argparse.Namespace) -> int:
    require_executable("git")
    target = workspace_root(args.workspace)
    execute = bool(args.execute)
    remote = args.remote
    revision = args.revision

    if target.exists() and not target.is_dir():
        raise UserError(f"Target exists but is not a directory: {target}")
    if target.exists() and not (target / ".git").exists() and any(target.iterdir()):
        raise UserError(f"Target exists but is not an empty directory or git checkout: {target}")

    if not target.exists() or (target.exists() and not (target / ".git").exists()):
        target.parent.mkdir(parents=True, exist_ok=True) if execute else None
        if run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                "--branch",
                args.branch,
                "--single-branch",
                remote,
                str(target),
            ],
            execute=execute,
        ) != 0:
            return 1
    else:
        print(f"workspace exists: {target}")
        if execute and git_dirty(target) and not args.allow_dirty:
            raise UserError("Workspace has local changes. Use --allow-dirty only when you accept checkout mutation risk.")

    if run(["git", "-C", str(target), "fetch", "--depth", "1", "origin", args.branch], execute=execute) != 0:
        return 1
    if revision != args.branch and run(["git", "-C", str(target), "fetch", "--depth", "1", "origin", revision], execute=execute) != 0:
        return 1
    if run(["git", "-C", str(target), "checkout", "--detach", revision], execute=execute) != 0:
        return 1

    if args.with_xpolicylab:
        if run(["git", "-C", str(target), "submodule", "sync", "--", XPOLICYLAB_PATH], execute=execute) != 0:
            return 1
        if run(["git", "-C", str(target), "submodule", "update", "--init", "--recursive", XPOLICYLAB_PATH], execute=execute) != 0:
            return 1
        xpl = target / XPOLICYLAB_PATH
        if xpl.exists():
            if run(["git", "-C", str(xpl), "fetch", "--depth", "1", "origin", args.xpolicylab_revision], execute=execute) != 0:
                return 1
            if run(["git", "-C", str(xpl), "checkout", "--detach", args.xpolicylab_revision], execute=execute) != 0:
                return 1
    if not execute:
        print("dry-run only; add --execute to create or mutate the workspace")
    return 0


def check(args: argparse.Namespace) -> int:
    root = workspace_root(args.workspace)
    ok = True
    print(f"workspace={root}")
    for rel in ["README.md", "envs", "env_cfg", "scripts", "description"]:
        exists = (root / rel).exists()
        print(f"path {rel}: {'ok' if exists else 'missing'}")
        ok = ok and exists

    modules = ["numpy", "torch", "sapien", "mplib", "open3d", "gymnasium", "transforms3d", "cv2", "h5py", "yaml", "rich"]
    import importlib.util

    for module in modules:
        spec = importlib.util.find_spec(module)
        print(f"module {module}: {'ok' if spec else 'missing'}")
        ok = ok and bool(spec)

    for rel in ["assets/objects/objaverse/list.json", "assets/objects/same.json", "assets/embodiments"]:
        exists = (root / rel).exists()
        print(f"asset {rel}: {'ok' if exists else 'missing'}")
        ok = ok and exists

    for rel in ["XPolicyLab/setup_policy_server.py", "XPolicyLab/policy", "XPolicyLab/utils/robot/_robot_info.json"]:
        exists = (root / rel).exists()
        print(f"xpolicylab {rel}: {'ok' if exists else 'missing'}")

    return 0 if ok else 1


def safe_extract(zip_path: Path, dest: Path, *, force: bool = False) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            name = Path(info.filename)
            if name.is_absolute() or ".." in name.parts:
                raise UserError(f"unsafe archive member in {zip_path.name}: {info.filename!r}")
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise UserError(f"refusing symlink in {zip_path.name}: {info.filename!r}")
        for info in zf.infolist():
            out = dest / info.filename
            if out.exists() and not force:
                continue
            zf.extract(info, dest)


def download_assets(args: argparse.Namespace) -> int:
    root = workspace_root(args.workspace)
    assert_workspace(root)
    assets_dir = root / "assets"
    print(f"asset_target={assets_dir}")
    if not args.execute:
        print("dry-run: would download public RoboTwin asset archives from Hugging Face and extract them under the workspace assets directory")
        for archive in ASSET_ARCHIVES:
            print(f"would acquire: hf://datasets/{args.repo_id}/{archive}")
        return 0
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise UserError("huggingface_hub is required for --execute asset download") from exc

    assets_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=args.repo_id,
        repo_type="dataset",
        revision=args.revision,
        allow_patterns=ASSET_ARCHIVES,
        local_dir=str(assets_dir),
        resume_download=True,
    )
    for archive in ASSET_ARCHIVES:
        zip_path = assets_dir / archive
        if zip_path.exists():
            print(f"extracting {zip_path.name} -> {assets_dir}")
            safe_extract(zip_path, assets_dir, force=args.force_extract)
    return check(argparse.Namespace(workspace=root))


def validate_zip_members(zip_file: zipfile.ZipFile) -> None:
    members = [info for info in zip_file.infolist() if not info.is_dir()]
    if not members:
        raise UserError("archive is empty")
    for info in members:
        member_path = Path(info.filename)
        if member_path.is_absolute() or ".." in member_path.parts:
            raise UserError(f"unsafe archive member path: {info.filename!r}")
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise UserError(f"symbolic links are not allowed: {info.filename!r}")


def normalize_relative_path(relative: Path) -> Path:
    parts = [DIRECTORY_ALIASES.get(part, part) for part in relative.parts]
    match = EPISODE_FILE_RE.fullmatch(parts[-1])
    if match:
        index = int(match.group(1))
        ext = match.group(2).lower()
        parts[-1] = f"episode_{index:07d}{'.hdf5' if ext == '.h5' else ext}"
    return Path(*parts)


def locate_payload(extract_root: Path, task: str, task_config: str, embodiment: str) -> Path:
    candidates = [
        path
        for path in extract_root.rglob(embodiment)
        if path.is_dir() and path.parent.name == task and (path / "data").is_dir()
    ]
    if not candidates:
        direct = extract_root / task_config / task / embodiment
        if (direct / "data").is_dir():
            candidates = [direct]
        direct = extract_root / task / embodiment
        if (direct / "data").is_dir():
            candidates = [direct]
    if len(candidates) != 1:
        found = ", ".join(str(path.relative_to(extract_root)) for path in candidates[:10]) or "none"
        raise UserError(f"archive does not contain exactly one {task}/{embodiment}/data payload; found {found}")
    return candidates[0]


def discover_tasks(repo_id: str, revision: str, archive_name: str) -> list[str]:
    try:
        from huggingface_hub import HfApi
    except Exception as exc:
        raise UserError("huggingface_hub is required to discover tasks") from exc
    suffix = f"/{archive_name}"
    files = HfApi().list_repo_files(repo_id=repo_id, repo_type="dataset", revision=revision)
    tasks = sorted({path.split("/")[1] for path in files if path.startswith("dataset/") and path.endswith(suffix) and len(path.split("/")) == 3})
    return tasks


def download_one_data_archive(task: str, args: argparse.Namespace, target_root: Path, cache_root: Path) -> None:
    from huggingface_hub import hf_hub_download

    filename = f"dataset/{task}/{args.archive_name}"
    task_config = Path(args.archive_name).name[:-4]
    archive_path = Path(
        hf_hub_download(
            repo_id=args.repo_id,
            repo_type="dataset",
            revision=args.revision,
            filename=filename,
            local_dir=str(cache_root),
            force_download=args.force_download,
        )
    )
    with zipfile.ZipFile(archive_path) as zf:
        validate_zip_members(zf)
        with tempfile.TemporaryDirectory(prefix=f"robotwin-{task}-") as tmp:
            tmp_root = Path(tmp)
            zf.extractall(tmp_root)
            payload = locate_payload(tmp_root, task, task_config, args.embodiment)
            output_base = target_root / task_config / task / args.embodiment
            for source in payload.rglob("*"):
                if not source.is_file():
                    continue
                rel = normalize_relative_path(source.relative_to(payload))
                dest = output_base / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                if dest.exists() and not args.force_extract:
                    continue
                shutil.copy2(source, dest)
    print(f"downloaded {task} -> {target_root / task_config / task / args.embodiment}")


def download_data(args: argparse.Namespace) -> int:
    root = workspace_root(args.workspace) if args.workspace else None
    if root:
        assert_workspace(root)
    target_root = (args.target_root or ((root / "data") if root else Path("data"))).expanduser().resolve()
    cache_root = (args.cache_root or (target_root / "download_cache")).expanduser().resolve()
    if not args.archive_name.lower().endswith(".zip"):
        raise UserError("--archive-name must end with .zip")
    task_config = Path(args.archive_name).name[:-4]
    safe_name(task_config, "task config derived from archive name")

    tasks = list(dict.fromkeys(args.tasks)) if args.tasks else []
    if not tasks:
        if not args.execute:
            print("dry-run: would discover available tasks from Hugging Face because no task names were provided")
            return 0
        tasks = discover_tasks(args.repo_id, args.revision, args.archive_name)
    for task in tasks:
        safe_name(task, "task name")

    print(f"data_target={target_root}")
    print(f"archive_cache={cache_root}")
    if not args.execute:
        for task in tasks:
            print(f"would download: hf://datasets/{args.repo_id}/dataset/{task}/{args.archive_name}")
        print("dry-run only; add --execute to download and extract")
        return 0
    try:
        import huggingface_hub  # noqa: F401
    except Exception as exc:
        raise UserError("huggingface_hub is required for --execute data download") from exc
    target_root.mkdir(parents=True, exist_ok=True)
    cache_root.mkdir(parents=True, exist_ok=True)
    for task in tasks:
        download_one_data_archive(task, args, target_root, cache_root)
    return 0


def collect(args: argparse.Namespace) -> int:
    root = workspace_root(args.workspace)
    assert_workspace(root)
    safe_name(args.task_name, "task name")
    safe_name(args.task_config, "task config")
    cmd = ["bash", "collect_data.sh", args.task_name, args.task_config, str(args.gpu_id)]
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(args.gpu_id)
    return run(cmd, cwd=root, execute=args.execute, env=env)


def eval_policy(args: argparse.Namespace) -> int:
    root = workspace_root(args.workspace)
    assert_workspace(root)
    tail = list(args.eval_args)
    if tail and tail[0] == "--":
        tail = tail[1:]
    if not tail:
        raise UserError("Pass RoboTwin evaluation arguments after '--', for example: eval --workspace RoboTwin -- multitask --config env_cfg/eval/all_tasks.yml --dry-run ...")
    cmd = ["bash", "scripts/eval_policy.sh", *tail]
    return run(cmd, cwd=root, execute=args.execute)


def print_manifest(_args: argparse.Namespace) -> int:
    manifest = {
        "schemaVersion": 1,
        "robotwin": {"remote": DEFAULT_REMOTE, "branch": DEFAULT_BRANCH, "revision": DEFAULT_REVISION},
        "xpolicylab": {"path": XPOLICYLAB_PATH, "remote": XPOLICYLAB_REMOTE, "revision": XPOLICYLAB_REVISION},
        "huggingface": {"repo_id": HF_REPO_ID, "revision": HF_REVISION, "asset_archives": ASSET_ARCHIVES, "data_archive_pattern": "dataset/<task>/<archive_name>"},
        "entryPoints": ["bootstrap", "check", "download-assets", "download-data", "collect", "eval"],
    }
    print(json.dumps(manifest, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("manifest", help="Print the public source/data artifact manifest.")
    p.set_defaults(func=print_manifest)

    p = sub.add_parser("bootstrap", help="Materialize a pinned RoboTwin workspace from public source.")
    p.add_argument("--workspace", required=True, type=Path)
    p.add_argument("--remote", default=DEFAULT_REMOTE)
    p.add_argument("--revision", default=DEFAULT_REVISION)
    p.add_argument("--branch", default=DEFAULT_BRANCH)
    p.add_argument("--with-xpolicylab", action="store_true", help="Initialize XPolicyLab submodule and pin it when possible.")
    p.add_argument("--xpolicylab-revision", default=XPOLICYLAB_REVISION)
    p.add_argument("--allow-dirty", action="store_true", help="Allow checkout mutation when target workspace has local changes.")
    p.add_argument("--execute", action="store_true", help="Actually run git commands. Omit for dry-run command preview.")
    p.set_defaults(func=bootstrap)

    p = sub.add_parser("check", help="Read-only prerequisite check for a RoboTwin workspace and current Python.")
    p.add_argument("--workspace", required=True, type=Path)
    p.set_defaults(func=check)

    p = sub.add_parser("download-assets", help="Download and extract public RoboTwin asset archives.")
    p.add_argument("--workspace", required=True, type=Path)
    p.add_argument("--repo-id", default=HF_REPO_ID)
    p.add_argument("--revision", default=HF_REVISION)
    p.add_argument("--force-extract", action="store_true")
    p.add_argument("--execute", action="store_true", help="Actually download/extract. Omit for dry-run summary.")
    p.set_defaults(func=download_assets)

    p = sub.add_parser("download-data", help="Download and normalize public RoboTwin trajectory archives without source scripts.")
    p.add_argument("tasks", nargs="*", help="Task names. Omit to discover all tasks when executing.")
    p.add_argument("--workspace", type=Path, help="Optional RoboTwin workspace; target defaults to <workspace>/data.")
    p.add_argument("--target-root", type=Path, help="Output data root. Default: <workspace>/data or ./data.")
    p.add_argument("--cache-root", type=Path, help="Archive cache root. Default: <target-root>/download_cache.")
    p.add_argument("--repo-id", default=HF_REPO_ID)
    p.add_argument("--revision", default=HF_REVISION)
    p.add_argument("--archive-name", default="demo_clean.zip")
    p.add_argument("--embodiment", default=DEFAULT_EMBODIMENT)
    p.add_argument("--force-download", action="store_true")
    p.add_argument("--force-extract", action="store_true")
    p.add_argument("--execute", action="store_true", help="Actually download/extract. Omit for dry-run summary.")
    p.set_defaults(func=download_data)

    p = sub.add_parser("collect", help="Dispatch RoboTwin collection through this bundled wrapper.")
    p.add_argument("--workspace", required=True, type=Path)
    p.add_argument("--task-name", required=True)
    p.add_argument("--task-config", required=True)
    p.add_argument("--gpu-id", required=True)
    p.add_argument("--execute", action="store_true", help="Actually run collection. Omit for command preview.")
    p.set_defaults(func=collect)

    p = sub.add_parser("eval", help="Dispatch RoboTwin/XPolicyLab evaluation through this bundled wrapper.")
    p.add_argument("--workspace", required=True, type=Path)
    p.add_argument("--execute", action="store_true", help="Actually run eval command. Omit for command preview.")
    p.add_argument("eval_args", nargs=argparse.REMAINDER)
    p.set_defaults(func=eval_policy)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except UserError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
