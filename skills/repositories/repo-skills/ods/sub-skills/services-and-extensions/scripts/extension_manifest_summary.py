#!/usr/bin/env python3
"""Read-only inventory of ODS extension manifests.

Summarize service ids, categories, ports, GPU backends, and compose state for
one or more ODS catalog roots.
"""

from __future__ import annotations

import argparse
import json
import sys

sys.dont_write_bytecode = True

from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover - dependency failure is user-visible
    print(
        "ERROR: PyYAML is required to summarize ODS extension manifests.",
        file=sys.stderr,
    )
    print("Install it and rerun the helper.", file=sys.stderr)
    sys.exit(2)

MANIFEST_NAMES = ("manifest.yaml", "manifest.yml", "manifest.json")


@dataclass
class Issue:
    level: str
    message: str
    path: str | None = None
    service: str | None = None


@dataclass
class ServiceRow:
    id: str
    name: str
    category: str
    type: str
    port: str
    gpu_backends: list[str]
    compose_state: str
    manifest_path: str
    issues: list[Issue] = field(default_factory=list)


@dataclass
class CatalogReport:
    label: str
    path: str
    services: list[ServiceRow]
    issues: list[Issue] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        categories = Counter(service.category for service in self.services)
        types = Counter(service.type for service in self.services)
        compose_states = Counter(service.compose_state for service in self.services)
        backends = Counter()
        for service in self.services:
            for backend in service.gpu_backends:
                if backend and backend != "—":
                    backends[backend] += 1
        return {
            "services": len(self.services),
            "categories": dict(sorted(categories.items())),
            "types": dict(sorted(types.items())),
            "compose_states": dict(sorted(compose_states.items())),
            "gpu_backends": dict(sorted(backends.items())),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize ODS extension manifests without mutating files.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Catalog root to scan (repo root or a services directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of a human-readable report.",
    )
    return parser.parse_args()


def load_document(path: Path) -> Any:
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_manifest(service_dir: Path) -> Path | None:
    for name in MANIFEST_NAMES:
        candidate = service_dir / name
        if candidate.exists():
            return candidate
    return None


def has_catalog_manifests(path: Path) -> bool:
    if not path.is_dir():
        return False
    for child in sorted(path.iterdir()):
        if child.is_dir() and find_manifest(child) is not None:
            return True
    return False


def discover_catalog_roots(root: Path) -> list[Path]:
    candidates = [
        root,
        root / "services",
        root / "library" / "services",
        root / "extensions" / "services",
        root / "extensions" / "library" / "services",
    ]
    discovered: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if not has_catalog_manifests(candidate):
            continue
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        discovered.append(candidate)
    return discovered


def catalog_label(path: Path) -> str:
    parts = set(path.parts)
    if "library" in parts and path.name == "services":
        return "library"
    if "extensions" in parts and path.name == "services":
        return "runtime"
    return path.name or "catalog"


def format_port(service: dict[str, Any]) -> str:
    if service.get("host_network"):
        return "host-network"

    port = service.get("port")
    if port in (None, ""):
        return "—"

    external = service.get("external_port_default")
    if external in (None, ""):
        return str(port)

    try:
        external_int = int(external)
    except (TypeError, ValueError):
        return f"{port}→{external}"

    if external_int == 0:
        return f"{port} (internal-only)"
    if external_int == port:
        return str(port)
    return f"{port}→{external_int}"


def format_backends(service: dict[str, Any]) -> list[str]:
    raw = service.get("gpu_backends") or []
    if not isinstance(raw, list):
        return ["—"]
    values = [str(item) for item in raw if str(item)]
    return values or ["—"]


def compose_state(service_dir: Path, service: dict[str, Any], category: str) -> str:
    service_type = str(service.get("type") or "docker")
    if service.get("host_network"):
        return "host-network"
    if service_type == "host-systemd":
        return "host-systemd"

    compose_rel = str(service.get("compose_file") or "")
    if not compose_rel:
        return "core-only" if category == "core" else "missing-compose"

    enabled = service_dir / compose_rel
    disabled = service_dir / f"{compose_rel}.disabled"
    if enabled.exists():
        return "enabled"
    if disabled.exists():
        return "disabled"
    return "missing-compose"


def load_service_row(service_dir: Path, manifest_path: Path) -> tuple[ServiceRow | None, list[Issue]]:
    issues: list[Issue] = []
    try:
        manifest = load_document(manifest_path)
    except Exception as exc:  # pragma: no cover - surfaced to the caller
        issues.append(
            Issue(
                level="error",
                message=f"failed to parse manifest: {exc}",
                path=str(manifest_path),
                service=service_dir.name,
            )
        )
        return None, issues

    if not isinstance(manifest, dict):
        issues.append(
            Issue(
                level="error",
                message="manifest root must be a mapping",
                path=str(manifest_path),
                service=service_dir.name,
            )
        )
        return None, issues

    schema_version = str(manifest.get("schema_version") or "")
    if schema_version and schema_version != "ods.services.v1":
        issues.append(
            Issue(
                level="warning",
                message=f"unexpected schema_version {schema_version!r}",
                path=str(manifest_path),
                service=service_dir.name,
            )
        )

    service = manifest.get("service")
    if not isinstance(service, dict):
        issues.append(
            Issue(
                level="error",
                message="manifest must contain a service mapping",
                path=str(manifest_path),
                service=service_dir.name,
            )
        )
        return None, issues

    sid = str(service.get("id") or service_dir.name)
    name = str(service.get("name") or sid)
    category = str(service.get("category") or "unknown")
    service_type = str(service.get("type") or "docker")
    service_backends = format_backends(service)
    row = ServiceRow(
        id=sid,
        name=name,
        category=category,
        type=service_type,
        port=format_port(service),
        gpu_backends=service_backends,
        compose_state=compose_state(service_dir, service, category),
        manifest_path=str(manifest_path),
    )
    return row, issues


def collect_catalog(path: Path) -> CatalogReport:
    services: list[ServiceRow] = []
    issues: list[Issue] = []
    seen_ids: set[str] = set()

    for service_dir in sorted(path.iterdir()):
        if not service_dir.is_dir():
            continue
        manifest_path = find_manifest(service_dir)
        if manifest_path is None:
            continue
        row, row_issues = load_service_row(service_dir, manifest_path)
        issues.extend(row_issues)
        if row is None:
            continue
        if row.id in seen_ids:
            issues.append(
                Issue(
                    level="warning",
                    message=f"duplicate service id {row.id!r} skipped",
                    path=str(manifest_path),
                    service=row.id,
                )
            )
            continue
        seen_ids.add(row.id)
        services.append(row)

    return CatalogReport(label=catalog_label(path), path=str(path), services=services, issues=issues)


def table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    def line(values: list[str]) -> str:
        return "| " + " | ".join(
            values[index].ljust(widths[index]) for index in range(len(values))
        ) + " |"

    output = [line(headers)]
    output.append("|-" + "-|-".join("-" * width for width in widths) + "-|")
    for row in rows:
        output.append(line(row))
    return "\n".join(output)


def print_catalog(report: CatalogReport) -> None:
    summary = report.summary()
    print(f"Catalog: {report.label} ({report.path})")
    print(
        "  Summary: "
        f"{summary['services']} services; "
        f"categories={summary['categories'] or {}}; "
        f"types={summary['types'] or {}}; "
        f"compose={summary['compose_states'] or {}}; "
        f"gpu_backends={summary['gpu_backends'] or {}}"
    )
    if report.issues:
        print(f"  Issues: {len(report.issues)}")
        for issue in report.issues:
            location = f" ({issue.path})" if issue.path else ""
            print(f"    - {issue.level.upper()}: {issue.message}{location}", file=sys.stderr)
    else:
        print("  Issues: none")

    rows: list[list[str]] = []
    for service in report.services:
        rows.append(
            [
                service.id,
                service.name,
                service.category,
                service.type,
                service.port,
                ",".join(service.gpu_backends),
                service.compose_state,
            ]
        )

    if rows:
        print()
        print(
            table(
                rows,
                ["ID", "Name", "Category", "Type", "Port", "GPU backends", "Compose"],
            )
        )
    else:
        print()
        print("No service manifests found.")


def main() -> int:
    args = parse_args()
    root = args.root
    if not root.exists():
        print(f"ERROR: root path does not exist: {root}", file=sys.stderr)
        return 2

    catalog_roots = discover_catalog_roots(root)
    if not catalog_roots:
        message = f"No service manifests found under {root}"
        if args.json:
            payload = {"root": str(root), "catalogs": [], "message": message}
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(message)
        return 0

    reports = [collect_catalog(path) for path in catalog_roots]
    exit_code = 0
    if any(issue.level == "error" for report in reports for issue in report.issues):
        exit_code = 1

    if args.json:
        payload = {
            "root": str(root),
            "catalogs": [
                {
                    "label": report.label,
                    "path": report.path,
                    "summary": report.summary(),
                    "services": [asdict(service) for service in report.services],
                    "issues": [asdict(issue) for issue in report.issues],
                }
                for report in reports
            ],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for index, report in enumerate(reports):
            if index:
                print()
                print("=" * 78)
                print()
            print_catalog(report)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
