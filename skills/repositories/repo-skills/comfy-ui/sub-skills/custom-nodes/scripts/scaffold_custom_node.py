#!/usr/bin/env python3
"""Scaffold a safe classic ComfyUI custom-node package."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
NODE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def snake_case(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    value = re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
    return value or "custom_node"


def title_from_id(node_id: str) -> str:
    spaced = re.sub(r"(?<!^)(?=[A-Z])", " ", node_id).replace("_", " ")
    return " ".join(part.capitalize() for part in spaced.split())


def validate_node_id(value: str) -> str:
    if not NODE_ID_RE.match(value):
        raise argparse.ArgumentTypeError("node id must start with a letter and contain only letters, digits, and underscores")
    return value


def package_name(value: str) -> str:
    if not IDENT_RE.match(value):
        raise argparse.ArgumentTypeError("package name must be a valid Python identifier")
    return value


def render_nodes_py(node_id: str, display_name: str, category: str, include_hidden: bool, include_validate: bool) -> str:
    hidden_block = ""
    signature_hidden = ""
    hidden_note = ""
    if include_hidden:
        hidden_block = '''\n            "hidden": {\n                "prompt": "PROMPT",\n                "unique_id": "UNIQUE_ID",\n            },'''
        signature_hidden = ", prompt=None, unique_id=None"
        hidden_note = '''\n        _ = prompt\n        _ = unique_id'''

    validate_block = ""
    if include_validate:
        validate_block = '''\n\n    @classmethod\n    def VALIDATE_INPUTS(cls, strength):\n        if strength < 0.0 or strength > 1.0:\n            return "strength must be between 0.0 and 1.0"\n        return True'''

    return f'''class {node_id}:\n    """Pass an image through with an optional strength widget."""\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {{\n            "required": {{\n                "image": ("IMAGE",),\n            }},\n            "optional": {{\n                "strength": ("FLOAT", {{"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}}),\n            }},{hidden_block}\n        }}\n\n    RETURN_TYPES = ("IMAGE",)\n    RETURN_NAMES = ("image",)\n    FUNCTION = "execute"\n    CATEGORY = "{category}"\n\n    def execute(self, image, strength=1.0{signature_hidden}):\n        _ = strength{hidden_note}\n        return (image,){validate_block}\n\n\nNODE_CLASS_MAPPINGS = {{\n    "{node_id}": {node_id},\n}}\n\nNODE_DISPLAY_NAME_MAPPINGS = {{\n    "{node_id}": "{display_name}",\n}}\n'''


def render_init_py() -> str:
    return '''from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS\n\n__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]\n'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a minimal classic ComfyUI custom-node package.")
    parser.add_argument("output_dir", type=Path, help="Directory to create or update with the scaffolded package")
    parser.add_argument("--package", type=package_name, default=None, help="Python package directory name; defaults to snake_case(node id)")
    parser.add_argument("--node-id", type=validate_node_id, default="ExampleImageNode", help="Stable NODE_CLASS_MAPPINGS key and class name")
    parser.add_argument("--display-name", default=None, help="Friendly UI display name")
    parser.add_argument("--category", default="custom/example", help="ComfyUI add-node category")
    parser.add_argument("--no-hidden", action="store_true", help="Do not include PROMPT/UNIQUE_ID hidden inputs")
    parser.add_argument("--no-validate", action="store_true", help="Do not include a simple VALIDATE_INPUTS example")
    parser.add_argument("--force", action="store_true", help="Overwrite existing __init__.py or nodes.py")
    args = parser.parse_args()

    package = args.package or snake_case(args.node_id)
    target = args.output_dir / package
    init_path = target / "__init__.py"
    nodes_path = target / "nodes.py"

    target.mkdir(parents=True, exist_ok=True)
    for path in (init_path, nodes_path):
        if path.exists() and not args.force:
            parser.error(f"{path} already exists; pass --force to overwrite")

    display_name = args.display_name or title_from_id(args.node_id)
    init_path.write_text(render_init_py(), encoding="utf-8")
    nodes_path.write_text(
        render_nodes_py(
            node_id=args.node_id,
            display_name=display_name,
            category=args.category,
            include_hidden=not args.no_hidden,
            include_validate=not args.no_validate,
        ),
        encoding="utf-8",
    )

    print(f"Created {target}")
    print(f"- {init_path.name}: exports NODE_CLASS_MAPPINGS and NODE_DISPLAY_NAME_MAPPINGS")
    print(f"- {nodes_path.name}: defines {args.node_id} with one IMAGE output")
    print("Next: copy the package under ComfyUI custom_nodes and restart ComfyUI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
