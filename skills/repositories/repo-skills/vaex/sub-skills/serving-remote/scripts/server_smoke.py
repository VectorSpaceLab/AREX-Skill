#!/usr/bin/env python3
"""Safe Vaex server/FastAPI smoke check.

Default mode uses FastAPI TestClient against the installed
``vaex.server.fastapi.app`` and queries ``GET /dataset`` without starting a
Uvicorn/Tornado listener. Pass ``--histogram`` for a tiny optional histogram
route check, or ``--skip-route-checks`` to stop after import/help diagnostics.

Import boundary: Vaex's FastAPI module initializes server globals at import time
and may normally initialize example-data/cache state. This helper sets temporary
Vaex data/cache settings and patches ``vaex.example`` before importing the app so
its own route checks use tiny in-memory data instead of public network services
or persistent user cache locations.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check vaex.server.fastapi with FastAPI TestClient and tiny "
            "in-memory datasets. No network listener is started."
        ),
        epilog=(
            "By default the script imports vaex.server.fastapi, replaces the "
            "server dataset registry with tiny in-memory DataFrames, and calls "
            "GET /dataset. Use --histogram for a tiny /histogram check. Use "
            "--skip-route-checks when importing/help is enough or TestClient "
            "dependencies are unavailable."
        ),
    )
    parser.add_argument(
        "--skip-route-checks",
        "--import-only",
        dest="route_checks",
        action="store_false",
        help="Import vaex.server.fastapi but skip FastAPI TestClient route checks.",
    )
    parser.set_defaults(route_checks=True)
    parser.add_argument(
        "--server-help",
        action="store_true",
        help=(
            "Also run `python -m vaex server --help` in a subprocess with the "
            "same temporary Vaex environment."
        ),
    )
    parser.add_argument(
        "--histogram",
        action="store_true",
        help="Also query GET and POST /histogram with tiny-safe defaults.",
    )
    parser.add_argument(
        "--heatmap",
        action="store_true",
        help="Also query GET and POST /heatmap with tiny-safe defaults.",
    )
    parser.add_argument(
        "--dataset-metadata",
        action="store_true",
        help="Also query GET /dataset/{id} for the tiny example dataset.",
    )
    parser.add_argument(
        "--include-plot-endpoints",
        action="store_true",
        help="Also check PNG plot endpoints. Requires plotting dependencies.",
    )
    parser.add_argument(
        "--include-openapi",
        action="store_true",
        help="Also check /docs and /openapi.json.",
    )
    parser.add_argument(
        "--dataset",
        default="example",
        help="Tiny dataset name used for optional histogram checks. Default: %(default)s.",
    )
    parser.add_argument(
        "--expression",
        default="x",
        help="Expression used for optional histogram checks. Default: %(default)s.",
    )
    parser.add_argument(
        "--shape",
        type=int,
        default=4,
        help="Histogram bin count for optional checks. Default: %(default)s.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Subprocess timeout in seconds for --server-help. Default: %(default)s.",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output.")
    return parser.parse_args(argv)


def _json_default(value: Any) -> Any:
    try:
        import numpy as np  # type: ignore
    except Exception:  # pragma: no cover - numpy import failure is reported elsewhere
        np = None  # type: ignore
    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            return value.tolist()
    if hasattr(value, "as_py"):
        return value.as_py()
    if isinstance(value, Path):
        return str(value)
    return str(value)


def _tiny_dataframe(name: str, length: int, offset: float = 0.0):
    import numpy as np
    import vaex

    base = np.arange(length, dtype="float64") + offset
    df = vaex.from_arrays(
        x=base,
        y=base * 2,
        group=np.array(["even" if i % 2 == 0 else "odd" for i in range(length)]),
    )
    df.name = name
    return df


def _response_summary(response) -> Dict[str, Any]:
    return {
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type"),
        "x_process_time": response.headers.get("x-process-time"),
        "x_data_passes": response.headers.get("x-data-passes"),
    }


def _assert_status(response, expected: int, label: str) -> None:
    if response.status_code != expected:
        raise AssertionError(
            f"{label} returned HTTP {response.status_code}, expected {expected}: {response.text[:1000]}"
        )


def _assert_png(response, label: str) -> None:
    _assert_status(response, 200, label)
    if not response.content.startswith(b"\x89PNG") or len(response.content) < 100:
        raise AssertionError(f"{label} did not return non-empty PNG content")


def _excerpt(text: str, limit: int = 1000) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...<truncated {len(text) - limit} chars>"


def _run_server_help(env: Dict[str, str], timeout: float) -> Dict[str, Any]:
    completed = subprocess.run(
        [sys.executable, "-m", "vaex", "server", "--help"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
        check=False,
    )
    return {
        "returncode": completed.returncode,
        "stdout_excerpt": _excerpt(completed.stdout),
        "stderr_excerpt": _excerpt(completed.stderr),
        "contains_expected_flags": all(
            flag in completed.stdout
            for flag in ["--add-example", "--host", "--base-url", "--port", "--verbose", "--quiet", "--graphql"]
        ),
    }


def _prepare_vaex_environment(temp_root: Path) -> Dict[str, str]:
    env = os.environ.copy()
    env["VAEX_HOME"] = str(temp_root / "vaex-home")
    env["VAEX_DATA_PATH"] = str(temp_root / "vaex-data")
    env["VAEX_CACHE_PATH"] = str(temp_root / "vaex-cache")
    env["VAEX_FS_PATH"] = str(temp_root / "vaex-fs-cache")
    for key, value in env.items():
        if key.startswith("VAEX_"):
            os.environ[key] = value
    return env


def _ensure_matplotlib_compat() -> None:
    try:
        import matplotlib
    except Exception:
        return
    if not hasattr(matplotlib.cm, "get_cmap") and hasattr(matplotlib, "colormaps"):
        matplotlib.cm.get_cmap = matplotlib.colormaps.get_cmap  # type: ignore[attr-defined]


def _import_fastapi_module() -> Any:
    import vaex

    original_example = getattr(vaex, "example", None)

    def deterministic_example():
        return _tiny_dataframe("example", length=10, offset=0.0)

    # vaex.server.fastapi may call vaex.example() at import time. Patch it first
    # so app initialization uses tiny in-memory data rather than external example
    # acquisition or persistent cache state.
    vaex.example = deterministic_example  # type: ignore[assignment]
    if hasattr(vaex, "settings") and hasattr(vaex.settings, "server"):
        try:
            vaex.settings.server.files = {}
        except Exception:
            pass
        try:
            vaex.settings.server.graphql = False
        except Exception:
            pass

    try:
        import vaex.server.fastapi as vf
    finally:
        if original_example is not None:
            vaex.example = original_example  # type: ignore[assignment]
    return vf


def _install_tiny_datasets(vf: Any) -> Dict[str, Any]:
    datasets = {
        "example": _tiny_dataframe("example", length=12, offset=0.0),
        "second": _tiny_dataframe("second", length=8, offset=100.0),
    }
    vf.datasets.clear()
    vf.datasets.update({name: df.dataset for name, df in datasets.items()})
    vf.update_service(datasets)
    return datasets


def _check_dataset_list(client, expected_names: List[str]) -> Dict[str, Any]:
    response = client.get("/dataset")
    _assert_status(response, 200, "GET /dataset")
    names = response.json()
    if set(names) != set(expected_names):
        raise AssertionError(f"unexpected dataset list: {names!r}")
    return {**_response_summary(response), "json": names}


def _check_dataset_metadata(client, dataset: str, expected_rows: int) -> Dict[str, Any]:
    response = client.get(f"/dataset/{dataset}")
    _assert_status(response, 200, f"GET /dataset/{dataset}")
    metadata = response.json()
    if metadata.get("id") != dataset or metadata.get("row_count") != expected_rows:
        raise AssertionError(f"unexpected dataset metadata: {metadata!r}")
    for required_column in ["x", "y", "group"]:
        if required_column not in metadata.get("schema", {}):
            raise AssertionError(f"missing {required_column!r} in schema: {metadata!r}")
    return {**_response_summary(response), "json": metadata}


def _check_histogram(client, dataset: str, expression: str, shape: int) -> Dict[str, Any]:
    payload = {
        "dataset_id": dataset,
        "expression": expression,
        "min": 0,
        "max": 12,
        "shape": shape,
        "filter": None,
        "virtual_columns": {},
    }
    response = client.post("/histogram", json=payload)
    _assert_status(response, 200, "POST /histogram")
    histogram_post = response.json()
    if histogram_post.get("dataset_id") != dataset or len(histogram_post.get("centers", [])) != shape or len(histogram_post.get("values", [])) != shape:
        raise AssertionError(f"unexpected histogram POST response: {histogram_post!r}")

    response_get = client.get(f"/histogram/{dataset}/{expression}?min=0&max=12&shape={shape}")
    _assert_status(response_get, 200, f"GET /histogram/{dataset}/{expression}")
    histogram_get = response_get.json()
    if histogram_get.get("values") != histogram_post.get("values"):
        raise AssertionError(f"GET/POST histogram mismatch: {histogram_get!r} vs {histogram_post!r}")
    return {
        "post": {**_response_summary(response), "json": histogram_post},
        "get": {**_response_summary(response_get), "json": histogram_get},
    }


def _check_heatmap(client) -> Dict[str, Any]:
    payload = {
        "dataset_id": "second",
        "expression_x": "x",
        "expression_y": "y",
        "min_x": 100,
        "max_x": 108,
        "min_y": 200,
        "max_y": 216,
        "shape_x": 4,
        "shape_y": 4,
        "filter": None,
        "virtual_columns": {"sum_xy": "x + y"},
    }
    response = client.post("/heatmap", json=payload)
    _assert_status(response, 200, "POST /heatmap")
    heatmap_post = response.json()
    values = heatmap_post.get("values", [])
    if (
        heatmap_post.get("dataset_id") != "second"
        or len(heatmap_post.get("centers_x", [])) != 4
        or len(heatmap_post.get("centers_y", [])) != 4
        or len(values) != 4
        or any(len(row) != 4 for row in values)
    ):
        raise AssertionError(f"unexpected heatmap POST response: {heatmap_post!r}")

    response_get = client.get("/heatmap/second/x/y?min_x=100&max_x=108&min_y=200&max_y=216&shape_x=4&shape_y=4")
    _assert_status(response_get, 200, "GET /heatmap/second/x/y")
    heatmap_get = response_get.json()
    if heatmap_get.get("values") != heatmap_post.get("values"):
        raise AssertionError(f"GET/POST heatmap mismatch: {heatmap_get!r} vs {heatmap_post!r}")
    return {
        "post": {**_response_summary(response), "json": heatmap_post},
        "get": {**_response_summary(response_get), "json": heatmap_get},
    }


def run_smoke(args: argparse.Namespace) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="vaex-server-smoke-") as temp_dir:
        env = _prepare_vaex_environment(Path(temp_dir))
        report: Dict[str, Any] = {
            "ok": False,
            "route_checks_requested": args.route_checks,
            "warnings": [
                "No Uvicorn/Tornado listener is started.",
                "Temporary Vaex home/data/cache settings are used only inside this process.",
                "Importing vaex.server.fastapi normally initializes server globals; this helper patches vaex.example before import for tiny local data.",
            ],
            "checks": {},
        }

        if args.server_help:
            report["checks"]["server_help"] = _run_server_help(env, args.timeout)

        _ensure_matplotlib_compat()
        vf = _import_fastapi_module()
        report["checks"]["fastapi_import"] = {"passed": True, "app_type": type(vf.app).__name__}

        if not args.route_checks:
            report["ok"] = True
            report["checks"]["routes"] = {"skipped": True}
            return report

        from fastapi.testclient import TestClient

        datasets = _install_tiny_datasets(vf)
        client = TestClient(vf.app, raise_server_exceptions=True)
        report["checks"]["dataset_list"] = _check_dataset_list(client, list(datasets))

        if args.dataset_metadata:
            report["checks"]["dataset_metadata"] = _check_dataset_metadata(client, "example", expected_rows=12)

        response = client.get("/dataset/does-not-exist")
        _assert_status(response, 404, "GET /dataset/does-not-exist")
        report["checks"]["dataset_404"] = _response_summary(response)

        if args.histogram:
            if args.dataset not in datasets:
                raise AssertionError(f"--dataset {args.dataset!r} is not one of {sorted(datasets)!r}")
            report["checks"]["histogram"] = _check_histogram(client, args.dataset, args.expression, args.shape)

        if args.heatmap:
            report["checks"]["heatmap"] = _check_heatmap(client)

        if args.include_plot_endpoints:
            response = client.get("/histogram.plot/example/x?min=0&max=12&shape=4")
            _assert_png(response, "GET /histogram.plot/example/x")
            report["checks"]["histogram_plot"] = {**_response_summary(response), "bytes": len(response.content)}

            response = client.get("/heatmap.plot/second/x/y?min_x=100&max_x=108&min_y=200&max_y=216&shape_x=4&shape_y=4")
            _assert_png(response, "GET /heatmap.plot/second/x/y")
            report["checks"]["heatmap_plot"] = {**_response_summary(response), "bytes": len(response.content)}

        if args.include_openapi:
            response = client.get("/docs")
            _assert_status(response, 200, "GET /docs")
            report["checks"]["docs"] = _response_summary(response)

            response = client.get("/openapi.json")
            _assert_status(response, 200, "GET /openapi.json")
            openapi = response.json()
            report["checks"]["openapi"] = {
                **_response_summary(response),
                "title": openapi.get("info", {}).get("title"),
                "path_count": len(openapi.get("paths", {})),
            }

        report["ok"] = True
        return report


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_smoke(args)
    except Exception as exc:  # noqa: BLE001 - command-line diagnostic
        failure = {"ok": False, "error_type": type(exc).__name__, "error": str(exc)}
        print(json.dumps(failure, indent=2 if args.pretty else None, sort_keys=True))
        return 1

    print(json.dumps(summary, default=_json_default, indent=2 if args.pretty else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
