#!/usr/bin/env python3
"""Safe lightweight ColBERT JSON search API.

Adapt this template for small read-only serving tasks. It avoids ColBERT and
Flask imports until after CLI/env configuration is parsed, and it constructs the
Searcher lazily instead of at module import time.
"""

from __future__ import annotations

import argparse
import math
import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any


MAX_K = 100


def nonempty(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("value must not be empty")
    return value


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("value must be an integer") from exc
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def existing_file(value: str) -> str:
    path = Path(value).expanduser()
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file does not exist: {path}")
    return str(path)


def env_default(name: str) -> str | None:
    value = os.getenv(name)
    return value if value else None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve a ColBERT index over a small JSON search API.")
    parser.add_argument("--index-name", default=env_default("INDEX_NAME"), help="index name; env fallback INDEX_NAME")
    parser.add_argument("--index-root", default=env_default("INDEX_ROOT"), help="optional index root; env fallback INDEX_ROOT")
    parser.add_argument("--root", default=env_default("COLBERT_ROOT"), help="optional ColBERT experiment root; env fallback COLBERT_ROOT")
    parser.add_argument("--experiment", default=env_default("COLBERT_EXPERIMENT") or "default", help="ColBERT experiment namespace")
    parser.add_argument("--checkpoint", default=env_default("COLBERT_CHECKPOINT"), help="optional checkpoint/model; env fallback COLBERT_CHECKPOINT")
    parser.add_argument("--collection", type=existing_file, default=env_default("COLBERT_COLLECTION"), help="optional collection TSV; env fallback COLBERT_COLLECTION")
    parser.add_argument("--host", default=env_default("HOST") or "0.0.0.0", help="bind host")
    parser.add_argument("--port", type=positive_int, default=int(env_default("PORT") or "8893"), help="bind port; env fallback PORT")
    parser.add_argument("--debug", action="store_true", help="enable Flask debug mode")
    return parser


def stable_probabilities(scores: list[float]) -> list[float]:
    if not scores:
        return []
    max_score = max(scores)
    weights = [math.exp(score - max_score) for score in scores]
    total = sum(weights)
    if total == 0:
        return [0.0 for _ in weights]
    return [weight / total for weight in weights]


def create_app(config: dict[str, Any]):
    try:
        from flask import Flask, jsonify, request
    except Exception as exc:  # pragma: no cover - depends on runtime env
        raise RuntimeError("Flask is required to serve the search API") from exc

    app = Flask(__name__)
    state: dict[str, Any] = {"searcher": None, "error": None}
    lock = threading.Lock()

    def missing_config() -> list[str]:
        missing = []
        if not config.get("index_name"):
            missing.append("index_name")
        return missing

    def load_searcher():
        missing = missing_config()
        if missing:
            raise RuntimeError("missing required configuration: " + ", ".join(missing))

        with lock:
            if state["searcher"] is not None:
                return state["searcher"]
            if state["error"] is not None:
                raise RuntimeError(state["error"])
            try:
                from colbert import Searcher
                from colbert.infra import ColBERTConfig

                colbert_config = None
                if config.get("root"):
                    colbert_config = ColBERTConfig(root=config["root"], experiment=config.get("experiment") or "default")
                state["searcher"] = Searcher(
                    index=config["index_name"],
                    checkpoint=config.get("checkpoint"),
                    collection=config.get("collection"),
                    config=colbert_config,
                    index_root=config.get("index_root"),
                )
                return state["searcher"]
            except Exception as exc:  # pragma: no cover - depends on index/backend
                state["error"] = str(exc)
                raise

    @lru_cache(maxsize=100000)
    def cached_search(query: str, k: int) -> dict[str, Any]:
        searcher = load_searcher()
        search_k = min(k, MAX_K)
        pids, ranks, scores = searcher.search(query, k=search_k)
        float_scores = [float(score) for score in scores]
        probabilities = stable_probabilities(float_scores)
        topk = []
        for pid, rank, score, probability in zip(pids, ranks, float_scores, probabilities):
            text = ""
            if getattr(searcher, "collection", None) is not None:
                try:
                    text = searcher.collection[pid]
                except Exception:
                    text = ""
            topk.append({"text": text, "pid": int(pid), "rank": int(rank), "score": score, "prob": probability})
        topk.sort(key=lambda row: (-row["score"], row["pid"]))
        return {"query": query, "topk": topk}

    @app.get("/healthz")
    def healthz():
        missing = missing_config()
        return jsonify({"ok": not missing, "configured": not missing, "searcher_loaded": state["searcher"] is not None, "error": state["error"]})

    @app.get("/api/search")
    def api_search():
        query = request.args.get("query", "").strip()
        if not query:
            return jsonify({"error": "missing required query parameter: query"}), 400
        raw_k = request.args.get("k", "10")
        try:
            k = int(raw_k)
        except ValueError:
            return jsonify({"error": "k must be an integer"}), 400
        if k < 1:
            return jsonify({"error": "k must be positive"}), 400
        k = min(k, MAX_K)
        try:
            return jsonify(cached_search(query, k))
        except RuntimeError as exc:
            return jsonify({"error": str(exc)}), 503
        except Exception as exc:  # pragma: no cover - depends on runtime backend
            return jsonify({"error": f"search failed: {exc}"}), 500

    return app


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = {
        "index_name": args.index_name,
        "index_root": args.index_root,
        "root": args.root,
        "experiment": args.experiment,
        "checkpoint": args.checkpoint,
        "collection": args.collection,
    }
    app = create_app(config)
    app.run(args.host, args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
