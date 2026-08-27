#!/usr/bin/env python
"""Smoke-test TorchIO patch training and dense inference workflows.

The script uses only synthetic tensors. It verifies random samplers,
Queue + SubjectsLoader batching, GridSampler + PatchAggregator dense
inference, patch-location metadata, and multi-output aggregation.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any


torch: Any = None
tio: Any = None


@dataclass(frozen=True)
class SmokeConfig:
    shape: tuple[int, int, int]
    patch_size: tuple[int, int, int]
    patch_overlap: tuple[int, int, int]
    subjects: int
    batch_size: int
    patches_per_volume: int
    seed: int


class IdentityLogits:
    """Tiny deterministic model that preserves spatial shape."""

    def __call__(self, tensor: Any) -> Any:
        return tensor * 1.0


def _triple(value: list[int], name: str) -> tuple[int, int, int]:
    if len(value) != 3:
        raise argparse.ArgumentTypeError(f"{name} requires exactly 3 integers")
    return (value[0], value[1], value[2])


def make_subject(index: int, shape: tuple[int, int, int]) -> tio.Subject:
    base = torch.arange(shape[0] * shape[1] * shape[2], dtype=torch.float32)
    image = base.reshape(1, *shape) / 1000 + index

    label = torch.zeros(1, *shape, dtype=torch.long)
    center = tuple(s // 2 for s in shape)
    label[
        :,
        center[0] - 3 : center[0] + 3,
        center[1] - 3 : center[1] + 3,
        center[2] - 3 : center[2] + 3,
    ] = 1

    weights = torch.zeros(1, *shape, dtype=torch.float32)
    weights[
        :,
        center[0] - 4 : center[0] + 4,
        center[1] - 4 : center[1] + 4,
        center[2] - 4 : center[2] + 4,
    ] = 1

    return tio.Subject(
        t1=tio.ScalarImage(image),
        seg=tio.LabelMap(label),
        sampling_weights=tio.ScalarImage(weights),
        subject_id=f"synthetic-{index}",
    )


def assert_patch_locations(batch: tio.SubjectsBatch) -> None:
    assert "patch_location" in batch.metadata, "missing patch_location metadata"
    locations = batch.metadata["patch_location"]
    assert len(locations) == batch.batch_size
    for location in locations:
        assert isinstance(location, tio.PatchLocation)
        assert len(location.index) == 3
        assert len(location.size) == 3


def run_queue_training_smoke(subjects: list[tio.Subject], config: SmokeConfig) -> None:
    sampler = tio.UniformSampler(subjects[0], patch_size=config.patch_size)
    queue = tio.Queue(
        subjects,
        patch_sampler=sampler,
        max_length=max(config.batch_size * 2, 4),
        patches_per_volume=config.patches_per_volume,
        num_workers=0,
        shuffle_subjects=False,
        shuffle_patches=False,
    )
    loader = tio.SubjectsLoader(queue, batch_size=config.batch_size)
    model = IdentityLogits()

    total = 0
    for batch in loader:
        assert_patch_locations(batch)
        inputs = batch.t1.data
        targets = batch.seg.data
        logits = model(inputs)
        assert inputs.shape[0] == batch.batch_size
        assert inputs.shape[-3:] == config.patch_size
        assert logits.shape == inputs.shape
        assert targets.shape[-3:] == config.patch_size
        total += batch.batch_size

    expected = config.subjects * config.patches_per_volume
    assert total == expected, f"expected {expected} queued patches, got {total}"
    assert queue.patches_per_epoch == expected
    assert queue.max_memory > 0


def run_weighted_and_label_sampler_smoke(subject: tio.Subject, config: SmokeConfig) -> None:
    weighted = tio.WeightedSampler(
        subject,
        patch_size=config.patch_size,
        probability_map="sampling_weights",
        num_patches=3,
    )
    weighted_patches = list(weighted)
    assert len(weighted_patches) == 3
    assert all(patch.t1.spatial_shape == config.patch_size for patch in weighted_patches)
    assert all(isinstance(patch.patch_location, tio.PatchLocation) for patch in weighted_patches)

    label = tio.LabelSampler(
        subject,
        patch_size=config.patch_size,
        label_name="seg",
        label_probabilities={0: 0.0, 1: 1.0},
        num_patches=3,
    )
    label_patches = list(label)
    assert len(label_patches) == 3
    assert all(patch.seg.data.sum() > 0 for patch in label_patches)


def run_dense_inference_smoke(subject: tio.Subject, config: SmokeConfig) -> None:
    sampler = tio.GridSampler(
        subject,
        patch_size=config.patch_size,
        patch_overlap=config.patch_overlap,
    )
    loader = tio.SubjectsLoader(sampler, batch_size=config.batch_size)
    aggregator = tio.PatchAggregator(
        spatial_shape=subject.spatial_shape,
        overlap_mode="average",
        patch_overlap=config.patch_overlap,
    )
    multi = tio.PatchAggregator(
        spatial_shape=subject.spatial_shape,
        overlap_mode="average",
        patch_overlap=config.patch_overlap,
    )
    model = IdentityLogits()

    seen = 0
    with torch.no_grad():
        for batch in loader:
            assert_patch_locations(batch)
            outputs = model(batch.t1.data)
            locations = batch.metadata["patch_location"]
            aggregator.add_batch(outputs, locations)
            multi.add_batch({"identity": outputs, "doubled": outputs * 2}, locations)
            seen += batch.batch_size

    assert seen == len(sampler)
    dense = aggregator.get_output()
    identity = multi.get_output("identity")
    doubled = multi.get_output("doubled")
    assert dense.shape == subject.t1.data.shape
    assert identity.shape == subject.t1.data.shape
    assert doubled.shape == subject.t1.data.shape
    torch.testing.assert_close(dense, subject.t1.data)
    torch.testing.assert_close(identity, subject.t1.data)
    torch.testing.assert_close(doubled, subject.t1.data * 2)


def parse_args() -> SmokeConfig:
    parser = argparse.ArgumentParser(
        description="Run synthetic TorchIO patch workflow smoke assertions.",
    )
    parser.add_argument("--shape", nargs=3, type=int, default=[24, 24, 24])
    parser.add_argument("--patch-size", nargs=3, type=int, default=[12, 12, 12])
    parser.add_argument("--patch-overlap", nargs=3, type=int, default=[4, 4, 4])
    parser.add_argument("--subjects", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--patches-per-volume", type=int, default=4)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    if args.subjects < 1:
        parser.error("--subjects must be at least 1")
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")
    if args.patches_per_volume < 1:
        parser.error("--patches-per-volume must be at least 1")

    shape = _triple(args.shape, "--shape")
    patch_size = _triple(args.patch_size, "--patch-size")
    patch_overlap = _triple(args.patch_overlap, "--patch-overlap")
    for axis, (size, patch, overlap) in enumerate(zip(shape, patch_size, patch_overlap, strict=True)):
        if patch <= 0:
            parser.error(f"--patch-size values must be positive; axis {axis} got {patch}")
        if patch > size:
            parser.error(f"patch size {patch} exceeds shape {size} on axis {axis}")
        if overlap < 0:
            parser.error(f"--patch-overlap values must be nonnegative; axis {axis} got {overlap}")
        if overlap >= patch:
            parser.error(f"patch overlap {overlap} must be smaller than patch size {patch} on axis {axis}")

    return SmokeConfig(
        shape=shape,
        patch_size=patch_size,
        patch_overlap=patch_overlap,
        subjects=args.subjects,
        batch_size=args.batch_size,
        patches_per_volume=args.patches_per_volume,
        seed=args.seed,
    )


def import_runtime_dependencies() -> None:
    global torch, tio
    try:
        import torch as torch_module
        import torchio as tio_module
    except ModuleNotFoundError as error:
        raise SystemExit(
            "This smoke test requires installed runtime dependencies: "
            "torch and torchio. Install them in the active Python environment "
            "before running assertions."
        ) from error
    torch = torch_module
    tio = tio_module


def main() -> None:
    config = parse_args()
    import_runtime_dependencies()
    torch.manual_seed(config.seed)
    subjects = [make_subject(index, config.shape) for index in range(config.subjects)]

    run_queue_training_smoke(subjects, config)
    run_weighted_and_label_sampler_smoke(subjects[0], config)
    run_dense_inference_smoke(subjects[0], config)

    print("TorchIO patch workflow smoke test passed")


if __name__ == "__main__":
    main()
