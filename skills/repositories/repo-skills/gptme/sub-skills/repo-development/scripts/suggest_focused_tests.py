#!/usr/bin/env python3
"""Map changed paths to focused pytest and Web UI commands."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Suggestion:
    command: str
    reason: str
    paths: tuple[str, ...]
    priority: int = 100


@dataclass
class SuggestionAccumulator:
    reasons: list[str]
    paths: list[str]
    priority: int


WEBUI_SPEC_SUFFIX = ".spec.ts"


SERVER_RULES: dict[str, tuple[Suggestion, ...]] = {
    "a2a_api": (
        Suggestion(
            "pytest tests/test_server_a2a.py -q -m 'not slow and not requires_api'",
            "A2A server API changed.",
            (),
            20,
        ),
    ),
    "api_v2": (
        Suggestion(
            "pytest tests/test_server_v2.py -q -m 'not slow and not requires_api'",
            "v2 API surface changed.",
            (),
            20,
        ),
    ),
    "api_v2_common": (
        Suggestion(
            "pytest tests/test_server_api_v2_common.py tests/test_server_v2.py -q -m 'not slow and not requires_api'",
            "Shared v2 request/response helpers changed.",
            (),
            10,
        ),
        Suggestion(
            "cd webui && npm test",
            "Shared v2 message shape can affect the frontend.",
            (),
            30,
        ),
    ),
    "api_v2_agents": (
        Suggestion(
            "pytest tests/test_server_v2_agents.py -q -m 'not slow and not requires_api'",
            "v2 agent endpoints changed.",
            (),
            20,
        ),
    ),
    "api_v2_sessions": (
        Suggestion(
            "pytest tests/test_server_v2_sessions.py tests/test_server_v2_sse.py tests/test_server_v2_auto_stepping.py -q -m 'not slow and not requires_api'",
            "Session and SSE behavior changed.",
            (),
            10,
        ),
        Suggestion(
            "cd webui && npm test",
            "Session event shape is consumed by the frontend.",
            (),
            30,
        ),
    ),
    "app": (
        Suggestion(
            "pytest tests/test_server.py tests/test_server_webui_dir.py tests/test_webui_redirects.py tests/test_server_cors.py tests/test_server_host_validation.py -q -m 'not slow and not requires_api'",
            "Server app wiring or served static assets changed.",
            (),
            10,
        ),
        Suggestion(
            "cd webui && npm test",
            "The served UI surface can affect frontend integration.",
            (),
            30,
        ),
    ),
    "artifacts_api": (
        Suggestion(
            "pytest tests/test_server_artifacts.py -q -m 'not slow and not requires_api'",
            "Artifact serving changed.",
            (),
            20,
        ),
    ),
    "auth": (
        Suggestion(
            "pytest tests/test_server_auth.py tests/test_server_cors.py tests/test_server_host_validation.py -q -m 'not slow and not requires_api'",
            "Server auth or host validation changed.",
            (),
            20,
        ),
    ),
    "cli": (
        Suggestion(
            "pytest tests/test_server_cli_fallback.py tests/test_server_cli_tools.py tests/test_server.py -q -m 'not slow and not requires_api'",
            "Server CLI entrypoint changed.",
            (),
            20,
        ),
    ),
    "client": (
        Suggestion(
            "pytest tests/test_server_client.py -q -m 'not slow and not requires_api'",
            "Server API client changed.",
            (),
            20,
        ),
        Suggestion(
            "cd webui && npm test",
            "API client changes can affect frontend-backed flows.",
            (),
            40,
        ),
    ),
    "computer_api": (
        Suggestion(
            "pytest tests/test_computer_api.py tests/test_computer_docker_config.py -q -m 'not slow and not requires_api'",
            "Computer-use API changed.",
            (),
            30,
        ),
    ),
    "external_sessions": (
        Suggestion(
            "pytest tests/test_external_sessions.py tests/test_server_parent_death_watcher.py -q -m 'not slow and not requires_api'",
            "External session lifecycle changed.",
            (),
            20,
        ),
    ),
    "metrics": (
        Suggestion(
            "pytest tests/test_server_metrics.py -q -m 'not slow and not requires_api'",
            "Server metrics changed.",
            (),
            20,
        ),
    ),
    "openapi_docs": (
        Suggestion(
            "make check-openapi",
            "OpenAPI documentation or route wiring changed.",
            (),
            10,
        ),
    ),
    "panels_api": (
        Suggestion(
            "pytest tests/test_server_panels.py -q -m 'not slow and not requires_api'",
            "Panel API changed.",
            (),
            20,
        ),
    ),
    "session_models": (
        Suggestion(
            "pytest tests/test_server_session_models.py -q -m 'not slow and not requires_api'",
            "Session model shape changed.",
            (),
            20,
        ),
    ),
    "session_step": (
        Suggestion(
            "pytest tests/test_server_v2_auto_stepping.py tests/test_server_v2_sessions.py tests/test_server_v2_sse.py -q -m 'not slow and not requires_api'",
            "Session step orchestration changed.",
            (),
            15,
        ),
        Suggestion(
            "cd webui && npm test",
            "Step flow feeds the frontend conversation view.",
            (),
            35,
        ),
    ),
    "skills_api": (
        Suggestion(
            "pytest tests/test_server_skills_api.py -q -m 'not slow and not requires_api'",
            "Skills API changed.",
            (),
            20,
        ),
    ),
    "tasks_api": (
        Suggestion(
            "pytest tests/test_tasks_api.py -q -m 'not slow and not requires_api'",
            "Task API changed.",
            (),
            20,
        ),
    ),
    "tools_api": (
        Suggestion(
            "pytest tests/test_server_tools_query.py -q -m 'not slow and not requires_api'",
            "Tools query API changed.",
            (),
            20,
        ),
    ),
    "tts_api": (
        Suggestion(
            "pytest tests/test_server_tts_api.py -q -m 'not slow and not requires_api'",
            "TTS API changed.",
            (),
            20,
        ),
    ),
    "workspace_api": (
        Suggestion(
            "pytest tests/test_workspace_api.py tests/test_server_workspace.py -q -m 'not slow and not requires_api'",
            "Workspace API changed.",
            (),
            20,
        ),
        Suggestion(
            "cd webui && npm test",
            "Workspace shape is visible to the frontend.",
            (),
            40,
        ),
    ),
}


FAMILY_RULES: tuple[tuple[tuple[str, ...], tuple[Suggestion, ...]], ...] = (
    (
        ("gptme/cli/", "gptme/chat.py", "gptme/logmanager/", "gptme/message.py", "gptme/agent/", "gptme/commands/"),
        (
            Suggestion(
                "pytest tests/test_cli.py tests/test_commands*.py tests/test_chats*.py tests/test_agent*.py tests/test_logmanager.py tests/test_message*.py -q -m 'not slow and not requires_api'",
                "CLI / conversation / agent code changed.",
                (),
                40,
            ),
        ),
    ),
    (
        ("gptme/config/", "gptme/credentials.py", "gptme/llm/", "gptme/oauth/"),
        (
            Suggestion(
                "pytest tests/test_config*.py tests/test_credentials*.py tests/test_custom_providers.py tests/test_llm*.py tests/test_oauth_openrouter.py -q -m 'not slow and not requires_api'",
                "Config, credentials, or provider code changed.",
                (),
                40,
            ),
        ),
    ),
    (
        ("gptme/tools/", "gptme/hooks/", "gptme/plugins/", "gptme/lessons/", "gptme/mcp/"),
        (
            Suggestion(
                "pytest tests/test_tools*.py tests/test_plugins.py tests/test_hooks*.py tests/test_lessons*.py tests/test_mcp*.py -q -m 'not slow and not requires_api'",
                "Tools or extensibility code changed.",
                (),
                50,
            ),
        ),
    ),
    (
        ("gptme/tui/",),
        (
            Suggestion(
                "pytest tests/test_tui.py tests/test_tui_visual.py -q -m 'not slow and not requires_api'",
                "TUI code changed.",
                (),
                50,
            ),
        ),
    ),
    (
        ("gptme/acp/",),
        (
            Suggestion(
                "pytest tests/test_acp*.py -q -m 'not slow and not requires_api'",
                "ACP code changed.",
                (),
                45,
            ),
        ),
    ),
)


WEBUI_CONFIG_NAMES = {
    "components.json",
    "eslint.config.js",
    "jest.config.ts",
    "playwright.config.ts",
    "postcss.config.js",
    "prettier.config.cjs",
    "tailwind.config.ts",
    "tsconfig.app.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "tsconfig.test.json",
    "vite.config.ts",
    "wrangler.toml",
    "package.json",
    "package-lock.json",
}

WEBUI_BUILD_TRIGGER_NAMES = {
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "wrangler.toml",
}


def normalize_path(raw: str) -> str:
    cleaned = raw.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def expand_inputs(inputs: list[str], root: Path) -> list[str]:
    if not inputs:
        if sys.stdin.isatty():
            raise SystemExit("error: provide changed paths as arguments or via stdin")
        inputs = [line.strip() for line in sys.stdin if line.strip()]

    expanded: list[str] = []
    for raw in inputs:
        path = root / raw
        normalized = normalize_path(raw)
        if normalized in {".", ""}:
            expanded.append(normalized)
            continue
        if path.is_dir() and normalized not in {".", "./"}:
            for child in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
                expanded.append(child.relative_to(root).as_posix())
            continue
        expanded.append(normalized)
    return expanded


def exact_test_file(root: Path, source: str) -> str | None:
    source_path = Path(source)
    stem = source_path.stem
    if not stem:
        return None

    candidates = [
        root / "tests" / f"test_{stem}.py",
        root / "tests" / f"test_{stem}.pyi",
        root / "tests" / f"test_{stem}.sh",
    ]
    if source.startswith("webui/src/"):
        candidates.append(
            root
            / "webui"
            / "src"
            / source_path.parent.relative_to("webui/src")
            / "__tests__"
            / f"{stem}.test.tsx"
        )
    for candidate in candidates:
        if candidate.exists():
            return candidate.relative_to(root).as_posix()

    if source.startswith("webui/src/"):
        base = source_path.name.rsplit(".", 1)[0]
        webui_dir = root / "webui" / "src"
        matches = []
        for pattern in (
            f"**/__tests__/{base}.test.tsx",
            f"**/__tests__/{base}.test.ts",
            f"**/{base}.test.tsx",
            f"**/{base}.test.ts",
            f"**/{base}.test.jsx",
            f"**/{base}.test.js",
        ):
            matches.extend(sorted(webui_dir.glob(pattern)))
        for candidate in matches:
            if candidate.is_file():
                return candidate.relative_to(root).as_posix()
    return None


def server_suggestions(path: str) -> tuple[Suggestion, ...]:
    stem = Path(path).stem
    if stem in SERVER_RULES:
        return SERVER_RULES[stem]

    if stem == "__main__":
        return (
            Suggestion(
                "pytest tests/test_server*.py -q -m 'not slow and not requires_api'",
                "Server entrypoint changed.",
                (),
                30,
            ),
        )

    if stem in {"app", "auth", "client", "metrics", "panels_api", "session_models", "tools_api", "workspace_api"}:
        return SERVER_RULES.get(stem, ())

    return (
        Suggestion(
            "pytest tests/test_server*.py -q -m 'not slow and not requires_api'",
            "Server code changed.",
            (),
            60,
        ),
    )


def webui_suggestions(path: str, root: Path) -> tuple[Suggestion, ...]:
    rel = Path(path)
    if path.startswith("webui/e2e/") and path.endswith(WEBUI_SPEC_SUFFIX):
        return (
            Suggestion(
                f"cd webui && npm run test:e2e -- {rel.as_posix().removeprefix('webui/')} ".rstrip(),
                "Playwright spec changed.",
                (),
                10,
            ),
        )

    if path.startswith("webui/src/"):
        commands: list[Suggestion] = []
        test_file = exact_test_file(root, path)
        if test_file:
            commands.append(
                Suggestion(
                    f"cd webui && npm test -- {test_file.removeprefix('webui/')} ".rstrip(),
                    "Matching Jest test found.",
                    (),
                    10,
                )
            )
        else:
            commands.append(
                Suggestion(
                    "cd webui && npm test",
                    "Frontend source changed but no co-located test file was found.",
                    (),
                    40,
                )
            )
        commands.append(
            Suggestion(
                "cd webui && npm run typecheck",
                "TypeScript source changed.",
                (),
                20,
            )
        )
        if path.endswith((".css", ".html", ".json", ".js", ".cjs", ".mjs")) or Path(path).name in WEBUI_CONFIG_NAMES:
            commands.append(
                Suggestion(
                    "cd webui && npm run lint",
                    "Frontend layout or config changed.",
                    (),
                    30,
                )
            )
        return tuple(commands)

    if Path(path).name in WEBUI_CONFIG_NAMES:
        commands = [
            Suggestion("cd webui && npm run typecheck", "Frontend config changed.", (), 20),
            Suggestion("cd webui && npm run lint", "Frontend config changed.", (), 20),
        ]
        if Path(path).name in WEBUI_BUILD_TRIGGER_NAMES:
            commands.append(
                Suggestion("cd webui && npm run build", "Build inputs changed.", (), 15)
            )
        if Path(path).name in {"package.json", "package-lock.json"}:
            commands.append(Suggestion("cd webui && npm test", "Dependency or script metadata changed.", (), 25))
        return tuple(commands)

    if path.startswith("webui/"):
        return (
            Suggestion(
                "cd webui && npm run typecheck",
                "Web UI code changed.",
                (),
                40,
            ),
            Suggestion(
                "cd webui && npm test",
                "Web UI code changed.",
                (),
                45,
            ),
        )

    return ()


def source_suggestions(path: str, root: Path) -> tuple[Suggestion, ...]:
    if path.startswith("gptme/server/"):
        return server_suggestions(path)

    if path.startswith("gptme/acp/"):
        return FAMILY_RULES[-1][1]  # ACP family

    for prefixes, suggestions in FAMILY_RULES:
        if any(path.startswith(prefix) for prefix in prefixes):
            return suggestions

    stem = Path(path).stem
    if path.startswith("gptme/") and stem:
        exact = exact_test_file(root, path)
        if exact:
            return (
                Suggestion(
                    f"pytest {exact} -q",
                    "Matching test file found.",
                    (),
                    10,
                ),
            )

    return ()


def metadata_suggestions(path: str) -> tuple[Suggestion, ...]:
    if path in {"pyproject.toml", "poetry.lock", ".pre-commit-config.yaml"}:
        return (
            Suggestion(
                "python scripts/check_python_project_health.py",
                "Project metadata or lockfile changed.",
                (),
                10,
            ),
        )

    if path == "Makefile" or path.startswith(".github/workflows/"):
        return (
            Suggestion(
                "python scripts/check_python_project_health.py",
                "Build or release policy changed.",
                (),
                10,
            ),
        )

    if path.startswith("docs/") and path.endswith(".rst"):
        return (
            Suggestion(
                "python scripts/check_rst_patterns.py docs/",
                "RST formatting may have changed.",
                (),
                10,
            ),
            Suggestion(
                "make docs",
                "Full docs build when needed.",
                (),
                40,
            ),
        )

    if path.startswith(("webui/dist/", "gptme/server/webui-dist/", "scripts/validate_release_package.py", "scripts/build_changelog.py", "scripts/bump_version.sh")):
        return (
            Suggestion(
                "python scripts/check_release_package_contents.py dist/*.whl dist/*.tar.gz",
                "Release/package contents changed.",
                (),
                10,
            ),
        )

    if path in {"webui/package.json", "webui/package-lock.json", "webui/vite.config.ts", "webui/tsconfig.json", "webui/tsconfig.app.json", "webui/tsconfig.node.json", "webui/tsconfig.test.json", "webui/jest.config.ts", "webui/playwright.config.ts", "webui/eslint.config.js", "webui/postcss.config.js", "webui/prettier.config.cjs", "webui/tailwind.config.ts", "webui/components.json", "webui/README.md"}:
        return webui_suggestions(path, Path("."))

    return ()


def test_file_suggestions(path: str, root: Path) -> tuple[Suggestion, ...]:
    if path.startswith("tests/") and path.endswith(".py"):
        return (
            Suggestion(
                f"pytest {path} -q",
                "Changed test file.",
                (),
                5,
            ),
        )

    if path.startswith("tests/") and path.endswith(".sh"):
        return (
            Suggestion(
                f"bash {path}",
                "Changed shell test helper.",
                (),
                5,
            ),
        )

    if path.startswith("webui/src/") and (
        "/__tests__/" in path or path.endswith((".test.ts", ".test.tsx", ".test.js", ".test.jsx"))
    ):
        return (
            Suggestion(
                f"cd webui && npm test -- {path.removeprefix('webui/')} ".rstrip(),
                "Changed Web UI unit test file.",
                (),
                5,
            ),
        )

    if path.startswith("webui/e2e/") and path.endswith(WEBUI_SPEC_SUFFIX):
        return (
            Suggestion(
                f"cd webui && npm run test:e2e -- {path.removeprefix('webui/')} ".rstrip(),
                "Changed Playwright spec.",
                (),
                5,
            ),
        )

    return ()



def collect_suggestions(paths: list[str], root: Path) -> list[Suggestion]:
    collected: list[Suggestion] = []
    for path in paths:
        suggestions = (
            test_file_suggestions(path, root)
            or metadata_suggestions(path)
            or webui_suggestions(path, root)
            or source_suggestions(path, root)
        )
        collected.extend(
            Suggestion(command=s.command, reason=s.reason, paths=(path,), priority=s.priority)
            for s in suggestions
        )
    return suppress_redundant_broad_webui_test(merge_suggestions(collected))


def suppress_redundant_broad_webui_test(suggestions: list[Suggestion]) -> list[Suggestion]:
    has_exact_webui_test = any(
        suggestion.command.startswith("cd webui && npm test -- ")
        for suggestion in suggestions
    )
    if not has_exact_webui_test:
        return suggestions
    return [
        suggestion
        for suggestion in suggestions
        if suggestion.command != "cd webui && npm test"
    ]


def merge_suggestions(suggestions: Iterable[Suggestion]) -> list[Suggestion]:
    merged: dict[str, SuggestionAccumulator] = {}
    for suggestion in suggestions:
        bucket = merged.setdefault(
            suggestion.command,
            SuggestionAccumulator(reasons=[], paths=[], priority=suggestion.priority),
        )
        if suggestion.reason not in bucket.reasons:
            bucket.reasons.append(suggestion.reason)
        for path in suggestion.paths:
            if path not in bucket.paths:
                bucket.paths.append(path)
        bucket.priority = min(bucket.priority, suggestion.priority)

    rendered = [
        Suggestion(
            command=command,
            reason="; ".join(bucket.reasons),
            paths=tuple(bucket.paths),
            priority=bucket.priority,
        )
        for command, bucket in merged.items()
    ]
    return sorted(rendered, key=lambda item: (item.priority, item.command))


def render_text(paths: list[str], suggestions: list[Suggestion]) -> str:
    lines = ["Changed paths:"]
    for path in paths:
        lines.append(f"- {path}")

    if not suggestions:
        lines.append("\nNo focused command matched these paths.")
        return "\n".join(lines)

    lines.append("\nSuggested commands:")
    for index, suggestion in enumerate(suggestions, start=1):
        lines.append(f"{index}. {suggestion.command}")
        lines.append(f"   why: {suggestion.reason}")
        lines.append(f"   from: {', '.join(suggestion.paths)}")
    return "\n".join(lines)


def render_json(paths: list[str], suggestions: list[Suggestion]) -> str:
    payload = {
        "paths": paths,
        "suggestions": [
            {
                "command": suggestion.command,
                "reason": suggestion.reason,
                "paths": list(suggestion.paths),
                "priority": suggestion.priority,
            }
            for suggestion in suggestions
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        help="Changed files or directories. If omitted, read newline-delimited paths from stdin.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="Repository root to use when searching for matching tests.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    raw_paths = expand_inputs(args.paths, root)
    normalized_paths = [normalize_path(path) for path in raw_paths if path]
    suggestions = collect_suggestions(normalized_paths, root)

    if args.format == "json":
        print(render_json(normalized_paths, suggestions))
    else:
        print(render_text(normalized_paths, suggestions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
