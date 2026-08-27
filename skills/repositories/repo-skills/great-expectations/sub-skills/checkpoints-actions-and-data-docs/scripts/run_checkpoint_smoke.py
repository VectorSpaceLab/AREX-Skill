#!/usr/bin/env python3
"""Run a tiny no-network Great Expectations checkpoint smoke workflow.

By default this uses an ephemeral context and no external notification actions.
Pass --with-data-docs to create a temporary file project, configure a local Data
Docs site inside that temporary directory, and run UpdateDataDocsAction only.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny GX validation definition, run it through a checkpoint, "
            "and print JSON signals without Slack, email, network calls, or "
            "destructive writes."
        )
    )
    parser.add_argument(
        "--with-data-docs",
        action="store_true",
        help=(
            "Use a temporary file context, configure a local Data Docs site, and "
            "include UpdateDataDocsAction. The temporary directory is removed "
            "after the summary is printed."
        ),
    )
    parser.add_argument(
        "--result-format",
        choices=["BOOLEAN_ONLY", "BASIC", "SUMMARY", "COMPLETE"],
        default="SUMMARY",
        help="Checkpoint result format. Default: %(default)s.",
    )
    parser.add_argument(
        "--expect-failure",
        action="store_true",
        help="Use data that intentionally fails one expectation so failure-path signals can be inspected.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for the printed summary. Default: %(default)s.",
    )
    return parser


def load_runtime_dependencies() -> tuple[Any, Any]:
    try:
        import pandas as pd
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "This smoke workflow requires pandas because it validates a tiny dataframe. "
            "Install GX with pandas support or add pandas to the environment."
        ) from error

    try:
        import great_expectations as gx
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "This smoke workflow requires great_expectations to be importable in the active Python environment."
        ) from error

    return pd, gx


def make_dataframe(pd: Any, expect_failure: bool) -> Any:
    order_ids = [1001, 1002, 1003]
    if expect_failure:
        order_ids[1] = None
    return pd.DataFrame(
        {
            "order_id": order_ids,
            "amount": [25.0, 80.5, 120.0],
            "status": ["new", "paid", "shipped"],
        }
    )


def make_context(gx: Any, with_data_docs: bool, project_root: Path | None) -> Any:
    if with_data_docs:
        if project_root is None:
            raise ValueError("project_root is required when with_data_docs is true")
        return gx.get_context(mode="file", project_root_dir=project_root)
    return gx.get_context(mode="ephemeral")


def configure_local_data_docs(context: Any) -> str:
    site_name = "local_site"
    existing_sites = set(context.get_site_names()) if hasattr(context, "get_site_names") else set()
    site_config = {
        "class_name": "SiteBuilder",
        "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
        "store_backend": {
            "class_name": "TupleFilesystemStoreBackend",
            "base_directory": "uncommitted/data_docs/local_site/",
        },
    }
    if site_name in existing_sites:
        context.update_data_docs_site(site_name=site_name, site_config=site_config)
    else:
        context.add_data_docs_site(site_name=site_name, site_config=site_config)
    return site_name


def build_validation_definition(gx: Any, context: Any, dataframe: Any) -> Any:
    datasource = context.data_sources.add_pandas(name="checkpoint_smoke_pandas")
    asset = datasource.add_dataframe_asset(name="orders_dataframe")
    batch_definition = asset.add_batch_definition_whole_dataframe(name="whole_dataframe")

    suite = gx.ExpectationSuite(name="checkpoint_smoke_suite")
    suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
    suite.add_expectation(
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="amount",
            min_value=0,
            max_value={"$PARAMETER": "max_amount"},
        )
    )
    suite = context.suites.add(suite)

    validation_definition = gx.ValidationDefinition(
        name="checkpoint_smoke_validation",
        data=batch_definition,
        suite=suite,
    )
    validation_definition = context.validation_definitions.add(validation_definition)

    return validation_definition


def build_checkpoint(gx: Any, validation_definition: Any, result_format: str, data_docs_site: str | None) -> Any:
    actions = []
    if data_docs_site is not None:
        from great_expectations.checkpoint import UpdateDataDocsAction

        actions.append(UpdateDataDocsAction(name="update_local_docs", site_names=[data_docs_site]))

    return gx.Checkpoint(
        name="checkpoint_smoke",
        validation_definitions=[validation_definition],
        actions=actions,
        result_format=result_format,
    )


def summarize_result(result: Any, context: Any, data_docs_site: str | None) -> dict[str, Any]:
    description = result.describe_dict()
    run_results = list(result.run_results.values())
    first_result = run_results[0] if run_results else None
    first_statistics = getattr(first_result, "statistics", {}) if first_result is not None else {}
    docs_urls = []
    if data_docs_site is not None:
        docs_urls = context.get_docs_sites_urls(site_name=data_docs_site, only_if_exists=True)

    return {
        "checkpoint_name": result.name,
        "checkpoint_success": bool(result.success),
        "evaluated_validations": description["statistics"]["evaluated_validations"],
        "successful_validations": description["statistics"]["successful_validations"],
        "unsuccessful_validations": description["statistics"]["unsuccessful_validations"],
        "first_validation_statistics": first_statistics,
        "data_docs_enabled": data_docs_site is not None,
        "data_docs_site_names": context.get_site_names() if hasattr(context, "get_site_names") else [],
        "data_docs_urls_available": [entry for entry in docs_urls if entry.get("site_url")],
        "external_notifications_configured": False,
    }


def run_workflow(args: argparse.Namespace, project_root: Path | None = None) -> dict[str, Any]:
    pd, gx = load_runtime_dependencies()
    dataframe = make_dataframe(pd, expect_failure=args.expect_failure)
    context = make_context(gx, with_data_docs=args.with_data_docs, project_root=project_root)
    data_docs_site = configure_local_data_docs(context) if args.with_data_docs else None

    validation_definition = build_validation_definition(gx, context, dataframe)
    checkpoint = build_checkpoint(
        gx=gx,
        validation_definition=validation_definition,
        result_format=args.result_format,
        data_docs_site=data_docs_site,
    )
    checkpoint = context.checkpoints.add_or_update(checkpoint)
    result = checkpoint.run(
        batch_parameters={"dataframe": dataframe},
        expectation_parameters={"max_amount": 200.0},
    )
    return summarize_result(result=result, context=context, data_docs_site=data_docs_site)


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.with_data_docs:
            with tempfile.TemporaryDirectory(prefix="gx_checkpoint_smoke_") as temp_dir:
                summary = run_workflow(args=args, project_root=Path(temp_dir))
        else:
            summary = run_workflow(args=args)
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    print(json.dumps(summary, indent=args.indent, sort_keys=True, default=str))
    return 0 if summary["checkpoint_success"] or args.expect_failure else 1


if __name__ == "__main__":
    raise SystemExit(main())
