#!/usr/bin/env python3
"""Print the bundled Generative Models catalog.

This helper reads references/model-catalog.json from the generated skill tree.
It does not import or execute the original repository scripts.

Examples:
  python scripts/model_catalog.py --list-families
  python scripts/model_catalog.py --family gan
  python scripts/model_catalog.py --model wgan-gp
  python scripts/model_catalog.py --json --family vae
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def catalog_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "model-catalog.json"


def load_catalog() -> Dict[str, Any]:
    path = catalog_path()
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_items(catalog: Dict[str, Any]) -> Iterable[tuple[str, Dict[str, Any]]]:
    for family_id, family in catalog.get("families", {}).items():
        for item in family.get("items", []):
            yield family_id, item


def print_family(catalog: Dict[str, Any], family_id: str) -> None:
    families = catalog.get("families", {})
    if family_id not in families:
        raise SystemExit(f"Unknown family: {family_id}. Known: {', '.join(sorted(families))}")
    family = families[family_id]
    print(f"{family_id}: {family.get('title', family_id)}")
    print(f"owner: {family.get('owner_sub_skill')}")
    for item in family.get("items", []):
        print(f"\n- {item['id']}: {item['title']}")
        print(f"  hint: {item.get('selection_hint', '')}")
        for artifact in item.get("source_artifacts", []):
            print(f"  {artifact.get('framework', 'unknown')}: {artifact.get('path')}")


def print_model(catalog: Dict[str, Any], model_id: str) -> None:
    matches: List[tuple[str, Dict[str, Any]]] = []
    needle = model_id.lower().replace("_", "-")
    for family_id, item in iter_items(catalog):
        hay = {item.get("id", "").lower(), item.get("title", "").lower().replace(" ", "-")}
        if needle in hay or needle in item.get("title", "").lower() or needle in item.get("id", "").lower():
            matches.append((family_id, item))
    if not matches:
        raise SystemExit(f"No catalog model matched: {model_id}")
    for family_id, item in matches:
        print(f"{item['id']} ({item['title']})")
        print(f"family: {family_id}")
        print(f"hint: {item.get('selection_hint', '')}")
        for artifact in item.get("source_artifacts", []):
            print(f"{artifact.get('framework', 'unknown')}: {artifact.get('path')}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Print the bundled Generative Models script catalog.")
    parser.add_argument("--list-families", action="store_true", help="List known family ids.")
    parser.add_argument("--family", help="Print one family, e.g. gan, vae, rbm, helmholtz-machine.")
    parser.add_argument("--model", help="Print one model by id or title fragment, e.g. wgan-gp.")
    parser.add_argument("--json", action="store_true", help="Emit matching catalog data as JSON.")
    args = parser.parse_args()

    catalog = load_catalog()

    if args.json:
        data: Any = catalog
        if args.family:
            data = catalog.get("families", {}).get(args.family)
            if data is None:
                raise SystemExit(f"Unknown family: {args.family}")
        elif args.model:
            data = [{"family": fam, "item": item} for fam, item in iter_items(catalog)
                    if args.model.lower().replace("_", "-") in item.get("id", "").lower()
                    or args.model.lower() in item.get("title", "").lower()]
        print(json.dumps(data, indent=2))
        return 0

    if args.list_families:
        for family_id, family in sorted(catalog.get("families", {}).items()):
            print(f"{family_id}\t{family.get('title', '')}\t{family.get('owner_sub_skill', '')}")
        return 0
    if args.family:
        print_family(catalog, args.family)
        return 0
    if args.model:
        print_model(catalog, args.model)
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
