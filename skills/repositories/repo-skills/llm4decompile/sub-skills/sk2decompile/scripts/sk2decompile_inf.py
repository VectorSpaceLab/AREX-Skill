#!/usr/bin/env python3
"""Two-stage SK²Decompile inference helper."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

from transformers import AutoTokenizer
from vllm import LLM, SamplingParams


def _load_samples(dataset_path: str):
    if dataset_path.endswith(".json"):
        with open(dataset_path, "r", encoding="utf-8") as f:
            return json.load(f)
    if dataset_path.endswith(".jsonl"):
        samples = []
        with open(dataset_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(json.loads(line))
        return samples
    raise ValueError("dataset_path must end with .json or .jsonl")


def _llm_inference(inputs, model_path, gpus=1, max_total_tokens=8192, gpu_memory_utilization=0.8, temperature=0, max_new_tokens=512, stop_sequences=None):
    llm = LLM(
        model=model_path,
        tensor_parallel_size=gpus,
        max_model_len=max_total_tokens,
        gpu_memory_utilization=gpu_memory_utilization,
    )
    sampling_params = SamplingParams(temperature=temperature, max_tokens=max_new_tokens, stop=stop_sequences)
    gen_results = llm.generate(inputs, sampling_params)
    return [[output.outputs[0].text] for output in gen_results]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", default="LLM4Binary/sk2decompile-struct-6.7b")
    parser.add_argument("--recover_model_path", default="LLM4Binary/sk2decompile-ident-6.7")
    parser.add_argument("--dataset_path", default="reverse_sample.json")
    parser.add_argument("--decompiler", default="ida_pseudo_norm")
    parser.add_argument("--gpus", type=int, default=1)
    parser.add_argument("--gpu_memory_utilization", type=float, default=0.8)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--max_total_tokens", type=int, default=32768)
    parser.add_argument("--max_new_tokens", type=int, default=4096)
    parser.add_argument("--stop_sequences", type=str, default=None)
    parser.add_argument("--output_path", default="./result/sk2decompile")
    parser.add_argument("--strip", type=int, default=1)
    parser.add_argument("--language", default="c")
    args = parser.parse_args()

    samples = _load_samples(args.dataset_path)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    if args.stop_sequences is None:
        args.stop_sequences = [tokenizer.eos_token]

    before = "# This is the assembly code:\n"
    after = "\n# What is the source code?\n"

    inputs = []
    for sample in samples:
        prompt = before + sample[args.decompiler].strip() + after
        sample["prompt_model1"] = prompt
        inputs.append(prompt)

    print("Starting first model inference...")
    gen_results = _llm_inference(
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
    for idx in range(len(gen_results)):
        samples[idx]["gen_result_model1"] = gen_results[idx]

    inputs_recovery = []
    before_recovery = "# This is the normalized code:\n"
    after_recovery = "\n# What is the source code?\n"
    for idx, sample in enumerate(gen_results):
        prompt_recovery = before_recovery + sample.strip() + after_recovery
        samples[idx]["prompt_model2"] = prompt_recovery
        inputs_recovery.append(prompt_recovery)

    print("Starting recovery model inference...")
    gen_results_recovery = _llm_inference(
        inputs_recovery,
        args.recover_model_path,
        args.gpus,
        args.max_total_tokens,
        args.gpu_memory_utilization,
        args.temperature,
        args.max_new_tokens,
        args.stop_sequences,
    )
    gen_results_recovery = [gen_result[0] for gen_result in gen_results_recovery]
    for idx in range(len(gen_results_recovery)):
        samples[idx]["gen_result_model2"] = gen_results_recovery[idx]

    if args.output_path:
        if os.path.exists(args.output_path):
            shutil.rmtree(args.output_path)
        for opt in ["O0", "O1", "O2", "O3"]:
            os.makedirs(os.path.join(args.output_path, opt), exist_ok=True)

    if args.strip:
        print("Processing function name stripping...")
        for idx in range(len(gen_results_recovery)):
            one = gen_results_recovery[idx]
            func_name_in_gen = one.split("(")[0].split(" ")[-1].strip()
            if func_name_in_gen.strip() and func_name_in_gen.startswith("**"):
                func_name_in_gen = func_name_in_gen[2:]
            elif func_name_in_gen.strip() and func_name_in_gen.startswith("*"):
                func_name_in_gen = func_name_in_gen[1:]
            original_func_name = samples[idx]["func_name"]
            gen_results_recovery[idx] = one.replace(func_name_in_gen, original_func_name)
            samples[idx]["gen_result_model2_stripped"] = gen_results_recovery[idx]

    print("Saving inference results and logs...")
    for idx_sample, final_result in enumerate(gen_results_recovery):
        opt = samples[idx_sample]["opt"]
        language = samples[idx_sample].get("language", args.language)
        original_index = samples[idx_sample]["index"]
        save_path = os.path.join(args.output_path, opt, f"{original_index}_{opt}.{language}")
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(final_result)

        log_path = save_path + ".log"
        log_data = {
            "index": original_index,
            "opt": opt,
            "language": language,
            "func_name": samples[idx_sample]["func_name"],
            "decompiler": args.decompiler,
            "input_asm": samples[idx_sample][args.decompiler].strip(),
            "prompt_model1": samples[idx_sample]["prompt_model1"],
            "gen_result_model1": samples[idx_sample]["gen_result_model1"],
            "prompt_model2": samples[idx_sample]["prompt_model2"],
            "gen_result_model2": samples[idx_sample]["gen_result_model2"],
            "final_result": final_result,
            "stripped": args.strip,
        }
        if args.strip and "gen_result_model2_stripped" in samples[idx_sample]:
            log_data["gen_result_model2_stripped"] = samples[idx_sample]["gen_result_model2_stripped"]
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

    json_path = os.path.join(args.output_path, "inference_results.jsonl")
    with open(json_path, "w", encoding="utf-8") as f:
        for sample in samples:
            f.write(json.dumps(sample) + "\n")

    stats_path = os.path.join(args.output_path, "inference_stats.txt")
    with open(stats_path, "w", encoding="utf-8") as f:
        f.write(f"Total samples processed: {len(samples)}\n")
        f.write(f"Model path: {args.model_path}\n")
        f.write(f"Recovery model path: {args.recover_model_path}\n")
        f.write(f"Dataset path: {args.dataset_path}\n")
        f.write(f"Language: {args.language}\n")
        f.write(f"Decompiler: {args.decompiler}\n")
        f.write(f"Strip function names: {bool(args.strip)}\n")

    print(f"Inference completed! Results saved to {args.output_path}")


if __name__ == "__main__":
    main()
