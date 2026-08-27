#!/usr/bin/env python3
"""Safely inventory CubeStudio Kubernetes/Compose manifests and shell hazards.

This helper is read-only: it never invokes Docker, kubectl, shell scripts,
network access, package managers, or long-running services. It accepts either a
CubeStudio checkout or any directory/file containing deployment manifests.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:  # PyYAML is optional; the fallback still gives useful inventory.
    import yaml  # type: ignore
except Exception:  # pragma: no cover - depends on caller environment
    yaml = None  # type: ignore

YAML_SUFFIXES = {".yaml", ".yml"}
COMPOSE_NAMES = {
    "docker-compose.yml",
    "docker-compose.yaml",
    "compose.yml",
    "compose.yaml",
}
SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "dist",
    "build",
}

# Intentionally broad image-like token. It is used as a fallback scanner only;
# structured YAML image fields are preferred when available.
IMAGE_TOKEN = re.compile(
    r"(?<![\w./:-])"
    r"(?:[a-zA-Z0-9.-]+(?::[0-9]+)?/)?"
    r"(?:[a-zA-Z0-9._-]+/)"
    r"[a-zA-Z0-9._-]+"
    r"(?:[:@][A-Za-z0-9._:+-]+)?"
)

HAZARD_PATTERNS: List[Tuple[str, re.Pattern[str]]] = [
    ("kubectl-apply", re.compile(r"\bkubectl\s+(?:--\S+\s+)*apply\b")),
    ("kubectl-create", re.compile(r"\bkubectl\s+(?:--\S+\s+)*create\b")),
    ("kubectl-delete", re.compile(r"\bkubectl\s+(?:--\S+\s+)*delete\b")),
    ("kubectl-patch", re.compile(r"\bkubectl\s+(?:--\S+\s+)*patch\b")),
    ("kubectl-label", re.compile(r"\bkubectl\s+(?:--\S+\s+)*label\b")),
    ("docker-build", re.compile(r"\bdocker\s+build\b")),
    ("docker-pull", re.compile(r"\bdocker\s+pull\b")),
    ("docker-push", re.compile(r"\bdocker\s+push\b")),
    ("docker-save-load", re.compile(r"\bdocker\s+(?:save|load|tag|login)\b")),
    ("compose-up", re.compile(r"\b(?:docker-compose|docker\s+compose)\s+.*\bup\b")),
    ("network-download", re.compile(r"\b(?:wget|curl)\b.*https?://")),
    ("package-install", re.compile(r"\b(?:apt(?:-get)?|yum|pip3?|npm|yarn)\s+(?:install|add|update|upgrade)\b")),
    ("host-service", re.compile(r"\b(?:systemctl|service|reboot|modprobe|iptables|firewall-cmd)\b")),
    ("destructive-rm", re.compile(r"\brm\s+-[rfRF]+\b")),
    ("background-or-wait", re.compile(r"(?:\s&\s*$|\bwait\b|\bsleep\s+[0-9]+)")),
]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only inventory for CubeStudio Kubernetes YAML, Docker Compose "
            "files, image references, namespaces, and hazardous shell commands."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="CubeStudio checkout, manifest directory, YAML file, Compose file, or shell script to inspect.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. Default: text.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=2_000_000,
        help="Skip individual files larger than this many bytes. Default: 2000000.",
    )
    parser.add_argument(
        "--show-all-images",
        action="store_true",
        help="In text mode, print every image reference instead of the first 80.",
    )
    return parser.parse_args(argv)


def iter_files(root: Path, max_file_bytes: int) -> Iterable[Path]:
    if root.is_file():
        if safe_size(root) <= max_file_bytes:
            yield root
        return
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if not path.is_file():
            continue
        if safe_size(path) > max_file_bytes:
            continue
        yield path


def safe_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0


def read_text(path: Path) -> Optional[str]:
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:4096]:
        return None
    return raw.decode("utf-8", errors="replace")


def rel(path: Path, root: Path) -> str:
    try:
        if root.is_file():
            return path.name
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_yaml_docs(text: str) -> Tuple[List[Any], Optional[str]]:
    if yaml is None:
        return [], "PyYAML not available; used text fallback"
    try:
        docs = list(yaml.safe_load_all(text))
        return docs, None
    except Exception as exc:
        return [], f"YAML parse error: {exc}"


def walk_images(obj: Any, out: List[str]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "image" and isinstance(value, str):
                out.append(value)
            else:
                walk_images(value, out)
    elif isinstance(obj, list):
        for item in obj:
            walk_images(item, out)


def extract_kustomize_images(doc: Dict[str, Any]) -> List[str]:
    images: List[str] = []
    if str(doc.get("kind", "")).lower() != "kustomization":
        return images
    raw = doc.get("images")
    if not isinstance(raw, list):
        return images
    for item in raw:
        if not isinstance(item, dict):
            continue
        for key in ("name", "newName"):
            value = item.get(key)
            if isinstance(value, str) and value:
                images.append(value)
    return images


def first_scalar(doc: Dict[str, Any], *keys: str) -> Optional[str]:
    cur: Any = doc
    for key in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    if isinstance(cur, str):
        return cur
    return None


def fallback_yaml_records(text: str) -> Tuple[List[Dict[str, str]], List[str]]:
    """Extract rough kind/name/namespace/image data without a YAML parser."""
    docs = re.split(r"^---\s*$", text, flags=re.MULTILINE)
    records: List[Dict[str, str]] = []
    images: List[str] = []
    for doc in docs:
        kind = match_value(doc, "kind")
        api = match_value(doc, "apiVersion")
        name = None
        namespace = None
        meta = re.search(r"(?ms)^metadata:\s*\n(?P<body>(?:^[ \t]+[^\n]*\n?)*)", doc)
        if meta:
            name = match_value(meta.group("body"), "name")
            namespace = match_value(meta.group("body"), "namespace")
        for image in re.findall(r"(?m)^\s*image:\s*['\"]?([^'\"\s#]+)", doc):
            images.append(image.strip())
        if kind or api or name or namespace:
            records.append(
                {
                    "apiVersion": api or "",
                    "kind": kind or "",
                    "name": name or "",
                    "namespace": namespace or "",
                }
            )
    return records, images


def match_value(text: str, key: str) -> Optional[str]:
    pat = re.compile(rf"(?m)^\s*{re.escape(key)}:\s*['\"]?([^'\"\n#]+)")
    m = pat.search(text)
    return m.group(1).strip() if m else None


def fallback_compose_services(text: str) -> List[Dict[str, str]]:
    services: List[Dict[str, str]] = []
    m = re.search(r"(?ms)^services:\s*\n(?P<body>.*)", text)
    if not m:
        return services
    body = m.group("body")
    current: Optional[Dict[str, str]] = None
    for line in body.splitlines():
        svc = re.match(r"^\s{2}([A-Za-z0-9_.-]+):\s*(?:#.*)?$", line)
        if svc:
            current = {"service": svc.group(1), "image": "", "command": ""}
            services.append(current)
            continue
        if current is None:
            continue
        img = re.match(r"^\s{4}image:\s*['\"]?([^'\"\s#]+)", line)
        if img:
            current["image"] = img.group(1)
        cmd = re.match(r"^\s{4}command:\s*(.+)$", line)
        if cmd:
            current["command"] = cmd.group(1).strip()
    return services


def scan_shell_hazards(text: str) -> List[Dict[str, Any]]:
    hazards: List[Dict[str, Any]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        labels = [label for label, pat in HAZARD_PATTERNS if pat.search(stripped)]
        if labels:
            hazards.append({"line": lineno, "labels": labels, "command": stripped[:500]})
    return hazards


def looks_shell(path: Path, text: str) -> bool:
    if path.suffix == ".sh":
        return True
    first = text.splitlines()[0] if text.splitlines() else ""
    return first.startswith("#!") and ("sh" in first or "bash" in first)


def scan_image_tokens(text: str) -> List[str]:
    found = []
    for token in IMAGE_TOKEN.findall(text):
        if "/" not in token:
            continue
        if token.startswith(("http://", "https://")):
            continue
        if token.endswith((".yaml", ".yml", ".md", ".py", ".sh")):
            continue
        found.append(token)
    return found


def inventory(root: Path, max_file_bytes: int) -> Dict[str, Any]:
    root = root.resolve()
    result: Dict[str, Any] = {
        "root": root.as_posix(),
        "pyyaml_available": yaml is not None,
        "files_scanned": 0,
        "yaml_files": [],
        "compose_files": [],
        "shell_files": [],
        "kind_counts": Counter(),
        "namespace_counts": Counter(),
        "images": defaultdict(list),
        "parse_warnings": [],
        "skipped_large_files": [],
    }

    if root.is_dir():
        for path in root.rglob("*"):
            if path.is_file() and safe_size(path) > max_file_bytes:
                result["skipped_large_files"].append(rel(path, root))

    for path in iter_files(root, max_file_bytes):
        text = read_text(path)
        if text is None:
            continue
        rpath = rel(path, root)
        result["files_scanned"] += 1

        if path.suffix.lower() in YAML_SUFFIXES:
            docs, warning = load_yaml_docs(text)
            file_record: Dict[str, Any] = {
                "file": rpath,
                "resources": [],
                "images": [],
                "compose_services": [],
                "warning": warning,
            }
            if warning:
                result["parse_warnings"].append({"file": rpath, "warning": warning})

            if docs:
                for doc in docs:
                    if not isinstance(doc, dict):
                        continue
                    api = doc.get("apiVersion")
                    kind = doc.get("kind")
                    metadata = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
                    name = metadata.get("name") if isinstance(metadata, dict) else None
                    namespace = metadata.get("namespace") if isinstance(metadata, dict) else None
                    if kind:
                        result["kind_counts"][str(kind)] += 1
                    if namespace:
                        result["namespace_counts"][str(namespace)] += 1
                    elif kind:
                        result["namespace_counts"]["<none>"] += 1
                    if api or kind or name or namespace:
                        file_record["resources"].append(
                            {
                                "apiVersion": str(api or ""),
                                "kind": str(kind or ""),
                                "name": str(name or ""),
                                "namespace": str(namespace or ""),
                            }
                        )
                    imgs: List[str] = []
                    walk_images(doc, imgs)
                    imgs.extend(extract_kustomize_images(doc))
                    for image in imgs:
                        file_record["images"].append(image)
                        result["images"][image].append(rpath)

                # Docker Compose is also YAML. Structured parse is easiest.
                if path.name in COMPOSE_NAMES or "services" in {str(k) for doc in docs if isinstance(doc, dict) for k in doc.keys()}:
                    for doc in docs:
                        if not isinstance(doc, dict) or not isinstance(doc.get("services"), dict):
                            continue
                        for svc_name, svc in doc["services"].items():
                            if isinstance(svc, dict):
                                image = svc.get("image", "")
                                command = svc.get("command", "")
                                if isinstance(image, str) and image:
                                    result["images"][image].append(rpath)
                                file_record["compose_services"].append(
                                    {
                                        "service": str(svc_name),
                                        "image": str(image or ""),
                                        "command": short_value(command),
                                    }
                                )
            else:
                resources, images = fallback_yaml_records(text)
                for rec in resources:
                    if rec.get("kind"):
                        result["kind_counts"][rec["kind"]] += 1
                    if rec.get("namespace"):
                        result["namespace_counts"][rec["namespace"]] += 1
                    elif rec.get("kind"):
                        result["namespace_counts"]["<none>"] += 1
                for image in images:
                    result["images"][image].append(rpath)
                file_record["resources"] = resources
                file_record["images"] = images
                if path.name in COMPOSE_NAMES:
                    services = fallback_compose_services(text)
                    for svc in services:
                        if svc.get("image"):
                            result["images"][svc["image"]].append(rpath)
                    file_record["compose_services"] = services

            if file_record["resources"] or file_record["images"] or file_record["compose_services"] or warning:
                result["yaml_files"].append(file_record)
            if file_record["compose_services"]:
                result["compose_files"].append({"file": rpath, "services": file_record["compose_services"]})

        elif looks_shell(path, text):
            hazards = scan_shell_hazards(text)
            image_tokens = scan_image_tokens(text)
            for image in image_tokens:
                result["images"][image].append(rpath)
            result["shell_files"].append(
                {
                    "file": rpath,
                    "hazard_count": len(hazards),
                    "hazards": hazards,
                    "image_tokens": sorted(set(image_tokens)),
                }
            )

    # Convert counters/defaultdicts for JSON/text consumers.
    result["kind_counts"] = dict(sorted(result["kind_counts"].items()))
    result["namespace_counts"] = dict(sorted(result["namespace_counts"].items()))
    result["images"] = {k: sorted(set(v)) for k, v in sorted(result["images"].items())}
    return result


def short_value(value: Any) -> str:
    if isinstance(value, str):
        return value[:300]
    try:
        return json.dumps(value, ensure_ascii=False)[:300]
    except TypeError:
        return str(value)[:300]


def print_text(data: Dict[str, Any], show_all_images: bool = False) -> None:
    print("CubeStudio manifest inventory (read-only)")
    print(f"Root: {data['root']}")
    print(f"Files scanned: {data['files_scanned']}")
    print(f"PyYAML available: {data['pyyaml_available']}")
    if data.get("skipped_large_files"):
        print(f"Skipped large files: {len(data['skipped_large_files'])}")

    print("\nResource kinds:")
    if data["kind_counts"]:
        for kind, count in sorted(data["kind_counts"].items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {kind}: {count}")
    else:
        print("  (none found)")

    print("\nNamespaces:")
    if data["namespace_counts"]:
        for namespace, count in sorted(data["namespace_counts"].items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"  {namespace}: {count}")
    else:
        print("  (none found)")

    print("\nCompose services:")
    compose_found = False
    for compose in data["compose_files"]:
        compose_found = True
        print(f"  {compose['file']}")
        for svc in compose["services"]:
            image = f" image={svc['image']}" if svc.get("image") else ""
            command = f" command={svc['command']}" if svc.get("command") else ""
            print(f"    - {svc['service']}{image}{command}")
    if not compose_found:
        print("  (none found)")

    print("\nImages:")
    images = sorted(data["images"].items())
    if not images:
        print("  (none found)")
    else:
        limit = len(images) if show_all_images else 80
        for image, sources in images[:limit]:
            source_str = ", ".join(sources[:5])
            extra = f" (+{len(sources) - 5} more)" if len(sources) > 5 else ""
            print(f"  {image}  [{source_str}{extra}]")
        if len(images) > limit:
            print(f"  ... {len(images) - limit} more images omitted; use --show-all-images")

    print("\nShell hazards:")
    any_hazard = False
    for shell in data["shell_files"]:
        if shell["hazard_count"] == 0:
            continue
        any_hazard = True
        print(f"  {shell['file']} ({shell['hazard_count']} hazards)")
        for hazard in shell["hazards"][:20]:
            labels = ",".join(hazard["labels"])
            print(f"    L{hazard['line']}: {labels}: {hazard['command']}")
        if shell["hazard_count"] > 20:
            print(f"    ... {shell['hazard_count'] - 20} more hazards")
    if not any_hazard:
        print("  (none found)")

    if data.get("parse_warnings"):
        print("\nParse warnings:")
        for warning in data["parse_warnings"]:
            print(f"  {warning['file']}: {warning['warning']}")

    print("\nNo commands were executed; this was a static read-only inventory.")


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    root = Path(args.path)
    if not root.exists():
        print(f"error: path does not exist: {root}", file=sys.stderr)
        return 2
    data = inventory(root, args.max_file_bytes)
    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print_text(data, show_all_images=args.show_all_images)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
