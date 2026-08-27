#!/usr/bin/env python3
"""Object-level smoke checks for Towhee APIService.

This script intentionally avoids starting HTTP/gRPC servers, Docker, Triton, or
GPU work. By default it verifies direct APIService route construction. Pass
``--with-pipeline`` to additionally build a service from a tiny local Towhee
RuntimePipeline.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _dump_model(model: Any) -> dict:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    raise TypeError(f"Object is not a Pydantic-like model: {type(model)!r}")


def _import_towhee():
    try:
        from pydantic import BaseModel
        from towhee import api_service
        from towhee.serve.io import JSON
    except ModuleNotFoundError as exc:
        hint = ""
        if exc.name == "pkg_resources":
            hint = (
                " Towhee 1.1.3 imports pkg_resources; use a Towhee-compatible "
                "environment that provides it, such as Python 3.11 with a "
                "setuptools version that still includes pkg_resources."
            )
        raise SystemExit(f"Import failed: {exc}.{hint}") from exc
    return BaseModel, api_service, JSON


def smoke_api_service() -> dict:
    BaseModel, api_service, JSON = _import_towhee()

    class EchoRequest(BaseModel):
        text: str
        repeat: int = 1

    class EchoResponse(BaseModel):
        text: str
        repeated: list[str]

    service = api_service.APIService(desc="Towhee APIService smoke")

    @service.api(path="/echo", input_model=JSON(EchoRequest), output_model=JSON(EchoResponse))
    def echo(item: EchoRequest) -> EchoResponse:
        return EchoResponse(text=item.text, repeated=[item.text] * item.repeat)

    assert service.routers is not None, "APIService did not initialize routers"
    assert len(service.routers) == 1, f"expected one router, got {len(service.routers)}"
    router = service.routers[0]
    assert router.path == "/echo", router.path
    assert router.func is echo, "registered function differs from decorator result"
    assert router.input_model is not None, "missing input JSON wrapper"
    assert router.output_model is not None, "missing output JSON wrapper"

    result = router.func(EchoRequest(text="towhee", repeat=2))
    assert _dump_model(result) == {"text": "towhee", "repeated": ["towhee", "towhee"]}

    return {
        "api_service": "ok",
        "paths": [r.path for r in service.routers],
        "desc": service.desc,
    }


def smoke_build_service_with_pipeline() -> dict:
    BaseModel, api_service, JSON = _import_towhee()  # noqa: F841 - validates same imports
    try:
        from towhee import pipe
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Pipeline import failed: {exc}") from exc

    pipeline = (
        pipe.input("x")
        .map("x", "y", lambda x: x)
        .output("y")
    )
    service = api_service.build_service([(pipeline, "/pipeline-echo")], desc="Pipeline smoke")

    assert service.routers is not None, "build_service did not initialize routers"
    paths = [router.path for router in service.routers]
    assert "/pipeline-echo" in paths, paths
    assert "/pipeline-echo/batch" in paths, paths

    single_router = next(router for router in service.routers if router.path == "/pipeline-echo")
    batch_router = next(router for router in service.routers if router.path == "/pipeline-echo/batch")

    single = single_router.func("one")
    batch = batch_router.func(["a", "b"])

    assert single == [["one"]], single
    assert batch == [[["a"]], [["b"]]], batch

    return {
        "build_service": "ok",
        "paths": paths,
        "single": single,
        "batch": batch,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-pipeline",
        action="store_true",
        help="also build an APIService from a tiny local Towhee RuntimePipeline",
    )
    args = parser.parse_args(argv)

    report = smoke_api_service()
    if args.with_pipeline:
        report.update(smoke_build_service_with_pipeline())

    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
