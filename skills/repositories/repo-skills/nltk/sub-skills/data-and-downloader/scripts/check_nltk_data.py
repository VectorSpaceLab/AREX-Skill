#!/usr/bin/env python3
"""No-download NLTK data checker.

Default behavior is read-only: import NLTK, show the effective data path,
and probe targeted resources with nltk.data.find(). Network/downloads occur
only when --download is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

DEFAULT_PACKAGES = [
    "punkt_tab",
    "averaged_perceptron_tagger_eng",
    "averaged_perceptron_tagger_rus",
    "wordnet",
    "omw-2.0",
    "vader_lexicon",
    "universal_tagset",
]

EXTRA_KNOWN_PACKAGES = [
    "brown",
    "treebank",
    "reuters",
    "comtrans",
]

RESOURCE_PROBES: dict[str, list[str]] = {
    "punkt_tab": [
        "tokenizers/punkt_tab/english/",
        "tokenizers/punkt_tab.zip/punkt_tab/english/",
    ],
    "averaged_perceptron_tagger_eng": [
        "taggers/averaged_perceptron_tagger_eng/",
        "taggers/averaged_perceptron_tagger_eng.zip/averaged_perceptron_tagger_eng/",
    ],
    "averaged_perceptron_tagger_rus": [
        "taggers/averaged_perceptron_tagger_rus/",
        "taggers/averaged_perceptron_tagger_rus.zip/averaged_perceptron_tagger_rus/",
    ],
    "wordnet": [
        "corpora/wordnet/",
        "corpora/wordnet.zip/wordnet/",
    ],
    "omw-2.0": [
        "corpora/omw-2.0/",
        "corpora/omw-2.0.zip/omw-2.0/",
    ],
    "vader_lexicon": [
        "sentiment/vader_lexicon.zip/vader_lexicon/vader_lexicon.txt",
        "sentiment/vader_lexicon/vader_lexicon.txt",
    ],
    "universal_tagset": [
        "taggers/universal_tagset/",
        "taggers/universal_tagset.zip/universal_tagset/",
        "taggers/universal_tagset/en-brown.map",
        "taggers/universal_tagset.zip/universal_tagset/en-brown.map",
    ],
    "brown": [
        "corpora/brown/",
        "corpora/brown.zip/brown/",
    ],
    "treebank": [
        "corpora/treebank/combined/",
        "corpora/treebank.zip/treebank/combined/",
        "corpora/treebank/",
        "corpora/treebank.zip/treebank/",
    ],
    "reuters": [
        "corpora/reuters/",
        "corpora/reuters.zip/reuters/",
    ],
    "comtrans": [
        "corpora/comtrans/",
        "corpora/comtrans.zip/comtrans/",
    ],
}


@dataclass
class ProbeResult:
    name: str
    probes: list[str]
    present: bool
    matched_probe: str | None = None
    pointer_type: str | None = None
    pointer: str | None = None
    size: int | None = None
    errors: list[str] | None = None


def _load_nltk():
    try:
        import nltk  # type: ignore
        import nltk.data  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on runtime install
        print(f"ERROR: could not import nltk: {exc}", file=sys.stderr)
        sys.exit(3)
    return nltk


def _dedupe(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _apply_data_dirs(nltk, data_dirs: list[str], append: bool) -> None:
    if not data_dirs:
        return
    expanded = [os.path.abspath(os.path.expanduser(p)) for p in data_dirs]
    current = list(nltk.data.path)
    if append:
        nltk.data.path[:] = _dedupe([*current, *expanded])
    else:
        nltk.data.path[:] = _dedupe([*expanded, *current])


def _pointer_size(pointer) -> int | None:
    if hasattr(pointer, "file_size"):
        try:
            return int(pointer.file_size())
        except Exception:
            return None
    return None


def _probe_one(nltk, name: str, probes: list[str], inspect: bool) -> ProbeResult:
    errors: list[str] = []
    for resource in probes:
        try:
            pointer = nltk.data.find(resource)
        except LookupError as exc:
            first_line = str(exc).strip().splitlines()[0] if str(exc).strip() else "LookupError"
            errors.append(f"{resource}: {first_line}")
        except ValueError as exc:
            errors.append(f"{resource}: ValueError: {exc}")
        else:
            return ProbeResult(
                name=name,
                probes=probes,
                present=True,
                matched_probe=resource,
                pointer_type=type(pointer).__name__ if inspect else None,
                pointer=str(pointer) if inspect else None,
                size=_pointer_size(pointer) if inspect else None,
                errors=[] if inspect else None,
            )
    return ProbeResult(
        name=name,
        probes=probes,
        present=False,
        errors=errors[-3:] if inspect else None,
    )


def _download_packages(nltk, packages: list[str], download_dir: str | None, quiet: bool) -> dict[str, bool]:
    results: dict[str, bool] = {}
    for package in packages:
        try:
            ok = bool(nltk.download(package, download_dir=download_dir, quiet=quiet, halt_on_error=True))
        except Exception as exc:
            print(f"ERROR downloading {package!r}: {exc}", file=sys.stderr)
            ok = False
        results[package] = ok
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check targeted NLTK data resources without downloading by default. "
            "Use --download to explicitly call nltk.download for selected package IDs."
        )
    )
    parser.add_argument(
        "-p",
        "--package",
        action="append",
        dest="packages",
        help=(
            "Package ID to check. Repeatable. Defaults to targeted core packages: "
            + ", ".join(DEFAULT_PACKAGES)
        ),
    )
    parser.add_argument(
        "--all-known",
        action="store_true",
        help="Also check corpus packages used by the NLTK repo skill examples: brown, treebank, reuters, comtrans.",
    )
    parser.add_argument(
        "-r",
        "--resource",
        action="append",
        default=[],
        help="Additional exact resource path to probe with nltk.data.find(). Repeatable.",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        action="append",
        default=[],
        help="Top-level nltk_data directory to prepend to nltk.data.path before probing. Repeatable.",
    )
    parser.add_argument(
        "--append-data-dir",
        action="store_true",
        help="Append --data-dir entries instead of prepending them.",
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
        help="Print pointer type/path/size details and short probe errors.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text.",
    )
    parser.add_argument(
        "--require",
        action="store_true",
        help="Exit non-zero if any selected package/resource is missing.",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Explicitly download selected package IDs before probing. Not enabled by default.",
    )
    parser.add_argument(
        "--download-dir",
        help="Directory passed to nltk.download when --download is used. Also prepended for the follow-up probe.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Pass quiet=True to nltk.download when --download is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    nltk = _load_nltk()

    data_dirs = list(args.data_dir)
    if args.download_dir:
        data_dirs.insert(0, args.download_dir)
    _apply_data_dirs(nltk, data_dirs, append=args.append_data_dir)

    packages = args.packages[:] if args.packages else list(DEFAULT_PACKAGES)
    if args.all_known:
        packages.extend(EXTRA_KNOWN_PACKAGES)
    packages = _dedupe(packages)

    download_results: dict[str, bool] | None = None
    if args.download:
        download_results = _download_packages(nltk, packages, args.download_dir, args.quiet)

    results: list[ProbeResult] = []
    for package in packages:
        probes = RESOURCE_PROBES.get(package, [])
        if not probes:
            probes = [f"corpora/{package}/", f"corpora/{package}.zip/{package}/"]
        results.append(_probe_one(nltk, package, probes, args.inspect))

    for resource in args.resource:
        results.append(_probe_one(nltk, f"resource:{resource}", [resource], args.inspect))

    payload = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "nltk_version": getattr(nltk, "__version__", "unknown"),
        "nltk_data_env": os.environ.get("NLTK_DATA"),
        "nltk_data_path": list(nltk.data.path),
        "download_attempted": bool(args.download),
        "download_results": download_results,
        "results": [asdict(result) for result in results],
    }

    missing = [result.name for result in results if not result.present]

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"Python: {payload['python']} ({payload['platform']})")
        print(f"NLTK: {payload['nltk_version']}")
        print(f"NLTK_DATA: {payload['nltk_data_env']}")
        print("nltk.data.path:")
        for item in payload["nltk_data_path"]:
            print(f"  - {item}")
        if download_results is not None:
            print("download results:")
            for package, ok in download_results.items():
                print(f"  - {package}: {'ok' if ok else 'failed'}")
        print("resource checks:")
        for result in results:
            status = "present" if result.present else "missing"
            print(f"  - {result.name}: {status}")
            if result.matched_probe:
                print(f"      matched: {result.matched_probe}")
            if args.inspect and result.pointer:
                print(f"      pointer: {result.pointer_type}: {result.pointer}")
                if result.size is not None:
                    print(f"      size: {result.size}")
            if args.inspect and result.errors:
                for error in result.errors:
                    print(f"      tried: {error}")
        if missing:
            print("missing package/resource names:")
            for name in missing:
                print(f"  - {name}")
            print("No downloads were attempted." if not args.download else "Downloads were attempted; inspect failures above.")

    if args.require and missing:
        return 2
    if args.download and download_results and not all(download_results.values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
