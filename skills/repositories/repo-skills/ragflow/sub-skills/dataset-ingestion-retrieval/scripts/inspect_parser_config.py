#!/usr/bin/env python3
"""Offline parser_config inspector for RAGFlow dataset/document ingestion.

This helper validates the shape of a JSON parser_config file and prints warnings
for common dataset/document/chunk ingestion mismatches. It does not import
RAGFlow, open network connections, or modify files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DATASET_CHUNK_METHODS = {
    "naive",
    "book",
    "email",
    "laws",
    "manual",
    "one",
    "paper",
    "picture",
    "presentation",
    "qa",
    "table",
    "tag",
    "resume",
}

DOCUMENT_EXTRA_CHUNK_METHODS = {"knowledge_graph"}
KNOWN_CHUNK_METHODS = DATASET_CHUNK_METHODS | DOCUMENT_EXTRA_CHUNK_METHODS | {"general"}

METHODS_WITH_DISABLED_AUX_DEFAULTS = {
    "qa",
    "manual",
    "paper",
    "book",
    "laws",
    "presentation",
}

KNOWN_TOP_LEVEL_KEYS = {
    "layout_recognize",
    "chunk_token_num",
    "delimiter",
    "auto_keywords",
    "auto_questions",
    "html4excel",
    "filename_embd_weight",
    "topn_tags",
    "tag_kb_ids",
    "task_page_size",
    "pages",
    "table_context_size",
    "image_context_size",
    "parent_child",
    "children_delimiter",
    "enable_children",
    "toc_extraction",
    "enable_metadata",
    "metadata",
    "built_in_metadata",
    "llm_id",
    "raptor",
    "graphrag",
    "ext",
    "field_map",
    "entity_types",
}

KNOWN_RAPTOR_KEYS = {
    "use_raptor",
    "prompt",
    "max_token",
    "threshold",
    "max_cluster",
    "random_seed",
    "scope",
    "clustering_method",
    "tree_builder",
    "ext",
}

KNOWN_RAPTOR_EXT_KEYS = {
    "psi_exact_max_leaves",
    "psi_bucket_size",
}

KNOWN_GRAPHRAG_KEYS = {
    "use_graphrag",
    "entity_types",
    "method",
    "resolution",
    "community",
    "batch_chunk_token_size",
    "retry_attempts",
    "retry_backoff_seconds",
    "retry_backoff_max_seconds",
    "build_subgraph_retry_attempts",
    "merge_retry_attempts",
    "resolution_retry_attempts",
    "community_retry_attempts",
    "build_subgraph_timeout_per_chunk_seconds",
    "build_subgraph_min_timeout_seconds",
    "merge_timeout_seconds",
    "resolution_timeout_seconds",
    "community_timeout_seconds",
    "lock_acquire_timeout_seconds",
}

GRAPHRAG_METHODS = {"light", "general", "ner"}
RAPTOR_SCOPES = {"file", "dataset"}
RAPTOR_CLUSTERING_METHODS = {"gmm", "kmeans"}

PDF_EXTS = {".pdf"}
SPREADSHEET_EXTS = {".xls", ".xlsx", ".csv"}
PRESENTATION_EXTS = {".ppt", ".pptx", ".pages"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".tif", ".tiff", ".bmp", ".webp"}
EMAIL_EXTS = {".eml", ".msg"}
AUDIO_EXTS = {".wav", ".mp3", ".aac", ".flac", ".ogg", ".aiff", ".au"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a RAGFlow parser_config JSON file offline and print "
            "warnings for common ingestion/retrieval mismatches."
        )
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a JSON parser_config file.",
    )
    parser.add_argument(
        "--chunk-method",
        default=None,
        help="Optional public chunk_method/parser_id to check against the config.",
    )
    parser.add_argument(
        "--document-name",
        default=None,
        help="Optional document filename used for extension compatibility hints.",
    )
    parser.add_argument(
        "--strict-unknown-keys",
        action="store_true",
        help="Return a nonzero exit code when unknown top-level or nested keys are present.",
    )
    return parser.parse_args()


def load_json(path: str) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    file_path = Path(path)
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"config file not found: {path}"]
    except json.JSONDecodeError as exc:
        return None, [f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"]
    except OSError as exc:
        return None, [f"could not read config file: {exc}"]

    if not isinstance(payload, dict):
        errors.append("parser_config must be a JSON object")
        return None, errors
    return payload, errors


def type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def add_type_warning(messages: list[str], key: str, value: Any, expected: str) -> None:
    messages.append(f"{key} should be {expected}; got {type_name(value)}")


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def check_range(
    warnings: list[str],
    key: str,
    value: Any,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    integer: bool = False,
) -> None:
    if integer and (not isinstance(value, int) or isinstance(value, bool)):
        add_type_warning(warnings, key, value, "an integer")
        return
    if not integer and not is_number(value):
        add_type_warning(warnings, key, value, "a number")
        return
    if minimum is not None and value < minimum:
        warnings.append(f"{key} should be >= {minimum}; got {value}")
    if maximum is not None and value > maximum:
        warnings.append(f"{key} should be <= {maximum}; got {value}")


def check_pages(warnings: list[str], value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, list):
        add_type_warning(warnings, "pages", value, "an array of [from, to] ranges or null")
        return
    for index, item in enumerate(value):
        if not isinstance(item, list) or len(item) != 2 or not all(isinstance(v, int) and not isinstance(v, bool) for v in item):
            warnings.append(f"pages[{index}] should be a two-integer array")
            continue
        if item[0] < 1:
            warnings.append(f"pages[{index}] starts before page 1")
        if item[1] < item[0]:
            warnings.append(f"pages[{index}] ends before it starts")


def check_metadata(warnings: list[str], key: str, value: Any) -> None:
    if value in (None, [], {}):
        return
    if isinstance(value, dict):
        if value.get("type") and value.get("type") != "object":
            warnings.append(f"{key}.type is usually 'object' for JSON-schema metadata")
        if "properties" in value and not isinstance(value["properties"], dict):
            warnings.append(f"{key}.properties should be an object when present")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            if not isinstance(item, dict):
                warnings.append(f"{key}[{index}] should be an object")
                continue
            if not item.get("name"):
                warnings.append(f"{key}[{index}] should include a non-empty name")
        return
    add_type_warning(warnings, key, value, "an object, array, or empty value")


def inspect_parent_child(config: dict[str, Any], warnings: list[str]) -> None:
    parent_child = config.get("parent_child")
    if parent_child is None:
        return
    if not isinstance(parent_child, dict):
        add_type_warning(warnings, "parent_child", parent_child, "an object")
        return

    use_parent_child = parent_child.get("use_parent_child")
    if use_parent_child is not None and not isinstance(use_parent_child, bool):
        add_type_warning(warnings, "parent_child.use_parent_child", use_parent_child, "a boolean")
    children_delimiter = parent_child.get("children_delimiter")
    if children_delimiter is not None and not isinstance(children_delimiter, str):
        add_type_warning(warnings, "parent_child.children_delimiter", children_delimiter, "a string")

    if parent_child.get("use_parent_child"):
        if not parent_child.get("children_delimiter"):
            warnings.append("parent_child is enabled but children_delimiter is empty")
        if config.get("children_delimiter") in (None, ""):
            warnings.append("parent_child is enabled; dataset update should flatten children_delimiter for execution")
        if config.get("enable_children") is not True:
            warnings.append("parent_child is enabled; execution config should include enable_children=true")


def inspect_raptor(config: dict[str, Any], warnings: list[str], unknowns: list[str]) -> None:
    raptor = config.get("raptor")
    if raptor is None:
        return
    if not isinstance(raptor, dict):
        add_type_warning(warnings, "raptor", raptor, "an object")
        return

    for key in sorted(set(raptor) - KNOWN_RAPTOR_KEYS):
        unknowns.append(f"raptor.{key}")

    if "use_raptor" in raptor and not isinstance(raptor["use_raptor"], bool):
        add_type_warning(warnings, "raptor.use_raptor", raptor["use_raptor"], "a boolean")
    if raptor.get("use_raptor"):
        if not raptor.get("prompt"):
            warnings.append("raptor.use_raptor is true but raptor.prompt is empty")
        if "max_token" in raptor:
            check_range(warnings, "raptor.max_token", raptor["max_token"], minimum=1, maximum=2048, integer=True)
        if "threshold" in raptor:
            check_range(warnings, "raptor.threshold", raptor["threshold"], minimum=0.0, maximum=1.0)
        if "max_cluster" in raptor:
            check_range(warnings, "raptor.max_cluster", raptor["max_cluster"], minimum=1, integer=True)
        if "random_seed" in raptor and not isinstance(raptor["random_seed"], int):
            add_type_warning(warnings, "raptor.random_seed", raptor["random_seed"], "an integer")
        scope = raptor.get("scope")
        if scope is not None and scope not in RAPTOR_SCOPES:
            warnings.append(f"raptor.scope is usually one of {sorted(RAPTOR_SCOPES)}; got {scope!r}")
        clustering = raptor.get("clustering_method")
        if clustering is not None and clustering not in RAPTOR_CLUSTERING_METHODS:
            warnings.append(f"raptor.clustering_method is usually one of {sorted(RAPTOR_CLUSTERING_METHODS)}; got {clustering!r}")
        ext = raptor.get("ext")
        if ext is not None:
            if not isinstance(ext, dict):
                add_type_warning(warnings, "raptor.ext", ext, "an object")
            else:
                for key in sorted(set(ext) - KNOWN_RAPTOR_EXT_KEYS):
                    unknowns.append(f"raptor.ext.{key}")


def inspect_graphrag(config: dict[str, Any], warnings: list[str], unknowns: list[str]) -> None:
    graphrag = config.get("graphrag")
    if graphrag is None:
        return
    if not isinstance(graphrag, dict):
        add_type_warning(warnings, "graphrag", graphrag, "an object")
        return

    for key in sorted(set(graphrag) - KNOWN_GRAPHRAG_KEYS):
        unknowns.append(f"graphrag.{key}")

    if "use_graphrag" in graphrag and not isinstance(graphrag["use_graphrag"], bool):
        add_type_warning(warnings, "graphrag.use_graphrag", graphrag["use_graphrag"], "a boolean")
    if graphrag.get("use_graphrag"):
        method = graphrag.get("method", "light")
        if method not in GRAPHRAG_METHODS:
            warnings.append(f"graphrag.method must be one of {sorted(GRAPHRAG_METHODS)}; got {method!r}")
        entity_types = graphrag.get("entity_types")
        if not isinstance(entity_types, list) or not all(isinstance(item, str) and item.strip() for item in entity_types):
            warnings.append("graphrag.entity_types should be a non-empty array of strings when GraphRAG is enabled")
        for key in ("resolution", "community"):
            if key in graphrag and not isinstance(graphrag[key], bool):
                add_type_warning(warnings, f"graphrag.{key}", graphrag[key], "a boolean")
        for key in (
            "batch_chunk_token_size",
            "retry_attempts",
            "build_subgraph_retry_attempts",
            "merge_retry_attempts",
            "resolution_retry_attempts",
            "community_retry_attempts",
            "build_subgraph_timeout_per_chunk_seconds",
            "build_subgraph_min_timeout_seconds",
            "merge_timeout_seconds",
            "resolution_timeout_seconds",
            "community_timeout_seconds",
            "lock_acquire_timeout_seconds",
        ):
            if key in graphrag:
                check_range(warnings, f"graphrag.{key}", graphrag[key], minimum=0, integer=True)
        for key in ("retry_backoff_seconds", "retry_backoff_max_seconds"):
            if key in graphrag:
                check_range(warnings, f"graphrag.{key}", graphrag[key], minimum=0.0)


def inspect_top_level(config: dict[str, Any], warnings: list[str], unknowns: list[str]) -> None:
    for key in sorted(set(config) - KNOWN_TOP_LEVEL_KEYS):
        unknowns.append(key)

    if "chunk_token_num" in config:
        check_range(warnings, "chunk_token_num", config["chunk_token_num"], minimum=1, maximum=2048, integer=True)
    if "delimiter" in config and not isinstance(config["delimiter"], str):
        add_type_warning(warnings, "delimiter", config["delimiter"], "a string")
    if "auto_keywords" in config:
        check_range(warnings, "auto_keywords", config["auto_keywords"], minimum=0, maximum=32, integer=True)
    if "auto_questions" in config:
        check_range(warnings, "auto_questions", config["auto_questions"], minimum=0, maximum=10, integer=True)
    if "html4excel" in config and not isinstance(config["html4excel"], bool):
        add_type_warning(warnings, "html4excel", config["html4excel"], "a boolean")
    if "filename_embd_weight" in config:
        check_range(warnings, "filename_embd_weight", config["filename_embd_weight"], minimum=0.0, maximum=1.0)
    if "topn_tags" in config:
        check_range(warnings, "topn_tags", config["topn_tags"], minimum=1, maximum=10, integer=True)
    if "tag_kb_ids" in config:
        tag_kb_ids = config["tag_kb_ids"]
        if not isinstance(tag_kb_ids, list) or not all(isinstance(item, str) for item in tag_kb_ids):
            add_type_warning(warnings, "tag_kb_ids", tag_kb_ids, "an array of strings")
    if "task_page_size" in config and config["task_page_size"] is not None:
        check_range(warnings, "task_page_size", config["task_page_size"], minimum=1, integer=True)
    if "pages" in config:
        check_pages(warnings, config["pages"])
    if "table_context_size" in config:
        check_range(warnings, "table_context_size", config["table_context_size"], minimum=0.0)
    if "image_context_size" in config:
        check_range(warnings, "image_context_size", config["image_context_size"], minimum=0.0)
    if "enable_children" in config and not isinstance(config["enable_children"], bool):
        add_type_warning(warnings, "enable_children", config["enable_children"], "a boolean")
    if "children_delimiter" in config and not isinstance(config["children_delimiter"], str):
        add_type_warning(warnings, "children_delimiter", config["children_delimiter"], "a string")
    if "toc_extraction" in config and not isinstance(config["toc_extraction"], bool):
        add_type_warning(warnings, "toc_extraction", config["toc_extraction"], "a boolean")
    if "enable_metadata" in config and not isinstance(config["enable_metadata"], bool):
        add_type_warning(warnings, "enable_metadata", config["enable_metadata"], "a boolean")
    if config.get("enable_metadata") and not config.get("metadata") and not config.get("built_in_metadata"):
        warnings.append("enable_metadata is true but metadata/built_in_metadata rules are empty")
    if "metadata" in config:
        check_metadata(warnings, "metadata", config["metadata"])
    if "built_in_metadata" in config:
        check_metadata(warnings, "built_in_metadata", config["built_in_metadata"])
    if "llm_id" in config and config["llm_id"] is not None and not isinstance(config["llm_id"], str):
        add_type_warning(warnings, "llm_id", config["llm_id"], "a string")
    if "ext" in config and not isinstance(config["ext"], dict):
        add_type_warning(warnings, "ext", config["ext"], "an object")


def inspect_method(chunk_method: str | None, config: dict[str, Any], warnings: list[str]) -> None:
    if not chunk_method:
        return
    method = chunk_method.strip().lower()
    if method not in KNOWN_CHUNK_METHODS:
        warnings.append(f"unknown chunk_method {chunk_method!r}; update validation and parser factory together if this is new")
        return
    if method == "general":
        warnings.append("chunk_method 'general' is an internal alias; public dataset APIs usually use 'naive'")
    if method in DOCUMENT_EXTRA_CHUNK_METHODS:
        warnings.append(f"chunk_method {method!r} is accepted on document update but not normal dataset create/update validation")
    if method in METHODS_WITH_DISABLED_AUX_DEFAULTS:
        if config.get("raptor", {}).get("use_raptor"):
            warnings.append(f"{method} usually disables RAPTOR by default; confirm this explicit enablement is intended")
        if config.get("graphrag", {}).get("use_graphrag"):
            warnings.append(f"{method} usually disables GraphRAG by default; confirm this explicit enablement is intended")
    if method == "tag":
        if config.get("raptor", {}).get("use_raptor") or config.get("graphrag", {}).get("use_graphrag"):
            warnings.append("tag datasets are tag sets; do not usually enable RAPTOR or GraphRAG")
    if method == "naive":
        if "chunk_token_num" not in config:
            warnings.append("naive config normally includes chunk_token_num")
        if "delimiter" not in config:
            warnings.append("naive config normally includes delimiter")


def inspect_document_name(document_name: str | None, chunk_method: str | None, warnings: list[str]) -> None:
    if not document_name or not chunk_method:
        return
    suffix = Path(document_name).suffix.lower()
    method = chunk_method.strip().lower()
    if suffix in IMAGE_EXTS and method != "picture":
        warnings.append("image-like document extension usually requires chunk_method 'picture'")
    if suffix in PRESENTATION_EXTS and method != "presentation":
        warnings.append("presentation document extension usually requires chunk_method 'presentation'")
    if suffix in EMAIL_EXTS and method != "email":
        warnings.append("email document extension usually pairs with chunk_method 'email'")
    if suffix in AUDIO_EXTS and method not in {"audio", "naive", "general"}:
        warnings.append("audio-like document extension may need the audio parser path")
    if suffix in SPREADSHEET_EXTS and method == "naive":
        warnings.append("spreadsheet with naive/general parsing: confirm html4excel/table handling matches the desired output")
    if suffix in PDF_EXTS and method in {"tag", "email"}:
        warnings.append(f"PDF extension is unusual for chunk_method {method!r}")


def print_section(title: str, items: list[str]) -> None:
    print(title)
    if items:
        for item in items:
            print(f"- {item}")
    else:
        print("- none")


def main() -> int:
    args = parse_args()
    config, errors = load_json(args.config)
    if errors:
        print_section("Errors", errors)
        return 2
    assert config is not None

    warnings: list[str] = []
    unknowns: list[str] = []

    inspect_top_level(config, warnings, unknowns)
    inspect_parent_child(config, warnings)
    inspect_raptor(config, warnings, unknowns)
    inspect_graphrag(config, warnings, unknowns)
    inspect_method(args.chunk_method, config, warnings)
    inspect_document_name(args.document_name, args.chunk_method, warnings)

    print(f"Config: {args.config}")
    if args.chunk_method:
        print(f"Chunk method: {args.chunk_method}")
    if args.document_name:
        print(f"Document name: {args.document_name}")
    print_section("Warnings", warnings)
    print_section("Unknown keys", unknowns)

    if args.strict_unknown_keys and unknowns:
        return 1
    return 1 if warnings else 0


if __name__ == "__main__":
    sys.exit(main())
