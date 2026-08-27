#!/usr/bin/env python3
"""
Render TensorFlowOnSpark spark-submit and SavedModel command plans.

This helper is intentionally render-only. It prints commands for review; it does
not execute Spark, Docker, network downloads, service changes, or file deletion.
All paths must be supplied by the caller.
"""

from __future__ import annotations

import argparse
import posixpath
import shlex
import sys
from typing import Iterable, List, Sequence


SPARK_WORKFLOWS = {
    "mnist-tensorflow-train",
    "mnist-spark-train",
    "mnist-pipeline-train",
    "mnist-pipeline-inference",
    "batch-inference",
    "generic-tensorflow-train",
    "generic-spark-train",
    "resnet-tensorflow-train",
    "segmentation-tensorflow-train",
}


def q(value: object) -> str:
    return shlex.quote(str(value))


def spark_submit_path(args: argparse.Namespace) -> str:
    if args.spark_submit:
        return args.spark_submit
    return posixpath.join(args.spark_home, "bin", "spark-submit")


def total_cores(args: argparse.Namespace) -> str:
    if args.total_cores is not None:
        return str(args.total_cores)
    return str(args.cluster_size * args.cores_per_worker)


def add_if(tokens: List[str], condition: bool, values: Sequence[object]) -> None:
    if condition:
        tokens.extend(str(v) for v in values)


def add_extra_args(tokens: List[str], extra_args: Iterable[str] | None) -> None:
    if extra_args:
        tokens.extend(extra_args)


def render_command(title: str, tokens: Sequence[str]) -> str:
    lines = [f"# {title}"]
    if not tokens:
        return "\n".join(lines)
    if len(tokens) == 1:
        lines.append(q(tokens[0]))
        return "\n".join(lines)
    lines.append(q(tokens[0]) + " \\")
    for token in tokens[1:-1]:
        lines.append(f"  {q(token)} \\")
    lines.append(f"  {q(tokens[-1])}")
    return "\n".join(lines)


def base_spark_tokens(args: argparse.Namespace) -> List[str]:
    tokens = [
        spark_submit_path(args),
        "--master",
        args.master,
        "--conf",
        f"spark.cores.max={total_cores(args)}",
        "--conf",
        f"spark.task.cpus={args.cores_per_worker}",
    ]
    for conf in args.conf or []:
        tokens.extend(["--conf", conf])
    add_if(tokens, bool(args.java_home), ["--conf", f"spark.executorEnv.JAVA_HOME={args.java_home}"])
    add_if(tokens, bool(args.jars), ["--jars", args.jars])
    add_if(tokens, bool(args.py_files), ["--py-files", args.py_files])
    tokens.append(args.app_script)
    return tokens


def common_train_args(args: argparse.Namespace) -> List[str]:
    tokens = [
        "--cluster_size",
        str(args.cluster_size),
        "--model_dir",
        args.model_dir,
        "--export_dir",
        args.export_dir,
        "--epochs",
        str(args.epochs),
        "--batch_size",
        str(args.batch_size),
    ]
    add_if(tokens, bool(args.steps_per_epoch), ["--steps_per_epoch", str(args.steps_per_epoch)])
    add_if(tokens, args.tensorboard, ["--tensorboard"])
    return tokens


def mnist_tensorflow_train(args: argparse.Namespace) -> List[str]:
    return base_spark_tokens(args) + common_train_args(args)


def mnist_spark_train(args: argparse.Namespace) -> List[str]:
    return base_spark_tokens(args) + [
        "--cluster_size",
        str(args.cluster_size),
        "--images_labels",
        args.images_labels,
        "--model_dir",
        args.model_dir,
        "--export_dir",
        args.export_dir,
        "--epochs",
        str(args.epochs),
        "--batch_size",
        str(args.batch_size),
    ] + (["--tensorboard"] if args.tensorboard else [])


def pipeline_train(args: argparse.Namespace) -> List[str]:
    return base_spark_tokens(args) + [
        "--cluster_size",
        str(args.cluster_size),
        "--images_labels",
        args.images_labels,
        "--format",
        args.input_format,
        "--mode",
        "train",
        "--model_dir",
        args.model_dir,
        "--export_dir",
        args.export_dir,
        "--epochs",
        str(args.epochs),
        "--batch_size",
        str(args.batch_size),
    ] + (["--tensorboard"] if args.tensorboard else [])


