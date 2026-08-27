#!/usr/bin/env python3
"""Deterministic MineContext/OpenContext folder-monitor smoke check.

This script imports the installed ``opencontext`` package and exercises
FolderMonitorCapture create/update/delete behavior with a temporary watch
directory and mocked storage. It does not start the OpenContext server, does not
write to real MineContext storage, and does not require model credentials.

Use --repo-root only for development checkouts that have not been installed.
"""

from __future__ import annotations

import argparse
import json
import logging
import shutil
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

LOGGER = logging.getLogger("smoke_folder_monitor")


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"--repo-root does not exist: {root}")
    sys.path.insert(0, str(root))


def _scan_once(monitor) -> None:
    """Drive one deterministic scan without waiting for a background poll."""
    monitor._scan_folder_file_changes()  # noqa: SLF001 - intentional smoke of repo component.


def _capture_once(monitor):
    """Capture queued events without requiring a long-running server."""
    return monitor._capture_impl()  # noqa: SLF001 - avoids timing-dependent BaseCapture loop.


def run_smoke(args: argparse.Namespace) -> dict:
    _add_repo_root(args.repo_root)

    from opencontext.context_capture.folder_monitor import FolderMonitorCapture
    from opencontext.models.enums import ContextSource, ContextType

    watch_dir = Path(args.watch_dir).expanduser().resolve() if args.watch_dir else None
    temp_root = None
    if watch_dir is None:
        temp_root = Path(tempfile.mkdtemp(prefix="opencontext-folder-monitor-"))
        watch_dir = temp_root / "watch"
    watch_dir.mkdir(parents=True, exist_ok=True)

    mock_storage = MagicMock(name="mock_storage")
    mock_storage.get_all_processed_contexts.return_value = {}
    mock_storage.delete_processed_context.return_value = True

    monitor = None
    try:
        with patch("opencontext.context_capture.folder_monitor.get_storage", return_value=mock_storage):
            monitor = FolderMonitorCapture()
            config = {
                "monitor_interval": 3600,  # Do not rely on background polling in this smoke.
                "watch_folder_paths": [str(watch_dir)],
                "recursive": True,
                "max_file_size": args.max_file_size,
                "initial_scan": True,
            }
            if not monitor.initialize(config):
                raise AssertionError("FolderMonitorCapture.initialize() returned False")

            # Establish initial empty cache deterministically.
            monitor._scan_existing_folders()  # noqa: SLF001

            sample = watch_dir / "sample.txt"
            sample.write_text("MineContext folder monitor create event\n", encoding="utf-8")
            _scan_once(monitor)
            created = _capture_once(monitor)
            if len(created) != 1:
                raise AssertionError(f"expected 1 create event, got {len(created)}")
            create_ctx = created[0]
            if create_ctx.source != ContextSource.LOCAL_FILE:
                raise AssertionError(f"unexpected source for create event: {create_ctx.source}")
            if create_ctx.additional_info.get("event_type") != "file_created":
                raise AssertionError(f"unexpected create event metadata: {create_ctx.additional_info}")
            if "create event" not in (create_ctx.content_text or ""):
                raise AssertionError("create event did not include text file content")

            # Ensure mtime/hash changes are visible on filesystems with coarse timestamp resolution.
            time.sleep(args.sleep)
            sample.write_text(
                "MineContext folder monitor create event\nMineContext update event\n",
                encoding="utf-8",
            )
            _scan_once(monitor)
            updated = _capture_once(monitor)
            if len(updated) != 1:
                raise AssertionError(f"expected 1 update event, got {len(updated)}")
            if updated[0].additional_info.get("event_type") != "file_updated":
                raise AssertionError(f"unexpected update event metadata: {updated[0].additional_info}")

            mock_storage.get_all_processed_contexts.return_value = {
                ContextType.KNOWLEDGE_CONTEXT: [
                    SimpleNamespace(id="mock_ctx_id_1"),
                    SimpleNamespace(id="mock_ctx_id_2"),
                ]
            }
            sample.unlink()
            _scan_once(monitor)
            deleted = _capture_once(monitor)
            if deleted:
                raise AssertionError(f"delete should not emit raw contexts, got {len(deleted)}")
            if mock_storage.delete_processed_context.call_count < 2:
                raise AssertionError(
                    "delete cleanup did not call storage.delete_processed_context for mocked contexts"
                )

            result = {
                "ok": True,
                "watch_dir": str(watch_dir),
                "create_events": len(created),
                "update_events": len(updated),
                "delete_raw_events": len(deleted),
                "storage_delete_calls": mock_storage.delete_processed_context.call_count,
                "created_context_source": create_ctx.source.value,
                "created_content_format": create_ctx.content_format.value,
            }
            LOGGER.info("folder monitor smoke passed")
            return result
    finally:
        if monitor is not None:
            try:
                # It may not be running because this smoke avoids background capture threads.
                monitor.stop(graceful=True)
            except Exception:  # pragma: no cover - cleanup best effort.
                LOGGER.debug("monitor.stop cleanup failed", exc_info=True)
        if temp_root is not None and not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        help="Optional checkout root to prepend to sys.path before importing opencontext.",
    )
    parser.add_argument(
        "--watch-dir",
        help="Optional existing directory to use instead of a temporary watch directory.",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=1024 * 1024,
        help="Maximum file size in bytes accepted by the monitor (default: 1 MiB).",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.05,
        help="Short delay between create and update writes for mtime visibility.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep the temporary directory for manual inspection.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    _configure_logging(args.verbose)
    try:
        result = run_smoke(args)
    except Exception as exc:  # noqa: BLE001 - command-line smoke should print concise failure.
        LOGGER.exception("folder monitor smoke failed: %s", exc)
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
