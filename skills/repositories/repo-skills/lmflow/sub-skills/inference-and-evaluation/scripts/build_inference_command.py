#!/usr/bin/env python
"""Render a self-contained LMFlow inference or evaluation command.

This helper prints a copyable Python heredoc that imports the installed LMFlow
package. It does not start generation or evaluation by itself.

Examples:
  python scripts/build_inference_command.py --pipeline inferencer \
    --model-name-or-path gpt2 --dataset-path data/alpaca/prompt_only
"""

from __future__ import annotations

import argparse
from textwrap import indent


def render_kwargs(kwargs: dict[str, object]) -> str:
    parts = []
    for key, value in kwargs.items():
        if value is None:
            continue
        if isinstance(value, bool):
            parts.append(f"{key}={value}")
        elif isinstance(value, str):
            parts.append(f"{key}={value!r}")
        else:
            parts.append(f"{key}={value!r}")
    return ", ".join(parts)


def render_command(args: argparse.Namespace) -> str:
    model_kwargs = {
        "model_name_or_path": args.model_name_or_path,
        "arch_type": args.arch_type,
        "trust_remote_code": bool(args.trust_remote_code),
        "torch_dtype": args.torch_dtype,
    }
    if args.lora_model_path:
        model_kwargs["lora_model_path"] = args.lora_model_path
    if args.pipeline == "rm_inferencer":
        model_kwargs["arch_type"] = "text_regression"
    data_kwargs = {
        "dataset_path": args.dataset_path,
        "conversation_template": args.conversation_template,
        "dataset_cache_dir": args.dataset_cache_dir,
    }
    if args.pipeline == "evaluator":
        pipeline_kwargs = {
            "output_dir": args.output_dir,
            "use_wandb": bool(args.use_wandb),
            "random_seed": args.random_seed,
            "mixed_precision": args.mixed_precision,
            "deepspeed": args.deepspeed,
            "answer_type": args.answer_type,
            "prompt_structure": args.prompt_structure,
            "metric": args.metric,
            "max_new_tokens": args.max_new_tokens,
            "minibatch_size": args.minibatch_size,
            "save_inference_results": bool(args.save_inference_results),
            "inference_results_path": args.inference_results_path,
        }
    else:
        pipeline_kwargs = {
            "device": args.device,
            "inference_batch_size": args.inference_batch_size,
            "vllm_inference_batch_size": args.vllm_inference_batch_size,
            "temperature": args.temperature,
            "repetition_penalty": args.repetition_penalty,
            "max_new_tokens": args.max_new_tokens,
            "random_seed": args.random_seed,
            "deepspeed": args.deepspeed,
            "mixed_precision": args.mixed_precision,
            "do_sample": bool(args.do_sample),
            "return_logprob": bool(args.return_logprob),
            "use_beam_search": bool(args.use_beam_search),
            "num_output_sequences": args.num_output_sequences,
            "top_p": args.top_p,
            "top_k": args.top_k,
            "apply_chat_template": bool(args.apply_chat_template),
            "enable_decode_inference_result": bool(args.enable_decode_inference_result),
            "inference_engine": args.inference_engine,
            "inference_tensor_parallel_size": args.inference_tensor_parallel_size,
            "inference_data_parallel_size": args.inference_data_parallel_size,
            "inference_gpu_memory_utilization": args.inference_gpu_memory_utilization,
            "inference_max_model_len": args.inference_max_model_len,
            "enable_deterministic_inference": bool(args.enable_deterministic_inference),
            "attention_backend": args.attention_backend,
            "save_inference_results": bool(args.save_inference_results),
            "inference_results_path": args.inference_results_path,
        }

    body = f'''from lmflow.args import AutoArguments, DatasetArguments, ModelArguments\nfrom lmflow.datasets import Dataset\nfrom lmflow.models.auto_model import AutoModel\nfrom lmflow.pipeline.auto_pipeline import AutoPipeline\n\npipeline_name = {args.pipeline!r}\nPipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)\nmodel_args = ModelArguments({render_kwargs(model_kwargs)})\ndata_args = DatasetArguments({render_kwargs(data_kwargs)})\npipeline_args = PipelineArguments({render_kwargs(pipeline_kwargs)})\nmodel = AutoModel.get_model(model_args, do_train=False)\ndataset = Dataset(data_args)\npipeline = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args)\nif pipeline_name == "evaluator":\n    pipeline.evaluate(model=model, dataset=dataset, metric=pipeline_args.metric)\nelse:\n    pipeline.inference(model=model, dataset=dataset, max_new_tokens=pipeline_args.max_new_tokens, temperature=getattr(pipeline_args, "temperature", 0.0))'''
    return "python - <<'PY'\n" + indent(body, "") + "\nPY"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a self-contained LMFlow inference/evaluation command.")
    parser.add_argument("--pipeline", choices=["inferencer", "evaluator", "vllm_inferencer", "sglang_inferencer", "rm_inferencer"], default="inferencer")
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--dataset-path", required=True)
    parser.add_argument("--output-dir", default="./output_dir")
    parser.add_argument("--conversation-template", default=None)
    parser.add_argument("--dataset-cache-dir", default=None)
    parser.add_argument("--lora-model-path", default=None)
    parser.add_argument("--arch-type", default="decoder_only")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--torch-dtype", default=None)
    parser.add_argument("--device", default="cpu", choices=["cpu", "gpu"])
    parser.add_argument("--inference-batch-size", type=int, default=1)
    parser.add_argument("--vllm-inference-batch-size", type=int, default=1)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--repetition-penalty", type=float, default=1.0)
    parser.add_argument("--max-new-tokens", type=int, default=100)
    parser.add_argument("--random-seed", type=int, default=1)
    parser.add_argument("--deepspeed", default=None)
    parser.add_argument("--mixed-precision", default="bf16")
    parser.add_argument("--do-sample", action="store_true")
    parser.add_argument("--return-logprob", action="store_true")
    parser.add_argument("--use-beam-search", action="store_true")
    parser.add_argument("--num-output-sequences", type=int, default=8)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--top-k", type=int, default=-1)
    parser.add_argument("--apply-chat-template", action="store_true", default=True)
    parser.add_argument("--enable-decode-inference-result", action="store_true")
    parser.add_argument("--inference-engine", default="huggingface", choices=["huggingface", "vllm", "sglang"])
    parser.add_argument("--inference-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--inference-data-parallel-size", type=int, default=1)
    parser.add_argument("--inference-gpu-memory-utilization", type=float, default=0.95)
    parser.add_argument("--inference-max-model-len", type=int, default=None)
    parser.add_argument("--enable-deterministic-inference", action="store_true")
    parser.add_argument("--attention-backend", default=None)
    parser.add_argument("--save-inference-results", action="store_true")
    parser.add_argument("--inference-results-path", default=None)
    parser.add_argument("--use-wandb", action="store_true")
    parser.add_argument("--answer-type", default="text")
    parser.add_argument("--prompt-structure", default="{input}")
    parser.add_argument("--metric", default="accuracy")
    parser.add_argument("--minibatch-size", type=int, default=1)
    args = parser.parse_args()
    print(render_command(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
