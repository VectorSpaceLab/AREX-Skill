#!/usr/bin/env python3
"""Print a CVAT serverless deployment checklist and command shape.

This helper does not run Docker or Nuclio. It exists so future agents can prepare a
reviewable command for an operator without accidentally building images or deploying
functions.
"""

from __future__ import annotations

import argparse
import shlex


def q(parts: list[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("function_dir", help="function directory to deploy, e.g. serverless/.../<model>/nuclio")
    parser.add_argument("--gpu", action="store_true", help="use function-gpu.yaml instead of function.yaml")
    parser.add_argument("--project", default="cvat")
    parser.add_argument("--platform", default="local")
    parser.add_argument("--network", default="cvat_cvat")
    args = parser.parse_args()

    yaml_name = "function-gpu.yaml" if args.gpu else "function.yaml"
    print("Checklist before running:")
    print("- Docker daemon and nuctl are installed and usable.")
    print("- CVAT serverless component is enabled and CVAT containers are running.")
    print(f"- {yaml_name} exists in the chosen function directory.")
    if args.gpu:
        print("- NVIDIA driver, Docker GPU runtime, and sufficient VRAM are available.")
    print("- The function labels/model type match the CVAT task or UI tool.")
    print()
    print("Command shape:")
    print(q(["nuctl", "create", "project", args.project, "--platform", args.platform]))
    print(q([
        "nuctl", "deploy",
        "--project-name", args.project,
        "--path", args.function_dir,
        "--file", f"{args.function_dir.rstrip('/')}/{yaml_name}",
        "--platform", args.platform,
        "--env", "CVAT_FUNCTIONS_REDIS_HOST=cvat_redis_ondisk",
        "--env", "CVAT_FUNCTIONS_REDIS_PORT=6666",
        "--platform-config", '{"attributes": {"network": "' + args.network + '"}}',
    ]))
    print(q(["nuctl", "get", "function", "--platform", args.platform]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
