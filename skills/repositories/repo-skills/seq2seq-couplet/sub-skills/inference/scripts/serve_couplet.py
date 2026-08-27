#!/usr/bin/env python3
"""Parameterized Flask/gevent service wrapper for seq2seq-couplet.

The legacy source service uses fixed file paths and starts a listener at import
time. This wrapper keeps startup explicit and path-driven.
"""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
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


def configure_logging(log_file: Optional[Path]) -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(str(log_file), maxBytes=1024 * 1024 * 20, backupCount=10)
        handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        logger.addHandler(handler)
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve seq2seq-couplet through Flask/gevent.")
    parser.add_argument("--repo-root", default=None, help="Optional checkout to use instead of the bundled runtime copy.")
    parser.add_argument("--vocab-file", type=path_arg, required=True)
    parser.add_argument("--model-dir", type=path_arg, required=True)
    parser.add_argument("--censor-words-file", type=path_arg)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--log-file", type=path_arg)
    parser.add_argument("--max-input-length", type=int, default=50)
    parser.add_argument("--num-units", type=int, default=1024)
    parser.add_argument("--layers", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--no-cors", action="store_true", help="Disable Flask-CORS setup.")
    parser.add_argument("--flask-dev-server", action="store_true", help="Use Flask's dev server instead of gevent.")
    parser.add_argument("--dry-run", action="store_true", help="Validate config and route setup without loading the checkpoint or starting a listener.")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.vocab_file.exists():
        raise SystemExit("vocab file not found: %s" % args.vocab_file)
    if not args.model_dir.exists():
        raise SystemExit("model directory not found: %s" % args.model_dir)
    couplet_runtime.validate_vocab_file(args.vocab_file)
    censor_words = couplet_runtime.load_censor_words(args.censor_words_file)
    configure_logging(args.log_file)

    if args.dry_run:
        app = couplet_runtime.build_flask_app(
            FakeModel(),
            censor_words=censor_words,
            max_input_length=args.max_input_length,
            enable_cors=not args.no_cors,
        )
        print("Dry run passed. Routes:")
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
            if rule.endpoint != "static":
                print(" -", rule)
        return 0

    model = couplet_runtime.load_inference_model(
        args.repo_root,
        vocab_file=args.vocab_file,
        model_dir=args.model_dir,
        num_units=args.num_units,
        layers=args.layers,
        dropout=args.dropout,
    )
    app = couplet_runtime.build_flask_app(
        model,
        censor_words=censor_words,
        max_input_length=args.max_input_length,
        enable_cors=not args.no_cors,
    )

    logging.info("Starting seq2seq-couplet service on %s:%s", args.host, args.port)
    if args.flask_dev_server:
        app.run(host=args.host, port=args.port)
    else:
        from gevent.pywsgi import WSGIServer

        WSGIServer((args.host, args.port), app).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
