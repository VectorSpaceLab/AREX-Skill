import argparse
import json
import tempfile
from pathlib import Path

import resolve_sources
from resolve_sources import arxiv_id_from_source, parse_arxiv_feed, resolve_paper, resolve_repo, run_command, slugify


def test_slugify_normalizes_to_snake_case():
    assert slugify("Skill-SD 2604.10674") == "skill_sd_2604_10674"


def test_arxiv_id_from_source_accepts_url_and_plain_id():
    assert arxiv_id_from_source("https://arxiv.org/abs/2604.10674") == "2604.10674"
    assert arxiv_id_from_source("arXiv:2604.10674v2") == "2604.10674v2"


def test_parse_arxiv_feed_extracts_candidate_metadata():
    feed = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2604.10674v1</id>
    <title>Skill-SD: Skill-Conditioned Self-Distillation</title>
    <link title="pdf" href="http://arxiv.org/pdf/2604.10674v1" type="application/pdf"/>
  </entry>
</feed>
"""
    candidates = parse_arxiv_feed(feed)
    assert candidates[0]["arxiv_id"] == "2604.10674v1"
    assert "Skill-SD" in candidates[0]["title"]
    assert candidates[0]["pdf_url"].endswith("2604.10674v1")


def test_resolve_paper_accepts_existing_local_path():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paper = root / "paper.txt"
        paper.write_text("paper", encoding="utf-8")
        args = argparse.Namespace(paper_source=str(paper), slug="paper", network_timeout=1, allow_title_top_hit=False)
        result = resolve_paper(args, root / "out", network_log=[])
        assert result["ready"] is True
        assert result["type"] == "local_path"
        assert result["path"] == str(paper.resolve())


def test_resolve_repo_none_is_allowed():
    args = argparse.Namespace(repo_source="none", command_timeout=1, network_timeout=1, repo_discovery_mode="ask")
    with tempfile.TemporaryDirectory() as tmp:
        result = resolve_repo(args, Path(tmp), command_log=[])
        assert result["ready"] is False
        assert result["type"] == "none"
        assert result["blockers"] == []


def test_resolve_repo_unknown_asks_before_discovery():
    args = argparse.Namespace(repo_source="unknown", command_timeout=1, network_timeout=1, repo_discovery_mode="ask")
    with tempfile.TemporaryDirectory() as tmp:
        result = resolve_repo(args, Path(tmp), command_log=[], network_log=[], paper={"input": "Example Paper"})
        assert result["ready"] is False
        assert result["type"] == "repo_discovery"
        assert result["candidates"] == []
        assert any("ask the user" in blocker for blocker in result["blockers"])


def test_resolve_repo_auto_discovers_and_clones_github_candidate():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        source_repo = root / "source"
        source_repo.mkdir()
        run_command(["git", "-C", str(source_repo), "init"], 5, [], "init")
        (source_repo / "README.md").write_text("# discovered repo\n", encoding="utf-8")
        run_command(["git", "-C", str(source_repo), "add", "README.md"], 5, [], "add")
        run_command(
            ["git", "-C", str(source_repo), "-c", "user.email=test@example.com", "-c", "user.name=Test User", "commit", "-m", "init"],
            5,
            [],
            "commit",
        )
        clone_url = source_repo.as_uri()

        def fake_discover(query, timeout, network_log):
            network_log.append({"url": "mock://github-search", "status": "completed", "query": query})
            return [
                {
                    "full_name": "example/discovered",
                    "html_url": "https://github.com/example/discovered",
                    "clone_url": clone_url,
                    "description": "implementation",
                    "stars": 10,
                    "forks": 1,
                    "updated_at": "2026-01-01T00:00:00Z",
                }
            ]

        args = argparse.Namespace(
            repo_source="unknown",
            command_timeout=5,
            network_timeout=5,
            repo_discovery_mode="auto",
            repo_search_query="Example Paper",
            slug="example_paper",
        )
        command_log = []
        network_log = []

        original_discover = resolve_sources.discover_repo_candidates
        try:
            resolve_sources.discover_repo_candidates = fake_discover
            result = resolve_repo(
                args,
                root / "out",
                command_log=command_log,
                network_log=network_log,
                paper={"input": "Example Paper"},
            )
        finally:
            resolve_sources.discover_repo_candidates = original_discover

        assert result["ready"] is True
        assert result["type"] == "github_discovery"
        assert result["url"] == clone_url
        assert result["selected_candidate"]["full_name"] == "example/discovered"
        assert Path(result["path"], "README.md").exists()
        assert any(item["label"] == "repo_clone" for item in command_log)
        assert network_log[0]["query"] == "Example Paper"
