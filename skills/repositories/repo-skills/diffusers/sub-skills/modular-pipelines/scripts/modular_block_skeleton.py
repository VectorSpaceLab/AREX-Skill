#!/usr/bin/env python3
"""Create a minimal Diffusers ModularPipelineBlocks custom block skeleton."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CLASS_NAME_RE = re.compile(r"^[A-Z][A-Za-z0-9]*Block$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_class_name(class_name: str) -> None:
    if not CLASS_NAME_RE.match(class_name):
        raise argparse.ArgumentTypeError(
            "class name must be PascalCase, contain only letters/numbers, and end with 'Block'"
        )


def validate_state_name(name: str) -> None:
    if not IDENTIFIER_RE.match(name):
        raise argparse.ArgumentTypeError(f"state name {name!r} is not a valid Python identifier")


def render_block(class_name: str, input_name: str, output_name: str, description: str) -> str:
    return f'''from diffusers.modular_pipelines import InputParam, ModularPipelineBlocks, OutputParam


class {class_name}(ModularPipelineBlocks):
    @property
    def description(self):
        return {description!r}

    @property
    def inputs(self):
        return [
            InputParam({input_name!r}, required=True, description="Input value consumed by this block."),
        ]

    @property
    def intermediate_outputs(self):
        return [
            OutputParam({output_name!r}, description="Output value produced by this block."),
        ]

    def __call__(self, components, state):
        block_state = self.get_block_state(state)
        block_state.{output_name} = block_state.{input_name}
        self.set_block_state(state, block_state)
        return components, state
'''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Print or write a minimal custom block skeleton for Diffusers Modular Pipelines."
    )
    parser.add_argument("--class-name", required=True, help="PascalCase class name ending in 'Block'.")
    parser.add_argument("--input-name", default="input_value", help="Input state key to declare and read.")
    parser.add_argument("--output-name", default="output_value", help="Output state key to declare and write.")
    parser.add_argument(
        "--description",
        default="Minimal custom modular pipeline block.",
        help="Description returned by the block's description property.",
    )
    parser.add_argument("--output", type=Path, help="Optional file to write, for example block.py. Prints to stdout if omitted.")
    parser.add_argument("--force", action="store_true", help="Overwrite --output if it already exists.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    for value, validator in (
        (args.class_name, validate_class_name),
        (args.input_name, validate_state_name),
        (args.output_name, validate_state_name),
    ):
        try:
            validator(value)
        except argparse.ArgumentTypeError as error:
            parser.error(str(error))

    source = render_block(args.class_name, args.input_name, args.output_name, args.description)

    if args.output is None:
        sys.stdout.write(source)
        return 0

    if args.output.exists() and not args.force:
        parser.error(f"{args.output} already exists; pass --force to overwrite")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(source, encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
