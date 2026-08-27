#!/usr/bin/env python3
"""Safe Chronos-2 fine-tuning smoke/template helper.

Default behavior prints the planned tiny-data fine-tuning call and exits. It only
loads a model and runs `Chronos2Pipeline.fit` when both --model-id-or-path and
--run are supplied.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect or run a tiny Chronos-2 fit smoke with explicit opt-in.")
    parser.add_argument("--model-id-or-path", default=None, help="Local/HF Chronos-2 model anchor. Required with --run.")
    parser.add_argument("--run", action="store_true", help="Actually load the model and run tiny fine-tuning.")
    parser.add_argument("--device-map", default="cpu", help="device_map passed to from_pretrained; default: cpu.")
    parser.add_argument("--prediction-length", type=int, default=2, help="Tiny forecast horizon for the smoke.")
    parser.add_argument("--history-length", type=int, default=12, help="Synthetic history length per series.")
    parser.add_argument("--num-steps", type=int, default=1, help="Training steps for the tiny smoke. Keep very small.")
    parser.add_argument("--batch-size", type=int, default=2, help="Tiny fine-tuning batch size.")
    parser.add_argument("--learning-rate", type=float, default=1e-5, help="Learning rate for the smoke.")
    parser.add_argument("--finetune-mode", choices=["full", "lora"], default="lora", help="Fine-tuning mode.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory. Defaults to a temporary directory.")
    parser.add_argument("--save-final", action="store_true", help="Call save_pretrained on the returned pipeline.")
    return parser


def synthetic_inputs(history_length: int):
    import numpy as np

    if history_length < 4:
        raise ValueError("history_length must be at least 4")
    x = np.arange(history_length, dtype="float32")
    return [
        {"target": 10.0 + np.sin(x / 2.0), "past_covariates": {"promo": (x % 3 == 0).astype("float32")}},
        {"target": 20.0 + np.cos(x / 3.0), "past_covariates": {"promo": (x % 4 == 0).astype("float32")}},
    ]


def print_plan(args: argparse.Namespace) -> None:
    print("Chronos-2 fit smoke/template")
    print("No model is loaded and no training is run unless --run is supplied.")
    print(f"model_id_or_path={args.model_id_or_path!r}")
    print(f"device_map={args.device_map!r}")
    print(f"finetune_mode={args.finetune_mode!r}")
    print(f"prediction_length={args.prediction_length}")
    print(f"history_length={args.history_length}")
    print(f"num_steps={args.num_steps}")
    print(f"batch_size={args.batch_size}")
    print("Example explicit run:")
    print("  python chronos2_fit_smoke_template.py --model-id-or-path LOCAL_OR_HF_CHRONOS2 --run --num-steps 1 --device-map cpu")


def run_smoke(args: argparse.Namespace) -> int:
    if not args.model_id_or_path:
        raise SystemExit("--model-id-or-path is required when --run is supplied")

    from chronos import BaseChronosPipeline, Chronos2Pipeline

    pipeline = BaseChronosPipeline.from_pretrained(args.model_id_or_path, device_map=args.device_map)
    if not isinstance(pipeline, Chronos2Pipeline):
        raise SystemExit("Loaded model is not a Chronos2Pipeline")

    output_dir = args.output_dir
    temp_ctx = None
    if output_dir is None:
        temp_ctx = tempfile.TemporaryDirectory(prefix="chronos2-fit-smoke-")
        output_dir = Path(temp_ctx.name)
    output_dir.mkdir(parents=True, exist_ok=True)

    inputs = synthetic_inputs(args.history_length)
    print(f"running tiny fit: output_dir={output_dir}")
    fitted = pipeline.fit(
        inputs,
        prediction_length=args.prediction_length,
        finetune_mode=args.finetune_mode,
        learning_rate=args.learning_rate,
        num_steps=args.num_steps,
        batch_size=args.batch_size,
        output_dir=output_dir,
        remove_unused_columns=False,
        report_to=[],
    )
    print(f"fit_return_type={type(fitted).__name__}")
    if args.save_final:
        final_dir = output_dir / "final"
        fitted.save_pretrained(final_dir)
        print(f"saved_final={final_dir}")
    if temp_ctx is not None and not args.save_final:
        temp_ctx.cleanup()
        print("temporary output cleaned")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.run:
        print_plan(args)
        return 0
    return run_smoke(args)


if __name__ == "__main__":
    raise SystemExit(main())
