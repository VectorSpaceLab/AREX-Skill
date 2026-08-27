#!/usr/bin/env python3
"""Validate PocketFlow checkpoint/export artifacts without running conversion."""

import argparse
import json
from pathlib import Path


def find_checkpoint_like(model_dir):
    files = [p.name for p in model_dir.iterdir() if p.is_file()]
    return {
        "meta": sorted([f for f in files if f.endswith(".meta")]),
        "index": sorted([f for f in files if f.endswith(".index")]),
        "data": sorted([f for f in files if ".data-" in f]),
        "checkpoint_state": sorted([f for f in files if f == "checkpoint"]),
        "pb": sorted([f for f in files if f.endswith(".pb")]),
        "tflite": sorted([f for f in files if f.endswith(".tflite")]),
    }


def inspect_meta(model_dir, meta_name, input_coll, output_coll):
    try:
        import tensorflow as tf  # type: ignore
    except Exception as exc:
        return {"status": "tf-import-failed", "error": str(exc)}
    meta_path = str(model_dir / meta_name)
    try:
        with tf.Graph().as_default():
            tf.train.import_meta_graph(meta_path)
            inputs = [getattr(t, "name", str(t)) for t in tf.get_collection(input_coll)]
            outputs = [getattr(t, "name", str(t)) for t in tf.get_collection(output_coll)]
        return {"status": "ok", "input_collection": inputs, "output_collection": outputs}
    except Exception as exc:
        return {"status": "meta-inspect-failed", "error": str(exc)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", required=True, type=Path)
    parser.add_argument("--input-coll", default="images_final")
    parser.add_argument("--output-coll", default="logits_final")
    parser.add_argument("--inspect-meta", action="store_true", help="Attempt TensorFlow import_meta_graph inspection")
    args = parser.parse_args(argv)

    if not args.model_dir.exists() or not args.model_dir.is_dir():
        raise SystemExit("model dir not found: {}".format(args.model_dir))
    found = find_checkpoint_like(args.model_dir)
    result = {"model_dir": str(args.model_dir), "files": found, "warnings": []}
    warnings = result["warnings"]
    if not found["meta"]:
        warnings.append("no .meta graph file found")
    if not found["index"] and not found["data"] and not found["checkpoint_state"]:
        warnings.append("no checkpoint index/data/state files found")
    if args.inspect_meta and found["meta"]:
        preferred = "model.ckpt.meta" if "model.ckpt.meta" in found["meta"] else found["meta"][0]
        result["meta_inspection"] = inspect_meta(args.model_dir, preferred, args.input_coll, args.output_coll)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not warnings else 2


if __name__ == "__main__":
    raise SystemExit(main())
