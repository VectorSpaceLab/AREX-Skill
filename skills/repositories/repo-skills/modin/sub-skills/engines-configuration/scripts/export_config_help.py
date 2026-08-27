#!/usr/bin/env python3
"""Export the installed Modin config catalog to a CSV file."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pandas_pd

import modin.config as cfg


def export_config_help(filename: str) -> int:
    configs_data = []
    default_values = {
        "RayRedisPassword": "random string",
        "CpuCount": "multiprocessing.cpu_count()",
        "NPartitions": "equals to MODIN_CPUS env",
    }
    for objname in sorted(cfg.__all__):
        obj = getattr(cfg, objname)
        if isinstance(obj, type) and issubclass(obj, cfg.Parameter) and not obj.is_abstract:
            data = {
                "Config Name": obj.__name__,
                "Env. Variable Name": getattr(obj, "varname", "not backed by environment"),
                "Default Value": default_values.get(obj.__name__, obj._get_default()),
                "Description": (obj.__doc__ or "").replace("Notes\n-----", "Notes:\n"),
                "Options": obj.choices,
            }
            configs_data.append(data)

    output = Path(filename)
    pandas_pd.DataFrame(
        configs_data,
        columns=[
            "Config Name",
            "Env. Variable Name",
            "Default Value",
            "Description",
            "Options",
        ],
    ).to_csv(output, index=False)
    print(f"Wrote {len(configs_data)} Modin config rows to {output}")
    return len(configs_data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export the installed Modin package's configuration help to a CSV file."
    )
    parser.add_argument("output_path", help="CSV file to create, for example ./modin-configs.csv.")
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output file.")
    args = parser.parse_args()

    out_path = Path(args.output_path)
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} already exists; use --overwrite to replace it")
    export_config_help(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
