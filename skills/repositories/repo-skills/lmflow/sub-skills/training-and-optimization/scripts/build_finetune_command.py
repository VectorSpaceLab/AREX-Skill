#!/usr/bin/env python
"""Render a self-contained LMFlow fine-tuning command.

This helper prints a copyable Python heredoc that imports the installed LMFlow
package. It does not start training on its own.

Examples:
  python scripts/build_finetune_command.py --method lora --model-name-or-path gpt2 \
    --dataset-path data/alpaca/train_conversation --output-dir output_models/finetune_lora
"""

from __future__ import annotations

import argparse
from textwrap import indent


def py_bool(value: bool) -> str:
    return "True" if value else "False"


def render_kwargs(kwargs: dict[str, object]) -> str:
    items = []
    for key, value in kwargs.items():
        if value is None:
            continue
        if isinstance(value, bool):
            items.append(f"{key}={py_bool(value)}")
        elif isinstance(value, str):
            items.append(f"{key}={value!r}")
        else:
            items.append(f"{key}={value!r}")
    return ", ".join(items)


def make_command(args: argparse.Namespace) -> str:
    model_kwargs = {
        "model_name_or_path": args.model_name_or_path,
        "trust_remote_code": bool(args.trust_remote_code),
        "torch_dtype": args.torch_dtype,
    }
    if args.method in {"lora", "qlora", "lisa", "custom"}:
        model_kwargs["use_lora"] = args.method in {"lora", "qlora"}
        model_kwargs["use_qlora"] = args.method == "qlora"
        model_kwargs["quant_bit"] = args.quant_bit if args.method == "qlora" else None
        model_kwargs["lora_r"] = args.lora_r
        model_kwargs["lora_alpha"] = args.lora_alpha
        model_kwargs["lora_dropout"] = args.lora_dropout
    data_kwargs = {
        "dataset_path": args.dataset_path,
        "conversation_template": args.conversation_template,
        "disable_group_texts": bool(args.disable_group_texts),
        "validation_split_percentage": args.validation_split_percentage,
        "block_size": args.block_size,
        "preprocessing_num_workers": args.preprocessing_num_workers,
        "dataset_cache_dir": args.dataset_cache_dir,
        "overwrite_cache": bool(args.overwrite_cache),
    }
    pipeline_kwargs = {
        "output_dir": args.output_dir,
        "overwrite_output_dir": bool(args.overwrite_output_dir),
        "num_train_epochs": args.num_train_epochs,
        "learning_rate": args.learning_rate,
        "per_device_train_batch_size": args.per_device_train_batch_size,
        "gradient_accumulation_steps": args.gradient_accumulation_steps,
        "lr_scheduler_type": args.lr_scheduler_type,
        "bf16": bool(args.bf16),
        "seed": args.seed,
        "logging_steps": args.logging_steps,
        "save_steps": args.save_steps,
        "report_to": args.report_to,
        "do_train": True,
    }
    if args.method == "lisa":
        pipeline_kwargs["use_lisa"] = True
        pipeline_kwargs["lisa_activated_layers"] = args.lisa_activated_layers
        pipeline_kwargs["lisa_interval_steps"] = args.lisa_interval_steps
    if args.method == "custom":
        pipeline_kwargs["use_customized_optim"] = True
        pipeline_kwargs["customized_optim"] = args.customized_optim
        pipeline_kwargs["optim_dummy_beta1"] = args.optim_dummy_beta1
        pipeline_kwargs["optim_dummy_beta2"] = args.optim_dummy_beta2
        pipeline_kwargs["optim_beta1"] = args.optim_beta1
        pipeline_kwargs["optim_beta2"] = args.optim_beta2
        pipeline_kwargs["optim_beta3"] = args.optim_beta3
        pipeline_kwargs["optim_momentum"] = args.optim_momentum
        pipeline_kwargs["optim_weight_decay"] = args.optim_weight_decay
    if args.method == "qlora":
        model_kwargs["load_in_4bit"] = True

    body = f'''from lmflow.args import AutoArguments, DatasetArguments, ModelArguments\nfrom lmflow.datasets import Dataset\nfrom lmflow.models.auto_model import AutoModel\nfrom lmflow.pipeline.auto_pipeline import AutoPipeline\n\npipeline_name = "finetuner"\nPipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)\nmodel_args = ModelArguments({render_kwargs(model_kwargs)})\ndata_args = DatasetArguments({render_kwargs(data_kwargs)})\npipeline_args = PipelineArguments({render_kwargs(pipeline_kwargs)})\nfinetuner = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args)\ndataset = Dataset(data_args)\nmodel = AutoModel.get_model(model_args)\nfinetuner.tune(model=model, dataset=dataset)'''
    return "python - <<'PY'\n" + indent(body, "") + "\nPY"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a self-contained LMFlow fine-tuning command.")
    parser.add_argument("--method", choices=["full", "lora", "qlora", "lisa", "custom"], default="full")
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--conversation-template", default="llama3")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--torch-dtype", default="bfloat16")
    parser.add_argument("--disable-group-texts", action="store_true", default=True)
    parser.add_argument("--validation-split-percentage", type=int, default=0)
    parser.add_argument("--block-size", type=int, default=512)
    parser.add_argument("--preprocessing-num-workers", type=int, default=8)
    parser.add_argument("--dataset-cache-dir", default=None)
    parser.add_argument("--overwrite-cache", action="store_true")
    parser.add_argument("--overwrite-output-dir", action="store_true", default=True)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--logging-steps", type=int, default=20)
    parser.add_argument("--save-steps", type=int, default=5000)
    parser.add_argument("--report-to", default="none")
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.1)
    parser.add_argument("--quant-bit", type=int, default=4)
    parser.add_argument("--lisa-activated-layers", type=int, default=1)
    parser.add_argument("--lisa-interval-steps", type=int, default=20)
    parser.add_argument("--customized-optim", default="adabelief")
    parser.add_argument("--optim-dummy-beta1", type=float, default=0.9)
    parser.add_argument("--optim-dummy-beta2", type=float, default=0.999)
    parser.add_argument("--optim-beta1", type=float, default=0.9)
    parser.add_argument("--optim-beta2", type=float, default=0.999)
    parser.add_argument("--optim-beta3", type=float, default=0.9)
    parser.add_argument("--optim-momentum", type=float, default=0.999)
    parser.add_argument("--optim-weight-decay", type=float, default=0.0)
    args = parser.parse_args()
    print(make_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
