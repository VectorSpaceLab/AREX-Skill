#!/usr/bin/env python3
"""Evaluate a scispaCy-compatible NER model on TSV or MedMentions data.

This is a thin, explicit wrapper around `scispacy.train_utils.evaluate_ner`.
It keeps GPU usage optional and supports pre-importing custom code before the
spaCy model loads.

Example:
    python scripts/evaluate_ner.py --model_path /path/to/model --dataset /path/to/ner.tsv --output_path /tmp/metrics.json
"""

from __future__ import annotations

import argparse
import importlib.util

import spacy

from scispacy.data_util import read_full_med_mentions, read_ner_from_tsv
from scispacy.train_utils import evaluate_ner

try:
    from thinc.api import require_gpu
except ImportError:  # pragma: no cover - optional dependency only used when requested
    require_gpu = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_path", type=str, required=True, help="Path to a spaCy model or package name.")
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Either a BIO TSV path or a MedMentions split name like medmentions-test.",
    )
    parser.add_argument("--output_path", type=str, required=True, help="Path where the metrics JSON will be appended.")
    parser.add_argument("--code", type=str, default=None, help="Optional Python file to import before loading the model.")
    parser.add_argument(
        "--med_mentions_folder_path",
        type=str,
        default=None,
        help="MedMentions folder path, required when dataset starts with medmentions-.",
    )
    parser.add_argument("--gpu_id", type=int, default=-1, help="GPU id to use, or -1 for CPU.")
    return parser


def import_custom_code(code_path: str) -> None:
    spec = importlib.util.spec_from_file_location("python_code", str(code_path))
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not load custom code file: {code_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)



def main() -> None:
    args = build_parser().parse_args()

    if args.gpu_id is not None and args.gpu_id >= 0:
        if require_gpu is None:
            raise SystemExit("GPU evaluation was requested, but thinc is not available in this environment.")
        require_gpu(args.gpu_id)

    if args.code is not None:
        import_custom_code(args.code)

    nlp = spacy.load(args.model_path)
    if args.dataset.startswith("medmentions"):
        if args.med_mentions_folder_path is None:
            raise SystemExit("--med_mentions_folder_path is required when dataset starts with medmentions-")
        train_data, dev_data, test_data = read_full_med_mentions(args.med_mentions_folder_path, None, False)
        split = args.dataset.split("-", 1)[1]
        if split == "train":
            data = train_data
        elif split == "dev":
            data = dev_data
        elif split == "test":
            data = test_data
        else:
            raise SystemExit(f"Unrecognized MedMentions split: {split}")
    else:
        data = read_ner_from_tsv(args.dataset)

    metrics = evaluate_ner(nlp, data, dump_path=args.output_path)
    print(metrics)


if __name__ == "__main__":
    main()
