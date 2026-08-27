#!/usr/bin/env python3
"""Safe smoke checks for Opyrator UI and component behavior.

This helper stays in-process: it does not launch a Streamlit browser session or a
long-running server. It only inspects schemas, validates FileContent round trips,
and checks custom renderer hooks.
"""

import argparse
import datetime as _dt
import json
import sys
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field, SecretStr

from opyrator.components.types import FileContent
from opyrator.ui import schema_utils


class SelectionValue(str, Enum):
    FOO = "foo"
    BAR = "bar"


class NestedInput(BaseModel):
    text: str
    integer: int


class ShowcaseInput(BaseModel):
    short_text: str = Field(..., max_length=60, description="Short text property")
    password: SecretStr = Field(..., description="Password text property")
    long_text: str = Field(..., description="Unlimited text property")
    integer_in_range: int = Field(
        20,
        ge=10,
        lt=30,
        multiple_of=2,
        description="Number property with a limited range.",
    )
    positive_integer: int = Field(
        ..., ge=0, multiple_of=10, description="Positive integer with step count of 10."
    )
    float_number: float = Field(0.001)
    date: Optional[_dt.date] = Field(
        _dt.date(2021, 4, 22), description="Date property. Optional because of default value."
    )
    time: Optional[_dt.time] = Field(
        _dt.time(8, 14, 18, 285271), description="Time property. Optional because of default value."
    )
    string_list: List[str] = Field(..., max_items=20, description="List of string values")
    int_list: List[int] = Field(..., description="List of int values")
    boolean: bool = Field(False, description="Boolean property. Optional because of default value.")
    file_list: Optional[List[FileContent]] = Field(None, description="A list of files. Optional property.")
    single_file: Optional[FileContent] = Field(
        None,
        mime_type="image/png",
        description="A single file. Optional property.",
    )
    string_dict: Dict[str, str] = Field(..., description="Dict property with string values")
    float_dict: Dict[str, float] = Field(..., description="Dict property with float values")
    single_selection: SelectionValue = Field(..., description="Only select a single item from a set.")
    multi_selection: Set[SelectionValue] = Field(..., description="Allows multiple items from a set.")
    single_object: NestedInput = Field(..., description="Another object embedded into this model.")
    object_list: List[NestedInput] = Field(..., description="A list of objects embedded into this model.")


class NestedOutput(BaseModel):
    title: str
    confidence: float


class ShowcaseOutput(BaseModel):
    summary: str = Field(..., description="Text summary")
    label: SelectionValue = Field(..., description="Selected label")
    payload_file: FileContent = Field(..., mime_type="image/png", description="File payload")
    metadata: Dict[str, str] = Field(..., description="Metadata map")
    rows: List[NestedOutput] = Field(..., description="Nested row list")

    def render_output_ui(self, streamlit, input):  # type: ignore[no-untyped-def]
        streamlit.subheader("Showcase output")
        streamlit.write({"input": getattr(input, "dict", lambda: input)() if input is not None else None})


class FallbackOutput(BaseModel):
    value: int

    def render_output_ui(self, streamlit):  # type: ignore[no-untyped-def]
        raise RuntimeError("intentional renderer failure")


class CustomInputModel(BaseModel):
    text: str

    @classmethod
    def render_input_ui(cls, streamlit, input_data):  # type: ignore[no-untyped-def]
        value = ""
        if isinstance(input_data, dict):
            value = input_data.get("text", "")
        elif isinstance(input_data, cls):
            value = input_data.text
        return cls(text=value)


def _property_classification(property_schema: Dict[str, Any], references: Dict[str, Any]) -> str:
    predicates: List[Tuple[str, Any]] = [
        ("is_single_enum_property", lambda p: schema_utils.is_single_enum_property(p, references)),
        ("is_multi_enum_property", lambda p: schema_utils.is_multi_enum_property(p, references)),
        ("is_single_file_property", schema_utils.is_single_file_property),
        ("is_multi_file_property", schema_utils.is_multi_file_property),
        ("is_single_datetime_property", schema_utils.is_single_datetime_property),
        ("is_single_boolean_property", schema_utils.is_single_boolean_property),
        ("is_single_dict_property", schema_utils.is_single_dict_property),
        ("is_single_number_property", schema_utils.is_single_number_property),
        ("is_single_string_property", schema_utils.is_single_string_property),
        ("is_single_object", lambda p: schema_utils.is_single_object(p, references)),
        ("is_object_list_property", lambda p: schema_utils.is_object_list_property(p, references)),
        ("is_property_list", schema_utils.is_property_list),
        ("is_single_reference", schema_utils.is_single_reference),
    ]
    for name, predicate in predicates:
        try:
            if predicate(property_schema):
                return name
        except Exception as exc:  # pragma: no cover - defensive helper path
            return "error:%s:%s" % (name, exc)
    return "unsupported"


