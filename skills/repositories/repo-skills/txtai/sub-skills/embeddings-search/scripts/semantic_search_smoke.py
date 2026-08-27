#!/usr/bin/env python3
"""
Self-contained txtai semantic-search smoke/template script.

This is adapted from txtai's similarity demo but removes Streamlit and avoids
model downloads by default. Run with --help for options or --run for a tiny local
external-vector dry-run. Pass --model to exercise a real txtai vector model when
network/cache access is intentionally available.
"""

import argparse
import hashlib
import json
import math
import sys
from typing import Iterable, List

CORPUS = [
    {"id": "health", "text": "US tops 5 million confirmed virus cases", "topic": "public-health"},
    {"id": "climate", "text": "Canada's last fully intact ice shelf suddenly collapsed", "topic": "climate"},
    {"id": "asia", "text": "Beijing mobilises invasion craft along coast as Taiwan tensions escalate", "topic": "geopolitics"},
    {"id": "wildlife", "text": "The National Park Service warns against sacrificing slower friends in a bear attack", "topic": "wildlife"},
    {"id": "lucky", "text": "Maine man wins one million dollars from a lottery ticket", "topic": "human-interest"},
    {"id": "spam", "text": "Make huge profits without work, earn up to one hundred thousand dollars a day", "topic": "spam"},
]

QUERIES = [
    "feel good story",
    "climate change",
    "public health story",
    "war",
    "wildlife",
    "asia",
    "lucky",
    "dishonest junk",
]

FEATURE_GROUPS = [
    ("public-health", ["health", "virus", "cases", "public"]),
    ("climate", ["climate", "ice", "shelf", "collapsed", "change"]),
    ("geopolitics", ["war", "asia", "taiwan", "beijing", "invasion", "coast"]),
    ("wildlife", ["wildlife", "bear", "park", "animal", "friends"]),
    ("human-interest", ["lucky", "lottery", "win", "wins", "million", "good", "story"]),
    ("spam", ["dishonest", "junk", "spam", "profit", "profits", "work", "earn"]),
]


def numpy_module():
    """Imports numpy only for --run so --help/template modes stay dependency-safe."""

    try:
        import numpy as np
    except ImportError as exc:
        raise SystemExit("--run requires numpy from the txtai runtime environment") from exc

    return np


def hashed_features(text: str, dimensions: int = 24):
    """Returns a deterministic tiny vector for offline smoke tests."""

    np = numpy_module()
    text = str(text).lower()
    vector = np.zeros(dimensions, dtype=np.float32)

    for index, (_, keywords) in enumerate(FEATURE_GROUPS):
        matches = sum(1 for keyword in keywords if keyword in text)
        if matches:
            vector[index] += 3.0 * matches

    hash_offset = len(FEATURE_GROUPS)
    for token in text.split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        vector[hash_offset + (digest[0] % (dimensions - hash_offset))] += 0.05 + (digest[1] / 2048.0)

    norm = math.sqrt(float(np.dot(vector, vector)))
    return vector / norm if norm else vector


def transform(values: Iterable[object]) -> List[object]:
    """txtai external transform hook for data and query values."""

    return [hashed_features(value.get("text", "") if isinstance(value, dict) else value) for value in values]


def build_embeddings(args):
    """Creates a txtai Embeddings instance for either offline or model-backed runs."""

    try:
        from txtai import Embeddings
    except ImportError as exc:
        raise SystemExit("--run requires txtai in the active Python environment") from exc

    if args.model:
        config = {"path": args.model, "content": args.sql}
    else:
        config = {"method": "external", "transform": transform, "content": args.sql}

    if args.hybrid:
        config["hybrid"] = True

    return Embeddings(config)


def rows(args):
    """Returns corpus rows in the selected txtai indexing format."""

    if args.sql:
        return [(item["id"], {"text": item["text"], "topic": item["topic"]}, None) for item in CORPUS]

    return [(item["id"], item["text"], None) for item in CORPUS]


def run(args):
    """Builds a tiny index and runs semantic or SQL searches."""

    embeddings = build_embeddings(args)

    try:
        embeddings.index(rows(args))
        output = []

        if args.sql:
            sql = f"""
                    select id, text, topic, score
                    from txtai
                    where similar(:query, 10)
                    order by score desc
                    limit {args.limit}
                    """
            for query in args.query or QUERIES:
                results = embeddings.search(sql, parameters={"query": query})
                output.append({"query": query, "results": results})
        else:
            lookup = {item["id"]: item for item in CORPUS}
            for query in args.query or QUERIES:
                matches = embeddings.search(query, args.limit)
                output.append(
                    {
                        "query": query,
                        "results": [
                            {"id": uid, "score": float(score), "text": lookup[uid]["text"]}
                            for uid, score in matches
                        ],
                    }
                )

        print(json.dumps(output, indent=2, default=str))
    finally:
        embeddings.close()


def print_template(args):
    """Prints a copyable template instead of importing txtai or building an index."""

    mode = "content=True SQL/dict results" if args.sql else "tuple-only vector results"
    print(f"txtai semantic-search template ({mode})")
    print()
    print("from txtai import Embeddings")
    print()
    if args.sql:
        print("embeddings = Embeddings(content=True)")
        print("rows = [('doc-1', {'text': 'example text', 'topic': 'demo'}, None)]")
        print("embeddings.index(rows)")
        print("results = embeddings.search(")
        print("    'select id, text, score from txtai where similar(:q, 25) and topic = :topic',")
        print("    parameters={'q': 'example', 'topic': 'demo'},")
        print(")")
    else:
        print("embeddings = Embeddings()")
        print("embeddings.index(['Correct', 'Not what we hoped'])")
        print("results = embeddings.search('positive', 1)  # [(id, score)]")
    print("print(results)")


def parse(argv):
    parser = argparse.ArgumentParser(
        description="Safe txtai semantic-search smoke/template helper. Defaults to printing a template; --run executes a tiny local corpus.",
    )
    parser.add_argument("--run", action="store_true", help="Build a tiny index and execute searches. Without --model, uses a no-download external transform.")
    parser.add_argument("--sql", action="store_true", help="Enable content=True and run SQL similar(...) queries returning dictionaries.")
    parser.add_argument("--hybrid", action="store_true", help="Add hybrid=True to the config. This may require sparse/scoring dependencies and/or model access.")
    parser.add_argument("--model", help="Optional real vector model path. May require local cache or network download access.")
    parser.add_argument("--query", action="append", help="Query to run. Can be repeated. Defaults to a small built-in query set.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum results per query. Defaults to 1.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse(argv or sys.argv[1:])

    if args.limit < 1:
        raise SystemExit("--limit must be >= 1")

    if args.hybrid and not args.model:
        print("warning: --hybrid with the no-download external transform is only a config-shape check", file=sys.stderr)

    if args.run:
        run(args)
    else:
        print_template(args)


if __name__ == "__main__":
    main()
