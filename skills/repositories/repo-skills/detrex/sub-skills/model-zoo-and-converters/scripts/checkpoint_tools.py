#!/usr/bin/env python3
"""Safe detrex checkpoint inspection and bounded conversion helpers.

This helper is intentionally local-only:
- it never downloads checkpoints;
- it inspects trusted files on disk;
- it only converts when an explicit family and output path are provided.

Supported conversion families:
- detr
- deformable_detr
- deformable_two_stage
- conditional_detr
- dn_deformable_detr
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, Mapping, MutableMapping, Sequence, Tuple

import torch

COCO_CLASS_INDEX = torch.tensor(
    [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        27,
        28,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        44,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
        61,
        62,
        63,
        64,
        65,
        67,
        70,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        82,
        84,
        85,
        86,
        87,
        88,
        89,
        90,
    ],
    dtype=torch.long,
)
COCO_LABEL_ENCODER_INDEX = torch.tensor(
    [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
        20,
        21,
        22,
        23,
        24,
        25,
        27,
        28,
        31,
        32,
        33,
        34,
        35,
        36,
        37,
        38,
        39,
        40,
        41,
        42,
        43,
        44,
        46,
        47,
        48,
        49,
        50,
        51,
        52,
        53,
        54,
        55,
        56,
        57,
        58,
        59,
        60,
        61,
        62,
        63,
        64,
        65,
        67,
        70,
        72,
        73,
        74,
        75,
        76,
        77,
        78,
        79,
        80,
        81,
        82,
        84,
        85,
        86,
        87,
        88,
        89,
        90,
        91,
    ],
    dtype=torch.long,
)
FAMILY_CHOICES = (
    "auto",
    "detr",
    "deformable_detr",
    "deformable_two_stage",
    "conditional_detr",
    "dn_deformable_detr",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect or convert DETR-family checkpoints without downloads.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect = subparsers.add_parser(
        "inspect",
        help="Summarize a checkpoint and suggest a conversion family.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    inspect.add_argument(
        "checkpoint_arg",
        nargs="?",
        type=str,
        help="Local checkpoint path to inspect. You may also use --checkpoint.",
    )
    inspect.add_argument(
        "--checkpoint",
        dest="checkpoint_opt",
        type=str,
        default="",
        help="Local checkpoint path to inspect.",
    )
    inspect.add_argument(
        "--family",
        choices=FAMILY_CHOICES,
        default="auto",
        help="Optional family hint for the inspect report.",
    )
    inspect.add_argument(
        "--sample-keys",
        type=int,
        default=10,
        help="Number of keys to show in the sample list.",
    )

    convert = subparsers.add_parser(
        "convert",
        help="Convert a local official checkpoint into detrex format.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    convert.add_argument(
        "--family",
        choices=FAMILY_CHOICES,
        default="auto",
        help="Converter family to apply.",
    )
    convert.add_argument(
        "--source-model",
        required=True,
        type=str,
        help="Local source checkpoint path.",
    )
    convert.add_argument(
        "--output-model",
        required=True,
        type=str,
        help="Path for the converted checkpoint.",
    )
    convert.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned conversion without writing an output file.",
    )

    return parser.parse_args()


def _is_url(path_text: str) -> bool:
    return path_text.startswith(("http://", "https://"))


def load_checkpoint(path_text: str):
    if _is_url(path_text):
        raise ValueError("Remote checkpoint downloads are disabled in this helper.")
    path = Path(path_text)
    if not path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {path}")
    return torch.load(path, map_location="cpu")


def extract_state_dict(checkpoint) -> Tuple[MutableMapping[str, object], str, Sequence[str]]:
    if isinstance(checkpoint, Mapping):
        top_keys = list(checkpoint.keys())
        for candidate in ("model", "state_dict", "model_state_dict"):
            value = checkpoint.get(candidate)
            if isinstance(value, Mapping):
                return dict(value), candidate, top_keys
        if checkpoint and all(torch.is_tensor(v) for v in checkpoint.values()):
            return dict(checkpoint), "flat_state_dict", top_keys
    raise TypeError(
        "Unsupported checkpoint format. Expected a mapping with a model/state_dict entry or a flat state dict."
    )


def strip_module_prefix(state_dict: MutableMapping[str, object]) -> Tuple[MutableMapping[str, object], str]:
    keys = list(state_dict.keys())
    if keys and all(key.startswith("module.") for key in keys):
        return {key[len("module.") :]: value for key, value in state_dict.items()}, "module."
    return dict(state_dict), ""


def has_signal(keys: Iterable[str], token: str) -> bool:
    return any(token in key for key in keys)


def detect_family(keys: Sequence[str]) -> Tuple[str, str]:
    key_list = list(keys)
    if has_signal(key_list, "label_enc"):
        return "conditional_detr", "found label_enc"
    if has_signal(key_list, "ca_qcontent_proj") or has_signal(key_list, "sa_qcontent_proj"):
        if has_signal(key_list, "input_proj"):
            return "dn_deformable_detr", "found conditional projections plus input_proj"
        return "conditional_detr", "found conditional projections"
    if has_signal(key_list, "class_embed.6"):
        return "deformable_two_stage", "found class_embed.6"
    if has_signal(key_list, "input_proj"):
        return "deformable_detr", "found input_proj"
    if has_signal(key_list, "query_embed") or has_signal(key_list, "level_embed"):
        return "detr", "found query_embed/level_embed"
    return "unknown", "no strong family signal found"


def is_already_detrex(keys: Sequence[str]) -> bool:
    key_list = list(keys)
    converted_signals = [
        "attentions.",
        "neck.",
        "label_encoder",
        "decoder.post_norm_layer",
        "level_embeds",
        "query_embedding",
    ]
    return any(has_signal(key_list, token) for token in converted_signals)


def remap_backbone_key(key: str) -> str:
    key = key.replace("backbone.0.body.", "")
    if "layer" not in key:
        key = "stem." + key
    for level in (1, 2, 3, 4):
        key = key.replace(f"layer{level}", f"res{level + 1}")
    for bn_idx in (1, 2, 3):
        key = key.replace(f"bn{bn_idx}", f"conv{bn_idx}.norm")
    key = key.replace("downsample.0", "shortcut")
    key = key.replace("downsample.1", "shortcut.norm")
    return "backbone." + key


def remap_input_proj_key(key: str) -> str:
    key = key.replace("input_proj.0.0", "neck.convs.0.conv")
    key = key.replace("input_proj.0.1", "neck.convs.0.norm")
    key = key.replace("input_proj.1.0", "neck.convs.1.conv")
    key = key.replace("input_proj.1.1", "neck.convs.1.norm")
    key = key.replace("input_proj.2.0", "neck.convs.2.conv")
    key = key.replace("input_proj.2.1", "neck.convs.2.norm")
    key = key.replace("input_proj.3.0", "neck.extra_convs.0.conv")
    key = key.replace("input_proj.3.1", "neck.extra_convs.0.norm")
    return key


def remap_detr_key(key: str, value: object) -> Tuple[str, object, str | None]:
    new_key = key
    note = None
    if "backbone" in new_key:
        new_key = remap_backbone_key(new_key)
    if "encoder" in new_key:
        if "self_attn" in new_key:
            new_key = new_key.replace("self_attn", "attentions.0.attn")
        elif "linear1" in new_key:
            new_key = new_key.replace("linear1", "ffns.0.layers.0.0")
        elif "linear2" in new_key:
            new_key = new_key.replace("linear2", "ffns.0.layers.1")
        elif "norm1" in new_key:
            new_key = new_key.replace("norm1", "norms.0")
        elif "norm2" in new_key:
            new_key = new_key.replace("norm2", "norms.1")
    if "decoder" in new_key:
        if "decoder.norm" in new_key:
            new_key = new_key.replace("decoder.norm", "decoder.post_norm_layer")
        elif "linear1" in new_key:
            new_key = new_key.replace("linear1", "ffns.0.layers.0.0")
        elif "linear2" in new_key:
            new_key = new_key.replace("linear2", "ffns.0.layers.1")
        elif "norm1" in new_key:
            new_key = new_key.replace("norm1", "norms.0")
        elif "norm2" in new_key:
            new_key = new_key.replace("norm2", "norms.1")
        elif "norm3" in new_key:
            new_key = new_key.replace("norm3", "norms.2")
        elif "self_attn" in new_key:
            new_key = new_key.replace("self_attn", "attentions.0.attn")
        elif "multihead_attn" in new_key:
            new_key = new_key.replace("multihead_attn", "attentions.1.attn")
    if "level_embed" in new_key:
        new_key = new_key.replace("level_embed", "level_embeds")
    if "query_embed" in new_key:
        new_key = new_key.replace("query_embed", "query_embedding")
    if "class_embed" in key and torch.is_tensor(value) and value.ndim >= 1 and value.shape[0] == 92:
        new_value = value.index_select(0, COCO_CLASS_INDEX)
        note = f"class head remap {tuple(value.shape)} -> {tuple(new_value.shape)}"
        return new_key, new_value, note
    if torch.is_tensor(value):
        value = value.detach()
    return new_key, value, note


def remap_deformable_key(key: str, value: object) -> Tuple[str, object, str | None]:
    new_key = key
    note = None
    if "backbone" in new_key:
        new_key = remap_backbone_key(new_key)
    if "input_proj" in new_key:
        new_key = remap_input_proj_key(new_key)
    if "encoder.layers" in new_key:
        if "self_attn" in new_key:
            new_key = new_key.replace("self_attn", "attentions.0")
        elif "linear1" in new_key:
            new_key = new_key.replace("linear1", "ffns.0.layers.0.0")
        elif "linear2" in new_key:
            new_key = new_key.replace("linear2", "ffns.0.layers.1")
        elif "norm1" in new_key:
            new_key = new_key.replace("norm1", "norms.0")
        elif "norm2" in new_key:
            new_key = new_key.replace("norm2", "norms.1")
    if "decoder" in new_key:
        if "linear1" in new_key:
            new_key = new_key.replace("linear1", "ffns.0.layers.0.0")
        elif "linear2" in new_key:
            new_key = new_key.replace("linear2", "ffns.0.layers.1")
        elif "norm1" in new_key:
            new_key = new_key.replace("norm1", "norms.1")
        elif "norm2" in new_key:
            new_key = new_key.replace("norm2", "norms.0")
        elif "norm3" in new_key:
            new_key = new_key.replace("norm3", "norms.2")
        elif "self_attn" in new_key:
            new_key = new_key.replace("self_attn", "attentions.0.attn")
        elif "cross_attn" in new_key:
            new_key = new_key.replace("cross_attn", "attentions.1")
    if "level_embed" in new_key:
        new_key = new_key.replace("level_embed", "level_embeds")
    if "query_embed" in new_key:
        new_key = new_key.replace("query_embed", "query_embedding")
    if "class_embed" in key and "class_embed.6" not in key and torch.is_tensor(value) and value.ndim >= 1 and value.shape[0] == 91:
        new_value = value.index_select(0, COCO_CLASS_INDEX)
        note = f"class head remap {tuple(value.shape)} -> {tuple(new_value.shape)}"
        return new_key, new_value, note
    if torch.is_tensor(value):
        value = value.detach()
    return new_key, value, note


def remap_deformable_two_stage_key(key: str, value: object) -> Tuple[str, object, str | None]:
    new_key, new_value, note = remap_deformable_key(key, value)
    if "class_embed.6" in key and torch.is_tensor(value):
        new_value = value.detach()[:80]
        note = f"two-stage class head trim {tuple(value.shape)} -> {tuple(new_value.shape)}"
    return new_key, new_value, note


def remap_conditional_key(key: str, value: object) -> Tuple[str, object, str | None]:
    new_key = key
    note = None
    if "backbone" in new_key:
        new_key = remap_backbone_key(new_key)
    if "encoder.layers" in new_key:
        if "self_attn" in new_key:
            new_key = new_key.replace("self_attn", "attentions.0.attn")
        elif "linear1" in new_key:
            new_key = new_key.replace("linear1", "ffns.0.layers.0.0")
        elif "linear2" in new_key:
            new_key = new_key.replace("linear2", "ffns.0.layers.1")
        elif "norm1" in new_key:
            new_key = new_key.replace("norm1", "norms.0")
        elif "norm2" in new_key:
            new_key = new_key.replace("norm2", "norms.1")
        elif "activation" in new_key:
            new_key = new_key.replace("activation", "ffns.0.layers.0.1")
    if "decoder" in new_key:
        if "decoder.norm" in new_key:
            new_key = new_key.replace("decoder.norm", "decoder.post_norm_layer")
        elif "ca_kcontent_proj" in new_key:
            new_key = new_key.replace("ca_kcontent_proj", "attentions.1.key_content_proj")
        elif "ca_kpos_proj" in new_key:
            new_key = new_key.replace("ca_kpos_proj", "attentions.1.key_pos_proj")
        elif "ca_qcontent_proj" in new_key:
            new_key = new_key.replace("ca_qcontent_proj", "attentions.1.query_content_proj")
        elif "ca_qpos_proj" in new_key:
            new_key = new_key.replace("ca_qpos_proj", "attentions.1.query_pos_proj")
        elif "ca_qpos_sine_proj" in new_key:
            new_key = new_key.replace("ca_qpos_sine_proj", "attentions.1.query_pos_sine_proj")
        elif "ca_v_proj" in new_key:
            new_key = new_key.replace("ca_v_proj", "attentions.1.value_proj")
        elif "sa_kcontent_proj" in new_key:
            new_key = new_key.replace("sa_kcontent_proj", "attentions.0.key_content_proj")
        elif "sa_kpos_proj" in new_key:
            new_key = new_key.replace("sa_kpos_proj", "attentions.0.key_pos_proj")
        elif "sa_qcontent_proj" in new_key:
            new_key = new_key.replace("sa_qcontent_proj", "attentions.0.query_content_proj")
        elif "sa_qpos_proj" in new_key:
            new_key = new_key.replace("sa_qpos_proj", "attentions.0.query_pos_proj")
        elif "sa_v_proj" in new_key:
            new_key = new_key.replace("sa_v_proj", "attentions.0.value_proj")
        elif "self_attn.out_proj" in new_key:
            new_key = new_key.replace("self_attn.out_proj", "attentions.0.out_proj")
        elif "cross_attn.out_proj" in new_key:
            new_key = new_key.replace("cross_attn.out_proj", "attentions.1.out_proj")
        elif "linear1" in new_key:
            new_key = new_key.replace("linear1", "ffns.0.layers.0.0")
        elif "linear2" in new_key:
            new_key = new_key.replace("linear2", "ffns.0.layers.1")
        elif "norm1" in new_key:
            new_key = new_key.replace("norm1", "norms.1")
        elif "norm2" in new_key:
            new_key = new_key.replace("norm2", "norms.0")
        elif "norm3" in new_key:
            new_key = new_key.replace("norm3", "norms.2")
        elif "activation" in new_key:
            new_key = new_key.replace("activation", "ffns.0.layers.0.1")
    if "level_embed" in new_key:
        new_key = new_key.replace("level_embed", "level_embeds")
    if "class_embed" in key and torch.is_tensor(value) and value.ndim >= 1 and value.shape[0] == 91:
        new_value = value.index_select(0, COCO_CLASS_INDEX)
        note = f"class head remap {tuple(value.shape)} -> {tuple(new_value.shape)}"
        return new_key, new_value, note
    if "label_enc" in key and torch.is_tensor(value):
        new_key = new_key.replace("label_enc", "label_encoder")
        if value.ndim >= 1 and value.shape[0] == 92:
            new_value = value.index_select(0, COCO_LABEL_ENCODER_INDEX)
            note = f"label encoder remap {tuple(value.shape)} -> {tuple(new_value.shape)}"
            return new_key, new_value, note
    if torch.is_tensor(value):
        value = value.detach()
    return new_key, value, note


def remap_dn_deformable_key(key: str, value: object) -> Tuple[str, object, str | None]:
    if "input_proj" in key:
        key = remap_input_proj_key(key)
    return remap_conditional_key(key, value)


FAMILY_REMAPS = {
    "detr": remap_detr_key,
    "deformable_detr": remap_deformable_key,
    "deformable_two_stage": remap_deformable_two_stage_key,
    "conditional_detr": remap_conditional_key,
    "dn_deformable_detr": remap_dn_deformable_key,
}


def summarize_state_dict(state_dict: Mapping[str, object], sample_keys: int) -> None:
    keys = list(state_dict.keys())
    print(f"Tensor entries: {len(keys)}")
    prefix_counts = Counter(key.split(".", 1)[0] for key in keys)
    print("Top-level prefixes:")
    for prefix, count in prefix_counts.most_common(8):
        print(f"  - {prefix}: {count}")
    print("Sample keys:")
    for key in sorted(keys)[: max(sample_keys, 0)]:
        value = state_dict[key]
        if torch.is_tensor(value):
            shape = tuple(value.shape)
            dtype = str(value.dtype).replace("torch.", "")
        else:
            shape = type(value).__name__
            dtype = "non-tensor"
        print(f"  - {key}: {shape} [{dtype}]")


def inspect_checkpoint(args: argparse.Namespace) -> None:
    checkpoint_path = args.checkpoint_opt or args.checkpoint_arg
    if not checkpoint_path:
        raise ValueError("inspect requires a checkpoint path, either positional or --checkpoint")
    checkpoint = load_checkpoint(checkpoint_path)
    state_dict, container, top_keys = extract_state_dict(checkpoint)
    state_dict, stripped_prefix = strip_module_prefix(state_dict)
    keys = list(state_dict.keys())
    family, reason = detect_family(keys)
    already_converted = is_already_detrex(keys)

    print(f"Checkpoint: {checkpoint_path}")
    print(f"Top-level container: {container}")
    if len(top_keys) <= 10:
        print("Top-level keys: " + ", ".join(map(str, top_keys)))
    else:
        print("Top-level keys: " + ", ".join(map(str, top_keys[:10])) + ", ...")
    if stripped_prefix:
        print(f"Stripped wrapper prefix: {stripped_prefix}")
    print(f"Detected family: {family} ({reason})")
    print(f"Already looks detrex-shaped: {'yes' if already_converted else 'no'}")
    summarize_state_dict(state_dict, args.sample_keys)

    if already_converted:
        print("Suggested next step: load this checkpoint directly; it already looks detrex-shaped.")
    elif family != "unknown":
        print(
            "Suggested convert command: "
            f"python scripts/checkpoint_tools.py convert --family {family} "
            f"--source-model {checkpoint_path} --output-model converted_checkpoint.pth"
        )
    else:
        print(
            "Suggested next step: compare the key summary against the family matrix in references/converters.md."
        )


def convert_state_dict(
    state_dict: Mapping[str, object], family: str
) -> Tuple[Dict[str, object], Sequence[str]]:
    remap = FAMILY_REMAPS[family]
    converted: Dict[str, object] = {}
    notes = []
    for key, value in state_dict.items():
        new_key, new_value, note = remap(key, value)
        converted[new_key] = new_value
        if note is not None:
            notes.append(f"{key}: {note}")
    return converted, notes


def convert_checkpoint(args: argparse.Namespace) -> None:
    checkpoint = load_checkpoint(args.source_model)
    state_dict, container, top_keys = extract_state_dict(checkpoint)
    state_dict, stripped_prefix = strip_module_prefix(state_dict)
    keys = list(state_dict.keys())

    if is_already_detrex(keys):
        raise ValueError(
            "This checkpoint already looks detrex-shaped. Inspect it or load it directly instead of converting again."
        )

    family = args.family
    if family == "auto":
        family, reason = detect_family(keys)
        print(f"Auto-detected family: {family} ({reason})")
    if family not in FAMILY_REMAPS:
        if family == "unknown":
            raise ValueError(
                "Unable to auto-detect a supported family. Re-run inspect and choose an explicit family."
            )
        raise ValueError(f"Unsupported family: {family}")

    converted, notes = convert_state_dict(state_dict, family)
    output_path = Path(args.output_model)
    print(f"Source container: {container}")
    if stripped_prefix:
        print(f"Stripped wrapper prefix: {stripped_prefix}")
    print(f"Input keys: {len(state_dict)}")
    print(f"Output keys: {len(converted)}")
    if notes:
        print("Head remap notes:")
        for note in notes[:10]:
            print(f"  - {note}")
        if len(notes) > 10:
            print(f"  - ... {len(notes) - 10} more")
    if args.dry_run:
        print(f"Dry run only; no file written to {output_path}")
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model": converted}, output_path)
    print(f"Wrote converted checkpoint to {output_path}")


def main() -> None:
    args = parse_args()
    if args.command == "inspect":
        inspect_checkpoint(args)
    elif args.command == "convert":
        convert_checkpoint(args)
    else:
        raise ValueError(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
