#!/usr/bin/env python3
"""Server-backed text-generation evaluation for LLM4Decompile."""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from text_generation import TextGenerationClient, TextGenerationServer
from transformers import AutoTokenizer
from tqdm import tqdm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--dtype", type=str, default="bfloat16")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--max_input_len", type=int, default=8192)
    parser.add_argument("--max_total_tokens", type=int, default=8800)
    parser.add_argument("--max_batch_prefill_tokens", type=int, default=72000)
    parser.add_argument("--num_shards", type=int, default=4)
    parser.add_argument("--max_new_tokens", type=int, default=512)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--testset_path", type=str, required=True)
    parser.add_argument("--num_workers", type=int, default=16)
    parser.add_argument("--output_path", type=str, default=None)
    parser.add_argument("--only_save", type=int, default=0)
    return parser.parse_args()


def evaluate_func(params):
    c_func, c_test, c_func_decompile = (
        params["c_func"],
        params["c_test"],
        params["c_func_decompile"],
    )

    timeout = 10
    flag_compile = 0
    flag_run = 0
    c_include = ""
    for line in c_func.split("\n"):
        if "#include" in line:
            c_include += line + "\n"
            c_func = c_func.replace(line, "")
    for line in c_test.split("\n"):
        if "#include" in line:
            c_include += line + "\n"
            c_test = c_test.replace(line, "")
    c_combine = c_include + "\n" + c_func_decompile + "\n" + c_test
    c_onlyfunc = c_include + "\n" + c_func_decompile

    with tempfile.TemporaryDirectory() as temp_dir:
        pid = os.getpid()
        c_file = os.path.join(temp_dir, f"combine_{pid}.c")
        executable = os.path.join(temp_dir, f"combine_{pid}")
        c_file_onlyfunc = os.path.join(temp_dir, f"onlyfunc_{pid}.c")
        executable_onlyfunc = os.path.join(temp_dir, f"onlyfunc_{pid}")

        with open(c_file, "w", encoding="utf-8") as f:
            f.write(c_combine)
        with open(c_file_onlyfunc, "w", encoding="utf-8") as f:
            f.write(c_onlyfunc)

        try:
            subprocess.run(["gcc", "-S", c_file_onlyfunc, "-o", executable_onlyfunc, "-lm"], check=True, timeout=timeout)
            flag_compile = 1
        except Exception:
            return flag_compile, flag_run

        try:
            subprocess.run(["gcc", c_file, "-o", executable, "-lm"], check=True, timeout=timeout)
            flag_compile = 1
        except Exception:
            return flag_compile, flag_run

        try:
            subprocess.run([executable], capture_output=True, text=True, timeout=timeout, check=True)
            flag_run = 1
        except Exception:
            return flag_compile, flag_run

    return flag_compile, flag_run


def run_eval_pipeline(args: argparse.Namespace) -> int:
    with open(args.testset_path, "r", encoding="utf-8") as f:
        testsets = json.load(f)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    stop_sequences = [tokenizer.eos_token]

    before = "# This is the assembly code:\n"
    after = "\n# What is the source code?\n"
    inputs = [before + sample["input_asm_prompt"].strip() + after for sample in testsets]

    server = TextGenerationServer(
        str(args.model_path),
        args.port,
        args.dtype,
        args.max_input_len,
        args.max_total_tokens,
        args.max_batch_prefill_tokens,
        args.num_shards,
    )
    client = TextGenerationClient(port=args.port, stop_sequences=stop_sequences)

    import asyncio

    loop = asyncio.get_event_loop()
    gen_results_repeat = []
    for _ in range(args.repeat):
        gen_results = loop.run_until_complete(
            client.generate_code_results(inputs, args.max_new_tokens, num_outputs=1)
        )
        gen_results_repeat.append(gen_results)

    del server
    if args.output_path:
        with open(args.output_path, "w", encoding="utf-8") as handle:
            json.dump([
                dict(sample, output=res[0]) for sample, res in zip(testsets, gen_results_repeat[0])
            ], handle, indent=4, ensure_ascii=True)

    if args.only_save:
        return 0

    tasks = [
        {
            "c_func": testset["c_func"],
            "c_test": testset["c_test"],
            "c_func_decompile": output[0],
        }
        for testset, output in zip(testsets, gen_results_repeat[0])
    ]

    with multiprocessing.Pool(args.num_workers) as pool:
        eval_results = list(tqdm(pool.imap(evaluate_func, tasks), total=len(tasks), desc="Evaluating"))

    compile_count = sum(flag[0] for flag in eval_results)
    run_count = sum(flag[1] for flag in eval_results)
    print(f"Compile rate: {compile_count / len(testsets):.4f}")
    print(f"Run rate: {run_count / len(testsets):.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_eval_pipeline(parse_args()))
