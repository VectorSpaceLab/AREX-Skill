#!/usr/bin/env python3
"""CPU-only Accelerate checkpoint/tracker smoke test.

This helper verifies that a tiny model can save and restore training state,
that a registered custom object round-trips, that save/load hooks run, and
that a custom local tracker receives config and metric records. It does not
contact external tracking services.
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import tempfile
from pathlib import Path


class CounterState:
    def __init__(self):
        self.value = 0

    def state_dict(self):
        return {"value": self.value}

    def load_state_dict(self, state):
        self.value = int(state["value"])


def make_jsonl_tracker_class(GeneralTracker, on_main_process, torch):
    class JsonlTracker(GeneralTracker):
        name = "jsonl"
        requires_logging_directory = False
        main_process_only = True

        def __init__(self, path: Path):
            super().__init__()
            self.path = Path(path)
            self.handle = None

        @property
        def tracker(self):
            return self.handle

        @on_main_process
        def start(self):
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.handle = self.path.open("a", encoding="utf-8")

        @on_main_process
        def store_init_configuration(self, values: dict):
            self.handle.write(json.dumps({"type": "config", "values": values}, sort_keys=True) + "\n")
            self.handle.flush()

        @on_main_process
        def log(self, values: dict, step: int | None = None, **kwargs):
            serializable = {}
            for key, value in values.items():
                if isinstance(value, torch.Tensor):
                    value = value.detach().cpu().item()
                serializable[key] = value
            self.handle.write(
                json.dumps({"type": "metric", "step": step, "values": serializable}, sort_keys=True) + "\n"
            )
            self.handle.flush()

        @on_main_process
        def finish(self):
            if self.handle is not None:
                self.handle.close()
                self.handle = None

    return JsonlTracker


def build_components(torch):
    from torch.utils.data import DataLoader, TensorDataset

    x_values = torch.linspace(-1.0, 1.0, steps=16).unsqueeze(1)
    y_values = 2.0 * x_values + 0.5
    dataloader = DataLoader(TensorDataset(x_values, y_values), batch_size=4, shuffle=False)
    model = torch.nn.Linear(1, 1)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1, gamma=0.9)
    return model, optimizer, scheduler, dataloader


def train_one_epoch(torch, accelerator, model, optimizer, scheduler, dataloader, counter):
    model.train()
    total_loss = 0.0
    for step, (features, targets) in enumerate(dataloader):
        optimizer.zero_grad()
        predictions = model(features)
        loss = torch.nn.functional.mse_loss(predictions, targets)
        accelerator.backward(loss)
        optimizer.step()
        total_loss += float(loss.detach().cpu())
        counter.value += 1
        accelerator.log({"train/loss": loss.detach()}, step=step)
    scheduler.step()
    return total_loss / len(dataloader)


def tensor_snapshot(model):
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def assert_snapshots_close(torch, expected, actual):
    for name, expected_tensor in expected.items():
        actual_tensor = actual[name]
        if not torch.allclose(expected_tensor, actual_tensor):
            raise AssertionError(f"Parameter {name} did not restore correctly")


def parse_args():
    parser = argparse.ArgumentParser(description="Run a CPU-only Accelerate checkpoint and tracker smoke test.")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=None,
        help="Optional directory for smoke artifacts. Defaults to a temporary directory.",
    )
    parser.add_argument("--seed", type=int, default=123, help="Seed used for deterministic tiny model setup.")
    parser.add_argument("--keep", action="store_true", help="Keep temporary artifacts and print their location.")
    return parser.parse_args()


def run_smoke(work_dir: Path, seed: int):
    import torch

    from accelerate import Accelerator
    from accelerate.logging import get_logger
    from accelerate.tracking import GeneralTracker, on_main_process
    from accelerate.utils import ProjectConfiguration, set_seed

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = get_logger(__name__)
    JsonlTracker = make_jsonl_tracker_class(GeneralTracker, on_main_process, torch)
    set_seed(seed)

    tracker_path = work_dir / "metrics.jsonl"
    project_config = ProjectConfiguration(
        project_dir=str(work_dir / "project"),
        logging_dir=str(work_dir / "logs"),
        automatic_checkpoint_naming=True,
        total_limit=2,
    )
    accelerator = Accelerator(cpu=True, project_config=project_config, log_with=JsonlTracker(tracker_path))
    accelerator.init_trackers("checkpoint-tracker-smoke", config={"seed": seed, "backend": "cpu"})

    model, optimizer, scheduler, dataloader = build_components(torch)
    model, optimizer, scheduler, dataloader = accelerator.prepare(model, optimizer, scheduler, dataloader)
    counter = CounterState()
    accelerator.register_for_checkpointing(counter)

    hook_events = []

    def save_hook(models, weights, output_dir):
        hook_events.append("save")
        Path(output_dir, "hook_metadata.json").write_text(json.dumps({"hook": "save"}), encoding="utf-8")

    def load_hook(models, input_dir):
        hook_events.append("load")
        metadata = json.loads(Path(input_dir, "hook_metadata.json").read_text(encoding="utf-8"))
        if metadata != {"hook": "save"}:
            raise AssertionError("Hook metadata did not round-trip")

    accelerator.register_save_state_pre_hook(save_hook)
    accelerator.register_load_state_pre_hook(load_hook)

    initial_loss = train_one_epoch(torch, accelerator, model, optimizer, scheduler, dataloader, counter)
    checkpoint_dir = accelerator.save_state()
    saved_snapshot = tensor_snapshot(accelerator.unwrap_model(model))
    saved_counter = counter.value

    resumed_loss = train_one_epoch(torch, accelerator, model, optimizer, scheduler, dataloader, counter)
    if math.isclose(initial_loss, resumed_loss, rel_tol=0.0, abs_tol=0.0):
        raise AssertionError("Expected model to change after another epoch")

    accelerator.load_state(str(checkpoint_dir), map_location="cpu")
    restored_snapshot = tensor_snapshot(accelerator.unwrap_model(model))
    assert_snapshots_close(torch, saved_snapshot, restored_snapshot)
    if counter.value != saved_counter:
        raise AssertionError(f"Custom counter did not restore: expected {saved_counter}, got {counter.value}")
    if hook_events != ["save", "load"]:
        raise AssertionError(f"Unexpected hook event order: {hook_events}")

    logger.info("main process log after checkpoint restore")
    accelerator.log({"smoke/restored_counter": counter.value}, step=counter.value)
    accelerator.end_training()

    records = [json.loads(line) for line in tracker_path.read_text(encoding="utf-8").splitlines()]
    if not any(record.get("type") == "config" for record in records):
        raise AssertionError("Tracker config record missing")
    if not any(record.get("values", {}).get("smoke/restored_counter") == saved_counter for record in records):
        raise AssertionError("Tracker restored counter metric missing")

    return {
        "checkpoint_dir": str(checkpoint_dir),
        "tracker_path": str(tracker_path),
        "records": len(records),
        "counter": counter.value,
    }


def main():
    args = parse_args()
    if args.work_dir is not None:
        args.work_dir.mkdir(parents=True, exist_ok=True)
        result = run_smoke(args.work_dir, args.seed)
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))
        return

    with tempfile.TemporaryDirectory(prefix="accelerate-checkpoint-tracker-") as tmpdir:
        work_dir = Path(tmpdir)
        result = run_smoke(work_dir, args.seed)
        if args.keep:
            kept_dir = Path(tempfile.mkdtemp(prefix="accelerate-checkpoint-tracker-kept-"))
            import shutil

            shutil.copytree(work_dir, kept_dir, dirs_exist_ok=True)
            result["kept_dir"] = str(kept_dir)
        print(json.dumps({"ok": True, **result}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
