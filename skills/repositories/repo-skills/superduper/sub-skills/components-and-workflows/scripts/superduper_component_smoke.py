#!/usr/bin/env python3
"""Construct safe Superduper component workflow objects without requiring a DB."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def uppercase_text(value: Any) -> str:
    """Deterministic singleton callable for ObjectModel smoke checks."""
    return str(value).upper()


def describe_text(value: Any) -> dict[str, Any]:
    """Return JSON-compatible metadata for a downstream model example."""
    text = str(value)
    return {"text": text, "length": len(text)}


def chunk_words(text: Any, chunk_size: int = 4) -> list[str]:
    """Small local chunker shaped like a RAG preprocessing component."""
    words = str(text).split()
    if not words:
        return []
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), chunk_size)]


def import_superduper():
    """Import Superduper lazily so --help works without the package."""
    try:
        from superduper import Application, Listener, ObjectModel
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Could not import Superduper. Install the package in the active "
            f"Python environment before running this smoke helper. Original error: {exc}"
        ) from exc
    return Application, Listener, ObjectModel


def summarize_component(component: Any) -> dict[str, Any]:
    """Return stable, non-sensitive fields from a component."""
    summary = {
        "component": getattr(component, "component", component.__class__.__name__),
        "identifier": getattr(component, "identifier", None),
    }
    if hasattr(component, "key"):
        summary["key"] = getattr(component, "key")
    if hasattr(component, "outputs"):
        try:
            summary["outputs"] = component.outputs
        except Exception as exc:  # pragma: no cover - defensive only
            summary["outputs_error"] = str(exc)
    if hasattr(component, "predict_id"):
        try:
            summary["predict_id"] = component.predict_id
        except Exception as exc:  # pragma: no cover - defensive only
            summary["predict_id_error"] = str(exc)
    if hasattr(component, "model"):
        model = getattr(component, "model")
        summary["model_identifier"] = getattr(model, "identifier", None)
        summary["model_signature"] = getattr(model, "signature", None)
    return summary


def build_demo_components(include_rag_shape: bool) -> dict[str, Any]:
    """Construct ObjectModel, Listener, and Application objects only."""
    Application, Listener, ObjectModel = import_superduper()

    uppercase_model = ObjectModel(
        identifier="uppercase-model",
        object=uppercase_text,
        datatype="str",
    )
    uppercase_listener = Listener(
        identifier="uppercase-listener",
        model=uppercase_model,
        key="text",
        select=None,
    )

    describe_model = ObjectModel(
        identifier="describe-model",
        object=describe_text,
        datatype="json",
    )
    describe_listener = Listener(
        identifier="describe-listener",
        model=describe_model,
        key=uppercase_listener.outputs,
        select=None,
        upstream=[uppercase_listener],
    )

    components = [uppercase_listener, describe_listener]
    summary: dict[str, Any] = {
        "models": [summarize_component(uppercase_model), summarize_component(describe_model)],
        "listeners": [
            summarize_component(uppercase_listener),
            summarize_component(describe_listener),
        ],
        "notes": [
            "No database connection is opened by this helper.",
            "Listener select=None is construction-only; provide a real query before db.apply(listener).",
            "Use upstream_listener.outputs as a downstream listener key.",
        ],
    }

    if include_rag_shape:
        chunk_model = ObjectModel(
            identifier="chunk-words-model",
            object=chunk_words,
            datatype="json",
        )
        chunk_listener = Listener(
            identifier="chunk-words-listener",
            model=chunk_model,
            key="text",
            select=None,
            flatten=True,
        )
        components.append(chunk_listener)
        summary["rag_shape"] = {
            "chunk_model": summarize_component(chunk_model),
            "chunk_listener": summarize_component(chunk_listener),
            "reminder": "This is only the component shape; vector retrieval and provider LLM setup are separate routes.",
        }

    app = Application(identifier="component-workflow-demo", components=components)
    summary["application"] = {
        "component": getattr(app, "component", app.__class__.__name__),
        "identifier": app.identifier,
        "component_identifiers": [c.identifier for c in app.components],
    }
    summary["_objects"] = {
        "uppercase_model": uppercase_model,
        "describe_model": describe_model,
    }
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Construct Superduper ObjectModel, Listener, and Application objects "
            "without opening a database connection."
        )
    )
    parser.add_argument(
        "--predict-value",
        default=None,
        help="Optional value to run through the constructed ObjectModel examples.",
    )
    parser.add_argument(
        "--include-rag-shape",
        action="store_true",
        help="Also construct a tiny chunking listener shaped like the first step of a RAG workflow.",
    )
    parser.add_argument(
        "--as-json",
        action="store_true",
        help="Emit machine-readable JSON instead of a readable text summary.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    summary = build_demo_components(include_rag_shape=args.include_rag_shape)

    objects = summary.pop("_objects")
    if args.predict_value is not None:
        uppercase_model = objects["uppercase_model"]
        describe_model = objects["describe_model"]
        uppercase = uppercase_model.predict(args.predict_value)
        summary["prediction"] = {
            "input": args.predict_value,
            "uppercase_predict": uppercase,
            "uppercase_predict_batches": uppercase_model.predict_batches([args.predict_value, args.predict_value]),
            "describe_predict": describe_model.predict(uppercase),
        }

    if args.as_json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("Superduper component construction smoke")
        print("======================================")
        print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
