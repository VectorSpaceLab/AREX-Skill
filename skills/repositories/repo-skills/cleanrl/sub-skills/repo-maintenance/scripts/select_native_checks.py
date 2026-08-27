#!/usr/bin/env python3
"""Select focused CleanRL maintenance checks without running them.

The script maps touched files and capability keywords to candidate pytest,
docs, help, formatting, requirements, and warning items. It is intentionally
read-only: it prints commands and review notes but never executes them.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass
class Selection:
    pytest: list[str] = field(default_factory=list)
    help: list[str] = field(default_factory=list)
    docs: list[str] = field(default_factory=list)
    maintenance: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    review: list[str] = field(default_factory=list)

    def add(self, section: str, *items: str) -> None:
        bucket = getattr(self, section)
        for item in items:
            if item and item not in bucket:
                bucket.append(item)

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "pytest": self.pytest,
            "help": self.help,
            "docs": self.docs,
            "maintenance": self.maintenance,
            "warnings": self.warnings,
            "review": self.review,
        }


SCRIPT_RULES: dict[str, dict[str, object]] = {
    "cleanrl/ppo.py": {"tests": ["tests/test_classic_control.py"], "docs": ["docs/rl-algorithms/ppo.md"]},
    "cleanrl/dqn.py": {"tests": ["tests/test_classic_control_gymnasium.py"], "docs": ["docs/rl-algorithms/dqn.md"]},
    "cleanrl/c51.py": {"tests": ["tests/test_classic_control_gymnasium.py"], "docs": ["docs/rl-algorithms/c51.md"]},
    "cleanrl/dqn_jax.py": {
        "tests": ["tests/test_classic_control_jax_gymnasium.py"],
        "docs": ["docs/rl-algorithms/dqn.md"],
        "extras": ["jax"],
    },
    "cleanrl/c51_jax.py": {
        "tests": ["tests/test_classic_control_jax_gymnasium.py"],
        "docs": ["docs/rl-algorithms/c51.md"],
        "extras": ["jax"],
    },
    "cleanrl/ppo_atari.py": {
        "tests": ["tests/test_atari.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["atari"],
    },
    "cleanrl/ppo_atari_lstm.py": {
        "tests": ["tests/test_atari.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["atari"],
    },
    "cleanrl/dqn_atari.py": {
        "tests": ["tests/test_atari_gymnasium.py"],
        "docs": ["docs/rl-algorithms/dqn.md"],
        "extras": ["atari"],
    },
    "cleanrl/c51_atari.py": {
        "tests": ["tests/test_atari_gymnasium.py"],
        "docs": ["docs/rl-algorithms/c51.md"],
        "extras": ["atari"],
    },
    "cleanrl/rainbow_atari.py": {
        "tests": ["tests/test_atari_gymnasium.py"],
        "docs": ["docs/rl-algorithms/rainbow.md"],
        "extras": ["atari"],
    },
    "cleanrl/sac_atari.py": {
        "tests": ["tests/test_atari_gymnasium.py"],
        "docs": ["docs/rl-algorithms/sac.md"],
        "extras": ["atari"],
    },
    "cleanrl/qdagger_dqn_atari_impalacnn.py": {
        "tests": ["tests/test_atari_gymnasium.py"],
        "docs": ["docs/rl-algorithms/qdagger.md"],
        "extras": ["atari"],
    },
    "cleanrl/dqn_atari_jax.py": {
        "tests": ["tests/test_atari_jax_gymnasium.py"],
        "docs": ["docs/rl-algorithms/dqn.md"],
        "extras": ["atari", "jax"],
    },
    "cleanrl/c51_atari_jax.py": {
        "tests": ["tests/test_atari_jax_gymnasium.py"],
        "docs": ["docs/rl-algorithms/c51.md"],
        "extras": ["atari", "jax"],
    },
    "cleanrl/qdagger_dqn_atari_jax_impalacnn.py": {
        "tests": ["tests/test_atari_jax_gymnasium.py"],
        "docs": ["docs/rl-algorithms/qdagger.md"],
        "extras": ["atari", "jax"],
    },
    "cleanrl/ppo_atari_envpool.py": {
        "tests": ["tests/test_envpool.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["envpool"],
    },
    "cleanrl/ppo_rnd_envpool.py": {
        "tests": ["tests/test_envpool.py"],
        "docs": ["docs/rl-algorithms/ppo-rnd.md"],
        "extras": ["envpool"],
    },
    "cleanrl/ppo_atari_envpool_xla_jax.py": {
        "tests": ["tests/test_envpool.py", "tests/test_jax_compute_gae.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["envpool", "jax"],
    },
    "cleanrl/ppo_atari_envpool_xla_jax_scan.py": {
        "tests": ["tests/test_envpool.py", "tests/test_jax_compute_gae.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["envpool", "jax"],
    },
    "cleanrl/pqn_atari_envpool.py": {
        "tests": ["tests/test_envpool.py"],
        "docs": ["docs/rl-algorithms/pqn.md"],
        "extras": ["envpool"],
        "manual": ["uv run python cleanrl/pqn_atari_envpool.py --num-envs 8 --num-steps 32 --total-timesteps 256"],
    },
    "cleanrl/pqn_atari_envpool_lstm.py": {
        "tests": ["tests/test_envpool.py"],
        "docs": ["docs/rl-algorithms/pqn.md"],
        "extras": ["envpool"],
        "manual": ["uv run python cleanrl/pqn_atari_envpool_lstm.py --num-envs 8 --num-steps 32 --total-timesteps 256"],
    },
    "cleanrl/ppo_atari_multigpu.py": {
        "tests": ["tests/test_atari_multigpu.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["atari", "multigpu"],
    },
    "cleanrl/ppo_procgen.py": {
        "tests": ["tests/test_procgen.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["procgen"],
    },
    "cleanrl/ppg_procgen.py": {
        "tests": ["tests/test_procgen.py"],
        "docs": ["docs/rl-algorithms/ppg.md"],
        "extras": ["procgen"],
    },
    "cleanrl/ppo_pettingzoo_ma_atari.py": {
        "tests": ["tests/test_pettingzoo_ma_atari.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["pettingzoo", "atari"],
        "argparse": True,
    },
    "cleanrl/ddpg_continuous_action.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/ddpg.md"],
        "extras": ["mujoco"],
    },
    "cleanrl/ddpg_continuous_action_jax.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/ddpg.md"],
        "extras": ["mujoco", "jax"],
    },
    "cleanrl/td3_continuous_action.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/td3.md"],
        "extras": ["mujoco"],
    },
    "cleanrl/td3_continuous_action_jax.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/td3.md"],
        "extras": ["mujoco", "jax"],
    },
    "cleanrl/sac_continuous_action.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/sac.md"],
        "extras": ["mujoco"],
    },
    "cleanrl/ppo_continuous_action.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/ppo.md"],
        "extras": ["mujoco", "dm_control"],
    },
    "cleanrl/rpo_continuous_action.py": {
        "tests": ["tests/test_mujoco.py"],
        "docs": ["docs/rl-algorithms/rpo.md"],
        "extras": ["mujoco", "dm_control"],
    },
    "cleanrl/pqn.py": {"tests": [], "docs": ["docs/rl-algorithms/pqn.md"], "extras": ["jax"]},
    "cleanrl/ppo_continuous_action_isaacgym/ppo_continuous_action_isaacgym.py": {
        "tests": [],
        "docs": ["docs/rl-algorithms/ppo-isaacgymenvs.md"],
        "extras": ["isaacgym"],
    },
    "cleanrl/ppo_trxl/ppo_trxl.py": {
        "tests": [],
        "docs": ["docs/rl-algorithms/ppo-trxl.md"],
        "extras": ["memory_gym"],
    },
    "cleanrl/ppo_trxl/enjoy.py": {
        "tests": ["tests/test_enjoy.py"],
        "docs": ["docs/rl-algorithms/ppo-trxl.md"],
        "extras": ["memory_gym"],
    },
}

UTILITY_RULES: dict[str, dict[str, object]] = {
    "cleanrl_utils/benchmark.py": {
        "tests": [],
        "help": ["uv run python -m cleanrl_utils.benchmark --help"],
        "docs": ["docs/get-started/benchmark-utility.md"],
        "warnings": ["Benchmark execution can run long experiments, W&B tracking, Xvfb, or Slurm; keep routine checks to help/dry-run output unless approved."],
    },
    "cleanrl_utils/tuner.py": {"tests": ["tests/test_tuner.py"], "docs": ["docs/advanced/hyperparameter-tuning.md"], "extras": ["optuna"]},
    "tuner_example.py": {"tests": ["tests/test_tuner.py"], "docs": ["docs/advanced/hyperparameter-tuning.md"], "extras": ["optuna"]},
    "cleanrl_utils/submit_exp.py": {
        "tests": ["tests/test_utils.py"],
        "warnings": ["Cloud submission helpers can require Docker, AWS, and W&B credentials; do not run real submissions as routine validation."],
    },
    "cleanrl_utils/enjoy.py": {"tests": ["tests/test_enjoy.py"], "help": ["uv run python -m cleanrl_utils.enjoy --help"]},
}

EXTRA_WARNINGS = {
    "atari": "Atari checks require Atari extras and ROM/ALE compatibility; failures may be dependency or license/setup issues rather than code regressions.",
    "envpool": "EnvPool checks are platform-sensitive and generally Linux-oriented; avoid treating missing wheels as source failures.",
    "procgen": "Procgen checks require the Procgen optional extra and can fail before source code is reached if the backend is absent.",
    "mujoco": "MuJoCo checks require MuJoCo-compatible packages, rendering/display support, and can be sensitive to version pins.",
    "dm_control": "dm_control smoke paths require the dm_control extra in addition to MuJoCo-compatible packages.",
    "pettingzoo": "PettingZoo multi-agent Atari checks require both PettingZoo and Atari dependencies.",
    "jax": "JAX checks require the pinned JAX/JAXLIB stack; do not install GPU-specific JAX builds without an explicit environment decision.",
    "multigpu": "Multi-GPU checks use torchrun and can be hardware/platform-sensitive; ask before running broad distributed checks.",
    "optuna": "Optuna checks require the optuna extra and may create study artifacts; keep test runs tiny.",
    "isaacgym": "Isaac Gym validation is not routine: it can require proprietary/manual installation and narrow Python compatibility.",
    "memory_gym": "Memory Gym/TRXL has its own subproject dependencies and requirements export process; do not use the root uv-export hook for its requirements snapshot.",
}

REQUIREMENT_HOOKS = {
    "requirements/requirements.txt": "uv run pre-commit run \"uv-export requirements.txt\" --hook-stage manual",
    "requirements/requirements-atari.txt": "uv run pre-commit run \"uv-export requirements-atari.txt\" --hook-stage manual",
    "requirements/requirements-mujoco.txt": "uv run pre-commit run \"uv-export requirements-mujoco.txt\" --hook-stage manual",
    "requirements/requirements-dm_control.txt": "uv run pre-commit run \"uv-export requirements-dm_control.txt\" --hook-stage manual",
    "requirements/requirements-procgen.txt": "uv run pre-commit run \"uv-export requirements-procgen.txt\" --hook-stage manual",
    "requirements/requirements-envpool.txt": "uv run pre-commit run \"uv-export requirements-envpool.txt\" --hook-stage manual",
    "requirements/requirements-pettingzoo.txt": "uv run pre-commit run \"uv-export requirements-pettingzoo.txt\" --hook-stage manual",
    "requirements/requirements-jax.txt": "uv run pre-commit run \"uv-export requirements-jax.txt\" --hook-stage manual",
    "requirements/requirements-optuna.txt": "uv run pre-commit run \"uv-export requirements-optuna.txt\" --hook-stage manual",
    "requirements/requirements-docs.txt": "uv run pre-commit run \"uv-export requirements-docs.txt\" --hook-stage manual",
    "requirements/requirements-cloud.txt": "uv run pre-commit run \"uv-export requirements-cloud.txt\" --hook-stage manual",
}

KEYWORD_ALIASES = {
    "arg": "cli",
    "args": "cli",
    "argument": "cli",
    "arguments": "cli",
    "flag": "cli",
    "flags": "cli",
    "readme": "docs",
    "doc": "docs",
    "documentation": "docs",
    "dependency": "deps",
    "dependencies": "deps",
    "package": "deps",
    "packaging": "deps",
    "requirements": "deps",
    "format": "style",
    "lint": "style",
    "precommit": "style",
    "pre-commit": "style",
    "benchmark": "performance",
    "benchmarks": "performance",
    "rlops": "performance",
    "regression": "performance",
}


def normalize_path(path: str) -> str:
    normalized = str(PurePosixPath(path.replace("\\", "/")))
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def normalize_keywords(keywords: Iterable[str]) -> set[str]:
    result = set()
    for keyword in keywords:
        key = keyword.strip().lower().replace("_", "-")
        if not key:
            continue
        result.add(KEYWORD_ALIASES.get(key, key))
    return result


def command_for_tests(test_files: Iterable[str]) -> str:
    unique = []
    for test_file in test_files:
        if test_file not in unique:
            unique.append(test_file)
    return "uv run pytest " + " ".join(unique)


def add_rule(selection: Selection, path: str, rule: dict[str, object], keywords: set[str]) -> None:
    tests = list(rule.get("tests", []))
    docs = list(rule.get("docs", []))
    extras = list(rule.get("extras", []))
    manual = list(rule.get("manual", []))

    if tests:
        selection.add("pytest", command_for_tests(tests))
    elif path.startswith("cleanrl/") and path.endswith(".py"):
        selection.add("review", f"No direct focused pytest module is mapped for {path}; use a tiny manual smoke command only if its optional backend is available.")

    if path.endswith(".py") and path.startswith(("cleanrl/", "cleanrl_utils/")):
        if rule.get("argparse"):
            selection.add("help", f"uv run python {path} --help")
        elif path in SCRIPT_RULES or "cli" in keywords:
            selection.add("help", f"uv run python {path} --help")

    for help_command in list(rule.get("help", [])):
        selection.add("help", help_command)

    for docs_path in docs:
        selection.add("review", f"Review {docs_path} for usage, defaults, logged metrics, implementation details, and benchmark-result expectations.")

    for manual_command in manual:
        selection.add("review", f"No exact pytest coverage for this variant; consider this tiny smoke command if dependencies are installed: {manual_command}")

    for extra in extras:
        selection.add("warnings", EXTRA_WARNINGS[extra])

    for warning in list(rule.get("warnings", [])):
        selection.add("warnings", warning)


def select(paths: list[str], keywords: set[str]) -> Selection:
    selection = Selection()
    normalized_paths = [normalize_path(path) for path in paths]

    if normalized_paths:
        python_files = [path for path in normalized_paths if path.endswith(".py")]
        if python_files:
            selection.add("maintenance", "uv run pre-commit run --files " + " ".join(python_files))
        else:
            selection.add("maintenance", "uv run pre-commit run --files " + " ".join(normalized_paths))
    else:
        selection.add("review", "No paths were provided; pass touched files and optional --keywords to get focused checks.")

    docs_touched = False
    deps_touched = False
    cloud_touched = False
    tests_touched = []

    for path in normalized_paths:
        rule = SCRIPT_RULES.get(path) or UTILITY_RULES.get(path)
        if rule:
            add_rule(selection, path, rule, keywords)

        if path.startswith("tests/") and path.endswith(".py"):
            tests_touched.append(path)

        if path == "README.md" or path == "mkdocs.yml" or path.startswith("docs/"):
            docs_touched = True

        if path in {"pyproject.toml", "uv.lock", ".pre-commit-config.yaml"} or path.startswith("requirements/"):
            deps_touched = True

        if path.startswith("cloud/") or path.startswith("cleanrl_utils/docker") or "submit_exp" in path or "aws" in path.lower():
            cloud_touched = True

        if path.startswith("benchmark/") or "benchmark" in path:
            selection.add("warnings", "Benchmark scripts can launch long tracked experiments; keep routine validation to review/help unless execution is explicitly approved.")

        if path.startswith("cleanrl_utils/") and path.endswith(".py") and path not in UTILITY_RULES:
            selection.add("review", f"No exact utility test mapping for {path}; inspect adjacent utility tests or add a focused smoke check if behavior changed.")

        if path.startswith("requirements/") and path in REQUIREMENT_HOOKS:
            selection.add("maintenance", REQUIREMENT_HOOKS[path])

    if tests_touched:
        selection.add("pytest", command_for_tests(tests_touched))

    if docs_touched or "docs" in keywords:
        selection.add("docs", "uv run mkdocs build --strict")
        selection.add("warnings", "Docs checks require the docs optional extra; update mkdocs navigation and Markdown includes together.")

    if "cli" in keywords:
        selection.add("warnings", "CLI changes should include --help review and docs snippet updates; tyro derives flag names/help from Args dataclass fields and comments.")
        if not selection.help:
            selection.add("review", "CLI keyword was provided but no script path was mapped; add the touched CLI script path to get a concrete --help command.")

    if deps_touched or "deps" in keywords:
        selection.add("review", "If dependency metadata changed, regenerate only the affected requirements snapshots and inspect resolver diffs.")
        if "deps" in keywords and not any(item.startswith("uv run pre-commit run \"uv-export") for item in selection.maintenance):
            selection.add("review", "Dependency keyword was provided without a specific requirements file; choose the affected manual uv-export hook from the changed extra.")
        selection.add("warnings", "Root package metadata targets Python >=3.8,<3.11; do not broaden compatibility without a deliberate migration plan.")

    if "style" in keywords:
        selection.add("maintenance", "uv run pre-commit run --all-files")

    if "performance" in keywords:
        selection.add("warnings", "Performance-impacting changes require RLOps benchmark/regression evidence; smoke tests only prove commands do not crash.")
        selection.add("review", "Plan benchmark tags, baseline comparison, docs result-table updates, and W&B/report links before claiming no regression.")

    if cloud_touched or "cloud" in keywords:
        selection.add("warnings", "Cloud, Docker, AWS, Slurm, and W&B-tracked commands can incur cost or require credentials; do not run them without explicit approval.")
        selection.add("review", "Prefer fake-credential tests, help output, or dry-run review for cloud maintenance unless a safe execution environment is confirmed.")

    if any(path.startswith("cleanrl/") and path.endswith(".py") for path in normalized_paths):
        selection.add("review", "Preserve CleanRL's single-file style; avoid extracting shared abstractions solely to remove duplication.")

    return selection


def print_human(selection: Selection) -> None:
    headings = [
        ("Pytest", selection.pytest),
        ("Help", selection.help),
        ("Docs", selection.docs),
        ("Maintenance", selection.maintenance),
        ("Warnings", selection.warnings),
        ("Review", selection.review),
    ]
    print("CleanRL focused check suggestions (not executed):")
    for title, items in headings:
        if not items:
            continue
        print(f"\n{title}:")
        for item in items:
            print(f"  - {item}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Select focused CleanRL maintenance checks without running them.")
    parser.add_argument("paths", nargs="*", help="Touched repo-relative files, such as cleanrl/sac_continuous_action.py")
    parser.add_argument("--keywords", nargs="*", default=[], help="Capability hints such as cli docs deps style performance cloud")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON instead of human text")
    args = parser.parse_args()

    keywords = normalize_keywords(args.keywords)
    selection = select(args.paths, keywords)
    if args.json:
        print(json.dumps(selection.as_dict(), indent=2, sort_keys=True))
    else:
        print_human(selection)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