def pipeline_inference(args: argparse.Namespace) -> List[str]:
    return base_spark_tokens(args) + [
        "--cluster_size",
        str(args.cluster_size),
        "--images_labels",
        args.images_labels,
        "--format",
        args.input_format,
        "--mode",
        "inference",
        "--export_dir",
        args.export_dir,
        "--output",
        args.output,
        "--batch_size",
        str(args.batch_size),
    ]


def batch_inference(args: argparse.Namespace) -> List[str]:
    return base_spark_tokens(args) + [
        "--cluster_size",
        str(args.cluster_size),
        "--images_labels",
        args.images_labels,
        "--export_dir",
        args.export_dir,
        "--output",
        args.output,
    ]


def resnet_train(args: argparse.Namespace) -> List[str]:
    tokens = base_spark_tokens(args) + [
        "--cluster_size",
        str(args.cluster_size),
        "--num_ps",
        str(args.num_ps),
    ]
    add_if(tokens, args.tensorboard, ["--tensorboard"])
    tokens.extend([
        "--epochs",
        str(args.epochs),
        "--data_dir",
        args.data_dir,
        "--num_gpus",
        str(args.num_gpus),
        "--ds",
        args.distribution_strategy,
        "--train_epochs",
        str(args.train_epochs),
    ])
    add_extra_args(tokens, args.extra_app_arg)
    return tokens


def segmentation_train(args: argparse.Namespace) -> List[str]:
    return base_spark_tokens(args) + common_train_args(args)


def saved_model_cli_commands(args: argparse.Namespace) -> List[str]:
    commands = [
        render_command("Inspect SavedModel signatures", [
            "saved_model_cli",
            "show",
            "--dir",
            args.saved_model_dir,
            "--all",
        ])
    ]
    if args.input_exp:
        commands.append(render_command("Run one SavedModel inference example", [
            "saved_model_cli",
            "run",
            "--dir",
            args.saved_model_dir,
            "--tag_set",
            args.tag_set,
            "--signature_def",
            args.signature_def,
            "--input_exp",
            args.input_exp,
        ]))
    else:
        commands.append("# Add --input-exp after inspecting tensor names to render an inference command.")
    return commands


def required_for_workflow(workflow: str) -> List[str]:
    req = []
    if workflow in SPARK_WORKFLOWS:
        req.extend(["master", "app_script", "cluster_size"])
    if workflow in {
        "mnist-tensorflow-train",
        "generic-tensorflow-train",
        "segmentation-tensorflow-train",
    }:
        req.extend(["model_dir", "export_dir"])
    if workflow in {"mnist-spark-train", "generic-spark-train"}:
        req.extend(["images_labels", "model_dir", "export_dir"])
    if workflow == "mnist-pipeline-train":
        req.extend(["images_labels", "model_dir", "export_dir"])
    if workflow == "mnist-pipeline-inference":
        req.extend(["images_labels", "export_dir", "output"])
    if workflow == "batch-inference":
        req.extend(["images_labels", "export_dir", "output"])
    if workflow == "resnet-tensorflow-train":
        req.extend(["data_dir"])
    if workflow == "saved-model-cli":
        req.extend(["saved_model_dir"])
    return req


def validate(args: argparse.Namespace) -> List[str]:
    missing = []
    if args.workflow in SPARK_WORKFLOWS and not (args.spark_submit or args.spark_home):
        missing.append("spark_submit or spark_home")
    for name in required_for_workflow(args.workflow):
        if getattr(args, name) in (None, ""):
            missing.append(name.replace("_", "-"))
    return missing


