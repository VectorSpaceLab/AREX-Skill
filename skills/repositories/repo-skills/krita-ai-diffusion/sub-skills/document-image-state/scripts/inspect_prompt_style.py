#!/usr/bin/env python3
"""Offline prompt/style/LoRA inspector for Krita AI Diffusion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def find_repo_root(start: Path) -> Path | None:
    for path in [start, *start.parents]:
        if (path / "ai_diffusion" / "__init__.py").exists():
            return path
    return None


def add_local_repo_to_path() -> None:
    for candidate in [Path.cwd(), Path(__file__).resolve().parent]:
        root = find_repo_root(candidate)
        if root is not None:
            root_text = str(root)
            if root_text not in sys.path:
                sys.path.insert(0, root_text)
            return


def make_file_library(lora_ids: list[str]):
    from ai_diffusion.files import File, FileCollection, FileLibrary, FileSource

    loras = FileCollection()
    added = []
    for item in lora_ids:
        if ":" in item:
            name, strength_text = item.split(":", 1)
            strength = float(strength_text)
        else:
            name, strength = item, 1.0
        file = File.remote(name if name.endswith(".safetensors") else f"{name}.safetensors")
        added_file = loras.add(file)
        loras.set_meta(added_file, "lora_strength", strength)
        added.append({"id": added_file.id, "name": added_file.name, "default_strength": strength})
    loras.update([File.remote(entry["name"]) for entry in added], FileSource.remote)
    return FileLibrary(FileCollection(), loras), added


def inspect_prompt(args) -> dict[str, Any]:
    from ai_diffusion.backend.api import ConditioningInput
    from ai_diffusion.backend.workflow import prepare_prompts
    from ai_diffusion.backend.resources import Arch
    from ai_diffusion.image import Extent
    from ai_diffusion.style import Style
    from ai_diffusion.text import eval_wildcards, extract_loras, merge_prompt, replace_layers, strip_prompt_comments

    files, lora_files = make_file_library(args.lora_id)
    style = Style(Path("skill-style.json"))
    style.style_prompt = args.style_prompt
    style.negative_prompt = args.negative_prompt
    style.cfg_scale = args.cfg_scale
    style.live_cfg_scale = args.live_cfg_scale
    style.checkpoints = [args.checkpoint] if args.checkpoint else []
    for item in args.style_lora:
        name, _, strength_text = item.partition(":")
        style.loras.append({"name": name, "strength": float(strength_text or "1.0")})

    stripped = strip_prompt_comments(args.prompt)
    merged = merge_prompt(stripped, args.style_prompt, args.language)
    after_lora, loras = extract_loras(merged, files.loras)
    wildcard_eval = eval_wildcards(after_lora, args.seed)
    layer_mapping = {}
    for index, name in enumerate(args.layer, start=1):
        layer_mapping[name] = index
    layer_replaced = replace_layers(wildcard_eval, layer_mapping) if layer_mapping else wildcard_eval

    cond = ConditioningInput(args.prompt, args.negative_prompt, language=args.language)
    prepared = prepare_prompts(cond, style, seed=args.seed, arch=Arch[args.arch], files=files, is_live=args.live)

    result = {
        "runtime": "standalone-no-krita-no-server",
        "prompt": {
            "raw": args.prompt,
            "comment_stripped": stripped,
            "merged_with_style": merged,
            "after_lora_extraction": after_lora,
            "loras": [{"name": lora.name, "strength": lora.strength, "storage_id": lora.storage_id} for lora in loras],
            "wildcards_evaluated": wildcard_eval,
            "layers": layer_mapping,
            "after_layer_replacement": layer_replaced,
        },
        "prepare_prompts": {
            "positive": prepared.conditioning.positive if prepared.conditioning else None,
            "negative": prepared.conditioning.negative if prepared.conditioning else None,
            "loras": [{"name": lora.name, "strength": lora.strength, "storage_id": lora.storage_id} for lora in prepared.loras],
            "metadata": prepared.metadata,
        },
        "lora_files": lora_files,
        "assumptions": {
            "seed": args.seed,
            "arch": args.arch,
            "language": args.language,
            "live": args.live,
            "extent_for_metadata": "512x512",
        },
    }
    if args.metadata:
        from ai_diffusion.image import Bounds
        from ai_diffusion.model.jobs import JobParams
        from ai_diffusion.text import create_img_metadata

        metadata = dict(prepared.metadata)
        metadata.setdefault("checkpoint", args.checkpoint or "Unknown")
        metadata.setdefault("sampler", "")
        metadata.setdefault("steps", 0)
        metadata.setdefault("guidance", args.cfg_scale)
        params = JobParams(
            bounds=Bounds(0, 0, 512, 512),
            name="skill-preview",
            metadata=metadata,
            seed=args.seed,
        )
        try:
            result["metadata_preview"] = create_img_metadata(params)
        except Exception as exc:  # noqa: BLE001
            result["metadata_error"] = f"{type(exc).__name__}: {exc}"
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Offline prompt/style/LoRA inspector for Krita AI Diffusion.")
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--style-prompt", default="{prompt}")
    parser.add_argument("--negative-prompt", default="")
    parser.add_argument("--lora-id", action="append", default=[], help="Available LoRA id/name, optionally name:default_strength. Repeatable.")
    parser.add_argument("--style-lora", action="append", default=[], help="Style LoRA name:strength. Repeatable.")
    parser.add_argument("--layer", action="append", default=[], help="Layer names available for <layer:name> replacement. Repeatable.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--arch", default="sd15")
    parser.add_argument("--language", default="")
    parser.add_argument("--checkpoint", default="")
    parser.add_argument("--cfg-scale", type=float, default=7.0)
    parser.add_argument("--live-cfg-scale", type=float, default=1.0)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--metadata", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    add_local_repo_to_path()

    result = inspect_prompt(args)
    print(json.dumps(result, indent=None if args.json else 2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
