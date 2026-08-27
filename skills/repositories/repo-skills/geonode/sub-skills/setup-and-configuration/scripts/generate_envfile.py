#!/usr/bin/env python3
"""Render a GeoNode environment template without repository-relative behavior.

The generator writes secrets to the requested output file but never prints
secret values. It refuses to overwrite an existing output unless --force is
provided. The template and output paths are explicit so this script is safe to
bundle and invoke from another project.
"""
from __future__ import annotations

import argparse
import json
import secrets
import string
import sys
from pathlib import Path
from typing import Any

PLACEHOLDER = r"(?<!\$)\{([A-Za-z_][A-Za-z0-9_]*)\}"


def _secret(length: int = 50) -> str:
    # Keep generated values safe in unquoted dotenv assignments.
    alphabet = string.ascii_letters + string.digits + "-_.~"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _simple(length: int = 15) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _load_config(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read configuration file: {exc.__class__.__name__}") from exc
    if not isinstance(value, dict):
        raise ValueError("configuration file must contain a JSON object")
    return value


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in {"true", "1", "yes", "on"}:
        return True
    if isinstance(value, str) and value.lower() in {"false", "0", "no", "off"}:
        return False
    raise ValueError("https must be a boolean")


def render(args: argparse.Namespace) -> tuple[str, int]:
    sample = Path(args.sample_file)
    output = Path(args.output)
    if not sample.is_file():
        raise FileNotFoundError("sample file does not exist")
    if output.exists() and not args.force:
        raise FileExistsError("output exists; pass --force to replace it")
    if not output.parent.is_dir():
        raise FileNotFoundError("output parent directory does not exist")

    config = _load_config(Path(args.config) if args.config else None)
    https = _bool(config.get("https", args.https))
    email = config.get("email", args.email)
    if https and not email:
        raise ValueError("--email is required when --https is enabled")

    hostname = str(config.get("hostname", args.hostname))
    env_type = str(config.get("env_type", args.env_type))
    scheme = "https" if https else "http"
    values: dict[str, Any] = {
        "hostname": hostname,
        "env_type": env_type,
        "email": email or "",
        "https": https,
        "http_host": "" if https else hostname,
        "https_host": hostname if https else "",
        "public_port": "443" if https else "80",
        "siteurl": f"{scheme}://{hostname}",
        "letsencrypt_mode": ("disabled" if not https else "staging" if env_type == "test" else "production"),
        "debug": env_type not in {"prod", "test"},
    }

    option_names = {
        "geonodepwd": "geonodepwd",
        "geoserverpwd": "geoserverpwd",
        "pgpwd": "pgpwd",
        "dbpwd": "dbpwd",
        "geodbpwd": "geodbpwd",
        "clientid": "clientid",
        "clientsecret": "clientsecret",
        "secret_key": "secret_key",
    }
    for argument, key in option_names.items():
        supplied = config.get(key, getattr(args, argument))
        if supplied is None or supplied == "":
            supplied = _secret() if key in {"secret_key", "clientsecret"} else _simple()
        values[key] = supplied

    # Preserve explicit template/config keys, but fail closed on unknown tokens.
    values.update({key: value for key, value in config.items() if key not in {"https", "hostname", "env_type"}})
    text = sample.read_text(encoding="utf-8")
    import re

    tokens = sorted(set(re.findall(PLACEHOLDER, text)))
    unknown = [token for token in tokens if token not in values]
    if unknown:
        raise ValueError("template has unsupported placeholders: " + ", ".join(unknown))
    for key, value in values.items():
        if isinstance(value, (dict, list, tuple)):
            value = str(value)
        if "\n" in str(value) or "\r" in str(value):
            raise ValueError(f"value for {key} contains a newline")
        values[key] = value
    text, count = re.subn(PLACEHOLDER, lambda match: str(values[match.group(1)]), text)
    return text, count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a GeoNode environment template to an explicit output path without logging secrets.",
        allow_abbrev=False,
    )
    parser.add_argument("--sample-file", required=True, help="template file containing {placeholders}")
    parser.add_argument("--output", required=True, help="destination environment file")
    parser.add_argument("--config", help="optional JSON object with template values")
    parser.add_argument("--hostname", default="localhost", help="public hostname (default: localhost)")
    parser.add_argument("--env-type", choices=("prod", "test", "dev"), default="dev")
    parser.add_argument("--https", action="store_true", help="derive HTTPS host/ports and site URL")
    parser.add_argument("--email", help="administrator/certificate email; required for HTTPS")
    parser.add_argument("--geonodepwd", help="GeoNode admin password")
    parser.add_argument("--geoserverpwd", help="GeoServer admin password")
    parser.add_argument("--pgpwd", help="PostgreSQL admin password")
    parser.add_argument("--dbpwd", help="GeoNode database password")
    parser.add_argument("--geodbpwd", help="GeoNode datastore password")
    parser.add_argument("--clientid", help="GeoServer OAuth2 client id")
    parser.add_argument("--clientsecret", help="GeoServer OAuth2 client secret")
    parser.add_argument("--secret-key", dest="secret_key", help="Django SECRET_KEY")
    parser.add_argument("--no-input", action="store_true", help="accepted for automation; never prompts")
    parser.add_argument("--force", action="store_true", help="replace an existing output file")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        text, replacements = render(args)
        output = Path(args.output)
        output.write_text(text, encoding="utf-8")
        try:
            output.chmod(0o600)
        except OSError:
            pass
    except (FileNotFoundError, FileExistsError, ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {args.output} ({replacements} placeholders rendered)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
