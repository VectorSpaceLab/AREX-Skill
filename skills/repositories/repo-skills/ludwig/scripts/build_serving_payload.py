#!/usr/bin/env python3
"""Build a sample Ludwig serving payload from a config."""
import argparse
import json
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


def load_config(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    if yaml is None:
        raise RuntimeError("PyYAML is required for YAML configs")
    return yaml.safe_load(text)


def sample_value(ftype: str):
    return {
        "number": 1.0,
        "binary": True,
        "category": "example",
        "text": "example text",
        "sequence": "a b c",
        "set": "a b",
        "bag": "a b a",
        "date": "2026-01-01",
        "h3": "8928308280fffff",
        "vector": [0.1, 0.2, 0.3],
        "timeseries": [1.0, 2.0, 3.0],
        "image": "path-or-upload-field",
        "audio": "path-or-upload-field",
    }.get(ftype, None)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create sample /predict or /batch_predict JSON from Ludwig config.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--mode", choices=["predict", "batch"], default="predict")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    config = load_config(Path(args.config))
    row = {}
    for feat in config.get("input_features", []):
        name = feat.get("name") or feat.get("column")
        row[name] = sample_value(feat.get("type", ""))
    payload = row if args.mode == "predict" else [row, dict(row)]
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
