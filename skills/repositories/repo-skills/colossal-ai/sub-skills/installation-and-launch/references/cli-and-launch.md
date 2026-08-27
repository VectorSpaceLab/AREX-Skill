# CLI and Launch Reference

## `colossalai run`

Basic single-node launch:

```bash
colossalai run --nproc_per_node 4 --master_port 29500 train.py --config config.py
```

Run a Python module:

```bash
colossalai run --nproc_per_node 1 -m package.module --arg value
```

Multi-node with explicit hosts:

```bash
colossalai run --host node0,node1 --master_addr node0 --nproc_per_node 8 train.py
```

Multi-node with a hostfile:

```bash
colossalai run --hostfile hosts.txt --master_addr node0 --num_nodes 2 --nproc_per_node 8 train.py
```

Hostfile lines are hostnames. `--include` and `--exclude` filter hostfile entries and are mutually exclusive.

## Main CLI flags

- `--nproc_per_node`: number of GPU worker processes on each node.
- `--master_addr`, `--master_port`: rendezvous endpoint.
- `--host`: comma-separated host list.
- `--hostfile`: file containing one hostname per line.
- `--include` / `--exclude`: host filters for hostfile launches.
- `--extra_launch_args`: comma-separated extra torch distributed launcher args, converted to `--key=value` or `--flag`.
- `-m`: run a Python module rather than a `.py` script.

## Programmatic launch APIs

Use `colossalai.launch_from_torch()` inside a script launched by `torchrun` or `colossalai run`; it reads `RANK`, `LOCAL_RANK`, `WORLD_SIZE`, `MASTER_ADDR`, and `MASTER_PORT`.

Use `colossalai.launch(rank, world_size, host, port, local_rank=None, seed=1024)` when you manage ranks yourself.

Use `launch_from_slurm(host, port)` when SLURM provides `SLURM_PROCID` and `SLURM_NPROCS`.

Use `launch_from_openmpi(host, port)` when OpenMPI provides `OMPI_COMM_WORLD_RANK`, `OMPI_COMM_WORLD_LOCAL_RANK`, and `OMPI_COMM_WORLD_SIZE`.

## Command builder helper

Run the bundled helper to generate safe commands:

```bash
python scripts/colossalai_launch_builder.py --nproc-per-node 2 --script train.py -- --epochs 1
python scripts/colossalai_launch_builder.py --hostfile hosts.txt --master-addr node0 --nproc-per-node 8 --script train.py
```

The helper prints a command; it does not execute it.
