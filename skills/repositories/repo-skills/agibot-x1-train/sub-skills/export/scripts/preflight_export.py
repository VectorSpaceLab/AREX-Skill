#!/usr/bin/env python3
"""Safe, dependency-light preflight and artifact check for X1 DH exports.

This helper deliberately does not import humanoid, humanoid.envs, or Isaac Gym.
It can therefore check paths and (when already installed) model-side artifacts
without pretending that the repository's export entry points are runnable.
"""

from __future__ import print_function

import argparse
import os
import sys
from pathlib import Path


TASK_CONTRACTS = {
    "x1_dh_stand": {
        "experiment": "x1_dh_stand",
        "observations": 66 * 47,
        "single_observation": 47,
        "history_frames": 66,
        "short_observations": 5 * 47,
        "actions": 12,
    }
}


def fail(message):
    print("FAIL: " + message, file=sys.stderr)
    return False


def warn(message):
    print("WARN: " + message)


def error(message):
    fail(message)
    return 1


def info(message):
    print("OK: " + message)


def select_run(root, load_run):
    """Select a run using the source helper's -1/relative-name convention."""
    root = Path(root)
    if str(load_run) == "-1":
        candidates = [p for p in root.iterdir() if p.is_dir()]
        candidates = [p for p in candidates if p.name != "exported"]
        if not candidates:
            raise ValueError("no runs found under {}".format(root))
        return sorted(candidates, key=lambda p: p.name)[-1]
    selected = Path(str(load_run))
    if not selected.is_absolute():
        selected = root / selected
    return selected


def select_training_checkpoint(root, load_run, checkpoint):
    run = select_run(root, load_run)
    if not run.is_dir():
        raise ValueError("selected run is not a directory: {}".format(run))
    if checkpoint == -1:
        models = [p for p in run.iterdir() if p.is_file() and "model" in p.name]
        if not models:
            raise ValueError("no model* checkpoint found under {}".format(run))
        model = sorted(models, key=lambda p: p.name.zfill(15))[-1]
    else:
        model = run / "model_{}.pt".format(checkpoint)
    return model


def select_jit_artifact(root, load_run):
    run = select_run(root, load_run)
    if not run.is_dir():
        raise ValueError("selected exported-policy run is not a directory: {}".format(run))
    files = [p for p in run.iterdir() if p.is_file()]
    if not files:
        raise ValueError("no files found under {}".format(run))
    # The ONNX source helper sorts every directory entry and takes the last;
    # restricting the advisory helper to files avoids selecting a subdirectory.
    return sorted(files, key=lambda p: p.name.zfill(15))[-1]


def inspect_checkpoint(path, contract):
    try:
        import torch
    except ImportError:
        warn("SKIP: PyTorch is not installed; checkpoint structure was not inspected")
        return 3
    try:
        payload = torch.load(str(path), map_location="cpu")
    except Exception as exc:
        return error("torch.load failed for {}: {}".format(path, exc))
    if not isinstance(payload, dict):
        return error("checkpoint payload is not a mapping")
    state = payload.get("model_state_dict")
    if not isinstance(state, dict):
        return error("checkpoint has no model_state_dict mapping")

    expected = {
        "actor.0.weight": (512, 302),
        "actor.6.weight": (12, 128),
        "long_history.0.weight": (32, 66, 6),
        "long_history.2.weight": (16, 32, 4),
        "long_history.7.weight": (64, 128),
        "state_estimator.0.weight": (256, 235),
        "state_estimator.6.weight": (3, 64),
    }
    if contract is None:
        warn("checkpoint has model_state_dict; architecture checks were skipped for an unknown task")
        return 0
    for key, shape in expected.items():
        if key not in state:
            return error("checkpoint is missing {}".format(key))
        actual = tuple(state[key].shape)
        if actual != shape:
            return error("{} has shape {}, expected {}".format(key, actual, shape))
    info("checkpoint contains model_state_dict with the X1 DH architecture")
    return 0


def validate_jit(path, contract):
    try:
        import torch
    except ImportError:
        warn("SKIP: PyTorch is not installed; JIT load/shape check was skipped")
        return 3
    if contract is None:
        warn("SKIP: no dimension contract is available for this task")
        return 3
    try:
        model = torch.jit.load(str(path), map_location="cpu")
        model.eval()
        output = model(torch.zeros(1, contract["observations"], dtype=torch.float32))
    except Exception as exc:
        return error("JIT load or zero-input inference failed: {}".format(exc))
    shape = tuple(output.shape)
    if shape != (1, contract["actions"]):
        return error("JIT output shape is {}, expected {}".format(shape, (1, contract["actions"])))
    if not bool(torch.isfinite(output).all()):
        return error("JIT zero-input output contains non-finite values")
    info("JIT artifact loads on CPU and returns {} finite actions".format(contract["actions"]))
    return 0


