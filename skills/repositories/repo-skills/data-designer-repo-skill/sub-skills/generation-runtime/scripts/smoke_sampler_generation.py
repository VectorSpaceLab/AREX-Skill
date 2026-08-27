#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Deterministic sampler-only smoke check for installed DataDesigner runtime APIs.

This script intentionally imports the installed ``data_designer`` package only.
It never reads a source checkout and never calls a remote model provider. The
smoke exercises the safe local path:

    validate -> check_models -> preview -> create -> export -> result round-trips

The dummy provider exists only because the runtime requires a provider registry;
the sampler-only config has no model aliases, so no request is sent to it.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

import data_designer.config as dd
from data_designer.interface import DataDesigner


def build_sampler_only_builder() -> dd.DataDesignerConfigBuilder:
    builder = dd.DataDesignerConfigBuilder(model_configs=[])
    builder.add_column(
        dd.SamplerColumnConfig(
            name="bucket",
            sampler_type=dd.SamplerType.CATEGORY,
            params=dd.CategorySamplerParams(values=["alpha"]),
        )
    )
    return builder


def make_designer(artifact_root: Path) -> DataDesigner:
    provider = dd.ModelProvider(
        name="sampler-only-smoke",
        endpoint="https://example.invalid/v1",
        provider_type="openai",
        api_key="sampler-only-smoke",
    )
    designer = DataDesigner(
        artifact_path=artifact_root,
        model_providers=[provider],
        auto_configure_logging=False,
    )
    designer.set_run_config(
        dd.RunConfig(
            buffer_size=2,
            display_tui=False,
            async_trace=False,
            write_scheduler_events=False,
            otel_metrics_port=None,
        )
    )
    return designer


def assert_all_alpha(df: Any, *, expected_rows: int) -> None:
    assert len(df) == expected_rows, f"expected {expected_rows} rows, found {len(df)}"
    assert list(df["bucket"]) == ["alpha"] * expected_rows


def run_smoke(*, artifact_root: Path, dataset_name: str, num_records: int) -> dict[str, Any]:
    export_path = artifact_root / "exports" / "sampler-smoke.jsonl"
    export_path.parent.mkdir(parents=True, exist_ok=True)

    designer = make_designer(artifact_root)
    builder = build_sampler_only_builder()

    designer.validate(builder)
    designer.check_models(builder)

    preview_records = min(num_records, 3)
    preview = designer.preview(builder, num_records=preview_records)
    assert preview.dataset is not None
    assert preview.analysis is not None
    assert preview.dataset_metadata is not None
    assert_all_alpha(preview.dataset, expected_rows=preview_records)
    assert preview.to_config_builder().get_seed_config() is not None

    results = designer.create(builder, num_records=num_records, dataset_name=dataset_name)
    assert results.dataset_metadata is not None
    assert results.load_analysis().target_num_records == num_records
    assert results.count_records() == num_records

    dataset = results.load_dataset()
    assert_all_alpha(dataset, expected_rows=num_records)

    roundtrip_builder = results.to_config_builder()
    assert roundtrip_builder.get_seed_config() is not None

    written_export = results.export(export_path)
    assert written_export == export_path
    exported_rows = export_path.read_text(encoding="utf-8").splitlines()
    assert len(exported_rows) == num_records
    for row in exported_rows:
        assert json.loads(row)["bucket"] == "alpha"

    return {
        "status": "ok",
        "dataset_name": dataset_name,
        "num_records": num_records,
        "preview_records": preview_records,
        "artifact_root": str(artifact_root),
        "dataset_path": str(results.artifact_storage.base_dataset_path),
        "export_path": str(export_path),
        "remote_model_calls": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-records", type=int, default=4, help="Number of records to create")
    parser.add_argument("--dataset-name", default="sampler-smoke", help="Dataset directory name")
    parser.add_argument("--artifact-path", type=Path, help="Artifact root; defaults to a temporary directory")
    parser.add_argument("--json", action="store_true", help="Print a JSON report")
    args = parser.parse_args()

    if args.num_records < 1:
        parser.error("--num-records must be positive")

    if args.artifact_path is None:
        artifact_root = Path(tempfile.mkdtemp(prefix="data-designer-sampler-smoke-"))
    else:
        artifact_root = args.artifact_path.expanduser().resolve()
        artifact_root.mkdir(parents=True, exist_ok=True)

    report = run_smoke(artifact_root=artifact_root, dataset_name=args.dataset_name, num_records=args.num_records)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"ok - sampler-only generation smoke passed: {artifact_root}")
        print(f"ok - export written to: {report['export_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
