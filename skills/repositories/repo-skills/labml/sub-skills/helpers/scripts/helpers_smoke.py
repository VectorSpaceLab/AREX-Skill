#!/usr/bin/env python3
"""Run a safe synthetic `labml_helpers` training smoke test.

This script uses a tiny synthetic dataset, `SimpleTrainValidConfigs`,
`DeviceConfigs`, `OptimizerConfigs`, `SeedConfigs`, and `Accuracy` to prove that
helper training abstractions work without downloading a real dataset.

Example:
    python scripts/helpers_smoke.py
    python scripts/helpers_smoke.py --cuda
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from labml import experiment, lab, tracker
from labml.configs import option
from labml_helpers.device import DeviceConfigs
from labml_helpers.metrics.accuracy import Accuracy
from labml_helpers.optimizer import OptimizerConfigs
from labml_helpers.seed import SeedConfigs
from labml_helpers.train_valid import SimpleTrainValidConfigs


class SmokeConfigs(SimpleTrainValidConfigs):
    epochs = 1
    inner_iterations = 1
    update_batches = 1
    # Keep this smoke test focused on helper loop mechanics. Tracking a raw
    # nn.Sequential model as an indicator requires LabML's model-probe writer
    # setup, so disable parameter logging here.
    log_params_updates = 0
    log_activations_batches = 0
    log_save_batches = 1
    is_track_time = False

    device = DeviceConfigs()
    set_seed = SeedConfigs()
    model: nn.Module
    optimizer: torch.optim.Adam
    loss_func = nn.CrossEntropyLoss()

    def init(self):
        self.state_modules = [Accuracy()]


@option(SmokeConfigs.train_loader)
def train_loader(c: SmokeConfigs):
    x = torch.tensor([
        [0.0, 0.1, 0.2, 0.3],
        [0.1, 0.0, 0.2, 0.4],
        [1.0, 1.1, 1.2, 1.3],
        [1.1, 1.0, 1.2, 1.4],
        [0.2, 0.2, 0.2, 0.2],
        [1.2, 1.2, 1.2, 1.2],
        [0.3, 0.4, 0.1, 0.2],
        [1.3, 1.4, 1.1, 1.2],
    ], dtype=torch.float32)
    y = torch.tensor([0, 0, 1, 1, 0, 1, 0, 1], dtype=torch.long)
    return DataLoader(TensorDataset(x, y), batch_size=4, shuffle=True)


@option(SmokeConfigs.valid_loader)
def valid_loader(c: SmokeConfigs):
    x = torch.tensor([
        [0.05, 0.1, 0.15, 0.2],
        [1.05, 1.1, 1.15, 1.2],
        [0.25, 0.3, 0.35, 0.4],
        [1.25, 1.3, 1.35, 1.4],
    ], dtype=torch.float32)
    y = torch.tensor([0, 1, 0, 1], dtype=torch.long)
    return DataLoader(TensorDataset(x, y), batch_size=2, shuffle=False)


@option(SmokeConfigs.model)
def model(c: SmokeConfigs):
    return nn.Sequential(
        nn.Linear(4, 8),
        nn.ReLU(),
        nn.Linear(8, 2),
    ).to(c.device)


@option(SmokeConfigs.optimizer)
def optimizer(c: SmokeConfigs):
    opt = OptimizerConfigs()
    opt.parameters = c.model.parameters()
    opt.learning_rate = 0.05
    return opt


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a synthetic labml_helpers smoke test.")
    parser.add_argument("--cuda", action="store_true", help="Allow DeviceConfigs to select CUDA if available.")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="labml-helpers-smoke-") as tmp:
        project_root = Path(tmp)
        lab.configure({"path": str(project_root), "data_path": "data", "experiments_path": "logs"})

        conf = SmokeConfigs()
        conf.set_seed.set()

        overrides = {"optimizer.optimizer": "Adam"}
        if not args.cuda:
            overrides["device.use_cuda"] = False

        experiment.create(name="helpers-smoke")
        experiment.configs(conf, overrides)

        with experiment.start():
            conf.run()

        print(f"project_root={lab.get_path()}")
        print(f"device={conf.device}")
        print(f"optimizer={type(conf.optimizer).__name__}")
        print(f"log_dir={lab.get_experiments_path()}")
        print(f"loss_queue={tracker.get_global_step()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
