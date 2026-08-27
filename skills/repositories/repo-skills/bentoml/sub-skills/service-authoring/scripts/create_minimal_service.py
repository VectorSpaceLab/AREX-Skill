#!/usr/bin/env python3
"""Generate a safe BentoML service.py starter for the current SDK."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


_CLASS_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _service_name(value: str) -> str:
    if not value:
        raise argparse.ArgumentTypeError("service name must not be empty")
    return value


def _class_name(value: str) -> str:
    if not _CLASS_RE.match(value):
        raise argparse.ArgumentTypeError(
            "class name must be a valid Python identifier, for example TextTools"
        )
    return value


def _path_prefix(value: str) -> str:
    if not value.startswith("/"):
        raise argparse.ArgumentTypeError("path prefix must start with '/'")
    return value.rstrip("/") or "/"


def render_service(class_name: str, service_name: str | None, path_prefix: str | None) -> str:
    decorator_args: list[str] = []
    if service_name:
        decorator_args.append(f"name={service_name!r}")
    if path_prefix:
        decorator_args.append(f"path_prefix={path_prefix!r}")
    decorator = "@bentoml.service"
    if decorator_args:
        decorator = "@bentoml.service(\n    " + ",\n    ".join(decorator_args) + ",\n)"

    return f'''from __future__ import annotations

from typing import Generator

import bentoml
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    text: str = Field(description="Input text to process")
    repeat: int = Field(default=1, ge=1, le=5)


{decorator}
class {class_name}:
    def __init__(self) -> None:
        self.prefix = "BentoML"

    @bentoml.api(route="/echo", name="echo")
    def echo(self, text: str = "hello") -> str:
        return f"{{self.prefix}}: {{text}}"

    @bentoml.api(batchable=True, max_batch_size=8, max_latency_ms=1000)
    def batch_echo(self, texts: list[str]) -> list[str]:
        return [self.echo(text) for text in texts]

    @bentoml.api(input_spec=GenerateRequest)
    def generate(self, **params: object) -> str:
        text = str(params["text"])
        repeat = int(params["repeat"])
        return " ".join([text] * repeat)

    @bentoml.task(name="background_echo")
    def background_echo(self, text: str) -> str:
        return self.echo(text)

    @bentoml.api
    def stream_words(self, text: str = "hello bentoml") -> Generator[str, None, None]:
        for word in text.split():
            yield word
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("service.py"),
        help="Path to write, default: service.py",
    )
    parser.add_argument(
        "--class-name",
        type=_class_name,
        default="TextTools",
        help="Service class name, default: TextTools",
    )
    parser.add_argument(
        "--service-name",
        type=_service_name,
        default=None,
        help="Optional public BentoML service name",
    )
    parser.add_argument(
        "--path-prefix",
        type=_path_prefix,
        default=None,
        help="Optional URL path prefix, for example /v1",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output if it already exists",
    )
    args = parser.parse_args()

    output = args.output
    if output.exists() and not args.force:
        parser.error(f"{output} already exists; pass --force to overwrite")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_service(args.class_name, args.service_name, args.path_prefix),
        encoding="utf-8",
    )
    print(f"Wrote {output}")
    print(f"Validate with: python validate_service_target.py --target {output.stem}:{args.class_name} --working-dir {output.parent or Path('.')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
