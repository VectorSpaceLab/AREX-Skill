#!/usr/bin/env python3
"""Offline text-document smoke test for MineContext DocumentProcessor.

The repository's full document examples can call model services for semantic
chunking or visual extraction. This skill-owned helper keeps the smoke CPU-only:
it creates a temporary config directory, monkeypatches the text chunker to avoid
LLM calls, processes a tiny `.txt` fixture, verifies `knowledge_context` output,
and cleans up all temporary files.

Examples:
  python smoke_document_text.py
  python smoke_document_text.py --repo-root /path/to/MineContext --text "custom fixture"
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import List


class SmokeFailure(RuntimeError):
    """Raised when a smoke assertion fails."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe DocumentProcessor text smoke test.")
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional MineContext checkout root to add to sys.path before importing opencontext.",
    )
    parser.add_argument(
        "--text",
        default="MineContext smoke document. This text should become a knowledge context chunk.",
        help="Fixture text to process (default: a short MineContext sentence).",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging.")
    return parser.parse_args()


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def add_repo_root(repo_root: Path | None) -> None:
    if not repo_root:
        return
    repo_root = repo_root.expanduser().resolve()
    if not (repo_root / "opencontext").is_dir():
        raise SmokeFailure(f"--repo-root does not contain opencontext/: {repo_root}")
    sys.path.insert(0, str(repo_root))


def write_minimal_config(work_dir: Path) -> None:
    config_dir = work_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.yaml").write_text(
        """
enabled: true
logging:
  level: INFO
  log_path: null
user_setting_path: "./config/user_setting.yaml"
prompts:
  language: en
document_processing:
  enabled: true
  batch_size: 1
  max_image_size: 512
  dpi: 100
  text_threshold_per_page: 50
processing:
  enabled: true
  document_processor:
    enabled: true
    batch_size: 1
    batch_timeout: 1
  screenshot_processor:
    enabled: false
  context_merger:
    enabled: false
storage:
  enabled: false
capture:
  enabled: false
content_generation:
  activity: {enabled: false, interval: 900}
  tips: {enabled: false, interval: 1800}
  todos: {enabled: false, interval: 1800}
  report: {enabled: false, time: "08:00"}
completion:
  enabled: false
api_auth:
  enabled: false
  api_keys: []
  excluded_paths: []
vlm_model:
  base_url: ""
  api_key: ""
  model: ""
  provider: ""
embedding_model:
  base_url: ""
  api_key: ""
  model: ""
  provider: ""
  output_dim: 2048
""".strip()
        + "\n",
        encoding="utf-8",
    )
    # Prompt manager only needs the file to exist for this smoke because the
    # chunker is monkeypatched before any prompt lookup is needed.
    (config_dir / "prompts_en.yaml").write_text("{}\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose)
    temp_dir = Path(tempfile.mkdtemp(prefix="minecontext-doc-smoke-"))
    old_cwd = Path.cwd()
    failures: List[str] = []
    processor = None

    try:
        add_repo_root(args.repo_root)
        write_minimal_config(temp_dir)
        os.chdir(temp_dir)

        # Reset singleton config/storage in case this helper is run inside an
        # existing Python process that imported opencontext earlier.
        from opencontext.config.global_config import GlobalConfig
        from opencontext.models.context import Chunk, RawContextProperties
        from opencontext.models.enums import ContentFormat, ContextSource, ContextType

        GlobalConfig.reset()

        from opencontext.context_processing.processor.document_processor import DocumentProcessor

        fixture = temp_dir / "fixture.txt"
        fixture.write_text(args.text, encoding="utf-8")

        processor = DocumentProcessor()

        def offline_chunk_text(texts, document_title=None):
            joined = "\n\n".join(t.strip() for t in texts if t and t.strip())
            return [Chunk(text=joined, chunk_index=0)] if joined else []

        processor._document_chunker.chunk_text = offline_chunk_text  # noqa: SLF001 - deliberate smoke patch

        raw = RawContextProperties(
            source=ContextSource.LOCAL_FILE,
            content_format=ContentFormat.FILE,
            content_path=str(fixture),
            content_text="",
            filter_path=str(fixture),
            create_time=dt.datetime.now(),
            additional_info={"event_type": "file_created", "smoke": True},
            enable_merge=False,
        )
        if not processor.can_process(raw):
            raise SmokeFailure("DocumentProcessor.can_process() rejected the .txt fixture")

        contexts = processor.real_process(raw)
        if not contexts:
            raise SmokeFailure("DocumentProcessor.real_process() returned no contexts")
        if not isinstance(contexts, list):
            raise SmokeFailure(f"DocumentProcessor.real_process() returned {type(contexts)!r}")

        first = contexts[0]
        if first.extracted_data.context_type != ContextType.KNOWLEDGE_CONTEXT:
            failures.append(f"expected knowledge_context, got {first.extracted_data.context_type}")
        if args.text.split()[0] not in (first.extracted_data.summary or ""):
            failures.append("processed summary does not contain fixture text")
        if not first.vectorize.text:
            failures.append("processed context has empty vectorize text")
        if not first.metadata or first.metadata.get("knowledge_file_path") != str(fixture):
            failures.append("processed context metadata did not preserve fixture path")

        if failures:
            for failure in failures:
                logging.error("FAIL: %s", failure)
            return 1

        logging.info("PASS: DocumentProcessor produced %d knowledge_context item(s)", len(contexts))
        logging.info("Summary: %s", first.extracted_data.summary)
        return 0

    except Exception as exc:
        logging.exception("Document text smoke failed: %s", exc)
        return 1
    finally:
        if processor is not None:
            try:
                processor.shutdown(_graceful=True)
            except Exception:
                logging.exception("DocumentProcessor shutdown failed during cleanup")
        os.chdir(old_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)
        logging.info("Temporary runtime directory removed")


if __name__ == "__main__":
    raise SystemExit(main())
