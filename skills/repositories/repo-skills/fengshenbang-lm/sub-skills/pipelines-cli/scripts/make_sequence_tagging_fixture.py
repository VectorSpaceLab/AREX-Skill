#!/usr/bin/env python3
"""Create a tiny Fengshen sequence-tagging fixture layout.

The fixture is safe: it writes labels.txt and *.all.bmes files only, then prints
parser flags and decode-type guidance. It does not import Fengshen, download
models, launch training, or mutate checkpoints.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

LABELS = [
    "O",
    "B-PER",
    "I-PER",
    "E-PER",
    "B-LOC",
    "I-LOC",
    "E-LOC",
    "B-ORG",
    "I-ORG",
    "E-ORG",
    "S-ORG",
]

TRAIN_SENTENCES: List[List[Tuple[str, str]]] = [
    [("小", "B-PER"), ("明", "E-PER"), ("在", "O"), ("北", "B-LOC"), ("京", "E-LOC"), ("工", "O"), ("作", "O")],
    [("华", "B-ORG"), ("为", "E-ORG"), ("发", "O"), ("布", "O"), ("手", "O"), ("机", "O")],
]
DEV_SENTENCES: List[List[Tuple[str, str]]] = [
    [("小", "B-PER"), ("红", "E-PER"), ("去", "O"), ("上", "B-LOC"), ("海", "E-LOC")],
]
TEST_SENTENCES: List[List[Tuple[str, str]]] = [
    [("腾", "B-ORG"), ("讯", "E-ORG"), ("在", "O"), ("深", "B-LOC"), ("圳", "E-LOC")],
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write labels.txt and train/dev/test .all.bmes files for Fengshen sequence tagging."
    )
    parser.add_argument("--out-dir", default="./fengshen-sequence-tagging-fixture", help="Directory to create.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing fixture files.")
    parser.add_argument(
        "--decode-type",
        default="linear",
        choices=["linear", "crf", "span", "biaffine"],
        help="Decode type to emphasize in printed guidance.",
    )
    parser.add_argument("--model-type", default="bert", help="Model type prefix, usually bert.")
    return parser


def write_text(path: Path, content: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} exists; pass --overwrite to replace it")
    path.write_text(content, encoding="utf-8")


def format_bmes(sentences: Iterable[Sequence[Tuple[str, str]]]) -> str:
    blocks = []
    for sentence in sentences:
        blocks.append("\n".join(f"{token} {label}" for token, label in sentence))
    return "\n\n".join(blocks) + "\n"


def print_guidance(out_dir: Path, args: argparse.Namespace) -> None:
    print("\nRequired files:")
    print(f"  labels: {(out_dir / 'labels.txt').as_posix()}")
    print(f"  train:  {(out_dir / 'train.all.bmes').as_posix()}")
    print(f"  dev:    {(out_dir / 'dev.all.bmes').as_posix()}")
    print(f"  test:   {(out_dir / 'test.all.bmes').as_posix()}  (included for completeness)")
    print("\nParser flags:")
    print(f"  --data_dir {out_dir.as_posix()} --model_type {args.model_type} --decode_type {args.decode_type} --max_seq_length 128")
    print("\nProgrammatic initialization shape:")
    print("  from argparse import ArgumentParser")
    print("  from fengshen.pipelines.sequence_tagging import SequenceTaggingPipeline")
    print("  parser = ArgumentParser()")
    print("  parser.add_argument('--model', default='MODEL_OR_LOCAL_DIR')")
    print("  parser = SequenceTaggingPipeline.add_pipeline_specific_args(parser)")
    print("  args = parser.parse_args(['--model','MODEL_OR_LOCAL_DIR',")
    print(f"      '--data_dir','{out_dir.as_posix()}',")
    print(f"      '--model_type','{args.model_type}','--decode_type','{args.decode_type}',")
    print("      '--max_seq_length','128','--gpus','0'])")
    print("  pipe = SequenceTaggingPipeline(model_path=args.model, args=args)")
    print("\nDecode-type notes:")
    print("  - linear/crf use full token labels from labels.txt, such as B-PER and E-PER.")
    print("  - span/biaffine derive entity types from label suffixes, such as PER and LOC.")
    print("  - labels.txt should not include [PAD], [START], or [END]; Fengshen adds them internally.")
    print("  - The generic fengshen-pipeline train route is not recommended for sequence_tagging; use Python.")


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_text(out_dir / "labels.txt", "\n".join(LABELS) + "\n", args.overwrite)
    write_text(out_dir / "train.all.bmes", format_bmes(TRAIN_SENTENCES), args.overwrite)
    write_text(out_dir / "dev.all.bmes", format_bmes(DEV_SENTENCES), args.overwrite)
    write_text(out_dir / "test.all.bmes", format_bmes(TEST_SENTENCES), args.overwrite)

    print(f"wrote sequence-tagging fixture under {out_dir.as_posix()}")
    print_guidance(out_dir, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
