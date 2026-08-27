#!/usr/bin/env python3
"""Compile a tiny self-contained KFP authoring smoke pipeline.

The helper verifies that an installed KFP SDK can parse common authoring
constructs. It does not contact a KFP service, run containers, or read an
original source checkout.
"""

import argparse
from pathlib import Path
import tempfile

from kfp import compiler
from kfp import dsl


@dsl.component(base_image="python:3.11", packages_to_install=[])
def make_dataset(message: str, dataset: dsl.Output[dsl.Dataset]) -> str:
    """Write a small dataset artifact and return an upper-case parameter."""
    import json

    payload = {"message": message, "length": len(message)}
    with open(dataset.path, "w", encoding="utf-8") as output_file:
        json.dump(payload, output_file)
    dataset.metadata["format"] = "json"
    dataset.metadata["rows"] = 1
    return message.upper()


@dsl.component(base_image="python:3.11", packages_to_install=[])
def summarize_dataset(dataset: dsl.Input[dsl.Dataset]) -> int:
    """Read the dataset artifact and return the message length."""
    import json

    with open(dataset.path, "r", encoding="utf-8") as input_file:
        payload = json.load(input_file)
    return int(payload["length"])


@dsl.component(base_image="python:3.11", packages_to_install=[])
def record_metrics(length: int, metrics: dsl.Output[dsl.Metrics]):
    """Record a scalar metric artifact."""
    metrics.log_metric("message_length", float(length))


@dsl.container_component
def echo_container(text: str):
    """Container component used only to verify authoring-time syntax."""
    return dsl.ContainerSpec(
        image="python:3.11-slim",
        command=["python", "-c"],
        args=["import sys; print(sys.argv[1])", text],
    )


@dsl.pipeline(
    name="authoring-smoke-pipeline",
    description="Self-contained authoring smoke pipeline for the KFP DSL.",
    pipeline_root="gs://example-bucket/kfp-authoring-smoke",
)
def authoring_smoke_pipeline(
    message: str = "hello",
    run_container_step: str = "no",
) -> int:
    make_task = make_dataset(message=message)
    make_task.set_display_name("make dataset")
    make_task.set_cpu_limit("500m").set_memory_limit("512Mi")
    make_task.set_caching_options(enable_caching=True)

    summary_task = summarize_dataset(dataset=make_task.outputs["dataset"])
    summary_task.after(make_task)
    summary_task.set_retry(num_retries=1, backoff_duration="0s")
    summary_task.set_env_variable("AUTHORING_SMOKE", "true")

    record_metrics(length=summary_task.output).after(summary_task)

    with dsl.If(run_container_step == "yes"):
        echo_container(text=make_task.outputs["Output"]).after(summary_task)

    with dsl.ParallelFor(items=["alpha", "beta"], parallelism=1) as label:
        echo_container(text=label)

    return summary_task.output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a tiny KFP DSL pipeline that exercises component, "
            "container_component, artifact, task modifier, and control-flow "
            "authoring constructs."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=(
            "YAML output path. If omitted, a temporary directory is created "
            "and the output path is printed."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output is None:
        output_path = Path(tempfile.mkdtemp(prefix="kfp-authoring-smoke-")) / "pipeline.yaml"
    else:
        output_path = args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)

    compiler.Compiler().compile(
        pipeline_func=authoring_smoke_pipeline,
        package_path=str(output_path),
    )

    text = output_path.read_text(encoding="utf-8")
    required_markers = ["pipelineInfo:", "root:", "components:", "deploymentSpec:"]
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        raise RuntimeError(
            f"Compiled YAML is missing expected KFP sections: {', '.join(missing)}"
        )

    print(f"Compiled KFP authoring smoke pipeline: {output_path}")
    print("Validated markers: " + ", ".join(required_markers))


if __name__ == "__main__":
    main()
