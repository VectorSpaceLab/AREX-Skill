#!/usr/bin/env python3
"""Print Composer launcher help without launching a training process."""

from __future__ import annotations

import sys
import warnings


_STATIC_HELP = """usage: composer [-h] [--version] [-n NPROC] [--stdout STDOUT] [--stderr STDERR]
                [-v] [-m] [-c] [--world_size WORLD_SIZE]
                [--base_rank BASE_RANK] [--node_rank NODE_RANK]
                [--master_addr MASTER_ADDR] [--master_port MASTER_PORT]
                training_script ...

Utility for launching distributed machine learning jobs.

required arguments:
  training_script       The path to the training script used to initialize a single
                        training process. Follow with any script arguments.
  training_script_args  Any arguments for the training script.

options:
  -h, --help            show this help message and exit
  --version             show Composer version and exit
  -n NPROC, --nproc NPROC
                        Processes to launch on this node. Overrides LOCAL_WORLD_SIZE;
                        otherwise defaults to max(1, torch.cuda.device_count()).
  --stdout STDOUT       Filename format for non-local-rank-zero stdout. Supports
                        {rank}, {local_rank}, {world_size}, {node_rank}, and
                        {local_world_size}. Include rank placeholders to avoid
                        file collisions.
  --stderr STDERR       Filename format for non-local-rank-zero stderr. Supports
                        the same placeholders as --stdout.
  -v, --verbose         Print verbose launcher messages.
  -m, --module_mode     Run training_script as a Python module. Mutually exclusive
                        with --command_mode.
  -c, --command_mode    Run training_script as a command without prepending Python.
                        Mutually exclusive with --module_mode.

multi-node arguments:
  --world_size WORLD_SIZE
                        Total process count across all nodes. Defaults to nproc.
  --base_rank BASE_RANK
                        Lowest global rank launched on this node.
  --node_rank NODE_RANK
                        Integer node index.
  --master_addr MASTER_ADDR
                        Hostname or IP for the rank-zero C10d TCP store.
  --master_port MASTER_PORT
                        Port for the rank-zero C10d TCP store.

This helper prints help only and never calls the Composer launcher main().
"""


def main() -> int:
    warnings.filterwarnings(
        "ignore",
        message="The pynvml package is deprecated.*",
        category=FutureWarning,
    )

    try:
        from composer.cli.launcher import _get_parser
    except Exception as exc:  # pragma: no cover - environment diagnostic path
        print(
            f"Unable to import Composer launcher parser ({type(exc).__name__}: {exc}); "
            "printing static launcher usage instead.",
            file=sys.stderr,
        )
        print(_STATIC_HELP, end="")
        return 0

    parser = _get_parser()
    parser.prog = "composer"
    print(parser.format_help(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
