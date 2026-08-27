import argparse
import glob
import json
import multiprocessing
import os
import re
import subprocess

OPT = ["O0", "O1", "O2", "O3"]
ZEROS_PATTERN = r"^0+\s"


def write_to_file(file_path, data):
    with multiprocessing.Lock():
        with open(file_path, "a", encoding="utf-8") as handle:
            json.dump(data, handle)
            handle.write("\n")


def compile_and_write(input_file, output_file):
    base_output_file = input_file.replace(".c", "")
    asm_all = {}
    input_text = open(input_file, encoding="utf-8").read()
    if "/* Variables and functions */" in input_text:
        input_text = input_text.split("/* Variables and functions */")[-1]
        input_text = "\n\n".join(input_text.split("\n\n")[1:])
        input_text = input_text.replace("__attribute__((used)) ", "")

    try:
        for opt_state in OPT:
            obj_output = base_output_file + "_" + opt_state + ".o"
            asm_output = base_output_file + "_" + opt_state + ".s"

            subprocess.run(
                ["gcc", "-c", "-o", obj_output, input_file, "-" + opt_state],
                check=True,
            )

            subprocess.run(
                f"objdump -d {obj_output} > {asm_output}",
                shell=True,
                check=True,
            )

            with open(asm_output, encoding="utf-8") as handle:
                asm = handle.read()
                asm_clean = ""
                asm = asm.split("Disassembly of section .text:")[-1].strip()
                for tmp in asm.split("\n"):
                    tmp_asm = tmp.split("\t")[-1]
                    tmp_asm = tmp_asm.split("#")[0].strip()
                    asm_clean += tmp_asm + "\n"
                if len(asm_clean.split("\n")) < 4:
                    raise ValueError("compile fails")
                asm = asm_clean
                asm = re.sub(ZEROS_PATTERN, "", asm)
                asm = asm.replace("__attribute__((used)) ", "")
                asm_all["opt-state-" + opt_state] = asm

            if os.path.exists(obj_output):
                os.remove(obj_output)

    except Exception as exc:
        print(f"Error in file {input_file}: {exc}")
        return
    finally:
        for opt_state in OPT:
            asm_output = base_output_file + "_" + opt_state + ".s"
            if os.path.exists(asm_output):
                os.remove(asm_output)

    sample = {
        "name": input_file,
        "input": input_text,
        "input_ori": open(input_file, encoding="utf-8").read(),
        "output": asm_all,
    }
    write_to_file(output_file, sample)


def parse_args():
    parser = argparse.ArgumentParser(description="Compile C files and generate JSONL output.")
    parser.add_argument("--root", required=True, help="Root directory where C files are located.")
    parser.add_argument("--output", required=True, help="Path to JSONL output file.")
    return parser.parse_args()


def main():
    args = parse_args()
    files = glob.glob(f"{args.root}/**/*.c", recursive=True)
    with multiprocessing.Pool(32) as pool:
        from functools import partial

        compile_write_func = partial(compile_and_write, output_file=args.output)
        pool.map(compile_write_func, files)


if __name__ == "__main__":
    main()