def _load_streamlit_helpers():
    from opyrator.ui.streamlit_ui import (  # imported lazily for a focused UI smoke
        function_has_named_arg,
        has_input_ui_renderer,
        has_output_ui_renderer,
    )

    return function_has_named_arg, has_input_ui_renderer, has_output_ui_renderer


def _build_summary() -> Dict[str, Any]:
    schema = ShowcaseInput.schema(by_alias=True)
    properties = schema.get("properties", {})
    references = schema.get("definitions", {})

    expected = {
        "short_text": "is_single_string_property",
        "password": "is_single_string_property",
        "long_text": "is_single_string_property",
        "integer_in_range": "is_single_number_property",
        "positive_integer": "is_single_number_property",
        "float_number": "is_single_number_property",
        "date": "is_single_datetime_property",
        "time": "is_single_datetime_property",
        "string_list": "is_property_list",
        "int_list": "is_property_list",
        "boolean": "is_single_boolean_property",
        "file_list": "is_multi_file_property",
        "single_file": "is_single_file_property",
        "string_dict": "is_single_dict_property",
        "float_dict": "is_single_dict_property",
        "single_selection": "is_single_enum_property",
        "multi_selection": "is_multi_enum_property",
        "single_object": "is_single_object",
        "object_list": "is_object_list_property",
    }

    classifications = {
        name: _property_classification(properties[name], references)
        for name in expected
    }

    unsupported_sample = {"title": "Unsupported", "type": "array", "items": {"type": "boolean"}}
    unsupported_classification = _property_classification(unsupported_sample, references)

    file_payload = b"opyrator-ui-smoke"
    encoded = FileContent.validate(file_payload)
    text_payload = FileContent.validate(b"hello-ui").as_str()

    function_has_named_arg, has_input_ui_renderer, has_output_ui_renderer = _load_streamlit_helpers()
    showcase_output = ShowcaseOutput(
        summary="ok",
        label=SelectionValue.FOO,
        payload_file=FileContent.validate(b"image-bytes"),
        metadata={"kind": "demo"},
        rows=[NestedOutput(title="first", confidence=0.9)],
    )
    fallback_output = FallbackOutput(value=1)

    hook_summary = {
        "input_renderer_present": has_input_ui_renderer(CustomInputModel),
        "output_renderer_present": has_output_ui_renderer(showcase_output),
        "custom_output_signature_accepts_input": function_has_named_arg(
            showcase_output.render_output_ui, "input"
        ),
        "fallback_renderer_present": has_output_ui_renderer(fallback_output),
        "fallback_signature_accepts_input": function_has_named_arg(
            fallback_output.render_output_ui, "input"
        ),
    }

    expected_hook_summary = {
        "input_renderer_present": True,
        "output_renderer_present": True,
        "custom_output_signature_accepts_input": True,
        "fallback_renderer_present": True,
        "fallback_signature_accepts_input": False,
    }

    schema_checks = {
        "single_file_has_mime_type": properties["single_file"].get("mime_type") == "image/png",
        "file_schema_format_byte": properties["single_file"].get("format") == "byte",
        "multi_file_schema_format_byte": properties["file_list"].get("items", {}).get("format") == "byte",
        "enum_reference_present": "SelectionValue" in references,
        "nested_reference_present": "NestedInput" in references,
    }

    classification_ok = classifications == expected
    file_round_trip_ok = encoded.as_bytes() == file_payload and text_payload == "hello-ui"
    unsupported_ok = unsupported_classification == "unsupported"
    hook_ok = hook_summary == expected_hook_summary
    schema_ok = all(schema_checks.values())

    return {
        "status": "ok" if classification_ok and file_round_trip_ok and unsupported_ok and hook_ok and schema_ok else "failed",
        "python": sys.version.split()[0],
        "schema_classifications": classifications,
        "unsupported_sample": unsupported_classification,
        "schema_checks": schema_checks,
        "file_round_trip": {
            "base64_text": str(encoded),
            "round_trip_bytes_match": encoded.as_bytes() == file_payload,
            "string_round_trip": text_payload,
        },
        "hook_summary": hook_summary,
        "expected_hook_summary": expected_hook_summary,
        "expected_classifications": expected,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a deterministic Opyrator UI/component smoke check without starting a Streamlit server."
    )
    parser.add_argument("--json", action="store_true", help="Print a JSON summary only.")
    args = parser.parse_args(argv)

    try:
        summary = _build_summary()
    except Exception as exc:  # pragma: no cover - smoke failure path
        payload = {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("schema_smoke: error")
            print(json.dumps(payload, indent=2, sort_keys=True))
        return 2

    exit_code = 0 if summary["status"] == "ok" else 1
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("schema_smoke: %s" % summary["status"])
        print("classifications: %d fields checked" % len(summary["schema_classifications"]))
        print("file_round_trip: %s" % summary["file_round_trip"]["round_trip_bytes_match"])
        print("custom_hooks: %s" % summary["hook_summary"])
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
