#!/usr/bin/env python3
"""Smoke-check the retrieval-doc-chat configuration surface.

This script is deterministic and does not make provider or network calls by
default. It imports the doc-chat, parsing, vector-store, loader, citation, and
attachment surfaces, checks the key defaults, and reports optional dependency
availability without failing on missing extras.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[6]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def install_namespace_packages() -> None:
    package_paths = {
        "langroid": "langroid",
        "langroid.agent": "langroid/agent",
        "langroid.agent.special": "langroid/agent/special",
        "langroid.agent.special.lance_rag": "langroid/agent/special/lance_rag",
        "langroid.agent.tools": "langroid/agent/tools",
        "langroid.parsing": "langroid/parsing",
        "langroid.vector_store": "langroid/vector_store",
        "langroid.embedding_models": "langroid/embedding_models",
        "langroid.language_models": "langroid/language_models",
        "langroid.utils": "langroid/utils",
        "langroid.utils.output": "langroid/utils/output",
        "langroid.cachedb": "langroid/cachedb",
        "langroid.prompts": "langroid/prompts",
    }
    for name, rel_path in package_paths.items():
        if name not in sys.modules:
            module = types.ModuleType(name)
            module.__path__ = [str(REPO_ROOT / rel_path)]
            sys.modules[name] = module

    try:
        from langroid.exceptions import LangroidImportError
    except Exception:
        return
    sys.modules["langroid"].LangroidImportError = LangroidImportError


install_namespace_packages()

try:
    from langroid.utils.output import printing as _output_printing
    from langroid.utils.output.status import status as _output_status
except Exception:
    pass
else:
    _output_pkg = sys.modules.get("langroid.utils.output")
    if _output_pkg is not None:
        for _name in [
            "shorten_text",
            "print_long_text",
            "show_if_debug",
            "SuppressLoggerWarnings",
            "PrintColored",
        ]:
            setattr(_output_pkg, _name, getattr(_output_printing, _name))
        setattr(_output_pkg, "status", _output_status)

if importlib.util.find_spec("nest_asyncio") is None and "nest_asyncio" not in sys.modules:
    nest_asyncio_stub = types.ModuleType("nest_asyncio")
    nest_asyncio_stub.apply = lambda: None  # type: ignore[attr-defined]
    sys.modules["nest_asyncio"] = nest_asyncio_stub

if importlib.util.find_spec("fakeredis") is None and "fakeredis" not in sys.modules:
    fakeredis_stub = types.ModuleType("fakeredis")

    class _FakeStrictRedis:  # pragma: no cover - import shim only
        pass

    fakeredis_stub.FakeStrictRedis = _FakeStrictRedis  # type: ignore[attr-defined]
    sys.modules["fakeredis"] = fakeredis_stub

if importlib.util.find_spec("redis") is None and "redis" not in sys.modules:
    redis_stub = types.ModuleType("redis")

    class _ConnectionPool:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class _Redis:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def close(self) -> None:
            pass

        def client_list(self) -> list[dict[str, Any]]:
            return []

        def client_kill(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def flushdb(self) -> None:
            pass

        def flushall(self) -> None:
            pass

        def set(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def get(self, *_args: Any, **_kwargs: Any) -> None:
            return None

        def delete(self, *_args: Any, **_kwargs: Any) -> None:
            pass

        def keys(self, *_args: Any, **_kwargs: Any) -> list[str]:
            return []

    class _ConnectionError(Exception):
        pass

    redis_stub.ConnectionPool = _ConnectionPool  # type: ignore[attr-defined]
    redis_stub.Redis = _Redis  # type: ignore[attr-defined]
    redis_stub.exceptions = types.SimpleNamespace(ConnectionError=_ConnectionError)
    sys.modules["redis"] = redis_stub

if importlib.util.find_spec("json_repair") is None and "json_repair" not in sys.modules:
    json_repair_stub = types.ModuleType("json_repair")

    def repair_json(value: Any, return_objects: bool = False, *args: Any, **kwargs: Any):
        return value

    json_repair_stub.repair_json = repair_json  # type: ignore[attr-defined]
    sys.modules["json_repair"] = json_repair_stub

if importlib.util.find_spec("tiktoken") is None and "tiktoken" not in sys.modules:
    tiktoken_stub = types.ModuleType("tiktoken")

    class _FakeEncoding:  # pragma: no cover - import shim only
        def encode(self, text: str, *args: Any, **kwargs: Any) -> list[str]:
            return text.split()

        def decode(self, tokens: list[Any], *args: Any, **kwargs: Any) -> str:
            return " ".join(str(token) for token in tokens)

    def encoding_for_model(*args: Any, **kwargs: Any) -> _FakeEncoding:
        return _FakeEncoding()

    def get_encoding(*args: Any, **kwargs: Any) -> _FakeEncoding:
        return _FakeEncoding()

    tiktoken_stub.encoding_for_model = encoding_for_model  # type: ignore[attr-defined]
    tiktoken_stub.get_encoding = get_encoding  # type: ignore[attr-defined]
    sys.modules["tiktoken"] = tiktoken_stub

if importlib.util.find_spec("faker") is None and "faker" not in sys.modules:
    faker_stub = types.ModuleType("faker")

    class _FakeFaker:  # pragma: no cover - import shim only
        @classmethod
        def seed(cls, *args: Any, **kwargs: Any) -> None:
            return None

        def sentence(self) -> str:
            return "placeholder sentence"

    faker_stub.Faker = _FakeFaker  # type: ignore[attr-defined]
    sys.modules["faker"] = faker_stub

if importlib.util.find_spec("fire") is None and "fire" not in sys.modules:
    fire_stub = types.ModuleType("fire")

    def Fire(*args: Any, **kwargs: Any) -> None:
        return None

    fire_stub.Fire = Fire  # type: ignore[attr-defined]
    sys.modules["fire"] = fire_stub

if importlib.util.find_spec("rank_bm25") is None and "rank_bm25" not in sys.modules:
    rank_bm25_stub = types.ModuleType("rank_bm25")

    class BM25Okapi:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def get_scores(self, *args: Any, **kwargs: Any) -> list[float]:
            return []

    rank_bm25_stub.BM25Okapi = BM25Okapi  # type: ignore[attr-defined]
    sys.modules["rank_bm25"] = rank_bm25_stub

if importlib.util.find_spec("thefuzz") is None and "thefuzz" not in sys.modules:
    thefuzz_stub = types.ModuleType("thefuzz")
    thefuzz_stub.fuzz = types.SimpleNamespace(partial_ratio=lambda *_args, **_kwargs: 100)
    thefuzz_stub.process = types.SimpleNamespace(
        extract=lambda query, choices, limit=None, scorer=None: []
    )
    sys.modules["thefuzz"] = thefuzz_stub

if importlib.util.find_spec("colorlog") is None and "colorlog" not in sys.modules:
    import logging as _logging

    colorlog_stub = types.ModuleType("colorlog")

    class _ColoredFormatter(_logging.Formatter):  # pragma: no cover - import shim only
        def __init__(
            self,
            fmt: str | None = None,
            datefmt: str | None = None,
            *args: Any,
            **kwargs: Any,
        ) -> None:
            super().__init__(fmt=fmt, datefmt=datefmt)

    colorlog_stub.ColoredFormatter = _ColoredFormatter  # type: ignore[attr-defined]
    sys.modules["colorlog"] = colorlog_stub

if importlib.util.find_spec("openai") is None and "openai" not in sys.modules:
    openai_stub = types.ModuleType("openai")

    class _OpenAIError(Exception):  # pragma: no cover - import shim only
        pass

    class _AuthenticationError(_OpenAIError):
        pass

    class _APIError(_OpenAIError):
        pass

    class _APIStatusError(_APIError):
        pass

    class _APITimeoutError(_APIError):
        pass

    class _RateLimitError(_APIError):
        pass

    class _BadRequestError(_APIError):
        pass

    class _PermissionDeniedError(_APIError):
        pass

    class _NotFoundError(_APIError):
        pass

    class _UnprocessableEntityError(_APIError):
        pass

    class _APIConnectionError(_APIError):
        pass

    class _ModelList:
        def list(self, *args: Any, **kwargs: Any) -> list[Any]:
            return []

    class _OpenAI:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.models = _ModelList()

    class _AsyncOpenAI(_OpenAI):  # pragma: no cover - import shim only
        pass

    class _AzureOpenAI(_OpenAI):  # pragma: no cover - import shim only
        pass

    class _AsyncAzureOpenAI(_AsyncOpenAI):  # pragma: no cover - import shim only
        pass

    openai_stub.OpenAIError = _OpenAIError  # type: ignore[attr-defined]
    openai_stub.AuthenticationError = _AuthenticationError  # type: ignore[attr-defined]
    openai_stub.APIError = _APIError  # type: ignore[attr-defined]
    openai_stub.APIStatusError = _APIStatusError  # type: ignore[attr-defined]
    openai_stub.APITimeoutError = _APITimeoutError  # type: ignore[attr-defined]
    openai_stub.RateLimitError = _RateLimitError  # type: ignore[attr-defined]
    openai_stub.BadRequestError = _BadRequestError  # type: ignore[attr-defined]
    openai_stub.PermissionDeniedError = _PermissionDeniedError  # type: ignore[attr-defined]
    openai_stub.NotFoundError = _NotFoundError  # type: ignore[attr-defined]
    openai_stub.UnprocessableEntityError = _UnprocessableEntityError  # type: ignore[attr-defined]
    openai_stub.APIConnectionError = _APIConnectionError  # type: ignore[attr-defined]
    openai_stub.OpenAI = _OpenAI  # type: ignore[attr-defined]
    openai_stub.AsyncOpenAI = _AsyncOpenAI  # type: ignore[attr-defined]
    openai_stub.AzureOpenAI = _AzureOpenAI  # type: ignore[attr-defined]
    openai_stub.AsyncAzureOpenAI = _AsyncAzureOpenAI  # type: ignore[attr-defined]
    sys.modules["openai"] = openai_stub

if importlib.util.find_spec("groq") is None and "groq" not in sys.modules:
    groq_stub = types.ModuleType("groq")

    class _Groq:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class _AsyncGroq(_Groq):  # pragma: no cover - import shim only
        pass

    groq_stub.Groq = _Groq  # type: ignore[attr-defined]
    groq_stub.AsyncGroq = _AsyncGroq  # type: ignore[attr-defined]
    sys.modules["groq"] = groq_stub

try:
    _cerebras_spec = importlib.util.find_spec("cerebras.cloud.sdk")
except ModuleNotFoundError:
    _cerebras_spec = None

if _cerebras_spec is None:
    cerebras_stub = types.ModuleType("cerebras")
    cerebras_cloud_stub = types.ModuleType("cerebras.cloud")
    cerebras_sdk_stub = types.ModuleType("cerebras.cloud.sdk")

    class _Cerebras:  # pragma: no cover - import shim only
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class _AsyncCerebras(_Cerebras):  # pragma: no cover - import shim only
        pass

    cerebras_sdk_stub.Cerebras = _Cerebras  # type: ignore[attr-defined]
    cerebras_sdk_stub.AsyncCerebras = _AsyncCerebras  # type: ignore[attr-defined]
    sys.modules["cerebras"] = cerebras_stub
    sys.modules["cerebras.cloud"] = cerebras_cloud_stub
    sys.modules["cerebras.cloud.sdk"] = cerebras_sdk_stub

OPTIONAL_MODULES = [
    "sentence_transformers",
    "fitz",
    "pymupdf4llm",
    "pypdfium2",
    "docling",
    "pypdf",
    "pdf2image",
    "pytesseract",
    "unstructured",
    "markitdown",
    "marker",
    "trafilatura",
    "firecrawl",
    "exa_py",
    "crawl4ai",
    "chromadb",
    "lancedb",
    "qdrant_client",
    "weaviate",
    "pinecone",
    "meilisearch_python_sdk",
    "sqlalchemy",
    "pgvector",
]

OPTIONAL_BINARIES = ["tesseract", "pdftoppm", "marker_single"]


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def probe_modules() -> dict[str, bool]:
    return {name: module_available(name) for name in OPTIONAL_MODULES}


def probe_binaries() -> dict[str, str | None]:
    return {name: shutil.which(name) for name in OPTIONAL_BINARIES}


def build_report(probe_local_backends: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "ok": False,
        "core_import_error": None,
        "construction_errors": {},
        "defaults_ok": None,
        "defaults": {},
        "objects": {},
        "optional_modules": probe_modules(),
        "optional_binaries": probe_binaries(),
        "local_backend_probes": {},
    }

    try:
        from langroid.agent.special.doc_chat_agent import DocChatAgentConfig
        from langroid.embedding_models.models import OpenAIEmbeddingsConfig
        from langroid.mytypes import DocMetaData, Document
        from langroid.parsing.file_attachment import FileAttachment
        from langroid.parsing.parser import ParsingConfig, PdfParsingConfig, Splitter
        from langroid.parsing.url_loader import URLLoader
        from langroid.utils.output.citations import (
            extract_markdown_references,
            format_cited_references,
        )
        from langroid.vector_store.base import VectorStoreConfig
        from langroid.vector_store.chromadb import ChromaDB, ChromaDBConfig
        from langroid.vector_store.lancedb import LanceDB, LanceDBConfig
        from langroid.vector_store.qdrantdb import QdrantDB, QdrantDBConfig
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["core_import_error"] = repr(exc)
        return report

    docchat_fields = DocChatAgentConfig.model_fields
    vector_fields = VectorStoreConfig.model_fields

    report["defaults"] = {
        "docchat_n_relevant_chunks": docchat_fields["n_relevant_chunks"].default,
        "docchat_n_similar_chunks": docchat_fields["n_similar_chunks"].default,
        "docchat_use_bm25_search": docchat_fields["use_bm25_search"].default,
        "docchat_use_fuzzy_match": docchat_fields["use_fuzzy_match"].default,
        "pdf_library": PdfParsingConfig.model_fields["library"].default,
        "vectorstore_full_eval": vector_fields["full_eval"].default,
    }
    report["defaults_ok"] = (
        docchat_fields["n_relevant_chunks"].default == 3
        and docchat_fields["n_similar_chunks"].default == 3
        and docchat_fields["use_bm25_search"].default is True
        and docchat_fields["use_fuzzy_match"].default is True
        and PdfParsingConfig.model_fields["library"].default == "pypdfium2"
        and vector_fields["full_eval"].default is False
    )

    parsing_cfg = None
    vector_cfg = None

    try:
        parsing_cfg = ParsingConfig.model_construct(
            splitter=Splitter.MARKDOWN,
            pdf=PdfParsingConfig.model_construct(library="pypdfium2"),
        )
        report["objects"]["parsing_config"] = {
            "splitter": parsing_cfg.splitter,
            "pdf_library": parsing_cfg.pdf.library,
        }
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["construction_errors"]["parsing_config"] = repr(exc)

    try:
        vector_cfg = QdrantDBConfig.model_construct(
            cloud=False,
            collection_name=None,
            storage_path=".rag-smoke/qdrant",
            embedding=OpenAIEmbeddingsConfig.model_construct(
                model_type="openai",
                model_name="text-embedding-3-small",
                dims=1536,
            ),
        )
        report["objects"]["vector_config"] = {
            "class": vector_cfg.__class__.__name__,
            "cloud": vector_cfg.cloud,
            "collection_name": vector_cfg.collection_name,
            "storage_path": vector_cfg.storage_path,
        }
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["construction_errors"]["vector_config"] = repr(exc)

    try:
        if parsing_cfg is None or vector_cfg is None:
            raise RuntimeError("Missing prerequisite config")
        docchat_cfg = DocChatAgentConfig.model_construct(
            vecdb=vector_cfg,
            parsing=parsing_cfg,
        )
        report["objects"]["docchat_config"] = {
            "vecdb": docchat_cfg.vecdb.__class__.__name__,
            "parsing_splitter": docchat_cfg.parsing.splitter,
            "parsing_pdf_library": docchat_cfg.parsing.pdf.library,
        }
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["construction_errors"]["docchat_config"] = repr(exc)

    try:
        attachment = FileAttachment.from_text(
            "Retrieval smoke check",
            filename="smoke.txt",
        )
        attachment_payload = attachment.to_dict("gpt-4o")
        report["objects"]["file_attachment"] = {
            "filename": attachment.filename,
            "payload_type": attachment_payload["type"],
        }
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["construction_errors"]["file_attachment"] = repr(exc)

    try:
        passages = [
            Document(
                content="Alpha passage",
                metadata=DocMetaData(source="alpha"),
            )
        ]
        citation_ids = extract_markdown_references("A claim with [^1].")
        full_citations, brief_citations = format_cited_references(
            citation_ids, passages
        )
        report["objects"]["citation_helpers"] = {
            "extract_markdown_references": citation_ids,
            "citations_brief": brief_citations,
            "citations_full_lines": (
                len(full_citations.splitlines()) if full_citations else 0
            ),
        }
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["construction_errors"]["citation_helpers"] = repr(exc)

    try:
        if parsing_cfg is None:
            raise RuntimeError("Missing parsing config")
        url_loader = URLLoader(urls=[], parsing_config=parsing_cfg)
        report["objects"]["url_loader"] = {
            "crawler": url_loader.crawler.__class__.__name__,
            "needs_parser": getattr(url_loader.crawler, "needs_parser", None),
        }
    except Exception as exc:  # pragma: no cover - surfaced in report
        report["construction_errors"]["url_loader"] = repr(exc)

    if probe_local_backends:
        tmp_root = Path(tempfile.mkdtemp(prefix="rag-smoke-local-"))
        backend_results: dict[str, Any] = {}
        try:
            backend_specs = [
                (
                    "qdrant",
                    QdrantDB,
                    QdrantDBConfig.model_construct(
                        cloud=False,
                        collection_name="probe",
                        storage_path=str(tmp_root / "qdrant"),
                        embedding=OpenAIEmbeddingsConfig.model_construct(
                            model_type="openai",
                            model_name="text-embedding-3-small",
                            dims=1536,
                        ),
                    ),
                ),
                (
                    "lancedb",
                    LanceDB,
                    LanceDBConfig.model_construct(
                        cloud=False,
                        collection_name="probe",
                        storage_path=str(tmp_root / "lance"),
                        embedding=OpenAIEmbeddingsConfig.model_construct(
                            model_type="openai",
                            model_name="text-embedding-3-small",
                            dims=1536,
                        ),
                    ),
                ),
                (
                    "chromadb",
                    ChromaDB,
                    ChromaDBConfig.model_construct(
                        collection_name="probe",
                        storage_path=str(tmp_root / "chroma"),
                        embedding=OpenAIEmbeddingsConfig.model_construct(
                            model_type="openai",
                            model_name="text-embedding-3-small",
                            dims=1536,
                        ),
                    ),
                ),
            ]
            for name, cls, cfg in backend_specs:
                try:
                    store = cls(cfg)
                    backend_results[name] = {
                        "ok": True,
                        "class": store.__class__.__name__,
                        "collection_name": getattr(store.config, "collection_name", None),
                    }
                    if hasattr(store, "close"):
                        store.close()
                except Exception as exc:  # pragma: no cover - surfaced in report
                    backend_results[name] = {"ok": False, "error": repr(exc)}
        finally:
            shutil.rmtree(tmp_root, ignore_errors=True)
        report["local_backend_probes"] = backend_results

    report["ok"] = (
        report["core_import_error"] is None
        and bool(report["defaults_ok"])
        and not report["construction_errors"]
    )
    return report


def format_human_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("DocChat retrieval smoke report")
    lines.append(f"core_import_error: {report['core_import_error']}")
    lines.append(f"construction_errors: {report.get('construction_errors')}")
    lines.append(f"defaults_ok: {report['defaults_ok']}")
    lines.append("defaults:")
    for key, value in sorted(report["defaults"].items()):
        lines.append(f"  - {key}: {value}")
    lines.append("optional_modules:")
    for key, value in sorted(report["optional_modules"].items()):
        lines.append(f"  - {key}: {'ok' if value else 'missing'}")
    lines.append("optional_binaries:")
    for key, value in sorted(report["optional_binaries"].items()):
        lines.append(f"  - {key}: {value or 'missing'}")
    if report["objects"]:
        lines.append("objects:")
        for key, value in report["objects"].items():
            lines.append(f"  - {key}: {value}")
    if report["local_backend_probes"]:
        lines.append("local_backend_probes:")
        for key, value in report["local_backend_probes"].items():
            lines.append(f"  - {key}: {value}")
    lines.append(f"ok: {report['ok']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check retrieval-doc-chat configs, parsers, vector-store "
            "objects, attachments, and citation helpers without provider calls."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    parser.add_argument(
        "--probe-local-backends",
        action="store_true",
        help="instantiate safe local vector-store backends in temp dirs",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return a non-zero status if a core import or default check fails",
    )
    args = parser.parse_args(argv)

    report = build_report(probe_local_backends=args.probe_local_backends)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        print(format_human_report(report))

    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
