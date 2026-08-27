#!/usr/bin/env python3
"""Tiny MMEngine data contract smoke check.

This script creates only temporary local files. It validates a minimal
BaseDataset subclass, transform/collate behavior, InstanceData constraints,
PixelData shape checks, and unified file IO JSON/text/bytes helpers.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def run_smoke(verbose: bool = False) -> None:
    try:
        import torch
        from mmengine.dataset import BaseDataset, default_collate, pseudo_collate
        from mmengine.fileio import (dump, exists, get, get_text,
                                     list_dir_or_file, load, put, put_text)
        from mmengine.structures import BaseDataElement, InstanceData, PixelData
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency for this smoke check. Install MMEngine "
            "with its PyTorch runtime dependencies, then rerun this script. "
            f"Original import error: {exc}") from exc

    class TinyDataset(BaseDataset):
        """Minimal dataset that copies records before adding derived fields."""

        METAINFO = {"classes": ("negative", "positive"), "task_name": "tiny"}

        def parse_data_info(self, raw_data_info):
            data_info = raw_data_info.copy()
            data_info["values"] = list(data_info["values"])
            data_info["label"] = int(data_info["label"])
            return data_info

    class AddInputsAndSample:
        """Tiny callable transform with a clear data contract."""

        def __call__(self, data):
            data = data.copy()
            data["inputs"] = torch.tensor(data["values"], dtype=torch.float32)
            data["data_sample"] = BaseDataElement(
                metainfo={"sample_idx": data["sample_idx"]},
                gt_label=torch.tensor(data["label"], dtype=torch.long),
            )
            return data

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        tmp_dir = Path(tmp_dir_name)
        ann_path = tmp_dir / "annotations.json"
        bytes_path = tmp_dir / "nested" / "payload.bin"
        text_path = tmp_dir / "nested" / "labels.txt"

        annotations = {
            "metainfo": {"source": "generated-smoke"},
            "data_list": [
                {"id": "a", "values": [1, 2], "label": 0},
                {"id": "b", "values": [3, 4], "label": 1},
            ],
        }
        dump(annotations, ann_path)
        assert load(ann_path) == annotations

        dataset = TinyDataset(
            ann_file=str(ann_path),
            pipeline=[AddInputsAndSample()],
            serialize_data=False,
            lazy_init=True,
        )
        assert not dataset._fully_initialized
        dataset.full_init()
        assert dataset._fully_initialized
        assert dataset.metainfo["classes"] == ("negative", "positive")
        assert dataset.metainfo["source"] == "generated-smoke"
        assert len(dataset) == 2

        info = dataset.get_data_info(0)
        sample = dataset[0]
        assert info["sample_idx"] == 0
        assert sample["inputs"].shape == (2,)
        assert sample["data_sample"].gt_label.item() == 0

        pseudo_batch = pseudo_collate([dataset[0], dataset[1]])
        assert isinstance(pseudo_batch["inputs"], list)
        assert len(pseudo_batch["data_sample"]) == 2

        default_batch = default_collate([dataset[0], dataset[1]])
        assert tuple(default_batch["inputs"].shape) == (2, 2)
        assert len(default_batch["data_sample"]) == 2

        instances = InstanceData(metainfo={"img_shape": (8, 8)})
        instances.bboxes = torch.zeros((2, 4))
        instances.labels = torch.tensor([0, 1])
        try:
            instances.scores = torch.ones(3)
        except AssertionError:
            pass
        else:
            raise AssertionError("InstanceData accepted mismatched field length")
        assert len(instances[torch.tensor([True, False])]) == 1

        pixel_data = PixelData(mask=torch.zeros((8, 8)))
        assert tuple(pixel_data.mask.shape) == (1, 8, 8)
        try:
            pixel_data.other = torch.zeros((1, 9, 8))
        except AssertionError:
            pass
        else:
            raise AssertionError("PixelData accepted mismatched height/width")

        put(b"payload", bytes_path)
        assert get(bytes_path) == b"payload"
        put_text("negative\npositive\n", text_path)
        assert get_text(text_path).splitlines() == ["negative", "positive"]
        assert exists(bytes_path)
        txt_entries = list(
            list_dir_or_file(
                tmp_dir, list_dir=False, suffix=".txt", recursive=True))
        assert "nested/labels.txt" in {entry.replace("\\", "/") for entry in txt_entries}

        if verbose:
            print(f"dataset_length={len(dataset)}")
            print(f"metainfo_keys={sorted(dataset.metainfo)}")
            print(f"pseudo_inputs_type={type(pseudo_batch['inputs']).__name__}")
            print(f"default_inputs_shape={tuple(default_batch['inputs'].shape)}")

    print("MMEngine data contract smoke passed")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a tiny local smoke check for MMEngine BaseDataset, "
            "collate functions, data elements, and file IO."))
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print the validated mini contract details.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_smoke(verbose=args.verbose)


if __name__ == "__main__":
    main()
