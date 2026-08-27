#!/usr/bin/env python3
"""Infer headers for normalized code samples using Psychec."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
from functools import partial

from tqdm import tqdm


def process_one(sample_src, generator, solver):
    with tempfile.TemporaryDirectory() as tmpdir:
        sample_path = os.path.join(tmpdir, "sample.c")
        output_path = os.path.join(tmpdir, "sample.cstr")
        header_path = os.path.join(tmpdir, "sample.h")

        with open(sample_path, "w", encoding="utf-8") as f:
            f.write(sample_src)

        try:
            subprocess.run(
                [generator, sample_path, "-o", output_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1,
            )
            subprocess.run(
                ["stack", "exec", solver, "--", "-i", output_path, "-o", header_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=1,
            )
            with open(header_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None


def jsonfile(input_json, output_json, generator, solver):
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    data_good = []
    worker = partial(process_one, generator=generator, solver=solver)
    for one in tqdm(data):
        code = one.get("func", one.get("code_format", one.get("code", "")))
        header = worker(code)
        if header:
            one["func_dep"] = header
            one["header"] = header
            data_good.append(one)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data_good, f, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(description="Batch-process C samples into headers.")
    parser.add_argument("--input_json", required=True)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--generator", default=os.getenv("PSYCHEC_GENERATOR", "./psychec/psychecgen"))
    parser.add_argument("--solver", default=os.getenv("PSYCHEC_SOLVER", "./psychec/psychecsolver-exe"))
    args = parser.parse_args()
    jsonfile(args.input_json, args.output_json, args.generator, args.solver)


if __name__ == "__main__":
    main()