def warnings_for(args: argparse.Namespace) -> List[str]:
    warnings = []
    if args.workflow.startswith("mnist-pipeline") and not args.jars:
        warnings.append("Pipeline TFRecord/DataFrame workflows often need the TensorFlow Hadoop jar; add --jars when using TFRecords or site classpath is not preconfigured.")
    if args.workflow == "resnet-tensorflow-train" and not args.py_files:
        warnings.append("ResNet-style conversions usually require --py-files or installed packages so executors can import the TensorFlow model module.")
    if args.workflow in {"mnist-tensorflow-train", "segmentation-tensorflow-train"}:
        warnings.append("TensorFlow-native data readers may access datasets from every worker; pre-stage data or caches on managed clusters.")
    if args.workflow in {"mnist-spark-train", "generic-spark-train"}:
        warnings.append("Spark-fed synchronous training needs balanced partitions and enough rows per worker; route feed stalls to datafeed-inputmode.")
    if args.workflow == "batch-inference":
        warnings.append("Each executor loads the SavedModel independently; confirm executor memory before running the rendered command.")
    return warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render dry-run TensorFlowOnSpark command plans from caller-provided paths."
    )
    parser.add_argument("--workflow", required=True, choices=sorted(SPARK_WORKFLOWS | {"saved-model-cli"}))
    parser.add_argument("--spark-home", help="Spark home directory used to derive bin/spark-submit.")
    parser.add_argument("--spark-submit", help="Explicit spark-submit executable path.")
    parser.add_argument("--master", help="Spark master URL, yarn, or site-specific master string.")
    parser.add_argument("--app-script", help="Converted application script to pass to spark-submit.")
    parser.add_argument("--cluster-size", type=int, help="Number of TensorFlow worker nodes requested by the application.")
    parser.add_argument("--cores-per-worker", type=int, default=1)
    parser.add_argument("--total-cores", type=int, help="Override spark.cores.max; defaults to cluster-size times cores-per-worker.")
    parser.add_argument("--conf", action="append", help="Additional Spark --conf entry. May be repeated.")
    parser.add_argument("--java-home", help="Value for spark.executorEnv.JAVA_HOME.")
    parser.add_argument("--jars", help="Comma-separated jar paths for Spark --jars.")
    parser.add_argument("--py-files", help="Comma-separated Python files/archives for Spark --py-files.")
    parser.add_argument("--images-labels", help="Executor-visible input directory for MNIST/image-label rows or records.")
    parser.add_argument("--model-dir", help="Executor-visible checkpoint/model directory.")
    parser.add_argument("--export-dir", help="SavedModel export directory or versioned SavedModel directory, depending on workflow.")
    parser.add_argument("--output", help="Executor-visible prediction output directory.")
    parser.add_argument("--format", dest="input_format", choices=["csv", "tfr"], default="csv", help="Input format for pipeline workflows.")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--steps-per-epoch", type=int)
    parser.add_argument("--tensorboard", action="store_true", help="Render the application --tensorboard flag.")
    parser.add_argument("--num-ps", type=int, default=0, help="Parameter-server count for ResNet/generic wrappers that expose it.")
    parser.add_argument("--data-dir", help="Executor-visible dataset directory for ResNet-style TensorFlow-native examples.")
    parser.add_argument("--num-gpus", type=int, default=0)
    parser.add_argument("--distribution-strategy", default="multi_worker_mirrored")
    parser.add_argument("--train-epochs", type=int, default=1)
    parser.add_argument("--extra-app-arg", action="append", help="Extra application argument token for ResNet-style wrappers. Repeat for each token.")
    parser.add_argument("--saved-model-dir", help="Versioned SavedModel directory for saved_model_cli.")
    parser.add_argument("--tag-set", default="serve")
    parser.add_argument("--signature-def", default="serving_default")
    parser.add_argument("--input-exp", help="saved_model_cli --input_exp value after tensor names are known.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    missing = validate(args)
    if missing:
        parser.error("missing required arguments for {}: {}".format(args.workflow, ", ".join(missing)))

    print("# TensorFlowOnSpark command plan")
    print("# Render-only: review before manual execution.")
    print("# No Spark job, Docker action, network download, service change, or file deletion was executed by this helper.")
    print("# Ensure every path is visible from the intended Spark executors.\n")

    for warning in warnings_for(args):
        print(f"# WARNING: {warning}")
    if warnings_for(args):
        print()

    if args.workflow == "saved-model-cli":
        print("\n\n".join(saved_model_cli_commands(args)))
        return 0

    builders = {
        "mnist-tensorflow-train": mnist_tensorflow_train,
        "mnist-spark-train": mnist_spark_train,
        "mnist-pipeline-train": pipeline_train,
        "mnist-pipeline-inference": pipeline_inference,
        "batch-inference": batch_inference,
        "generic-tensorflow-train": mnist_tensorflow_train,
        "generic-spark-train": mnist_spark_train,
        "resnet-tensorflow-train": resnet_train,
        "segmentation-tensorflow-train": segmentation_train,
    }
    tokens = builders[args.workflow](args)
    print(render_command(f"Run {args.workflow}", tokens))
    print("\n# Suggested validation after the manual run:")
    if args.export_dir:
        print(f"#   saved_model_cli show --dir {q(args.export_dir)} --all")
    if args.output:
        print(f"#   inspect prediction output at {q(args.output)}")
    if args.model_dir:
        print(f"#   inspect checkpoint/model output at {q(args.model_dir)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
