#!/usr/bin/env python
"""Render a self-contained LMFlow alignment recipe.

This helper prints copyable Python heredocs for reward modeling, DPO,
DPOv2, iterative DPO, RAFT, or LoRA merge workflows. It does not execute
training on its own.
"""

from __future__ import annotations

import argparse
from textwrap import indent


def render_kwargs(kwargs: dict[str, object]) -> str:
    parts: list[str] = []
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


def wrap(body: str) -> str:
    return "python - <<'PY'\n" + indent(body, "") + "\nPY"


def reward_recipe(args: argparse.Namespace) -> str:
    body = f'''from lmflow.args import AutoArguments, DatasetArguments, ModelArguments
from lmflow.datasets import Dataset
from lmflow.models.auto_model import AutoModel
from lmflow.pipeline.auto_pipeline import AutoPipeline

pipeline_name = "rm_tuner"
PipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)
model_args = ModelArguments({render_kwargs({"model_name_or_path": args.model_name_or_path, "arch_type": "text_regression", "trust_remote_code": args.trust_remote_code})})
data_args = DatasetArguments({render_kwargs({"dataset_path": args.dataset_path, "conversation_template": args.conversation_template})})
pipeline_args = PipelineArguments({render_kwargs({"output_dir": args.output_dir, "num_train_epochs": args.num_train_epochs, "learning_rate": args.learning_rate, "per_device_train_batch_size": args.per_device_train_batch_size, "gradient_accumulation_steps": args.gradient_accumulation_steps, "report_to": args.report_to, "do_train": True})})
finetuner = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args)
model = AutoModel.get_model(model_args)
dataset = Dataset(data_args)
finetuner.tune(model=model, dataset=dataset)'''
    return wrap(body)


def dpo_recipe(args: argparse.Namespace) -> str:
    body = f'''from lmflow.args import AutoArguments, DatasetArguments, ModelArguments
from lmflow.models.auto_model import AutoModel
from lmflow.pipeline.auto_pipeline import AutoPipeline

pipeline_name = "dpo_aligner"
PipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)
model_args = ModelArguments({render_kwargs({"model_name_or_path": args.model_name_or_path, "trust_remote_code": args.trust_remote_code})})
data_args = DatasetArguments({render_kwargs({"dataset_path": args.dataset_path, "conversation_template": args.conversation_template})})
pipeline_args = PipelineArguments({render_kwargs({"output_dir": args.output_dir, "max_steps": args.max_steps, "per_device_train_batch_size": args.per_device_train_batch_size, "per_device_eval_batch_size": args.per_device_eval_batch_size, "gradient_accumulation_steps": args.gradient_accumulation_steps, "learning_rate": args.learning_rate, "eval_steps": args.eval_steps, "save_steps": args.save_steps, "logging_steps": args.logging_steps, "warmup_steps": args.warmup_steps, "optimizer_type": args.optimizer_type, "lr_scheduler_type": args.lr_scheduler_type, "run_name": args.run_name, "seed": args.seed, "report_to": args.report_to})})
aligner = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args)
model = AutoModel.get_model(model_args)
aligner.align(model=model, dataset=None, reward_model=None)'''
    return wrap(body)


