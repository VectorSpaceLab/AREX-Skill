#!/usr/bin/env python3
"""Smoke-check Dagster Pythonic config/resource conversion.

The script is intentionally self-contained and only imports dagster. It validates a
small Config, ConfigurableResource, RunConfig, and EnvVar conversion path without
reading secrets from the environment.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a tiny Dagster Config/ConfigurableResource/RunConfig shape "
            "and print EnvVar-safe guidance."
        )
    )
    parser.add_argument(
        "--op-name",
        default="demo_asset",
        help="Node key to use under RunConfig.ops in the rendered shape.",
    )
    parser.add_argument(
        "--resource-key",
        default="api_client",
        help="Resource key to use under RunConfig.resources in the rendered shape.",
    )
    parser.add_argument(
        "--env-var",
        default="DEMO_API_TOKEN",
        help="Environment variable name to reference with dagster.EnvVar without resolving it.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Positive integer value for the sample Config field.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.limit <= 0:
        parser.error("--limit must be a positive integer")

    try:
        import dagster as dg
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(
            "Unable to import dagster. Run this script in an environment where the "
            "dagster package is installed. Original error: " + repr(exc)
        ) from exc

    class DemoConfig(dg.Config):
        table: str
        limit: int
        token: str

    class DemoResource(dg.ConfigurableResource):
        base_url: str
        token: str

        def redacted_summary(self) -> str:
            return f"{self.base_url} token=<deferred>"

    run_config = dg.RunConfig(
        ops={
            args.op_name: DemoConfig(
                table="example_table",
                limit=args.limit,
                token=dg.EnvVar(args.env_var),
            )
        },
        resources={
            args.resource_key: DemoResource(
                base_url="https://example.invalid",
                token=dg.EnvVar(args.env_var),
            )
        },
    )

    rendered: dict[str, Any] = run_config.to_config_dict()
    print(json.dumps(rendered, indent=2, sort_keys=True))
    print()
    print("Guidance:")
    print(
        "- EnvVar values above are intentionally rendered as Dagster env-var config, "
        "not resolved secrets."
    )
    print(
        "- Pass structured objects through dagster.RunConfig when building run config "
        "in Python."
    )
    print(
        "- Use EnvVar.get_value(default=...) only for explicit non-Dagster "
        "environment reads."
    )
    print(
        "- If a nested resource sees a literal variable name, let Dagster manage it "
        "as a typed field."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
