#!/usr/bin/env python3
"""Print safe nano-graphrag provider templates or inspect local callable shapes.

This script is safe by default: printing templates and signature checks do not call
provider APIs. Explicit --call-validation is required before a local embedding
callable is executed with sample text.
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import inspect
import sys
import textwrap
from pathlib import Path
from types import ModuleType
from typing import Any

OPENAI_COMPATIBLE_TEMPLATE = r'''
import os
from openai import AsyncOpenAI
from nano_graphrag import GraphRAG
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash

MODEL = os.environ.get("NANO_GRAPHRAG_LLM_MODEL", "your-chat-model")
BASE_URL = os.environ["NANO_GRAPHRAG_LLM_BASE_URL"]
API_KEY = os.environ["NANO_GRAPHRAG_LLM_API_KEY"]

async def openai_compatible_model_if_cache(
    prompt, system_prompt=None, history_messages=None, **kwargs
) -> str:
    if history_messages is None:
        history_messages = []

    hashing_kv: BaseKVStorage | None = kwargs.pop("hashing_kv", None)

    # Optional: set NANO_GRAPHRAG_STRIP_KWARGS="response_format,max_tokens"
    # only for providers that reject those OpenAI-style kwargs.
    for name in os.environ.get("NANO_GRAPHRAG_STRIP_KWARGS", "").split(","):
        if name.strip():
            kwargs.pop(name.strip(), None)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    if hashing_kv is not None:
        args_hash = compute_args_hash(MODEL, messages)
        cached = await hashing_kv.get_by_id(args_hash)
        if cached is not None:
            return cached["return"]

    client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
    response = await client.chat.completions.create(
        model=MODEL,
        messages=messages,
        **kwargs,
    )
    result = response.choices[0].message.content

    if hashing_kv is not None:
        await hashing_kv.upsert({args_hash: {"return": result, "model": MODEL}})
        await hashing_kv.index_done_callback()
    return result

rag = GraphRAG(
    working_dir="./rag-workdir",
    best_model_func=openai_compatible_model_if_cache,
    cheap_model_func=openai_compatible_model_if_cache,
)
'''

OLLAMA_TEMPLATE = r'''
import os
import ollama
from nano_graphrag import GraphRAG
from nano_graphrag.base import BaseKVStorage
from nano_graphrag._utils import compute_args_hash

MODEL = os.environ.get("OLLAMA_MODEL", "qwen2:ctx32k")

async def ollama_model_if_cache(
    prompt, system_prompt=None, history_messages=None, **kwargs
) -> str:
    if history_messages is None:
        history_messages = []

    # Ollama chat does not accept these OpenAI-specific kwargs.
    kwargs.pop("max_tokens", None)
    kwargs.pop("response_format", None)
    hashing_kv: BaseKVStorage | None = kwargs.pop("hashing_kv", None)

    options = kwargs.pop("options", {}) or {}
    options.setdefault("num_ctx", int(os.environ.get("OLLAMA_NUM_CTX", "8192")))

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})

    if hashing_kv is not None:
        args_hash = compute_args_hash(MODEL, messages)
        cached = await hashing_kv.get_by_id(args_hash)
        if cached is not None:
            return cached["return"]

    client_kwargs = {}
    if os.environ.get("OLLAMA_HOST"):
        client_kwargs["host"] = os.environ["OLLAMA_HOST"]
    client = ollama.AsyncClient(**client_kwargs)
    response = await client.chat(
        model=MODEL,
        messages=messages,
        options=options,
        **kwargs,
    )
    result = response["message"]["content"]

    if hashing_kv is not None:
        await hashing_kv.upsert({args_hash: {"return": result, "model": MODEL}})
        await hashing_kv.index_done_callback()
    return result

rag = GraphRAG(
    working_dir="./rag-workdir",
    best_model_func=ollama_model_if_cache,
    cheap_model_func=ollama_model_if_cache,
    best_model_max_async=1,
    cheap_model_max_async=1,
)
'''

LOCAL_EMBEDDING_TEMPLATE = r'''
import os
import numpy as np
from sentence_transformers import SentenceTransformer
from nano_graphrag import GraphRAG
from nano_graphrag._utils import wrap_embedding_func_with_attrs

EMBED_MODEL_NAME = os.environ.get(
    "NANO_GRAPHRAG_EMBED_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)
EMBED_DEVICE = os.environ.get("NANO_GRAPHRAG_EMBED_DEVICE", "cpu")
EMBED_MODEL = SentenceTransformer(EMBED_MODEL_NAME, device=EMBED_DEVICE)

@wrap_embedding_func_with_attrs(
    embedding_dim=EMBED_MODEL.get_sentence_embedding_dimension(),
    max_token_size=EMBED_MODEL.max_seq_length,
)
async def local_embedding(texts: list[str]) -> np.ndarray:
    vectors = EMBED_MODEL.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype=np.float32)

rag = GraphRAG(
    working_dir="./rag-workdir",
    embedding_func=local_embedding,
    embedding_batch_num=16,
    embedding_func_max_async=2,
)
'''


def _print_template(title: str, body: str) -> None:
    print(f"# --- {title} ---")
    print(textwrap.dedent(body).strip())
    print()


def _load_module_from_path(path: Path) -> ModuleType:
    module_name = f"provider_template_user_{abs(hash(path.resolve()))}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def load_symbol(spec: str) -> Any:
    """Load 'module:function' or '/path/to/file.py:function'."""
    if ":" not in spec:
        raise ValueError("Expected SPEC as module:function or /path/file.py:function")
    module_part, symbol_name = spec.rsplit(":", 1)
    if not module_part or not symbol_name:
        raise ValueError("Expected non-empty module/path and symbol name")

    maybe_path = Path(module_part)
    if module_part.endswith(".py") or maybe_path.exists():
        module = _load_module_from_path(maybe_path)
    else:
        module = importlib.import_module(module_part)

    obj: Any = module
    for attr in symbol_name.split("."):
        obj = getattr(obj, attr)
    return obj


def validate_llm(spec: str) -> int:
    obj = load_symbol(spec)
    if not callable(obj):
        print(f"ERROR: {spec} is not callable", file=sys.stderr)
        return 2

    target = getattr(obj, "func", obj)
    sig = inspect.signature(target)
    params = sig.parameters
    has_prompt = "prompt" in params or any(
        p.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for p in params.values()
    )
    has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
    is_async = inspect.iscoroutinefunction(target) or inspect.iscoroutinefunction(obj)

    print(f"callable: {spec}")
    print(f"signature: {sig}")
    print(f"async callable: {is_async}")
    print(f"accepts prompt-like positional arg: {has_prompt}")
    print(f"accepts **kwargs: {has_kwargs}")

    problems = []
    if not is_async:
        problems.append("LLM function should be async because nano-graphrag awaits it")
    if not has_prompt:
        problems.append("LLM function should accept prompt as the first argument")
    if not has_kwargs:
        problems.append("LLM function should accept **kwargs and pop hashing_kv")

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1
    print("LLM shape check passed; no provider call was made.")
    return 0


async def _call_embedding(obj: Any, sample_texts: list[str]) -> int:
    try:
        import numpy as np
    except Exception as exc:  # pragma: no cover - depends on user's env
        print(f"ERROR: numpy is required for call validation: {exc}", file=sys.stderr)
        return 2

    result = obj(sample_texts)
    if inspect.isawaitable(result):
        result = await result

    print(f"returned type: {type(result).__name__}")
    if not isinstance(result, np.ndarray):
        print("ERROR: embedding callable must return numpy.ndarray", file=sys.stderr)
        return 1

    print(f"returned shape: {result.shape}")
    expected_dim = getattr(obj, "embedding_dim", None)
    expected_shape = (len(sample_texts), expected_dim)
    if expected_dim is not None and tuple(result.shape) != expected_shape:
        print(
            f"ERROR: expected shape {expected_shape} from embedding_dim={expected_dim}",
            file=sys.stderr,
        )
        return 1
    if not np.isfinite(result).all():
        print("ERROR: embedding array contains non-finite values", file=sys.stderr)
        return 1
    print("Embedding call validation passed.")
    return 0


def validate_embedding(spec: str, expected_dim: int | None, call_validation: bool, sample_text: str) -> int:
    obj = load_symbol(spec)
    if not callable(obj):
        print(f"ERROR: {spec} is not callable", file=sys.stderr)
        return 2

    embedding_dim = getattr(obj, "embedding_dim", None)
    max_token_size = getattr(obj, "max_token_size", None)
    target = getattr(obj, "func", obj)
    sig = inspect.signature(target)

    print(f"callable: {spec}")
    print(f"signature: {sig}")
    print(f"embedding_dim: {embedding_dim}")
    print(f"max_token_size: {max_token_size}")
    print(f"wrapped async func: {inspect.iscoroutinefunction(target)}")

    problems = []
    if embedding_dim is None:
        problems.append("missing embedding_dim attribute; use wrap_embedding_func_with_attrs")
    if max_token_size is None:
        problems.append("missing max_token_size attribute; use wrap_embedding_func_with_attrs")
    if expected_dim is not None and embedding_dim != expected_dim:
        problems.append(f"embedding_dim {embedding_dim!r} does not match expected {expected_dim}")
    if not inspect.iscoroutinefunction(target):
        problems.append("wrapped embedding implementation should be async")

    if problems:
        for problem in problems:
            print(f"ERROR: {problem}", file=sys.stderr)
        return 1

    if not call_validation:
        print("Embedding attribute check passed; no callable execution was performed.")
        return 0

    return asyncio.run(_call_embedding(obj, [sample_text, sample_text + " again"]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print credential-free nano-graphrag provider skeletons or inspect local "
            "callable shapes. Default behavior never calls provider APIs."
        )
    )
    parser.add_argument(
        "--print-openai-compatible",
        action="store_true",
        help="print an AsyncOpenAI(base_url=...) chat wrapper skeleton",
    )
    parser.add_argument(
        "--print-ollama",
        action="store_true",
        help="print an Ollama chat wrapper skeleton that strips unsupported kwargs",
    )
    parser.add_argument(
        "--print-local-embedding",
        action="store_true",
        help="print a sentence-transformer embedding wrapper skeleton",
    )
    parser.add_argument("--print-all", action="store_true", help="print all templates")
    parser.add_argument(
        "--validate-llm",
        metavar="SPEC",
        help="inspect async LLM callable shape from module:function or /path/file.py:function; does not call it",
    )
    parser.add_argument(
        "--validate-embedding",
        metavar="SPEC",
        help="inspect embedding callable attributes from module:function or /path/file.py:function",
    )
    parser.add_argument(
        "--expected-dim",
        type=int,
        help="expected embedding dimension for --validate-embedding",
    )
    parser.add_argument(
        "--call-validation",
        action="store_true",
        help=(
            "with --validate-embedding, explicitly call the local embedding callable "
            "on sample text; use only for callables known not to contact provider APIs"
        ),
    )
    parser.add_argument(
        "--sample-text",
        default="nano-graphrag provider template validation",
        help="sample text used only with --call-validation",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    printed = False
    if args.print_all or args.print_openai_compatible:
        _print_template("OpenAI-compatible chat wrapper", OPENAI_COMPATIBLE_TEMPLATE)
        printed = True
    if args.print_all or args.print_ollama:
        _print_template("Ollama chat wrapper", OLLAMA_TEMPLATE)
        printed = True
    if args.print_all or args.print_local_embedding:
        _print_template("Local sentence-transformer embedding wrapper", LOCAL_EMBEDDING_TEMPLATE)
        printed = True

    status = 0
    if args.validate_llm:
        status = max(status, validate_llm(args.validate_llm))
    if args.validate_embedding:
        status = max(
            status,
            validate_embedding(
                args.validate_embedding,
                args.expected_dim,
                args.call_validation,
                args.sample_text,
            ),
        )

    if not printed and not args.validate_llm and not args.validate_embedding:
        parser.print_help()
    return status


if __name__ == "__main__":
    raise SystemExit(main())
