#!/usr/bin/env python3
"""Conservatively rename matching OpenQASM AST Identifier nodes."""

from __future__ import annotations

import argparse
import collections
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterator, Optional, Set, Tuple


IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
# This intentionally conservative set catches lexical keywords before printing.
RESERVED = {
    "OPENQASM",
    "include",
    "gate",
    "def",
    "extern",
    "qubit",
    "bit",
    "bool",
    "int",
    "uint",
    "float",
    "angle",
    "complex",
    "array",
    "duration",
    "stretch",
    "const",
    "input",
    "output",
    "let",
    "measure",
    "reset",
    "barrier",
    "delay",
    "box",
    "if",
    "else",
    "for",
    "while",
    "switch",
    "case",
    "default",
    "break",
    "continue",
    "return",
    "end",
    "inv",
    "pow",
    "ctrl",
    "negctrl",
    "gphase",
    "true",
    "false",
    "pragma",
    "cal",
    "defcal",
    "defcalgrammar",
    "readonly",
    "mutable",
    "nop",
}


class ToolError(RuntimeError):
    """A user-facing, non-traceback CLI error."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Rename matching AST Identifier nodes, print normalized OpenQASM 3, "
            "and reparse the result before reporting success."
        ),
        epilog=(
            "LIMITS: this is a global lexical AST rewrite, not binding-aware renaming. "
            "It rejects an already-present target name as a possible collision/capture, "
            "does not rewrite strings or raw calibration bodies, and normalized output "
            "omits comments. Reparse success is not semantic/compiler validation."
        ),
    )
    parser.add_argument("old", help="existing identifier name")
    parser.add_argument("new", help="replacement identifier name")
    parser.add_argument("path", nargs="?", help="input path; choose this, --source, or --stdin")
    source_group = parser.add_mutually_exclusive_group()
    source_group.add_argument("--source", help="parse this source string")
    source_group.add_argument("--stdin", action="store_true", help="read source from standard input")
    parser.add_argument("--output", type=Path, help="write validated output to this path")
    parser.add_argument(
        "--overwrite-input",
        action="store_true",
        help="explicitly allow --output to replace the input path",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacing an existing output path other than the input",
    )
    return parser


def load_parser_api():
    try:
        import openqasm3  # type: ignore
    except ImportError as exc:
        raise ToolError(
            "openqasm3 parser components could not be imported. Install "
            "the parser extra with: python -m pip install 'openqasm3[parser]'. "
            f"Original error: {exc}"
        ) from exc
    if not hasattr(openqasm3, "parse") or not hasattr(openqasm3, "dumps"):
        raise ToolError(
            "openqasm3 parsing is unavailable. Install the parser extra with: "
            "python -m pip install 'openqasm3[parser]'."
        )
    return openqasm3


def read_source(args: argparse.Namespace) -> Tuple[str, Optional[Path]]:
    choices = int(args.path is not None) + int(args.source is not None) + int(args.stdin)
    if choices != 1:
        raise ToolError("choose exactly one input: PATH, --source, or --stdin")
    if args.source is not None:
        return args.source, None
    if args.stdin:
        return sys.stdin.read(), None
    path = Path(args.path)
    try:
        return path.read_text(encoding="utf-8"), path
    except OSError as exc:
        raise ToolError(f"could not read input {path}: {exc}") from exc


def walk_nodes(value: Any, ast_module: Any, seen: Optional[Set[int]] = None) -> Iterator[Any]:
    if seen is None:
        seen = set()
    if isinstance(value, ast_module.QASMNode):
        marker = id(value)
        if marker in seen:
            return
        seen.add(marker)
        yield value
        for child in vars(value).values():
            yield from walk_nodes(child, ast_module, seen)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from walk_nodes(child, ast_module, seen)
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk_nodes(child, ast_module, seen)


def identifier_names(program: Any, ast_module: Any) -> list[str]:
    return [node.name for node in walk_nodes(program, ast_module) if isinstance(node, ast_module.Identifier)]


def validate_name(name: str, role: str) -> None:
    if not IDENTIFIER_RE.fullmatch(name):
        raise ToolError(
            f"{role} name {name!r} is rejected by the conservative ASCII identifier policy "
            "(expected [A-Za-z_][A-Za-z0-9_]*)"
        )
    if name in RESERVED:
        raise ToolError(
            f"{role} name {name!r} is reserved by this tool's conservative "
            "OpenQASM-name policy"
        )


def parse_or_fail(source: str, openqasm3: Any, label: str) -> Any:
    try:
        return openqasm3.parse(source)
    except Exception as exc:
        line = getattr(exc, "line", None)
        column = getattr(exc, "column", None)
        location = ""
        if line is not None and column is not None:
            location = f" at line {line}, column {column}"
        elif line is not None:
            location = f" at line {line}"
        raise ToolError(f"{label} failed{location}: {exc}") from exc


class RenameTransformer:
    """Defined after loading the package so the script fails clearly without the extra."""

    def __init__(self, old: str, new: str):
        from openqasm3.visitor import QASMTransformer

        class _Rename(QASMTransformer):
            def __init__(self) -> None:
                super().__init__()
                self.changed = 0

            def visit_Identifier(self, node: Any) -> Any:
                if node.name == old:
                    node.name = new
                    self.changed += 1
                return node

        self.instance = _Rename()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=str(path.parent),
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        if temporary is not None:
            try:
                temporary.unlink()
            except OSError:
                pass
        raise ToolError(f"could not write output {path}: {exc}") from exc


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        validate_name(args.old, "old")
        validate_name(args.new, "new")
        if args.old == args.new:
            raise ToolError("old and new names are identical; refusing a no-op rewrite")
        source, input_path = read_source(args)
        openqasm3 = load_parser_api()
        program = parse_or_fail(source, openqasm3, "input parse")
        before = identifier_names(program, openqasm3.ast)
        old_count = before.count(args.old)
        if old_count == 0:
            raise ToolError(f"no AST Identifier node named {args.old!r} was found")
        if args.new in before:
            raise ToolError(
                f"target name {args.new!r} already occurs in the AST; refusing a possible "
                "global collision or capture"
            )

        transformer = RenameTransformer(args.old, args.new)
        transformer.instance.visit(program)
        changed = transformer.instance.changed
        if changed != old_count:
            raise ToolError(
                f"transform changed {changed} of {old_count} matching Identifier nodes; "
                "at least one match is in a nested container shape that the base "
                "QASMTransformer does not traverse, so a partial rewrite was refused"
            )

        try:
            rendered = openqasm3.dumps(program)
        except Exception as exc:
            raise ToolError(f"printing transformed AST failed: {exc}") from exc
        reparsed = parse_or_fail(rendered, openqasm3, "reparse of transformed output")
        if reparsed != program:  # QASMNode dataclass equality deliberately ignores spans.
            raise ToolError(
                "reparsed output does not reproduce the transformed AST structure; "
                "refusing to emit it"
            )
        after = identifier_names(reparsed, openqasm3.ast)
        expected = collections.Counter(before)
        expected[args.old] -= old_count
        if expected[args.old] == 0:
            del expected[args.old]
        expected[args.new] += old_count
        if collections.Counter(after) != expected:
            raise ToolError(
                "reparsed output changed an unrelated AST identifier; refusing to emit it"
            )
        if args.old in after:
            raise ToolError(f"reparsed output still contains AST identifier {args.old!r}")

        output_path = args.output
        if output_path is not None:
            resolved_output = output_path.resolve()
            resolved_input = input_path.resolve() if input_path is not None else None
            same_input = resolved_input is not None and resolved_output == resolved_input
            if same_input and not args.overwrite_input:
                raise ToolError(
                    "output resolves to the input path; pass --overwrite-input explicitly "
                    "to permit replacement"
                )
            if output_path.exists() and not same_input and not args.force:
                raise ToolError(
                    f"output {output_path} already exists; pass --force to replace it"
                )
            atomic_write(output_path, rendered)
            print(f"wrote {changed} renamed AST identifier(s) to {output_path}", file=sys.stderr)
        else:
            sys.stdout.write(rendered)

        print(
            "warning: this is a lexical AST-identifier rename. It does not resolve "
            "scopes or bindings, normalized output omits comments, and it does not "
            "rewrite strings or raw calibration bodies; run semantic/compiler "
            "validation separately.",
            file=sys.stderr,
        )
        return 0
    except ToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
