#!/usr/bin/env python3
"""Safe synthetic smoke for SpikingJelly vision training contracts.

This script checks the legacy `Trainer` hooks, distributed vision config
round-trips, built-in model-builder shapes, and pipeline-boundary metadata
without downloading data or launching distributed training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import TensorDataset

from spikingjelly.activation_based import functional
from spikingjelly.activation_based.distributed import vision


def build_synthetic_datasets(
    samples: int = 8,
    classes: int = 5,
    image_size: int = 32,
    time_steps: int = 2,
    input_layout: str = "NCHW",
    seed: int = 1234,
) -> tuple[TensorDataset, TensorDataset]:
    """Return tiny deterministic synthetic datasets for shape checks."""
    if samples <= 0 or classes <= 0 or image_size <= 0 or time_steps <= 0:
        raise ValueError("synthetic dataset dimensions must be positive.")
    generator = torch.Generator().manual_seed(seed)
    if input_layout == "NCHW":
        train_images = torch.randn(samples, 3, image_size, image_size, generator=generator)
        validation_images = torch.randn(
            max(2, samples // 4), 3, image_size, image_size, generator=generator
        )
    elif input_layout == "NTCHW":
        train_images = torch.randn(
            samples, time_steps, 3, image_size, image_size, generator=generator
        )
        validation_images = torch.randn(
            max(2, samples // 4),
            time_steps,
            3,
            image_size,
            image_size,
            generator=generator,
        )
    else:
        raise ValueError("input_layout must be 'NCHW' or 'NTCHW'.")
    train_targets = torch.arange(samples, dtype=torch.long) % classes
    validation_targets = torch.arange(validation_images.shape[0], dtype=torch.long) % classes
    return (
        TensorDataset(train_images, train_targets),
        TensorDataset(validation_images, validation_targets),
    )


def _fail(message: str) -> None:
    raise AssertionError(message)


def _expect_value_error(label: str, fn, message_fragment: str) -> str:
    try:
        fn()
    except ValueError as error:
        if message_fragment not in str(error):
            raise AssertionError(
                f"{label} raised the wrong ValueError: {error!r}"
            ) from error
        return str(error)
    raise AssertionError(f"{label} did not raise ValueError")


def run_trainer_case() -> dict[str, Any]:
    from spikingjelly.activation_based.model import train_classify

    trainer = train_classify.Trainer()
    parser = trainer.get_args_parser(add_help=False)
    parsed = parser.parse_args([])

    args = SimpleNamespace(
        opt="adamw",
        lr=1e-3,
        momentum=0.9,
        weight_decay=0.01,
        lr_scheduler="cosa",
        lr_step_size=30,
        lr_gamma=0.1,
        epochs=4,
        lr_warmup_epochs=1,
        lr_warmup_method="linear",
        lr_warmup_decay=0.1,
    )
    parameter = nn.Parameter(torch.tensor(1.0))
    optimizer = trainer.set_optimizer(args, [parameter])
    scheduler = trainer.set_lr_scheduler(args, optimizer)
    try:
        trainer.load_model(parsed, num_classes=2)
    except NotImplementedError:
        load_model_contract = "not-implemented-as-expected"
    else:
        _fail("Trainer.load_model should require an override")

    return {
        "parsed_model": parsed.model,
        "parsed_epochs": parsed.epochs,
        "parsed_batch_size": parsed.batch_size,
        "optimizer": optimizer.__class__.__name__,
        "scheduler": scheduler.__class__.__name__ if scheduler is not None else None,
        "load_model_contract": load_model_contract,
    }


def run_config_case() -> dict[str, Any]:
    config = vision.TrainingConfig(
        model=vision.SEWResNet34Config(
            time_steps=2,
            num_classes=5,
            step_mode="m",
            image_size=32,
        ),
        dataset_builder="spikingjelly.activation_based.distributed.vision.build_imagefolder_datasets",
        dataset_kwargs={"root": Path("synthetic-imagefolder"), "image_size": 32},
        input_layout="NCHW",
        epochs=1,
        batch_size=2,
        workers=0,
        optimizer="torch.optim.AdamW",
        optimizer_kwargs={"lr": 1e-3, "weight_decay": 0.0},
        loss_function="torch.nn.functional.cross_entropy",
        loss_kwargs={},
        tensor_parallel_size=1,
        pipeline_parallel_size=1,
        pipeline_microbatches=1,
        data_parallel="ddp",
        precision="fp32",
        memopt_level=0,
        max_steps=1,
        timing_warmup_steps=0,
    )
    restored = vision.TrainingConfig.from_dict(config.as_dict())
    if restored != config:
        _fail("TrainingConfig did not round-trip through as_dict/from_dict")

    nchw_train, nchw_val = build_synthetic_datasets(
        samples=8, classes=5, image_size=32, time_steps=2, input_layout="NCHW"
    )
    ntchw_train, ntchw_val = build_synthetic_datasets(
        samples=8, classes=5, image_size=32, time_steps=2, input_layout="NTCHW"
    )
    if nchw_train[0][0].shape != (3, 32, 32):
        _fail(f"NCHW synthetic train sample has wrong shape: {nchw_train[0][0].shape}")
    if ntchw_train[0][0].shape != (2, 3, 32, 32):
        _fail(f"NTCHW synthetic train sample has wrong shape: {ntchw_train[0][0].shape}")
    if len(nchw_train) != 8 or len(nchw_val) < 2:
        _fail("unexpected NCHW synthetic dataset sizes")
    if len(ntchw_train) != 8 or len(ntchw_val) < 2:
        _fail("unexpected NTCHW synthetic dataset sizes")

    invalids = {
        "pipeline_step_mode": _expect_value_error(
            "pipeline_step_mode",
            lambda: vision.TrainingConfig(
                model=vision.SEWResNet34Config(step_mode="s"),
                dataset_builder="package.build",
                pipeline_parallel_size=2,
            ),
            "step_mode='m'",
        ),
        "pipeline_microbatches": _expect_value_error(
            "pipeline_microbatches",
            lambda: vision.TrainingConfig(
                model=vision.SEWResNet34Config(),
                dataset_builder="package.build",
                batch_size=3,
                pipeline_microbatches=2,
            ),
            "batch_size",
        ),
        "pipeline_fp16": _expect_value_error(
            "pipeline_fp16",
            lambda: vision.TrainingConfig(
                model=vision.SEWResNet34Config(),
                dataset_builder="package.build",
                precision="fp16",
                pipeline_parallel_size=2,
            ),
            "Vision PP currently supports fp32 and bf16",
        ),
        "spikformer_step_mode": _expect_value_error(
            "spikformer_step_mode",
            lambda: vision.SpikformerConfig(step_mode="s"),
            "step_mode='m'",
        ),
    }

    return {
        "round_trip": True,
        "dataset_builder": config.dataset_builder,
        "nchw_sample_shape": list(nchw_train[0][0].shape),
        "ntchw_sample_shape": list(ntchw_train[0][0].shape),
        "invalids": invalids,
    }


def run_forward_case(device: torch.device) -> dict[str, Any]:
    from spikingjelly.activation_based import neuron, surrogate
    from spikingjelly.activation_based.model import sew_resnet, spiking_resnet, spikformer

    results: dict[str, Any] = {}

    torch.manual_seed(7)
    resnet = spiking_resnet.spiking_resnet18(
        pretrained=False,
        spiking_neuron=neuron.IFNode,
        surrogate_function=surrogate.ATan(),
        detach_reset=True,
        step_mode="m",
        num_classes=5,
    ).to(device).eval()
    functional.set_step_mode(resnet, "m")
    functional.reset_net(resnet)
    resnet_input = torch.randn(1, 2, 3, 32, 32, device=device)
    with torch.inference_mode():
        resnet_output = resnet(resnet_input)
    if tuple(resnet_output.shape) != (1, 2, 5):
        _fail(f"spiking_resnet18 output shape mismatch: {tuple(resnet_output.shape)}")
    results["spiking_resnet18"] = list(resnet_output.shape)

    torch.manual_seed(8)
    sew = sew_resnet.sew_resnet34(
        pretrained=False,
        cnf="ADD",
        spiking_neuron=neuron.LIFNode,
        tau=2.0,
        detach_reset=True,
        num_classes=5,
        backend="torch",
    ).to(device).eval()
    functional.set_step_mode(sew, "m")
    functional.reset_net(sew)
    sew_input = torch.randn(2, 1, 3, 32, 32, device=device)
    with torch.inference_mode():
        sew_multi = sew(sew_input)
    functional.set_step_mode(sew, "s")
    functional.reset_net(sew)
    with torch.inference_mode():
        sew_loop = torch.stack([sew(step) for step in sew_input], dim=0)
    torch.testing.assert_close(sew_loop, sew_multi)
    if tuple(sew_multi.shape) != (2, 1, 5):
        _fail(f"sew_resnet34 output shape mismatch: {tuple(sew_multi.shape)}")
    results["sew_resnet34"] = list(sew_multi.shape)

    torch.manual_seed(9)
    spk = spikformer.spikformer_ti(
        T=2,
        img_size_h=32,
        img_size_w=32,
        num_classes=7,
        backend="torch",
    ).to(device).eval()
    functional.reset_net(spk)
    spikformer_input = torch.randn(1, 3, 32, 32, device=device)
    with torch.inference_mode():
        spikformer_output = spk(spikformer_input)
    if tuple(spikformer_output.shape) != (2, 1, 7):
        _fail(
            f"spikformer_ti output shape mismatch: {tuple(spikformer_output.shape)}"
        )
    results["spikformer_ti"] = list(spikformer_output.shape)

    return results


def run_pipeline_case(device: torch.device) -> dict[str, Any]:
    sew_cfg = vision.SEWResNet34Config(
        time_steps=2,
        num_classes=5,
        step_mode="m",
        image_size=32,
    )
    sew_builder = sew_cfg.get_builder_cls()(sew_cfg)
    sew_rank0 = sew_builder.build(
        process_group=None,
        pipeline_rank=0,
        pipeline_size=2,
        pipeline_microbatches=2,
        device=device,
        micro_batch_size=4,
        memopt_level=0,
        memopt_compress_inputs=False,
    )
    sew_rank1 = sew_builder.build(
        process_group=None,
        pipeline_rank=1,
        pipeline_size=2,
        pipeline_microbatches=2,
        device=device,
        micro_batch_size=4,
        memopt_level=0,
        memopt_compress_inputs=False,
    )
    sew_input_shape_0 = sew_rank0[2]
    sew_output_shape_0 = sew_rank0[3]
    sew_input_shape_1 = sew_rank1[2]
    sew_output_shape_1 = sew_rank1[3]
    if sew_input_shape_0 != (2, 2, 3, 32, 32):
        _fail(f"SEW PP input shape mismatch: {sew_input_shape_0}")
    if sew_output_shape_0 != (2, 2, 128, 4, 4):
        _fail(f"SEW PP output shape mismatch: {sew_output_shape_0}")
    if sew_input_shape_1 != (2, 2, 128, 4, 4):
        _fail(f"SEW PP second-stage input shape mismatch: {sew_input_shape_1}")
    if sew_output_shape_1 != (2, 2, 5):
        _fail(f"SEW PP second-stage output shape mismatch: {sew_output_shape_1}")

    spk_cfg = vision.SpikformerCIFAR10Config(
        time_steps=2,
        num_classes=10,
        step_mode="m",
    )
    spk_builder = spk_cfg.get_builder_cls()(spk_cfg)
    spk_rank0 = spk_builder.build(
        process_group=None,
        pipeline_rank=0,
        pipeline_size=2,
        pipeline_microbatches=2,
        device=device,
        micro_batch_size=4,
        memopt_level=0,
        memopt_compress_inputs=False,
    )
    spk_rank1 = spk_builder.build(
        process_group=None,
        pipeline_rank=1,
        pipeline_size=2,
        pipeline_microbatches=2,
        device=device,
        micro_batch_size=4,
        memopt_level=0,
        memopt_compress_inputs=False,
    )
    spk_input_shape_0 = spk_rank0[2]
    spk_output_shape_0 = spk_rank0[3]
    spk_input_shape_1 = spk_rank1[2]
    spk_output_shape_1 = spk_rank1[3]
    if spk_input_shape_0 != (2, 2, 3, 32, 32):
        _fail(f"Spikformer PP input shape mismatch: {spk_input_shape_0}")
    if spk_output_shape_0 != (2, 2, 384, 8, 8):
        _fail(f"Spikformer PP output shape mismatch: {spk_output_shape_0}")
    if spk_input_shape_1 != (2, 2, 384, 8, 8):
        _fail(f"Spikformer PP second-stage input shape mismatch: {spk_input_shape_1}")
    if spk_output_shape_1 != (2, 2, 10):
        _fail(f"Spikformer PP second-stage output shape mismatch: {spk_output_shape_1}")

    ragged_error = _expect_value_error(
        "ragged_spikformer_pp",
        lambda: vision.SpikformerConfig(
            time_steps=2,
            image_height=33,
            image_width=32,
        ).get_builder_cls()(vision.SpikformerConfig(
            time_steps=2,
            image_height=33,
            image_width=32,
        )).build(
            process_group=None,
            pipeline_rank=0,
            pipeline_size=2,
            pipeline_microbatches=1,
            device=device,
            micro_batch_size=2,
            memopt_level=0,
            memopt_compress_inputs=False,
        ),
        "divisible by 16",
    )

    return {
        "sew": {
            "input_shape_stage0": list(sew_input_shape_0),
            "output_shape_stage0": list(sew_output_shape_0),
            "input_shape_stage1": list(sew_input_shape_1),
            "output_shape_stage1": list(sew_output_shape_1),
        },
        "spikformer_cifar10": {
            "input_shape_stage0": list(spk_input_shape_0),
            "output_shape_stage0": list(spk_output_shape_0),
            "input_shape_stage1": list(spk_input_shape_1),
            "output_shape_stage1": list(spk_output_shape_1),
        },
        "ragged_spikformer_pp": ragged_error,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe synthetic smoke for SpikingJelly vision training contracts."
    )
    parser.add_argument(
        "--case",
        choices=("all", "trainer", "config", "forward", "pipeline"),
        default="all",
        help="Which smoke group to run.",
    )
    parser.add_argument("--device", default="cpu", help="torch device, e.g. cpu or cuda:0")
    parser.add_argument("--output", default=None, help="Optional JSON output path.")
    return parser.parse_args()


def _write_output(path: str | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    args = parse_args()
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but is not available.")

    torch.manual_seed(0)
    if device.type == "cpu":
        torch.set_num_threads(1)

    runners = {
        "trainer": run_trainer_case,
        "config": run_config_case,
        "forward": lambda: run_forward_case(device),
        "pipeline": lambda: run_pipeline_case(device),
    }
    case_order = list(runners) if args.case == "all" else [args.case]

    results: dict[str, Any] = {
        "device": str(device),
        "case": args.case,
        "suites": {},
    }
    for case in case_order:
        results["suites"][case] = runners[case]()
        print(json.dumps({case: results["suites"][case]}, sort_keys=True), flush=True)

    _write_output(args.output, results)
    print(json.dumps(results, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
