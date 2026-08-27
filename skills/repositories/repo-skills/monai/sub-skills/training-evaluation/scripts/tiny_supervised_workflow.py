#!/usr/bin/env python3
"""Run a tiny MONAI SupervisedTrainer/SupervisedEvaluator workflow on CPU.

The script is intentionally small and synthetic. It checks that MONAI's Ignite-based
engines, StatsHandler, ValidationHandler, CheckpointSaver, and MeanDice can be
imported and wired together in the current Python environment.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tiny CPU MONAI supervised trainer/evaluator smoke workflow.")
    parser.add_argument("--epochs", type=int, default=1, help="Number of tiny training epochs to run. Default: 1.")
    parser.add_argument("--batch-size", type=int, default=2, help="Batch size for synthetic tensors. Default: 2.")
    parser.add_argument("--work-dir", type=Path, default=None, help="Optional directory for temporary checkpoints.")
    parser.add_argument(
        "--keep-checkpoints",
        action="store_true",
        help="Keep checkpoints in --work-dir or a temporary directory and print their location.",
    )
    return parser.parse_args()


def import_workflow_apis():
    try:
        import ignite  # noqa: F401
        import torch
        from torch.utils.data import DataLoader

        from monai.data import Dataset
        from monai.engines import SupervisedEvaluator, SupervisedTrainer
        from monai.handlers import CheckpointSaver, MeanDice, StatsHandler, ValidationHandler, from_engine
        from monai.networks.nets import UNet
        from monai.transforms import Activationsd, AsDiscreted, Compose
    except Exception as exc:  # pragma: no cover - diagnostic path depends on environment
        message = str(exc)
        print("SKIP: MONAI Ignite-based training workflow APIs are not fully available.")
        print(f"Reason: {exc.__class__.__name__}: {message}")
        print("Recovery: install a MONAI environment with a compatible pytorch-ignite package, then rerun this script.")
        return None

    return {
        "torch": torch,
        "DataLoader": DataLoader,
        "Dataset": Dataset,
        "SupervisedEvaluator": SupervisedEvaluator,
        "SupervisedTrainer": SupervisedTrainer,
        "CheckpointSaver": CheckpointSaver,
        "MeanDice": MeanDice,
        "StatsHandler": StatsHandler,
        "ValidationHandler": ValidationHandler,
        "from_engine": from_engine,
        "UNet": UNet,
        "Activationsd": Activationsd,
        "AsDiscreted": AsDiscreted,
        "Compose": Compose,
    }


def make_records(torch_module, count: int = 4) -> list[dict[str, object]]:
    records = []
    for index in range(count):
        image = torch_module.zeros((1, 16, 16), dtype=torch_module.float32)
        image[:, 4:12, 4:12] = 1.0 + float(index) * 0.01
        label = (image > 0.5).to(dtype=torch_module.long)
        records.append({"image": image, "label": label})
    return records


def main() -> int:
    args = parse_args()
    if args.epochs < 1:
        print("ERROR: --epochs must be >= 1", file=sys.stderr)
        return 2
    if args.batch_size < 1:
        print("ERROR: --batch-size must be >= 1", file=sys.stderr)
        return 2

    apis = import_workflow_apis()
    if apis is None:
        return 0

    torch = apis["torch"]
    DataLoader = apis["DataLoader"]
    Dataset = apis["Dataset"]
    SupervisedEvaluator = apis["SupervisedEvaluator"]
    SupervisedTrainer = apis["SupervisedTrainer"]
    CheckpointSaver = apis["CheckpointSaver"]
    MeanDice = apis["MeanDice"]
    StatsHandler = apis["StatsHandler"]
    ValidationHandler = apis["ValidationHandler"]
    from_engine = apis["from_engine"]
    UNet = apis["UNet"]
    Activationsd = apis["Activationsd"]
    AsDiscreted = apis["AsDiscreted"]
    Compose = apis["Compose"]

    torch.manual_seed(7)
    device = torch.device("cpu")
    records = make_records(torch, count=max(4, args.batch_size * 2))
    loader = DataLoader(Dataset(records), batch_size=args.batch_size, shuffle=False)

    network = UNet(
        spatial_dims=2,
        in_channels=1,
        out_channels=2,
        channels=(4, 8),
        strides=(2,),
        num_res_units=0,
    ).to(device)
    optimizer = torch.optim.Adam(network.parameters(), lr=1e-3)

    def loss_function(prediction, label):
        return torch.nn.functional.cross_entropy(prediction, label.squeeze(1).long())

    postprocessing = Compose(
        [
            Activationsd(keys="pred", softmax=True),
            AsDiscreted(keys="pred", argmax=True, to_onehot=2),
            AsDiscreted(keys="label", to_onehot=2),
        ]
    )

    if args.work_dir is not None:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        for filename in ("final.pt", "best_metric.pt"):
            existing = args.work_dir / filename
            if existing.exists() and not args.keep_checkpoints:
                print(f"ERROR: refusing to overwrite existing checkpoint file: {existing}", file=sys.stderr)
                print("Use a new --work-dir or pass --keep-checkpoints when overwriting is intentional.", file=sys.stderr)
                return 2
        checkpoint_context = None
        checkpoint_dir = args.work_dir
    else:
        checkpoint_context = tempfile.TemporaryDirectory(prefix="monai-tiny-workflow-")
        checkpoint_dir = Path(checkpoint_context.name)

    try:
        evaluator = SupervisedEvaluator(
            device=device,
            val_data_loader=loader,
            network=network,
            postprocessing=postprocessing,
            key_val_metric={"val_mean_dice": MeanDice(output_transform=from_engine(["pred", "label"]))},
            val_handlers=[
                StatsHandler(iteration_log=False, output_transform=lambda output: None),
                CheckpointSaver(
                    save_dir=str(checkpoint_dir),
                    save_dict={"network": network},
                    save_key_metric=True,
                    key_metric_name="val_mean_dice",
                    key_metric_filename="best_metric.pt",
                ),
            ],
            amp=False,
        )

        trainer = SupervisedTrainer(
            device=device,
            max_epochs=args.epochs,
            train_data_loader=loader,
            network=network,
            optimizer=optimizer,
            loss_function=loss_function,
            train_handlers=[
                ValidationHandler(interval=1, validator=evaluator, exec_at_start=True),
                StatsHandler(output_transform=lambda output: output["loss"]),
                CheckpointSaver(
                    save_dir=str(checkpoint_dir),
                    save_dict={"network": network, "optimizer": optimizer},
                    save_final=True,
                    final_filename="final.pt",
                ),
            ],
            amp=False,
        )
        trainer.run()

        metric = evaluator.state.metrics.get("val_mean_dice")
        final_checkpoint = checkpoint_dir / "final.pt"
        best_checkpoint = checkpoint_dir / "best_metric.pt"
        print("OK: tiny MONAI supervised workflow completed.")
        print(f"val_mean_dice={float(metric):.4f}" if metric is not None else "val_mean_dice=<missing>")
        print(f"final_checkpoint_exists={final_checkpoint.exists()}")
        print(f"best_checkpoint_exists={best_checkpoint.exists()}")
        if args.keep_checkpoints or args.work_dir is not None:
            print(f"checkpoint_dir={checkpoint_dir}")
    finally:
        if checkpoint_context is not None and not args.keep_checkpoints:
            checkpoint_context.cleanup()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
