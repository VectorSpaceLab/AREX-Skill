#!/usr/bin/env python3
"""Build CLIP zero-shot classifier weights from class names and templates.

The importable `build_zeroshot_classifier` function expects a loaded CLIP model.
The CLI defaults to `--dry-run-tokenize`, which validates prompt expansion and
CLIP tokenization without loading or downloading model checkpoints.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, List, Optional, Sequence, Union

if TYPE_CHECKING:
    import torch

DEFAULT_CONTEXT_LENGTH = 77


def read_entries(path: Union[str, Path]) -> List[str]:
    """Read non-empty, non-comment lines from a UTF-8 text file."""
    entries: List[str] = []
    with Path(path).expanduser().open("r", encoding="utf-8") as handle:
        for line in handle:
            value = line.strip()
            if value and not value.startswith("#"):
                entries.append(value)
    return entries


def merge_entries(inline_values: Optional[Sequence[str]], files: Optional[Sequence[str]]) -> List[str]:
    """Merge repeated CLI values with one-entry-per-line files."""
    merged: List[str] = []
    if inline_values:
        merged.extend(inline_values)
    if files:
        for path in files:
            merged.extend(read_entries(path))
    return merged


def validate_templates(templates: Sequence[str], require_placeholder: bool = True) -> None:
    """Validate standard single-placeholder CLIP class templates."""
    if not templates:
        raise ValueError("At least one template is required")
    if require_placeholder:
        bad_templates = [template for template in templates if template.count("{}") != 1]
        if bad_templates:
            formatted = "; ".join(repr(template) for template in bad_templates)
            raise ValueError(f"Templates must contain exactly one {{}} placeholder: {formatted}")


def expand_prompts(class_names: Sequence[str], templates: Sequence[str]) -> List[List[str]]:
    """Return expanded prompts grouped by class name."""
    if not class_names:
        raise ValueError("At least one class name is required")
    validate_templates(templates)
    expanded: List[List[str]] = []
    for class_name in class_names:
        if not class_name.strip():
            raise ValueError("Class names must not be blank")
        try:
            expanded.append([template.format(class_name) for template in templates])
        except (IndexError, KeyError, ValueError) as exc:
            raise ValueError(f"Failed to format templates for class {class_name!r}: {exc}") from exc
    return expanded


def flatten(groups: Iterable[Iterable[str]]) -> List[str]:
    """Flatten grouped prompt strings."""
    return [prompt for group in groups for prompt in group]


def load_simple_tokenizer_class():
    """Load CLIP's SimpleTokenizer without importing clip.__init__ first."""
    sys.modules.pop("clip", None)
    package_spec = importlib.util.find_spec("clip")
    if package_spec is None or not package_spec.submodule_search_locations:
        raise ModuleNotFoundError("clip")

    package_dir = Path(next(iter(package_spec.submodule_search_locations)))
    tokenizer_path = package_dir / "simple_tokenizer.py"
    if not tokenizer_path.is_file():
        raise ModuleNotFoundError("clip.simple_tokenizer")

    tokenizer_spec = importlib.util.spec_from_file_location("_clip_simple_tokenizer_for_dry_run", tokenizer_path)
    if tokenizer_spec is None or tokenizer_spec.loader is None:
        raise ModuleNotFoundError("clip.simple_tokenizer")

    module = importlib.util.module_from_spec(tokenizer_spec)
    tokenizer_spec.loader.exec_module(module)
    return module.SimpleTokenizer


def dry_run_tokenize(
    class_names: Sequence[str],
    templates: Sequence[str],
    *,
    context_length: int = DEFAULT_CONTEXT_LENGTH,
    truncate: bool = False,
) -> dict:
    """Validate prompt expansion and CLIP-compatible tokenization without loading a model."""
    grouped_prompts = expand_prompts(class_names, templates)
    prompts = flatten(grouped_prompts)

    try:
        import clip
    except ModuleNotFoundError:
        clip = None

    if clip is not None:
        tokens = clip.tokenize(prompts, context_length=context_length, truncate=truncate)
        nonzero_counts = (tokens != 0).sum(dim=1).tolist()
        token_shape = list(tokens.shape)
        token_dtype = str(tokens.dtype)
        tokenizer_source = "clip.tokenize"
    else:
        tokenizer = load_simple_tokenizer_class()()
        sot_token = tokenizer.encoder["<|startoftext|>"]
        eot_token = tokenizer.encoder["<|endoftext|>"]
        encoded_prompts = [[sot_token] + tokenizer.encode(prompt) + [eot_token] for prompt in prompts]
        nonzero_counts = []
        for prompt, token_ids in zip(prompts, encoded_prompts):
            if len(token_ids) > context_length:
                if truncate:
                    token_ids = token_ids[:context_length]
                    token_ids[-1] = eot_token
                else:
                    raise RuntimeError(f"Input {prompt} is too long for context length {context_length}")
            nonzero_counts.append(len(token_ids))
        token_shape = [len(prompts), context_length]
        token_dtype = "integer ids; torch tensor dtype depends on installed torch version"
        tokenizer_source = "clip.simple_tokenizer fallback"

    return {
        "class_count": len(class_names),
        "template_count": len(templates),
        "prompt_count": len(prompts),
        "context_length": context_length,
        "truncate": truncate,
        "token_shape": token_shape,
        "token_dtype": token_dtype,
        "tokenizer_source": tokenizer_source,
        "max_nonzero_tokens": max(nonzero_counts) if nonzero_counts else 0,
        "sample_prompts": prompts[: min(5, len(prompts))],
    }


