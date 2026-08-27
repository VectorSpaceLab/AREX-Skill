#!/usr/bin/env python3
"""Normalize pseudo-code into the skeleton form used by SK²Decompile."""

from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
from multiprocessing import Pool, cpu_count

from tqdm import tqdm


def good_func(func):
    func = "{".join(func.split("{")[1:])
    func_sp = func.split("\n")
    total = 0
    for line in func_sp:
        if len(line.strip()) >= 3:
            total += 1
    return 3 < total < 300


def strip_empty(code):
    return "\n".join(line for line in code.splitlines() if line.strip())


def format_with_clang(func: str, style: str = "Google") -> str:
    if not func:
        return None
    cmd = ["clang-format", f"--style={style}"]
    try:
        proc = subprocess.run(cmd, input=func, text=True, capture_output=True, check=True, timeout=0.5)
        return proc.stdout
    except Exception:
        return None


def hex_to_dec(text):
    pattern = re.compile(r"\b(0x[0-9a-fA-F]+)([uUlL]{1,3})?\b")

    def convert(match):
        hex_part = match.group(1)
        suffix = match.group(2) or ""
        return str(int(hex_part, 16)) + suffix

    return pattern.sub(convert, text)


def remove_keywords(text):
    patterns = [
        r"\b__fastcall\b",
        r"\b__cdecl\b",
        r"\b__ptr32\b",
        r"\b__noreturn\s+noreturn\b",
    ]
    combined_pattern = re.compile("|".join(patterns))
    return combined_pattern.sub("", text)


typedef_map = {
    "cpu_set_t": "int",
    "nl_item": "int",
    "__time_t": "int",
    "__mode_t": "unsigned short",
    "__off64_t": "long long",
    "__blksize_t": "long",
    "__ino_t": "unsigned long",
    "__blkcnt_t": "unsigned long long",
    "__syscall_slong_t": "long",
    "__ssize_t": "long int",
    "wchar_t": "unsigned short int",
    "wctype_t": "unsigned short int",
    "__int64": "long long",
    "__int32": "int",
    "__int16": "short",
    "__int8": "char",
    "_QWORD": "uint64_t",
    "_OWORD": "long double",
    "_DWORD": "uint32_t",
    "size_t": "unsigned int",
    "_BYTE": "uint8_t",
    "_TBYTE": "uint16_t",
    "_BOOL8": "uint8_t",
    "gcc_va_list": "va_list",
    "_WORD": "unsigned short",
    "_BOOL4": "int",
    "__va_list_tag": "va_list",
    "_IO_FILE": "FILE",
    "DIR": "int",
    "__fsword_t": "long",
    "__kernel_ulong_t": "int",
    "cc_t": "int",
    "speed_t": "int",
    "fd_set": "int",
    "__suseconds_t": "int",
    "_UNKNOWN": "void",
    "__sighandler_t": "void (*)(int)",
    "__compar_fn_t": "int (*)(const void *, const void *)",
}


def replace_typedefs(text):
    for alias, original in typedef_map.items():
        pattern = re.compile(rf"\b{re.escape(alias)}\b")
        text = pattern.sub(original, text)
    return text


def remove_comments(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    return text


def process_code(code_str):
    code_str = remove_comments(code_str)
    code_str = hex_to_dec(code_str)
    code_str = remove_keywords(code_str)
    code_str = replace_typedefs(code_str)
    return code_str


def process_entry(entry, key_name="pseudo"):
    result = process_code(entry.get(key_name, ""))
    if not result.strip():
        return ""
    formatted = format_with_clang(result)
    if formatted is None:
        return None
    return strip_empty(formatted)


def normalize_code_list_parallel(input_json, output_json, key_name="pseudo", num_workers=None, remove=1):
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("输入 JSON 应为对象数组")

    num_workers = num_workers or cpu_count()
    print(f"[+] 开始处理 {len(data)} 条记录，使用 {num_workers} 个进程")

    from functools import partial

    process_entry_key = partial(process_entry, key_name=key_name)
    with Pool(processes=num_workers) as pool:
        result = list(tqdm(pool.imap(process_entry_key, data), total=len(data), desc="Processing"))

    data_good = []
    for record, norm in zip(data, result):
        if norm:
            if not good_func(norm):
                continue
            record[f"{key_name}_norm"] = norm
            data_good.append(record)
        elif norm is None and not remove:
            record[f"{key_name}_norm"] = record[f"{key_name}"]
            data_good.append(record)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data_good, f, indent=2, ensure_ascii=False)

    print(f"[✓] 完成处理：{input_json}:{len(data)} → {output_json}:{len(data_good)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="并行处理伪代码字符串列表")
    parser.add_argument("--input_json", required=True)
    parser.add_argument("--output_json", required=True)
    parser.add_argument("--key_name", default="pseudo")
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--remove", type=int, default=1)
    args = parser.parse_args()
    normalize_code_list_parallel(args.input_json, args.output_json, args.key_name, args.workers, args.remove)
