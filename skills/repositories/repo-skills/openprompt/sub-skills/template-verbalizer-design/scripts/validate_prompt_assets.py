#!/usr/bin/env python3
"""Static validator for bundled OpenPrompt prompt assets.

The script intentionally uses only the Python standard library for its default
checks so it can run from the generated skill without the original OpenPrompt
checkout. Optional tokenizer checks can be enabled with --tokenizer when a
local Hugging Face tokenizer cache is available.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

ALLOWED_TEMPLATE_KEYS = {
    "placeholder",
    "meta",
    "mask",
    "soft",
    "soft_id",
    "duplicate",
    "same",
    "special",
    "text",
    "shortenable",
    "post_processing",
    "add_prefix_space",
}
PRIMARY_TEMPLATE_KEYS = {"placeholder", "meta", "mask", "soft", "special", "text"}
QUALIFIER_TEMPLATE_KEYS = {"soft_id", "duplicate", "same", "shortenable", "post_processing", "add_prefix_space"}
TEXT_EXTS = {".txt"}
JSON_EXTS = {".json", ".jsonl"}
ASSET_EXTS = TEXT_EXTS | JSON_EXTS


@dataclass
class Issue:
    severity: str
    path: Path
    line: Optional[int]
    message: str


class Reporter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.issues: List[Issue] = []
        self.files_seen = 0
        self.template_lines = 0
        self.verbalizer_files = 0
        self.json_files = 0

    def add(self, severity: str, path: Path, line: Optional[int], message: str) -> None:
        self.issues.append(Issue(severity=severity, path=path, line=line, message=message))

    def error(self, path: Path, line: Optional[int], message: str) -> None:
        self.add("ERROR", path, line, message)

    def warn(self, path: Path, line: Optional[int], message: str) -> None:
        self.add("WARN", path, line, message)

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    @property
    def error_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        return sum(1 for issue in self.issues if issue.severity == "WARN")

    def print(self) -> None:
        for issue in self.issues:
            location = self.rel(issue.path)
            if issue.line is not None:
                location = f"{location}:{issue.line}"
            print(f"{issue.severity}: {location}: {issue.message}")
        print(
            "Summary: "
            f"{self.files_seen} asset files, "
            f"{self.template_lines} template lines, "
            f"{self.verbalizer_files} verbalizer files, "
            f"{self.json_files} JSON/JSONL files, "
            f"{self.error_count} errors, {self.warning_count} warnings."
        )


def default_assets_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "prompt-assets" / "scripts"


def classify_asset(path: Path) -> str:
    name = path.name.lower()
    rel = "/".join(part.lower() for part in path.parts)
    if path.suffix.lower() in JSON_EXTS:
        if "verbalizer" in name:
            if "generation_verbalizer" in name:
                return "generation_verbalizer_json"
            if "ptr_verbalizer" in name:
                return "ptr_verbalizer_json"
            if "knowledgeable" in name or "knowledeable" in name:
                return "knowledgeable_verbalizer_json"
            return "verbalizer_json"
        return "json"
    if path.suffix.lower() in TEXT_EXTS:
        if "generation_verbalizer" in name:
            return "generation_verbalizer_txt"
        if "verbalizer" in name:
            if "knowledgeable" in name or "knowledeable" in name:
                return "knowledgeable_verbalizer_txt"
            return "verbalizer_txt"
        if "template" in name or name == "template.txt" or "template_for_auto_t" in name:
            return "template_txt"
        if rel.endswith("relationclassification/semeval/temp.txt"):
            return "relation_tsv"
        return "text"
    return "unknown"


def iter_asset_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.suffix.lower() in ASSET_EXTS:
            yield path


def is_int_constant(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, int) and not isinstance(node.value, bool)


def constant_string(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def constant_bool(node: ast.AST) -> Optional[bool]:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    return None


def find_template_chunks(text: str, path: Path, line_no: int, reporter: Reporter) -> List[str]:
    chunks: List[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "}":
            reporter.error(path, line_no, "unmatched '}' outside a template token")
            i += 1
            continue
        if ch != "{":
            i += 1
            continue
        start = i
        depth = 0
        quote: Optional[str] = None
        escaped = False
        while i < len(text):
            ch = text[i]
            if quote is not None:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = None
            else:
                if ch in {"'", '"'}:
                    quote = ch
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        chunks.append(text[start : i + 1])
                        break
            i += 1
        else:
            reporter.error(path, line_no, "template token starting here has no matching '}'")
            break
        i += 1
    return chunks


def extract_template_keys(expr: ast.AST, path: Path, line_no: int, chunk: str, reporter: Reporter) -> Tuple[set, dict]:
    keys = set()
    values = {}
    if isinstance(expr, ast.Set):
        for elt in expr.elts:
            key = constant_string(elt)
            if key is None:
                reporter.error(path, line_no, f"template set token must contain string keys only: {chunk}")
                continue
            keys.add(key)
            values[key] = None
        if len(keys) != 1 or not keys.issubset({"mask", "soft"}):
            reporter.error(path, line_no, f"set-style template token is only supported for {{'mask'}} or {{'soft'}}: {chunk}")
    elif isinstance(expr, ast.Dict):
        for key_node, value_node in zip(expr.keys, expr.values):
            key = constant_string(key_node) if key_node is not None else None
            if key is None:
                reporter.error(path, line_no, f"template dict keys must be string literals: {chunk}")
                continue
            keys.add(key)
            values[key] = value_node
    else:
        reporter.error(path, line_no, f"template token must be a Python dict or set literal: {chunk}")
    return keys, values


def validate_template_value_types(path: Path, line_no: int, chunk: str, values: dict, reporter: Reporter) -> None:
    for key, value in values.items():
        if key == "mask":
            if value is not None and not (isinstance(value, ast.Constant) and value.value is None):
                reporter.error(path, line_no, f"'mask' should be set-style {{'mask'}} or have value None: {chunk}")
        elif key in {"placeholder", "meta", "text", "special"}:
            if value is None or constant_string(value) is None:
                reporter.error(path, line_no, f"'{key}' value should be a string literal: {chunk}")
        elif key == "soft":
            if value is not None and not (
                (isinstance(value, ast.Constant) and (value.value is None or isinstance(value.value, str)))
            ):
                reporter.error(path, line_no, f"'soft' value should be None or a string literal: {chunk}")
        elif key == "soft_id":
            if not (is_int_constant(value) and value.value > 0):
                reporter.error(path, line_no, f"'soft_id' should be an integer greater than zero: {chunk}")
        elif key == "duplicate":
            if not (is_int_constant(value) and value.value > 0):
                reporter.error(path, line_no, f"'duplicate' should be a positive integer: {chunk}")
        elif key == "same":
            if constant_bool(value) is None:
                reporter.error(path, line_no, f"'same' should be boolean True/False: {chunk}")
        elif key == "shortenable":
            if constant_bool(value) is None:
                reporter.error(path, line_no, f"'shortenable' should be boolean True/False: {chunk}")
        elif key == "post_processing":
            if not isinstance(value, (ast.Lambda, ast.Constant, ast.Name)):
                reporter.warn(path, line_no, f"post_processing is syntactically valid but not a simple lambda/string/name: {chunk}")
        elif key == "add_prefix_space":
            if value is None or constant_string(value) is None:
                reporter.error(path, line_no, f"'add_prefix_space' value should be a string literal: {chunk}")


def validate_template_line(text: str, path: Path, line_no: int, reporter: Reporter, require_mask: bool = True) -> None:
    chunks = find_template_chunks(text, path, line_no, reporter)
    if not chunks:
        reporter.error(path, line_no, "template line has no OpenPrompt template tokens")
        return
    mask_count = 0
    for chunk in chunks:
        try:
            expr = ast.parse(chunk, mode="eval").body
        except SyntaxError as exc:
            reporter.error(path, line_no, f"template token has Python-literal syntax error: {chunk} ({exc.msg})")
            continue
        keys, values = extract_template_keys(expr, path, line_no, chunk, reporter)
        unknown = keys - ALLOWED_TEMPLATE_KEYS
        if unknown:
            reporter.error(path, line_no, f"unknown template key(s) {sorted(unknown)} in {chunk}")
        primary = keys & PRIMARY_TEMPLATE_KEYS
        if len(primary) > 1:
            reporter.error(path, line_no, f"template token has multiple primary roles {sorted(primary)}: {chunk}")
        if not primary and "soft_id" not in keys:
            reporter.error(path, line_no, f"template token lacks a primary role: {chunk}")
        if "duplicate" in keys and "soft" not in keys:
            reporter.error(path, line_no, f"'duplicate' is meaningful only on a soft-token template piece: {chunk}")
        if "same" in keys and "duplicate" not in keys:
            reporter.warn(path, line_no, f"'same' has no effect without 'duplicate': {chunk}")
        if "mask" in keys:
            mask_count += 1
        validate_template_value_types(path, line_no, chunk, values, reporter)
    if require_mask and mask_count == 0:
        reporter.error(path, line_no, "template line has no {'mask'} token; OpenPrompt Template._check_template_format will fail")
    rel = "/".join(part.lower() for part in path.parts)
    multi_mask_expected = any(marker in rel for marker in ("ptr_template", "template_for_auto_t", "/lmbff/"))
    if mask_count > 1 and not multi_mask_expected:
        reporter.warn(path, line_no, f"template has {mask_count} masks; use PTR/generation logic or confirm the verbalizer expects multiple masks")


def parse_json_or_jsonl(path: Path, reporter: Reporter) -> Optional[Any]:
    text = path.read_text(encoding="utf-8")
    if text.strip() == "":
        reporter.error(path, None, "empty JSON/JSONL asset")
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError as first_error:
        if path.suffix.lower() != ".jsonl":
            reporter.error(path, first_error.lineno, f"malformed JSON: {first_error.msg}")
            return None
        docs = []
        ok = True
        for line_no, line in enumerate(text.splitlines(), 1):
            if not line.strip():
                continue
            try:
                docs.append(json.loads(line))
            except json.JSONDecodeError as exc:
                reporter.error(path, line_no, f"malformed JSONL record: {exc.msg}")
                ok = False
        if not ok:
            return None
        if not docs:
            reporter.error(path, None, "JSONL asset has no records")
            return None
        return docs


def is_generation_rule_word(word: str) -> bool:
    stripped = word.strip()
    return stripped.startswith("{") and stripped.endswith("}")


def static_multi_token_issue(word: str) -> Optional[str]:
    stripped = word.strip()
    if stripped.startswith("<!>"):
        stripped = stripped[3:]
    if stripped == "":
        return "empty label word"
    if re.search(r"\s", stripped):
        return "contains whitespace and is likely a multi-token label word"
    return None


def tokenizer_multi_token_issue(word: str, tokenizer: Any, prefix: str) -> Optional[str]:
    stripped = word.strip()
    if stripped.startswith("<!>"):
        surface = stripped[3:]
    else:
        surface = prefix + stripped
    token_ids = tokenizer.encode(surface, add_special_tokens=False)
    if len(token_ids) > 1:
        try:
            tokens = tokenizer.convert_ids_to_tokens(token_ids)
        except Exception:
            tokens = token_ids
        return f"tokenizer splits label word into {len(token_ids)} tokens: {tokens}"
    return None


def collect_label_words_from_json(data: Any, container: list) -> None:
    if isinstance(data, dict):
        for value in data.values():
            collect_label_words_from_json(value, container)
    elif isinstance(data, list):
        for value in data:
            collect_label_words_from_json(value, container)
    elif isinstance(data, str):
        container.append(data)
    elif data is None:
        return
    else:
        # Non-string leaves are not label words, but preserve a type warning elsewhere.
        return


def validate_label_word(
    word: str,
    path: Path,
    line_no: Optional[int],
    reporter: Reporter,
    *,
    allow_generation_rule: bool,
    tokenizer: Any = None,
    tokenizer_prefix: str = " ",
) -> None:
    if allow_generation_rule and is_generation_rule_word(word):
        # Rule-style generation verbalizers intentionally use template fragments as target text.
        try:
            validate_template_line(word, path, line_no or 1, reporter, require_mask=False)
        except Exception as exc:  # defensive: template validation should report its own errors
            reporter.error(path, line_no, f"generation verbalizer rule could not be checked: {exc}")
        return
    issue = static_multi_token_issue(word)
    if issue is not None:
        reporter.error(path, line_no, f"label word {word!r} {issue}")
        return
    if tokenizer is not None:
        tok_issue = tokenizer_multi_token_issue(word, tokenizer, tokenizer_prefix)
        if tok_issue is not None:
            reporter.error(path, line_no, f"label word {word!r} {tok_issue}")


def validate_duplicate_label_words(groups: Sequence[Sequence[Sequence[str]]], path: Path, reporter: Reporter, *, strict: bool, knowledge_style: bool, ptr_style: bool) -> None:
    if knowledge_style or ptr_style:
        severity = "WARN" if strict else "WARN"
    else:
        severity = "ERROR" if strict else "WARN"
    for group_id, group in enumerate(groups):
        seen = {}
        duplicate_examples = []
        for class_id, words in enumerate(group):
            for word in words:
                key = word.strip().lower()
                if key.startswith("<!>"):
                    key = key[3:]
                if key in seen and seen[key] != class_id:
                    duplicate_examples.append((word, seen[key], class_id))
                else:
                    seen[key] = class_id
        if duplicate_examples:
            sample = "; ".join(f"{w!r} in classes {a} and {b}" for w, a, b in duplicate_examples[:5])
            more = "" if len(duplicate_examples) <= 5 else f" (+{len(duplicate_examples) - 5} more)"
            message = f"duplicate label words across classes in group {group_id}: {sample}{more}"
            if severity == "ERROR":
                reporter.error(path, None, message)
            else:
                reporter.warn(path, None, message)


def validate_txt_verbalizer(path: Path, reporter: Reporter, *, generation: bool, knowledge_style: bool, ptr_style: bool, tokenizer: Any, tokenizer_prefix: str, strict_duplicates: bool) -> None:
    text = path.read_text(encoding="utf-8")
    reporter.verbalizer_files += 1
    if text.strip() == "":
        reporter.error(path, None, "empty verbalizer file")
        return
    groups: List[List[List[str]]] = []
    group: List[List[str]] = []
    for line_no, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if line == "":
            if group:
                groups.append(group)
                group = []
            continue
        if generation:
            validate_label_word(line, path, line_no, reporter, allow_generation_rule=True, tokenizer=None, tokenizer_prefix=tokenizer_prefix)
            group.append([line])
        else:
            words = [piece.strip() for piece in line.split(",")]
            if any(word == "" for word in words):
                reporter.error(path, line_no, "verbalizer line has an empty comma-separated label word")
            words = [word for word in words if word]
            if not words:
                reporter.error(path, line_no, "verbalizer line has no label words")
                continue
            for word in words:
                validate_label_word(word, path, line_no, reporter, allow_generation_rule=False, tokenizer=tokenizer, tokenizer_prefix=tokenizer_prefix)
            group.append(words)
    if group:
        groups.append(group)
    if not groups:
        reporter.error(path, None, "verbalizer file has no non-empty groups")
        return
    class_counts = {len(group) for group in groups}
    if len(class_counts) > 1:
        reporter.warn(path, None, f"multiple verbalizer groups have different class counts: {sorted(class_counts)}")
    if not generation:
        validate_duplicate_label_words(groups, path, reporter, strict=strict_duplicates, knowledge_style=knowledge_style, ptr_style=ptr_style)


def normalize_json_verbalizer_groups(data: Any) -> List[List[List[str]]]:
    """Best-effort group/class/words shape for duplicate checks."""
    docs = data if isinstance(data, list) and all(isinstance(x, dict) for x in data) else [data]
    groups: List[List[List[str]]] = []
    for doc in docs:
        group: List[List[str]] = []
        if isinstance(doc, dict):
            for value in doc.values():
                if isinstance(value, list):
                    words = [str(v) for v in value if isinstance(v, str)]
                elif isinstance(value, str):
                    words = [value]
                else:
                    words = []
                group.append(words)
        elif isinstance(doc, list):
            for value in doc:
                if isinstance(value, list):
                    group.append([str(v) for v in value if isinstance(v, str)])
                elif isinstance(value, str):
                    group.append([value])
        if group:
            groups.append(group)
    return groups


def validate_json_verbalizer(path: Path, data: Any, reporter: Reporter, *, generation: bool, knowledge_style: bool, ptr_style: bool, tokenizer: Any, tokenizer_prefix: str, strict_duplicates: bool) -> None:
    reporter.verbalizer_files += 1
    if not isinstance(data, (dict, list)):
        reporter.error(path, None, "verbalizer JSON must be a dict, a list of class-word lists, or a list of dict verbalizers")
        return
    words: List[str] = []
    collect_label_words_from_json(data, words)
    if not words:
        reporter.error(path, None, "verbalizer JSON contains no string label words")
        return
    for word in words:
        validate_label_word(word, path, None, reporter, allow_generation_rule=generation, tokenizer=(None if generation else tokenizer), tokenizer_prefix=tokenizer_prefix)
    if not generation:
        groups = normalize_json_verbalizer_groups(data)
        validate_duplicate_label_words(groups, path, reporter, strict=strict_duplicates, knowledge_style=knowledge_style, ptr_style=ptr_style)


def validate_text_template_file(path: Path, reporter: Reporter) -> None:
    text = path.read_text(encoding="utf-8")
    nonempty = [(line_no, line.strip()) for line_no, line in enumerate(text.splitlines(), 1) if line.strip()]
    if not nonempty:
        reporter.error(path, None, "template file has no non-empty template lines")
        return
    for line_no, line in nonempty:
        reporter.template_lines += 1
        validate_template_line(line, path, line_no, reporter, require_mask=True)


def validate_generic_text(path: Path, reporter: Reporter) -> None:
    text = path.read_text(encoding="utf-8")
    if text.strip() == "":
        reporter.warn(path, None, "empty generic text asset")
    nul = "\x00" in text
    if nul:
        reporter.error(path, None, "text asset contains NUL bytes")


def build_tokenizer(name: Optional[str], local_files_only: bool) -> Any:
    if not name:
        return None
    try:
        from transformers import AutoTokenizer  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(f"--tokenizer requires transformers to be importable: {exc}") from exc
    try:
        return AutoTokenizer.from_pretrained(name, local_files_only=local_files_only)
    except Exception as exc:  # pragma: no cover - optional dependency path
        raise RuntimeError(f"failed to load tokenizer {name!r} (local_files_only={local_files_only}): {exc}") from exc


def validate_assets(args: argparse.Namespace) -> Reporter:
    root = args.assets_dir.resolve()
    reporter = Reporter(root)
    tokenizer = build_tokenizer(args.tokenizer, args.local_files_only) if args.tokenizer else None
    if not root.exists():
        reporter.error(root, None, "asset directory does not exist")
        return reporter
    for path in iter_asset_files(root):
        reporter.files_seen += 1
        try:
            kind = classify_asset(path)
            if kind == "template_txt":
                validate_text_template_file(path, reporter)
            elif kind in {"verbalizer_txt", "knowledgeable_verbalizer_txt", "generation_verbalizer_txt"}:
                validate_txt_verbalizer(
                    path,
                    reporter,
                    generation=(kind == "generation_verbalizer_txt"),
                    knowledge_style=(kind == "knowledgeable_verbalizer_txt"),
                    ptr_style=False,
                    tokenizer=tokenizer,
                    tokenizer_prefix=args.tokenizer_prefix,
                    strict_duplicates=args.strict_duplicates,
                )
            elif path.suffix.lower() in JSON_EXTS:
                reporter.json_files += 1
                data = parse_json_or_jsonl(path, reporter)
                if data is None:
                    continue
                if kind in {"verbalizer_json", "knowledgeable_verbalizer_json", "generation_verbalizer_json", "ptr_verbalizer_json"}:
                    validate_json_verbalizer(
                        path,
                        data,
                        reporter,
                        generation=(kind == "generation_verbalizer_json"),
                        knowledge_style=(kind == "knowledgeable_verbalizer_json"),
                        ptr_style=(kind == "ptr_verbalizer_json"),
                        tokenizer=tokenizer,
                        tokenizer_prefix=args.tokenizer_prefix,
                        strict_duplicates=args.strict_duplicates,
                    )
            else:
                validate_generic_text(path, reporter)
        except UnicodeDecodeError as exc:
            reporter.error(path, None, f"not valid UTF-8 text: {exc}")
        except Exception as exc:  # defensive: keep batch validation actionable
            reporter.error(path, None, f"validator internal error while checking this asset: {type(exc).__name__}: {exc}")
    if reporter.files_seen == 0:
        reporter.error(root, None, "no .txt/.json/.jsonl assets found")
    return reporter


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate bundled OpenPrompt template/verbalizer prompt assets.")
    parser.add_argument(
        "--assets-dir",
        type=Path,
        default=default_assets_dir(),
        help="Directory containing the bundled scripts-style prompt assets (default: references/prompt-assets/scripts).",
    )
    parser.add_argument(
        "--tokenizer",
        help="Optional Hugging Face tokenizer name/path for exact label-word tokenization checks; no model weights are loaded.",
    )
    parser.add_argument(
        "--tokenizer-prefix",
        default=" ",
        help="Prefix applied before tokenizer label-word checks to mirror OpenPrompt ManualVerbalizer prefix behavior (default: one space).",
    )
    parser.add_argument(
        "--allow-remote-tokenizer",
        action="store_true",
        help="Allow AutoTokenizer.from_pretrained to reach remote resources. Default is local-files-only to avoid downloads.",
    )
    parser.add_argument(
        "--strict-duplicates",
        action="store_true",
        help="Treat duplicate label words across classes as errors for ordinary manual verbalizers. Knowledgeable/PTR duplicates remain warnings because their implementations de-duplicate or combine per-mask logic.",
    )
    args = parser.parse_args(argv)
    args.local_files_only = not args.allow_remote_tokenizer
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        reporter = validate_assets(args)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    reporter.print()
    return 1 if reporter.error_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
