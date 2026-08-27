#!/usr/bin/env python3
"""Build source/pseudo/assembly function maps for BringUpBench-style data."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

FUNC_KEYWORDS = {"if", "for", "while", "switch", "return", "sizeof", "do", "case", "else"}

TYPEDEF_MAP = {
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


def _get_bench_root(cli_value: str | None = None) -> Path:
    if cli_value:
        return Path(cli_value).resolve()
    env_val = os.environ.get("BENCH_REPO_ROOT")
    if env_val:
        return Path(env_val).resolve()
    raise SystemExit("error: BENCH_REPO_ROOT not set. Use --bench-root or set the env var")


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_comments_and_strings(text: str) -> str:
    result = list(text)
    i = 0
    length = len(text)
    while i < length:
        nxt = text[i : i + 2]
        ch = text[i]
        if nxt == "//":
            end = text.find("\n", i)
            if end == -1:
                end = length
            for j in range(i, end):
                result[j] = " "
            i = end
            continue
        if nxt == "/*":
            end = text.find("*/", i + 2)
            if end == -1:
                end = length - 2
            for j in range(i, end + 2):
                result[j] = " "
            i = end + 2
            continue
        if ch in {'"', "'"}:
            quote = ch
            result[i] = " "
            i += 1
            while i < length:
                c = text[i]
                result[i] = " "
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    i += 1
                    break
                i += 1
            continue
        i += 1
    return "".join(result)


def _find_matching_brace(text: str, start_idx: int) -> int:
    depth = 0
    i = start_idx
    length = len(text)
    while i < length:
        nxt = text[i : i + 2]
        ch = text[i]
        if nxt == "//":
            i = text.find("\n", i)
            if i == -1:
                return length - 1
            continue
        if nxt == "/*":
            i = text.find("*/", i + 2)
            if i == -1:
                return length - 1
            i += 2
            continue
        if ch in {'"', "'"}:
            quote = ch
            i += 1
            while i < length:
                c = text[i]
                if c == "\\":
                    i += 2
                    continue
                if c == quote:
                    i += 1
                    break
                i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return length - 1


def _extract_source_functions(path: Path, repo_root: Path) -> Dict[str, Dict[str, str]]:
    text = _read_text(path)
    sanitized = _strip_comments_and_strings(text)
    pattern = re.compile(r"(?P<prefix>^|[;\n}])(?P<signature>[^{;}]*?)\b(?P<name>[A-Za-z_][\w]*)\s*\([^;{}]*\)\s*\{", re.MULTILINE)
    funcs: Dict[str, Dict[str, str]] = {}
    for match in pattern.finditer(sanitized):
        name = match.group("name")
        if name in FUNC_KEYWORDS:
            continue
        brace_idx = sanitized.find("{", match.start("signature"))
        if brace_idx == -1:
            continue
        end_idx = _find_matching_brace(text, brace_idx)
        if end_idx <= brace_idx:
            continue
        start_idx = match.start("signature")
        content = text[start_idx : end_idx + 1].strip("\n") + "\n"
        funcs.setdefault(name, {"path": str(path.relative_to(repo_root)), "function_name": name, "content": content})
    return funcs


def _normalize_pseudo(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\b(0x[0-9a-fA-F]+)([uUlL]{1,3})?\b", lambda m: str(int(m.group(1), 16)) + (m.group(2) or ""), text)
    text = re.sub(r"\b__fastcall\b|\b__cdecl\b|\b__ptr32\b|\b__noreturn\s+noreturn\b", "", text)
    for alias, original in TYPEDEF_MAP.items():
        text = re.sub(rf"\b{re.escape(alias)}\b", original, text)
    return text


def _parse_pseudo(pseudo_path: Path, repo_root: Path) -> Dict[str, Dict[str, str]]:
    text = _read_text(pseudo_path)
    lines = text.splitlines()
    pattern = re.compile(r"^/\*\s*(?P<name>[^@]+?)\s*@\s*(?P<addr>0x[0-9a-fA-F]+)\s*\*/$")
    current: Optional[str] = None
    current_addr: Optional[str] = None
    buffer: List[str] = []
    out: Dict[str, Dict[str, str]] = {}
    for raw_line in lines:
        line = raw_line.strip()
        match = pattern.match(line)
        if match:
            if current and buffer:
                content = "\n".join(buffer).strip("\n") + "\n"
                out.setdefault(current, {"path": str(pseudo_path.relative_to(repo_root)), "function_name": current, "address": current_addr, "label": current, "content": content})
            current = match.group("name").strip()
            current_addr = match.group("addr")
            buffer = []
        elif current is not None:
            buffer.append(raw_line)
    if current and buffer:
        content = "\n".join(buffer).strip("\n") + "\n"
        out.setdefault(current, {"path": str(pseudo_path.relative_to(repo_root)), "function_name": current, "address": current_addr, "label": current, "content": content})
    return out


def _clean_instruction(raw: str) -> Optional[str]:
    stripped = raw.strip()
    if not stripped:
        return None
    parts = raw.split("\t")
    relevant = parts[2:] if len(parts) >= 3 else parts[1:] if len(parts) == 2 else [stripped]
    instr = "\t".join(relevant)
    instr = instr.split("#")[0].strip()
    if not instr:
        return None
    if all(c in "0123456789abcdefABCDEF" for c in instr.replace(" ", "")):
        return None
    return instr


def _clean_asm_block(name: str, lines: List[str]) -> str:
    cleaned = [f"<{name}>"]
    cleaned[0] += ":"
    for raw in lines[1:]:
        instr = _clean_instruction(raw)
        if instr:
            cleaned.append(instr)
    return "\n".join(cleaned) + "\n"


def _parse_assembly(asm_path: Path) -> Dict[str, str]:
    lines = _read_text(asm_path).splitlines()
    header = re.compile(r"^\s*([0-9a-fA-F]+)\s+<([^>]+)>:\s*$")
    current: Optional[str] = None
    buffer: List[str] = []
    result: Dict[str, str] = {}
    for line in lines:
        match = header.match(line)
        if match:
            if current and buffer:
                result.setdefault(current, _clean_asm_block(current, buffer))
            current = match.group(2)
            buffer = [line]
        elif current is not None:
            buffer.append(line)
    if current and buffer:
        result.setdefault(current, _clean_asm_block(current, buffer))
    return result


def _discover_binaries(explicit: Optional[List[str]], repo_root: Path) -> List[Path]:
    if explicit:
        binaries = []
        for entry in explicit:
            candidate = Path(entry)
            if not candidate.is_absolute():
                candidate = repo_root / candidate
            if candidate.exists():
                binaries.append(candidate)
        return binaries
    matches = []
    for path in repo_root.rglob("*.O*"):
        suffix = path.suffix.lower()
        if suffix in {".o0", ".o1", ".o2", ".o3"}:
            matches.append(path)
    return sorted(matches)


def _collect_source_functions(bench_dir: Path, repo_root: Path) -> Dict[str, Dict[str, str]]:
    func_map: Dict[str, Dict[str, str]] = {}
    for src in sorted(list(bench_dir.rglob("*.c")) + list(bench_dir.rglob("*.cpp"))):
        func_map.update(_extract_source_functions(src, repo_root))
    return func_map


def _build_map(binary: Path, repo_root: Path) -> None:
    pseudo_path = Path(str(binary) + ".pseudo")
    asm_path = Path(str(binary) + ".s")
    if not pseudo_path.exists() or not asm_path.exists():
        print(f"[skip] Missing pseudo or assembly for {binary.relative_to(repo_root)}")
        return
    bench_dir = binary.parent
    source_funcs = _collect_source_functions(bench_dir, repo_root)
    pseudo_funcs = _parse_pseudo(pseudo_path, repo_root)
    asm_funcs = _parse_assembly(asm_path)
    common = sorted(set(source_funcs) & set(pseudo_funcs) & set(asm_funcs))
    if not common:
        print(f"[warn] No overlapping functions for {binary.relative_to(repo_root)}")
        return
    output_path = Path(str(binary) + ".func_map.jsonl")
    rel_binary = str(binary.relative_to(repo_root))
    with output_path.open("w", encoding="utf-8") as handle:
        for name in common:
            pseudo_entry = pseudo_funcs[name]
            pseudo_norm = _normalize_pseudo(pseudo_entry.get("content", ""))
            record = {
                "source": source_funcs[name],
                "pseudo": pseudo_entry,
                "pseudo_normalize": pseudo_norm,
                "binary": rel_binary,
                "assembly": asm_funcs[name],
            }
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
    print(f"[ok] {output_path.relative_to(repo_root)} -> {len(common)} functions")


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Map source/pseudo/assembly per function")
    parser.add_argument("--binary", action="append", help="Specific binary path (relative to repo) to process; can be repeated.")
    parser.add_argument("--bench-root", default=None, help="Path to the BringUpBench repository root or the repo root.")
    args = parser.parse_args(argv)
    repo_root = _get_bench_root(args.bench_root)
    binaries = _discover_binaries(args.binary, repo_root)
    if not binaries:
        print("No binaries found")
        return 1
    for binary in binaries:
        _build_map(binary, repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
