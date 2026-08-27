#!/usr/bin/env python3
"""Generate benchmark outputs and compute executable rate."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from llm_server import llm_inference
from calc_execute_rate import execute_rate_main
from transformers import AutoTokenizer

opts = ["O0", "O1", "O2", "O3"]


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--model_path", type=str, required=True)
    arg_parser.add_argument("--dataset_path", type=str, required=True)
    arg_parser.add_argument("--decompiler", type=str, default="asm")
    arg_parser.add_argument("--gpus", type=int, default=1)
    arg_parser.add_argument("--max_num_seqs", type=int, default=1)
    arg_parser.add_argument("--gpu_memory_utilization", type=float, default=0.95)
    arg_parser.add_argument("--temperature", type=float, default=0)
    arg_parser.add_argument("--max_total_tokens", type=int, default=30000)
    arg_parser.add_argument("--max_new_tokens", type=int, default=512)
    arg_parser.add_argument("--stop_sequences", type=str, default=None)
    arg_parser.add_argument("--output_path", type=str, default="./data/humaneval")
    arg_parser.add_argument("--only_save", type=int, default=0)
    args = arg_parser.parse_args()

    before = "# This is the assembly code:\n"
    after = "\n# What is the source code?\n"
    with open(args.dataset_path, "r", encoding="utf-8") as f:
        samples = json.load(f)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if args.stop_sequences is None:
        args.stop_sequences = [tokenizer.eos_token]

    results = []
    inputs = []
    infos = []
    for sample in samples:
        prompt = before + sample[args.decompiler].strip() + after
        inputs.append(prompt)
        infos.append({"opt": sample["opt"], "language": sample["language"]})

    gen_results = llm_inference(
        inputs,
        args.model_path,
        args.gpus,
        args.max_total_tokens,
        args.gpu_memory_utilization,
        args.temperature,
        args.max_new_tokens,
        args.stop_sequences,
    )
    gen_results = [gen_result[0] for gen_result in gen_results]

    gen_results_opt = {}
    if args.output_path:
        if os.path.exists(args.output_path):
            shutil.rmtree(args.output_path)
        for opt in opts:
            os.makedirs(os.path.join(args.output_path, opt), exist_ok=True)
            gen_results_opt[opt] = []
        for idx_sample, sample in enumerate(gen_results):
            save_path = os.path.join(
                args.output_path,
                infos[idx_sample]["opt"],
                f"{idx_sample}_{infos[idx_sample]['opt']}.{infos[idx_sample]['language']}",
            )
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(gen_results[idx_sample])
            gen_results_opt[infos[idx_sample]["opt"]].append(gen_results[idx_sample])

    if not args.only_save:
        eval_results, comp, exe = execute_rate_main(samples, gen_results, num_workers=32)
        results = {"O0": 0, "O1": 0, "O2": 0, "O3": 0}
        total = {"O0": 0, "O1": 0, "O2": 0, "O3": 0}
        for idx, res in enumerate(eval_results):
            results[infos[idx]["opt"]] += res[1]
            total[infos[idx]["opt"]] += 1
        name = args.dataset_path.split("/")[-1]
        print(f"dataset: {name}")
        for opt in opts:
            exe_rate = results[opt] * 1.0 / total[opt]
            print(f"{opt}: {exe_rate * 100:.2f}")
            with open(os.path.join(args.output_path, args.output_path.split('/')[-1] + "_results.txt"), "a", encoding="utf-8") as f:
                f.write(f"{opt}: {exe_rate * 100:.2f}\n")


if __name__ == "__main__":
    main()
