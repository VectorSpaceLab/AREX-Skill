#!/usr/bin/env python3
"""Summarize an ALAE training config without importing ALAE source code."""

from __future__ import annotations

import argparse
from pathlib import Path
from pprint import pformat
from textwrap import indent
import sys

KNOWN_TOP_LEVEL = {"NAME", "PPL_CELEBA_ADJUSTMENT", "OUTPUT_DIR", "DATASET", "MODEL", "TRAIN"}
DATASET_KEYS = {
    "PATH",
    "PATH_TEST",
    "FFHQ_SOURCE",
    "PART_COUNT",
    "PART_COUNT_TEST",
    "SIZE",
    "SIZE_TEST",
    "FLIP_IMAGES",
    "SAMPLES_PATH",
    "STYLE_MIX_PATH",
    "MAX_RESOLUTION_LEVEL",
}
MODEL_KEYS = {
    "LAYER_COUNT",
    "START_CHANNEL_COUNT",
    "MAX_CHANNEL_COUNT",
    "LATENT_SPACE_SIZE",
    "DLATENT_AVG_BETA",
    "TRUNCATIOM_PSI",
    "TRUNCATIOM_CUTOFF",
    "STYLE_MIXING_PROB",
    "MAPPING_LAYERS",
    "CHANNELS",
    "GENERATOR",
    "ENCODER",
    "MAPPING_D",
    "MAPPING_F",
    "Z_REGRESSION",
}
TRAIN_KEYS = {
    "EPOCHS_PER_LOD",
    "BASE_LEARNING_RATE",
    "ADAM_BETA_0",
    "ADAM_BETA_1",
    "LEARNING_DECAY_RATE",
    "LEARNING_DECAY_STEPS",
    "TRAIN_EPOCHS",
    "LOD_2_BATCH_8GPU",
    "LOD_2_BATCH_4GPU",
    "LOD_2_BATCH_2GPU",
    "LOD_2_BATCH_1GPU",
    "SNAPSHOT_FREQ",
    "REPORT_FREQ",
    "LEARNING_RATES",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize an ALAE training config and print a safe launch skeleton.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python scripts/inspect_alae_config.py -c ffhq --repo-root <alae-repository-root>\n"
            "  python scripts/inspect_alae_config.py -c configs/celeba.yaml --repo-root <alae-repository-root>\n"
            "  python scripts/inspect_alae_config.py -c celeba --repo-root <alae-repository-root>\n"
        ),
    )
    parser.add_argument(
        "-c",
        "--config",
        default="ffhq",
        help="Config file path or config name (default: ffhq)",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Checkout root used to resolve relative config names (default: current directory)",
    )
    return parser.parse_args()


def load_yaml(path: Path):
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency issue is reported to user
        raise SystemExit(
            "PyYAML is required to inspect configs. Install it in the ALAE training environment."
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return {} if data is None else data


def unique_paths(paths):
    seen = set()
    result = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def candidate_paths(config_arg: str, repo_root: Path):
    raw = Path(config_arg)
    if raw.suffix.lower() not in {".yaml", ".yml"}:
        raw = raw.with_suffix(".yaml")

    candidates = [raw]
    if not raw.is_absolute():
        candidates.extend(
            [
                repo_root / raw,
                repo_root / "configs" / raw.name,
                Path.cwd() / raw,
                Path.cwd() / "configs" / raw.name,
            ]
        )
    return unique_paths(candidates)


def display_path(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def resolve_config(config_arg: str, repo_root: Path):
    checked = candidate_paths(config_arg, repo_root)
    for path in checked:
        if path.exists():
            return path, checked
    return None, checked


def pretty_value(value):
    if isinstance(value, (dict, list, tuple)):
        return pformat(value, width=88, compact=False)
    return str(value)


def print_section(title: str, section, keys, known_keys=None):
    print(f"{title}:")
    if not isinstance(section, dict):
        print("  <missing or invalid>")
        return

    for key in keys:
        if key in section:
            rendered = pretty_value(section[key])
            print(indent(f"{key}: {rendered}", "  "))

    allowed_for_extra = set(known_keys or keys)
    extras = sorted(set(section.keys()) - allowed_for_extra)
    if extras:
        print(indent(f"extra keys: {', '.join(extras)}", "  "))


def print_command_skeleton(config_arg: str):
    print("Launch skeleton:")
    print("  cd <alae-repository-root>")
    print('  export PYTHONPATH="$PYTHONPATH:$(pwd)"')
    print(f"  python train_alae.py -c {config_arg}")
    print(f"  python train_alae.py -c {config_arg} TRAIN.TRAIN_EPOCHS 1")


def print_path_hints(data):
    output_dir = str(data.get("OUTPUT_DIR", "results"))
    dataset = data.get("DATASET", {}) if isinstance(data.get("DATASET", {}), dict) else {}
    print("Likely paths:")
    print(indent(f"checkpoint pointer: {output_dir}/last_checkpoint", "  "))
    print(indent(f"checkpoints: {output_dir}/model_tmp_intermediate_lod<N>.pth, {output_dir}/model_tmp_lod<N>.pth, {output_dir}/model_final.pth", "  "))
    print(indent(f"logs and samples: {output_dir}/log.txt, {output_dir}/log.csv, {output_dir}/plot.png, {output_dir}/sample_<epoch>_<tick>.jpg", "  "))
    if dataset:
        if "PATH" in dataset:
            print(indent(f"train TFRecords: {dataset['PATH']}", "  "))
        if "PATH_TEST" in dataset:
            print(indent(f"test TFRecords: {dataset['PATH_TEST']}", "  "))
        if "SAMPLES_PATH" in dataset:
            print(indent(f"sample directory: {dataset['SAMPLES_PATH']}", "  "))
        if "STYLE_MIX_PATH" in dataset:
            print(indent(f"style-mixing images: {dataset['STYLE_MIX_PATH']}", "  "))


def warn_for_missing_sections(data):
    missing = sorted(KNOWN_TOP_LEVEL - set(data.keys())) if isinstance(data, dict) else sorted(KNOWN_TOP_LEVEL)
    important_missing = [key for key in ("DATASET", "MODEL", "TRAIN") if key in missing]
    if important_missing:
        print("Warnings:")
        for key in important_missing:
            print(indent(f"missing section: {key}", "  "))


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)
    config_path, checked = resolve_config(args.config, repo_root)

    if config_path is None:
        print("Could not find a config file.", file=sys.stderr)
        print("Checked:", file=sys.stderr)
        for path in checked:
            print(f"  - {path}", file=sys.stderr)
        return 2

    data = load_yaml(config_path)
    if not isinstance(data, dict):
        print(f"Config {display_path(config_path, repo_root)} did not parse as a mapping.", file=sys.stderr)
        return 2

    print(f"Config file: {display_path(config_path, repo_root)}")
    print_command_skeleton(args.config)
    print()
    warn_for_missing_sections(data)
    print_section(
        "Top level",
        data,
        sorted(KNOWN_TOP_LEVEL - {"DATASET", "MODEL", "TRAIN"}),
        known_keys=KNOWN_TOP_LEVEL,
    )
    print_section("DATASET", data.get("DATASET", {}), sorted(DATASET_KEYS))
    print_section("MODEL", data.get("MODEL", {}), sorted(MODEL_KEYS))
    print_section("TRAIN", data.get("TRAIN", {}), sorted(TRAIN_KEYS))
    print()
    print_path_hints(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
