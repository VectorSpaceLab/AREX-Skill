#!/usr/bin/env python3
"""Emit a minimal FastVideo serve config without starting a server."""
import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--streaming", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    config = {
        "generator": {"model_path": args.model, "engine": {"num_gpus": 1}},
        "server": {"host": args.host, "port": args.port, "output_dir": args.output_dir},
    }
    if args.streaming:
        config["streaming"] = {"stream_mode": "av_fmp4"}
    print(json.dumps(config, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
