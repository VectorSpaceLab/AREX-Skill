#!/usr/bin/env python3
"""Read-only AutoGPT Platform frontend layout and tool preflight."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

REQUIRED_FILES = (
    "package.json",
    "orval.config.ts",
    "src/app/api/openapi.json",
    "src/app/api/mutators/custom-mutator.ts",
    "src/mocks/mock-server.ts",
    "src/tests/integrations/test-utils.tsx",
    "playwright.config.ts",
)
REQUIRED_DIRS = (
    "src/app/(platform)",
    "src/app/api",
    "src/components/atoms",
    "src/components/molecules",
    "src/mocks",
    "src/tests/integrations",
    "src/playwright",
)
TOOLS = ("node", "corepack", "pnpm")
PLAYWRIGHT_SPECS = (
    "auth-happy-path.spec.ts",
    "builder-happy-path.spec.ts",
    "library-happy-path.spec.ts",
    "marketplace-happy-path.spec.ts",
    "copilot-happy-path.spec.ts",
)


def version(command: str) -> str | None:
    executable = shutil.which(command)
    if executable is None:
        return None
    try:
        result = subprocess.run(
            [command, "--version"], check=False, capture_output=True, text=True, timeout=5
        )
    except (OSError, subprocess.TimeoutExpired):
        return executable
    lines = (result.stdout or result.stderr).strip().splitlines()
    return lines[0] if lines else executable


def package_summary(package_json: Path) -> dict[str, Any]:
    if not package_json.is_file():
        return {}
    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.get("scripts", {})
    return {
        "name": data.get("name"),
        "version": data.get("version"),
        "node_engine": data.get("engines", {}).get("node"),
        "package_manager": data.get("packageManager"),
        "scripts_present": {
            key: key in scripts
            for key in ("dev", "build", "lint", "format", "types", "test", "test:unit", "generate:api")
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    frontend = repo / "autogpt_platform" / "frontend"
    files = {path: (frontend / path).is_file() for path in REQUIRED_FILES}
    dirs = {path: (frontend / path).is_dir() for path in REQUIRED_DIRS}
    specs = {name: (frontend / "src" / "playwright" / name).is_file() for name in PLAYWRIGHT_SPECS}
    result: dict[str, Any] = {
        "frontend_root": str(frontend),
        "files": files,
        "directories": dirs,
        "playwright_specs": specs,
        "tools": {tool: version(tool) for tool in TOOLS},
        "package": package_summary(frontend / "package.json"),
        "generated_api_present": (frontend / "src" / "app" / "api" / "__generated__").is_dir(),
    }
    ready = frontend.is_dir() and all(files.values()) and all(dirs.values()) and all(specs.values())
    if args.as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Frontend root: {frontend}")
        print(f"Layout ready: {'yes' if ready else 'no'}")
        print(f"Generated API present: {'yes' if result['generated_api_present'] else 'no'}")
        print("Tools:")
        for tool, value in result["tools"].items():
            print(f"  {tool}: {value or 'not found'}")
        package = result["package"]
        if package:
            print(f"Package: {package.get('name')} {package.get('version')}")
            print(f"Node engine: {package.get('node_engine')}")
            print(f"Package manager: {package.get('package_manager')}")
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
