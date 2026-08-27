#!/usr/bin/env python3
"""Bundled Data-Juicer API service entrypoint.

This version discovers modules from the installed `data_juicer` package,
so it works without a source checkout.
"""

from __future__ import annotations

import datetime
import importlib
import inspect
import json
import logging
import os
import pkgutil
from typing import Dict
from urllib.parse import parse_qs

from pydantic import validate_call

from data_juicer.config.config import get_default_cfg, get_init_configs
from data_juicer.core.data.dataset_builder import DatasetBuilder
from data_juicer.core.exporter import Exporter
from data_juicer.utils.lazy_loader import LazyLoader

fastapi = LazyLoader("fastapi")

DJ_OUTPUT = os.environ.get("DJ_OUTPUT", "outputs")

allowed_methods = {
    "run",
    "process",
    "compute_stats",
    "compute_hash",
    "analyze",
    "compute",
    "process_single",
    "process_batched",
    "compute_stats_single",
    "compute_stats_batched",
}

logger = logging.getLogger("uvicorn.error")
app = fastapi.FastAPI()


def _iter_package_modules(package_name: str):
    package = importlib.import_module(package_name)
    yield package
    if not hasattr(package, "__path__"):
        return
    prefix = package.__name__ + "."
    for module_info in pkgutil.walk_packages(package.__path__, prefix=prefix):
        if module_info.ispkg:
            try:
                yield importlib.import_module(module_info.name)
            except Exception as exc:  # pragma: no cover - import best effort
                logger.debug("Skipping %s: %s", module_info.name, exc)


def register_objects_from_package(package_name: str = "data_juicer"):
    """Register public classes and functions from installed package modules."""

    for module in _iter_package_modules(package_name):
        if hasattr(module, "__all__"):
            for name in module.__all__:
                obj = getattr(module, name, None)
                if inspect.isclass(obj):
                    register_class(module, obj)
                elif callable(obj):
                    register_function(module, obj)


def register_class(module, cls):
    """Register a class and selected methods as POST endpoints."""

    def create_class_call(cls, method_name: str):
        async def class_call(request: "fastapi.Request"):
            try:
                cls.__init__ = validate_call(cls.__init__, config=dict(arbitrary_types_allowed=True))
                init_args = await request.json() if await request.body() else {}
                instance = cls(**_setup_cfg(init_args))
                method = validate_call(getattr(instance, method_name), config=dict(arbitrary_types_allowed=True))
                result = _invoke(method, request)
                return {"status": "success", "result": result}
            except Exception as exc:
                raise fastapi.HTTPException(status_code=500, detail=str(exc))

        return class_call

    module_path = module.__name__.replace(".", os.sep)
    cls_name = cls.__name__
    for method_name in _get_public_methods(cls, allowed_methods):
        api_path = f"/{module_path}/{cls_name}/{method_name}"
        app.add_api_route(api_path, create_class_call(cls, method_name), methods=["POST"], tags=["POST"])
        logger.debug("Registered %s", api_path)


def register_function(module, func):
    """Register a function as a GET endpoint."""

    def create_func_call(func):
        async def func_call(request: "fastapi.Request"):
            try:
                nonlocal func
                func = validate_call(func, config=dict(arbitrary_types_allowed=True))
                result = _invoke(func, request)
                return {"status": "success", "result": result}
            except Exception as exc:
                raise fastapi.HTTPException(status_code=500, detail=str(exc))

        return func_call

    module_path = module.__name__.replace(".", os.sep)
    api_path = f"/{module_path}/{func.__name__}"
    app.add_api_route(api_path, create_func_call(func), methods=["GET"], tags=["GET"])
    logger.debug("Registered %s", api_path)


def _get_public_methods(cls, allowed_methods):
    return [name for name in allowed_methods if hasattr(cls, name)]


def _invoke(callable_obj, request):
    q_params = parse_qs(request.url.query, keep_blank_values=True)
    d_params = dict((k, v if len(v) > 1 else v[0]) for k, v in q_params.items())
    d_params = _parse_json_dumps(d_params)
    d_params = _setup_cfg(d_params)
    exporter = _setup_dataset(d_params)
    skip_return = d_params.pop("skip_return", False)
    result = callable_obj(**d_params)
    if exporter is not None:
        exporter.export(result)
        result = exporter.export_path
    if skip_return:
        result = ""
    return result


def _parse_json_dumps(params: Dict, prefix="<json_dumps>"):
    for key, value in params.items():
        if isinstance(value, str) and value.startswith(prefix):
            params[key] = json.loads(value[len(prefix) :])
    return params


def _setup_cfg(params: Dict):
    cfg_val = params.get("cfg")
    if cfg_val is not None and isinstance(cfg_val, (str, dict)):
        if isinstance(cfg_val, str):
            cfg_val = json.loads(cfg_val)
        params["cfg"] = get_init_configs(cfg_val, load_configs_only=True)
    return params


def _setup_dataset(params: Dict):
    exporter = None
    dataset_path = params.get("dataset")
    if dataset_path and isinstance(dataset_path, str):
        cfg = get_default_cfg()
        cfg.dataset_path = dataset_path
        builder = DatasetBuilder(cfg)
        dataset = builder.load_dataset()
        params["dataset"] = dataset
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = os.path.join(DJ_OUTPUT, timestamp, "processed_data.jsonl")
        exporter = Exporter(
            export_path,
            keep_stats_in_res_ds=True,
            keep_hashes_in_res_ds=True,
            export_stats=False,
        )
    return exporter


register_objects_from_package("data_juicer")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