def dpov2_recipe(args: argparse.Namespace) -> str:
    body = f'''import copy

from lmflow.args import AutoArguments, DatasetArguments, ModelArguments
from lmflow.datasets import Dataset
from lmflow.models.auto_model import AutoModel
from lmflow.pipeline.auto_pipeline import AutoPipeline

pipeline_name = "dpov2_aligner"
PipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)
model_args = ModelArguments({render_kwargs({"model_name_or_path": args.model_name_or_path, "trust_remote_code": args.trust_remote_code})})
ref_model_args = ModelArguments({render_kwargs({"model_name_or_path": args.reference_model_name_or_path, "trust_remote_code": args.trust_remote_code})})
data_args = DatasetArguments({render_kwargs({"dataset_path": args.dataset_path, "conversation_template": args.conversation_template})})
pipeline_args = PipelineArguments({render_kwargs({"eval_dataset_path": args.eval_dataset_path, "output_dir": args.output_dir, "num_train_epochs": args.num_train_epochs, "per_device_train_batch_size": args.per_device_train_batch_size, "per_device_eval_batch_size": args.per_device_eval_batch_size, "gradient_accumulation_steps": args.gradient_accumulation_steps, "learning_rate": args.learning_rate, "save_strategy": args.save_strategy, "evaluation_strategy": args.evaluation_strategy, "eval_steps": args.eval_steps, "save_steps": args.save_steps, "warmup_steps": args.warmup_steps, "optim": args.optim, "bf16": args.bf16, "run_name": args.run_name, "seed": args.seed, "report_to": args.report_to})})
train_dataset = Dataset(data_args)
eval_data_args = copy.deepcopy(data_args)
eval_data_args.dataset_path = pipeline_args.eval_dataset_path
eval_dataset = Dataset(eval_data_args)
model = AutoModel.get_model(model_args)
ref_model = AutoModel.get_model(ref_model_args)
aligner = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args, ref_model_args=ref_model_args)
aligner.align(model=model, ref_model=ref_model, train_dataset=train_dataset, eval_dataset=eval_dataset)'''
    return wrap(body)


def iterative_dpo_recipe(args: argparse.Namespace) -> str:
    dataset_list = ", ".join(repr(item) for item in args.dataset_path_list)
    body = f'''import copy

from lmflow.args import AutoArguments, DatasetArguments, ModelArguments
from lmflow.datasets import Dataset
from lmflow.pipeline.auto_pipeline import AutoPipeline

pipeline_name = "iterative_dpo_aligner"
PipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)
model_args = ModelArguments({render_kwargs({"model_name_or_path": args.model_name_or_path, "trust_remote_code": args.trust_remote_code})})
ref_model_args = ModelArguments({render_kwargs({"model_name_or_path": args.reference_model_name_or_path, "trust_remote_code": args.trust_remote_code})})
reward_model_args = ModelArguments({render_kwargs({"model_name_or_path": args.reward_model_name_or_path, "arch_type": "text_regression", "trust_remote_code": args.trust_remote_code})})
data_args = DatasetArguments({render_kwargs({"dataset_path": None, "conversation_template": args.conversation_template, "preprocessing_num_workers": args.preprocessing_num_workers})})
pipeline_args = PipelineArguments(dataset_path_list=[{dataset_list}], output_dir={args.output_dir!r}, run_name={args.run_name!r}, random_seed={args.random_seed!r}, enable_distributed_inference={bool(args.enable_distributed_inference)}, distributed_inference_num_instances={args.distributed_inference_num_instances!r}, do_response_generation={bool(args.do_response_generation)}, do_scoring={bool(args.do_scoring)}, do_dpo_align={bool(args.do_dpo_align)}, bf16={bool(args.bf16)}, num_train_epochs={args.num_train_epochs!r}, learning_rate={args.learning_rate!r}, gradient_accumulation_steps={args.gradient_accumulation_steps!r}, loss_type={args.loss_type!r}, optim={args.optim!r}, report_to={args.report_to!r})
dataset_list = []
for dataset_path in pipeline_args.dataset_path_list:
    iter_data_args = copy.deepcopy(data_args)
    iter_data_args.dataset_path = dataset_path
    dataset_list.append(Dataset(iter_data_args))
aligner = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args, ref_model_args=ref_model_args, reward_model_args=reward_model_args)
aligner.align(dataset_list=dataset_list)'''
    return wrap(body)


