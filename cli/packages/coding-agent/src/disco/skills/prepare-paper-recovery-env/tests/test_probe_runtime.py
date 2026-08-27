import json
import subprocess
import sys
from pathlib import Path
import tempfile

from probe_runtime import (
    benchmark_probe,
    bounded_model_cache_probe,
    default_recovery_env_prefix,
    has_worktree_content,
    load_command_log,
    package_probe,
    run_command,
    snapshot_files,
    write_command_log,
)


def test_package_probe_reports_boolean_values():
    result = package_probe(["sys", "definitely_missing_distiller_probe_pkg"])
    assert result["sys"] is True
    assert result["definitely_missing_distiller_probe_pkg"] is False


def test_default_recovery_env_prefix_uses_disco_agent_env_root(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        monkeypatch.setenv("DISCO_CODING_AGENT_DIR", str(root / "agent"))
        prefix = default_recovery_env_prefix(root / "my_paper" / "distillation")
        assert prefix == root / "agent" / "envs" / "paper-recovery-my_paper"


def test_bounded_model_cache_probe_finds_named_cache_dir():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "models--Qwen--Qwen3-4B").mkdir()
        result = bounded_model_cache_probe(["Qwen/Qwen3-4B"], [root], timeout=2)
        assert result["timed_out"] is False
        assert result["cache_hits"]


def test_snapshot_files_copies_resource_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = root / "alfred.twl2"
        source.write_text("grammar", encoding="utf-8")
        copied = snapshot_files([source], root / "snapshot")
        assert len(copied) == 1
        assert Path(copied[0]).read_text(encoding="utf-8") == "grammar"


def test_run_command_appends_command_log_entry():
    command_log = []
    result = run_command(["python", "-c", "print('ok')"], timeout=5, command_log=command_log, label="unit")
    assert result["returncode"] == 0
    assert command_log
    assert command_log[0]["label"] == "unit"
    assert "python" in command_log[0]["command"]


def test_command_log_loader_preserves_existing_entries():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "command_log.json"
        write_command_log(path, "created", [{"label": "first", "command": "true"}])
        created_at, commands = load_command_log(path)
        commands.append({"label": "second", "command": "false"})
        write_command_log(path, created_at, commands)

        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["created_at_utc"] == "created"
        assert [item["label"] for item in data["commands"]] == ["first", "second"]


def test_partial_clone_with_only_git_is_not_usable_benchmark_source():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        clone_dir = root / "partial_clone"
        (clone_dir / ".git").mkdir(parents=True)
        assert has_worktree_content(clone_dir) is False

        class Args:
            attempt_dir = str(root / "attempt")
            benchmark_name = "alfworld"
            benchmark_url = "https://example.invalid/alfworld.git"
            fresh_clone_dir = str(clone_dir)
            attempt_fresh_clone = False
            reuse_benchmark_path = ""
            resource_file = ["README.md"]
            network_timeout = 1
            command_timeout = 1

        result = benchmark_probe(Args(), root / "attempt/environment/logs", command_log=[])
        assert result["fresh_ok"] is False
        assert result["reused_local_source"] == ""
        assert any("partial" in blocker or "empty" in blocker for blocker in result["blockers"])


def test_probe_runtime_appends_command_log_across_runs():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = root / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("benchmark", encoding="utf-8")
        subprocess.run(["git", "init"], cwd=str(repo), check=True, text=True, capture_output=True, timeout=10)
        subprocess.run(["git", "add", "README.md"], cwd=str(repo), check=True, text=True, capture_output=True, timeout=10)
        subprocess.run(
            ["git", "-c", "user.email=test@example.com", "-c", "user.name=Test", "commit", "-m", "init"],
            cwd=str(repo),
            check=True,
            text=True,
            capture_output=True,
            timeout=10,
        )
        script = Path(__file__).resolve().parents[1] / "scripts" / "probe_runtime.py"
        common = [
            sys.executable,
            str(script),
            "--attempt-dir",
            str(root / "attempt"),
            "--package",
            "sys",
            "--benchmark-name",
            "localbench",
            "--reuse-benchmark-path",
            str(repo),
            "--resource-file",
            "README.md",
            "--command-timeout",
            "1",
        ]
        subprocess.run(common, check=True, text=True, capture_output=True, timeout=10)
        subprocess.run(common, check=True, text=True, capture_output=True, timeout=10)

        data = json.loads((root / "attempt/environment/logs/command_log.json").read_text(encoding="utf-8"))
        labels = [item.get("label") for item in data["commands"]]
        assert labels.count("benchmark_reuse_git_worktree") == 2
        assert labels.count("benchmark_reuse_git_commit") == 2


def test_probe_runtime_updates_manifest_prepare_stage():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        attempt.mkdir()
        (attempt / "run_manifest.json").write_text(
            json.dumps({"stages": {"prepare_environment": "pending"}}) + "\n",
            encoding="utf-8",
        )
        script = Path(__file__).resolve().parents[1] / "scripts" / "probe_runtime.py"

        subprocess.run(
            [
                sys.executable,
                str(script),
                "--attempt-dir",
                str(attempt),
                "--package",
                "sys",
                "--preferred-model",
                "missing-model",
                "--command-timeout",
                "1",
            ],
            check=True,
            text=True,
            capture_output=True,
            timeout=10,
        )

        manifest = json.loads((attempt / "run_manifest.json").read_text(encoding="utf-8"))
        assert manifest["stages"]["prepare_environment"] == "blocked"
        assert manifest["environment_handoff"].endswith("environment/runtime_handoff.json")
        assert manifest["environment_command_log"].endswith("environment/logs/command_log.json")


def test_probe_runtime_attempts_isolated_env_when_mutation_allowed():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        attempt = root / "attempt"
        env_prefix = root / "envs" / "paper-recovery-attempt"
        script = Path(__file__).resolve().parents[1] / "scripts" / "probe_runtime.py"

        subprocess.run(
            [
                sys.executable,
                str(script),
                "--attempt-dir",
                str(attempt),
                "--package",
                "definitely_missing_distiller_probe_pkg",
                "--allow-env-mutation",
                "--env-prefix",
                str(env_prefix),
                "--env-manager",
                "venv",
                "--install-timeout",
                "1",
                "--command-timeout",
                "1",
            ],
            check=True,
            text=True,
            capture_output=True,
            timeout=20,
        )

        setup = json.loads((attempt / "environment/logs/environment_setup.json").read_text(encoding="utf-8"))
        command_log = json.loads((attempt / "environment/logs/command_log.json").read_text(encoding="utf-8"))
        labels = [item.get("label") for item in command_log["commands"]]
        assert setup["requested_prefix"] == str(env_prefix.resolve())
        assert setup["strategy"] == "isolated_environment_repair"
        assert "create_isolated_venv" in labels
        assert "pip_install_definitely_missing_distiller_probe_pkg" in labels
