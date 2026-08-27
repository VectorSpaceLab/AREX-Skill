#!/usr/bin/env python3
"""Check mcp-agent workflow imports without requiring provider credentials by default."""

from __future__ import annotations

import argparse
import ast
import importlib
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ImportCheck:
    module: str
    names: tuple[str, ...]
    optional: bool = False


CORE_CHECKS = (
    ImportCheck(
        "mcp_agent.workflows.factory",
        (
            "AgentSpec",
            "OrchestratorOverrides",
            "RequestParams",
            "create_deep_orchestrator",
            "create_evaluator_optimizer_llm",
            "create_intent_classifier_embedding",
            "create_intent_classifier_llm",
            "create_llm",
            "create_orchestrator",
            "create_parallel_llm",
            "create_router_embedding",
            "create_router_llm",
            "create_swarm",
        ),
    ),
    ImportCheck("mcp_agent.workflows.router.router_llm", ("LLMRouter", "LLMRouterResult")),
    ImportCheck("mcp_agent.workflows.router.router_embedding", ("EmbeddingRouter",)),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_base", ("Intent",)),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_llm", ("LLMIntentClassifier",)),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_embedding", ("EmbeddingIntentClassifier",)),
    ImportCheck("mcp_agent.workflows.parallel.parallel_llm", ("ParallelLLM",)),
    ImportCheck("mcp_agent.workflows.parallel.fan_in", ("FanIn", "FanInInput")),
    ImportCheck("mcp_agent.workflows.parallel.fan_out", ("FanOut",)),
    ImportCheck("mcp_agent.workflows.orchestrator.orchestrator", ("Orchestrator", "OrchestratorOverrides")),
    ImportCheck("mcp_agent.workflows.orchestrator.orchestrator_models", ("Plan", "PlanResult", "Step", "Task")),
    ImportCheck("mcp_agent.workflows.deep_orchestrator.orchestrator", ("DeepOrchestrator",)),
    ImportCheck("mcp_agent.workflows.deep_orchestrator.config", ("DeepOrchestratorConfig",)),
    ImportCheck("mcp_agent.workflows.evaluator_optimizer.evaluator_optimizer", ("EvaluatorOptimizerLLM", "EvaluationResult", "QualityRating")),
    ImportCheck("mcp_agent.workflows.swarm.swarm", ("AgentFunctionResult", "DoneAgent", "Swarm", "SwarmAgent")),
)

PROVIDER_CHECKS = (
    ImportCheck("mcp_agent.workflows.router.router_llm_openai", ("OpenAILLMRouter",), optional=True),
    ImportCheck("mcp_agent.workflows.router.router_llm_anthropic", ("AnthropicLLMRouter",), optional=True),
    ImportCheck("mcp_agent.workflows.router.router_embedding_openai", ("OpenAIEmbeddingRouter",), optional=True),
    ImportCheck("mcp_agent.workflows.router.router_embedding_cohere", ("CohereEmbeddingRouter",), optional=True),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_llm_openai", ("OpenAILLMIntentClassifier",), optional=True),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_llm_anthropic", ("AnthropicLLMIntentClassifier",), optional=True),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_embedding_openai", ("OpenAIEmbeddingIntentClassifier",), optional=True),
    ImportCheck("mcp_agent.workflows.intent_classifier.intent_classifier_embedding_cohere", ("CohereEmbeddingIntentClassifier",), optional=True),
    ImportCheck("mcp_agent.workflows.embedding.embedding_openai", ("OpenAIEmbeddingModel",), optional=True),
    ImportCheck("mcp_agent.workflows.embedding.embedding_cohere", ("CohereEmbeddingModel",), optional=True),
    ImportCheck("mcp_agent.workflows.swarm.swarm_openai", ("OpenAISwarm",), optional=True),
    ImportCheck("mcp_agent.workflows.swarm.swarm_anthropic", ("AnthropicSwarm",), optional=True),
)


class CheckFailure(Exception):
    """Raised for a failed import check."""


def add_import_paths(project_root: str | None = None) -> list[Path]:
    """Add likely source-layout paths so checks work from a checkout or installed package."""
    starts = [Path.cwd(), Path(__file__).resolve()]
    if project_root:
        starts.insert(0, Path(project_root).expanduser().resolve())

    added: list[Path] = []
    seen: set[Path] = set()
    for start in starts:
        for directory in (start, *start.parents):
            for candidate in (directory / "src", directory):
                if candidate in seen:
                    continue
                seen.add(candidate)
                if (candidate / "mcp_agent").exists():
                    sys.path.insert(0, str(candidate))
                    added.append(candidate)
    return added