def raft_recipe(args: argparse.Namespace) -> str:
    body = f'''from dataclasses import dataclass, field
from typing import Optional

from transformers import AutoTokenizer, HfArgumentParser, pipeline

from lmflow.args import AutoArguments, DatasetArguments, ModelArguments
from lmflow.datasets.dataset import Dataset
from lmflow.models.auto_model import AutoModel
from lmflow.pipeline.auto_pipeline import AutoPipeline

@dataclass
class RewardArguments:
    reward_type: Optional[str] = field(
        default={args.reward_type!r},
        metadata={{"help": "type of reward model, support huggingface pipeline."}},
    )
    reward_model_or_path: Optional[str] = field(
        default={args.reward_model_or_path!r},
        metadata={{"help": "reward model name (huggingface) or its path"}},
    )
    reward_task: Optional[str] = field(
        default={args.reward_task!r},
        metadata={{"help": "type of reward task, such as sentiment-analysis or detoxic"}},
    )
    reward_model_args: Optional[str] = field(
        default={args.reward_model_args!r},
        metadata={{"help": "extra arguments required by the reward model"}},
    )


def get_reward_function(reward_args, pipeline_args):
    if reward_args.reward_type == "hf_pipeline":
        rm_tokenizer = AutoTokenizer.from_pretrained(reward_args.reward_model_or_path)
        rm_tokenizer.pad_token = rm_tokenizer.eos_token
        rm_tokenizer.pad_token_id = rm_tokenizer.eos_token_id
        rm_tokenizer.padding_side = "left"
        hf_pipe = pipeline(
            reward_args.reward_task,
            model=reward_args.reward_model_or_path,
            device=f"cuda:{{pipeline_args.local_rank}}",
            tokenizer=rm_tokenizer,
        )

        def reward_func(dataset: Dataset):
            if dataset.type != "text_only":
                raise NotImplementedError('reward function only accepts "text_only" datasets')
            pipe_kwargs = {{"return_all_scores": True, "function_to_apply": "none", "batch_size": 1}}
            data_dict = dataset.to_dict()
            texts_for_rewards = [sample["text"] for sample in data_dict["instances"]]
            pipe_outputs = hf_pipe(texts_for_rewards, **pipe_kwargs)
            rewards = [output[0]["score"] for output in pipe_outputs]
            return Dataset.create_from_dict(
                {{"type": "float_only", "instances": [{{"value": reward}} for reward in rewards]}}
            )

        return reward_func
    raise NotImplementedError(f'unsupported reward type "{{reward_args.reward_type}}"')


pipeline_name = "raft_aligner"
PipelineArguments = AutoArguments.get_pipeline_args_class(pipeline_name)
model_args = ModelArguments({render_kwargs({"model_name_or_path": args.model_name_or_path, "trust_remote_code": args.trust_remote_code})})
data_args = DatasetArguments({render_kwargs({"dataset_path": args.dataset_path, "conversation_template": args.conversation_template})})
pipeline_args = PipelineArguments({render_kwargs({"output_dir": args.output_dir, "num_raft_iteration": args.num_raft_iteration, "collection_strategy": args.collection_strategy, "raft_batch_size": args.raft_batch_size, "top_reward_percentage": args.top_reward_percentage, "random_seed": args.random_seed, "bf16": args.bf16, "learning_rate": args.learning_rate, "gradient_accumulation_steps": args.gradient_accumulation_steps, "run_name": args.run_name, "report_to": args.report_to})})
reward_args = RewardArguments()
aligner = AutoPipeline.get_pipeline(pipeline_name=pipeline_name, model_args=model_args, data_args=data_args, pipeline_args=pipeline_args)
dataset = Dataset(data_args)
model = AutoModel.get_model(model_args)
reward_function = get_reward_function(reward_args, pipeline_args)
reward_model_args = ModelArguments(arch_type="text_regression")
reward_model = AutoModel.get_model(reward_model_args)
reward_model.register_inference_function(reward_function)
aligner.align(model=model, dataset=dataset, reward_model=reward_model)'''
    return wrap(body)


