#!/usr/bin/env python3
"""Freeze a LaneNet TensorFlow checkpoint into a frozen GraphDef (.pb).

This bundled helper adapts the repository's checkpoint-freezing workflow for
agent use. It preserves the public function name
``convert_ckpt_into_pb_file(ckpt_file_path, pb_file_path)`` while adding safer
CLI help, repo-root handling, checkpoint preflight checks, and node-name output.

Prerequisites:
  * A LaneNet checkout with ``lanenet_model/``, ``local_utils/``, and
    ``config/tusimple_lanenet.yaml`` available.
  * TensorFlow 1.x runtime compatible with the checkpoint. TensorFlow 1.15 is
    the verified target for this skill.
  * A checkpoint produced by the LaneNet training graph, preferably with moving
    average variables.

Example from this sub-skill directory:
  python scripts/freeze_lanenet_model.py \
    --repo-root <lanenet-repo-root> \
    --weights_path <checkpoint-prefix> \
    --save_path <output.pb>
"""
from __future__ import absolute_import, division, print_function

import argparse
import os
from pathlib import Path
import sys
from typing import Iterable, List

OUTPUT_NODE_NAMES = [
    "lanenet/input_tensor",
    "lanenet/final_binary_output",
    "lanenet/final_pixel_embedding_output",
]


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Freeze a LaneNet TensorFlow checkpoint into a frozen PB. The "
            "graph is built from the LaneNet repository at --repo-root, then "
            "the fixed export nodes are written into --save_path."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help=(
            "LaneNet repository root. The helper changes to this directory "
            "before importing repo modules because the repo config loader reads "
            "config/tusimple_lanenet.yaml relative to the current directory."
        ),
    )
    parser.add_argument(
        "-w",
        "--weights_path",
        required=False,
        default="./test.ckpt",
        help=(
            "TensorFlow checkpoint prefix to restore. Pass the prefix such as "
            "model.ckpt-10000; if a .index file is supplied, the suffix is "
            "stripped automatically."
        ),
    )
    parser.add_argument(
        "-s",
        "--save_path",
        required=False,
        default="./lanenet.pb",
        help="Destination frozen GraphDef (.pb) file.",
    )
    parser.add_argument(
        "--print-node-names",
        action="store_true",
        help="Print the fixed input/output node names used by the freeze and MNN runtime.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate repo-root/checkpoint arguments and print the planned export without importing TensorFlow.",
    )
    return parser


def _normalize_checkpoint_path(ckpt_file_path: str) -> str:
    """Return a TensorFlow Saver.restore-compatible checkpoint prefix."""
    raw = Path(ckpt_file_path).expanduser()
    text = str(raw)
    if text.endswith(".index"):
        raw = Path(text[:-len(".index")])
        text = str(raw)

    if raw.name == "checkpoint":
        raise ValueError(
            "Pass the actual checkpoint prefix (for example model.ckpt-10000), "
            "not the TensorFlow checkpoint state file named 'checkpoint'."
        )

    # TensorFlow 1 checkpoints commonly appear as prefix.index plus data/meta files.
    if Path(text + ".index").exists() or raw.exists():
        return text

    raise FileNotFoundError(
        "Checkpoint was not found. Expected either the supplied path itself or "
        "a '<checkpoint-prefix>.index' sidecar file: {}".format(ckpt_file_path)
    )


def _prepare_repo_imports(repo_root: str) -> Path:
    """Validate a LaneNet repo root, change into it, and add it to sys.path."""
    root = Path(repo_root).expanduser().resolve()
    required = [
        root / "lanenet_model",
        root / "local_utils",
        root / "config" / "tusimple_lanenet.yaml",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "--repo-root does not look like a LaneNet checkout; missing: {}".format(
                ", ".join(missing)
            )
        )
    sys.path.insert(0, str(root))
    os.chdir(str(root))
    return root


def _tf1():
    """Import TensorFlow and return its TF1-compatible API object."""
    try:
        import tensorflow as tf  # pylint: disable=import-outside-toplevel
    except ImportError as exc:  # pragma: no cover - depends on user environment
        raise ImportError(
            "TensorFlow is required to freeze LaneNet checkpoints. Use a "
            "TensorFlow 1.x-compatible environment; TensorFlow 1.15 was the "
            "verified target."
        ) from exc

    if hasattr(tf, "compat") and hasattr(tf.compat, "v1"):
        tf.compat.v1.disable_eager_execution()
        return tf.compat.v1, tf
    return tf, tf


