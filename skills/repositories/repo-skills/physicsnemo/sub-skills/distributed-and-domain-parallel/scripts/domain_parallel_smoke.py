#!/usr/bin/env python3
"""Tiny PhysicsNeMo distributed/domain-parallel smoke.

Default mode checks import and CUDA/device facts. Optional `--distributed`
mode is designed to be launched under torchrun/mpirun/srun and can validate a
named 2-D mesh plus an optional tiny scatter/sync path.
"""

from __future__ import annotations

import argparse
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--distributed", action="store_true", help="Expect launcher context and build a mesh.")
    parser.add_argument("--domain-size", type=int, default=1, help="Domain mesh size to use when building a 2-D mesh.")
    parser.add_argument("--check-scatter", action="store_true", help="Attempt a tiny scatter_tensor smoke on CUDA when possible.")
    parser.add_argument("--check-sync", action="store_true", help="Attempt a tiny sync_module_over_mesh smoke on a plain module.")
    args = parser.parse_args()

    import torch
    from physicsnemo.distributed import DistributedManager
    from physicsnemo.domain_parallel import scatter_tensor, sync_module_over_mesh
    from physicsnemo.models.mlp import FullyConnected

    DistributedManager.initialize()
    dm = DistributedManager()
    torch.cuda.set_device(dm.device)

    payload: dict[str, object] = {
        "python": sys.version.split()[0],
        "world_size": dm.world_size,
        "rank": dm.rank,
        "local_rank": dm.local_rank,
        "device": str(dm.device),
        "cuda_available": torch.cuda.is_available(),
        "cuda_device_count": torch.cuda.device_count(),
    }

    if args.distributed and dm.world_size > 1:
        if args.domain_size < 1 or dm.world_size % args.domain_size != 0:
            raise SystemExit("world_size must be divisible by --domain-size")
        ddp_size = dm.world_size // args.domain_size
        mesh = dm.initialize_mesh(mesh_shape=(ddp_size, args.domain_size), mesh_dim_names=("ddp", "domain"))
        payload["mesh_shape"] = [ddp_size, args.domain_size]
        payload["mesh_dims"] = list(mesh.mesh_dim_names)
        payload["mesh_sizes"] = {name: mesh[name].size() for name in mesh.mesh_dim_names}

        if args.check_scatter and torch.cuda.is_available():
            try:
                domain_mesh = mesh["domain"]
                src = torch.distributed.get_global_rank(domain_mesh.get_group(), 0)
                x = torch.arange(4, dtype=torch.float32, device=dm.device)
                from torch.distributed.tensor.placement_types import Shard

                shard = scatter_tensor(x, src, domain_mesh, placements=(Shard(0),), global_shape=x.shape)
                payload["scatter_status"] = "passed"
                payload["scatter_local_shape"] = list(shard.to_local().shape)
                payload["scatter_global_shape"] = list(x.shape)
            except Exception as exc:  # pragma: no cover - smoke path only
                payload["scatter_status"] = f"ERROR: {type(exc).__name__}: {exc}"

        if args.check_sync:
            try:
                domain_mesh = mesh["domain"]
                model = FullyConnected(in_features=4, out_features=4).to(dm.device)
                sync_module_over_mesh(model, domain_mesh)
                payload["sync_status"] = "passed"
                payload["sync_model"] = model.__class__.__name__
            except Exception as exc:  # pragma: no cover - smoke path only
                payload["sync_status"] = f"ERROR: {type(exc).__name__}: {exc}"
    else:
        payload["mesh_shape"] = None

    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
