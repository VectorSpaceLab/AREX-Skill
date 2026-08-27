#!/usr/bin/env python3
"""Safe legacy-extension rule/API smoke check.

By default this script does not load model files. Pass --cws-model and --load
only when a local legacy CWS model binary is available and loading is desired.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check legacy extension imports, CharacterType, and optional CWS model rule setup.")
    parser.add_argument("--no-model", action="store_true", help="force import/rule checks only")
    parser.add_argument("--cws-model", help="optional local CWS model file")
    parser.add_argument("--load", action="store_true", help="actually load --cws-model and apply a couple of rules")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = {"imports": False, "character_types": [], "stn_split": None, "loaded_model": False, "errors": []}
    try:
        from ltp import StnSplit
        from ltp_extension.algorithms import get_entities
        from ltp_extension.perceptron import CWSModel, CharacterType

        result["imports"] = True
        result["character_types"] = [name for name in dir(CharacterType) if not name.startswith("_")]
        result["stn_split"] = StnSplit().split("汤姆生病了。他去了医院。")
        result["entities"] = get_entities(["B-Nh", "I-Nh", "O", "S-Ns"])
        if args.cws_model:
            path = Path(args.cws_model)
            if not path.is_file():
                result["errors"].append(f"CWS model file not found: {path}")
            elif args.load and not args.no_model:
                model = CWSModel.load(str(path))
                model.enable_type_cut_d(CharacterType.Roman, CharacterType.Kanji)
                model.enable_type_concat(CharacterType.Digit, CharacterType.Roman)
                result["loaded_model"] = True
    except Exception as exc:  # pragma: no cover
        result["errors"].append(f"legacy smoke failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"imports: {result['imports']}")
        print(f"character_types: {result['character_types']}")
        print(f"stn_split: {result['stn_split']}")
        print(f"loaded_model: {result['loaded_model']}")
        if result["errors"]:
            print("errors:")
            for err in result["errors"]:
                print(f"- {err}")
    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
