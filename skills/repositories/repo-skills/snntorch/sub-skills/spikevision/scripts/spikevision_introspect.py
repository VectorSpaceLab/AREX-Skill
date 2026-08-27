#!/usr/bin/env python3
"""Import/signature smoke for the legacy snntorch.spikevision surface.

This helper never downloads datasets. It only imports the legacy package,
prints the deprecation warning, inspects live signatures, and runs small
synthetic transform checks.
"""

from __future__ import annotations

import argparse
import inspect
import json
import warnings
from typing import Any


def _sig(obj: Any) -> str:
    return str(inspect.signature(obj))


def _capture_import_surface() -> dict[str, Any]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        import snntorch.spikevision as spikevision  # noqa: F401
        from snntorch.spikevision import spikedata

    warning_texts = [str(item.message) for item in caught]
    return {
        "warning_texts": warning_texts,
        "spikedata_all": list(getattr(spikedata, "__all__", ())),
        "dataset_exports": {
            name: f"{getattr(spikedata, name).__module__}.{getattr(spikedata, name).__name__}"
            for name in ("NMNIST", "DVSGesture", "SHD")
        },
    }


def _capture_signatures() -> dict[str, Any]:
    from snntorch.spikevision.neuromorphic_dataset import (
        NeuromorphicDataset,
        StandardTransform,
        calculate_md5,
        check_integrity,
        check_md5,
        download_and_extract_archive,
        download_url,
        identity,
        _extract_archive,
    )
    from snntorch.spikevision import _transforms as tr
    from snntorch.spikevision import events_timeslices as ets
    from snntorch.spikevision.spikedata import dvs_gesture, nmnist, shd

    return {
        "dataset_wrappers": {
            "NeuromorphicDataset": _sig(NeuromorphicDataset),
            "StandardTransform": _sig(StandardTransform),
            "NMNIST": _sig(nmnist.NMNIST),
            "DVSGesture": _sig(dvs_gesture.DVSGesture),
            "SHD": _sig(shd.SHD),
        },
        "transform_helpers": {
            name: _sig(getattr(tr, name))
            for name in (
                "toOneHot",
                "toDtype",
                "Downsample",
                "CropDims",
                "CropCenter",
                "Attention",
                "ToChannelHeightWidth",
                "ToCountFrame",
                "ToEventSum",
                "FilterEvents",
                "ExpFilterEvents",
                "Rescale",
                "hflip",
                "rot90",
                "dvs_permute",
                "Repeat",
                "ToTensor",
            )
        },
        "file_helpers": {
            "download_url": _sig(download_url),
            "download_and_extract_archive": _sig(download_and_extract_archive),
            "check_integrity": _sig(check_integrity),
            "calculate_md5": _sig(calculate_md5),
            "check_md5": _sig(check_md5),
            "_extract_archive": _sig(_extract_archive),
            "identity": _sig(identity),
            "get_tmad_slice": _sig(ets.get_tmad_slice),
            "nmnist_load_events_from_bin": _sig(nmnist.nmnist_load_events_from_bin),
            "nmnist_get_file_names": _sig(nmnist.nmnist_get_file_names),
            "nmnist_create_events_hdf5": _sig(nmnist.create_events_hdf5),
            "dvs_gesture_gather_aedat": _sig(dvs_gesture.gather_aedat),
            "dvs_gesture_create_events_hdf5": _sig(dvs_gesture.create_events_hdf5),
            "shd_load_hdf5": _sig(shd.load_shd_hdf5),
            "shd_create_events_hdf5": _sig(shd.create_events_hdf5),
        },
    }


def _synthetic_smoke() -> dict[str, Any]:
    import numpy as np
    import torch

    from snntorch.spikevision.neuromorphic_dataset import StandardTransform
    from snntorch.spikevision._transforms import (
        Downsample,
        Repeat,
        ToChannelHeightWidth,
        ToCountFrame,
        ToTensor,
        dvs_permute,
        hflip,
        rot90,
        toOneHot,
    )

    result: dict[str, Any] = {}

    standard = StandardTransform(
        transform=lambda x: x + 1,
        target_transform=lambda y: y * 2,
    )
    sample_input = np.array([1, 2], dtype=np.int64)
    sample_target = np.array([3], dtype=np.int64)
    out_input, out_target = standard(sample_input, sample_target)
    result["standard_transform"] = {
        "input": out_input.tolist(),
        "target": out_target.tolist(),
    }

    events = np.array(
        [[0, 0, 1, 1], [999, 1, 2, 3], [1500, 0, 0, 0]],
        dtype=np.int64,
    )
    downsampled = Downsample([1000, 1, 1, 1])(events)
    count_frame = ToCountFrame(T=2, size=[2, 4, 4])(downsampled)
    tensor_frame = ToTensor()(count_frame)
    result["count_frame"] = {
        "downsampled": downsampled.tolist(),
        "count_shape": list(count_frame.shape),
        "tensor_shape": list(tensor_frame.shape),
        "count_sum": int(count_frame.sum()),
    }

    channel_rows = np.array([[0, 10], [1, 20]], dtype=np.int64)
    result["channel_height_width"] = {
        "shape": list(ToChannelHeightWidth()(channel_rows).shape),
    }

    label = np.array([1], dtype=np.int64)
    repeated_label = Repeat(3)(label)
    result["label_helpers"] = {
        "repeat_shape": list(repeated_label.shape),
        "one_hot_shape": list(toOneHot(4)(repeated_label).shape),
    }

    img = torch.arange(4).reshape(1, 2, 2)
    result["tensor_helpers"] = {
        "hflip": hflip()(img).tolist(),
        "rot90": rot90()(img).tolist(),
        "dvs_permute": dvs_permute()(img).tolist(),
    }

    return result


def _pretty_print(payload: dict[str, Any]) -> None:
    print("[spikevision] import surface")
    for warning_text in payload["import_surface"]["warning_texts"]:
        print(f"  warning: {warning_text}")
    print("  exports: " + ", ".join(payload["import_surface"]["spikedata_all"]))
    print()

    print("[spikevision] signatures")
    for section, mapping in payload["signatures"].items():
        print(f"  {section}:")
        for name, sig in mapping.items():
            print(f"    {name}{sig}")
    print()

    print("[spikevision] synthetic smoke")
    smoke = payload["synthetic_smoke"]
    print(f"  standard_transform: {smoke['standard_transform']}")
    print(f"  count_frame: {smoke['count_frame']}")
    print(f"  channel_height_width: {smoke['channel_height_width']}")
    print(f"  label_helpers: {smoke['label_helpers']}")
    print(f"  tensor_helpers: {smoke['tensor_helpers']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of pretty text",
    )
    args = parser.parse_args()

    payload = {
        "import_surface": _capture_import_surface(),
        "signatures": _capture_signatures(),
        "synthetic_smoke": _synthetic_smoke(),
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        _pretty_print(payload)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
