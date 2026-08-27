#!/usr/bin/env python3
"""Initialize a paper-to-skills distillation directory."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_ITERATION_BUDGET = 10


def infer_distiller_skills_root() -> Path:
    """Infer the bundled Distiller skills root from this script location."""
    return Path(__file__).resolve().parents[2]


def default_run_root(workspace_root: Path, slug: str) -> Path:
    return workspace_root / slug


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "paper"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", required=True, help="Local paper path.")
    parser.add_argument("--slug", required=True, help="Short paper slug.")
    parser.add_argument("--repo", default="", help="Optional local repository path.")
    parser.add_argument(
        "--test-root",
        default="",
        help="Compatibility root for distillation logs. Defaults to <cwd>/<slug>.",
    )
    parser.add_argument(
        "--skills-root",
        default="",
        help="Root directory for extracted module skills. Defaults to <cwd>/<slug>/skills.",
    )
    parser.add_argument(
        "--generated-skills-root",
        default="",
        help="Exact output directory for this paper's generated module skills. Defaults to <skills-root>.",
    )
    parser.add_argument(
        "--distiller-skills-root",
        default=str(infer_distiller_skills_root()),
        help="Root directory for workflow skills.",
    )
    parser.add_argument(
        "--iteration-budget",
        type=int,
        default=DEFAULT_ITERATION_BUDGET,
        help="Maximum number of refinement cycles after the first recovery. Defaults to 10.",
    )
    parser.add_argument(
        "--recovery-mode",
        choices=["hard", "soft"],
        default="hard",
        help=(
            "Recovery acceptance mode. hard requires the full requested standard and cannot accept "
            "proxy/reduced recovery as success; soft may accept a validated reduced/proxy recovery."
        ),
    )
    parser.add_argument(
        "--run-config",
        default="",
        help="Optional path to a normalized run config JSON to copy into the distillation directory.",
    )
    parser.add_argument(
        "--attempt-dir",
        default="",
        help="Optional exact distillation artifact directory. Defaults to <run-root>/distillation.",
    )
    args = parser.parse_args(argv)
    if args.iteration_budget < 0:
        parser.error("--iteration-budget must be zero or greater")

    slug = slugify(args.slug)
    workspace_root = Path.cwd().resolve()
    run_root = default_run_root(workspace_root, slug)
    paper = Path(args.paper).expanduser().resolve()
    repo = Path(args.repo).expanduser().resolve() if args.repo else None
    test_root = Path(args.test_root).expanduser().resolve() if args.test_root else run_root
    skills_root = Path(args.skills_root).expanduser().resolve() if args.skills_root else run_root / "skills"
    paper_skill_root = Path(args.generated_skills_root).expanduser().resolve() if args.generated_skills_root else skills_root
    distiller_skills_root = Path(args.distiller_skills_root).expanduser().resolve()

    attempt_dir = Path(args.attempt_dir).expanduser().resolve() if args.attempt_dir else test_root / "distillation"
    paper_skill_root.mkdir(parents=True, exist_ok=True)
    for rel in [
        "modules",
        "generated_skills_validation",
        "environment/logs",
        "recovery/logs",
        "analysis",
        "reports/generated-skills",
        "reports/verification",
        "reports/final",
    ]:
        (attempt_dir / rel).mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": 1,
        "slug": slug,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(workspace_root),
        "run_root": str(run_root),
        "distillation_root": str(attempt_dir),
        "attempt_dir": str(attempt_dir),
        "paper": str(paper),
        "repo": str(repo) if repo else "",
        "skills_root": str(skills_root),
        "paper_skill_root": str(paper_skill_root),
        "generated_skills_root": str(paper_skill_root),
        "distiller_skills_root": str(distiller_skills_root),
        "reports_root": str(attempt_dir / "reports"),
        "iteration_budget": args.iteration_budget,
        "recovery_mode": args.recovery_mode,
        "stages": {
            "modularize": "pending",
            "module_to_skill": "pending",
            "prepare_environment": "pending",
            "recover": "pending",
            "analysis": "pending",
        },
    }
    (attempt_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    if args.run_config:
        run_config_path = Path(args.run_config).expanduser().resolve()
        try:
            run_config = json.loads(run_config_path.read_text(encoding="utf-8"))
        except Exception as exc:
            parser.error(f"--run-config must be a readable JSON file: {exc}")
        (attempt_dir / "run_config.normalized.json").write_text(
            json.dumps(run_config, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
