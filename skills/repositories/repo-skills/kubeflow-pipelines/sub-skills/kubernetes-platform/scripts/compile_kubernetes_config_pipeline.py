#!/usr/bin/env python3
"""Compile-only smoke test for kfp-kubernetes task configuration.

This script compiles a tiny KFP pipeline and asserts that representative
Kubernetes platform markers appear in the emitted YAML. It never contacts a
Kubeflow Pipelines API server or Kubernetes cluster.
"""

import argparse
import importlib.metadata as metadata
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict

try:
    import yaml
    import kfp
    from kfp import compiler, dsl, kubernetes
except ModuleNotFoundError as exc:  # pragma: no cover - exercised by users.
    missing = exc.name or "required package"
    print(
        "Missing dependency while importing kfp-kubernetes smoke helper: "
        f"{missing}. Install matching KFP packages, for example "
        "`pip install kfp[kubernetes]` or `pip install kfp-kubernetes`.",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


@dsl.component(base_image="python:3.11")
def emit_message():
    print("kubernetes platform smoke")


@dsl.pipeline(name="kubernetes-platform-compile-smoke")
def kubernetes_platform_pipeline() -> None:
    task = emit_message()

    returned = kubernetes.use_secret_as_env(
        task,
        secret_name="training-secret",
        secret_key_to_env={"token": "TRAINING_TOKEN"},
        optional=True,
    )
    assert returned is task, "use_secret_as_env should return the same PipelineTask"

    returned = kubernetes.add_node_selector(
        task,
        label_key="cloud.google.com/gke-accelerator",
        label_value="nvidia-tesla-t4",
    )
    assert returned is task, "add_node_selector should return the same PipelineTask"

    returned = kubernetes.add_toleration(
        task,
        key="accelerator",
        operator="Equal",
        value="nvidia",
        effect="NoSchedule",
    )
    assert returned is task, "add_toleration should return the same PipelineTask"


def _assert_package_versions_match() -> None:
    try:
        kfp_kubernetes_version = metadata.version("kfp-kubernetes")
    except metadata.PackageNotFoundError as exc:
        raise AssertionError(
            "Distribution metadata for `kfp-kubernetes` was not found. "
            "Install the addon in the same environment as `kfp`."
        ) from exc

    if kfp.__version__ != kfp_kubernetes_version:
        raise AssertionError(
            "Expected matching `kfp` and `kfp-kubernetes` versions, got "
            f"kfp={kfp.__version__!r}, "
            f"kfp-kubernetes={kfp_kubernetes_version!r}."
        )


def _load_platform_spec(package_path: Path) -> Dict[str, Any]:
    docs = list(yaml.safe_load_all(package_path.read_text()))
    if len(docs) < 2:
        raise AssertionError(
            "Expected a compiled YAML package with a Kubernetes platform "
            f"document, got {len(docs)} document(s)."
        )
    platform_spec = docs[1]
    if not isinstance(platform_spec, dict):
        raise AssertionError("Compiled platform document is not a mapping.")
    return platform_spec


def _assert_platform_markers(platform_spec: Dict[str, Any], raw_yaml: str) -> None:
    try:
        executors = platform_spec["platforms"]["kubernetes"]["deploymentSpec"][
            "executors"
        ]
    except KeyError as exc:
        raise AssertionError(
            "Compiled YAML is missing platforms.kubernetes.deploymentSpec.executors."
        ) from exc

    executor_configs = list(executors.values())
    if not executor_configs:
        raise AssertionError("No executor platform configs were emitted.")

    if not any("secretAsEnv" in config for config in executor_configs):
        raise AssertionError("Expected a `secretAsEnv` Kubernetes marker.")
    if "training-secret" not in raw_yaml or "TRAINING_TOKEN" not in raw_yaml:
        raise AssertionError("Expected Secret name and env var markers in YAML.")

    node_selector_values = [
        config.get("nodeSelector", {}).get("labels", {})
        for config in executor_configs
    ]
    if not any(
        labels.get("cloud.google.com/gke-accelerator") == "nvidia-tesla-t4"
        for labels in node_selector_values
    ):
        raise AssertionError("Expected nodeSelector label marker in YAML.")

    tolerations = []
    for config in executor_configs:
        tolerations.extend(config.get("tolerations", []))
    if not any(
        toleration.get("key") == "accelerator"
        and toleration.get("operator") == "Equal"
        and toleration.get("value") == "nvidia"
        and toleration.get("effect") == "NoSchedule"
        for toleration in tolerations
    ):
        raise AssertionError("Expected toleration marker in YAML.")


def compile_and_check(output_path: Path) -> Path:
    _assert_package_versions_match()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    compiler.Compiler().compile(kubernetes_platform_pipeline, str(output_path))
    raw_yaml = output_path.read_text()
    platform_spec = _load_platform_spec(output_path)
    _assert_platform_markers(platform_spec, raw_yaml)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a tiny KFP pipeline using kfp-kubernetes helpers and "
            "assert Kubernetes platform YAML markers. No cluster is required."
        )
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output YAML path. Defaults to a temporary file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.output is None:
        output_path = Path(tempfile.mkdtemp(prefix="kfp-kubernetes-smoke-")) / "pipeline.yaml"
    else:
        output_path = args.output

    compiled_path = compile_and_check(output_path)
    print(f"Compiled Kubernetes platform smoke pipeline: {compiled_path}")
    print("Verified compile-only markers: secretAsEnv, nodeSelector, tolerations")


if __name__ == "__main__":
    main()
