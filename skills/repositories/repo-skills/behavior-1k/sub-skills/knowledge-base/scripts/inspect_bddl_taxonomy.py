#!/usr/bin/env python3
"""Safely inspect BDDL's packaged taxonomy and optional in-memory KB.

This command is read-only. It does not write files, access the network, enable
WordNet downloads, launch a simulator, or invoke BDDL data generation.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Callable


class QueryError(ValueError):
    """Raised when a requested taxonomy query cannot be completed safely."""


def non_negative_int(value: str) -> int:
    """Parse a non-negative integer for argparse."""
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be non-negative")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect packaged BDDL taxonomy data and, optionally, summarize an "
            "empty or populated in-memory KnowledgeBase."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--hierarchy-type",
        default="default",
        metavar="NAME",
        help=(
            "compatibility value passed to ObjectTaxonomy; BDDL 3.7.0 reads "
            "the packaged default hierarchy regardless of this value"
        ),
    )

    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--synset", metavar="SYNSET", help="query an exact taxonomy synset")
    selector.add_argument("--category", metavar="CATEGORY", help="resolve and query an exact category")
    selector.add_argument("--substance", metavar="SUBSTANCE", help="resolve and query an exact substance")
    selector.add_argument("--list-synsets", action="store_true", help="list synset names in topological order")
    selector.add_argument("--list-categories", action="store_true", help="list category-to-synset mappings")
    selector.add_argument("--list-substances", action="store_true", help="list substance-to-synset mappings")

    queries = parser.add_argument_group("target queries")
    queries.add_argument("--parents", action="store_true", help="show immediate parent synsets")
    queries.add_argument("--children", action="store_true", help="show immediate child synsets")
    queries.add_argument("--ancestors", action="store_true", help="show all ancestor synsets")
    queries.add_argument("--descendants", action="store_true", help="show all descendant synsets")
    queries.add_argument("--leaf-descendants", action="store_true", help="show descendant synsets that are leaves")
    queries.add_argument("--abilities", action="store_true", help="show the target ability mapping")
    queries.add_argument("--categories", action="store_true", help="show categories attached directly to the target")
    queries.add_argument("--substances", action="store_true", help="show substances attached directly to the target")
    queries.add_argument("--subtree-categories", action="store_true", help="show categories aggregated over leaf descendants")
    queries.add_argument("--subtree-substances", action="store_true", help="show substances aggregated over leaf descendants")
    queries.add_argument(
        "--leaf",
        "--is-leaf",
        dest="leaf",
        action="store_true",
        help="report whether the target is a leaf (alias: --is-leaf)",
    )
    queries.add_argument(
        "--required-meta-links",
        action="store_true",
        help="show metadata links required by the target abilities",
    )
    queries.add_argument("--has-ability", metavar="ABILITY", help="report whether the target has ABILITY")
    queries.add_argument(
        "--is-descendant-of",
        metavar="ANCESTOR",
        help="report whether the target is a descendant of ANCESTOR",
    )
    queries.add_argument(
        "--is-ancestor-of",
        metavar="DESCENDANT",
        help="report whether the target is an ancestor of DESCENDANT",
    )

    parser.add_argument(
        "--knowledge-base",
        choices=("none", "empty", "populated"),
        default="none",
        help=(
            "also summarize an in-memory KnowledgeBase; populated reads "
            "packaged records once with WordNet disabled"
        ),
    )
    parser.add_argument(
        "--limit",
        type=non_negative_int,
        default=0,
        metavar="N",
        help="limit a list mode; zero emits every entry",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of line-oriented text")
    return parser


def _load_taxonomy(parser: argparse.ArgumentParser, hierarchy_type: str):
    try:
        from bddl.object_taxonomy import ObjectTaxonomy

        return ObjectTaxonomy(hierarchy_type=hierarchy_type)
    except ModuleNotFoundError as exc:
        dependency = exc.name or "unknown dependency"
        parser.error(
            f"could not import BDDL taxonomy dependency {dependency!r}; "
            "install BDDL 3.7.0 and its declared dependencies"
        )
    except FileNotFoundError:
        parser.error(
            "packaged BDDL taxonomy data is missing; install a complete BDDL "
            "3.7.0 distribution containing generated runtime data"
        )
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        parser.error(
            "packaged BDDL taxonomy data could not be parsed "
            f"({type(exc).__name__}); reinstall a complete, matching distribution"
        )


def _resolve_target(args: argparse.Namespace, taxonomy) -> tuple[str | None, dict[str, str]]:
    if args.synset is not None:
        if not taxonomy.is_valid_synset(args.synset):
            raise QueryError(
                f"unknown taxonomy synset {args.synset!r}; check spelling or use "
                "--list-synsets --limit 20"
            )
        return args.synset, {"kind": "synset", "name": args.synset, "synset": args.synset}

    resolvers: list[tuple[str, str | None, Callable[[str], str | None], str]] = [
        ("category", args.category, taxonomy.get_synset_from_category, "--list-categories"),
        ("substance", args.substance, taxonomy.get_synset_from_substance, "--list-substances"),
    ]
    for kind, value, resolver, list_flag in resolvers:
        if value is None:
            continue
        try:
            synset = resolver(value)
        except ValueError as exc:
            raise QueryError(
                f"{kind} {value!r} is ambiguous: {exc}; query an exact synset with --synset"
            ) from exc
        if synset is None:
            raise QueryError(
                f"unknown taxonomy {kind} {value!r}; check spelling or use {list_flag} --limit 20"
            )
        return synset, {"kind": kind, "name": value, "synset": synset}

    return None, {}


def _query_requested(args: argparse.Namespace) -> bool:
    return any(
        (
            args.parents,
            args.children,
            args.ancestors,
            args.descendants,
            args.leaf_descendants,
            args.abilities,
            args.categories,
            args.substances,
            args.subtree_categories,
            args.subtree_substances,
            args.leaf,
            args.required_meta_links,
            args.has_ability is not None,
            args.is_descendant_of is not None,
            args.is_ancestor_of is not None,
        )
    )


def _require_valid_comparison(taxonomy, name: str, option: str) -> None:
    if not taxonomy.is_valid_synset(name):
        raise QueryError(
            f"unknown comparison synset {name!r} for {option}; check spelling or use "
            "--list-synsets --limit 20"
        )


def _query_target(args: argparse.Namespace, taxonomy, target: str) -> dict[str, Any]:
    result: dict[str, Any] = {}

    # A selector without query flags returns a compact, useful target summary.
    if not _query_requested(args):
        return {
            "parents": sorted(taxonomy.get_parents(target)),
            "children": sorted(taxonomy.get_children(target)),
            "abilities": taxonomy.get_abilities(target),
            "categories": sorted(taxonomy.get_categories(target)),
            "substances": sorted(taxonomy.get_substances(target)),
            "leaf": taxonomy.is_leaf(target),
            "required_meta_links": sorted(taxonomy.get_required_meta_links_for_synset(target)),
        }

    if args.parents:
        result["parents"] = sorted(taxonomy.get_parents(target))
    if args.children:
        result["children"] = sorted(taxonomy.get_children(target))
    if args.ancestors:
        result["ancestors"] = sorted(taxonomy.get_ancestors(target))
    if args.descendants:
        result["descendants"] = sorted(taxonomy.get_descendants(target))
    if args.leaf_descendants:
        result["leaf_descendants"] = sorted(taxonomy.get_leaf_descendants(target))
    if args.abilities:
        result["abilities"] = taxonomy.get_abilities(target)
    if args.categories:
        result["categories"] = sorted(taxonomy.get_categories(target))
    if args.substances:
        result["substances"] = sorted(taxonomy.get_substances(target))
    if args.subtree_categories:
        result["subtree_categories"] = sorted(taxonomy.get_subtree_categories(target))
    if args.subtree_substances:
        result["subtree_substances"] = sorted(taxonomy.get_subtree_substances(target))
    if args.leaf:
        result["leaf"] = taxonomy.is_leaf(target)
    if args.required_meta_links:
        result["required_meta_links"] = sorted(taxonomy.get_required_meta_links_for_synset(target))
    if args.has_ability is not None:
        result["has_ability"] = {
            "name": args.has_ability,
            "value": taxonomy.has_ability(target, args.has_ability),
        }
    if args.is_descendant_of is not None:
        _require_valid_comparison(taxonomy, args.is_descendant_of, "--is-descendant-of")
        result["is_descendant_of"] = {
            "synset": args.is_descendant_of,
            "value": taxonomy.is_descendant(target, args.is_descendant_of),
        }
    if args.is_ancestor_of is not None:
        _require_valid_comparison(taxonomy, args.is_ancestor_of, "--is-ancestor-of")
        result["is_ancestor_of"] = {
            "synset": args.is_ancestor_of,
            "value": taxonomy.is_ancestor(target, args.is_ancestor_of),
        }
    return result


def _list_entries(args: argparse.Namespace, taxonomy) -> tuple[str, list[Any]]:
    synsets = taxonomy.get_all_synsets()
    if args.list_synsets:
        return "synsets", synsets
    if args.list_categories:
        entries = [
            {"category": category, "synset": synset}
            for synset in synsets
            for category in taxonomy.get_categories(synset)
        ]
        return "categories", sorted(entries, key=lambda item: (item["category"], item["synset"]))
    if args.list_substances:
        entries = [
            {"substance": substance, "synset": synset}
            for synset in synsets
            for substance in taxonomy.get_substances(synset)
        ]
        return "substances", sorted(entries, key=lambda item: (item["substance"], item["synset"]))
    raise QueryError("no taxonomy selector was provided")


def _kb_summary(parser: argparse.ArgumentParser, mode: str) -> dict[str, Any] | None:
    if mode == "none":
        return None
    try:
        from bddl.knowledge_base import KnowledgeBase

        kb = KnowledgeBase(populate=(mode == "populated"), verbose=False, load_wordnet=False)
        return {
            "mode": mode,
            "synsets": len(kb.all_synsets()),
            "categories": len(kb.all_categories()),
            "particle_systems": len(kb.all_particle_systems()),
            "objects": len(kb.all_objects()),
            "scenes": len(kb.all_scenes()),
            "tasks": len(kb.all_tasks()),
            "transition_rules": len(kb.all_transition_rules()),
        }
    except ModuleNotFoundError as exc:
        dependency = exc.name or "unknown dependency"
        parser.error(
            f"could not import KnowledgeBase dependency {dependency!r}; install "
            "BDDL 3.7.0 and its declared dependencies"
        )
    except FileNotFoundError:
        parser.error(
            "KnowledgeBase generated runtime data is missing; install a complete "
            "BDDL 3.7.0 distribution or retry with --knowledge-base empty"
        )
    except Exception as exc:
        hint = (
            "retry with --knowledge-base empty to distinguish container import "
            "from generated-data population"
            if mode == "populated"
            else "verify the BDDL 3.7.0 installation and declared dependencies"
        )
        parser.error(
            f"could not construct the requested in-memory KnowledgeBase "
            f"({type(exc).__name__}); {hint}"
        )


def _normalize(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(_normalize(item) for item in value)
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    return value


def render(result: dict[str, Any], as_json: bool) -> None:
    result = _normalize(result)
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    for key, value in result.items():
        if isinstance(value, (dict, list)):
            print(f"{key}: {json.dumps(value, sort_keys=True)}")
        else:
            print(f"{key}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    list_mode = args.list_synsets or args.list_categories or args.list_substances
    if list_mode and _query_requested(args):
        parser.error("target query flags cannot be combined with a list mode")
    if not list_mode and args.limit:
        parser.error("--limit is only valid with a list mode")

    taxonomy = _load_taxonomy(parser, args.hierarchy_type)
    try:
        target, target_info = _resolve_target(args, taxonomy)
        result: dict[str, Any] = {
            "hierarchy_type": args.hierarchy_type,
            "taxonomy_synset_count": len(taxonomy.get_all_synsets()),
        }
        if args.hierarchy_type != "default":
            result["hierarchy_note"] = (
                "BDDL 3.7.0 accepts this compatibility value but reads the "
                "packaged default hierarchy."
            )

        if list_mode:
            key, entries = _list_entries(args, taxonomy)
            result[f"{key}_total"] = len(entries)
            result[key] = entries[: args.limit or None]
        else:
            if target is None:
                raise QueryError("a synset, category, substance, or list mode is required")
            result["target"] = target_info
            result["query"] = _query_target(args, taxonomy, target)

        kb = _kb_summary(parser, args.knowledge_base)
        if kb is not None:
            result["knowledge_base"] = kb
        render(result, args.json)
        return 0
    except (AssertionError, QueryError, ValueError) as exc:
        parser.error(str(exc))

    return 2


if __name__ == "__main__":
    sys.exit(main())
