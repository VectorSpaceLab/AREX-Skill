#!/usr/bin/env python3
"""No-network LazyLLM RAG BM25 smoke check."""
from __future__ import annotations

import argparse
import json
from typing import Dict


def run() -> Dict[str, object]:
    from lazyllm.tools.rag.component.bm25 import BM25
    from lazyllm.tools.rag.doc_node import DocNode

    en_nodes = [
        DocNode(text="This is a test document."),
        DocNode(text="This document is for testing BM25."),
        DocNode(text="BM25 is a ranking function used in information retrieval."),
    ]
    en_hits = BM25(en_nodes, language="en", topk=2).retrieve("test document")
    if len(en_hits) != 2 or en_nodes[0] not in [node for node, _score in en_hits]:
        raise AssertionError("English BM25 smoke failed")

    zh_nodes = [
        DocNode(text="这是一个测试文档。这个文档用于测试BM25。"),
        DocNode(text="BM25是一种在信息检索中使用的排序函数。"),
        DocNode(text="中文文档的测试内容。测试文档中包含多个句子。"),
    ]
    zh_hits = BM25(zh_nodes, language="zh", topk=2).retrieve("测试文档")
    if len(zh_hits) != 2 or zh_nodes[0] not in [node for node, _score in zh_hits]:
        raise AssertionError("Chinese BM25 smoke failed")

    return {
        "english_hits": [node.text for node, _score in en_hits],
        "chinese_hits": [node.text for node, _score in zh_hits],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local LazyLLM BM25 RAG smoke checks.")
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
