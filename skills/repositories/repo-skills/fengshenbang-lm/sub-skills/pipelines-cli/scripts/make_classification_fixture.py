#!/usr/bin/env python3
"""Create a tiny Fengshen text-classification JSONL fixture.

The fixture is safe: it writes local JSONL files only and prints matching field
flags plus a local-data Python training shape. It does not import Fengshen,
download datasets, train, or mutate checkpoints.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List, Mapping

TRAIN_ROWS = [
    {"id": 0, "sentence": "今天心情很好", "sentence2": "今天很开心", "label": 1},
    {"id": 1, "sentence": "天气很好", "sentence2": "我想吃火锅", "label": 0},
    {"id": 2, "sentence": "这家店味道不错", "sentence2": "这家餐馆很好吃", "label": 1},
    {"id": 3, "sentence": "我喜欢跑步", "sentence2": "股票今天下跌", "label": 0},
]
DEV_ROWS = [
    {"id": 100, "sentence": "这个问题很简单", "sentence2": "这个题目不难", "label": 1},
    {"id": 101, "sentence": "猫在窗边睡觉", "sentence2": "会议下午开始", "label": 0},
]
TEST_ROWS = [
    {"id": 200, "sentence": "今天适合散步", "sentence2": "今天可以出门走走", "label": 1},
    {"id": 201, "sentence": "手机需要充电", "sentence2": "我正在读书", "label": 0},
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Write tiny JSONL files with sentence/sentence2/label/id fields for Fengshen text classification."
    )
    parser.add_argument("--out-dir", default="./fengshen-classification-fixture", help="Directory to create.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing fixture files.")
    parser.add_argument(
        "--texta-name", default="sentence", help="First text field name to describe in printed flags."
    )
    parser.add_argument(
        "--textb-name", default="sentence2", help="Second text field name to describe in printed flags."
    )
    parser.add_argument("--label-name", default="label", help="Label field name to describe in printed flags.")
    return parser


def maybe_rename(row: Mapping[str, object], texta: str, textb: str, label: str) -> Mapping[str, object]:
    renamed = {"id": row["id"], texta: row["sentence"], textb: row["sentence2"], label: row["label"]}
    return renamed


def write_jsonl(path: Path, rows: Iterable[Mapping[str, object]], overwrite: bool) -> int:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} exists; pass --overwrite to replace it")
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def print_guidance(out_dir: Path, args: argparse.Namespace) -> None:
    train = out_dir / "train.json"
    dev = out_dir / "dev.json"
    test = out_dir / "test.json"
    print("\nField flags:")
    print(f"  --texta_name {args.texta_name} --textb_name {args.textb_name} --label_name {args.label_name} --max_length 128")
    print("\nPublic-dataset console pattern:")
    print("  fengshen-pipeline text_classification train \\")
    print("    --model MODEL_OR_LOCAL_DIR \\")
    print("    --datasets IDEA-CCNL/AFQMC \\")
    print(f"    --texta_name {args.texta_name} --textb_name {args.textb_name} --label_name {args.label_name} \\")
    print("    --gpus 0")
    print("\nLocal JSONL/no-download route (paste into your own script after choosing a model):")
    print("  from argparse import ArgumentParser")
    print("  from datasets import load_dataset")
    print("  from fengshen.pipelines.text_classification import TextClassificationPipeline")
    print("  parser = ArgumentParser()")
    print("  parser.add_argument('--model', default='MODEL_OR_LOCAL_DIR')")
    print("  parser = TextClassificationPipeline.add_pipeline_specific_args(parser)")
    print("  args = parser.parse_args(['--model','MODEL_OR_LOCAL_DIR',")
    print(f"      '--texta_name','{args.texta_name}','--textb_name','{args.textb_name}',")
    print(f"      '--label_name','{args.label_name}','--max_length','128','--gpus','0'])")
    print("  datasets = load_dataset('json', data_files={")
    print(f"      'train': '{train.as_posix()}',")
    print(f"      'validation': '{dev.as_posix()}',")
    print(f"      'test': '{test.as_posix()}',")
    print("  })")
    print("  pipe = TextClassificationPipeline(args=args, model=args.model)")
    print("  pipe.train(datasets)")
    print("\nNotes:")
    print("  - Labels are integer ids because the pipeline collator tensors them directly.")
    print("  - The generic console train path has only --datasets, not a full local data_files interface.")
    print("  - The code above still loads model/tokenizer weights unless MODEL_OR_LOCAL_DIR is local or cached.")


def main() -> int:
    args = build_parser().parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    splits: List[tuple[str, List[Mapping[str, object]]]] = [
        ("train.json", [maybe_rename(r, args.texta_name, args.textb_name, args.label_name) for r in TRAIN_ROWS]),
        ("dev.json", [maybe_rename(r, args.texta_name, args.textb_name, args.label_name) for r in DEV_ROWS]),
        ("test.json", [maybe_rename(r, args.texta_name, args.textb_name, args.label_name) for r in TEST_ROWS]),
    ]
    for filename, rows in splits:
        count = write_jsonl(out_dir / filename, rows, args.overwrite)
        print(f"wrote {count} rows: {(out_dir / filename).as_posix()}")
    print_guidance(out_dir, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