def validate_onnx(path, contract, run_runtime):
    try:
        import onnx
    except ImportError:
        warn("SKIP: onnx is not installed; ONNX graph validation was skipped")
        return 3
    if contract is None:
        warn("SKIP: no dimension contract is available for this task")
        return 3
    try:
        model = onnx.load(str(path))
        onnx.checker.check_model(model)
    except Exception as exc:
        return error("ONNX checker failed: {}".format(exc))
    info("ONNX graph passes onnx.checker")
    inputs = model.graph.input
    outputs = model.graph.output
    if len(inputs) != 1 or len(outputs) != 1:
        return error("ONNX graph must have one input and one output")
    if inputs[0].name != "input" or outputs[0].name != "output":
        return error("ONNX graph names are {}, {}; expected input/output".format(inputs[0].name, outputs[0].name))

    def dim_value(dim):
        return getattr(dim, "dim_value", 0)

    input_dims = tuple(dim_value(d) for d in inputs[0].type.tensor_type.shape.dim)
    output_dims = tuple(dim_value(d) for d in outputs[0].type.tensor_type.shape.dim)
    if input_dims != (1, contract["observations"]):
        return error("ONNX input shape is {}, expected {}".format(input_dims, (1, contract["observations"])))
    if output_dims != (1, contract["actions"]):
        return error("ONNX output shape is {}, expected {}".format(output_dims, (1, contract["actions"])))
    info("ONNX graph exposes input={} and output={}".format(input_dims, output_dims))

    if not run_runtime:
        return 0
    try:
        import numpy as np
        import onnxruntime as ort
        session = ort.InferenceSession(str(path), providers=["CPUExecutionProvider"])
        value = session.run(None, {session.get_inputs()[0].name: np.zeros((1, contract["observations"]), dtype=np.float32)})[0]
    except ImportError:
        warn("SKIP: onnxruntime is not installed; runtime check was skipped")
        return 3
    except Exception as exc:
        return error("ONNX Runtime zero-input check failed: {}".format(exc))
    if tuple(value.shape) != (1, contract["actions"]):
        return error("ONNX Runtime output shape is {}, expected {}".format(tuple(value.shape), (1, contract["actions"])))
    if not np.isfinite(value).all():
        return error("ONNX Runtime output contains non-finite values")
    info("ONNX Runtime CPU zero-input check passed")
    return 0


def check_output_dir(path):
    path = Path(path)
    if path.exists():
        if not path.is_dir():
            return fail("output path is not a directory: {}".format(path))
        if not os.access(str(path), os.W_OK):
            return fail("output directory is not writable: {}".format(path))
        info("output directory is writable: {}".format(path))
        return True
    parent = path
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    if not os.access(str(parent), os.W_OK):
        return fail("nearest existing output parent is not writable: {}".format(parent))
    info("output directory can be created below {}".format(parent))
    return True


def build_parser():
    parser = argparse.ArgumentParser(
        description="Preflight X1 DH checkpoints or validate existing JIT/ONNX artifacts without Isaac Gym."
    )
    parser.add_argument("--task", required=True, help="registered task; x1_dh_stand is the verified contract")
    parser.add_argument("--kind", choices=("jit", "onnx"), default="jit")
    parser.add_argument("--logs-root", default="logs", help="project logs directory")
    parser.add_argument("--experiment-name", help="experiment directory; defaults to the task name")
    parser.add_argument("--load-run", default="-1", help="run name, or -1 for the lexicographically last run")
    parser.add_argument("--checkpoint", type=int, default=-1, help="training checkpoint number, or -1 for latest")
    parser.add_argument("--artifact", help="existing artifact to validate instead of selecting an input")
    parser.add_argument("--output-dir", help="directory whose creation/writability should be checked")
    parser.add_argument("--inspect-checkpoint", action="store_true", help="load and inspect model_state_dict with CPU PyTorch")
    parser.add_argument("--run-runtime-check", action="store_true", help="also use ONNX Runtime when installed")
    parser.add_argument("--allow-unknown-task", action="store_true", help="perform path checks without known shape assertions")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    contract = TASK_CONTRACTS.get(args.task)
    if contract is None and not args.allow_unknown_task:
        return 2 if fail("unknown task {}; pass --allow-unknown-task to skip shape assertions".format(args.task)) is False else 2
    if contract is None:
        warn("no bundled dimension contract for {}; shape checks are disabled".format(args.task))

    if args.output_dir and not check_output_dir(args.output_dir):
        return 1

    if args.artifact:
        artifact = Path(args.artifact)
        if not artifact.is_file():
            return 1 if fail("artifact does not exist or is not a file: {}".format(artifact)) is False else 1
        if artifact.stat().st_size == 0:
            return 1 if fail("artifact is empty: {}".format(artifact)) is False else 1
        info("artifact exists and is non-empty: {}".format(artifact))
        if args.kind == "jit":
            return validate_jit(artifact, contract)
        return validate_onnx(artifact, contract, args.run_runtime_check)

    experiment = args.experiment_name or args.task
    if args.kind == "jit":
        root = Path(args.logs_root) / experiment / "exported_data"
        try:
            checkpoint = select_training_checkpoint(root, args.load_run, args.checkpoint)
        except (OSError, ValueError) as exc:
            return 1 if fail(str(exc)) is False else 1
        if not checkpoint.is_file() or checkpoint.stat().st_size == 0:
            return 1 if fail("selected checkpoint is missing or empty: {}".format(checkpoint)) is False else 1
        info("selected training checkpoint: {}".format(checkpoint))
        if args.inspect_checkpoint:
            return inspect_checkpoint(checkpoint, contract)
        return 0

    if args.checkpoint != -1:
        warn("--checkpoint is ignored by the source ONNX exporter; it selects a JIT artifact, not a training checkpoint")
    root = Path(args.logs_root) / experiment / "exported_policies"
    try:
        jit_path = select_jit_artifact(root, args.load_run)
    except (OSError, ValueError) as exc:
        return 1 if fail(str(exc)) is False else 1
    if jit_path.stat().st_size == 0:
        return 1 if fail("selected JIT input is empty: {}".format(jit_path)) is False else 1
    info("selected JIT input for ONNX conversion: {}".format(jit_path))
    return validate_jit(jit_path, contract)


if __name__ == "__main__":
    sys.exit(main())
