#!/usr/bin/env python3
"""Resolve local or remote paper/repo sources before a Distiller run."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


ARXIV_ID_RE = re.compile(r"(?:arxiv:)?(?P<id>\d{4}\.\d{4,5}(?:v\d+)?)", re.IGNORECASE)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "paper"


def default_source_dir(workspace_root: Path, slug: str) -> Path:
    return workspace_root / slug / "distillation" / "source"


def normalize_title(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


def is_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return parsed.scheme in {"http", "https", "git", "ssh"} or value.startswith("git@")


def arxiv_id_from_source(value: str) -> str:
    match = ARXIV_ID_RE.search(value.strip())
    return match.group("id") if match else ""


def arxiv_pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id}.pdf"


def read_url(url: str, timeout: int, network_log: list[dict]) -> bytes:
    started = time.time()
    item = {"url": url, "status": "started", "elapsed_seconds": 0.0, "error": ""}
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "Paper2Skills-Distiller/1.0"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read()
        item["status"] = "completed"
        return data
    except Exception as exc:
        item["status"] = "error"
        item["error"] = repr(exc)
        raise
    finally:
        item["elapsed_seconds"] = round(time.time() - started, 3)
        network_log.append(item)


def download_url(url: str, target: Path, timeout: int, network_log: list[dict]) -> None:
    data = read_url(url, timeout=timeout, network_log=network_log)
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(target)


def parse_arxiv_feed(data: bytes) -> list[dict]:
    root = ET.fromstring(data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    candidates: list[dict] = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
        entry_id = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id = arxiv_id_from_source(entry_id)
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href", "")
                break
        candidates.append(
            {
                "title": title,
                "arxiv_id": arxiv_id,
                "abs_url": entry_id,
                "pdf_url": pdf_url or (arxiv_pdf_url(arxiv_id) if arxiv_id else ""),
            }
        )
    return candidates


def search_arxiv_title(title: str, timeout: int, network_log: list[dict]) -> list[dict]:
    quoted_title = urllib.parse.quote(f'ti:"{title}"')
    url = f"https://export.arxiv.org/api/query?search_query={quoted_title}&start=0&max_results=5"
    try:
        return parse_arxiv_feed(read_url(url, timeout=timeout, network_log=network_log))
    except (urllib.error.URLError, ET.ParseError):
        return []


def paper_repo_search_terms(args: argparse.Namespace, paper: dict) -> str:
    parts = [
        str(getattr(args, "repo_search_query", "") or "").strip(),
        str(paper.get("selected_title") or "").strip(),
        str(paper.get("input") or "").strip(),
        str(paper.get("arxiv_id") or "").strip(),
    ]
    for part in parts:
        if part and not is_url(part) and Path(part).suffix.lower() not in {".pdf", ".txt"}:
            return part
    return str(getattr(args, "slug", "") or "paper").replace("_", " ")


def parse_github_repo_search(data: bytes) -> list[dict]:
    payload = json.loads(data.decode("utf-8"))
    candidates: list[dict] = []
    for item in payload.get("items", [])[:5]:
        clone_url = item.get("clone_url") or item.get("html_url") or ""
        candidates.append(
            {
                "full_name": item.get("full_name", ""),
                "html_url": item.get("html_url", ""),
                "clone_url": clone_url,
                "description": item.get("description", "") or "",
                "stars": item.get("stargazers_count", 0),
                "forks": item.get("forks_count", 0),
                "updated_at": item.get("updated_at", ""),
            }
        )
    return candidates


def discover_repo_candidates(query: str, timeout: int, network_log: list[dict]) -> list[dict]:
    terms = " ".join(query.split())
    if not terms:
        return []
    search_query = f"{terms} paper implementation"
    url = (
        "https://api.github.com/search/repositories?"
        + urllib.parse.urlencode({"q": search_query, "sort": "stars", "order": "desc", "per_page": "5"})
    )
    try:
        return parse_github_repo_search(read_url(url, timeout=timeout, network_log=network_log))
    except Exception:
        return []


def run_command(cmd: list[str], timeout: int, command_log: list[dict], label: str) -> dict:
    started = time.time()
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        status = "completed"
        returncode = proc.returncode
        stdout = proc.stdout[-4000:]
        stderr = proc.stderr[-4000:]
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        returncode = 124
        stdout = (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else ""
    except Exception as exc:  # pragma: no cover - defensive
        status = "error"
        returncode = 1
        stdout = ""
        stderr = repr(exc)
    result = {
        "command": " ".join(cmd),
        "label": label,
        "status": status,
        "returncode": returncode,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_tail": stdout,
        "stderr_tail": stderr,
    }
    command_log.append(result)
    return result


def resolve_paper(args: argparse.Namespace, out_dir: Path, network_log: list[dict]) -> dict:
    source = args.paper_source.strip()
    result = {
        "input": source,
        "ready": False,
        "type": "",
        "path": "",
        "url": "",
        "arxiv_id": "",
        "candidates": [],
        "blockers": [],
    }
    local = Path(source).expanduser()
    if local.exists():
        result.update({"ready": True, "type": "local_path", "path": str(local.resolve())})
        return result

    arxiv_id = arxiv_id_from_source(source)
    parsed = urllib.parse.urlparse(source)
    if arxiv_id and ("arxiv.org" in parsed.netloc or not is_url(source)):
        url = arxiv_pdf_url(arxiv_id)
        target = out_dir / f"{args.slug}.pdf"
        try:
            download_url(url, target, timeout=args.network_timeout, network_log=network_log)
            result.update({"ready": True, "type": "arxiv", "path": str(target.resolve()), "url": url, "arxiv_id": arxiv_id})
        except Exception as exc:
            result["blockers"].append(f"arXiv PDF download failed: {exc!r}")
        return result

    if is_url(source):
        suffix = Path(parsed.path).suffix or ".pdf"
        target = out_dir / f"{args.slug}{suffix}"
        try:
            download_url(source, target, timeout=args.network_timeout, network_log=network_log)
            result.update({"ready": True, "type": "url", "path": str(target.resolve()), "url": source})
        except Exception as exc:
            result["blockers"].append(f"paper URL download failed: {exc!r}")
        return result

    candidates = search_arxiv_title(source, timeout=args.network_timeout, network_log=network_log)
    result["type"] = "title_search"
    result["candidates"] = candidates
    source_norm = normalize_title(source)
    exact = [item for item in candidates if normalize_title(item.get("title", "")) == source_norm]
    selected = exact[0] if exact else (candidates[0] if args.allow_title_top_hit and candidates else None)
    if not selected:
        if candidates:
            result["blockers"].append("paper title search returned candidates but no exact match; ask the user to choose")
        else:
            result["blockers"].append("paper title search returned no arXiv candidates")
        return result
    target = out_dir / f"{args.slug}.pdf"
    try:
        download_url(selected["pdf_url"], target, timeout=args.network_timeout, network_log=network_log)
        result.update(
            {
                "ready": True,
                "path": str(target.resolve()),
                "url": selected["pdf_url"],
                "arxiv_id": selected.get("arxiv_id", ""),
                "selected_title": selected.get("title", ""),
            }
        )
    except Exception as exc:
        result["blockers"].append(f"selected paper download failed: {exc!r}")
    return result


def git_commit(path: Path, timeout: int, command_log: list[dict]) -> str:
    if not (path / ".git").exists():
        return ""
    result = run_command(["git", "-C", str(path), "rev-parse", "--short", "HEAD"], timeout, command_log, "repo_git_commit")
    return result["stdout_tail"].strip() if result["returncode"] == 0 else ""


def clone_repo_url(source: str, args: argparse.Namespace, out_dir: Path, command_log: list[dict], result: dict) -> dict:
    if not source:
        result["blockers"].append("repo candidate did not include a clone URL")
        return result
    git = shutil.which("git")
    if not git:
        result["blockers"].append("git executable not found")
        return result
    target = out_dir / "repo"
    if target.exists() and any(target.iterdir()):
        result["blockers"].append(f"repo clone target already exists and is not empty: {target}")
        return result
    cmd = [git, "clone", "--depth", "1", source, str(target)]
    command = run_command(cmd, timeout=args.network_timeout, command_log=command_log, label="repo_clone")
    if command["returncode"] != 0:
        result["blockers"].append(command["stderr_tail"] or command["stdout_tail"] or f"repo clone failed with {command['returncode']}")
        return result
    result.update({"ready": True, "type": result.get("type") or "git_url", "path": str(target.resolve()), "url": source})
    result["commit"] = git_commit(target.resolve(), args.command_timeout, command_log)
    return result


def resolve_repo(args: argparse.Namespace, out_dir: Path, command_log: list[dict], network_log: list[dict] | None = None, paper: dict | None = None) -> dict:
    source = (args.repo_source or "").strip()
    result = {
        "input": source,
        "ready": False,
        "type": "none",
        "path": "",
        "url": "",
        "commit": "",
        "discovery_mode": getattr(args, "repo_discovery_mode", "ask"),
        "candidates": [],
        "selected_candidate": {},
        "blockers": [],
    }
    source_lower = source.lower()
    if not source or source_lower in {"none", "no", "n/a"}:
        return result
    if source_lower == "unknown":
        mode = str(getattr(args, "repo_discovery_mode", "ask") or "ask").lower()
        result["type"] = "repo_discovery"
        if mode == "disabled":
            return result
        if mode == "ask":
            result["blockers"].append("repo source is unknown; ask the user whether to search for an implementation repo or proceed paper-only")
            return result
        query = paper_repo_search_terms(args, paper or {})
        result["query"] = query
        candidates = discover_repo_candidates(query, timeout=args.network_timeout, network_log=network_log if network_log is not None else [])
        result["candidates"] = candidates
        if not candidates:
            result["blockers"].append("repo discovery returned no GitHub candidates")
            return result
        selected = candidates[0]
        result["selected_candidate"] = selected
        result["type"] = "github_discovery"
        return clone_repo_url(selected.get("clone_url") or selected.get("html_url") or "", args, out_dir, command_log, result)
    local = Path(source).expanduser()
    if local.exists():
        result.update({"ready": True, "type": "local_path", "path": str(local.resolve())})
        result["commit"] = git_commit(local.resolve(), args.command_timeout, command_log)
        return result
    if not is_url(source):
        result["blockers"].append("repo source is neither an existing local path nor a URL")
        return result
    result["type"] = "git_url"
    return clone_repo_url(source, args, out_dir, command_log, result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", required=True)
    parser.add_argument("--paper-source", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--repo-source", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--network-timeout", type=int, default=120)
    parser.add_argument("--command-timeout", type=int, default=20)
    parser.add_argument("--allow-title-top-hit", action="store_true")
    parser.add_argument(
        "--repo-discovery-mode",
        choices=["ask", "auto", "disabled"],
        default="ask",
        help="How to handle --repo-source unknown: ask records a blocker, auto searches GitHub and clones the top candidate, disabled skips discovery.",
    )
    parser.add_argument(
        "--repo-search-query",
        default="",
        help="Optional query text for repo discovery. Defaults to selected paper title, paper input, arXiv id, or slug.",
    )
    args = parser.parse_args()
    args.slug = slugify(args.slug)

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    out_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else default_source_dir(workspace_root, args.slug)
    out_dir.mkdir(parents=True, exist_ok=True)
    command_log: list[dict] = []
    network_log: list[dict] = []

    paper = resolve_paper(args, out_dir, network_log)
    repo = resolve_repo(args, out_dir, command_log, network_log, paper)
    result = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(workspace_root),
        "slug": args.slug,
        "output_dir": str(out_dir),
        "paper": paper,
        "repo": repo,
        "logs": {
            "commands": command_log,
            "network_operations": network_log,
        },
        "ready": bool(paper.get("ready")),
    }
    write_json(out_dir / "source_resolution.json", result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ready"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
