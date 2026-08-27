#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a safe PySyft Python job template")
    parser.add_argument("--out", required=True)
    parser.add_argument("--folder", action="store_true")
    parser.add_argument("--dataset")
    parser.add_argument("--params", action="store_true")
    args = parser.parse_args()
    out = Path(args.out)
    root = out / "job_code" if args.folder else out
    root.mkdir(parents=True, exist_ok=True)
    code = "import json\n"
    if args.dataset:
        code += "import syft_client as sc\n"
        code += f"path = sc.resolve_dataset_file_path({args.dataset!r})\n"
        code += "text = path.read_text()\n"
    else:
        code += "text = 'hello'\n"
    code += "with open('result.json', 'w') as f:\n    json.dump({'length': len(text)}, f)\n"
    (root / "main.py").write_text(code)
    if args.params:
        (root / "params.json").write_text(json.dumps({"example": True}, indent=2) + "\n")
    print(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