def convert_ckpt_into_pb_file(ckpt_file_path, pb_file_path):
    """Convert a LaneNet checkpoint into a frozen PB file.

    Args:
        ckpt_file_path: TensorFlow checkpoint prefix, or a prefix ending in
            ``.index``. The checkpoint must match the LaneNet test graph and
            moving-average restore map.
        pb_file_path: Destination frozen GraphDef file.

    Returns:
        The list of output node names frozen into the graph.
    """
    ckpt_prefix = _normalize_checkpoint_path(ckpt_file_path)
    pb_path = Path(pb_file_path).expanduser()
    if pb_path.parent and str(pb_path.parent) != ".":
        pb_path.parent.mkdir(parents=True, exist_ok=True)

    tf1, tf_module = _tf1()
    from lanenet_model import lanenet  # pylint: disable=import-outside-toplevel
    from local_utils.config_utils import parse_config_utils  # pylint: disable=import-outside-toplevel

    cfg = parse_config_utils.lanenet_cfg
    tf1.reset_default_graph()

    with tf1.variable_scope("lanenet"):
        input_tensor = tf1.placeholder(
            dtype=tf_module.float32,
            shape=[1, 256, 512, 3],
            name="input_tensor",
        )

    net = lanenet.LaneNet(phase="test", cfg=cfg)
    binary_seg_ret, instance_seg_ret = net.inference(
        input_tensor=input_tensor,
        name="LaneNet",
    )

    with tf1.variable_scope("lanenet/"):
        binary_seg_ret = tf_module.cast(binary_seg_ret, dtype=tf_module.float32)
        tf_module.squeeze(binary_seg_ret, axis=0, name="final_binary_output")
        tf_module.squeeze(instance_seg_ret, axis=0, name="final_pixel_embedding_output")

    with tf1.variable_scope(name_or_scope="moving_avg"):
        variable_averages = tf1.train.ExponentialMovingAverage(
            cfg.SOLVER.MOVING_AVE_DECAY
        )
        variables_to_restore = variable_averages.variables_to_restore()

    saver = tf1.train.Saver(variables_to_restore)
    sess_config = tf1.ConfigProto()
    sess_config.gpu_options.per_process_gpu_memory_fraction = 0.85
    sess_config.gpu_options.allow_growth = False
    sess_config.gpu_options.allocator_type = "BFC"

    with tf1.Session(config=sess_config) as sess:
        saver.restore(sess, ckpt_prefix)
        converted_graph_def = tf1.graph_util.convert_variables_to_constants(
            sess,
            input_graph_def=sess.graph.as_graph_def(),
            output_node_names=OUTPUT_NODE_NAMES,
        )
        with tf1.gfile.GFile(str(pb_path), "wb") as output_file:
            output_file.write(converted_graph_def.SerializeToString())

    print("Wrote frozen LaneNet graph: {}".format(pb_path))
    print("Frozen nodes:")
    for node_name in OUTPUT_NODE_NAMES:
        print("  - {}".format(node_name))
    return list(OUTPUT_NODE_NAMES)


def _print_node_names(node_names: Iterable[str]) -> None:
    print("LaneNet freeze/MNN node names:")
    print("  input: {}".format(OUTPUT_NODE_NAMES[0]))
    print("  binary output: {}".format(OUTPUT_NODE_NAMES[1]))
    print("  pixel embedding output: {}".format(OUTPUT_NODE_NAMES[2]))


def main(argv: List[str] = None) -> int:
    args = _parser().parse_args(argv)
    if args.print_node_names:
        _print_node_names(OUTPUT_NODE_NAMES)
        if not args.dry_run:
            return 0

    repo_root = _prepare_repo_imports(args.repo_root)
    ckpt_prefix = _normalize_checkpoint_path(args.weights_path)
    save_path = Path(args.save_path).expanduser()

    if args.dry_run:
        print("LaneNet repo root: {}".format(repo_root))
        print("Checkpoint prefix: {}".format(ckpt_prefix))
        print("Frozen PB destination: {}".format(save_path))
        print("No TensorFlow graph was built because --dry-run was set.")
        return 0

    convert_ckpt_into_pb_file(ckpt_prefix, str(save_path))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # pragma: no cover - CLI guard for actionable errors
        print("freeze_lanenet_model.py: error: {}".format(exc), file=sys.stderr)
        raise SystemExit(2)
