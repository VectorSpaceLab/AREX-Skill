#!/usr/bin/env python3
"""Probe the local MPI / ChainerMN setup without running a full training job."""

from __future__ import annotations

import argparse
import importlib.util
import shutil


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--create",
        action="store_true",
        help="Try to create a communicator if mpi4py is available",
    )
    parser.add_argument(
        "--communicator",
        default="dummy",
        choices=("dummy", "naive", "flat", "non_cuda_aware", "pure_nccl"),
        help="Communicator name to create when --create is set",
    )
    args = parser.parse_args()

    try:
        import chainer
        import chainermn
    except Exception as exc:
        print(f"chainermn import failed: {exc}")
        return 1

    print(f"chainermn={chainermn.__version__}")
    print(f"chainer.cuda.available={chainer.backends.cuda.available}")
    print(f"mpi4py={_has_module('mpi4py')}")
    print(f"mpiexec={shutil.which('mpiexec') or 'missing'}")
    print(f"mpicc={shutil.which('mpicc') or 'missing'}")

    if not args.create:
        if not _has_module('mpi4py'):
            print("Install mpi4py and a matching MPI runtime before trying a real launch.")
        return 0

    if not _has_module('mpi4py'):
        print("Cannot create a communicator because mpi4py is missing.")
        return 1

    import mpi4py.MPI

    comm = chainermn.create_communicator(args.communicator, mpi_comm=mpi4py.MPI.COMM_WORLD)
    print(f"rank={comm.rank}")
    print(f"size={comm.size}")
    print(f"intra_rank={comm.intra_rank}")
    print(f"inter_rank={comm.inter_rank}")
    print(f"inter_size={comm.inter_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
