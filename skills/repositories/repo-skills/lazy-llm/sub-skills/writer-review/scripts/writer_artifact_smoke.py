#!/usr/bin/env python3
"""No-network LazyLLM writer artifact smoke check."""
from __future__ import annotations

import argparse
import json
import tempfile
from typing import Dict


def run() -> Dict[str, object]:
    from lazyllm.tools.writer.data_models import ResourceProfile, WriterBlock, WriterDocument, WriterSpan, WritingContext
    from lazyllm.tools.writer.tools.base import WriterToolBase
    from lazyllm.tools.writer.utils import load_artifact_json, save_artifact_json

    paragraph = WriterBlock(
        node_id="block-1",
        type="paragraph",
        content="正文内容",
        spans=[WriterSpan(text="正文内容", style={"bold": True})],
        stage="draft",
        provider_binding={"provider": "feishu", "block_id": "external-1"},
        provider_payload={"raw_type": "paragraph"},
    )
    section = WriterBlock(
        node_id="section-1",
        type="heading",
        content="第一章",
        stage="draft",
        numbering={"level": 1},
        children=[paragraph],
    )
    document = WriterDocument(
        document_id="document-1",
        stage="draft",
        title="测试文档",
        blocks=[section],
        revision="rev-1",
        metadata={"source": "skill-smoke"},
        provider_binding={"provider": "feishu", "document_id": "external-doc-1"},
    )
    restored = WriterDocument.model_validate_json(document.model_dump_json())
    assert restored.block_by_id("block-1").provider_payload["raw_type"] == "paragraph"

    context = WritingContext(context_id="ctx-1")
    profiles = [ResourceProfile(resource_id="r1", resource_role="background")]

    with tempfile.TemporaryDirectory(prefix="lazyllm_writer_smoke_") as directory:
        document_path = save_artifact_json(document, f"{directory}/document.json")
        loaded = load_artifact_json(document_path, WriterDocument)
        assert loaded.block_by_id("block-1").spans[0].style == {"bold": True}

        result = WriterToolBase(artifact_store=directory)._save_artifacts(
            {"document": document, "writing_context": context, "resource_profiles": profiles},
            step_name="create_document",
            primary_key="document",
            summary="Created document.",
            counts={"blocks": 2, "resource_profiles": 1},
        )
        assert result.metadata["counts"]["blocks"] == 2
        return {
            "document_title": loaded.title,
            "block_ids": [block.node_id for block in loaded.iter_blocks()],
            "artifact_path_suffix": result.artifact_path.rsplit("/", 1)[-1],
            "context_path_suffix": result.context_path.rsplit("/", 1)[-1],
            "counts": result.metadata["counts"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local LazyLLM writer artifact smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    result = run()
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
