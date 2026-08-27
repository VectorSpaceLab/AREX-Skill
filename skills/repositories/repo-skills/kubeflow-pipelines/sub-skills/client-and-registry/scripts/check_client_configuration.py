#!/usr/bin/env python3
"""Safely inspect Kubeflow Pipelines client configuration.

By default this helper performs no network calls and does not instantiate
``kfp.Client``. It reports which connection inputs are present, highlights common
misconfigurations, and redacts secret values and local filesystem paths.

Use ``--probe-healthz`` only when a user explicitly asks to probe a live KFP API
endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

CLIENT_ENDPOINT_ENV = "KF_PIPELINES_ENDPOINT"
CLIENT_UI_ENV = "KF_PIPELINES_UI_ENDPOINT"
CLI_ENDPOINT_ENV = "KFP_ENDPOINT"
CLI_NAMESPACE_ENV = "KFP_NAMESPACE"
CLI_TOKEN_ENV = "KFP_EXISTING_TOKEN"
CLI_IAP_ENV = "KFP_IAP_CLIENT_ID"
CLI_OTHER_CLIENT_ID_ENV = "KFP_OTHER_CLIENT_ID"
CLI_OTHER_CLIENT_SECRET_ENV = "KFP_OTHER_CLIENT_SECRET"
CLIENT_IAP_ENV = "KF_PIPELINES_IAP_OAUTH2_CLIENT_ID"
CLIENT_OTHER_CLIENT_ID_ENV = "KF_PIPELINES_APP_OAUTH2_CLIENT_ID"
CLIENT_OTHER_CLIENT_SECRET_ENV = "KF_PIPELINES_APP_OAUTH2_CLIENT_SECRET"


@dataclass
class Finding:
    level: str
    item: str
    detail: str

    def to_dict(self) -> Dict[str, str]:
        return {"level": self.level, "item": self.item, "detail": self.detail}


def env_present(name: str) -> bool:
    return bool(os.environ.get(name))


def first_value(values: Iterable[Optional[str]]) -> Optional[str]:
    for value in values:
        if value:
            return value
    return None


def parse_boolish(value: Optional[str]) -> Optional[bool]:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Expected a boolean value, got {value!r}.")


def redact_url(url: str) -> str:
    """Hide userinfo, query strings, and fragments from an endpoint URL."""
    parsed = urllib.parse.urlsplit(url)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    if not netloc and parsed.netloc:
        netloc = "<redacted-userinfo>"
    path = parsed.path.rstrip("/")
    return urllib.parse.urlunsplit((parsed.scheme, netloc, path, "", ""))


def normalize_host(host: str) -> str:
    host = host.strip().rstrip("/")
    if not host:
        return host
    if not host.startswith(("http://", "https://")):
        host = "https://" + host
    return host


def base_endpoint(host: str) -> str:
    """Return a request-safe endpoint base without userinfo/query/fragment."""
    return redact_url(normalize_host(host)).rstrip("/")


def healthz_url(host: str) -> str:
    return base_endpoint(host) + "/apis/v2beta1/healthz"


def kubeconfig_status() -> str:
    if env_present("KUBECONFIG"):
        count = len([part for part in os.environ["KUBECONFIG"].split(os.pathsep) if part])
        if count == 1:
            return "KUBECONFIG is set; value hidden."
        return f"KUBECONFIG is set with {count} entries; values hidden."
    default_path = os.path.join(os.path.expanduser("~"), ".kube", "config")
    if os.path.exists(default_path):
        return "Default kubeconfig appears to exist; path hidden."
    return "No KUBECONFIG signal found; default kubeconfig not detected."


def inspect_configuration(args: argparse.Namespace) -> Dict[str, Any]:
    host = first_value([args.host, os.environ.get(CLI_ENDPOINT_ENV), os.environ.get(CLIENT_ENDPOINT_ENV)])
    host_source = (
        "--host" if args.host else
        CLI_ENDPOINT_ENV if env_present(CLI_ENDPOINT_ENV) else
        CLIENT_ENDPOINT_ENV if env_present(CLIENT_ENDPOINT_ENV) else
        "not set"
    )
    ui_host = first_value([args.ui_host, os.environ.get(CLIENT_UI_ENV)])
    namespace = first_value([args.namespace, os.environ.get(CLI_NAMESPACE_ENV)])
    verify_ssl = parse_boolish(args.verify_ssl) if args.verify_ssl is not None else None
    token_env_name = args.existing_token_env or CLI_TOKEN_ENV
    token_present = env_present(token_env_name)

    findings: List[Finding] = []

    if host:
        redacted_host = redact_url(normalize_host(host))
        findings.append(Finding("ok", "api endpoint", f"Resolved from {host_source}: {redacted_host}"))
        if not host.startswith(("http://", "https://")):
            findings.append(Finding(
                "warn",
                "api endpoint scheme",
                "No URL scheme was supplied; kfp.Client warns and defaults to https:// for explicit hosts.",
            ))
    else:
        findings.append(Finding(
            "warn",
            "api endpoint",
            "No explicit endpoint found. Client may try in-cluster config or local kubeconfig proxying and can fail with localhost connection refused.",
        ))

    if ui_host:
        findings.append(Finding("ok", "ui host", f"UI host is set separately: {redact_url(normalize_host(ui_host))}"))
        if host and redact_url(normalize_host(host)) != redact_url(normalize_host(ui_host)):
            findings.append(Finding("info", "api/ui split", "API endpoint and UI host differ; this can be correct behind proxies."))
    else:
        findings.append(Finding("info", "ui host", "No separate UI host configured; client links may use the API host or relative UI path."))

    if namespace:
        findings.append(Finding("ok", "namespace", f"Namespace resolved from {'--namespace' if args.namespace else CLI_NAMESPACE_ENV}; value: {namespace!r}"))
    else:
        findings.append(Finding("info", "namespace", "No namespace override detected; CLI/Client defaults often use 'kubeflow'. Single-user deployments may expect None."))

    auth_modes: List[str] = []
    if token_present:
        auth_modes.append(f"existing token from {token_env_name} (value hidden)")
    if args.token_present:
        auth_modes.append("existing token supplied out-of-band (value hidden)")
    if env_present(CLI_IAP_ENV) or env_present(CLIENT_IAP_ENV) or args.iap_client_id_present:
        auth_modes.append("IAP client id present")
    if env_present(CLI_OTHER_CLIENT_ID_ENV) or env_present(CLIENT_OTHER_CLIENT_ID_ENV) or args.other_client_id_present:
        auth_modes.append("other OAuth client id present")
    if env_present(CLI_OTHER_CLIENT_SECRET_ENV) or env_present(CLIENT_OTHER_CLIENT_SECRET_ENV) or args.other_client_secret_present:
        auth_modes.append("other OAuth client secret present (value hidden)")
    if auth_modes:
        findings.append(Finding("ok", "auth", "; ".join(auth_modes)))
    else:
        findings.append(Finding("info", "auth", "No explicit token/IAP env signals detected. Unauthenticated or kubeconfig/in-cluster auth may still be intended."))

    if verify_ssl is None:
        findings.append(Finding("info", "verify_ssl", "No explicit verify_ssl override supplied."))
    elif verify_ssl:
        findings.append(Finding("ok", "verify_ssl", "TLS certificate verification requested."))
    else:
        findings.append(Finding("warn", "verify_ssl", "TLS certificate verification disabled; use only as a bounded troubleshooting step."))

    if args.ssl_ca_cert:
        if os.path.exists(args.ssl_ca_cert):
            findings.append(Finding("ok", "ssl_ca_cert", "Custom CA certificate argument exists; path hidden."))
        else:
            findings.append(Finding("warn", "ssl_ca_cert", "Custom CA certificate argument does not exist; path hidden."))

    findings.append(Finding("info", "kubeconfig", kubeconfig_status()))

    result: Dict[str, Any] = {
        "summary": {
            "api_endpoint_set": bool(host),
            "api_endpoint_source": host_source,
            "ui_host_set": bool(ui_host),
            "namespace_set": bool(namespace),
            "auth_signal_count": len(auth_modes),
            "probe_requested": bool(args.probe_healthz),
        },
        "findings": [finding.to_dict() for finding in findings],
    }

    if args.probe_healthz:
        result["healthz_probe"] = probe_healthz(host, token_env_name, args.timeout_seconds)

    return result


def classify_probe_error(error: BaseException) -> str:
    text = repr(error).lower()
    if "connection refused" in text:
        return "connection refused"
    if "timed out" in text or isinstance(error, socket.timeout):
        return "timed out"
    if "name or service not known" in text or "temporary failure in name resolution" in text:
        return "name resolution failed"
    if isinstance(error, urllib.error.HTTPError):
        return f"http {error.code}"
    return error.__class__.__name__


def probe_healthz(host: Optional[str], token_env_name: str, timeout_seconds: float) -> Dict[str, Any]:
    if not host:
        return {
            "level": "error",
            "detail": "--probe-healthz requires an explicit endpoint from --host, KFP_ENDPOINT, or KF_PIPELINES_ENDPOINT.",
        }

    url = healthz_url(host)
    headers: Dict[str, str] = {}
    token = os.environ.get(token_env_name)
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url=url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(4096)
            parsed: Any = None
            content_type = response.headers.get("content-type", "")
            if b"{" in body[:1] or "json" in content_type:
                try:
                    parsed = json.loads(body.decode("utf-8"))
                except Exception:
                    parsed = None
            return {
                "level": "ok",
                "endpoint": redact_url(url),
                "status": response.status,
                "json_keys": sorted(parsed.keys()) if isinstance(parsed, dict) else [],
                "used_bearer_token": bool(token),
            }
    except urllib.error.HTTPError as error:
        return {
            "level": "error",
            "endpoint": redact_url(url),
            "classification": classify_probe_error(error),
            "status": error.code,
            "used_bearer_token": bool(token),
        }
    except (urllib.error.URLError, TimeoutError, OSError, socket.timeout) as error:
        return {
            "level": "error",
            "endpoint": redact_url(url),
            "classification": classify_probe_error(error),
            "used_bearer_token": bool(token),
        }


def print_text(result: Dict[str, Any]) -> None:
    summary = result["summary"]
    print("KFP client configuration check")
    print("Network probe: " + ("requested" if summary["probe_requested"] else "not requested (dry run)"))
    print("")
    for finding in result["findings"]:
        print(f"[{finding['level']}] {finding['item']}: {finding['detail']}")
    if "healthz_probe" in result:
        probe = result["healthz_probe"]
        print("")
        print("Healthz probe:")
        for key in sorted(probe.keys()):
            print(f"  {key}: {probe[key]}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dry-run KFP Client connection configuration without printing secrets or local paths.",
    )
    parser.add_argument("--host", help="KFP API endpoint. Value is redacted for userinfo/query/fragment in output.")
    parser.add_argument("--namespace", help="KFP namespace to report. Usually the user's namespace for multi-user deployments.")
    parser.add_argument("--ui-host", help="KFP UI base URL. This is informational and distinct from the API endpoint.")
    parser.add_argument("--verify-ssl", choices=["true", "false", "yes", "no", "1", "0"], help="Report intended TLS verification behavior.")
    parser.add_argument("--ssl-ca-cert", help="Optional CA certificate path. Existence is checked, but the path is not printed.")
    parser.add_argument("--existing-token-env", default=CLI_TOKEN_ENV, help="Environment variable holding a bearer token. The token value is never printed. Default: KFP_EXISTING_TOKEN.")
    parser.add_argument("--token-present", action="store_true", help="Mark that a token is available out-of-band without passing or printing it.")
    parser.add_argument("--iap-client-id-present", action="store_true", help="Mark IAP client ID presence without printing it.")
    parser.add_argument("--other-client-id-present", action="store_true", help="Mark OAuth helper client ID presence without printing it.")
    parser.add_argument("--other-client-secret-present", action="store_true", help="Mark OAuth helper client secret presence without printing it.")
    parser.add_argument("--probe-healthz", action="store_true", help="Explicitly perform a live GET to /apis/v2beta1/healthz. Default is no network.")
    parser.add_argument("--timeout-seconds", type=float, default=5.0, help="Timeout for --probe-healthz only. Default: 5.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = inspect_configuration(args)
    except ValueError as error:
        print(f"configuration error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
