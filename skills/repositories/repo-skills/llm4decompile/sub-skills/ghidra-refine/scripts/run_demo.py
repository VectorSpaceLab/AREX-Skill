#!/usr/bin/env python3
"""Compile a sample, dump pseudo-code, and refine it with a V2 checkpoint.

The repo's source examples name this workflow "ghidra", but the bundled
postscript uses decompiler-specific APIs. Treat the headless binary and the
postscript as a matched pair supplied by the user environment.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless_bin", default=os.getenv("HEADLESS_BIN", "analyzeHeadless"))
    parser.add_argument("--postscript", default=os.getenv("POSTSCRIPT_PATH", "dump_pseudo.py"))
    parser.add_argument("--model_path", default=os.getenv("MODEL_PATH", "LLM4Binary/llm4decompile-6.7b-v2"))
    parser.add_argument("--func_path", default=os.getenv("FUNC_PATH", "sample.c"))
    parser.add_argument("--func_name", default=os.getenv("FUNC_NAME", "func0"))
    parser.add_argument("--file_name", default=os.getenv("FILE_NAME", "sample"))
    parser.add_argument("--project_name", default=os.getenv("PROJECT_NAME", "tmp_refine_proj"))
    parser.add_argument("--temp_timeout", type=int, default=10)
    parser.add_argument("--max_new_tokens", type=int, default=2048)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    opt = "O0"

    with tempfile.TemporaryDirectory() as temp_dir:
        pid = os.getpid()
        executable_path = os.path.join(temp_dir, f"{pid}_{opt}.o")
        subprocess.run(
            ["gcc", f"-{opt}", "-o", executable_path, args.func_path, "-lm"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=args.temp_timeout,
        )

        output_path = os.path.join(temp_dir, f"{pid}_{opt}.c")
        command = [
            args.headless_bin,
            temp_dir,
            args.project_name,
            "-import",
            executable_path,
            "-postScript",
            args.postscript,
            output_path,
            "-deleteProject",
        ]
        subprocess.run(command, text=True, capture_output=True, check=True)

        with open(output_path, "r", encoding="utf-8") as f:
            c_decompile = f.read()

        c_func = []
        flag = 0
        for line in c_decompile.split("\n"):
            if f"Function: {args.func_name}" in line:
                flag = 1
                c_func.append(line)
                continue
            if flag:
                if "// Function:" in line and len(c_func) > 1:
                    break
                c_func.append(line)

        if flag == 0:
            raise ValueError("bad case no function found")

        for idx_tmp in range(1, len(c_func)):
            if args.func_name in c_func[idx_tmp]:
                break
        c_func = c_func[idx_tmp:]
        input_asm = "\n".join(c_func).strip()

        prompt = "# This is the assembly code:\n" + input_asm + "\n# What is the source code?\n"
        prompt_file = f"{args.file_name}_{opt}.pseudo"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt)

    tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.bfloat16).cuda()
    with open(prompt_file, "r", encoding="utf-8") as f:
        asm_func = f.read()
    inputs = tokenizer(asm_func, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=args.max_new_tokens)
    c_func_decompile = tokenizer.decode(outputs[0][len(inputs[0]) : -1])

    with open(prompt_file, "r", encoding="utf-8") as f:
        func = f.read()

    print(f"pseudo function:\n{func}")
    print(f"refined function:\n{c_func_decompile}")


if __name__ == "__main__":
    main()
