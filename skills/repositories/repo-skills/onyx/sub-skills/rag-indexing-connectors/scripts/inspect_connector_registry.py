#!/usr/bin/env python3
"""Read-only helper for inspecting Onyx connector registry wiring.

The script adds the repository backend directory to sys.path, imports the
connector registry and factory when possible, and prints a per-source summary of
module/class resolution plus interface-based input support.

It never writes to the repository, never opens network connections, and treats
missing optional connector dependencies as reportable diagnostics instead of
fatal errors for the whole run.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Any


def _configure_sys_path(repo_root: Path) -> None:
    backend_dir = repo_root / "backend"
    if not backend_dir.is_dir():
        raise FileNotFoundError(f"Backend directory not found under {repo_root}")
    backend_str = str(backend_dir)
    if backend_str not in sys.path:
        sys.path.insert(0, backend_str)


def _parse_source_filters(
    raw_sources: str | None,
    document_source_type: type[Any],
) -> list[Any]:
    if not raw_sources:
        return sorted(document_source_type, key=lambda source: source.value)

    wanted: list[Any] = []
    for item in raw_sources.split(","):
        token = item.strip()
        if not token:
            continue
        try:
            wanted.append(document_source_type(token))
            continue
        except Exception:
            pass
        try:
            wanted.append(document_source_type[token])
            continue
        except Exception as exc:
            valid = ", ".join(sorted(source.value for source in document_source_type))
            raise ValueError(
                f"Unknown source {token!r}. Known values: {valid}"
            ) from exc
    return wanted


def _resolve_connector_class(
    module_path: str,
    class_name: str,
) -> tuple[type[Any] | None, str | None]:
    try:
        module = importlib.import_module(module_path)
        connector_class = getattr(module, class_name)
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

    if not isinstance(connector_class, type):
        return None, f"{class_name} is not a class"

    return connector_class, None


def _bool_flag(name: str, value: bool) -> str:
    return f"{name}={'yes' if value else 'no'}"


def _summarize_support(
    connector_class: type[Any],
    load_connector: type[Any] | None,
    poll_connector: type[Any] | None,
    slim_connector: type[Any] | None,
    slim_perm_connector: type[Any] | None,
    checkpointed_connector: type[Any] | None,
    checkpointed_perm_connector: type[Any] | None,
    credentials_connector: type[Any] | None,
    event_connector: type[Any] | None,
    interfaces_import_error: Exception | None,
) -> str:
    if interfaces_import_error is not None or any(
        interface is None
        for interface in (
            load_connector,
            poll_connector,
            slim_connector,
            slim_perm_connector,
            checkpointed_connector,
            checkpointed_perm_connector,
            credentials_connector,
            event_connector,
        )
    ):
        return f"support=unavailable({type(interfaces_import_error).__name__ if interfaces_import_error is not None else 'unknown'})"

    parts = [
        _bool_flag("load", issubclass(connector_class, load_connector)),
        _bool_flag("poll", issubclass(connector_class, poll_connector)),
        _bool_flag("event", issubclass(connector_class, event_connector)),
        _bool_flag("slim", issubclass(connector_class, slim_connector)),
        _bool_flag(
            "slim_perm", issubclass(connector_class, slim_perm_connector)
        ),
        _bool_flag("checkpoint", issubclass(connector_class, checkpointed_connector)),
        _bool_flag(
            "checkpoint_perm",
            issubclass(connector_class, checkpointed_perm_connector),
        ),
        _bool_flag("creds", issubclass(connector_class, credentials_connector)),
    ]
    return " ".join(parts)


def _summarize_factory_support(
    source: Any,
    identify_connector_class: Any | None,
    connector_missing_exception: type[Exception] | None,
    input_type_cls: type[Any],
) -> str:
    if identify_connector_class is None or connector_missing_exception is None:
        return "factory=unavailable"

    statuses: list[str] = []
    for input_type_name in ("LOAD_STATE", "POLL", "EVENT"):
        input_type = input_type_cls[input_type_name]
        try:
            identify_connector_class(source, input_type)
            statuses.append(f"{input_type.value}=ok")
        except connector_missing_exception:
            statuses.append(f"{input_type.value}=unsupported")
        except Exception as exc:
            statuses.append(f"{input_type.value}=error({type(exc).__name__})")
    return "factory[" + ", ".join(statuses) + "]"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Inspect Onyx connector registry wiring in a read-only way."
    )
    parser.add_argument(
        "--repo-root",
        required=True,
        help="Path to the repository root that contains backend/.",
    )
    parser.add_argument(
        "--source",
        help="Optional source filter. Accepts a DocumentSource value or enum name.",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).expanduser().resolve()
    _configure_sys_path(repo_root)

    try:
        from onyx.configs.constants import DocumentSource
        from onyx.connectors.models import InputType
        from onyx.connectors.registry import CONNECTOR_CLASS_MAP
    except Exception as exc:
        print(f"Failed to import connector registry dependencies: {exc}", file=sys.stderr)
        return 1

    try:
        from onyx.connectors.interfaces import (  # type: ignore[import-not-found]
            CheckpointedConnector,
            CheckpointedConnectorWithPermSync,
            CredentialsConnector,
            EventConnector,
            LoadConnector,
            PollConnector,
            SlimConnector,
            SlimConnectorWithPermSync,
        )
    except Exception as exc:
        LoadConnector = None
        PollConnector = None
        SlimConnector = None
        SlimConnectorWithPermSync = None
        CheckpointedConnector = None
        CheckpointedConnectorWithPermSync = None
        CredentialsConnector = None
        EventConnector = None
        interfaces_import_error = exc
    else:
        interfaces_import_error = None

    try:
        from onyx.connectors.factory import (  # type: ignore[import-not-found]
            ConnectorMissingException,
            identify_connector_class,
        )
    except Exception as exc:
        ConnectorMissingException = None
        identify_connector_class = None
        factory_import_error = exc
    else:
        factory_import_error = None

    try:
        sources = _parse_source_filters(args.source, DocumentSource)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if interfaces_import_error is not None:
        print(
            f"Connector interface import unavailable: {type(interfaces_import_error).__name__}: {interfaces_import_error}"
        )
    if factory_import_error is not None:
        print(
            f"Factory import unavailable: {type(factory_import_error).__name__}: {factory_import_error}"
        )

    for source in sources:
        mapping = CONNECTOR_CLASS_MAP.get(source)
        if mapping is None:
            print(f"{source.value} | unmapped")
            continue

        connector_class, import_error = _resolve_connector_class(
            mapping.module_path,
            mapping.class_name,
        )
        if import_error is not None or connector_class is None:
            print(
                f"{source.value} | {mapping.module_path}.{mapping.class_name} | import_error={import_error}"
            )
            continue

        support = _summarize_support(
            connector_class=connector_class,
            load_connector=LoadConnector,
            poll_connector=PollConnector,
            slim_connector=SlimConnector,
            slim_perm_connector=SlimConnectorWithPermSync,
            checkpointed_connector=CheckpointedConnector,
            checkpointed_perm_connector=CheckpointedConnectorWithPermSync,
            credentials_connector=CredentialsConnector,
            event_connector=EventConnector,
            interfaces_import_error=interfaces_import_error,
        )
        factory_support = _summarize_factory_support(
            source=source,
            identify_connector_class=identify_connector_class,
            connector_missing_exception=ConnectorMissingException,
            input_type_cls=InputType,
        )
        print(
            f"{source.value} | {mapping.module_path}.{mapping.class_name} | {support} | {factory_support}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
