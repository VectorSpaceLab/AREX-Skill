#!/usr/bin/env python3
"""Offline Kotaemon provider environment validator.

Reads .env-style files plus inherited environment variables, redacts secrets, and
checks provider-specific required pairs without making network calls.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

KEYWORDS_SECRET = ("KEY", "TOKEN", "SECRET", "CREDENTIAL", "PASSWORD")
PLACEHOLDER_VALUES = {
    "",
    "your-key",
    "placeholder",
    "changeme",
    "change-me",
    "dummy",
    "test",
    "none",
    "null",
    "<your_openai_key>",
    "<your openai api key here>",
    "<cohere_api_key>",
    "<your_key>",
}
TRUE_VALUES = {"1", "true", "yes", "on", "y", "t"}
FALSE_VALUES = {"0", "false", "no", "off", "n", "f"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Kotaemon provider .env settings without network calls."
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to a .env-style file. Missing default .env is allowed unless --require-env-file is set.",
    )
    parser.add_argument(
        "--settings-file",
        default=None,
        help="Optional GraphRAG settings YAML to inspect when custom GraphRAG settings are enabled.",
    )
    parser.add_argument(
        "--select",
        action="append",
        default=None,
        choices=[
            "auto",
            "openai",
            "azure",
            "local",
            "embeddings",
            "reranking",
            "web-search",
            "graphrag",
            "all",
        ],
        help="Provider group to validate. Repeat for multiple groups. Default: auto.",
    )
    parser.add_argument(
        "--docker",
        action="store_true",
        help="Warn when local provider URLs use localhost from an expected Docker container.",
    )
    parser.add_argument(
        "--require-env-file",
        action="store_true",
        help="Fail if --env-file is missing.",
    )
    return parser.parse_args()


def parse_env_file(path: Path, require: bool) -> tuple[dict[str, str], list[str]]:
    messages: list[str] = []
    values: dict[str, str] = {}
    if not path.exists():
        message = f"env file not found: {path}"
        if require:
            raise FileNotFoundError(message)
        messages.append(f"WARN {message}; using process environment only")
        return values, messages

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            messages.append(f"WARN {path}:{line_number}: ignored line without '='")
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = strip_inline_comment(raw_value.strip())
        value = strip_quotes(value)
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", key):
            messages.append(f"WARN {path}:{line_number}: ignored invalid key {key!r}")
            continue
        values[key] = value
    return values, messages


def strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
    return value


def merged_env(file_values: dict[str, str]) -> dict[str, str]:
    values = dict(os.environ)
    values.update(file_values)
    return values


def get(values: dict[str, str], key: str, default: str = "") -> str:
    return values.get(key, default).strip()


def has_value(values: dict[str, str], key: str) -> bool:
    return bool(get(values, key))


def normalize_placeholder(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def is_placeholder(value: str, *, allow_local_dummy: bool = False) -> bool:
    normalized = normalize_placeholder(value)
    if allow_local_dummy and normalized in {"dummy", "ollama"}:
        return False
    if normalized in PLACEHOLDER_VALUES:
        return True
    if normalized.startswith("<") and normalized.endswith(">"):
        return True
    if "your" in normalized and ("key" in normalized or "token" in normalized):
        return True
    return False


def bool_value(values: dict[str, str], key: str, default: bool) -> tuple[bool, str | None]:
    raw = get(values, key)
    if not raw:
        return default, None
    lowered = raw.lower()
    if lowered in TRUE_VALUES:
        return True, None
    if lowered in FALSE_VALUES:
        return False, None
    return default, f"{key}={raw!r} is not a recognized boolean"


def redact(key: str, value: str) -> str:
    if not value:
        return "<empty>"
    if any(keyword in key.upper() for keyword in KEYWORDS_SECRET):
        if len(value) <= 4:
            return "<redacted>"
        return f"{value[:2]}…{value[-2:]} ({len(value)} chars)"
    if is_placeholder(value, allow_local_dummy=True):
        return f"<placeholder:{value}>"
    return value


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    def fail(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        self.info.append(message)

    def emit(self) -> None:
        for message in self.info:
            print(f"OK   {message}")
        for message in self.warnings:
            print(f"WARN {message}")
        for message in self.errors:
            print(f"FAIL {message}")


def selected_groups(values: dict[str, str], selects: list[str] | None) -> list[str]:
    requested = selects or ["auto"]
    if "all" in requested:
        return ["openai", "azure", "local", "embeddings", "reranking", "web-search", "graphrag"]
    groups: set[str] = set(requested)
    groups.discard("auto")
    if "auto" in requested:
        auto = infer_groups(values)
        groups.update(auto or {"openai", "azure", "local", "web-search", "graphrag"})
    return sorted(groups)


def infer_groups(values: dict[str, str]) -> set[str]:
    groups: set[str] = set()
    if any(has_value(values, key) for key in ["OPENAI_API_KEY", "OPENAI_API_BASE", "OPENAI_CHAT_MODEL"]):
        groups.add("openai")
    if any(has_value(values, key) for key in ["AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_CHAT_DEPLOYMENT", "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"]):
        groups.add("azure")
    if any(has_value(values, key) for key in ["LOCAL_MODEL", "LOCAL_MODEL_EMBEDDINGS", "KH_OLLAMA_URL", "LOCAL_MODEL_PATH"]):
        groups.add("local")
    if any(has_value(values, key) for key in ["COHERE_API_KEY", "VOYAGE_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY"]):
        groups.add("embeddings")
        groups.add("reranking")
    if any(has_value(values, key) for key in ["TAVILY_API_KEY", "JINA_API_KEY", "KH_WEB_SEARCH_BACKEND"]):
        groups.add("web-search")
    if any(has_value(values, key) for key in ["GRAPHRAG_API_KEY", "USE_MS_GRAPHRAG", "USE_NANO_GRAPHRAG", "USE_LIGHTRAG", "USE_CUSTOMIZED_GRAPHRAG_SETTING"]):
        groups.add("graphrag")
    return groups


def check_required_key(
    reporter: Reporter,
    values: dict[str, str],
    key: str,
    label: str,
    *,
    allow_local_dummy: bool = False,
) -> None:
    value = get(values, key)
    if not value:
        reporter.fail(f"{label}: missing {key}")
    elif is_placeholder(value, allow_local_dummy=allow_local_dummy):
        reporter.fail(f"{label}: {key} is a placeholder ({redact(key, value)})")
    else:
        reporter.note(f"{label}: {key} set to {redact(key, value)}")


def parse_url(value: str) -> tuple[bool, str]:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False, "expected http(s) URL with host"
    return True, ""


def warn_url_shape(reporter: Reporter, key: str, value: str, expected_suffix: str | None = None) -> None:
    if not value:
        return
    ok, reason = parse_url(value)
    if not ok:
        reporter.fail(f"{key}: invalid URL {value!r}: {reason}")
        return
    if expected_suffix and not value.rstrip("/").endswith(expected_suffix.rstrip("/")):
        reporter.warn(f"{key}: expected an OpenAI-compatible URL ending in {expected_suffix!r}, got {value!r}")


def warn_docker_localhost(reporter: Reporter, key: str, value: str, docker: bool) -> None:
    if not docker or not value:
        return
    parsed = urlparse(value)
    if parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
        reporter.warn(f"{key}: {parsed.hostname} points inside the container; use host.docker.internal or container networking if the server runs on the host")


def check_openai(values: dict[str, str], reporter: Reporter) -> None:
    label = "OpenAI"
    key = get(values, "OPENAI_API_KEY")
    if key or any(has_value(values, k) for k in ["OPENAI_API_BASE", "OPENAI_CHAT_MODEL", "OPENAI_EMBEDDINGS_MODEL"]):
        check_required_key(reporter, values, "OPENAI_API_KEY", label)
    base = get(values, "OPENAI_API_BASE", "https://api.openai.com/v1") or "https://api.openai.com/v1"
    warn_url_shape(reporter, "OPENAI_API_BASE", base, "/v1")
    reporter.note(f"{label}: chat model {get(values, 'OPENAI_CHAT_MODEL', 'gpt-4o-mini') or 'gpt-4o-mini'}")
    reporter.note(f"{label}: embeddings model {get(values, 'OPENAI_EMBEDDINGS_MODEL', 'text-embedding-3-large') or 'text-embedding-3-large'}")


def check_azure(values: dict[str, str], reporter: Reporter) -> None:
    label = "Azure OpenAI"
    selected = any(
        has_value(values, key)
        for key in [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_CHAT_DEPLOYMENT",
            "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT",
        ]
    )
    if not selected:
        reporter.warn(f"{label}: no Azure values found")
        return
    check_required_key(reporter, values, "AZURE_OPENAI_ENDPOINT", label)
    check_required_key(reporter, values, "AZURE_OPENAI_API_KEY", label)
    endpoint = get(values, "AZURE_OPENAI_ENDPOINT")
    if endpoint:
        ok, reason = parse_url(endpoint)
        if not ok:
            reporter.fail(f"AZURE_OPENAI_ENDPOINT: invalid URL {endpoint!r}: {reason}")
        if "/openai/deployments" in endpoint:
            reporter.fail("AZURE_OPENAI_ENDPOINT should be the Azure resource endpoint, not a deployment URL")
    api_version = get(values, "OPENAI_API_VERSION", "2024-02-15-preview") or "2024-02-15-preview"
    reporter.note(f"{label}: API version {api_version}")
    if not get(values, "AZURE_OPENAI_CHAT_DEPLOYMENT") and not get(values, "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"):
        reporter.fail(f"{label}: set at least one deployment name for chat or embeddings")
    else:
        if get(values, "AZURE_OPENAI_CHAT_DEPLOYMENT"):
            reporter.note(f"{label}: chat deployment {get(values, 'AZURE_OPENAI_CHAT_DEPLOYMENT')}")
        else:
            reporter.warn(f"{label}: chat deployment not set; chat entry will not be seeded")
        if get(values, "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"):
            reporter.note(f"{label}: embeddings deployment {get(values, 'AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT')}")
        else:
            reporter.warn(f"{label}: embeddings deployment not set; embedding entry will not be seeded")


def check_local(values: dict[str, str], reporter: Reporter, docker: bool) -> None:
    label = "Local models"
    local_model = get(values, "LOCAL_MODEL")
    local_embeddings = get(values, "LOCAL_MODEL_EMBEDDINGS")
    ollama_url = get(values, "KH_OLLAMA_URL", "http://localhost:11434/v1/") or "http://localhost:11434/v1/"

    if local_model:
        reporter.note(f"{label}: LOCAL_MODEL={local_model}")
    else:
        reporter.warn(f"{label}: LOCAL_MODEL not set; ollama chat entry will not be seeded from .env")
    if local_embeddings:
        reporter.note(f"{label}: LOCAL_MODEL_EMBEDDINGS={local_embeddings}")
    else:
        reporter.warn(f"{label}: LOCAL_MODEL_EMBEDDINGS not set; ollama embeddings default may be used only when LOCAL_MODEL seeds local entries")

    warn_url_shape(reporter, "KH_OLLAMA_URL", ollama_url, "/v1")
    warn_docker_localhost(reporter, "KH_OLLAMA_URL", ollama_url, docker)
    if "/api" in ollama_url.rstrip("/"):
        reporter.fail("KH_OLLAMA_URL uses native Ollama /api path; ChatOpenAI/OpenAIEmbeddings entries need /v1/")

    for key in ["LOCAL_MODEL", "LOCAL_MODEL_PATH"]:
        value = get(values, key)
        if looks_like_path(value):
            path = Path(value).expanduser()
            if not path.exists():
                reporter.fail(f"{key}: local model path does not exist: {path}")
            elif path.is_dir():
                reporter.warn(f"{key}: path is a directory, not a GGUF file: {path}")
            elif path.suffix.lower() != ".gguf":
                reporter.warn(f"{key}: path exists but does not end with .gguf: {path}")
            else:
                reporter.note(f"{key}: GGUF path exists ({path.name})")


def looks_like_path(value: str) -> bool:
    if not value:
        return False
    if value.endswith(".gguf"):
        return True
    if value.startswith(("/", "./", "../", "~")):
        return True
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    return False


def check_embeddings(values: dict[str, str], reporter: Reporter) -> None:
    if has_value(values, "OPENAI_EMBEDDINGS_MODEL") or has_value(values, "OPENAI_API_KEY"):
        if get(values, "OPENAI_API_KEY"):
            check_required_key(reporter, values, "OPENAI_API_KEY", "OpenAI embeddings")
    if has_value(values, "VOYAGE_API_KEY"):
        check_required_key(reporter, values, "VOYAGE_API_KEY", "VoyageAI embeddings")
        reporter.note(f"VoyageAI embeddings: model {get(values, 'VOYAGE_EMBEDDINGS_MODEL', 'voyage-3-large') or 'voyage-3-large'}")
    if has_value(values, "COHERE_API_KEY"):
        check_required_key(reporter, values, "COHERE_API_KEY", "Cohere embeddings/reranking")
    google_key = get(values, "GOOGLE_API_KEY")
    if google_key:
        check_required_key(reporter, values, "GOOGLE_API_KEY", "Google embeddings")
    mistral_key = get(values, "MISTRAL_API_KEY")
    if mistral_key:
        check_required_key(reporter, values, "MISTRAL_API_KEY", "Mistral embeddings")


def check_reranking(values: dict[str, str], reporter: Reporter) -> None:
    cohere_key = get(values, "COHERE_API_KEY")
    voyage_key = get(values, "VOYAGE_API_KEY")
    if cohere_key:
        check_required_key(reporter, values, "COHERE_API_KEY", "Cohere reranking")
    else:
        reporter.warn("Cohere reranking: COHERE_API_KEY not set; default Cohere reranker will skip scoring")
    if voyage_key:
        check_required_key(reporter, values, "VOYAGE_API_KEY", "VoyageAI reranking")


def check_web_search(values: dict[str, str], reporter: Reporter) -> None:
    backend = get(values, "KH_WEB_SEARCH_BACKEND", "kotaemon.indices.retrievers.tavily_web_search.WebSearch")
    reporter.note(f"Web search: backend {backend}")
    backend_lower = backend.lower()
    if "jina" in backend_lower:
        check_required_key(reporter, values, "JINA_API_KEY", "Jina web search")
        jina_url = get(values, "JINA_URL", "https://r.jina.ai/") or "https://r.jina.ai/"
        warn_url_shape(reporter, "JINA_URL", jina_url)
    elif "tavily" in backend_lower:
        check_required_key(reporter, values, "TAVILY_API_KEY", "Tavily web search")
    else:
        reporter.warn("Web search: custom backend selected; validate its credentials and optional package manually")


def check_graphrag(values: dict[str, str], reporter: Reporter, settings_file: str | None) -> None:
    toggles: dict[str, bool] = {}
    for key, default in [
        ("USE_MS_GRAPHRAG", True),
        ("USE_NANO_GRAPHRAG", False),
        ("USE_LIGHTRAG", True),
        ("USE_GLOBAL_GRAPHRAG", True),
        ("USE_CUSTOMIZED_GRAPHRAG_SETTING", False),
    ]:
        value, warning = bool_value(values, key, default)
        toggles[key] = value
        if warning:
            reporter.fail(f"GraphRAG: {warning}")
        else:
            reporter.note(f"GraphRAG: {key}={str(value).lower()}")

    if not (toggles["USE_MS_GRAPHRAG"] or toggles["USE_NANO_GRAPHRAG"] or toggles["USE_LIGHTRAG"]):
        reporter.fail("GraphRAG: all graph implementations are disabled")

    if toggles["USE_MS_GRAPHRAG"]:
        check_required_key(reporter, values, "GRAPHRAG_API_KEY", "MS GraphRAG", allow_local_dummy=True)
        reporter.note(f"MS GraphRAG: LLM model {get(values, 'GRAPHRAG_LLM_MODEL', 'gpt-4o-mini') or 'gpt-4o-mini'}")
        reporter.note(f"MS GraphRAG: embedding model {get(values, 'GRAPHRAG_EMBEDDING_MODEL', 'text-embedding-3-small') or 'text-embedding-3-small'}")

    if toggles["USE_CUSTOMIZED_GRAPHRAG_SETTING"]:
        if not settings_file:
            reporter.warn("GraphRAG: custom settings enabled but --settings-file was not provided")
        else:
            inspect_graphrag_settings(Path(settings_file), reporter)


def inspect_graphrag_settings(path: Path, reporter: Reporter) -> None:
    if not path.exists():
        reporter.fail(f"GraphRAG settings file not found: {path}")
        return
    text = path.read_text(encoding="utf-8")
    reporter.note(f"GraphRAG settings: inspecting {path}")
    for dotted_key, value in extract_simple_yaml_scalars(text):
        if dotted_key in {"llm.api_base", "embeddings.llm.api_base"}:
            warn_url_shape(reporter, f"settings.yaml:{dotted_key}", value, "/v1")
        if dotted_key in {"llm.api_key", "embeddings.llm.api_key"}:
            if is_placeholder(value, allow_local_dummy=True):
                reporter.warn(f"settings.yaml:{dotted_key} appears placeholder-like ({redact(dotted_key, value)})")
            else:
                reporter.note(f"settings.yaml:{dotted_key} set to {redact(dotted_key, value)}")


def extract_simple_yaml_scalars(text: str) -> Iterable[tuple[str, str]]:
    stack: list[tuple[int, str]] = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = raw_line.strip()
        if ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip().strip('"\'')
        value = strip_inline_comment(value.strip())
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not value:
            stack.append((indent, key))
            continue
        value = strip_quotes(value)
        dotted = ".".join([item[1] for item in stack] + [key])
        yield dotted, value


def main() -> int:
    args = parse_args()
    reporter = Reporter()
    try:
        file_values, parse_messages = parse_env_file(Path(args.env_file), args.require_env_file)
    except OSError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    for message in parse_messages:
        reporter.warn(message.removeprefix("WARN "))
    values = merged_env(file_values)
    groups = selected_groups(values, args.select)
    reporter.note(f"Selected groups: {', '.join(groups)}")

    if "openai" in groups:
        check_openai(values, reporter)
    if "azure" in groups:
        check_azure(values, reporter)
    if "local" in groups:
        check_local(values, reporter, args.docker)
    if "embeddings" in groups:
        check_embeddings(values, reporter)
    if "reranking" in groups:
        check_reranking(values, reporter)
    if "web-search" in groups:
        check_web_search(values, reporter)
    if "graphrag" in groups:
        check_graphrag(values, reporter, args.settings_file)

    reporter.emit()
    if reporter.errors:
        print(f"\nProvider env check failed with {len(reporter.errors)} issue(s).", file=sys.stderr)
        return 1
    print("\nProvider env check passed without blocking offline issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
