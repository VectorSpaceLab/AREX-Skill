#!/usr/bin/env python3
"""Probe a Paper2Skills recovery runtime and write an auditable handoff."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlparse
from pathlib import Path


DEFAULT_PACKAGES = [
    "torch",
    "transformers",
    "huggingface_hub",
    "accelerate",
    "tokenizers",
    "datasets",
]

DEFAULT_PIP_PACKAGE_SPECS = {
    "huggingface_hub": "huggingface_hub",
    "sklearn": "scikit-learn",
}

DEFAULT_PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_manifest_stage(attempt_dir: Path, status: str, handoff_path: Path, command_log_path: Path) -> None:
    manifest_path = attempt_dir / "run_manifest.json"
    if not manifest_path.exists():
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return
    stages = manifest.setdefault("stages", {})
    if isinstance(stages, dict):
        stages["prepare_environment"] = status
    manifest["environment_handoff"] = str(handoff_path)
    manifest["environment_command_log"] = str(command_log_path)
    manifest["environment_prepared_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_command_log(path: Path) -> tuple[str, list[dict]]:
    created_at = datetime.now(timezone.utc).isoformat()
    if not path.exists():
        return created_at, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return created_at, []
    commands = data.get("commands", [])
    if not isinstance(commands, list):
        commands = []
    commands = [item for item in commands if isinstance(item, dict)]
    return data.get("created_at_utc") or created_at, commands


def write_command_log(path: Path, created_at_utc: str, command_log: list[dict]) -> None:
    write_json(
        path,
        {
            "schema_version": 1,
            "created_at_utc": created_at_utc,
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "commands": command_log,
        },
    )


def run_command(
    cmd: list[str],
    timeout: int,
    cwd: Path | None = None,
    command_log: list[dict] | None = None,
    label: str = "",
) -> dict:
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        status = "completed"
        returncode = proc.returncode
        stdout = proc.stdout[-4000:]
        stderr = proc.stderr[-4000:]
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        returncode = 124
        stdout = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
    except Exception as exc:  # pragma: no cover - defensive
        status = "error"
        returncode = 1
        stdout = ""
        stderr = repr(exc)
    result = {
        "command": " ".join(cmd),
        "label": label,
        "status": status,
        "returncode": returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": stdout,
        "stderr_tail": stderr,
    }
    if command_log is not None:
        command_log.append(result)
    return result


def package_probe(
    packages: list[str],
    python_executable: str | Path | None = None,
    timeout: int = 20,
    command_log: list[dict] | None = None,
) -> dict:
    if not python_executable or Path(python_executable).expanduser().absolute() == Path(
        sys.executable
    ).expanduser().absolute():
        return {name: importlib.util.find_spec(name) is not None for name in packages}

    code = (
        "import importlib.util,json,sys;"
        "packages=json.loads(sys.argv[1]);"
        "print(json.dumps({name: importlib.util.find_spec(name) is not None for name in packages}))"
    )
    command = run_command(
        [str(python_executable), "-c", code, json.dumps(packages)],
        timeout=timeout,
        command_log=command_log,
        label="package_probe",
    )
    if command["returncode"] != 0:
        return {name: False for name in packages}
    try:
        return json.loads(command["stdout_tail"].strip().splitlines()[-1])
    except Exception:
        return {name: False for name in packages}


def python_version_probe(python_executable: Path, timeout: int, command_log: list[dict]) -> str:
    if python_executable.expanduser().absolute() == Path(sys.executable).expanduser().absolute():
        return sys.version.split()[0]
    command = run_command(
        [str(python_executable), "--version"],
        timeout=timeout,
        command_log=command_log,
        label="recovery_python_version",
    )
    version_text = (command.get("stdout_tail") or command.get("stderr_tail") or "").strip()
    return version_text.replace("Python ", "", 1).strip() or "unknown"


def unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        value = value.strip()
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def venv_python(prefix: Path) -> Path:
    return prefix / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def find_env_python(prefix: Path) -> Path | None:
    candidates = [
        prefix / "bin" / "python",
        prefix / "bin" / "python3",
        prefix / "python",
        prefix / "Scripts" / "python.exe",
    ]
    for candidate in candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return candidate
    return None


def find_conda(conda_exe: str) -> str | None:
    discovered = shutil.which(conda_exe)
    if discovered:
        return discovered
    explicit = Path(conda_exe).expanduser()
    if explicit.exists():
        return str(explicit)
    return None


def conda_root_prefix(conda_executable: str, timeout: int, command_log: list[dict]) -> str:
    command = run_command(
        [conda_executable, "info", "--json"],
        timeout=timeout,
        command_log=command_log,
        label="conda_info",
    )
    if command["returncode"] != 0:
        return ""
    try:
        payload = json.loads(command["stdout_tail"])
    except Exception:
        return ""
    return str(payload.get("root_prefix") or "")


def safe_name(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._-")
    return cleaned or fallback


def recovery_env_name(attempt_dir: Path) -> str:
    name = attempt_dir.name
    if name in {"distillation", "attempt", "attempts"} and attempt_dir.parent.name:
        name = attempt_dir.parent.name
    return f"paper-recovery-{safe_name(name, 'recovery')}"


def default_recovery_env_prefix(attempt_dir: Path) -> Path:
    agent_dir = Path(os.environ.get("DISCO_CODING_AGENT_DIR") or Path.home() / ".disco" / "agent").expanduser()
    return agent_dir / "envs" / recovery_env_name(attempt_dir)


def parse_pip_package_specs(values: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for value in values:
        item = value.strip()
        if not item:
            continue
        if "=" in item:
            import_name, spec = item.split("=", 1)
            import_name = import_name.strip()
            spec = spec.strip()
        else:
            spec = item
            import_name = re.split(r"[<>=!~\[]", item, maxsplit=1)[0].replace("-", "_").strip()
        if import_name and spec:
            mapping[import_name] = spec
    return mapping


def create_or_reuse_environment(
    prefix: Path,
    manager: str,
    python_version: str,
    conda_executable: str,
    timeout: int,
    command_log: list[dict],
) -> tuple[Path | None, dict]:
    existing_python = find_env_python(prefix)
    if existing_python:
        existing_manager = "conda" if (prefix / "conda-meta").exists() else "venv"
        return existing_python, {
            "action": f"reuse_isolated_{existing_manager}",
            "manager": existing_manager,
            "prefix": str(prefix),
            "python": str(existing_python),
            "ok": True,
            "modified": False,
        }

    conda_path = find_conda(conda_executable)
    selected_manager = manager
    if selected_manager == "auto":
        selected_manager = "conda" if conda_path else "venv"
    if selected_manager == "conda" and not conda_path:
        return None, {
            "action": "create_isolated_conda",
            "manager": "conda",
            "prefix": str(prefix),
            "python": str(prefix / "bin" / "python"),
            "ok": False,
            "modified": False,
            "blocker": f"conda executable not found: {conda_executable}",
        }

    if selected_manager == "conda":
        root_prefix = conda_root_prefix(str(conda_path), timeout=timeout, command_log=command_log)
        if root_prefix and Path(root_prefix).expanduser().resolve() == prefix:
            return None, {
                "action": "create_isolated_conda",
                "manager": "conda",
                "prefix": str(prefix),
                "python": str(prefix / "bin" / "python"),
                "ok": False,
                "modified": False,
                "blocker": "target prefix resolves to the conda base/root prefix",
            }
        command = run_command(
            [
                str(conda_path),
                "create",
                "-y",
                "-p",
                str(prefix),
                f"python={python_version}",
                "pip",
            ],
            timeout=timeout,
            command_log=command_log,
            label="create_isolated_conda",
        )
    else:
        command = run_command(
            [sys.executable, "-m", "venv", "--upgrade-deps", str(prefix)],
            timeout=timeout,
            command_log=command_log,
            label="create_isolated_venv",
        )

    python_path = find_env_python(prefix)
    ok = command["returncode"] == 0 and python_path is not None
    return (
        python_path if ok else None,
        {
            "action": f"create_isolated_{selected_manager}",
            "manager": selected_manager,
            "prefix": str(prefix),
            "python": str(python_path or venv_python(prefix)),
            "ok": ok,
            "modified": True,
            "command": command,
        },
    )


def install_missing_packages(
    python_executable: Path,
    missing_packages: list[str],
    pip_specs: dict[str, str],
    timeout: int,
    command_log: list[dict],
    pip_index_url: str = "",
    pip_extra_index_urls: list[str] | None = None,
) -> list[dict]:
    actions: list[dict] = []
    extra_index_urls = pip_extra_index_urls or []
    for import_name in missing_packages:
        spec = pip_specs.get(import_name) or DEFAULT_PIP_PACKAGE_SPECS.get(import_name) or import_name
        cmd = [str(python_executable), "-m", "pip", "install", spec]
        if pip_index_url:
            cmd.extend(["--index-url", pip_index_url])
        for extra_url in extra_index_urls:
            if extra_url:
                cmd.extend(["--extra-index-url", extra_url])
        command = run_command(cmd, timeout=timeout, command_log=command_log, label=f"pip_install_{import_name}")
        actions.append(
            {
                "action": "pip_install",
                "import_name": import_name,
                "pip_spec": spec,
                "ok": command["returncode"] == 0,
                "command": command,
            }
        )
    return actions


def attempt_model_download(
    model_id: str,
    attempt_dir: Path,
    python_executable: Path,
    timeout: int,
    command_log: list[dict],
) -> dict:
    result = {
        "attempted": False,
        "model_id": model_id,
        "local_dir": "",
        "ok": False,
        "command": None,
        "blockers": [],
    }
    if not model_id:
        return result

    local_dir = attempt_dir / "environment" / "model_cache" / safe_name(model_id.replace("/", "--"), "model")
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    code = (
        "import json,sys;"
        "from huggingface_hub import snapshot_download;"
        "path=snapshot_download(repo_id=sys.argv[1], local_dir=sys.argv[2], local_dir_use_symlinks=False);"
        "print(json.dumps({'path': path}))"
    )
    command = run_command(
        [str(python_executable), "-c", code, model_id, str(local_dir)],
        timeout=timeout,
        command_log=command_log,
        label="model_snapshot_download",
    )
    result["attempted"] = True
    result["local_dir"] = str(local_dir)
    result["command"] = command
    if command["returncode"] == 0 and local_dir.exists() and any(local_dir.iterdir()):
        result["ok"] = True
    else:
        blocker = command["stderr_tail"] or command["stdout_tail"] or f"snapshot_download failed with {command['returncode']}"
        result["blockers"].append(blocker)
    return result


def dataset_probe(args: argparse.Namespace, logs_dir: Path, command_log: list[dict]) -> dict:
    result = {
        "name": args.dataset_name,
        "required": bool(args.require_dataset),
        "paths": [],
        "urls": list(args.dataset_url),
        "download_attempted": False,
        "downloaded_files": [],
        "blockers": [],
    }

    for value in args.dataset_path:
        path = Path(value).expanduser().resolve()
        if path.exists():
            result["paths"].append(str(path))
        else:
            result["blockers"].append(f"dataset path does not exist: {path}")

    if args.dataset_url and args.attempt_dataset_download:
        result["download_attempted"] = True
        dataset_dir = Path(args.attempt_dir).expanduser().resolve() / "environment" / "datasets" / safe_name(args.dataset_name, "dataset")
        dataset_dir.mkdir(parents=True, exist_ok=True)
        for index, url in enumerate(args.dataset_url, start=1):
            parsed = urlparse(url)
            filename = Path(parsed.path).name or f"dataset_{index}.dat"
            target = dataset_dir / safe_name(filename, f"dataset_{index}.dat")
            code = (
                "import json,sys,urllib.request;"
                "url,target,timeout=sys.argv[1],sys.argv[2],float(sys.argv[3]);"
                "urllib.request.urlretrieve(url, target);"
                "print(json.dumps({'target': target}))"
            )
            command = run_command(
                [sys.executable, "-c", code, url, str(target), str(args.network_timeout)],
                timeout=args.network_timeout,
                command_log=command_log,
                label="dataset_download",
            )
            write_json(logs_dir / f"dataset_download_{index}.json", command)
            if command["returncode"] == 0 and target.exists() and target.stat().st_size > 0:
                result["downloaded_files"].append(str(target.resolve()))
            else:
                blocker = command["stderr_tail"] or command["stdout_tail"] or f"dataset download failed with {command['returncode']}"
                result["blockers"].append(blocker)
    elif args.dataset_url:
        result["blockers"].append("dataset URLs were supplied but --attempt-dataset-download was not enabled")

    if args.require_dataset and not result["paths"] and not result["downloaded_files"]:
        result["blockers"].append("required dataset is unavailable after bounded local path and download attempts")
    return result


def gpu_probe(timeout: int, command_log: list[dict]) -> dict:
    nvidia_smi = shutil.which("nvidia-smi")
    result = {
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "nvidia_smi_available": bool(nvidia_smi),
        "devices": [],
        "command": None,
    }
    if not nvidia_smi:
        return result
    cmd = [nvidia_smi, "--query-gpu=index,name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"]
    command = run_command(cmd, timeout=timeout, command_log=command_log, label="gpu_probe")
    result["command"] = command
    if command["returncode"] == 0:
        devices = []
        for line in command["stdout_tail"].splitlines():
            parts = [part.strip() for part in line.split(",")]
            if len(parts) >= 5:
                devices.append(
                    {
                        "index": parts[0],
                        "name": parts[1],
                        "memory_total_mb": parts[2],
                        "memory_used_mb": parts[3],
                        "utilization_gpu_percent": parts[4],
                    }
                )
        result["devices"] = devices
    return result


def bounded_model_cache_probe(model_names: list[str], roots: list[Path], timeout: int) -> dict:
    cache_hits: list[str] = []
    checked_roots: list[str] = []
    patterns = []
    for model in model_names:
        if not model:
            continue
        model_leaf = model.split("/")[-1]
        patterns.extend([model, model.replace("/", "--"), model_leaf])

    deadline = time.time() + max(timeout, 1)
    for root in roots:
        root = root.expanduser()
        if not root.exists():
            continue
        checked_roots.append(str(root.resolve()))
        try:
            for child in root.iterdir():
                if time.time() > deadline:
                    return {"checked_roots": checked_roots, "cache_hits": cache_hits, "timed_out": True}
                name = child.name
                if any(pattern and pattern in name for pattern in patterns):
                    cache_hits.append(str(child.resolve()))
        except Exception:
            continue
    return {"checked_roots": checked_roots, "cache_hits": cache_hits, "timed_out": False}


def snapshot_files(files: list[Path], snapshot_dir: Path) -> list[str]:
    copied: list[str] = []
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    for source in files:
        if not source.exists() or not source.is_file():
            continue
        target = snapshot_dir / source.name
        suffix = 1
        while target.exists():
            target = snapshot_dir / f"{source.stem}_{suffix}{source.suffix}"
            suffix += 1
        shutil.copy2(source, target)
        copied.append(str(target.resolve()))
    return copied


def git_commit(path: Path, timeout: int, command_log: list[dict], label: str = "benchmark_git_commit") -> str:
    if not (path / ".git").exists():
        return ""
    result = run_command(
        ["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
        timeout=timeout,
        command_log=command_log,
        label=label,
    )
    if result["returncode"] == 0:
        return result["stdout_tail"].strip()
    return ""


def has_worktree_content(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    try:
        return any(child.name != ".git" for child in path.iterdir())
    except Exception:
        return False


def requested_resource_files(source_root: Path, resource_relpaths: list[str]) -> tuple[list[Path], list[str]]:
    resources: list[Path] = []
    missing: list[str] = []
    for rel in resource_relpaths:
        if not rel:
            continue
        candidate = source_root / rel
        if candidate.exists() and candidate.is_file():
            resources.append(candidate)
        else:
            missing.append(rel)
    return resources, missing


def validate_benchmark_source(
    source_root: Path,
    resource_relpaths: list[str],
    timeout: int,
    command_log: list[dict],
    label_prefix: str,
) -> dict:
    validation = {
        "path": str(source_root),
        "ok": False,
        "is_git_worktree": False,
        "commit": "",
        "resource_files": [],
        "missing_resource_files": [],
        "issues": [],
    }
    if not source_root.exists() or not source_root.is_dir():
        validation["issues"].append("source path does not exist or is not a directory")
        return validation

    resources, missing = requested_resource_files(source_root, resource_relpaths)
    validation["resource_files"] = [str(path.resolve()) for path in resources]
    validation["missing_resource_files"] = missing
    if missing:
        validation["issues"].append("requested resource files are missing: " + ", ".join(missing))

    if not has_worktree_content(source_root):
        validation["issues"].append("source contains no worktree/data files beyond .git")

    if (source_root / ".git").exists():
        worktree = run_command(
            ["git", "-C", str(source_root), "rev-parse", "--is-inside-work-tree"],
            timeout=timeout,
            command_log=command_log,
            label=f"{label_prefix}_git_worktree",
        )
        if worktree["returncode"] == 0 and worktree["stdout_tail"].strip() == "true":
            validation["is_git_worktree"] = True
        else:
            validation["issues"].append("git worktree validation failed")
        commit = git_commit(
            source_root,
            timeout=timeout,
            command_log=command_log,
            label=f"{label_prefix}_git_commit",
        )
        validation["commit"] = commit
        if not commit:
            validation["issues"].append("git commit could not be resolved")

    validation["ok"] = not validation["issues"]
    return validation


def benchmark_probe(args: argparse.Namespace, logs_dir: Path, command_log: list[dict]) -> dict:
    resource_relpaths = [item for item in args.resource_file if item]
    result = {
        "name": args.benchmark_name,
        "url": args.benchmark_url,
        "fresh_attempted": False,
        "fresh_ok": False,
        "fresh_command": "",
        "fresh_result": None,
        "reused_local_source": "",
        "reused_commit": "",
        "snapshot_dir": "",
        "resource_files": [],
        "source_validation": None,
        "blockers": [],
    }

    if args.benchmark_url and args.fresh_clone_dir:
        clone_dir = Path(args.fresh_clone_dir).expanduser().resolve()
        result["fresh_attempted"] = True
        if clone_dir.exists() and has_worktree_content(clone_dir):
            validation = validate_benchmark_source(
                clone_dir,
                resource_relpaths,
                timeout=args.command_timeout,
                command_log=command_log,
                label_prefix="benchmark_fresh_existing",
            )
            result["source_validation"] = validation
            if validation["ok"]:
                result["fresh_ok"] = True
                result["fresh_command"] = "existing clone"
                result["reused_local_source"] = str(clone_dir)
                result["reused_commit"] = validation.get("commit", "")
            else:
                result["fresh_command"] = "existing clone failed validation"
                result["blockers"].append("existing fresh clone failed validation: " + "; ".join(validation["issues"]))
        elif clone_dir.exists() and not has_worktree_content(clone_dir):
            result["fresh_command"] = "existing clone failed validation"
            result["blockers"].append("existing fresh clone is partial or empty and was not reused")
        elif args.attempt_fresh_clone:
            cmd = ["git", "clone", "--depth", "1", args.benchmark_url, str(clone_dir)]
            command = run_command(
                cmd,
                timeout=args.network_timeout,
                command_log=command_log,
                label="benchmark_fresh_clone",
            )
            result["fresh_command"] = " ".join(cmd)
            result["fresh_result"] = command
            write_json(logs_dir / "benchmark_fresh_clone_command.json", command)
            if command["returncode"] == 0:
                validation = validate_benchmark_source(
                    clone_dir,
                    resource_relpaths,
                    timeout=args.command_timeout,
                    command_log=command_log,
                    label_prefix="benchmark_fresh",
                )
                result["source_validation"] = validation
                if validation["ok"]:
                    result["fresh_ok"] = True
                    result["reused_local_source"] = str(clone_dir)
                    result["reused_commit"] = validation.get("commit", "")
                else:
                    result["blockers"].append("fresh clone failed validation: " + "; ".join(validation["issues"]))
            else:
                blocker = command["stderr_tail"] or command["stdout_tail"] or f"clone failed with {command['returncode']}"
                result["blockers"].append(blocker)
        else:
            result["fresh_command"] = "fresh clone disabled by caller"

    local_source = Path(args.reuse_benchmark_path).expanduser().resolve() if args.reuse_benchmark_path else None
    if not result["fresh_ok"] and local_source and local_source.exists():
        validation = validate_benchmark_source(
            local_source,
            resource_relpaths,
            timeout=args.command_timeout,
            command_log=command_log,
            label_prefix="benchmark_reuse",
        )
        result["source_validation"] = validation
        if validation["ok"]:
            result["reused_local_source"] = str(local_source)
            result["reused_commit"] = validation.get("commit", "")
        else:
            result["blockers"].append("reuse benchmark source failed validation: " + "; ".join(validation["issues"]))

    source_root = Path(result["reused_local_source"]) if result["reused_local_source"] else None
    if source_root and source_root.exists():
        resources, missing = requested_resource_files(source_root, resource_relpaths)
        if missing:
            result["blockers"].append("snapshot resource files are missing: " + ", ".join(missing))
        if not resource_relpaths:
            result["blockers"].append("no benchmark resource files were requested for snapshot")
        snapshot_dir = Path(args.attempt_dir).expanduser().resolve() / "environment" / "benchmark_sources" / f"{args.benchmark_name}_snapshot"
        result["snapshot_dir"] = str(snapshot_dir.resolve())
        result["resource_files"] = snapshot_files(resources, snapshot_dir)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt-dir", required=True)
    parser.add_argument("--preferred-model", default="")
    parser.add_argument("--fallback-model", default="")
    parser.add_argument("--package", action="append", default=[])
    parser.add_argument(
        "--pip-package",
        action="append",
        default=[],
        help="Package install spec. Use import_name=pip_spec when the import name differs from the pip package.",
    )
    parser.add_argument(
        "--env-prefix",
        default="",
        help="Isolated recovery environment prefix. Defaults to $DISCO_CODING_AGENT_DIR/envs/paper-recovery-<run> or ~/.disco/agent/envs/paper-recovery-<run>.",
    )
    parser.add_argument(
        "--env-manager",
        choices=["auto", "conda", "venv"],
        default="auto",
        help="Environment manager for isolated recovery envs. auto prefers conda and falls back to venv.",
    )
    parser.add_argument(
        "--python-version",
        default=DEFAULT_PYTHON_VERSION,
        help=f"Python version for a new conda recovery env. Defaults to the host family ({DEFAULT_PYTHON_VERSION}).",
    )
    parser.add_argument(
        "--conda",
        default="conda",
        help="Conda executable name/path when --env-manager is auto or conda.",
    )
    parser.add_argument("--cache-root", action="append", default=[])
    parser.add_argument("--pip-index-url", default="")
    parser.add_argument("--pip-extra-index-url", action="append", default=[])
    parser.add_argument("--benchmark-name", default="alfworld")
    parser.add_argument("--benchmark-url", default="")
    parser.add_argument("--fresh-clone-dir", default="")
    parser.add_argument("--attempt-fresh-clone", action="store_true")
    parser.add_argument("--reuse-benchmark-path", default="")
    parser.add_argument("--resource-file", action="append", default=[])
    parser.add_argument("--dataset-name", default="dataset")
    parser.add_argument("--dataset-path", action="append", default=[])
    parser.add_argument("--dataset-url", action="append", default=[])
    parser.add_argument("--require-dataset", action="store_true")
    parser.add_argument("--attempt-dataset-download", action="store_true")
    parser.add_argument("--attempt-model-download", action="store_true")
    parser.add_argument("--network-timeout", type=int, default=120)
    parser.add_argument("--command-timeout", type=int, default=20)
    parser.add_argument("--install-timeout", type=int, default=600)
    parser.add_argument("--env-setup-timeout", type=int, default=120)
    parser.add_argument("--allow-env-mutation", action="store_true")
    parser.add_argument(
        "--use-isolated-env",
        action="store_true",
        help="Use/create the isolated recovery env even when the active Python already has the requested imports.",
    )
    parser.add_argument("--reduced-recovery-allowed", action="store_true")
    args = parser.parse_args()

    attempt_dir = Path(args.attempt_dir).expanduser().resolve()
    env_dir = attempt_dir / "environment"
    logs_dir = env_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    command_log_path = logs_dir / "command_log.json"
    command_log_created_at, command_log = load_command_log(command_log_path)

    packages = unique_ordered(args.package or DEFAULT_PACKAGES)
    pip_specs = parse_pip_package_specs(args.pip_package)
    host_python = Path(sys.executable)
    active_python = host_python
    env_prefix = Path(args.env_prefix).expanduser().resolve() if args.env_prefix else default_recovery_env_prefix(attempt_dir)
    env_setup = {
        "strategy": "current_python_probe_only",
        "default_prefix": str(default_recovery_env_prefix(attempt_dir)),
        "requested_prefix": str(env_prefix),
        "requested_manager": args.env_manager,
        "python_version": args.python_version,
        "host_python": str(host_python),
        "python": str(active_python),
        "actions": [],
        "blockers": [],
        "modified": False,
    }

    initial_packages_result = package_probe(packages)
    write_json(logs_dir / "package_probe_initial.json", initial_packages_result)
    missing_packages = [name for name, present in initial_packages_result.items() if not present]
    packages_result = dict(initial_packages_result)

    if missing_packages or args.use_isolated_env:
        if args.allow_env_mutation:
            env_setup["strategy"] = "isolated_environment_repair"
            prepared_python, setup_action = create_or_reuse_environment(
                env_prefix,
                manager=args.env_manager,
                python_version=args.python_version,
                conda_executable=args.conda,
                timeout=args.env_setup_timeout,
                command_log=command_log,
            )
            env_setup["actions"].append(setup_action)
            env_setup["modified"] = bool(env_setup["modified"] or setup_action.get("modified"))
            if prepared_python:
                prepared_packages_result = package_probe(
                    packages,
                    python_executable=prepared_python,
                    timeout=args.command_timeout,
                    command_log=command_log,
                )
                missing_in_prepared = [
                    name for name, present in prepared_packages_result.items() if not present
                ]
                install_actions = install_missing_packages(
                    prepared_python,
                    missing_in_prepared,
                    pip_specs=pip_specs,
                    timeout=args.install_timeout,
                    command_log=command_log,
                    pip_index_url=args.pip_index_url,
                    pip_extra_index_urls=args.pip_extra_index_url,
                )
                env_setup["actions"].extend(install_actions)
                env_setup["modified"] = bool(env_setup["modified"] or install_actions)
                packages_result = package_probe(
                    packages,
                    python_executable=prepared_python,
                    timeout=args.command_timeout,
                    command_log=command_log,
                )
                active_python = prepared_python
                env_setup["python"] = str(active_python)
                still_missing = [name for name, present in packages_result.items() if not present]
                if still_missing:
                    env_setup["blockers"].append(
                        "packages still missing after isolated environment preparation: " + ", ".join(still_missing)
                    )
            else:
                detail = setup_action.get("blocker") or "isolated recovery environment creation failed; see command_log.json"
                env_setup["blockers"].append(str(detail))
        else:
            env_setup["blockers"].append(
                "isolated environment preparation was requested or packages are missing, but environment preparation was not enabled"
            )

    write_json(logs_dir / "environment_setup.json", env_setup)
    write_json(logs_dir / "package_probe.json", packages_result)

    gpu_result = gpu_probe(timeout=args.command_timeout, command_log=command_log)
    write_json(logs_dir / "gpu_probe.json", gpu_result)

    cache_roots = [
        Path(value)
        for value in [
            *args.cache_root,
            os.environ.get("HF_HOME", ""),
            os.environ.get("TRANSFORMERS_CACHE", ""),
            "~/.cache/huggingface",
            str(Path.cwd()),
        ]
        if value
    ]
    model_required = bool(args.preferred_model or args.fallback_model)
    model_result = bounded_model_cache_probe(
        [args.preferred_model, args.fallback_model],
        cache_roots,
        timeout=args.command_timeout,
    )
    model_result["preferred"] = args.preferred_model
    model_result["fallback"] = args.fallback_model
    model_result["required"] = model_required
    model_result["python"] = str(active_python)
    model_result["required_packages_present"] = (not model_required) or all(
        packages_result.get(name, False) for name in ["torch", "transformers"]
    )
    model_download_result = {
        "attempted": False,
        "ok": False,
        "blockers": [],
    }
    if model_required and not model_result["cache_hits"] and args.attempt_model_download:
        if not packages_result.get("huggingface_hub", False):
            model_download_result["blockers"].append("huggingface_hub is not importable in the selected recovery Python.")
        else:
            model_download_result = attempt_model_download(
                args.preferred_model or args.fallback_model,
                attempt_dir=attempt_dir,
                python_executable=active_python,
                timeout=args.network_timeout,
                command_log=command_log,
            )
            if model_download_result.get("ok") and model_download_result.get("local_dir"):
                model_result["cache_hits"].append(str(model_download_result["local_dir"]))
    model_result["download"] = model_download_result
    model_result["preferred_ready"] = (not model_required) or (
        bool(model_result["cache_hits"]) and model_result["required_packages_present"]
    )
    model_result["blockers"] = []
    if model_required and not model_result["required_packages_present"]:
        model_result["blockers"].append("torch and/or transformers are not importable in the active Python environment.")
    if model_required and not model_result["cache_hits"]:
        if args.attempt_model_download:
            model_result["blockers"].append("no bounded local model cache hit or successful model download was found for the preferred or fallback model.")
        else:
            model_result["blockers"].append("no bounded local model cache hit was found and model download was not enabled.")
    model_result["blockers"].extend(model_download_result.get("blockers", []))
    write_json(logs_dir / "model_cache_probe.json", model_result)

    benchmark_result = benchmark_probe(args, logs_dir, command_log=command_log)
    write_json(logs_dir / "benchmark_probe.json", benchmark_result)
    dataset_result = dataset_probe(args, logs_dir, command_log=command_log)
    write_json(logs_dir / "dataset_probe.json", dataset_result)

    blockers = []
    blockers.extend(env_setup["blockers"])
    blockers.extend(f"missing package: {name}" for name, present in packages_result.items() if not present)
    blockers.extend(model_result["blockers"])
    blockers.extend(benchmark_result.get("blockers", []))
    blockers.extend(dataset_result.get("blockers", []))
    runtime_ready = not blockers and bool(model_result["preferred_ready"])
    reduced_recovery_recommended = bool(args.reduced_recovery_allowed and not runtime_ready)

    allowed_sources = []
    if benchmark_result.get("reused_local_source"):
        allowed_sources.append(benchmark_result["reused_local_source"])
    if benchmark_result.get("snapshot_dir"):
        allowed_sources.append(benchmark_result["snapshot_dir"])
    allowed_sources.extend(benchmark_result.get("resource_files", []))
    allowed_sources.extend(dataset_result.get("paths", []))
    allowed_sources.extend(dataset_result.get("downloaded_files", []))
    active_python_version = python_version_probe(
        active_python,
        timeout=args.command_timeout,
        command_log=command_log,
    )
    selected_environment_manager = "current"
    if active_python != host_python:
        selected_environment_manager = str(env_setup["actions"][-1].get("manager") or "isolated")

    handoff = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "attempt_dir": str(attempt_dir),
        "python": {
            "executable": str(active_python),
            "host_executable": str(host_python),
            "version": active_python_version,
            "host_version": sys.version.split()[0],
        },
        "packages": packages_result,
        "environment": {
            "manager": selected_environment_manager,
            "prefix": str(env_prefix) if active_python != host_python else "",
            "python": str(active_python),
            "setup": env_setup,
        },
        "gpu": gpu_result,
        "models": model_result,
        "benchmarks": {args.benchmark_name: benchmark_result},
        "datasets": {args.dataset_name: dataset_result},
        "runtime_ready": runtime_ready,
        "reduced_recovery_recommended": reduced_recovery_recommended,
        "environment_modified": bool(env_setup.get("modified")),
        "environment_mutation_allowed": bool(args.allow_env_mutation),
        "allowed_sources_for_recovery": allowed_sources,
        "blockers": blockers,
    }
    handoff_path = env_dir / "runtime_handoff.json"
    write_json(handoff_path, handoff)
    write_command_log(command_log_path, command_log_created_at, command_log)
    update_manifest_stage(
        attempt_dir,
        "complete" if runtime_ready else "blocked",
        handoff_path,
        command_log_path,
    )
    print(json.dumps(handoff, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
