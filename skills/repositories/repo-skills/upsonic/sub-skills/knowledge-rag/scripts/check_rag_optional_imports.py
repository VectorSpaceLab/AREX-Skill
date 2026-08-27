#!/usr/bin/env python3
from __future__ import annotations

import importlib.util

MODULES = [
    'upsonic.knowledge_base.knowledge_base',
    'upsonic.embeddings.factory',
    'upsonic.vectordb.factory',
    'upsonic.loaders.factory',
    'upsonic.ocr.ocr',
    'chromadb',
    'qdrant_client',
    'pymilvus',
    'weaviate',
    'pinecone',
    'psycopg',
    'redis',
    'pdfplumber',
    'pymupdf',
    'pypdf',
    'docling',
    'rapidocr_onnxruntime',
]


def main() -> int:
    for module in MODULES:
        print(f'{module}: {importlib.util.find_spec(module) is not None}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