def import_names(check: ImportCheck) -> list[str]:
    module = importlib.import_module(check.module)
    missing = [name for name in check.names if not hasattr(module, name)]
    if missing:
        raise CheckFailure(f"{check.module} missing: {', '.join(missing)}")
    return [f"{check.module}:{name}" for name in check.names]


def module_file(module_name: str, import_paths: list[Path]) -> Path:
    relative = Path(*module_name.split("."))
    for base in import_paths:
        module_path = base / relative.with_suffix(".py")
        if module_path.exists():
            return module_path
        package_path = base / relative / "__init__.py"
        if package_path.exists():
            return package_path
    raise CheckFailure(f"could not find source file for {module_name}")


def source_names(check: ImportCheck, import_paths: list[Path]) -> list[str]:
    path = module_file(check.module, import_paths)
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name != "*":
                    names.add(alias.asname or alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".", 1)[0])
    missing = [name for name in check.names if name not in names]
    if missing:
        raise CheckFailure(f"{check.module} source missing: {', '.join(missing)}")
    return [f"{check.module}:{name}" for name in check.names]


def verify_no_router_llm_alias(source_only: bool, import_paths: list[Path]) -> None:
    if source_only:
        check = ImportCheck("mcp_agent.workflows.router.router_llm", ("RouterLLM",))
        try:
            source_names(check, import_paths)
        except CheckFailure:
            return
        raise CheckFailure("Unexpected RouterLLM alias found; use LLMRouter explicitly")

    module = importlib.import_module("mcp_agent.workflows.router.router_llm")
    if hasattr(module, "RouterLLM"):
        raise CheckFailure("Unexpected RouterLLM alias found; use LLMRouter explicitly")


def run_checks(
    include_provider: bool,
    quiet: bool,
    project_root: str | None = None,
    source_only: bool = False,
) -> int:
    added_paths = add_import_paths(project_root)
    if added_paths and not quiet:
        print("Added import paths: " + ", ".join(str(path) for path in added_paths))
    if source_only and not added_paths:
        print("workflow source check failed: no mcp_agent source tree found", file=sys.stderr)
        return 1

    checks = list(CORE_CHECKS)
    if include_provider:
        checks.extend(PROVIDER_CHECKS)

    failures: list[str] = []
    skipped: list[str] = []
    imported_count = 0

    checker = source_names if source_only else import_names
    checked_label = "source names" if source_only else "imports"

    for check in checks:
        try:
            if source_only:
                imported = checker(check, added_paths)  # type: ignore[misc]
            else:
                imported = checker(check)  # type: ignore[misc]
            imported_count += len(imported)
            if not quiet:
                print(f"OK {check.module}: {', '.join(check.names)}")
        except Exception as exc:  # noqa: BLE001 - report all import failures clearly
            message = f"{check.module}: {exc}"
            if check.optional and not include_provider:
                skipped.append(message)
            else:
                failures.append(message)
                if not quiet:
                    print(f"FAIL {message}", file=sys.stderr)

    try:
        verify_no_router_llm_alias(source_only=source_only, import_paths=added_paths)
        if not quiet:
            print("OK router class name: LLMRouter is canonical; RouterLLM is absent")
    except Exception as exc:  # noqa: BLE001
        failures.append(str(exc))
        if not quiet:
            print(f"FAIL {exc}", file=sys.stderr)

    if skipped and not quiet:
        for item in skipped:
            print(f"SKIP optional {item}")

    if failures:
        print(f"workflow import check failed: {len(failures)} failure(s)", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    if not quiet:
        print(f"workflow {checked_label} check passed: {imported_count} names verified")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify mcp-agent workflow imports and canonical class names. "
            "By default this avoids provider client instantiation and credential checks. "
            "Use --source-only in an uninstalled source checkout."
        )
    )
    parser.add_argument(
        "--include-provider",
        action="store_true",
        help="also import provider-specific wrappers; still does not instantiate clients",
    )
    parser.add_argument("--quiet", action="store_true", help="only print failures and final status")
    parser.add_argument(
        "--source-only",
        action="store_true",
        help="parse source files for expected names instead of importing runtime dependencies",
    )
    parser.add_argument(
        "--project-root",
        help="optional repository root to search for src/mcp_agent before importing",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return run_checks(
        include_provider=args.include_provider,
        quiet=args.quiet,
        project_root=args.project_root,
        source_only=args.source_only,
    )


if __name__ == "__main__":
    raise SystemExit(main())
