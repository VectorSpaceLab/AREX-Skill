#!/usr/bin/env python3
"""Smoke-test seq2seq-couplet serving routes without opening a network socket.

By default this trains a tiny checkpoint, loads it in inference mode, builds the
Flask app, and exercises both service routes through a test client. Use
``--fake-model`` when you only need to check route wiring and JSON shapes.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

SKILL_ROOT = Path(__file__).resolve().parents[3]
ROOT_SCRIPTS = SKILL_ROOT / "scripts"
if str(ROOT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ROOT_SCRIPTS))

import couplet_runtime  # noqa: E402


class FakeModel:
    def infer(self, text):
        import numpy as np

        return ["风云"], np.array([1.0])


def path_arg(value: str) -> Path:
    return Path(value).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-test the seq2seq-couplet Flask routes.")
    parser.add_argument("--repo-root", default=None, help="Optional checkout to use instead of the bundled runtime copy.")
    parser.add_argument("--workdir", help="Directory for tiny fixture and checkpoint. Defaults to a temp dir.")
    parser.add_argument("--vocab-file", type=path_arg, help="Existing vocab file to use instead of training a tiny checkpoint.")
    parser.add_argument("--model-dir", type=path_arg, help="Existing checkpoint directory to use instead of training a tiny checkpoint.")
    parser.add_argument("--input", default="天地", help="Raw input string to request through both routes.")
    parser.add_argument("--num-units", type=int, default=16)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--dropout", type=float, default=0.0)
    parser.add_argument("--max-input-length", type=int, default=50)
    parser.add_argument("--fake-model", action="store_true", help="Use a fake model for a fast route-shape check.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.workdir:
        workdir = Path(args.workdir).expanduser().resolve()
        workdir.mkdir(parents=True, exist_ok=True)
    else:
        workdir = Path(tempfile.mkdtemp(prefix="seq2seq-couplet-serve-smoke-"))

    generated = {}
    if args.fake_model:
        model = FakeModel()
        vocab_file = args.vocab_file
        model_dir = args.model_dir
    else:
        if args.vocab_file and args.model_dir:
            vocab_file = args.vocab_file
            model_dir = args.model_dir
        else:
            generated = couplet_runtime.train_tiny_checkpoint(
                args.repo_root,
                workdir,
                num_units=args.num_units,
                layers=args.layers,
                dropout=args.dropout,
                batch_size=1,
                learning_rate=0.01,
                epochs=1,
            )
            vocab_file = generated["vocab_file"]
            model_dir = generated["output_dir"]
        model = couplet_runtime.load_inference_model(
            args.repo_root,
            vocab_file=vocab_file,
            model_dir=model_dir,
            num_units=args.num_units,
            layers=args.layers,
            dropout=args.dropout,
        )

    app = couplet_runtime.build_flask_app(
        model,
        censor_words=[],
        max_input_length=args.max_input_length,
        enable_cors=False,
    )
    client = app.test_client()
    top_resp = client.get("/chat/couplet/%s" % args.input)
    v2_resp = client.get("/v0.2/couplet/%s" % args.input)
    if top_resp.status_code != 200 or v2_resp.status_code != 200:
        raise SystemExit("route smoke failed: %s %s" % (top_resp.status_code, v2_resp.status_code))
    top_json = top_resp.get_json()
    v2_json = v2_resp.get_json()
    if "output" not in top_json or "output" not in v2_json or "score" not in v2_json:
        raise SystemExit("route smoke failed: missing expected JSON keys")

    summary = {
        "mode": "fake" if args.fake_model else "tiny-checkpoint",
        "workdir": str(workdir),
        "vocab_file": str(vocab_file) if vocab_file else None,
        "model_dir": str(model_dir) if model_dir else None,
        "routes": {
            "/chat/couplet/<in_str>": top_json,
            "/v0.2/couplet/<in_str>": v2_json,
        },
    }
    if generated:
        summary["generated"] = {k: str(v) for k, v in generated.items() if k != "model"}
    print("Serving route smoke passed.")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
