#!/usr/bin/env python3
"""Read-only inspection of packaged BDDL activities.

Prerequisite:
    python -m pip install "bddl==3.7.0"

Examples:
    python inspect_bddl_activity.py
    python inspect_bddl_activity.py --activity some_activity --instance 0
    python inspect_bddl_activity.py --activity some_activity --natural-language
    python inspect_bddl_activity.py --activity some_activity --tokens

The script performs no writes, network calls, downloads, or simulator imports.
It emits JSON to standard output and concise classified errors to standard
error.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from importlib import metadata
from typing import Any, Sequence


class InspectionError(Exception):
    """Base class for expected inspection failures."""

    exit_code = 1
    label = "inspection error"


class ImportPrerequisiteError(InspectionError):
    exit_code = 2
    label = "import prerequisite error"


class ActivityLookupError(InspectionError):
    exit_code = 3
    label = "activity lookup error"


class PackageDataError(InspectionError):
    exit_code = 4
    label = "package data error"


class DefinitionParseError(InspectionError):
    exit_code = 5
    label = "BDDL syntax/parse error"


def nonnegative_int(value: str) -> int:
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
            "Inspect packaged BDDL activities without writes, network access, "
            "simulator imports, or GPU dependencies. Omit --activity to list "
            "available activity ids."
        )
    )
    parser.add_argument(
        "--activity",
        help="exact packaged activity id; omit to list all ids",
    )
    parser.add_argument(
        "--instance",
        type=nonnegative_int,
        default=0,
        help="zero-based problem instance (default: 0)",
    )
    parser.add_argument(
        "--domain",
        default="behavior-1k",
        help="packaged BDDL domain name (default: behavior-1k)",
    )
    parser.add_argument(
        "--natural-language",
        action="store_true",
        help="add natural-language initial and goal condition lists",
    )
    parser.add_argument(
        "--tokens",
        action="store_true",
        help="add the raw nested token tree for the selected problem",
    )
    return parser


def load_bddl_modules():
    """Import only the CPU BDDL modules needed by this helper."""
    try:
        from bddl import activity, config, parsing
    except ModuleNotFoundError as exc:
        missing = exc.name or "an unknown dependency"
        if missing == "bddl":
            message = (
                "the 'bddl' package is not importable; install it with "
                "`python -m pip install \"bddl==3.7.0\"` using this interpreter"
            )
        else:
            message = (
                f"BDDL import is incomplete because module {missing!r} is missing; "
                "run `python -m pip check` and reinstall the bddl distribution"
            )
        raise ImportPrerequisiteError(message) from exc
    except ImportError as exc:
        raise ImportPrerequisiteError(
            "the bddl package was found but its symbolic modules did not import; "
            "run `python -m pip check` and reinstall the bddl distribution"
        ) from exc
    return activity, config, parsing


def distribution_version() -> str | None:
    try:
        return metadata.version("bddl")
    except metadata.PackageNotFoundError:
        return None


def safe_exception_detail(exc: BaseException) -> str:
    """Return a useful error detail without emitting machine-specific paths."""
    detail = str(exc).strip()
    if not detail:
        return type(exc).__name__
    if "/" in detail or "\\" in detail:
        return type(exc).__name__
    return detail


def list_activities(activity_module: Any) -> list[str]:
    try:
        return sorted(activity_module.get_all_activities())
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        raise PackageDataError(
            "the installed bddl package does not expose readable activity definitions"
        ) from exc


def inspect_activity(args: argparse.Namespace) -> dict[str, Any]:
    activity_module, config_module, parsing_module = load_bddl_modules()
    activities = list_activities(activity_module)

    if args.activity is None:
        return {
            "distribution": {"name": "bddl", "version": distribution_version()},
            "activity_count": len(activities),
            "activities": activities,
        }

    if args.activity not in activities:
        suggestions = difflib.get_close_matches(
            args.activity, activities, n=3, cutoff=0.6
        )
        suffix = f"; close matches: {', '.join(suggestions)}" if suggestions else ""
        raise ActivityLookupError(
            f"activity {args.activity!r} is not packaged{suffix}; omit --activity to list exact ids"
        )

    try:
        instance_count = activity_module.get_instance_count(args.activity)
    except AssertionError as exc:
        raise PackageDataError(
            f"activity {args.activity!r} has non-contiguous packaged instance ids"
        ) from exc
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        raise PackageDataError(
            f"activity {args.activity!r} was discovered but its definition directory is unreadable"
        ) from exc

    if args.instance >= instance_count:
        available = f"0..{instance_count - 1}" if instance_count else "none"
        raise ActivityLookupError(
            f"instance {args.instance} is not packaged for activity {args.activity!r}; "
            f"available instances: {available}"
        )

    domain_filename = config_module.get_domain_filename(args.domain)
    definition_filename = config_module.get_definition_filename(
        args.activity, args.instance
    )

    try:
        (
            declared_domain,
            requirements,
            types,
            actions,
            predicates,
        ) = parsing_module.parse_domain(args.domain)
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        raise PackageDataError(
            f"packaged domain {args.domain!r} is missing or unreadable"
        ) from exc
    except Exception as exc:
        raise DefinitionParseError(
            f"domain {args.domain!r} could not be parsed: {safe_exception_detail(exc)}"
        ) from exc

    try:
        conds = activity_module.Conditions(
            args.activity,
            args.instance,
            args.domain,
        )
        problem_name, objects, initial_state, goal_state = parsing_module.parse_problem(
            args.activity,
            args.instance,
            declared_domain,
        )
        scope = activity_module.get_object_scope(conds)
    except (FileNotFoundError, NotADirectoryError, OSError) as exc:
        raise PackageDataError(
            f"the packaged definition for {args.activity!r} instance {args.instance} "
            "is missing or unreadable"
        ) from exc
    except Exception as exc:
        raise DefinitionParseError(
            f"activity {args.activity!r} instance {args.instance} could not be parsed: "
            f"{safe_exception_detail(exc)}"
        ) from exc

    result: dict[str, Any] = {
        "distribution": {"name": "bddl", "version": distribution_version()},
        "selection": {
            "activity": args.activity,
            "instance": args.instance,
            "instance_count": instance_count,
            "domain_requested": args.domain,
            "domain_declared": declared_domain,
            "problem_name": problem_name,
        },
        # File paths are useful for this explicit file inspection, but are
        # intentionally omitted from no-activity list mode.
        "files": {
            "domain": domain_filename,
            "problem": definition_filename,
        },
        "domain": {
            "requirements": requirements,
            "types": types,
            "action_count": len(actions),
            "predicate_arities": {
                token: len(parameters) for token, parameters in sorted(predicates.items())
            },
        },
        "objects": objects,
        "scope": sorted(scope),
        "parsed_initial_conditions": initial_state,
        "parsed_goal_conditions": goal_state,
        "counts": {
            "object_categories": len(objects),
            "object_instances": sum(len(instances) for instances in objects.values()),
            "initial_conditions": len(initial_state),
            "goal_conditions": len(goal_state),
        },
    }

    if args.natural_language:
        try:
            result["natural_language"] = {
                "initial_conditions": (
                    activity_module.get_natural_initial_conditions(conds)
                ),
                "goal_conditions": activity_module.get_natural_goal_conditions(conds),
            }
        except Exception as exc:
            raise DefinitionParseError(
                f"natural-language rendering failed for activity {args.activity!r} "
                f"instance {args.instance}: {safe_exception_detail(exc)}"
            ) from exc

    if args.tokens:
        try:
            result["tokens"] = parsing_module.scan_tokens(filename=definition_filename)
        except (FileNotFoundError, NotADirectoryError, OSError) as exc:
            raise PackageDataError(
                f"the packaged definition for {args.activity!r} instance {args.instance} "
                "became unreadable during token inspection"
            ) from exc
        except Exception as exc:
            raise DefinitionParseError(
                f"tokenization failed for activity {args.activity!r} instance {args.instance}: "
                f"{safe_exception_detail(exc)}"
            ) from exc

    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.activity is None and (args.tokens or args.natural_language):
        parser.error("--tokens and --natural-language require --activity")

    try:
        result = inspect_activity(args)
    except InspectionError as exc:
        print(f"{exc.label}: {exc}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # Avoid exposing a machine-specific traceback in normal CLI use.
        print(
            f"unexpected inspection error: {type(exc).__name__}: "
            f"{safe_exception_detail(exc)}",
            file=sys.stderr,
        )
        return 6

    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
