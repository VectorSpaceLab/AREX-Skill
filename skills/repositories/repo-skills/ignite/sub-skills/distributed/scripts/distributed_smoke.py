#!/usr/bin/env python3
from __future__ import annotations

import argparse

import torch
from torch.utils.data import DataLoader, TensorDataset

import ignite.distributed as idist
from ignite.utils import manual_seed


def build_loader() -> DataLoader:
    values = torch.arange(8, dtype=torch.float32).unsqueeze(1)
    labels = torch.tensor([0, 1, 0, 1, 0, 1, 0, 1])
    dataset = TensorDataset(values, labels)
    return DataLoader(dataset, batch_size=4, shuffle=False, num_workers=0)


def report(local_rank: int, label: str) -> None:
    loader = idist.auto_dataloader(TensorDataset(torch.arange(8, dtype=torch.float32).unsqueeze(1), torch.arange(8)), batch_size=4, shuffle=False, num_workers=0)
    batch = next(iter(loader))

    model = idist.auto_model(torch.nn.Linear(1, 2))
    optimizer = idist.auto_optim(torch.optim.SGD(model.parameters(), lr=0.1))

    rank_tensor = torch.tensor([idist.get_rank()], dtype=torch.float32)
    gathered = idist.all_gather(rank_tensor)
    broadcasted = idist.broadcast(torch.tensor([123.0]), src=0)
    shaped = idist.all_gather_tensors_with_shapes(torch.tensor([[1.0, 2.0]]), [[1, 2]])
    group = idist.new_group([0])

    @idist.one_rank_only()
    def only_rank_zero() -> str:
        return "rank-zero"

    with idist.one_rank_first():
        rank_first = "ok"

    idist.show_config()

    print(f"distributed_label={label}")
    print(f"distributed_backend={idist.backend()}")
    print(f"distributed_model={idist.model_name()}")
    print(f"distributed_device={idist.device().type}")
    print(f"distributed_rank={idist.get_rank()}")
    print(f"distributed_local_rank={idist.get_local_rank()}")
    print(f"distributed_world_size={idist.get_world_size()}")
    print(f"distributed_loader_batch={len(batch[0])}")
    print(f"distributed_model_type={type(model).__name__}")
    print(f"distributed_optimizer_type={type(optimizer).__name__}")
    print(f"distributed_gather={gathered.tolist() if hasattr(gathered, 'tolist') else gathered}")
    print(f"distributed_broadcast={broadcasted.tolist() if hasattr(broadcasted, 'tolist') else broadcasted}")
    print(f"distributed_shapes={[tuple(t.shape) for t in shaped]}")
    print(f"distributed_group_type={type(group).__name__}")
    print(f"distributed_one_rank_only={only_rank_zero()}")
    print(f"distributed_one_rank_first={rank_first}")


def run_serial() -> None:
    with idist.Parallel(backend=None) as parallel:
        parallel.run(report, "serial")


def run_gloo() -> None:
    if "gloo" not in idist.available_backends():
        print("distributed_gloo=skipped_no_backend")
        return

    with idist.Parallel(backend="gloo") as parallel:
        parallel.run(report, "gloo")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a compact Ignite distributed smoke check.")
    parser.add_argument(
        "--mode",
        choices=("auto", "serial", "gloo"),
        default="auto",
        help="Which distributed path to run.",
    )
    args = parser.parse_args()

    manual_seed(0)

    print(f"distributed_available_backends={idist.available_backends()}")

    if args.mode in ("auto", "serial"):
        run_serial()
    if args.mode in ("auto", "gloo"):
        run_gloo()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
