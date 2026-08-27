#!/usr/bin/env python3
from __future__ import annotations

import argparse
import textwrap


def pos(v):
    value = int(v)
    if value <= 0:
        raise argparse.ArgumentTypeError("must be > 0")
    return value


def main():
    p = argparse.ArgumentParser(description="Validate Petals prompt-tuning planning options and print a no-download checklist/code skeleton.")
    p.add_argument("--task", choices=("causal-lm", "classification"), required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--dataset-name", default="DATASET_NAME")
    p.add_argument("--text-column", default="text")
    p.add_argument("--label-column", default="label")
    p.add_argument("--num-labels", type=int)
    p.add_argument("--tuning-mode", choices=("ptune", "deep_ptune"), default="ptune")
    p.add_argument("--pre-seq-len", type=pos, default=16)
    p.add_argument("--device", default="cuda")
    p.add_argument("--no-wandb", action="store_true")
    p.add_argument("--max-length", type=pos, default=256)
    args = p.parse_args()
    if args.task == "classification" and args.num_labels is not None and args.num_labels < 2:
        p.error("classification requires --num-labels >= 2")
    if args.task == "classification" and args.num_labels is None:
        args.num_labels = 2
    ctor = "AutoDistributedModelForCausalLM" if args.task == "causal-lm" else "AutoDistributedModelForSequenceClassification"
    extra = "" if args.task == "causal-lm" else f", num_labels={args.num_labels}"
    print(
        textwrap.dedent(
            f'''
            Petals prompt-tuning no-download plan
            Model: {args.model}
            Dataset: {args.dataset_name}
            Task: {args.task}
            Tuning: {args.tuning_mode}, pre_seq_len={args.pre_seq_len}
            Device: {args.device}; max_length={args.max_length}; W&B={'disabled' if args.no_wandb else 'optional after approval'}

            Checklist:
            - Confirm model/tokenizer, dataset, swarm, cache, and credentials are approved.
            - Remove unsupported zero-valued attention_mask before Petals forwards.
            - Print trainable params; optimizer should update prompts and local head only.
            - Gate CUDA AMP by actual CUDA availability.

            Skeleton:
            from petals import {ctor}
            model = {ctor}.from_pretrained({args.model!r}, tuning_mode={args.tuning_mode!r}, pre_seq_len={args.pre_seq_len}{extra}).to({args.device!r})
            trainables = [p for p in model.parameters() if p.requires_grad]
            # tokenize {args.text_column!r}; labels from {args.label_column!r}; omit attention_mask or ensure all ones
            # optimizer = torch.optim.AdamW(trainables, lr=1e-2)
            '''
        ).strip()
    )


if __name__ == "__main__":
    main()
