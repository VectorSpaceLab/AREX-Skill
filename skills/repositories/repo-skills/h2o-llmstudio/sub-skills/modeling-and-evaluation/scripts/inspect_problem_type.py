#!/usr/bin/env python3
"""Inspect H2O LLM Studio problem-type modeling/evaluation contracts.

Safe by default: this script prints static and import-level metadata only. It does
not instantiate a model, download model weights, start training, or call an AI
judge endpoint.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

# When the script is run from a source checkout by path, Python puts this
# script's directory on sys.path rather than the caller's working directory.
# Add the current working directory so import checks can see an unpacked or
# editable package without requiring model loading or installation changes.
CWD = str(Path.cwd())
if CWD not in sys.path:
    sys.path.insert(0, CWD)

PROBLEM_TYPES: dict[str, dict[str, Any]] = {
    "text_causal_language_modeling": {
        "display_name": "Causal language modeling",
        "config_class": "llm_studio.python_configs.text_causal_language_modeling_config.ConfigProblemBase",
        "model_class": "llm_studio.src.models.text_causal_language_modeling_model.Model",
        "backbone": "transformers.AutoModelForCausalLM",
        "forward_signature": "forward(self, batch: dict, padding: bool = True) -> dict",
        "generate_signature": "generate(self, batch: dict, cfg: Any, streamer=None)",
        "generation_route": "generate for BLEU/GPT-style metrics; forward for Perplexity",
        "forward_batch_keys": ["input_ids", "attention_mask", "special_tokens_mask", "labels"],
        "primary_outputs": ["loss", "perplexity when metric is Perplexity"],
        "loss_factory": "llm_studio.src.losses.text_causal_language_modeling_losses.Losses",
        "losses": {
            "TokenAveragedCrossEntropy": "next-token CrossEntropyLoss over flattened tokens; default/fallback",
            "SampleAveragedCrossEntropy": "next-token CrossEntropyLoss averaged per sample",
        },
        "metric_factory": "llm_studio.src.metrics.text_causal_language_modeling_metrics.Metrics",
        "metrics": {
            "BLEU": {"direction": "max", "reduce": "mean", "requires": ["predicted_text", "target_text"]},
            "GPT": {"direction": "max", "reduce": "mean", "requires": ["predicted_text", "target_text", "OpenAI-compatible endpoint"]},
            "Perplexity": {"direction": "min", "reduce": "mean", "requires": ["perplexity"]},
        },
        "plots_class": "llm_studio.src.plots.text_causal_language_modeling_plots.Plots",
    },
    "text_sequence_to_sequence_modeling": {
        "display_name": "Sequence-to-sequence modeling",
        "config_class": "llm_studio.python_configs.text_sequence_to_sequence_modeling_config.ConfigProblemBase",
        "model_class": "llm_studio.src.models.text_sequence_to_sequence_modeling_model.Model",
        "backbone": "transformers.AutoModelForSeq2SeqLM",
        "forward_signature": "forward(self, batch: dict, padding: bool = True) -> dict",
        "generate_signature": "generate(self, batch: dict, cfg: Any, streamer=None)",
        "generation_route": "generate for BLEU/GPT-style metrics; forward for Perplexity; generation keeps seq2seq output without removing a causal prompt prefix",
        "forward_batch_keys": ["prompt_input_ids", "prompt_attention_mask", "answer_input_ids", "answer_attention_mask"],
        "primary_outputs": ["loss", "perplexity when metric is Perplexity"],
        "loss_factory": "llm_studio.src.losses.text_causal_language_modeling_losses.Losses",
        "losses": {
            "TokenAveragedCrossEntropy": "inherited language-modeling loss option",
            "SampleAveragedCrossEntropy": "inherited language-modeling loss option",
        },
        "metric_factory": "llm_studio.src.metrics.text_causal_language_modeling_metrics.Metrics",
        "metrics": {
            "BLEU": {"direction": "max", "reduce": "mean", "requires": ["predicted_text", "target_text"]},
            "GPT": {"direction": "max", "reduce": "mean", "requires": ["predicted_text", "target_text", "OpenAI-compatible endpoint"]},
            "Perplexity": {"direction": "min", "reduce": "mean", "requires": ["perplexity"]},
        },
        "plots_class": "llm_studio.src.plots.text_causal_language_modeling_plots.Plots",
    },
    "text_dpo_modeling": {
        "display_name": "DPO preference modeling",
        "config_class": "llm_studio.python_configs.text_dpo_modeling_config.ConfigProblemBase",
        "model_class": "llm_studio.src.models.text_dpo_modeling_model.Model",
        "backbone": "transformers.AutoModelForCausalLM",
        "forward_signature": "forward(self, batch: dict, padding: bool = True) -> dict",
        "generate_signature": "generate(self, batch: dict, cfg: Any, streamer=None)",
        "generation_route": "generate like causal LM for BLEU/GPT-style metrics; forward for Perplexity and preference diagnostics",
        "forward_batch_keys": ["chosen_input_ids", "chosen_attention_mask", "chosen_labels", "rejected_input_ids", "rejected_attention_mask", "rejected_labels"],
        "primary_outputs": ["loss", "chosen_logps", "rejected_logps", "additional_log_chosen_rewards", "additional_log_rejected_rewards", "additional_log_reward_margin"],
        "loss_factory": "llm_studio.src.losses.text_dpo_modeling_losses.Losses",
        "losses": {
            "DPOLoss": "reference-model DPO loss; default/fallback",
            "DPOHingeLoss": "reference-model hinge variant; average log probability reduction",
            "DPOIPOLoss": "reference-model IPO variant; average log probability reduction",
            "KTOPairLoss": "paired KTO loss with reference scores",
            "CPOLoss": "CPO loss without reference model",
            "SimPOLoss": "SimPO loss without reference model; average log probability reduction",
        },
        "metric_factory": "llm_studio.src.metrics.text_causal_language_modeling_metrics.Metrics",
        "metrics": {
            "BLEU": {"direction": "max", "reduce": "mean", "requires": ["predicted_text", "target_text"]},
            "GPT": {"direction": "max", "reduce": "mean", "requires": ["predicted_text", "target_text", "OpenAI-compatible endpoint"]},
            "Perplexity": {"direction": "min", "reduce": "mean", "requires": ["perplexity", "additional rejected perplexity diagnostics"]},
        },
        "plots_class": "llm_studio.src.plots.text_dpo_modeling_plots.Plots",
    },
    "text_causal_classification_modeling": {
        "display_name": "Causal classification modeling",
        "config_class": "llm_studio.python_configs.text_causal_classification_modeling_config.ConfigProblemBase",
        "model_class": "llm_studio.src.models.text_causal_classification_modeling_model.Model",
        "backbone": "transformers.AutoModelForCausalLM plus nn.Linear(vocab_size, num_classes, bias=False)",
        "forward_signature": "forward(self, batch: dict, padding: bool = True) -> dict",
        "generate_signature": None,
        "generation_route": "forward only; classification is a non-generation problem type",
        "forward_batch_keys": ["prompt_input_ids", "prompt_attention_mask", "special_tokens_mask", "labels", "class_label"],
        "primary_outputs": ["loss", "logits"],
        "postprocess_outputs": ["probabilities", "predictions", "predicted_text"],
        "loss_factory": "llm_studio.src.losses.text_causal_classification_modeling_losses.Losses",
        "losses": {
            "CrossEntropyLoss": "single-label binary/multiclass cross entropy; default/fallback",
            "BinaryCrossEntropyLoss": "BCE-with-logits for binary or multi-label style targets",
        },
        "metric_factory": "llm_studio.src.metrics.text_causal_classification_modeling_metrics.Metrics",
        "metrics": {
            "AUC": {"direction": "max", "reduce": "mean", "requires": ["logits", "target_text"]},
            "Accuracy": {"direction": "max", "reduce": "mean", "requires": ["predictions", "target_text"]},
            "LogLoss": {"direction": "min", "reduce": "mean", "requires": ["probabilities", "target_text"]},
        },
        "plots_class": "llm_studio.src.plots.text_causal_classification_modeling_plots.Plots",
    },
    "text_causal_regression_modeling": {
        "display_name": "Causal regression modeling",
        "config_class": "llm_studio.python_configs.text_causal_regression_modeling_config.ConfigProblemBase",
        "model_class": "llm_studio.src.models.text_causal_regression_modeling_model.Model",
        "backbone": "transformers.AutoModelForCausalLM plus nn.Linear(vocab_size, len(answer_column), bias=False)",
        "forward_signature": "forward(self, batch: dict, padding: bool = True) -> dict",
        "generate_signature": None,
        "generation_route": "forward only; regression is a non-generation problem type",
        "forward_batch_keys": ["prompt_input_ids", "prompt_attention_mask", "special_tokens_mask", "labels", "class_label"],
        "primary_outputs": ["loss", "predictions"],
        "postprocess_outputs": ["predicted_text"],
        "loss_factory": "llm_studio.src.losses.text_causal_regression_modeling_losses.Losses",
        "losses": {
            "MSELoss": "mean squared error; default/fallback",
            "MAELoss": "mean absolute error implemented with L1Loss",
        },
        "metric_factory": "llm_studio.src.metrics.text_causal_regression_modeling_metrics.Metrics",
        "metrics": {
            "MAE": {"direction": "min", "reduce": "mean", "requires": ["predictions", "target_text"]},
            "MSE": {"direction": "min", "reduce": "mean", "requires": ["predictions", "target_text"]},
        },
        "plots_class": "llm_studio.src.plots.text_causal_classification_modeling_plots.Plots",
    },
}


def split_import_path(path: str) -> tuple[str, str]:
    module_name, _, attr = path.rpartition(".")
    if not module_name or not attr:
        raise ValueError(f"Not an import path: {path}")
    return module_name, attr


def verify_import_path(path: str | None) -> dict[str, Any]:
    if not path:
        return {"path": path, "status": "skipped"}
    module_name, attr = split_import_path(path)
    try:
        module = importlib.import_module(module_name)
        getattr(module, attr)
    except Exception as exc:  # noqa: BLE001 - report any import-time problem safely.
        return {"path": path, "status": "error", "error": f"{type(exc).__name__}: {exc}"}
    return {"path": path, "status": "ok"}


def verify_problem_type(info: dict[str, Any]) -> list[dict[str, Any]]:
    paths = [
        info.get("config_class"),
        info.get("model_class"),
        info.get("loss_factory"),
        info.get("metric_factory"),
        info.get("plots_class"),
    ]
    return [verify_import_path(path) for path in paths]


def selected_problem_types(name: str) -> dict[str, dict[str, Any]]:
    if name == "all":
        return deepcopy(PROBLEM_TYPES)
    if name not in PROBLEM_TYPES:
        raise SystemExit(f"Unknown problem type {name!r}. Use --help for choices.")
    return {name: deepcopy(PROBLEM_TYPES[name])}


def print_human(name: str, info: dict[str, Any], list_metrics: bool, verify_imports: bool) -> None:
    print(f"\n{name} - {info['display_name']}")
    print("- config:", info["config_class"])
    print("- model:", info["model_class"])
    print("- backbone:", info["backbone"])
    print("- forward:", info["forward_signature"])
    print("- generate:", info["generate_signature"] or "not exposed for this problem type")
    print("- route:", info["generation_route"])
    print("- batch keys:", ", ".join(info["forward_batch_keys"]))
    print("- losses:", ", ".join(info["losses"].keys()))
    if list_metrics:
        print("- metrics:")
        for metric_name, metric_info in sorted(info["metrics"].items()):
            reqs = ", ".join(metric_info["requires"])
            print(
                f"  * {metric_name}: direction={metric_info['direction']}, "
                f"reduce={metric_info['reduce']}, requires={reqs}"
            )
    else:
        print("- metrics:", ", ".join(sorted(info["metrics"].keys())))
    print("- plots:", info["plots_class"])
    if verify_imports:
        print("- import check:")
        for result in verify_problem_type(info):
            if result["status"] == "ok":
                print(f"  * ok: {result['path']}")
            elif result["status"] == "skipped":
                print("  * skipped")
            else:
                print(f"  * error: {result['path']} -> {result['error']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect H2O LLM Studio problem-type model/loss/metric/plot mappings "
            "without loading model weights."
        )
    )
    parser.add_argument(
        "--problem-type",
        default="all",
        choices=["all", *sorted(PROBLEM_TYPES.keys())],
        help="Problem type to inspect. Default: all.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--list-metrics",
        action="store_true",
        help="Show metric direction, reduction, and required result keys.",
    )
    parser.add_argument(
        "--verify-imports",
        action="store_true",
        help=(
            "Import the configured Python modules/classes to verify availability. "
            "This still does not instantiate a model or download weights."
        ),
    )
    args = parser.parse_args(argv)

    data = selected_problem_types(args.problem_type)
    if args.verify_imports:
        for info in data.values():
            info["import_check"] = verify_problem_type(info)

    if args.json:
        json.dump(data, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for name, info in data.items():
            print_human(name, info, args.list_metrics, args.verify_imports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
