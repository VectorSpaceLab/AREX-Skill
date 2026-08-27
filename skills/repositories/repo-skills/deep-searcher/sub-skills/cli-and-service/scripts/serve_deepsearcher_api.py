#!/usr/bin/env python3
"""Source-free FastAPI helper for DeepSearcher.

This helper reproduces the public service surface described in the repo skill
without depending on the repository's source `main.py` at runtime. It supports
lazy initialization by default and can eagerly initialize the default provider
stack when the user wants startup failures to surface immediately.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from deepsearcher.configuration import Configuration, init_config
from deepsearcher.offline_loading import load_from_local_files, load_from_website
from deepsearcher.online_query import query


class ProviderConfigRequest(BaseModel):
    feature: str
    provider: str
    config: Dict[str, Any] = Field(default_factory=dict)


SENSITIVE_CONFIG_KEYS = ("api_key", "token", "password", "secret", "credential")


def redact_sensitive_config(value: Any) -> Any:
    """Return a copy of a provider config with credential-like values redacted."""
    if isinstance(value, dict):
        return {
            key: (
                "***REDACTED***"
                if any(marker in str(key).lower() for marker in SENSITIVE_CONFIG_KEYS)
                else redact_sensitive_config(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_sensitive_config(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_sensitive_config(item) for item in value)
    return value


@dataclass
class RuntimeState:
    config: Configuration
    initialized: bool = False


def create_app(
    *,
    config_path: str | None = None,
    enable_cors: bool = False,
    eager_init: bool = False,
) -> FastAPI:
    """Create a DeepSearcher FastAPI app.

    The returned app exposes the same four public routes as the source service:
    /set-provider-config/, /load-files/, /load-website/, and /query/.
    """

    app = FastAPI(title="DeepSearcher API", version="0.0.2")
    state = RuntimeState(
        config=Configuration(config_path) if config_path else Configuration(),
        initialized=False,
    )

    def ensure_initialized() -> None:
        if not state.initialized:
            init_config(state.config)
            state.initialized = True

    if eager_init:
        ensure_initialized()

    @app.post("/set-provider-config/")
    def set_provider_config(request: ProviderConfigRequest):
        try:
            state.initialized = False
            state.config.set_provider_config(request.feature, request.provider, request.config)
            init_config(state.config)
            state.initialized = True
            return {
                "message": "Provider config set successfully",
                "provider": request.provider,
                "config": redact_sensitive_config(request.config),
            }
        except Exception as exc:  # pragma: no cover - exercised through runtime probes
            raise HTTPException(status_code=500, detail=f"Failed to set provider config: {exc}") from exc

    @app.post("/load-files/")
    def load_files(
        paths: Union[str, List[str]] = Body(..., description="Local file paths or directories to load."),
        collection_name: Optional[str] = Body(None, description="Optional destination collection name."),
        collection_description: Optional[str] = Body(None, description="Optional collection description."),
        batch_size: Optional[int] = Body(None, description="Optional batch size."),
    ):
        try:
            ensure_initialized()
            load_kwargs: dict[str, Any] = {
                "paths_or_directory": paths,
                "collection_name": collection_name,
                "collection_description": collection_description,
            }
            if batch_size is not None:
                load_kwargs["batch_size"] = batch_size
            load_from_local_files(**load_kwargs)
            return {"message": "Files loaded successfully."}
        except Exception as exc:  # pragma: no cover - exercised through runtime probes
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/load-website/")
    def load_website(
        urls: Union[str, List[str]] = Body(..., description="Website URLs to crawl and load."),
        collection_name: Optional[str] = Body(None, description="Optional destination collection name."),
        collection_description: Optional[str] = Body(None, description="Optional collection description."),
        batch_size: Optional[int] = Body(None, description="Optional batch size."),
    ):
        try:
            ensure_initialized()
            load_kwargs: dict[str, Any] = {
                "urls": urls,
                "collection_name": collection_name,
                "collection_description": collection_description,
            }
            if batch_size is not None:
                load_kwargs["batch_size"] = batch_size
            load_from_website(**load_kwargs)
            return {"message": "Website loaded successfully."}
        except Exception as exc:  # pragma: no cover - exercised through runtime probes
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/query/")
    def perform_query(
        original_query: str = Query(..., description="Question to ask over the loaded data."),
        max_iter: int = Query(3, description="Maximum number of reflection iterations.", ge=1),
    ):
        try:
            ensure_initialized()
            result_text, _, consume_token = query(original_query, max_iter)
            return {"result": result_text, "consume_token": consume_token}
        except Exception as exc:  # pragma: no cover - exercised through runtime probes
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.state.deepsearcher_state = state
    app.state.deepsearcher_config = state.config
    app.state.deepsearcher_ensure_initialized = ensure_initialized
    return app


app = create_app()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bundled DeepSearcher FastAPI helper.")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the service to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the service to.")
    parser.add_argument("--config-path", default=None, help="Optional configuration YAML path.")
    parser.add_argument("--enable-cors", action="store_true", help="Enable permissive CORS headers.")
    parser.add_argument(
        "--eager-init",
        action="store_true",
        help="Initialize the provider stack before serving so startup errors surface immediately.",
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=("critical", "error", "warning", "info", "debug", "trace"),
        help="Uvicorn log level.",
    )
    return parser.parse_args()


def main() -> int:
    import uvicorn

    args = parse_args()
    runtime_app = create_app(
        config_path=args.config_path,
        enable_cors=args.enable_cors,
        eager_init=args.eager_init,
    )
    uvicorn.run(runtime_app, host=args.host, port=args.port, log_level=args.log_level)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
