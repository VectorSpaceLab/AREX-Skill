#!/usr/bin/env python3
"""Build, verify, and release the standalone DisCo npm package.

The publishable package is rooted at cli/ and is named
@auto-ml-skills/disco. Its Pi agent, AI, and TUI dependencies are normal npm
dependencies rather than sibling packages published by this repository.

The script reads environment variables from scripts/dev/.env by default
without executing it as shell code. It defaults to npm publish --dry-run; pass
--publish to perform the actual release.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


EXPECTED_PACKAGE_NAME = "@auto-ml-skills/disco"


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_dotenv(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    env: dict[str, str] = {}
    key_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    for lineno, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError as exc:
            fail(f"{path}:{lineno}: cannot parse .env line: {exc}")

        if parts and parts[0] == "export":
            parts = parts[1:]

        if len(parts) != 1 or "=" not in parts[0]:
            fail(f"{path}:{lineno}: expected KEY=VALUE syntax")

        key, value = parts[0].split("=", 1)
        if not key_pattern.match(key):
            fail(f"{path}:{lineno}: invalid environment variable name: {key}")
        env[key] = value

    return env


def merged_env(dotenv_path: Path) -> dict[str, str]:
    dotenv = load_dotenv(dotenv_path)
    env = dict(os.environ)
    for key, value in dotenv.items():
        env.setdefault(key, value)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"failed to read {path}: {exc}")


def package_info(package_dir: Path) -> dict[str, str | Path]:
    package_json = package_dir / "package.json"
    if not package_json.exists():
        fail(f"expected standalone DisCo package at {package_dir}")

    data = read_json(package_json)
    name = str(data.get("name") or "")
    version = str(data.get("version") or "")
    if name != EXPECTED_PACKAGE_NAME:
        fail(f"{package_json} has package name {name!r}; expected {EXPECTED_PACKAGE_NAME!r}")
    if not version:
        fail(f"{package_json} must contain a version")
    if data.get("private") is True:
        fail(f"{package_json} is marked private")
    return {"name": name, "version": version, "dir": package_dir}


def format_cmd(args: list[str]) -> str:
    return " ".join(shlex.quote(arg) for arg in args)


def run(args: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    print(f"==> {format_cmd(args)}")
    subprocess.run(args, cwd=cwd, env=env, check=True)


def run_capture(args: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)


def validate_publish_artifacts(package_dir: Path) -> None:
    required = [
        package_dir / "dist" / "cli.js",
        package_dir / "dist" / "index.js",
        package_dir / "npm-shrinkwrap.json",
    ]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        fail("missing publish artifacts; run npm run prepublishOnly first: " + ", ".join(missing))


def auth_key_for_registry(registry: str) -> str:
    parsed = urlparse(registry if "://" in registry else f"https://{registry}")
    if not parsed.netloc:
        fail(f"invalid npm registry URL: {registry}")
    path = parsed.path.rstrip("/")
    if path:
        return f"//{parsed.netloc}{path}/:_authToken"
    return f"//{parsed.netloc}/:_authToken"


def write_temp_npmrc(registry: str, env: dict[str, str]) -> Path | None:
    token = env.get("NODE_AUTH_TOKEN") or env.get("NPM_TOKEN")
    if not token:
        return None

    env["NODE_AUTH_TOKEN"] = token
    fd, path_text = tempfile.mkstemp(prefix="disco-npmrc-", text=True)
    path = Path(path_text)
    os.close(fd)
    path.chmod(0o600)
    path.write_text(
        "\n".join(
            [
                f"registry={registry}",
                f"{auth_key_for_registry(registry)}=${{NODE_AUTH_TOKEN}}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    env["NPM_CONFIG_USERCONFIG"] = str(path)
    return path


def package_exists(package_name: str, version: str, *, cwd: Path, env: dict[str, str], registry: str) -> bool:
    spec = f"{package_name}@{version}"
    proc = run_capture(["npm", "view", spec, "version", "--registry", registry], cwd=cwd, env=env)
    if proc.returncode == 0:
        return True

    output = f"{proc.stdout}\n{proc.stderr}"
    if "E404" in output or "404 Not Found" in output or "is not in this registry" in output:
        return False

    print(output.strip(), file=sys.stderr)
    fail(f"could not check whether {spec} already exists on npm")


def confirm_publish(package: dict[str, str | Path], tag: str, registry: str) -> None:
    print()
    print("The following package will be published:")
    print(f"  - {package['name']}@{package['version']}")
    print(f"Registry: {registry}")
    print(f"Tag: {tag}")
    print()
    answer = input("Type 'publish' to continue: ").strip()
    if answer != "publish":
        fail("release cancelled")


def main(argv: list[str] | None = None) -> int:
    root = repo_root()
    package_dir = root / "cli"

    parser = argparse.ArgumentParser(description="Build, verify, and publish the standalone DisCo npm package.")
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Perform a real npm publish. Without this flag, npm publish --dry-run is used.",
    )
    parser.add_argument("--yes", action="store_true", help="Skip the interactive publish confirmation.")
    parser.add_argument(
        "--env-file",
        default=str(root / "scripts" / "dev" / ".env"),
        help="Path to the .env file to read. Defaults to scripts/dev/.env.",
    )
    parser.add_argument("--registry", default="", help="npm registry URL. Defaults to NPM_CONFIG_REGISTRY, NPM_REGISTRY, or npmjs.")
    parser.add_argument("--tag", default="", help="npm dist-tag. Defaults to DISCO_NPM_TAG, NPM_TAG, or latest.")
    parser.add_argument("--access", default="", help="npm package access. Defaults to NPM_ACCESS or public.")
    parser.add_argument("--otp", default="", help="npm two-factor OTP. Defaults to NPM_CONFIG_OTP or NPM_OTP.")
    parser.add_argument("--skip-install", action="store_true", help="Skip npm ci --ignore-scripts in cli/.")
    parser.add_argument("--skip-verify", action="store_true", help="Skip npm run prepublishOnly in cli/ and use existing dist artifacts.")
    parser.add_argument(
        "--fail-if-exists",
        action="store_true",
        help="Fail instead of skipping when this package version already exists on npm.",
    )
    args = parser.parse_args(argv)

    package = package_info(package_dir)
    env = merged_env(Path(args.env_file).expanduser().resolve())
    registry = args.registry or env.get("NPM_CONFIG_REGISTRY") or env.get("NPM_REGISTRY") or "https://registry.npmjs.org/"
    tag = args.tag or env.get("DISCO_NPM_TAG") or env.get("NPM_TAG") or "latest"
    access = args.access or env.get("NPM_ACCESS") or "public"
    otp = args.otp or env.get("NPM_CONFIG_OTP") or env.get("NPM_OTP") or ""
    if otp:
        env["NPM_CONFIG_OTP"] = otp

    print("Release mode:", "publish" if args.publish else "dry-run")
    print("Release package:", f"{package['name']}@{package['version']}")
    print("Env file:", args.env_file)
    print("Package root:", package_dir)
    print("Registry:", registry)
    print("Tag:", tag)
    print("Access:", access)

    npmrc_path = write_temp_npmrc(registry, env)
    if npmrc_path:
        print("npm auth: using token from .env/environment via a temporary npmrc")
    else:
        print("npm auth: no NPM_TOKEN or NODE_AUTH_TOKEN found; using existing npm login if available")

    try:
        if not args.skip_install:
            run(["npm", "ci", "--ignore-scripts"], cwd=package_dir, env=env)
        if not args.skip_verify:
            run(["npm", "run", "prepublishOnly"], cwd=package_dir, env=env)

        validate_publish_artifacts(package_dir)

        if args.publish:
            name = str(package["name"])
            version = str(package["version"])
            exists = package_exists(name, version, cwd=package_dir, env=env, registry=registry)
            if exists and args.fail_if_exists:
                fail(f"{name}@{version} already exists on npm")
            if exists:
                print(f"==> Nothing to publish; {name}@{version} already exists on npm")
                return 0
            if not args.yes:
                confirm_publish(package, tag, registry)

        command = [
            "npm",
            "publish",
            "--access",
            access,
            "--tag",
            tag,
            "--registry",
            registry,
            "--ignore-scripts",
        ]
        if not args.publish:
            command.append("--dry-run")
        run(command, cwd=package_dir, env=env)

        print("==> Release script completed")
        return 0
    finally:
        if npmrc_path and npmrc_path.exists():
            npmrc_path.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
