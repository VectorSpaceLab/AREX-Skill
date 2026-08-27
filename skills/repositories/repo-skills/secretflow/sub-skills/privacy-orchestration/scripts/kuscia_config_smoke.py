#!/usr/bin/env python3
"""Tiny SecretFlow Kuscia/config smoke helper.

This helper only imports the Kuscia adapters and prints the key helper
signatures. It is safe to run without a Kuscia cluster.
"""

import inspect

from secretflow.kuscia.entry import convert_domain_data_to_individual_table
from secretflow.kuscia.sf_config import get_sf_cluster_config
from secretflow.kuscia.task_config import KusciaTaskConfig


def main() -> int:
    print(f"KusciaTaskConfig.from_json: {inspect.signature(KusciaTaskConfig.from_json)}")
    print(f"get_sf_cluster_config: {inspect.signature(get_sf_cluster_config)}")
    print(
        "convert_domain_data_to_individual_table: "
        f"{inspect.signature(convert_domain_data_to_individual_table)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
