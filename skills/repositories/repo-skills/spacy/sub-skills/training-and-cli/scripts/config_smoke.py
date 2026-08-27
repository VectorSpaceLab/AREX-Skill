#!/usr/bin/env python3
"""Generate and debug a tiny spaCy training config safely.

Purpose:
  Create a starter config, fill defaults, and run config debugging without
  training or downloading pretrained models.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe spaCy config smoke.")
    parser.add_argument("--lang", default="en", help="Language code for init config.")
    parser.add_argument("--pipeline", default="ner", help="Comma-separated pipeline list.")
    parser.add_argument("--optimize", choices=["efficiency", "accuracy"], default="efficiency", help="Optimization target.")
    parser.add_argument("--gpu", action="store_true", help="Generate a GPU-capable config template.")
    parser.add_argument("--pretraining", action="store_true", help="Include pretraining sections in the starter config.")
    parser.add_argument("--output-dir", type=Path, help="Directory for generated config files. Defaults to a temporary directory.")
    parser.add_argument("--run-validate", action="store_true", help="Also run python -m spacy validate after the config smoke.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    import subprocess
    import sys

    import spacy
    from spacy.cli import debug_config
    from spacy.cli.init_config import fill_config, init_config
    from spacy.tokens import DocBin

    if args.output_dir is None:
        temp = tempfile.TemporaryDirectory()
        outdir = Path(temp.name)
    else:
        outdir = args.output_dir
        outdir.mkdir(parents=True, exist_ok=True)

    base_path = outdir / "base.cfg"
    filled_path = outdir / "config.cfg"
    train_data = outdir / "train.spacy"
    dev_data = outdir / "dev.spacy"

    nlp = spacy.blank(args.lang)
    DocBin(docs=[nlp.make_doc("Hello world")]).to_disk(train_data)
    DocBin(docs=[nlp.make_doc("Hello world")]).to_disk(dev_data)

    cfg = init_config(lang=args.lang, pipeline=[p for p in args.pipeline.split(",") if p], optimize=args.optimize, gpu=args.gpu, pretraining=args.pretraining, silent=True)
    cfg["paths"]["train"] = str(train_data)
    cfg["paths"]["dev"] = str(dev_data)
    if args.pretraining:
        raw_text = outdir / "raw_text.jsonl"
        raw_text.write_text('{"text": "Pretraining smoke"}\n', encoding="utf8")
        cfg["paths"]["raw_text"] = str(raw_text)
    cfg.to_disk(base_path)
    fill_config(filled_path, base_path, pretraining=args.pretraining, silent=True)
    debug_config(filled_path)

    validate_rc = None
    if args.run_validate:
        completed = subprocess.run([sys.executable, "-m", "spacy", "validate"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
        validate_rc = completed.returncode

    payload = {
        "base_path": str(base_path),
        "filled_path": str(filled_path),
        "lang": args.lang,
        "pipeline": [p for p in args.pipeline.split(",") if p],
        "gpu": args.gpu,
        "pretraining": args.pretraining,
        "validate_rc": validate_rc,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
