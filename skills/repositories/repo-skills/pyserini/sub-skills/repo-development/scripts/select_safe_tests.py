#!/usr/bin/env python3
"""Select focused Pyserini maintainer test commands without running them.

The selector is intentionally conservative. It prints candidate commands and
skip reasons from hard-coded source-evidence patterns; it never imports
Pyserini, opens indexes, downloads data, or executes tests.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from fnmatch import fnmatch
from typing import Iterable


SAFETY_ORDER = ["safe", "bounded", "optional", "mutating", "network", "model", "expensive"]
DEFAULT_CATEGORIES = ["checkout"]


@dataclass(frozen=True)
class Candidate:
    category: str
    command: str
    safety: str
    why: str
    requires: tuple[str, ...] = ()
    change_patterns: tuple[str, ...] = ()


CANDIDATES: tuple[Candidate, ...] = (
    Candidate(
        category="checkout",
        command="python -m pip check",
        safety="safe",
        why="Detect dependency conflicts in the active editable environment.",
        change_patterns=("pyproject.toml", "requirements*.txt", "docs/installation.md", ".agents/skills/*"),
    ),
    Candidate(
        category="checkout",
        command="python -c \"import pyserini; print('pyserini import ok')\"",
        safety="safe",
        why="Verify the active interpreter imports the checkout/package without starting Lucene workflows.",
        change_patterns=("pyproject.toml", "pyserini/__init__.py", "pyserini/**"),
    ),
    Candidate(
        category="checkout",
        command="python -m unittest tests.base.test_jvm.TestJvmStartup",
        safety="safe",
        why="Mocked JVM classpath tests cover fatjar selection and startup-error detection without requiring Java resources.",
        change_patterns=("pyserini/_jvm.py", "pyserini/pyclass.py", "pyserini/search/lucene/**", "pyserini/index/lucene/**"),
    ),
    Candidate(
        category="checkout",
        command="python -m unittest tests.base.test_jvm.TestJvmStartupIntegration",
        safety="bounded",
        why="Fresh-process JVM smoke checks skip when PyJNIus, Java, or the Anserini fatjar is unavailable.",
        requires=("JDK 21", "PyJNIus", "Anserini fatjar or ANSERINI_CLASSPATH"),
        change_patterns=("pyserini/_jvm.py", "pyserini/pyclass.py", "pyserini/search/lucene/**", "pyserini/index/lucene/**"),
    ),
    Candidate(
        category="server",
        command="python -m unittest tests.core.test_server_config",
        safety="safe",
        why="Validates server YAML parsing and alias rules using temporary directories only.",
        change_patterns=("pyserini/server/config.py", "pyserini/server/utils.py", "docs/usage-rest.md", "docs/usage-mcp.md"),
    ),
    Candidate(
        category="server",
        command="python -m unittest tests.base.test_document_format",
        safety="safe",
        why="Pure Python tests for REST document parsing and truncation behavior.",
        change_patterns=("pyserini/server/document_format.py", "pyserini/server/rest/**"),
    ),
    Candidate(
        category="server",
        command="python -m unittest tests.core.test_rest.TestRestServer.test_openapi_yaml tests.core.test_rest.TestRestServer.test_openapi_json_reflects_bundled_schema tests.core.test_rest.TestRestServer.test_docs_available tests.core.test_rest.TestRestServer.test_root",
        safety="bounded",
        why="OpenAPI and root endpoint checks avoid explicit search calls but still import the REST server stack.",
        requires=("FastAPI/TestClient", "server import dependencies"),
        change_patterns=("pyserini/server/rest/**", "pyserini/server/rest/openapi.yaml", "docs/usage-rest.md"),
    ),
    Candidate(
        category="server",
        command="python -m unittest tests.core.test_mcp",
        safety="bounded",
        why="MCP in-process tests exercise server tools and can depend on Java, Faiss, and eval resources.",
        requires=("FastMCP", "Faiss when imported", "Java/fatjar", "eval resources for eval tools"),
        change_patterns=("pyserini/server/mcp/**", "docs/usage-mcp.md"),
    ),
    Candidate(
        category="lucene",
        command="python -m unittest tests.base.test_index_otf.TestIndexOTF",
        safety="bounded",
        why="Builds tiny local Lucene indexes from fixture documents; no prebuilt-index download, but Java/fatjar required.",
        requires=("JDK 21", "PyJNIus", "Anserini fatjar or ANSERINI_CLASSPATH"),
        change_patterns=("pyserini/index/lucene/**", "pyserini/search/lucene/**", "tests/resources/simple_cacm_corpus.json"),
    ),
    Candidate(
        category="lucene",
        command="python -m unittest tests.base.test_analysis.TestAnalyzers.test_analysis tests.base.test_analysis.TestAnalyzers.test_multilingual_analysis tests.base.test_analysis.TestAnalyzers.test_jwhite_space_analyzer",
        safety="network",
        why="Selected analyzer methods avoid searcher setup expectations, but the test class setup currently downloads a CACM index before each method.",
        requires=("network/cache for class setup", "Java/fatjar"),
        change_patterns=("pyserini/analysis/**", "pyserini/search/lucene/**"),
    ),
    Candidate(
        category="eval",
        command="python -m unittest tests.base.test_trectools.TestTrecTools.test_trec_run_read tests.base.test_trectools.TestTrecTools.test_trec_run_topics tests.base.test_trectools.TestTrecTools.test_normalize_scores",
        safety="safe",
        why="Uses fixture run files and pure TrecRun operations.",
        change_patterns=("pyserini/trectools/**", "tests/resources/simple_trec_run*"),
    ),
    Candidate(
        category="eval",
        command="python -m unittest tests.base.test_eval tests.base.test_trectools",
        safety="bounded",
        why="Full eval tests exercise qrels and trec_eval behavior after tools/resources are present.",
        requires=("initialized tools submodule", "built trec_eval", "local qrels/resources"),
        change_patterns=("pyserini/eval/**", "pyserini/trectools/**", "tools/eval/**", "tools/topics-and-qrels/**"),
    ),
    Candidate(
        category="fusion",
        command="python -m unittest tests.core.test_fusion.TestFusion.test_reciprocal_rank_fusion_simple tests.core.test_fusion.TestFusion.test_interpolation_fusion_simple tests.core.test_fusion.TestFusion.test_average_fusion_simple tests.core.test_fusion.TestFusion.test_normalize_fusion_simple",
        safety="network",
        why="Individual simple methods use fixtures, but TestFusion class setup opens prebuilt sparse/dense/Faiss indexes and encoder resources first.",
        requires=("prebuilt indexes", "Faiss", "encoder resources/cache"),
        change_patterns=("pyserini/fusion/**", "tests/resources/simple_trec_run_fusion*"),
    ),
    Candidate(
        category="dense",
        command="python -m pyserini.encode --help",
        safety="bounded",
        why="Help-only encoder CLI shape check; imports dense dependencies but should not encode data.",
        requires=("Torch/Transformers import stack"),
        change_patterns=("pyserini/encode/**", "docs/usage-index.md"),
    ),
    Candidate(
        category="dense",
        command="python -m pyserini.search.faiss --help",
        safety="optional",
        why="Help-only Faiss CLI check; requires the optional Faiss package.",
        requires=("faiss-cpu or compatible Faiss"),
        change_patterns=("pyserini/search/faiss/**", "docs/usage-search.md"),
    ),
    Candidate(
        category="docs",
        command="python -m unittest tests.base.test_generate_prebuilt_index_docs",
        safety="mutating",
        why="Regenerates prebuilt-index documentation and should be followed by diff review.",
        change_patterns=("pyserini/prebuilt_index_info.py", "docs/prebuilt-indexes.md", "tests/base/test_generate_prebuilt_index_docs.py"),
    ),
    Candidate(
        category="prebuilt",
        command="python -m unittest tests.base.test_index_download tests.base.test_prebuilt_index",
        safety="network",
        why="Intentionally exercises prebuilt-index download and URL behavior.",
        requires=("network", "writable cache", "Java/fatjar for Lucene prebuilt checks"),
        change_patterns=("pyserini/prebuilt_index_info.py", "pyserini/util.py", "pyserini/search/**"),
    ),
    Candidate(
        category="integration",
        command="python -m unittest discover -s integrations/core/sparse",
        safety="expensive",
        why="Core sparse integrations can download/open prebuilt indexes and are not quick unit checks.",
        requires=("network/cache", "Java/fatjar", "benchmark resources"),
        change_patterns=("integrations/core/sparse/**", "pyserini/search/lucene/**"),
    ),
    Candidate(
        category="integration",
        command="python -m unittest discover -s integrations/core/dense",
        safety="expensive",
        why="Core dense integrations can download models/indexes and require optional dense resources.",
        requires=("network/cache", "model resources", "Faiss/dense stack"),
        change_patterns=("integrations/core/dense/**", "pyserini/encode/**", "pyserini/search/faiss/**"),
    ),
    Candidate(
        category="jobs",
        command="python scripts/select_safe_tests.py --list-excluded",
        safety="safe",
        why="Use the bundled skip inventory for maintainer job manifests instead of opening or launching source repo scripts.",
        change_patterns=("scripts/jobs*.txt", "bin/run-*.sh", "integrations/**", "pyserini/2cr/**", "docs/reproducibility.md"),
    ),
    Candidate(
        category="integration",
        command="python -m unittest discover -s tests",
        safety="expensive",
        why="Full unit discovery includes network, model, optional, Java, server, and generated-doc cases; use focused commands first.",
        requires=("explicit approval", "complete dev resources"),
        change_patterns=(),
    ),
)


CATEGORY_DESCRIPTIONS: dict[str, str] = {
    "checkout": "Editable install, dependency, JVM classpath, and source-resource sanity checks.",
    "server": "REST/MCP config, OpenAPI, document formatting, and server import checks.",
    "lucene": "Java-backed indexing, search, analyzer, and Lucene fixture checks.",
    "eval": "TREC eval, qrels, trectools, and native evaluation resource checks.",
    "fusion": "Run fusion checks, including fixture-only and prebuilt-backed cases.",
    "dense": "Encoder, Faiss, model, and dense-search command-shape checks.",
    "docs": "Generated docs and prebuilt-index documentation checks.",
    "prebuilt": "Prebuilt-index metadata, URL, and download checks.",
    "integration": "Broad integration suite inventory and opt-in execution candidates.",
    "jobs": "Maintainer job manifests for docs, integrations, and regressions.",
}


EXCLUDED_BY_DEFAULT: tuple[dict[str, str], ...] = (
    {
        "pattern": "python -m unittest discover -s tests",
        "reason": "skip-expensive: includes network/model/prebuilt/generated-doc cases; choose focused tests first.",
    },
    {
        "pattern": "python -m unittest discover -s integrations/core/*",
        "reason": "skip-expensive: broad maintained integration suites can download indexes and benchmark resources.",
    },
    {
        "pattern": "scripts/jobs.docs-all.txt",
        "reason": "skip-expensive/skip-model: launches many dense model documentation jobs through bin/run-*.sh.",
    },
    {
        "pattern": "scripts/jobs.integrations-all.txt",
        "reason": "skip-expensive: launches broad integration discovery across core suites.",
    },
    {
        "pattern": "scripts/jobs.regressions-all.txt",
        "reason": "skip-expensive/network: two-click reproduction modules span many collections.",
    },
    {
        "pattern": "tests/base/test_search.py tests/base/test_analysis.py tests/base/test_index_reader.py tests/base/encoder/test_encode_cli.py",
        "reason": "skip-network: class setup downloads CACM indexes or related artifacts.",
    },
    {
        "pattern": "tests/base/test_prebuilt_index.py tests/base/test_index_download.py",
        "reason": "skip-network: intentionally exercises prebuilt-index downloads and remote URLs.",
    },
    {
        "pattern": "tests/core/test_fusion.py",
        "reason": "skip-network/model: class setup opens prebuilt sparse/dense/Faiss resources before simple methods run.",
    },
    {
        "pattern": "tests/base/encoder/test_encoder_model_* tests/optional/*",
        "reason": "skip-model/skip-optional: can require model downloads, optional extras, GPU, or cached assets.",
    },
)


PATH_TO_CATEGORY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("pyproject.toml", "checkout"),
    ("docs/installation.md", "checkout"),
    (".gitmodules", "checkout"),
    ("tools/**", "eval"),
    ("pyserini/_jvm.py", "checkout"),
    ("pyserini/pyclass.py", "checkout"),
    ("pyserini/server/**", "server"),
    ("docs/usage-rest.md", "server"),
    ("docs/usage-mcp.md", "server"),
    ("pyserini/search/lucene/**", "lucene"),
    ("pyserini/index/lucene/**", "lucene"),
    ("pyserini/analysis/**", "lucene"),
    ("docs/usage-index.md", "lucene"),
    ("docs/usage-search.md", "lucene"),
    ("docs/usage-fetch.md", "lucene"),
    ("pyserini/eval/**", "eval"),
    ("pyserini/trectools/**", "eval"),
    ("pyserini/fusion/**", "fusion"),
    ("pyserini/encode/**", "dense"),
    ("pyserini/search/faiss/**", "dense"),
    ("pyserini/search/hybrid/**", "dense"),
    ("docs/prebuilt-indexes.md", "docs"),
    ("pyserini/prebuilt_index_info.py", "prebuilt"),
    ("tests/**", "checkout"),
    ("integrations/**", "integration"),
    ("scripts/jobs*.txt", "jobs"),
    ("bin/run-*.sh", "jobs"),
)


def normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/").lstrip("./")


def path_matches(path: str, pattern: str) -> bool:
    normalized = normalize_path(path)
    return fnmatch(normalized, pattern) or fnmatch("./" + normalized, pattern)


def categories_for_paths(paths: Iterable[str]) -> set[str]:
    categories: set[str] = set()
    for path in paths:
        for pattern, category in PATH_TO_CATEGORY_PATTERNS:
            if path_matches(path, pattern):
                categories.add(category)
        for candidate in CANDIDATES:
            if any(path_matches(path, pattern) for pattern in candidate.change_patterns):
                categories.add(candidate.category)
    return categories


def allowed_safety(args: argparse.Namespace) -> set[str]:
    allowed = {"safe"}
    if args.include_bounded:
        allowed.add("bounded")
    if args.include_optional:
        allowed.add("optional")
    if args.include_mutating:
        allowed.add("mutating")
    if args.include_network:
        allowed.add("network")
    if args.include_model:
        allowed.add("model")
    if args.include_expensive:
        allowed.add("expensive")
    if args.include_heavy:
        allowed.update({"bounded", "optional", "mutating", "network", "model", "expensive"})
    return allowed


def selected_categories(args: argparse.Namespace) -> list[str]:
    categories: set[str] = set(args.category or [])
    if "all" in categories:
        categories = set(CATEGORY_DESCRIPTIONS)
    if args.paths:
        categories.update(categories_for_paths(args.paths))
    if not categories:
        categories.update(DEFAULT_CATEGORIES)
    return sorted(categories)


def should_include(candidate: Candidate, categories: set[str], allowed: set[str]) -> bool:
    return candidate.category in categories and candidate.safety in allowed


def make_record(candidate: Candidate, included: bool, reason: str) -> dict[str, object]:
    record = asdict(candidate)
    record["included"] = included
    record["decision"] = reason
    return record


def choose_candidates(args: argparse.Namespace) -> list[dict[str, object]]:
    categories = set(selected_categories(args))
    allowed = allowed_safety(args)
    records: list[dict[str, object]] = []
    for candidate in CANDIDATES:
        if candidate.category not in categories:
            continue
        if candidate.safety in allowed:
            records.append(make_record(candidate, True, "included"))
        else:
            records.append(make_record(candidate, False, f"skipped: requires --include-{candidate.safety}"))
    records.sort(key=lambda item: (not item["included"], SAFETY_ORDER.index(str(item["safety"])), str(item["category"]), str(item["command"])))
    return records


def print_categories() -> None:
    for category in sorted(CATEGORY_DESCRIPTIONS):
        print(f"{category}: {CATEGORY_DESCRIPTIONS[category]}")


def print_excluded() -> None:
    for item in EXCLUDED_BY_DEFAULT:
        print(f"{item['pattern']}: {item['reason']}")


def print_text(records: list[dict[str, object]], args: argparse.Namespace) -> None:
    categories = ", ".join(selected_categories(args))
    allowed = ", ".join(sorted(allowed_safety(args), key=SAFETY_ORDER.index))
    print(f"Categories: {categories}")
    print(f"Included safety levels: {allowed}")
    print()

    included = [record for record in records if record["included"]]
    skipped = [record for record in records if not record["included"]]

    if included:
        print("Candidate commands:")
        for record in included:
            print(f"- [{record['category']}:{record['safety']}] {record['command']}")
            print(f"  reason: {record['why']}")
            if record["requires"]:
                print(f"  requires: {', '.join(record['requires'])}")
    else:
        print("Candidate commands: none at current safety level")

    if skipped:
        print()
        print("Skipped candidates:")
        for record in skipped:
            print(f"- [{record['category']}:{record['safety']}] {record['command']}")
            print(f"  {record['decision']}; {record['why']}")
            if record["requires"]:
                print(f"  requires: {', '.join(record['requires'])}")

    print()
    print("This script only prints commands; review prerequisites before running any candidate.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print focused Pyserini maintainer test candidates without executing them.",
    )
    parser.add_argument("--paths", nargs="*", default=[], help="Changed files/directories used to infer categories.")
    parser.add_argument(
        "--category",
        action="append",
        choices=sorted(CATEGORY_DESCRIPTIONS) + ["all"],
        help="Add a category explicitly. May be repeated. Use 'all' for all categories.",
    )
    parser.add_argument("--include-bounded", action="store_true", help="Include local-resource tests such as Java/fatjar/eval/server checks.")
    parser.add_argument("--include-optional", action="store_true", help="Include optional-dependency checks such as Faiss help.")
    parser.add_argument("--include-mutating", action="store_true", help="Include tests that intentionally rewrite generated docs or metadata.")
    parser.add_argument("--include-network", action="store_true", help="Include download/prebuilt-index candidates.")
    parser.add_argument("--include-model", action="store_true", help="Include model/encoder-resource candidates.")
    parser.add_argument("--include-expensive", action="store_true", help="Include broad integration or full-tree candidates.")
    parser.add_argument("--include-heavy", action="store_true", help="Include all gated safety levels.")
    parser.add_argument("--list-categories", action="store_true", help="List category names and exit.")
    parser.add_argument("--list-excluded", action="store_true", help="List common commands excluded by default and exit.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Output format.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    if args.list_categories:
        print_categories()
        return 0
    if args.list_excluded:
        print_excluded()
        return 0

    records = choose_candidates(args)
    if args.format == "json":
        payload = {
            "categories": selected_categories(args),
            "included_safety": sorted(allowed_safety(args), key=SAFETY_ORDER.index),
            "candidates": records,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_text(records, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
