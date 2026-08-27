#!/usr/bin/env python3
"""Build reviewable CVAT Docker Compose command lines without executing them."""

from __future__ import annotations

import argparse
import shlex


def q(parts: list[str]) -> str:
    return " ".join(shlex.quote(p) for p in parts if p)


def compose_parts(files: list[str]) -> list[str]:
    parts = ["docker", "compose"]
    for file in files:
        parts += ["-f", file]
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("up", "down", "ps", "logs", "superuser"))
    parser.add_argument("--dev", action="store_true", help="include docker-compose.dev.yml")
    parser.add_argument("--serverless", action="store_true", help="include serverless compose overlay")
    parser.add_argument("--external-db", action="store_true", help="include external DB overlay")
    parser.add_argument("--https", action="store_true", help="include HTTPS overlay")
    parser.add_argument("--build", action="store_true", help="add --build to up")
    parser.add_argument("--detach", action="store_true", default=True, help="add -d to up (default true)")
    parser.add_argument("--no-detach", dest="detach", action="store_false")
    parser.add_argument("--service", help="service name for logs")
    parser.add_argument("--cvat-host", help="emit an export line for CVAT_HOST")
    parser.add_argument("--cvat-version", help="emit a CVAT_VERSION=value prefix")
    args = parser.parse_args()

    files = ["docker-compose.yml"]
    if args.dev:
        files.append("docker-compose.dev.yml")
    if args.external_db:
        files.append("docker-compose.external_db.yml")
    if args.https:
        files.append("docker-compose.https.yml")
    if args.serverless:
        files.append("components/serverless/docker-compose.serverless.yml")

    if args.cvat_host:
        print(q(["export", f"CVAT_HOST={args.cvat_host}"]))

    env_prefix = [f"CVAT_VERSION={args.cvat_version}"] if args.cvat_version else []

    if args.action == "up":
        cmd = env_prefix + compose_parts(files) + ["up"]
        if args.detach:
            cmd.append("-d")
        if args.build:
            cmd.append("--build")
    elif args.action == "down":
        cmd = compose_parts(files) + ["down"]
        print("# Warning: add -v only after explicit approval to delete volumes/data.")
    elif args.action == "ps":
        cmd = compose_parts(files) + ["ps"]
    elif args.action == "logs":
        cmd = compose_parts(files) + ["logs"]
        if args.service:
            cmd.append(args.service)
    else:
        cmd = ["docker", "exec", "-it", "cvat_server", "bash", "-ic", "python3 ~/manage.py createsuperuser"]

    print(q(cmd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