def build_zeroshot_classifier(
    model: "torch.nn.Module",
    class_names: Sequence[str],
    templates: Sequence[str],
    *,
    device: Optional[Union[str, "torch.device"]] = None,
    context_length: int = DEFAULT_CONTEXT_LENGTH,
    truncate: bool = False,
) -> "torch.Tensor":
    """Build normalized CLIP zero-shot classifier weights.

    Parameters
    ----------
    model:
        A loaded CLIP model with an `encode_text` method.
    class_names:
        Ordered class labels. Output columns follow this order.
    templates:
        Prompt templates containing exactly one `{}` placeholder.
    device:
        Device for token tensors. If omitted, inferred from model parameters.
    context_length:
        Token context length. Released CLIP models use 77.
    truncate:
        Whether `clip.tokenize` may truncate overlong prompts.

    Returns
    -------
    torch.Tensor
        Tensor shaped `[text_feature_dim, num_classes]` with normalized columns.
    """
    import clip
    import torch

    if device is None:
        try:
            device = next(model.parameters()).device
        except StopIteration:
            device = torch.device("cpu")
    else:
        device = torch.device(device)

    grouped_prompts = expand_prompts(class_names, templates)
    zeroshot_weights: List[torch.Tensor] = []

    was_training = model.training
    model.eval()
    with torch.no_grad():
        for prompts in grouped_prompts:
            text_tokens = clip.tokenize(prompts, context_length=context_length, truncate=truncate).to(device)
            class_embeddings = model.encode_text(text_tokens).float()
            class_embeddings = class_embeddings / class_embeddings.norm(dim=-1, keepdim=True)
            class_embedding = class_embeddings.mean(dim=0)
            class_embedding = class_embedding / class_embedding.norm()
            zeroshot_weights.append(class_embedding)

    if was_training:
        model.train()

    return torch.stack(zeroshot_weights, dim=1).to(device)


def default_device() -> str:
    try:
        import torch
    except ModuleNotFoundError:
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate CLIP prompts or build normalized zero-shot classifier weights.",
    )
    parser.add_argument("--class-name", action="append", default=[], help="Class label; repeat for multiple labels.")
    parser.add_argument("--class-file", action="append", default=[], help="Text file with one class label per line.")
    parser.add_argument("--template", action="append", default=[], help="Prompt template with one {} placeholder; repeat for multiple templates.")
    parser.add_argument("--template-file", action="append", default=[], help="Text file with one template per line.")
    parser.add_argument("--context-length", type=int, default=DEFAULT_CONTEXT_LENGTH, help="CLIP text context length; default: 77.")
    parser.add_argument("--truncate", action="store_true", help="Allow clip.tokenize to truncate overlong prompts deliberately.")
    parser.add_argument("--dry-run-tokenize", action="store_true", help="Only expand and tokenize prompts; do not load a model.")
    parser.add_argument("--load-model", help="Model name or local checkpoint path for clip.load. May download if a named checkpoint is not cached.")
    parser.add_argument("--download-root", help="Optional cache directory passed to clip.load when --load-model is used.")
    parser.add_argument("--device", default=default_device(), help="Torch device for optional model loading.")
    parser.add_argument("--output", help="Optional .pt file path for classifier weights built with --load-model.")
    parser.add_argument("--metadata-output", help="Optional JSON metadata path for class/template order and output details.")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    class_names = merge_entries(args.class_name, args.class_file)
    templates = merge_entries(args.template, args.template_file)

    if not class_names:
        parser.error("Provide at least one --class-name or --class-file")
    if not templates:
        parser.error("Provide at least one --template or --template-file")

    dry_run = args.dry_run_tokenize or not args.load_model

    try:
        summary = dry_run_tokenize(
            class_names,
            templates,
            context_length=args.context_length,
            truncate=args.truncate,
        )
    except ModuleNotFoundError as exc:
        missing = exc.name or str(exc) or "unknown"
        print(
            "Tokenization failed because --dry-run-tokenize requires the installed "
            f"CLIP tokenizer package and dependencies; missing module: {missing}",
            file=sys.stderr,
        )
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI should report concise validation failures.
        print(f"Tokenization failed: {exc}", file=sys.stderr)
        return 2

    if dry_run:
        print(json.dumps(summary, indent=2, sort_keys=True))
        if not args.dry_run_tokenize and not args.load_model:
            print("No --load-model supplied; completed no-download dry-run tokenization.", file=sys.stderr)
        return 0

    import clip
    import torch

    model, _ = clip.load(args.load_model, device=args.device, jit=False, download_root=args.download_root)
    weights = build_zeroshot_classifier(
        model,
        class_names,
        templates,
        device=args.device,
        context_length=args.context_length,
        truncate=args.truncate,
    )

    result = {
        **summary,
        "model": args.load_model,
        "device": str(args.device),
        "weights_shape": list(weights.shape),
        "class_names": class_names,
        "templates": templates,
    }

    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"weights": weights.detach().cpu(), "class_names": class_names, "templates": templates}, output_path)
        result["output"] = str(output_path)

    if args.metadata_output:
        metadata_path = Path(args.metadata_output).expanduser()
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        result["metadata_output"] = str(metadata_path)

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
