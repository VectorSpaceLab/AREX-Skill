#!/usr/bin/env python
"""Construct representative PEFT LoraConfig variants without loading a model."""

import argparse
import importlib.util
import json
import warnings
from dataclasses import asdict, is_dataclass


VARIANT_NOTES = [
    ("qlora_all_linear_rslora", "Use all-linear targeting with RS-LoRA scaling for QLoRA-style training."),
    ("dora_low_rank", "DoRA supports linear and Conv2D layers and has more overhead than plain LoRA."),
    ("pissa_fast_svd", "Fast PiSSA trades exact SVD quality for much faster initialization."),
    ("qalora_gptq", "QALoRA is currently implemented for GPTQ and requires divisible input dimensions."),
    ("alora_invocation", "aLoRA requires invocation tokens in every input and cannot be merged."),
    ("trainable_tokens_plus_lora", "Add tokens and resize embeddings before applying PEFT."),
    ("full_loftq_initialization", "Use only with an unquantized base model; PEFT quantizes the backbone."),
    ("eva_activation_svd", "Call initialize_lora_eva_weights(peft_model, dataloader) after wrapping."),
    ("corda_kpm", "Run CorDA preprocessing over representative data before wrapping."),
    ("lora_ga_full_precision", "Requires preprocess_loraga and full-precision weights; not for quantized models."),
]

OPTIONAL_BACKENDS = {
    "bitsandbytes": "4-bit/8-bit QLoRA and bitsandbytes LoftQ replacement workflows",
    "gptqmodel": "GPTQ post-training workflows and QALoRA-oriented GPTQ models",
    "aqlm": "AQLM prequantized model LoRA tuning",
    "eetq": "EETQ int8 model LoRA tuning",
    "hqq": "HQQ quantized model LoRA tuning",
    "torchao": "torchao int8 weight-only LoRA workflows",
    "neural_compressor": "Intel Neural Compressor quantized model LoRA loading",
    "scipy": "full LoftQ initialization with init_lora_weights='loftq'",
}


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def safe_config_summary(config) -> dict:
    data = config.to_dict()
    for key, value in list(data.items()):
        if is_dataclass(value):
            data[key] = asdict(value)
        elif isinstance(value, set):
            data[key] = sorted(value)
    keep = [
        "peft_type",
        "task_type",
        "target_modules",
        "r",
        "lora_alpha",
        "lora_dropout",
        "bias",
        "use_rslora",
        "init_lora_weights",
        "use_dora",
        "use_qalora",
        "qalora_group_size",
        "alora_invocation_tokens",
        "trainable_token_indices",
        "loftq_config",
        "eva_config",
        "corda_config",
        "lora_ga_config",
    ]
    return {key: data.get(key) for key in keep if data.get(key) not in (None, {}, [], set())}


def build_variants() -> list[tuple[str, object, list[str]]]:
    from peft import LoraConfig

    variants = []

    variants.append(
        (
            "qlora_all_linear_rslora",
            LoraConfig(
                task_type="CAUSAL_LM",
                target_modules="all-linear",
                r=16,
                lora_alpha=32,
                lora_dropout=0.05,
                bias="none",
                use_rslora=True,
            ),
            ["Use with a quantized base model prepared by prepare_model_for_kbit_training."],
        )
    )

    variants.append(
        (
            "dora_low_rank",
            LoraConfig(
                task_type="CAUSAL_LM",
                target_modules=["q_proj", "v_proj"],
                r=8,
                lora_alpha=16,
                use_dora=True,
            ),
            ["DoRA supports linear and Conv2D layers and has more overhead than plain LoRA."],
        )
    )

    variants.append(
        (
            "pissa_fast_svd",
            LoraConfig(
                task_type="CAUSAL_LM",
                target_modules="all-linear",
                r=16,
                lora_alpha=32,
                init_lora_weights="pissa_niter_16",
            ),
            ["Fast PiSSA trades exact SVD quality for much faster initialization."],
        )
    )

    variants.append(
        (
            "qalora_gptq",
            LoraConfig(
                task_type="CAUSAL_LM",
                target_modules="all-linear",
                use_qalora=True,
                qalora_group_size=16,
            ),
            ["QALoRA is currently implemented for GPTQ and requires divisible input dimensions."],
        )
    )

    variants.append(
        (
            "alora_invocation",
            LoraConfig(
                task_type="CAUSAL_LM",
                target_modules="all-linear",
                alora_invocation_tokens=[32000, 32001],
            ),
            ["aLoRA requires the invocation token sequence to be present in every input and cannot be merged."],
        )
    )

    variants.append(
        (
            "trainable_tokens_plus_lora",
            LoraConfig(
                task_type="CAUSAL_LM",
                target_modules="all-linear",
                trainable_token_indices={"embed_tokens": [32000, 32001]},
            ),
            ["Add tokens and resize embeddings before applying PEFT; FSDP requires use_orig_params=True."],
        )
    )

    if module_available("scipy"):
        from peft import LoftQConfig

        variants.append(
            (
                "full_loftq_initialization",
                LoraConfig(
                    task_type="CAUSAL_LM",
                    target_modules="all-linear",
                    init_lora_weights="loftq",
                    loftq_config=LoftQConfig(loftq_bits=4, loftq_iter=1),
                ),
                ["Use only with an unquantized base model; PEFT quantizes the backbone during initialization."],
            )
        )

    try:
        from peft import EvaConfig

        variants.append(
            (
                "eva_activation_svd",
                LoraConfig(
                    task_type="CAUSAL_LM",
                    target_modules="all-linear",
                    init_lora_weights="eva",
                    eva_config=EvaConfig(rho=2.0),
                ),
                ["Call initialize_lora_eva_weights(peft_model, dataloader) after wrapping."],
            )
        )
    except Exception as exc:  # pragma: no cover - depends on PEFT version surface
        variants.append(("eva_activation_svd", None, [f"Skipped EvaConfig import: {exc}"]))

    try:
        from peft import CordaConfig

        variants.append(
            (
                "corda_kpm",
                LoraConfig(
                    task_type="CAUSAL_LM",
                    target_modules="all-linear",
                    init_lora_weights="corda",
                    corda_config=CordaConfig(corda_method="kpm"),
                ),
                ["Run CorDA preprocessing over representative data before wrapping."],
            )
        )
    except Exception as exc:  # pragma: no cover - depends on PEFT version surface
        variants.append(("corda_kpm", None, [f"Skipped CordaConfig import: {exc}"]))

    try:
        from peft import LoraGAConfig

        variants.append(
            (
                "lora_ga_full_precision",
                LoraConfig(
                    task_type="CAUSAL_LM",
                    target_modules="all-linear",
                    init_lora_weights="lora_ga",
                    lora_ga_config=LoraGAConfig(direction="ArB2r", scale="stable"),
                ),
                ["Requires preprocess_loraga and full-precision weights; not for quantized models."],
            )
        )
    except Exception as exc:  # pragma: no cover - depends on PEFT version surface
        variants.append(("lora_ga_full_precision", None, [f"Skipped LoraGAConfig import: {exc}"]))

    return variants


