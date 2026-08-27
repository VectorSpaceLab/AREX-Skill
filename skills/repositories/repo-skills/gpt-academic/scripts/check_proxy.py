#!/usr/bin/env python3
"""Check GPT Academic proxy configuration without exposing secrets."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def setup_repo(repo_root: str | None) -> Path:
    root = Path(repo_root or os.getcwd()).resolve()
    if (root / "toolbox.py").exists():
        sys.path.insert(0, str(root))
        os.chdir(root)
    return root


def sanitize_proxy(value):
    if not value:
        return None
    value = str(value)
    if "@" in value and "://" in value:
        scheme, rest = value.split("://", 1)
        return scheme + "://***@" + rest.split("@", 1)[1]
    return value


def load_proxy_config():
    try:
        from toolbox import get_conf
        proxies, use_proxy = get_conf("proxies", "USE_PROXY")
        return {"USE_PROXY": use_proxy, "proxies": proxies}
    except Exception as exc:  # noqa: BLE001
        return {"USE_PROXY": None, "proxies": None, "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", help="GPT Academic checkout root; defaults to current working directory")
    parser.add_argument("--no-network", action="store_true", help="only print sanitized config")
    parser.add_argument("--timeout", type=float, default=4.0, help="request timeout seconds")
    args = parser.parse_args()
    setup_repo(args.repo_root)
    cfg = load_proxy_config()
    proxies = cfg.get("proxies") if isinstance(cfg.get("proxies"), dict) else {}
    sanitized = {"USE_PROXY": cfg.get("USE_PROXY"), "http": sanitize_proxy(proxies.get("http")), "https": sanitize_proxy(proxies.get("https"))}
    if "error" in cfg:
        sanitized["config_error"] = cfg["error"]
    result = {"config": sanitized, "network_check": "skipped"}
    if not args.no_network:
        try:
            import requests
            response = requests.get("https://ipapi.co/json/", proxies=cfg.get("proxies"), timeout=args.timeout)
            data = response.json()
            result["network_check"] = {"ok": response.ok, "status_code": response.status_code, "country_name": data.get("country_name"), "ip_present": bool(data.get("ip")), "error": data.get("error")}
        except Exception as exc:  # noqa: BLE001
            result["network_check"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
