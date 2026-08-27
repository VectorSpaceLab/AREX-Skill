#!/usr/bin/env python3
"""Validate a MiroFish ontology JSON payload.

The script is standalone and uses only the Python standard library. It accepts a
raw ontology object, an ontology-generate response envelope, or a project object
that contains an ``ontology`` field.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from typing import Any, Iterable

MAX_ONTOLOGY_TYPES = 10
MAX_ONTOLOGY_ATTRIBUTES = 10
MAX_ONTOLOGY_SOURCE_TARGETS = 10
RESERVED_ONTOLOGY_ATTRIBUTE_NAMES = frozenset(
    {
        "uuid",
        "name",
        "group_id",
        "graph_id",
        "name_embedding",
        "summary",
        "created_at",
    }
)

PASCAL_CASE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
UPPER_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
SNAKE_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


@dataclass
class ValidationIssue:
    level: str
    path: str
    message: str


@dataclass
class ValidationResult:
    ok: bool
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    summary: dict[str, Any]


def _issue(level: str, path: str, message: str) -> ValidationIssue:
    return ValidationIssue(level=level, path=path, message=message)


def _load_payload(path: str) -> Any:
    if path == "-":
        text = sys.stdin.read()
    else:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    if not text.strip():
        raise ValueError("input is empty")
    return json.loads(text)


def _extract_ontology(payload: Any) -> tuple[Any, str, list[ValidationIssue]]:
    warnings: list[ValidationIssue] = []
    if not isinstance(payload, dict):
        return payload, "$", warnings

    if "entity_types" in payload or "edge_types" in payload:
        return payload, "$", warnings

    data = payload.get("data")
    if isinstance(data, dict) and isinstance(data.get("ontology"), dict):
        return data["ontology"], "$.data.ontology", warnings

    ontology = payload.get("ontology")
    if isinstance(ontology, dict):
        return ontology, "$.ontology", warnings

    if "relation_types" in payload and "edge_types" not in payload:
        warnings.append(
            _issue(
                "warning",
                "$",
                "found relation_types but not canonical edge_types; MiroFish builds from edge_types",
            )
        )
    return payload, "$", warnings


def _attr_name(attribute: Any) -> str | None:
    if isinstance(attribute, str):
        return attribute.strip() or None
    if isinstance(attribute, dict):
        name = attribute.get("name")
        return name.strip() if isinstance(name, str) and name.strip() else None
    return None


def _validate_attributes(
    attributes: Any,
    *,
    path: str,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    if not isinstance(attributes, list):
        warnings.append(
            _issue(
                "warning",
                path,
                "attributes is not a list; MiroFish will replace invalid lists with fallback details",
            )
        )
        return

    if len(attributes) == 0:
        warnings.append(
            _issue(
                "warning",
                path,
                "empty attributes list will be replaced by fallback details during normalization",
            )
        )
        return

    if len(attributes) > MAX_ONTOLOGY_ATTRIBUTES:
        errors.append(
            _issue(
                "error",
                path,
                f"too many attributes: {len(attributes)} > {MAX_ONTOLOGY_ATTRIBUTES}",
            )
        )

    seen: set[str] = set()
    for index, attribute in enumerate(attributes):
        attr_path = f"{path}[{index}]"
        name = _attr_name(attribute)
        if name is None:
            warnings.append(
                _issue(
                    "warning",
                    attr_path,
                    "invalid attribute entry will be ignored during normalization",
                )
            )
            continue

        lowered = name.lower()
        if lowered in RESERVED_ONTOLOGY_ATTRIBUTE_NAMES:
            errors.append(
                _issue(
                    "error",
                    attr_path,
                    f"reserved attribute name {name!r}; use a non-reserved name such as full_name or org_name",
                )
            )
        if not SNAKE_RE.match(name):
            warnings.append(
                _issue(
                    "warning",
                    attr_path,
                    f"attribute name {name!r} is not lowercase snake_case",
                )
            )
        if lowered in seen:
            warnings.append(
                _issue("warning", attr_path, f"duplicate attribute name {name!r}")
            )
        seen.add(lowered)

        if isinstance(attribute, dict):
            description = attribute.get("description")
            if description is not None and not isinstance(description, str):
                warnings.append(
                    _issue("warning", f"{attr_path}.description", "description should be a string")
                )
            attr_type = attribute.get("type")
            if attr_type is not None and attr_type != "text":
                warnings.append(
                    _issue(
                        "warning",
                        f"{attr_path}.type",
                        "MiroFish ontology prompts use type 'text'; other values may not help Zep extraction",
                    )
                )


def _validate_entity_types(
    ontology: dict[str, Any],
    *,
    root: str,
    require_fallbacks: bool,
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> set[str]:
    entity_types = ontology.get("entity_types")
    if not isinstance(entity_types, list):
        errors.append(_issue("error", f"{root}.entity_types", "entity_types must be a list"))
        return set()

    if len(entity_types) > MAX_ONTOLOGY_TYPES:
        errors.append(
            _issue(
                "error",
                f"{root}.entity_types",
                f"too many entity types: {len(entity_types)} > {MAX_ONTOLOGY_TYPES}",
            )
        )
    if len(entity_types) != MAX_ONTOLOGY_TYPES:
        warnings.append(
            _issue(
                "warning",
                f"{root}.entity_types",
                "MiroFish's ontology prompt asks for exactly 10 entity types, with Person and Organization last",
            )
        )

    names: list[str] = []
    seen: set[str] = set()
    for index, entity in enumerate(entity_types):
        entity_path = f"{root}.entity_types[{index}]"
        if isinstance(entity, str):
            name = entity.strip()
            warnings.append(
                _issue(
                    "warning",
                    entity_path,
                    "bare string entity will be converted to an object by the generator, but stored project ontology should use object form",
                )
            )
        elif isinstance(entity, dict):
            raw_name = entity.get("name")
            name = raw_name.strip() if isinstance(raw_name, str) else ""
        else:
            errors.append(_issue("error", entity_path, "entity type must be an object"))
            continue

        if not name:
            errors.append(_issue("error", f"{entity_path}.name", "entity name is required"))
            continue
        if not PASCAL_CASE_RE.match(name):
            warnings.append(
                _issue(
                    "warning",
                    f"{entity_path}.name",
                    f"entity name {name!r} is not PascalCase; the generator normalizes raw LLM output",
                )
            )
        if name in seen:
            errors.append(_issue("error", f"{entity_path}.name", f"duplicate entity type {name!r}"))
        seen.add(name)
        names.append(name)

        if isinstance(entity, dict):
            description = entity.get("description")
            if description is not None and not isinstance(description, str):
                warnings.append(
                    _issue("warning", f"{entity_path}.description", "description should be a string")
                )
            if isinstance(description, str) and len(description) > 100:
                warnings.append(
                    _issue(
                        "warning",
                        f"{entity_path}.description",
                        "description exceeds 100 characters and generator output would be truncated",
                    )
                )
            _validate_attributes(
                entity.get("attributes", []),
                path=f"{entity_path}.attributes",
                errors=errors,
                warnings=warnings,
            )
            examples = entity.get("examples")
            if examples is not None and not isinstance(examples, list):
                warnings.append(_issue("warning", f"{entity_path}.examples", "examples should be a list"))

    has_fallbacks_last = len(names) >= 2 and names[-2:] == ["Person", "Organization"]
    if not has_fallbacks_last:
        target = errors if require_fallbacks else warnings
        target.append(
            _issue(
                "error" if require_fallbacks else "warning",
                f"{root}.entity_types",
                "expected fallback entity types Person and Organization as the final two entries",
            )
        )
    return set(names)


def _validate_source_targets(
    source_targets: Any,
    *,
    path: str,
    entity_names: set[str],
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    if not isinstance(source_targets, list):
        errors.append(_issue("error", path, "source_targets must be a non-empty list"))
        return
    if not source_targets:
        errors.append(
            _issue(
                "error",
                path,
                "edge has no source_targets; MiroFish will not install this edge type in Zep",
            )
        )
        return
    if len(source_targets) > MAX_ONTOLOGY_SOURCE_TARGETS:
        errors.append(
            _issue(
                "error",
                path,
                f"too many source_targets: {len(source_targets)} > {MAX_ONTOLOGY_SOURCE_TARGETS}",
            )
        )

    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(source_targets):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(_issue("error", item_path, "source_target entry must be an object"))
            continue
        source = item.get("source")
        target = item.get("target")
        if not isinstance(source, str) or not source.strip():
            errors.append(_issue("error", f"{item_path}.source", "source must be a non-empty string"))
            continue
        if not isinstance(target, str) or not target.strip():
            errors.append(_issue("error", f"{item_path}.target", "target must be a non-empty string"))
            continue
        pair = (source.strip(), target.strip())
        if pair in seen:
            warnings.append(_issue("warning", item_path, f"duplicate source_target {pair[0]} -> {pair[1]}"))
        seen.add(pair)
        for field_name, endpoint in (("source", pair[0]), ("target", pair[1])):
            if endpoint != "Entity" and endpoint not in entity_names:
                errors.append(
                    _issue(
                        "error",
                        f"{item_path}.{field_name}",
                        f"endpoint {endpoint!r} is not one of the defined entity types or Entity",
                    )
                )


def _validate_edge_types(
    ontology: dict[str, Any],
    *,
    root: str,
    entity_names: set[str],
    errors: list[ValidationIssue],
    warnings: list[ValidationIssue],
) -> None:
    edge_types = ontology.get("edge_types")
    if edge_types is None and "relation_types" in ontology:
        warnings.append(
            _issue(
                "warning",
                f"{root}.relation_types",
                "relation_types is not canonical; rename to edge_types for MiroFish graph build",
            )
        )
        edge_types = ontology.get("relation_types")
    if not isinstance(edge_types, list):
        errors.append(_issue("error", f"{root}.edge_types", "edge_types must be a list"))
        return

    if len(edge_types) > MAX_ONTOLOGY_TYPES:
        errors.append(
            _issue(
                "error",
                f"{root}.edge_types",
                f"too many edge types: {len(edge_types)} > {MAX_ONTOLOGY_TYPES}",
            )
        )
    if not (6 <= len(edge_types) <= 10):
        warnings.append(
            _issue(
                "warning",
                f"{root}.edge_types",
                "MiroFish's ontology prompt asks for 6-10 edge types",
            )
        )

    seen: set[str] = set()
    for index, edge in enumerate(edge_types):
        edge_path = f"{root}.edge_types[{index}]"
        if isinstance(edge, str):
            errors.append(
                _issue(
                    "error",
                    edge_path,
                    "bare string edge lacks source_targets and cannot be installed safely",
                )
            )
            continue
        if not isinstance(edge, dict):
            errors.append(_issue("error", edge_path, "edge type must be an object"))
            continue

        raw_name = edge.get("name")
        name = raw_name.strip() if isinstance(raw_name, str) else ""
        if not name:
            errors.append(_issue("error", f"{edge_path}.name", "edge name is required"))
        elif not UPPER_SNAKE_RE.match(name):
            warnings.append(
                _issue(
                    "warning",
                    f"{edge_path}.name",
                    f"edge name {name!r} is not uppercase snake case; generator normalizes raw LLM output",
                )
            )
        if name in seen:
            errors.append(_issue("error", f"{edge_path}.name", f"duplicate edge type {name!r}"))
        seen.add(name)

        description = edge.get("description")
        if description is not None and not isinstance(description, str):
            warnings.append(_issue("warning", f"{edge_path}.description", "description should be a string"))
        if isinstance(description, str) and len(description) > 100:
            warnings.append(
                _issue(
                    "warning",
                    f"{edge_path}.description",
                    "description exceeds 100 characters and generator output would be truncated",
                )
            )

        _validate_source_targets(
            edge.get("source_targets", []),
            path=f"{edge_path}.source_targets",
            entity_names=entity_names,
            errors=errors,
            warnings=warnings,
        )
        _validate_attributes(
            edge.get("attributes", []),
            path=f"{edge_path}.attributes",
            errors=errors,
            warnings=warnings,
        )


def validate_payload(payload: Any, *, require_fallbacks: bool = False) -> ValidationResult:
    ontology, root, extract_warnings = _extract_ontology(payload)
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = list(extract_warnings)

    if not isinstance(ontology, dict):
        errors.append(_issue("error", root, "ontology payload must be a JSON object"))
        return ValidationResult(False, errors, warnings, {"root": root})

    if "relation_types" in ontology and "edge_types" not in ontology:
        warnings.append(
            _issue(
                "warning",
                f"{root}.relation_types",
                "canonical MiroFish ontology key is edge_types, not relation_types",
            )
        )

    entity_names = _validate_entity_types(
        ontology,
        root=root,
        require_fallbacks=require_fallbacks,
        errors=errors,
        warnings=warnings,
    )
    _validate_edge_types(
        ontology,
        root=root,
        entity_names=entity_names,
        errors=errors,
        warnings=warnings,
    )

    summary = {
        "root": root,
        "entity_type_count": len(ontology.get("entity_types") or []) if isinstance(ontology.get("entity_types"), list) else None,
        "edge_type_count": len(ontology.get("edge_types") or []) if isinstance(ontology.get("edge_types"), list) else None,
        "reserved_attribute_names": sorted(RESERVED_ONTOLOGY_ATTRIBUTE_NAMES),
        "max_ontology_types": MAX_ONTOLOGY_TYPES,
        "max_attributes_per_type": MAX_ONTOLOGY_ATTRIBUTES,
        "max_source_targets_per_edge": MAX_ONTOLOGY_SOURCE_TARGETS,
    }
    return ValidationResult(not errors, errors, warnings, summary)


def _print_text(result: ValidationResult) -> None:
    status = "OK" if result.ok else "FAILED"
    print(f"MiroFish ontology validation: {status}")
    print(
        "Summary: "
        f"root={result.summary.get('root')} "
        f"entities={result.summary.get('entity_type_count')} "
        f"edges={result.summary.get('edge_type_count')}"
    )
    for collection_name, issues in (("ERROR", result.errors), ("WARN", result.warnings)):
        for issue in issues:
            print(f"{collection_name}: {issue.path}: {issue.message}")


def _print_json(result: ValidationResult) -> None:
    print(
        json.dumps(
            {
                "ok": result.ok,
                "summary": result.summary,
                "errors": [asdict(issue) for issue in result.errors],
                "warnings": [asdict(issue) for issue in result.warnings],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def _valid_sample() -> dict[str, Any]:
    entities = []
    for index in range(8):
        entities.append(
            {
                "name": f"ActorType{index}",
                "description": f"Specific actor type {index}.",
                "attributes": [
                    {"name": "role", "type": "text", "description": "Role in the event"}
                ],
                "examples": [f"actor {index}"],
            }
        )
    entities.extend(
        [
            {
                "name": "Person",
                "description": "Any individual person not fitting other specific person types.",
                "attributes": [
                    {"name": "full_name", "type": "text", "description": "Full name"}
                ],
                "examples": ["ordinary citizen"],
            },
            {
                "name": "Organization",
                "description": "Any organization not fitting other specific organization types.",
                "attributes": [
                    {"name": "org_name", "type": "text", "description": "Organization name"}
                ],
                "examples": ["community group"],
            },
        ]
    )
    edge_names = [
        "COMMENTS_ON",
        "RESPONDS_TO",
        "SUPPORTS",
        "OPPOSES",
        "REPORTS_ON",
        "AFFILIATED_WITH",
    ]
    edges = [
        {
            "name": name,
            "description": f"{name} relationship.",
            "source_targets": [{"source": "Person", "target": "Organization"}],
            "attributes": [
                {"name": "context", "type": "text", "description": "Relationship context"}
            ],
        }
        for name in edge_names
    ]
    return {"entity_types": entities, "edge_types": edges}


def _run_self_test() -> None:
    good = validate_payload(_valid_sample(), require_fallbacks=True)
    assert good.ok, good

    bad = _valid_sample()
    bad["entity_types"][0]["attributes"] = [{"name": "uuid", "type": "text"}]
    bad["edge_types"][0]["source_targets"] = [{"source": "MissingType", "target": "Person"}]
    bad_result = validate_payload(bad, require_fallbacks=True)
    messages = "\n".join(issue.message for issue in bad_result.errors)
    assert not bad_result.ok
    assert "reserved attribute" in messages
    assert "not one of the defined entity types" in messages

    envelope = {"success": True, "data": {"ontology": _valid_sample()}}
    envelope_result = validate_payload(envelope)
    assert envelope_result.ok
    assert envelope_result.summary["root"] == "$.data.ontology"

    print("validate_ontology_payload.py self-test: ok")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a MiroFish ontology JSON object, project object, or "
            "ontology-generate API response. Reads stdin when PATH is omitted or '-'."
        )
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="-",
        help="Ontology JSON file path, or '-' for stdin (default: stdin).",
    )
    parser.add_argument(
        "--require-fallbacks",
        action="store_true",
        help="Treat missing/non-final Person and Organization fallback entity types as errors.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON output instead of text.",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the bundled script's internal smoke tests and exit.",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.self_test:
        _run_self_test()
        return 0

    try:
        payload = _load_payload(args.path)
        result = validate_payload(payload, require_fallbacks=args.require_fallbacks)
    except Exception as exc:  # noqa: BLE001 - user-facing validator
        result = ValidationResult(
            ok=False,
            errors=[_issue("error", "$", f"failed to load/parse payload: {exc}")],
            warnings=[],
            summary={},
        )

    if args.json:
        _print_json(result)
    else:
        _print_text(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