def merge_recipe(args: argparse.Namespace) -> str:
    body = f'''from lmflow.args import ModelArguments
from lmflow.models.auto_model import AutoModel

model_args = ModelArguments({render_kwargs({"model_name_or_path": args.model_name_or_path, "lora_model_path": args.lora_model_path, "arch_type": args.arch_type})})
model = AutoModel.get_model(model_args, do_train=False, device="cpu")
model.save({args.output_model_path!r}, save_full_model=True)'''
    return wrap(body)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a self-contained LMFlow alignment recipe.")
    parser.add_argument("--mode", choices=["reward", "dpo", "dpov2", "iterative-dpo", "raft", "merge-lora"], default="reward")
    parser.add_argument("--model-name-or-path", required=True)
    parser.add_argument("--dataset-path", default=None)
    parser.add_argument("--dataset-path-list", nargs="*", default=[])
    parser.add_argument("--reference-model-name-or-path", default=None)
    parser.add_argument("--reward-model-name-or-path", default=None)
    parser.add_argument("--lora-model-path", default=None)
    parser.add_argument("--output-model-path", default=None)
    parser.add_argument("--output-dir", default="./output_models/alignment")
    parser.add_argument("--eval-dataset-path", default=None)
    parser.add_argument("--conversation-template", default="llama3")
    parser.add_argument("--arch-type", default="decoder_only")
    parser.add_argument("--trust-remote-code", action="store_true")
    parser.add_argument("--run-name", default="alignment")
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--preprocessing-num-workers", type=int, default=16)
    parser.add_argument("--enable-distributed-inference", action="store_true")
    parser.add_argument("--distributed-inference-num-instances", type=int, default=1)
    parser.add_argument("--do-response-generation", action="store_true", default=True)
    parser.add_argument("--do-scoring", action="store_true", default=True)
    parser.add_argument("--do-dpo-align", action="store_true", default=True)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--per-device-train-batch-size", type=int, default=1)
    parser.add_argument("--per-device-eval-batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=1)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--eval-steps", type=int, default=100)
    parser.add_argument("--save-steps", type=int, default=500)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--warmup-steps", type=int, default=0)
    parser.add_argument("--save-strategy", default="steps")
    parser.add_argument("--evaluation-strategy", default="steps")
    parser.add_argument("--optimizer-type", default="adamw_torch")
    parser.add_argument("--lr-scheduler-type", default="cosine")
    parser.add_argument("--optim", default="adamw_torch")
    parser.add_argument("--bf16", action="store_true", default=True)
    parser.add_argument("--report-to", default="none")
    parser.add_argument("--loss-type", default="sigmoid")
    parser.add_argument("--mask-prompt", action="store_true", default=False)
    parser.add_argument("--length-penalty", type=float, default=1.0)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--max-prompt-length", type=int, default=512)
    parser.add_argument("--sampling-paired-method", default="top")
    parser.add_argument("--margin-scale", type=float, default=1.0)
    parser.add_argument("--num-raft-iteration", type=int, default=1)
    parser.add_argument("--collection-strategy", default="top")
    parser.add_argument("--raft-batch-size", type=int, default=1)
    parser.add_argument("--top-reward-percentage", type=float, default=0.2)
    parser.add_argument("--reward-type", default="hf_pipeline")
    parser.add_argument("--reward-task", default="sentiment-analysis")
    parser.add_argument("--reward-model-args", default='return_all_scores=True, function_to_apply="none", batch_size=1')
    parser.add_argument("--output-reward-path", default=None)
    args = parser.parse_args()

    if args.mode == "reward":
        print(reward_recipe(args))
    elif args.mode == "dpo":
        print(dpo_recipe(args))
    elif args.mode == "dpov2":
        print(dpov2_recipe(args))
    elif args.mode == "iterative-dpo":
        print(iterative_dpo_recipe(args))
    elif args.mode == "raft":
        print(raft_recipe(args))
    else:
        print(merge_recipe(args))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
