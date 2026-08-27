#!/usr/bin/env python3
"""Compile or validate a tiny SketchCode GUI DSL string.

The default path is self-contained and does not require TensorFlow, Keras,
pretrained weights, or a SketchCode checkout. If --repo-root is supplied, the
script can optionally import SketchCode's original Compiler for comparison.
"""

import argparse
import html
import os
import sys

SUPPORTED_STYLES = ("default", "facebook", "airbnb")
DEFAULT_TOKENS = (
    "<START> header { btn-active , btn-inactive } "
    "row { single { big-title , text , btn-orange } } <END>"
)

STYLE_CSS = {
    "default": "body{background:#fff}.nav{background:#333}.panel{background:#f5f5f5}",
    "facebook": "body{background:#E8E9EE}.nav{background:#395592}.panel{background:#fff}",
    "airbnb": "body{background:#EEEEEE}.nav{background:#039D8E}.panel{background:#fff}",
}

BASE_MAPPING = {
    "opening-tag": "{",
    "closing-tag": "}",
    "header": "<div class=\"header\"><ul class=\"nav\">{}</ul></div>\n",
    "btn-active": "<li class=\"active\"><a href=\"#\">[]</a></li>\n",
    "btn-inactive": "<li><a href=\"#\">[]</a></li>\n",
    "row": "<div class=\"row\">{}</div>\n",
    "single": "<div class=\"col-lg-12 panel\">{}</div>\n",
    "double": "<div class=\"col-lg-6 panel\">{}</div>\n",
    "quadruple": "<div class=\"col-lg-3 panel\">{}</div>\n",
    "btn-green": "<a class=\"btn btn-success\" href=\"#\" role=\"button\">[]</a>\n",
    "btn-orange": "<a class=\"btn btn-warning\" href=\"#\" role=\"button\">[]</a>\n",
    "btn-red": "<a class=\"btn btn-danger\" href=\"#\" role=\"button\">[]</a>\n",
    "big-title": "<h2>[]</h2>\n",
    "small-title": "<h4>[]</h4>\n",
    "text": "<p>[]</p>\n",
}

PLACEHOLDER_TEXT = {
    "btn": "Button",
    "title": "Title",
    "text": "This is deterministic placeholder text for compiler checks.",
}


class CompileError(ValueError):
    """Raised for user-facing DSL validation failures."""


class TinyNode(object):
    def __init__(self, key):
        self.key = key
        self.children = []

    def render(self, mapping):
        if self.key not in mapping:
            raise CompileError("unknown token {!r}".format(self.key))

        rendered_children = "".join(child.render(mapping) for child in self.children)
        value = mapping[self.key]
        if self.children:
            value = value.replace("{}", rendered_children)
        return fill_placeholder(self.key, value)


def fill_placeholder(key, value):
    if "[]" not in value:
        return value
    if "btn" in key:
        replacement = PLACEHOLDER_TEXT["btn"]
    elif "title" in key:
        replacement = PLACEHOLDER_TEXT["title"]
    elif "text" in key:
        replacement = PLACEHOLDER_TEXT["text"]
    else:
        replacement = "Text"
    return value.replace("[]", html.escape(replacement))


def split_tokens(tokens):
    spaced = tokens.replace("{", " { ").replace("}", " } ").replace(",", " , ")
    parts = [part for part in spaced.split() if part]
    if parts and parts[0] == "<START>":
        parts = parts[1:]
    if parts and parts[-1] == "<END>":
        parts = parts[:-1]
    return parts


def parse_tiny_dsl(tokens):
    parts = split_tokens(tokens)
    root = TinyNode("body")
    stack = [root]
    index = 0

    while index < len(parts):
        token = parts[index]

        if token == ",":
            index += 1
            continue

        if token == "{":
            raise CompileError("opening brace without a preceding token")

        if token == "}":
            if len(stack) == 1:
                raise CompileError("extra closing brace")
            stack.pop()
            index += 1
            continue

        next_token = parts[index + 1] if index + 1 < len(parts) else None
        node = TinyNode(token)
        stack[-1].children.append(node)

        if next_token == "{":
            stack.append(node)
            index += 2
        else:
            index += 1

    if len(stack) != 1:
        unclosed = " -> ".join(node.key for node in stack[1:])
        raise CompileError("unbalanced braces; still inside {}".format(unclosed))

    return root


def fallback_mapping(style):
    mapping = dict(BASE_MAPPING)
    mapping["body"] = (
        "<html>\n"
        "  <head><meta charset=\"utf-8\"><style>{}</style></head>\n"
        "  <body data-style=\"{}\"><main class=\"container\">\n{{}}\n"
        "  </main></body>\n"
        "</html>\n"
    ).format(STYLE_CSS[style], style)
    return mapping


def compile_with_fallback(tokens, style):
    root = parse_tiny_dsl(tokens)
    return root.render(fallback_mapping(style))


def ensure_original_compiler_tokens(tokens):
    parts = tokens.split()
    if not parts or parts[0] != "<START>":
        parts = ["<START>"] + parts
    if parts[-1] != "<END>":
        parts = parts + ["<END>"]
    return parts


def compile_with_repo(tokens, style, repo_root):
    src_dir = os.path.join(os.path.abspath(repo_root), "src")
    if not os.path.isdir(src_dir):
        raise CompileError("--repo-root does not contain a src directory: {}".format(repo_root))
    sys.path.insert(0, src_dir)
    try:
        from classes.inference.Compiler import Compiler  # noqa: WPS433
    except Exception as exc:  # pragma: no cover - depends on optional checkout
        raise CompileError("could not import original Compiler: {}".format(exc))

    compiler = Compiler(style)
    result = compiler.compile(ensure_original_compiler_tokens(tokens))
    if result == "HTML Parsing Error":
        raise CompileError("original compiler returned HTML Parsing Error")
    return result


def build_parser():
    parser = argparse.ArgumentParser(
        description="Validate and compile a tiny SketchCode GUI DSL token string."
    )
    parser.add_argument(
        "--style",
        choices=SUPPORTED_STYLES,
        default="default",
        help="Style mapping to use. Supported values: default, facebook, airbnb.",
    )
    parser.add_argument(
        "--tokens",
        default=DEFAULT_TOKENS,
        help="GUI DSL tokens to compile. Sentinels <START>/<END> are optional for fallback mode.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Optional SketchCode project root. When supplied, use the original Compiler instead of the fallback.",
    )
    parser.add_argument(
        "--output-html",
        default=None,
        help="Optional path to write the compiled HTML. HTML is always printed unless --quiet is used.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print compiled HTML to stdout; useful with --output-html.",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.repo_root:
            compiled = compile_with_repo(args.tokens, args.style, args.repo_root)
        else:
            compiled = compile_with_fallback(args.tokens, args.style)
    except CompileError as exc:
        print("HTML Parsing Error: {}".format(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # Keep diagnostics friendly for optional repo mode.
        print("HTML Parsing Error: unexpected compiler failure: {}".format(exc), file=sys.stderr)
        return 2

    if args.output_html:
        output_dir = os.path.dirname(os.path.abspath(args.output_html))
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(args.output_html, "w", encoding="utf-8") as handle:
            handle.write(compiled)

    if not args.quiet:
        print(compiled)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
