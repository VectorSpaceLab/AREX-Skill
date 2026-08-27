#!/usr/bin/env python3
"""Print Marqo local-service command plans without executing them."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path
from textwrap import dedent


@dataclass(frozen=True)
class Plan:
    name: str
    title: str
    safety: str
    commands: str
    notes: tuple[str, ...] = ()


PLANS: dict[str, Plan] = {
    "env": Plan(
        name="env",
        title="Environment and package checks",
        safety="read-only except optional uv environment creation if you choose to run uv sync",
        commands="""
# from repository root
test -f .env && set -a && . ./.env && set +a
python --version
which python
uv --version

# main API component; run only after choosing this environment
cd components/marqo
uv sync --group dev
. .venv/bin/activate
PYTHONPATH=./src python -c "import marqo; print('marqo import ok')"
""",
        notes=("Use Python 3.11 for service components.",),
    ),
    "vespa": Plan(
        name="vespa",
        title="Local Vespa plan",
        safety="service-mutating if executed: starts containers and deploys local Vespa app",
        commands="""
# from repository root, after explicit approval
cd components/marqo
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py full-start
curl -s http://localhost:19071/state/v1/health
curl -s http://localhost:8080/state/v1/health

# separated start/deploy variant
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py start
PYTHONPATH=./src python scripts/vespa_local/vespa_local.py deploy-config
""",
        notes=("Single-node ports: 8080 document/query, 19071 config, 2181 Zookeeper.",),
    ),
    "local-api": Plan(
        name="local-api",
        title="Local Marqo API plan",
        safety="service-mutating if executed: starts an API process that can create/delete indexes when tested",
        commands="""
# requires healthy Vespa first
cd components/marqo
export PYTHONPATH=./src
export MARQO_ENABLE_BATCH_APIS=true
export MARQO_MODE=COMBINED
export MARQO_LOG_LEVEL=debug
export MARQO_MODELS_TO_PRELOAD=[]
export VESPA_CONFIG_URL=http://localhost:19071
export VESPA_DOCUMENT_URL=http://localhost:8080
export VESPA_QUERY_URL=http://localhost:8080
export ZOOKEEPER_HOSTS=localhost:2181
uvicorn marqo.tensor_search.api:app --host 0.0.0.0 --port 8882 --reload

# health checks from another terminal
curl -s http://localhost:8882/
curl -s http://localhost:8882/health
""",
        notes=("Terminate the API process after API tests finish.",),
    ),
    "compose-all": Plan(
        name="compose-all",
        title="Full compose stack plan",
        safety="service-mutating if executed: builds/starts Triton, API, MMC, and MIOC services",
        commands="""
# from repository root; inspect before up
test -f .env && set -a && . ./.env && set +a
docker compose --profile cpu -f compose.yaml config

# after review and explicit approval
docker compose --profile cpu -f compose.yaml up --build
""",
        notes=("Use --profile gpu only after NVIDIA Docker support is verified.",),
    ),
    "inference": Plan(
        name="inference",
        title="Inference-only compose plan",
        safety="service-mutating if executed: builds/starts Triton, MMC, and MIOC",
        commands="""
# from repository root; inspect before up
test -f .env && set -a && . ./.env && set +a
docker compose --profile cpu -f compose-inference.yaml config

# after review and explicit approval
docker compose --profile cpu -f compose-inference.yaml up --build

# health checks
curl -s http://localhost:8000/v2/health/ready
curl -s http://localhost:8883/v1/healthz
curl -s http://localhost:8884/healthz
""",
        notes=("MIOC exposes /vectorise on 8884; model downloads may be expensive.",),
    ),
    "triton": Plan(
        name="triton",
        title="Triton-only compose plan",
        safety="service-mutating if executed: starts Triton container",
        commands="""
# from repository root; inspect before up
test -f .env && set -a && . ./.env && set +a
docker compose --profile cpu -f compose-triton.yaml config

# after review and explicit approval
docker compose --profile cpu -f compose-triton.yaml up
curl -s http://localhost:8000/v2/health/ready
""",
        notes=("Triton uses ports 8000 HTTP, 8001 gRPC, and 8002 metrics.",),
    ),
    "maven": Plan(
        name="maven",
        title="Vespa custom searcher build plan",
        safety="build-only if executed; redeploy Vespa separately after review",
        commands="""
cd components/marqo/vespa
java -version
mvn -version
mvn clean package
""",
        notes=("Required after HybridSearcher.java changes; redeploy Vespa app before service validation.",),
    ),
    "api-tests": Plan(
        name="api-tests",
        title="API test lifecycle plan",
        safety="service-mutating if executed: API tests create/delete indexes and require a local API server",
        commands="""
# terminal 1: start Vespa and Marqo API first; see vespa and local-api plans

# terminal 2: run selected API tests only
cd components/marqo
PYTHONPATH=./tests/api_tests/v1/tests/api_tests pytest tests/api_tests/v1/tests/api_tests/test_health.py -q
PYTHONPATH=./tests/api_tests/v1/tests/api_tests pytest tests/api_tests/v1/tests/api_tests/test_create_index.py -q
""",
        notes=("Never point API tests at production or shared services.",),
    ),
    "shutdown": Plan(
        name="shutdown",
        title="Shutdown commands to review",
        safety="destructive if executed: stops/removes containers",
        commands="""
# review ownership of containers before executing any shutdown command
docker compose -f compose.yaml down
docker compose -f compose-inference.yaml down
docker compose -f compose-model-management.yaml down
docker compose -f compose-triton.yaml down

docker rm -f marqo vespa
""",
        notes=("Do not stop containers that another task or user is using.",),
    ),
}

ORDER = ["env", "vespa", "local-api", "compose-all", "inference", "triton", "maven", "api-tests", "shutdown"]


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "components" / "marqo").is_dir() and (path / "compose.yaml").is_file():
            return path
    return None


def render_plan(plan: Plan, markdown: bool) -> str:
    commands = dedent(plan.commands).strip()
    if markdown:
        note_lines = "\n".join(f"- {note}" for note in plan.notes)
        return f"## {plan.title}\n\nSafety: {plan.safety}\n\n```bash\n{commands}\n```\n" + (f"\nNotes:\n{note_lines}\n" if note_lines else "")
    lines = [f"# {plan.title}", f"# Safety: {plan.safety}"]
    lines.extend(f"# Note: {note}" for note in plan.notes)
    lines.append(commands)
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    choices = ["all", *ORDER]
    parser.add_argument("--plan", choices=choices, default="all", help="Which command plan to print.")
    parser.add_argument("--markdown", action="store_true", help="Render as Markdown instead of shell comments.")
    parser.add_argument("--no-root-check", action="store_true", help="Do not warn when the repository root is not detected.")
    args = parser.parse_args()

    if not args.no_root_check:
        root = find_repo_root(Path.cwd())
        if root is None:
            print("# Warning: repository root was not detected from the current directory. Commands remain relative plans.")
        else:
            rel = os.path.relpath(root, Path.cwd())
            print(f"# Detected repository root: {rel}")

    print("# DRY RUN: commands are printed only; this script does not execute them.")
    selected = ORDER if args.plan == "all" else [args.plan]
    blocks = [render_plan(PLANS[name], args.markdown) for name in selected]
    print("\n\n".join(blocks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
