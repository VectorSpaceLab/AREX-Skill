#!/usr/bin/env python3
"""Validate PEFT prompt/soft-method config construction without loading a model.

The script is intentionally lightweight: it imports PEFT, constructs representative
configs, and reports method-specific constraints that fail at config time.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from typing import Any


def _stringify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _stringify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_stringify(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def _config_summary(config: Any) -> dict[str, Any]:
    if is_dataclass(config):
        data = asdict(config)
    else:
        data = dict(getattr(config, "__dict__", {}))
    interesting_keys = {
        "task_type",
        "peft_type",
        "num_virtual_tokens",
        "num_transformer_submodules",
        "prompt_tuning_init",
        "encoder_reparameterization_type",
        "num_tasks",
        "num_ranks",
        "cpt_token_ids",
        "cpt_mask",
        "cpt_tokens_type_mask",
        "num_frozen_tokens",
        "token_indices",
        "target_modules",
        "adapter_len",
        "adapter_layers",
    }
    return {key: _stringify(value) for key, value in data.items() if key in interesting_keys and value is not None}


def _attempt(name: str, factory, expected_failure: bool = False) -> dict[str, Any]:
    try:
        config = factory()
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report all config construction failures.
        return {
            "name": name,
            "ok": expected_failure,
            "expected_failure": expected_failure,
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
    return {
        "name": name,
        "ok": not expected_failure,
        "expected_failure": expected_failure,
        "summary": _config_summary(config),
    }


def build_checks() -> list[dict[str, Any]]:
    from peft import (
        AdaptionPromptConfig,
        CPTConfig,
        CartridgeConfig,
        MultitaskPromptTuningConfig,
        PrefixTuningConfig,
        PromptEncoderConfig,
        PromptTuningConfig,
        TaskType,
        TrainableTokensConfig,
    )

    return [
        _attempt(
            "prompt_tuning_seq2seq_text",
            lambda: PromptTuningConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                num_virtual_tokens=12,
                prompt_tuning_init="TEXT",
                prompt_tuning_init_text="Summarize the input.",
                tokenizer_name_or_path="t5-small",
            ),
        ),
        _attempt(
            "prompt_tuning_text_missing_tokenizer",
            lambda: PromptTuningConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                num_virtual_tokens=12,
                prompt_tuning_init="TEXT",
                prompt_tuning_init_text="Summarize the input.",
            ),
            expected_failure=True,
        ),
        _attempt(
            "prefix_tuning_causal_projection",
            lambda: PrefixTuningConfig(
                task_type=TaskType.CAUSAL_LM,
                num_virtual_tokens=8,
                prefix_projection=True,
                encoder_hidden_size=256,
            ),
        ),
        _attempt(
            "p_tuning_mlp",
            lambda: PromptEncoderConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                num_virtual_tokens=10,
                encoder_reparameterization_type="MLP",
                encoder_hidden_size=256,
                encoder_num_layers=2,
            ),
        ),
        _attempt(
            "multitask_prompt_random",
            lambda: MultitaskPromptTuningConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                num_virtual_tokens=10,
                num_tasks=3,
                num_ranks=2,
                prompt_tuning_init="RANDOM",
            ),
        ),
        _attempt(
            "cpt_causal_lm",
            lambda: CPTConfig(
                task_type=TaskType.CAUSAL_LM,
                cpt_token_ids=[0, 1, 2, 3],
                cpt_mask=[1, 1, 1, 1],
                cpt_tokens_type_mask=[1, 2, 3, 4],
                opt_weighted_loss_type="decay",
            ),
        ),
        _attempt(
            "cpt_rejects_seq2seq",
            lambda: CPTConfig(
                task_type=TaskType.SEQ_2_SEQ_LM,
                cpt_token_ids=[0, 1],
            ),
            expected_failure=True,
        ),
        _attempt(
            "cpt_rejects_mask_length_mismatch",
            lambda: CPTConfig(
                task_type=TaskType.CAUSAL_LM,
                cpt_token_ids=[0, 1, 2],
                cpt_mask=[1, 1],
                cpt_tokens_type_mask=[1, 2, 3],
            ),
            expected_failure=True,
        ),
        _attempt(
            "cartridge_causal_lm",
            lambda: CartridgeConfig(
                task_type=TaskType.CAUSAL_LM,
                num_virtual_tokens=6,
                num_frozen_tokens=1,
            ),
        ),
        _attempt(
            "cartridge_rejects_too_many_frozen_tokens",
            lambda: CartridgeConfig(
                task_type=TaskType.CAUSAL_LM,
                num_virtual_tokens=4,
                num_frozen_tokens=5,
            ),
            expected_failure=True,
        ),
        _attempt(
            "adaption_prompt_llama_style",
            lambda: AdaptionPromptConfig(
                task_type=TaskType.CAUSAL_LM,
                target_modules="self_attn",
                adapter_len=10,
                adapter_layers=4,
            ),
        ),
        _attempt(
            "trainable_tokens_default_embedding",
            lambda: TrainableTokensConfig(
                token_indices=[100, 101],
            ),
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    try:
        results = build_checks()
    except ModuleNotFoundError as exc:
        if exc.name == "peft":
            message = "PEFT is not importable. Install it with `pip install peft` or use a source editable install."
        else:
            message = (
                f"Required import '{exc.name}' is missing while importing PEFT. "
                "Install PEFT with its runtime dependencies before running config checks."
            )
        if args.json:
            print(json.dumps({"ok": False, "error": message}, indent=2, sort_keys=True))
        else:
            print(message)
        return 2

    failed = [item for item in results if not item["ok"]]

    if args.json:
        print(json.dumps({"ok": not failed, "checks": results}, indent=2, sort_keys=True))
    else:
        for item in results:
            status = "PASS" if item["ok"] else "FAIL"
            expected = " expected-failure" if item.get("expected_failure") else ""
            print(f"[{status}] {item['name']}{expected}")
            if "message" in item:
                print(f"  {item['error_type']}: {item['message']}")
            else:
                print(f"  {item['summary']}")
        print("\nSummary:")
        print(f"  checks: {len(results)}")
        print(f"  unexpected failures: {len(failed)}")
        print("  constraints: TEXT init requires text+tokenizer; CPT requires CAUSAL_LM and aligned CPT masks; CARTRIDGE frozen tokens must not exceed virtual tokens.")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
