#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a tiny mock/private dataset fixture and analysis.py")
    parser.add_argument("--out", required=True)
    parser.add_argument("--name", default="census")
    args = parser.parse_args()
    out = Path(args.out)
    mock = out / "mock"
    private = out / "private"
    mock.mkdir(parents=True, exist_ok=True)
    private.mkdir(parents=True, exist_ok=True)
    (mock / "data.csv").write_text("id,value\n1,MOCK\n")
    (private / "data.csv").write_text("id,value\n1,PRIVATE\n")
    (out / "analysis.py").write_text(
        "import json\nimport syft_client as sc\n"
        f"path = sc.resolve_dataset_file_path({args.name!r})\n"
        "text = path.read_text()\n"
        "with open('result.json', 'w') as f:\n    json.dump({'length': len(text)}, f)\n"
    )
    print(json.dumps({"mock_path": str(mock), "private_path": str(private), "analysis": str(out / "analysis.py")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