def dependency_report() -> list[dict[str, object]]:
    return [
        {"package": package, "available": module_available(package), "used_for": purpose}
        for package, purpose in OPTIONAL_BACKENDS.items()
    ]


def unavailable_report(exc: Exception) -> dict:
    return {
        "peft_import_ok": False,
        "peft_import_error": str(exc),
        "install_guidance": "Install PEFT with `pip install peft` or use an editable source install for contributor checkouts.",
        "variants": [
            {"name": name, "ok": False, "notes": [note, "Not constructed because PEFT could not be imported."]}
            for name, note in VARIANT_NOTES
        ],
        "optional_dependencies": dependency_report(),
    }


def run_check(as_json: bool) -> int:
    try:
        import peft
    except Exception as exc:
        report = unavailable_report(exc)
        if as_json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print("PEFT import unavailable; representative configs were not constructed.")
            print(f"Reason: {exc}")
            print(report["install_guidance"])
            print("\nOptional dependency caveats:")
            for dep in report["optional_dependencies"]:
                state = "available" if dep["available"] else "missing"
                print(f"- {dep['package']}: {state} ({dep['used_for']})")
        return 0

    warnings.simplefilter("always")
    captured_warnings = []
    variants = []
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        for name, config, notes in build_variants():
            if config is None:
                variants.append({"name": name, "ok": False, "notes": notes})
            else:
                variants.append({"name": name, "ok": True, "config": safe_config_summary(config), "notes": notes})
        captured_warnings = [str(record.message) for record in records]

    report = {
        "peft_import_ok": True,
        "peft_version": getattr(peft, "__version__", "unknown"),
        "variants": variants,
        "optional_dependencies": dependency_report(),
        "warnings": captured_warnings,
        "loftq_replacement_note": (
            "For already quantized bitsandbytes 4-bit models, build ordinary LoRA first and then call "
            "replace_lora_weights_loftq(peft_model); do not set init_lora_weights='loftq'."
        ),
    }

    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"PEFT import OK: version {report['peft_version']}")
        print("\nRepresentative LoraConfig variants:")
        for item in variants:
            status = "OK" if item["ok"] else "SKIP"
            print(f"- {status} {item['name']}")
            for note in item.get("notes", []):
                print(f"  note: {note}")
        print("\nOptional dependency caveats:")
        for dep in report["optional_dependencies"]:
            state = "available" if dep["available"] else "missing"
            print(f"- {dep['package']}: {state} ({dep['used_for']})")
        if captured_warnings:
            print("\nWarnings captured while constructing configs:")
            for message in captured_warnings:
                print(f"- {message}")
        print(f"\nLoftQ replacement: {report['loftq_replacement_note']}")

    failed = [item for item in variants if not item["ok"] and not item["notes"]]
    return 1 if failed else 0


def list_variants() -> int:
    print("Representative variants constructed by --check:")
    for name, note in VARIANT_NOTES:
        print(f"- {name}")
        print(f"  {note}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="construct representative LoraConfig objects")
    parser.add_argument("--list-variants", action="store_true", help="list representative variants and caveats")
    parser.add_argument("--json", action="store_true", help="emit JSON for --check")
    args = parser.parse_args()

    if args.list_variants:
        return list_variants()
    if args.check or args.json:
        return run_check(as_json=args.json)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
