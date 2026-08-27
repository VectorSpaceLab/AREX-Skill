#!/usr/bin/env python3
# ------------------------------------------------------------------------
# RF-DETR
# Copyright (c) 2025 Roboflow. All Rights Reserved.
# Licensed under the Apache License, Version 2.0 [see LICENSE for details]
# ------------------------------------------------------------------------
"""Recommend RF-DETR contributor checks for changed paths without running them."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class Recommendation:
    """A command recommendation emitted by this script.

    Args:
        key: Stable key used for de-duplication.
        title: Short display title.
        command: Shell command to run from the RF-DETR repository root.
        reason: Why this command is relevant.
        note: Optional caveat, backend requirement, or scope note.
    """

    key: str
    title: str
    command: str
    reason: str
    note: str | None = None


@dataclass
class RecommendationSet:
    """Collect de-duplicated recommendations while preserving insertion order.

    Examples:
        >>> recs = RecommendationSet()
        >>> recs.add(Recommendation("unit", "Unit", "pytest tests/unit", "changed code"))
        >>> recs.add(Recommendation("unit", "Unit", "pytest tests/unit", "duplicate"))
        >>> [rec.key for rec in recs.items]
        ['unit']
    """

    items: list[Recommendation] = field(default_factory=list)
    _seen: set[str] = field(default_factory=set)

    def add(self, recommendation: Recommendation) -> None:
        """Add a recommendation if its key has not already been seen.

        Args:
            recommendation: Recommendation to append.
        """

        if recommendation.key in self._seen:
            return
        self._seen.add(recommendation.key)
        self.items.append(recommendation)

    def extend(self, recommendations: Iterable[Recommendation]) -> None:
        """Add multiple recommendations in order.

        Args:
            recommendations: Recommendations to append if unique.
        """

        for recommendation in recommendations:
            self.add(recommendation)


CPU_CI = Recommendation(
    key="cpu-ci",
    title="CPU CI-style pytest",
    command=(
        'uv run --no-sync pytest src/ tests/ -n 2 '
        '-m "not gpu and not coco17 and not e2e_coreml and not e2e_executorch and not xla and not tpu" '
        "--ignore=tests/run_smoke_all_models.py --ignore=tests/legacy/test_checkpoint_compat.py "
        "--cov=rfdetr --cov-report=xml --timeout=420 --durations=50"
    ),
    reason="broad required CPU behavior gate",
)

PRE_COMMIT = Recommendation(
    key="pre-commit",
    title="Full pre-commit",
    command="pre-commit run --all-files",
    reason="required formatting, lint, type, docs, spelling, and license hooks before handoff",
)

DOCS_BUILD = Recommendation(
    key="docs-build",
    title="Docs build",
    command='uv pip install -e ".[plus]" --group docs && uv run --no-sync mkdocs build --verbose',
    reason="documentation or API-reference surface changed",
    note="requires the public Plus package for XLarge/2XLarge reference pages",
)

PACKAGE_BUILD = Recommendation(
    key="package-build",
    title="Package build",
    command="uv pip install --group build && uv build && uv run --no-sync twine check --strict dist/*",
    reason="packaging, build metadata, package data, or distribution metadata changed",
)

DEPENDENCY_RESOLUTION = Recommendation(
    key="dependency-resolution",
    title="Dependency resolution",
    command="uv lock --quiet && uv sync --no-default-groups --extra EXTRA --python PYTHON --dry-run",
    reason="dependency metadata, extras, uv conflicts, or install-plan behavior changed",
    note="replace EXTRA and PYTHON with the affected optional extra and supported interpreter versions",
)

MYPY = Recommendation(
    key="mypy",
    title="Strict mypy",
    command="uv run --no-sync mypy src/rfdetr/ --no-error-summary",
    reason="typed source or typing configuration changed",
)

CLI_HELP = Recommendation(
    key="cli-help",
    title="CLI help smoke",
    command="uv run --no-sync rfdetr --help && uv run --no-sync python -m rfdetr --help",
    reason="CLI entry point or command surface changed",
)

GPU_TESTS = Recommendation(
    key="gpu-tests",
    title="GPU pytest",
    command=(
        'uv run --no-sync pytest tests/ -m "gpu and not e2e_tensorrt" '
        "--ignore=tests/legacy/test_checkpoint_compat.py -n 3 "
        '--reruns 1 --only-rerun "OutOfMemoryError" --cov=rfdetr --cov-report=xml '
        "--timeout=600 --durations=20"
    ),
    reason="GPU behavior or CUDA-sensitive path changed",
    note="requires CUDA-capable environment with RF-DETR GPU dependencies",
)

XLA_TESTS = Recommendation(
    key="xla-tests",
    title="XLA CPU-PJRT pytest",
    command=(
        'PJRT_DEVICE=CPU uv run --no-sync pytest src/ tests/ -n 1 -m "xla and not gpu and not tpu" '
        "--ignore=tests/run_smoke_all_models.py --ignore=tests/legacy/test_checkpoint_compat.py "
        "--timeout=420 --durations=50"
    ),
    reason="XLA-marked behavior changed",
    note="requires Linux torch_xla runtime with torch and torch_xla minor versions aligned",
)

EXECUTORCH_TESTS = Recommendation(
    key="executorch-tests",
    title="ExecuTorch parity pytest",
    command=(
        "uv run --no-sync pytest tests/export/test_executorch_export.py "
        "-m e2e_executorch -n 1 --timeout=600 --durations=20"
    ),
    reason="ExecuTorch export or runtime behavior changed",
    note="requires the ExecuTorch extra and compatible torch ABI",
)

COREML_TESTS = Recommendation(
    key="coreml-tests",
    title="CoreML parity pytest",
    command=(
        "uv run --no-sync pytest tests/export/test_coreml_export.py "
        "-m e2e_coreml -n 1 --timeout=600 --durations=20"
    ),
    reason="CoreML export or runtime behavior changed",
    note="macOS-only backend check",
)

TENSORRT_TESTS = Recommendation(
    key="tensorrt-tests",
    title="TensorRT parity pytest",
    command=(
        "uv run --no-sync pytest tests/export/test_tensorrt_export.py "
        "-m e2e_tensorrt -n 1 --timeout=600 --durations=20"
    ),
    reason="TensorRT export, engine build, or runtime behavior changed",
    note="requires CUDA, TensorRT/polygraphy, and CUDA runtime loader access",
)

SMOKE_ALL_MODELS = Recommendation(
    key="smoke-all-models",
    title="All-model smoke script",
    command="python tests/run_smoke_all_models.py",
    reason="model registry, public variants, downloads, or model instantiation changed",
    note="downloads weights and can be slower than unit tests",
)

LEGACY_CHECKPOINTS = Recommendation(
    key="legacy-checkpoints",
    title="Legacy checkpoint compatibility",
    command="uv run --no-sync pytest tests/legacy/ -v --tb=short --timeout=120",
    reason="checkpoint serialization or loading compatibility changed",
    note="advisory only; default required CPU gate ignores legacy checkpoint compatibility",
)

MODEL_SELECTION_AUDIT = Recommendation(
    key="model-selection-audit",
    title="Model-selection audit",
    command=(
        "rg -n \"RFDETRBase|rfdetr-base|RFDETRSegPreview|rfdetr-seg-preview|preview\" "
        "docs tests configs src README.md"
    ),
    reason="examples, docs, configs, or model variant text changed",
    note="new detection defaults should use RFDETRSmall/rfdetr-small; preview is only for keypoints",
)

FOCUSED_BY_PREFIX: tuple[tuple[str, Recommendation], ...] = (
    (
        "src/rfdetr/models/",
        Recommendation("tests-models", "Model tests", "uv run --no-sync pytest tests/models/", "model internals changed"),
    ),
    (
        "src/rfdetr/inference.py",
        Recommendation(
            "tests-inference", "Inference tests", "uv run --no-sync pytest tests/inference/", "public inference path changed"
        ),
    ),
    (
        "src/rfdetr/variants.py",
        Recommendation("tests-variants", "Variant/model tests", "uv run --no-sync pytest tests/models/ tests/inference/", "variant registry changed"),
    ),
    (
        "src/rfdetr/detr.py",
        Recommendation("tests-public-api", "Public API tests", "uv run --no-sync pytest tests/models/ tests/inference/ tests/training/", "RFDETR public wrapper changed"),
    ),
    (
        "src/rfdetr/datasets/",
        Recommendation("tests-datasets", "Dataset tests", "uv run --no-sync pytest tests/datasets/", "dataset code changed"),
    ),
    (
        "src/rfdetr/training/",
        Recommendation("tests-training", "Training tests", "uv run --no-sync pytest tests/training/ tests/models/test_evaluate.py", "training stack changed"),
    ),
    (
        "src/rfdetr/export/",
        Recommendation("tests-export", "Export tests", "uv run --no-sync pytest tests/export/", "export code changed"),
    ),
    (
        "src/rfdetr/evaluation/",
        Recommendation("tests-evaluation", "Evaluation tests", "uv run --no-sync pytest tests/evaluation/ tests/models/test_evaluate.py", "evaluation code changed"),
    ),
    (
        "src/rfdetr/utilities/",
        Recommendation("tests-utilities", "Utility tests", "uv run --no-sync pytest tests/utilities/", "utility code changed"),
    ),
    (
        "src/rfdetr/visualize/",
        Recommendation("tests-visualize", "Visualization tests", "uv run --no-sync pytest tests/visualize/", "visualization code changed"),
    ),
    (
        "src/rfdetr/cli/",
        Recommendation("tests-cli", "CLI tests", "uv run --no-sync pytest tests/cli/ tests/training/test_cli.py", "CLI code changed"),
    ),
    (
        "tests/models/",
        Recommendation("tests-models", "Model tests", "uv run --no-sync pytest tests/models/", "model tests changed"),
    ),
    (
        "tests/inference/",
        Recommendation("tests-inference", "Inference tests", "uv run --no-sync pytest tests/inference/", "inference tests changed"),
    ),
    (
        "tests/datasets/",
        Recommendation("tests-datasets", "Dataset tests", "uv run --no-sync pytest tests/datasets/", "dataset tests changed"),
    ),
    (
        "tests/training/",
        Recommendation("tests-training", "Training tests", "uv run --no-sync pytest tests/training/", "training tests changed"),
    ),
    (
        "tests/export/",
        Recommendation("tests-export", "Export tests", "uv run --no-sync pytest tests/export/", "export tests changed"),
    ),
    (
        "tests/evaluation/",
        Recommendation("tests-evaluation", "Evaluation tests", "uv run --no-sync pytest tests/evaluation/", "evaluation tests changed"),
    ),
    (
        "tests/utilities/",
        Recommendation("tests-utilities", "Utility tests", "uv run --no-sync pytest tests/utilities/", "utility tests changed"),
    ),
    (
        "tests/visualize/",
        Recommendation("tests-visualize", "Visualization tests", "uv run --no-sync pytest tests/visualize/", "visualization tests changed"),
    ),
    (
        "tests/cli/",
        Recommendation("tests-cli", "CLI tests", "uv run --no-sync pytest tests/cli/", "CLI tests changed"),
    ),
)


def normalize_path(raw_path: str) -> str:
    """Normalize a user-supplied path to a repository-relative POSIX-ish string.

    Args:
        raw_path: Path argument passed to the script.

    Returns:
        Normalized path with leading ``./`` removed and backslashes converted.

    Examples:
        >>> normalize_path('./src/rfdetr/models/model.py')
        'src/rfdetr/models/model.py'
        >>> normalize_path('tests\\models\\test_model.py')
        'tests/models/test_model.py'
    """

    path = raw_path.replace("\\", "/").strip()
    while path.startswith("./"):
        path = path[2:]
    return str(PurePosixPath(path)) if path else path


def contains_segment(path: str, segment: str) -> bool:
    """Return whether a POSIX path contains a segment.

    Args:
        path: Normalized path to inspect.
        segment: Segment name to find.

    Returns:
        Whether *segment* appears as a full path component.

    Examples:
        >>> contains_segment('tests/export/test_coreml_export.py', 'export')
        True
        >>> contains_segment('tests/export/test_coreml_export.py', 'port')
        False
    """

    return segment in PurePosixPath(path).parts


def add_path_recommendations(path: str, recs: RecommendationSet) -> None:
    """Add recommendations for one normalized path.

    Args:
        path: Repository-relative path.
        recs: Mutable recommendation set to update.
    """

    for prefix, recommendation in FOCUSED_BY_PREFIX:
        if path == prefix.rstrip("/") or path.startswith(prefix):
            recs.add(recommendation)

    if path.startswith("src/rfdetr/"):
        recs.add(MYPY)

    if path.startswith(("docs/", "mkdocs.yaml", "README.md")):
        recs.add(DOCS_BUILD)
        recs.add(MODEL_SELECTION_AUDIT)

    if path.startswith(("configs/", "docs/", "README.md", "tests/", "src/rfdetr/variants.py")):
        recs.add(MODEL_SELECTION_AUDIT)

    if path in {"pyproject.toml", "uv.lock"} or path.startswith("requirements"):
        recs.extend([DEPENDENCY_RESOLUTION, PACKAGE_BUILD, MYPY])

    if path.startswith(".github/workflows/"):
        recs.add(DEPENDENCY_RESOLUTION if "deps" in path else CPU_CI)

    if path == ".pre-commit-config.yaml" or path.startswith(".github/LICENSE_HEADER"):
        recs.add(PRE_COMMIT)

    if path.startswith("src/rfdetr/cli/") or path.startswith("tests/cli/") or path == "src/rfdetr/__main__.py":
        recs.add(CLI_HELP)

    if path.startswith("configs/"):
        recs.add(Recommendation("tests-configs", "Config tests", "uv run --no-sync pytest tests/cli/test_configs.py tests/training/test_args.py", "config files changed"))

    if "checkpoint" in path or "state_dict" in path or "safe_torch_load" in path:
        recs.add(LEGACY_CHECKPOINTS)

    lower = path.lower()
    if "gpu" in lower or "cuda" in lower or "kornia" in lower:
        recs.add(GPU_TESTS)
    if "xla" in lower or "tpu" in lower:
        recs.add(XLA_TESTS)
    if "executorch" in lower:
        recs.add(EXECUTORCH_TESTS)
    if "coreml" in lower:
        recs.add(COREML_TESTS)
    if "tensorrt" in lower or "trt" in lower:
        recs.add(TENSORRT_TESTS)
    if "tflite" in lower or "onnx" in lower or "export" in PurePosixPath(path).parts:
        recs.add(DEPENDENCY_RESOLUTION)
    if path == "tests/run_smoke_all_models.py" or "model_weights" in lower or "platform/models" in lower:
        recs.add(SMOKE_ALL_MODELS)

    if path.startswith("tests/"):
        recs.add(
            Recommendation(
                "doctest-plus",
                "Doctest-plus awareness",
                "uv run --no-sync pytest CHANGED_TEST_FILE_OR_DIRECTORY --doctest-plus",
                "test helpers and fixtures may need executable Examples doctests",
            )
        )


def build_recommendations(paths: Iterable[str], include_baseline: bool) -> RecommendationSet:
    """Build check recommendations for changed paths.

    Args:
        paths: Raw path strings from the command line.
        include_baseline: Whether to include broad CPU and pre-commit gates.

    Returns:
        De-duplicated recommendation set.

    Examples:
        >>> recs = build_recommendations(['src/rfdetr/export/_coreml/foo.py'], include_baseline=False)
        >>> [rec.key for rec in recs.items if rec.key in {'tests-export', 'coreml-tests'}]
        ['tests-export', 'coreml-tests']
    """

    recs = RecommendationSet()
    normalized_paths = [normalize_path(path) for path in paths if normalize_path(path)]

    for path in normalized_paths:
        add_path_recommendations(path, recs)

    if include_baseline:
        recs.extend([CPU_CI, PRE_COMMIT])
    elif not recs.items:
        recs.add(CPU_CI)
        recs.add(PRE_COMMIT)

    return recs


def render_recommendations(paths: list[str], recs: RecommendationSet) -> str:
    """Render recommendations as Markdown-ish plain text.

    Args:
        paths: Normalized paths used to build recommendations.
        recs: Recommendation set to render.

    Returns:
        Human-readable recommendation report.

    Examples:
        >>> recs = RecommendationSet([Recommendation('x', 'X', 'echo x', 'because')], {'x'})
        >>> 'echo x' in render_recommendations(['a.py'], recs)
        True
    """

    lines = ["RF-DETR recommended checks (dry run; no commands executed)", ""]
    if paths:
        lines.append("Changed paths:")
        lines.extend(f"- {path}" for path in paths)
        lines.append("")
    else:
        lines.append("No changed paths supplied; showing broad baseline checks.")
        lines.append("")

    for index, rec in enumerate(recs.items, start=1):
        lines.append(f"{index}. {rec.title}")
        lines.append(f"   Reason: {rec.reason}")
        if rec.note:
            lines.append(f"   Note: {rec.note}")
        lines.append("   Command:")
        lines.append(f"     {rec.command}")
        lines.append("")

    lines.append("Always run commands from the RF-DETR repository root after installing the required extras/groups.")
    lines.append("Backend-specific recommendations identify requirements but do not prove the backend is available locally.")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """

    parser = argparse.ArgumentParser(
        description="Recommend RF-DETR checks for changed paths without running tests.",
    )
    parser.add_argument("paths", nargs="*", help="Changed files or directories relative to the RF-DETR repository root.")
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Do not automatically append broad CPU pytest and pre-commit recommendations.",
    )
    return parser.parse_args()


def main() -> None:
    """Print RF-DETR check recommendations."""

    args = parse_args()
    normalized_paths = [normalize_path(path) for path in args.paths if normalize_path(path)]
    recs = build_recommendations(normalized_paths, include_baseline=not args.no_baseline)
    print(render_recommendations(normalized_paths, recs))


if __name__ == "__main__":
    main()
