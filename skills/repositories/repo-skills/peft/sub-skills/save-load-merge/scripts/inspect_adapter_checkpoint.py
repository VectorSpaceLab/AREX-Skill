#!/usr/bin/env python3
"""Inspect a local PEFT adapter checkpoint without network access."""

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any

TASK_CLASS_HINTS = {
    "CAUSAL_LM": "AutoPeftModelForCausalLM",
    "SEQ_2_SEQ_LM": "AutoPeftModelForSeq2SeqLM",
    "SEQ_CLS": "AutoPeftModelForSequenceClassification",
    "TOKEN_CLS": "AutoPeftModelForTokenClassification",
    "QUESTION_ANS": "AutoPeftModelForQuestionAnswering",
    "FEATURE_EXTRACTION": "AutoPeftModelForFeatureExtraction",
}

METHOD_NOTES = {
    "LORA": "Load with PeftModel/AutoPeftModel; merge may be available via merge_and_unload depending on target modules and quantization.",
    "IA3": "Load with PeftModel/AutoPeftModel; weighted adapter merging is linear for compatible IA3 adapters.",
    "PROMPT_TUNING": "Prompt-learning checkpoints store prompt parameters and are not merged into base weights like LoRA.",
    "P_TUNING": "Prompt-learning checkpoints store prompt parameters and are not merged into base weights like LoRA.",
    "PREFIX_TUNING": "Prefix checkpoints store virtual-token parameters and are not merged into base weights like LoRA.",
    "LOHA": "Use PeftModel for normal loading; mixed inference may require PeftMixedModel with compatible tuner types.",
    "LOKR": "Use PeftModel for normal loading; conversion to LoRA may be possible with PEFT conversion utilities.",
}


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, "missing adapter_config.json"
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON in adapter_config.json: {exc}"
    if not isinstance(data, dict):
        return None, "adapter_config.json must contain a JSON object"
    return data, None


def inspect_adapter(path: Path) -> dict[str, Any]:
    adapter_dir = path.expanduser().resolve()
    result: dict[str, Any] = {
        "path": str(adapter_dir),
        "exists": adapter_dir.exists(),
        "is_dir": adapter_dir.is_dir(),
        "ok": False,
        "errors": [],
        "warnings": [],
        "files": {},
        "config": {},
        "hints": [],
    }

    if not adapter_dir.exists():
        result["errors"].append("adapter directory does not exist")
        return result
    if not adapter_dir.is_dir():
        result["errors"].append("adapter path is not a directory")
        return result

    config_path = adapter_dir / "adapter_config.json"
    safe_path = adapter_dir / "adapter_model.safetensors"
    bin_path = adapter_dir / "adapter_model.bin"
    readme_path = adapter_dir / "README.md"

    result["files"] = {
        "adapter_config.json": config_path.exists(),
        "adapter_model.safetensors": safe_path.exists(),
        "adapter_model.bin": bin_path.exists(),
        "README.md": readme_path.exists(),
    }

    config, config_error = load_json(config_path)
    if config_error:
        result["errors"].append(config_error)
    else:
        assert config is not None
        peft_type = config.get("peft_type")
        task_type = config.get("task_type")
        base_model = config.get("base_model_name_or_path")
        revision = config.get("revision")
        result["config"] = {
            "peft_type": peft_type,
            "task_type": task_type,
            "base_model_name_or_path": base_model,
            "revision": revision,
        }
        if not peft_type:
            result["errors"].append("adapter_config.json is missing peft_type")
        if not task_type:
            result["warnings"].append("task_type is missing; use explicit PeftConfig + base model or generic AutoPeftModel")
        if not base_model:
            result["warnings"].append("base_model_name_or_path is missing; adapter cannot load its base model automatically")
        class_hint = TASK_CLASS_HINTS.get(str(task_type)) if task_type else None
        if class_hint:
            result["hints"].append(f"Automatic class hint: peft.{class_hint}.from_pretrained(<adapter_dir>)")
        else:
            result["hints"].append("Automatic class hint: peft.AutoPeftModel.from_pretrained(<adapter_dir>) or explicit PeftModel.from_pretrained(base_model, <adapter_dir>)")
        if base_model:
            result["hints"].append(f"Explicit load: load the base model from {base_model!r}, then call PeftModel.from_pretrained(base_model, <adapter_dir>)")
        method_note = METHOD_NOTES.get(str(peft_type)) if peft_type else None
        if method_note:
            result["hints"].append(method_note)

    if not safe_path.exists() and not bin_path.exists():
        result["errors"].append("missing adapter_model.safetensors or adapter_model.bin")
    if safe_path.exists() and bin_path.exists():
        result["warnings"].append("both safetensors and bin weights exist; PEFT usually prefers safetensors, verify duplicates are intentional")
    if bin_path.exists() and not safe_path.exists():
        result["warnings"].append("only adapter_model.bin found; safetensors is preferred when possible")

    result["ok"] = not result["errors"]
    return result


def print_text_report(result: dict[str, Any]) -> None:
    status = "OK" if result["ok"] else "NOT OK"
    print(f"PEFT adapter inspection: {status}")
    print(f"Path: {result['path']}")
    print("Files:")
    for name, present in result.get("files", {}).items():
        print(f"  {'✓' if present else '✗'} {name}")
    if result.get("config"):
        print("Config:")
        for key, value in result["config"].items():
            print(f"  {key}: {value!r}")
    if result.get("hints"):
        print("Hints:")
        for hint in result["hints"]:
            print(f"  - {hint}")
    if result.get("warnings"):
        print("Warnings:")
        for warning in result["warnings"]:
            print(f"  - {warning}")
    if result.get("errors"):
        print("Errors:")
        for error in result["errors"]:
            print(f"  - {error}")


def make_tiny_fixture() -> int:
    with tempfile.TemporaryDirectory(prefix="peft-adapter-fixture-") as tmp:
        adapter_dir = Path(tmp) / "adapter"
        adapter_dir.mkdir()
        (adapter_dir / "adapter_config.json").write_text(
            json.dumps(
                {
                    "peft_type": "LORA",
                    "task_type": "CAUSAL_LM",
                    "base_model_name_or_path": "tiny-local-base",
                    "revision": None,
                    "target_modules": ["q_proj", "v_proj"],
                    "r": 8,
                    "lora_alpha": 16,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        (adapter_dir / "adapter_model.safetensors").write_bytes(b"")
        result = inspect_adapter(adapter_dir)
        print_text_report(result)
        return 0 if result["ok"] else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect a local PEFT adapter checkpoint directory without importing PEFT or using network access."
    )
    parser.add_argument("adapter_dir", nargs="?", help="Path containing adapter_config.json and adapter_model.safetensors/bin")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--tiny-fixture", action="store_true", help="Create and inspect a temporary minimal adapter fixture")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.tiny_fixture:
        return make_tiny_fixture()
    if not args.adapter_dir:
        print("error: adapter_dir is required unless --tiny-fixture is used", file=sys.stderr)
        return 2
    result = inspect_adapter(Path(args.adapter_dir))
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_report(result)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
