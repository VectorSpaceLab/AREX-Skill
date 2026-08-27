#!/usr/bin/env python3
"""Update a service image version in .env and charts/core/values.yaml.

Safe by default: the helper prints the planned edits and only writes files when
--apply is supplied.

Examples:
  python scripts/update-service-version.py --repo-root /path/to/instill-core --service model --version be9e861
  python scripts/update-service-version.py --repo-root /path/to/instill-core --service model --version be9e861 --apply
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ServiceSpec:
    env_var: str
    repo_name: str
    helm_key: Optional[str]


SERVICE_MAP: dict[str, ServiceSpec] = {
    "api-gateway": ServiceSpec("API_GATEWAY_VERSION", "api-gateway", "apiGateway"),
    "mgmt": ServiceSpec("MGMT_BACKEND_VERSION", "mgmt-backend", "mgmtBackend"),
    "pipeline": ServiceSpec("PIPELINE_BACKEND_VERSION", "pipeline-backend", "pipelineBackend"),
    "artifact": ServiceSpec("ARTIFACT_BACKEND_VERSION", "artifact-backend", "artifactBackend"),
    "model": ServiceSpec("MODEL_BACKEND_VERSION", "model-backend", "modelBackend"),
    "console": ServiceSpec("CONSOLE_VERSION", "console", "console"),
    "ray": ServiceSpec("RAY_VERSION", "ray", None),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, help="Path to the Instill Core checkout")
    parser.add_argument("--service", required=True, choices=sorted(SERVICE_MAP), help="Service key to update")
    parser.add_argument("--version", required=True, help="New image tag or release version")
    parser.add_argument("--apply", action="store_true", help="Write the changes back to disk")
    return parser.parse_args()


def update_env_text(text: str, env_var: str, new_version: str) -> tuple[str, bool]:
    pattern = re.compile(rf"^({re.escape(env_var)}=).*$", re.MULTILINE)
    if not pattern.search(text):
        raise ValueError(f"{env_var} not found in .env")
    new_text = pattern.sub(lambda match: f"{match.group(1)}{new_version}", text, count=1)
    return new_text, new_text != text


def update_chart_text(text: str, repo_name: str, new_version: str) -> tuple[str, bool, bool]:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if line.strip() == f"repository: instill/{repo_name}":
            for j in range(idx + 1, min(idx + 4, len(lines))):
                if re.match(r"^\s+tag:\s*", lines[j]):
                    prefix = re.match(r"^(\s+tag:\s*).*$", lines[j]).group(1)
                    lines[j] = f'{prefix}"{new_version}"'
                    return "\n".join(lines) + "\n", True, True
            return text, False, True
    return text, False, False


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    env_path = repo_root / ".env"
    chart_path = repo_root / "charts/core/values.yaml"
    spec = SERVICE_MAP[args.service]

    env_text = env_path.read_text(encoding="utf-8")
    updated_env, env_changed = update_env_text(env_text, spec.env_var, args.version)

    chart_changed = False
    chart_found = False
    updated_chart = chart_path.read_text(encoding="utf-8")
    if spec.helm_key is not None:
        updated_chart, chart_changed, chart_found = update_chart_text(updated_chart, spec.repo_name, args.version)

    print(f"Service: {args.service}")
    print(f"  .env: {spec.env_var} -> {args.version} {'(will update)' if env_changed else '(already current)'}")
    if spec.helm_key is None:
        print("  chart: no current Helm image tag is present for this service; only .env is updated")
    else:
        if chart_found:
            print(f"  chart: charts/core/values.yaml repository instill/{spec.repo_name} -> tag {args.version} {'(will update)' if chart_changed else '(already current)'}")
        else:
            print(f"  chart: repository instill/{spec.repo_name} not found in charts/core/values.yaml")

    if not args.apply:
        print("\nDry run only. Re-run with --apply to write the changes.")
        return 0

    if spec.helm_key is not None and not chart_found:
        raise SystemExit(f"chart repository block for {spec.repo_name} was not found; no files were written")

    env_path.write_text(updated_env, encoding="utf-8")
    if spec.helm_key is not None and chart_found:
        chart_path.write_text(updated_chart, encoding="utf-8")

    print("\nUpdate applied successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
