#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Safe FastAPI template for serving text2vec embeddings."""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path
from typing import Any, List, Optional


def _discover_repo_root() -> Optional[Path]:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "text2vec" / "__init__.py").is_file():
            return parent
    return None


def _ensure_repo_on_path() -> None:
    repo_root = _discover_repo_root()
    if repo_root is not None:
        repo_root_str = str(repo_root)
        if repo_root_str not in sys.path:
            sys.path.insert(0, repo_root_str)


def _coerce_texts(payload: Any) -> List[str]:
    if isinstance(payload, dict):
        if "input" not in payload:
            raise ValueError("JSON object must contain an 'input' field.")
        raw_input = payload["input"]
    elif isinstance(payload, list):
        raw_input = payload
    else:
        raise ValueError(
            "Body must be a JSON object with 'input' or a raw JSON list of strings."
        )

    if isinstance(raw_input, str):
        texts = [raw_input]
    elif isinstance(raw_input, list):
        texts = raw_input
    else:
        raise ValueError("'input' must be a string or a list of strings.")

    if not texts:
        raise ValueError("At least one input string is required.")
    if not all(isinstance(item, str) for item in texts):
        raise ValueError("All inputs must be strings.")
    return texts


def _load_sentence_model(model_name_or_path: str, device: Optional[str]):
    _ensure_repo_on_path()
    try:
        from text2vec import SentenceModel
    except Exception as exc:  # pragma: no cover - import-time optional dependency failure
        raise ModuleNotFoundError(
            "text2vec is not importable. Install the package or expose the repository root on PYTHONPATH."
        ) from exc

    try:
        return SentenceModel(model_name_or_path=model_name_or_path, device=device)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to initialize SentenceModel from {model_name_or_path!r}. "
            "If this is a remote model id, the first load may download model files; "
            "if this is a local directory, confirm the files are complete."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Serve text2vec embeddings through a FastAPI app template.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--model-name-or-path",
        default="shibing624/text2vec-base-chinese",
        help="Model name or local model directory used by SentenceModel.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind address. Use 0.0.0.0 only when external access is required.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port for the Uvicorn server.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Device passed to SentenceModel, such as cpu, cuda, or cuda:0. Leave unset for auto.",
    )
    return parser


def create_app(model_name_or_path: str, device: Optional[str] = None):
    try:
        from fastapi import FastAPI, HTTPException, Request
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "FastAPI support is unavailable. Install the optional dependencies 'fastapi' and 'uvicorn'."
        ) from exc
    from starlette.concurrency import run_in_threadpool

    app = FastAPI(title="text2vec serving template", version="1.0.0")
    app.state.model_name_or_path = model_name_or_path
    app.state.device = device
    app.state.model = None
    app.state.model_error = None
    app.state.model_lock = threading.Lock()

    def ensure_model_loaded():
        if app.state.model is not None:
            return app.state.model
        if app.state.model_error is not None:
            raise RuntimeError(app.state.model_error)
        with app.state.model_lock:
            if app.state.model is None and app.state.model_error is None:
                try:
                    app.state.model = _load_sentence_model(model_name_or_path, device)
                except Exception as exc:
                    app.state.model_error = str(exc)
                    raise
        if app.state.model_error is not None:
            raise RuntimeError(app.state.model_error)
        return app.state.model

    app.state.ensure_model_loaded = ensure_model_loaded

    @app.get("/")
    async def index():
        return {
            "message": "text2vec serving template",
            "endpoints": ["/healthz", "/readyz", "/warmup", "/emb"],
        }

    @app.get("/healthz")
    async def healthz():
        return {
            "status": "ok",
            "model_name_or_path": app.state.model_name_or_path,
            "device": app.state.device,
            "model_loaded": app.state.model is not None,
        }

    @app.get("/readyz")
    async def readyz():
        if app.state.model_error is not None:
            raise HTTPException(status_code=503, detail=app.state.model_error)
        return {
            "status": "ready" if app.state.model is not None else "not_ready",
            "model_name_or_path": app.state.model_name_or_path,
            "device": app.state.device,
            "model_loaded": app.state.model is not None,
        }

    @app.post("/warmup")
    async def warmup():
        try:
            model = await run_in_threadpool(ensure_model_loaded)
            probe = await run_in_threadpool(
                model.encode,
                ["warmup"],
                normalize_embeddings=True,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        embedding_dim = int(probe.shape[-1])
        return {
            "status": "ok",
            "model_name_or_path": app.state.model_name_or_path,
            "device": app.state.device,
            "model_loaded": True,
            "embedding_dim": embedding_dim,
        }

    @app.post("/emb")
    async def emb(request: Request):
        try:
            payload = await request.json()
        except Exception as exc:
            raise HTTPException(status_code=422, detail="Request body must be valid JSON.") from exc
        try:
            texts = _coerce_texts(payload)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            model = await run_in_threadpool(ensure_model_loaded)
            embeddings = await run_in_threadpool(
                model.encode,
                texts,
                normalize_embeddings=True,
            )
        except Exception as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return {"emb": embeddings.tolist()}

    return app


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "Uvicorn is missing. Install the optional dependencies 'fastapi' and 'uvicorn' to launch the server."
        ) from exc
    app = create_app(args.model_name_or_path, device=args.device)
    uvicorn.run(app=app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
