#!/usr/bin/env python3
"""Classify InvokeAI model metadata/config files without loading model weights."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


BASE_HINTS: list[tuple[str, str]] = [
    (r"sdxl|stable[-_ ]?diffusion[-_ ]?xl", "sdxl"),
    (r"sd[-_ ]?3|stable[-_ ]?diffusion[-_ ]?3", "sd-3"),
    (r"sd[-_ ]?2|stable[-_ ]?diffusion[-_ ]?2", "sd-2"),
    (r"sd[-_ ]?1|stable[-_ ]?diffusion[-_ ]?1|v1[-_ ]?5", "sd-1"),
    (r"flux2|flux[-_ ]?2|klein", "flux2"),
    (r"flux", "flux"),
    (r"qwen[-_ ]?image", "qwen-image"),
    (r"qwen3", "any"),
    (r"z[-_ ]?image", "z-image"),
    (r"cogview4|cogview[-_ ]?4", "cogview4"),
    (r"anima|cosmos", "anima"),
    (r"external://", "external"),
]

CLASS_HINTS: list[tuple[str, dict[str, str]]] = [
    (r"stable.*xl.*pipeline|sdxlpipeline", {"base": "sdxl", "type": "main", "format": "diffusers"}),
    (r"stable.*3.*pipeline|sd3.*pipeline", {"base": "sd-3", "type": "main", "format": "diffusers"}),
    (r"stable.*2.*pipeline", {"base": "sd-2", "type": "main", "format": "diffusers"}),
    (r"stable.*pipeline", {"base": "sd-1", "type": "main", "format": "diffusers"}),
    (r"flux.*pipeline|fluxtransformer", {"base": "flux", "type": "main", "format": "diffusers"}),
    (r"qwen.*image", {"base": "qwen-image", "type": "main", "format": "diffusers"}),
    (r"cogview4", {"base": "cogview4", "type": "main", "format": "diffusers"}),
    (r"zimage|z[-_ ]?image", {"base": "z-image", "type": "main", "format": "diffusers"}),
    (r"autoencoderkl|vae", {"type": "vae", "format": "diffusers"}),
    (r"clipvision", {"base": "any", "type": "clip_vision", "format": "diffusers"}),
    (r"cliptext|clip.*embed", {"base": "any", "type": "clip_embed", "format": "diffusers"}),
    (r"t5", {"base": "any", "type": "t5_encoder"}),
    (r"qwen3", {"base": "any", "type": "qwen3_encoder"}),
    (r"llava", {"base": "any", "type": "llava_onevision", "format": "diffusers"}),
]

VARIANT_HINTS: list[tuple[str, str]] = [
    (r"inpaint|inpainting", "inpaint"),
    (r"depth", "depth"),
    (r"schnell", "schnell"),
    (r"dev[_ -]?fill|fill", "dev_fill"),
    (r"dev", "dev"),
    (r"klein[_ -]?4b[_ -]?base", "klein_4b_base"),
    (r"klein[_ -]?4b", "klein_4b"),
    (r"klein[_ -]?9b[_ -]?base", "klein_9b_base"),
    (r"klein[_ -]?9b", "klein_9b"),
    (r"turbo", "turbo"),
    (r"zbase|z[-_ ]?base", "zbase"),
    (r"edit", "edit"),
    (r"generate", "generate"),
]

METADATA_LOWER_KEYS = {
    "ss_network_module",
    "ss_network_dim",
    "ss_base_model_version",
    "modelspec.architecture",
    "modelspec.implementation",
    "lora_adapter_metadata",
}

EXPLICIT_FIELDS = ("base", "type", "format", "variant", "prediction_type", "provider_id", "provider_model_id")


def load_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        loaded = json.loads(text)
    except json.JSONDecodeError as json_error:
        try:
            import yaml  # type: ignore
        except Exception as import_error:
            raise ValueError(
                f"{path}: not valid JSON and PyYAML is unavailable for YAML parsing ({import_error})"
            ) from json_error
        loaded = yaml.safe_load(text)
    if not isinstance(loaded, dict):
        raise ValueError(f"{path}: expected a JSON/YAML object at the top level")
    return loaded


def nested_values(metadata: Any, limit: int = 200) -> list[str]:
    values: list[str] = []

    def visit(value: Any) -> None:
        if len(values) >= limit:
            return
        if isinstance(value, dict):
            for key, nested_value in value.items():
                values.append(str(key))
                visit(nested_value)
        elif isinstance(value, list):
            for nested_value in value:
                visit(nested_value)
        elif isinstance(value, (str, int, float, bool)) or value is None:
            values.append(str(value))

    visit(metadata)
    return values


def normalized_blob(metadata: dict[str, Any]) -> str:
    return "\n".join(nested_values(metadata)).lower()


def find_first_hint(patterns: list[tuple[str, str]], text: str) -> str | None:
    for pattern, value in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return value
    return None


def infer_from_class_names(text: str) -> tuple[dict[str, str], list[str]]:
    guesses: dict[str, str] = {}
    evidence: list[str] = []
    for pattern, updates in CLASS_HINTS:
        if re.search(pattern, text, re.IGNORECASE):
            guesses.update({key: value for key, value in updates.items() if key not in guesses})
            evidence.append(f"class/architecture matched /{pattern}/")
    return guesses, evidence


def infer_from_metadata_keys(metadata: dict[str, Any], text: str) -> tuple[dict[str, str], list[str]]:
    guesses: dict[str, str] = {}
    evidence: list[str] = []
    lower_keys = {str(key).lower() for key in metadata.keys()}

    if lower_keys & METADATA_LOWER_KEYS or "lora" in text:
        guesses["type"] = "lora"
        guesses.setdefault("format", "lycoris")
        evidence.append("LoRA-style metadata keys or values detected")

    if "model_index.json" in text or "_class_name" in metadata or "diffusers_version" in metadata:
        guesses.setdefault("format", "diffusers")
        evidence.append("diffusers model index/config fields detected")

    if "gguf" in text or "general.architecture" in lower_keys:
        guesses.setdefault("format", "gguf_quantized")
        evidence.append("GGUF-style metadata detected")

    if "quantization_config" in metadata or "bnb" in text or "bitsandbytes" in text:
        if "nf4" in text:
            guesses.setdefault("format", "bnb_quantized_nf4b")
        elif "int8" in text or "llm_int8" in text:
            guesses.setdefault("format", "bnb_quantized_int8b")
        evidence.append("quantization metadata detected")

    if "provider_id" in metadata and "provider_model_id" in metadata:
        guesses.update({"base": "external", "type": "external_image_generator", "format": "external_api"})
        evidence.append("external provider fields detected")

    source = str(metadata.get("source") or metadata.get("path") or "").lower()
    if source.startswith("external://"):
        guesses.update({"base": "external", "type": "external_image_generator", "format": "external_api"})
        evidence.append("external:// source detected")

    return guesses, evidence


def classify_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    text = normalized_blob(metadata)
    guesses: dict[str, str] = {}
    evidence: list[str] = []
    warnings: list[str] = []

    for field_name in EXPLICIT_FIELDS:
        if field_name in metadata and metadata[field_name] not in (None, ""):
            if field_name in {"provider_id", "provider_model_id"}:
                continue
            guesses[field_name] = str(metadata[field_name])
            evidence.append(f"explicit field {field_name}={metadata[field_name]}")

    class_guesses, class_evidence = infer_from_class_names(text)
    for key, value in class_guesses.items():
        guesses.setdefault(key, value)
    evidence.extend(class_evidence)

    key_guesses, key_evidence = infer_from_metadata_keys(metadata, text)
    for key, value in key_guesses.items():
        guesses.setdefault(key, value)
    evidence.extend(key_evidence)

    base = find_first_hint(BASE_HINTS, text)
    if base and "base" not in guesses:
        guesses["base"] = base
        evidence.append(f"base hint matched {base}")

    variant = find_first_hint(VARIANT_HINTS, text)
    if variant and "variant" not in guesses:
        guesses["variant"] = variant
        evidence.append(f"variant hint matched {variant}")

    if "format" not in guesses:
        warnings.append("No storage format inferred; inspect file extension or model record fields.")
    if "type" not in guesses:
        warnings.append("No model type inferred; safe metadata may be insufficient.")
    if "base" not in guesses:
        warnings.append("No base architecture inferred; use model record overrides or safe key inspection if needed.")

    if guesses.get("format") in {"checkpoint", "unknown"}:
        warnings.append("Checkpoint classification may require state-dict keys and shapes; avoid pickle loads unless authorized.")

    return {
        "guess": guesses,
        "confidence": "metadata-hint" if evidence else "none",
        "evidence": evidence,
        "warnings": warnings,
    }


def print_human(path: Path, result: dict[str, Any]) -> None:
    print(f"{path}:")
    guess = result.get("guess") or {}
    if guess:
        for key in sorted(guess):
            print(f"  {key}: {guess[key]}")
    else:
        print("  no taxonomy guess")
    for evidence_item in result.get("evidence", []):
        print(f"  evidence: {evidence_item}")
    for warning in result.get("warnings", []):
        print(f"  warning: {warning}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify InvokeAI model metadata/config JSON or YAML without loading model weights."
    )
    parser.add_argument("metadata_files", nargs="+", type=Path, help="JSON/YAML metadata or config files to inspect")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()

    results: list[dict[str, Any]] = []
    exit_code = 0
    for metadata_path in args.metadata_files:
        try:
            metadata = load_mapping(metadata_path)
            result = classify_metadata(metadata)
            result["path"] = str(metadata_path)
            results.append(result)
            if not args.json:
                print_human(metadata_path, result)
        except Exception as error:
            exit_code = 1
            result = {"path": str(metadata_path), "error": str(error)}
            results.append(result)
            if not args.json:
                print(f"{metadata_path}: error: {error}", file=sys.stderr)

    if args.json:
        print(json.dumps({"results": results}, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
