#!/usr/bin/env python3
"""Safe dependency probe for Chonkie storage integrations.

The default probe is intentionally non-mutating: it imports Chonkie classes and
optional client packages only. It does not instantiate datastore clients, open
network connections, create collections/indexes, or write chunks.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class IntegrationSpec:
    alias: str
    kind: str
    class_module: str
    class_name: str
    client_module: str | None
    install_hint: str
    safety_note: str


@dataclass
class ProbeResult:
    alias: str
    kind: str
    class_name: str
    class_ok: bool
    class_error: str | None
    client_module: str | None
    client_spec_found: bool | None
    client_import_ok: bool | None
    client_error: str | None
    install_hint: str
    safety_note: str


INTEGRATIONS: list[IntegrationSpec] = [
    IntegrationSpec(
        "json",
        "porter",
        "chonkie.porters",
        "JSONPorter",
        None,
        "included in the base chonkie package",
        "offline file export; creates/overwrites only the file path you choose",
    ),
    IntegrationSpec(
        "datasets",
        "porter",
        "chonkie.porters",
        "DatasetsPorter",
        "datasets",
        "python -m pip install 'chonkie[datasets]'",
        "offline Dataset creation/save; no datastore service required",
    ),
    IntegrationSpec(
        "chroma",
        "handshake",
        "chonkie.handshakes",
        "ChromaHandshake",
        "chromadb",
        "python -m pip install 'chonkie[chroma]'",
        "can use in-process or local persistent Chroma; writes still mutate that store",
    ),
    IntegrationSpec(
        "qdrant",
        "handshake",
        "chonkie.handshakes",
        "QdrantHandshake",
        "qdrant_client",
        "python -m pip install 'chonkie[qdrant]'",
        "can use in-memory Qdrant by default; URL/API key targets live service",
    ),
    IntegrationSpec(
        "lancedb",
        "handshake",
        "chonkie.handshakes",
        "LanceDBHandshake",
        "lancedb",
        "python -m pip install 'chonkie[lancedb]'",
        "defaults to memory://; persistent URIs mutate local/remote LanceDB storage",
    ),
    IntegrationSpec(
        "milvus",
        "handshake",
        "chonkie.handshakes",
        "MilvusHandshake",
        "pymilvus",
        "python -m pip install 'chonkie[milvus]'",
        "constructor may connect to Milvus and create/load collections",
    ),
    IntegrationSpec(
        "mongodb",
        "handshake",
        "chonkie.handshakes",
        "MongoDBHandshake",
        "pymongo",
        "python -m pip install 'chonkie[mongodb]'",
        "defaults can target localhost MongoDB; writes use insert_many",
    ),
    IntegrationSpec(
        "pgvector",
        "handshake",
        "chonkie.handshakes",
        "PgvectorHandshake",
        "vecs",
        "python -m pip install 'chonkie[pgvector]'",
        "defaults can target local PostgreSQL/pgvector via vecs",
    ),
    IntegrationSpec(
        "pinecone",
        "handshake",
        "chonkie.handshakes",
        "PineconeHandshake",
        "pinecone",
        "python -m pip install 'chonkie[pinecone]'",
        "requires API key or mocked client; may create remote indexes",
    ),
    IntegrationSpec(
        "turbopuffer",
        "handshake",
        "chonkie.handshakes",
        "TurbopufferHandshake",
        "turbopuffer",
        "python -m pip install 'chonkie[tpuf]'",
        "requires API key or mocks; may touch remote namespaces when instantiated",
    ),
    IntegrationSpec(
        "weaviate",
        "handshake",
        "chonkie.handshakes",
        "WeaviateHandshake",
        "weaviate",
        "python -m pip install 'chonkie[weaviate]'",
        "defaults can target localhost/cloud helpers and create collections",
    ),
    IntegrationSpec(
        "elastic",
        "handshake",
        "chonkie.handshakes",
        "ElasticHandshake",
        "elasticsearch",
        "python -m pip install 'chonkie[elastic]'",
        "defaults can target localhost Elasticsearch and create indexes",
    ),
]


def _short_error(exc: BaseException, verbose: bool) -> str:
    text = f"{type(exc).__name__}: {exc}"
    if verbose or len(text) <= 180:
        return text
    return text[:177] + "..."


def _import_class(module_name: str, class_name: str, verbose: bool) -> tuple[bool, str | None]:
    try:
        module = importlib.import_module(module_name)
        getattr(module, class_name)
        return True, None
    except Exception as exc:  # noqa: BLE001 - diagnostic script should report any import failure
        return False, _short_error(exc, verbose)


def _probe_client_module(
    module_name: str | None,
    *,
    import_clients: bool,
    verbose: bool,
) -> tuple[bool | None, bool | None, str | None]:
    if module_name is None:
        return None, None, None

    try:
        spec_found = importlib.util.find_spec(module_name) is not None
    except Exception as exc:  # noqa: BLE001
        return False, False, _short_error(exc, verbose)

    if not spec_found:
        return False, False, None

    if not import_clients:
        return True, None, None

    try:
        importlib.import_module(module_name)
        return True, True, None
    except Exception as exc:  # noqa: BLE001
        return True, False, _short_error(exc, verbose)


def run_probe(
    aliases: set[str] | None,
    *,
    import_clients: bool,
    verbose: bool,
) -> list[ProbeResult]:
    selected = [spec for spec in INTEGRATIONS if aliases is None or spec.alias in aliases]
    results: list[ProbeResult] = []
    for spec in selected:
        class_ok, class_error = _import_class(spec.class_module, spec.class_name, verbose)
        client_spec_found, client_import_ok, client_error = _probe_client_module(
            spec.client_module,
            import_clients=import_clients,
            verbose=verbose,
        )
        results.append(
            ProbeResult(
                alias=spec.alias,
                kind=spec.kind,
                class_name=spec.class_name,
                class_ok=class_ok,
                class_error=class_error,
                client_module=spec.client_module,
                client_spec_found=client_spec_found,
                client_import_ok=client_import_ok,
                client_error=client_error,
                install_hint=spec.install_hint,
                safety_note=spec.safety_note,
            )
        )
    return results


def _status(result: ProbeResult) -> str:
    if not result.class_ok:
        return "CLASS-FAIL"
    if result.client_module is None:
        return "OK"
    if not result.client_spec_found:
        return "MISSING"
    if result.client_import_ok is False:
        return "IMPORT-FAIL"
    if result.client_import_ok is None:
        return "FOUND"
    return "OK"


def print_table(results: list[ProbeResult], *, import_clients: bool) -> None:
    print("Chonkie integrations dependency probe")
    print("Safety: no clients are instantiated; no network calls or datastore writes are attempted.")
    if not import_clients:
        print("Client packages were checked with importlib.find_spec only.")
    print()

    header = f"{'alias':<13} {'kind':<10} {'class':<24} {'client package':<17} status"
    print(header)
    print("-" * len(header))
    for result in results:
        client = result.client_module or "(base)"
        print(
            f"{result.alias:<13} {result.kind:<10} {result.class_name:<24} "
            f"{client:<17} {_status(result)}"
        )
    print()

    for result in results:
        status = _status(result)
        if status == "OK" or status == "FOUND":
            continue
        print(f"{result.alias}: {status}")
        if result.class_error:
            print(f"  class import error: {result.class_error}")
        if result.client_error:
            print(f"  client import error: {result.client_error}")
        print(f"  install hint: {result.install_hint}")
        print(f"  safety: {result.safety_note}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Probe optional Chonkie porter/handshake dependencies without "
            "instantiating datastore clients or writing to services."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON instead of a table.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="ALIAS",
        help=(
            "Limit checks to aliases such as chroma qdrant datasets. "
            "Default: check all known storage integrations."
        ),
    )
    parser.add_argument(
        "--skip-client-imports",
        action="store_true",
        help=(
            "Use importlib.find_spec for optional client packages but do not "
            "import those packages. Chonkie classes are still imported."
        ),
    )
    parser.add_argument(
        "--fail-on-class-error",
        action="store_true",
        help="Exit non-zero if any requested Chonkie class cannot be imported.",
    )
    parser.add_argument(
        "--fail-on-missing-client",
        action="store_true",
        help=(
            "Exit non-zero if any requested optional client package is missing "
            "or cannot be imported."
        ),
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Do not truncate exception messages.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    known_aliases = {spec.alias for spec in INTEGRATIONS}
    aliases = set(args.only) if args.only else None
    if aliases is not None:
        unknown = sorted(aliases - known_aliases)
        if unknown:
            print(f"Unknown alias(es): {', '.join(unknown)}", file=sys.stderr)
            print(f"Known aliases: {', '.join(sorted(known_aliases))}", file=sys.stderr)
            return 2

    results = run_probe(
        aliases,
        import_clients=not args.skip_client_imports,
        verbose=args.verbose,
    )

    if args.json:
        payload: dict[str, Any] = {
            "safety": "no clients instantiated; no network calls; no datastore writes",
            "clientImportsAttempted": not args.skip_client_imports,
            "results": [asdict(result) | {"status": _status(result)} for result in results],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print_table(results, import_clients=not args.skip_client_imports)

    failed = False
    if args.fail_on_class_error and any(not result.class_ok for result in results):
        failed = True
    if args.fail_on_missing_client:
        failed = failed or any(
            result.client_module is not None
            and (result.client_spec_found is not True or result.client_import_ok is False)
            for result in results
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
