"""Shared helpers for BAPPS-style evaluation and training.

The bundled helpers use these routines instead of the buggy stock dataset
loaders so they can run from the generated skill tree without the original
checkout.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

import numpy as np
from PIL import Image
import torch
from torch.utils.data import ConcatDataset, DataLoader, Dataset

from lpips_common import image_to_tensor, load_rgb_image


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".ppm", ".PNG", ".JPG", ".JPEG", ".BMP", ".PPM"}
LABEL_EXTENSIONS = {".npy"}


def _resample_filter() -> int:
    try:
        return Image.Resampling.BILINEAR  # Pillow >= 9.1
    except AttributeError:  # pragma: no cover - older Pillow fallback
        return Image.BILINEAR


def _resize_preserve_aspect(image: Image.Image, load_size: int | None) -> Image.Image:
    if load_size is None:
        return image
    width, height = image.size
    if min(width, height) == load_size:
        return image
    if width < height:
        new_width = load_size
        new_height = max(1, int(round(height * load_size / float(width))))
    else:
        new_height = load_size
        new_width = max(1, int(round(width * load_size / float(height))))
    return image.resize((new_width, new_height), _resample_filter())


def resolve_split_root(dataset_root: str | Path, dataset_mode: str, dataset_name: str | Path) -> Path:
    """Resolve a dataset split path from either a direct path or a base root."""

    dataset_mode = dataset_mode.lower()
    required = ("ref", "p0", "p1", "judge") if dataset_mode == "2afc" else ("p0", "p1", "same")

    dataset_root = Path(dataset_root)
    dataset_name = Path(dataset_name)
    candidates = []
    if dataset_name.is_absolute():
        candidates.append(dataset_name)
    elif dataset_name.exists():
        candidates.append(dataset_name)
    candidates.extend(
        [
            dataset_root / dataset_mode / dataset_name,
            dataset_root / dataset_name,
            dataset_root / dataset_mode,
            dataset_root,
        ]
    )

    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve() if candidate.exists() else candidate
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists() and all((candidate / subdir).exists() for subdir in required):
            return candidate

    raise FileNotFoundError(
        f"could not resolve a {dataset_mode} split for {dataset_name!s} under {dataset_root!s}; "
        f"expected subdirectories: {', '.join(required)}"
    )


def _collect_relative_file_map(folder: Path, *, extensions: set[str]) -> dict[str, Path]:
    if not folder.exists():
        raise FileNotFoundError(f"missing required directory: {folder}")
    file_map: dict[str, Path] = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.suffix in extensions:
            key = path.relative_to(folder).with_suffix("").as_posix()
            if key in file_map:
                raise ValueError(f"duplicate relative key {key!r} under {folder}")
            file_map[key] = path
    if not file_map:
        raise ValueError(f"no supported files found under {folder}")
    return file_map


@dataclass(frozen=True)
class BAPSSplitSpec:
    dataset_mode: str
    split_root: Path
    load_size: int | None = 64


class AlignedBAPPSDataset(Dataset):
    """Dataset that enforces exact subdirectory alignment for BAPPS splits."""

    def __init__(self, split_root: str | Path, dataset_mode: str = "2afc", load_size: int | None = 64):
        self.split_root = Path(split_root)
        self.dataset_mode = dataset_mode.lower()
        self.load_size = load_size
        if self.dataset_mode not in {"2afc", "jnd"}:
            raise ValueError(f"unsupported dataset_mode: {dataset_mode}")

        self.required_subdirs = ("ref", "p0", "p1", "judge") if self.dataset_mode == "2afc" else ("p0", "p1", "same")
        self.file_maps = {
            name: _collect_relative_file_map(self.split_root / name, extensions=IMAGE_EXTENSIONS if name != self.required_subdirs[-1] else LABEL_EXTENSIONS)
            for name in self.required_subdirs
        }

        key_sets = [set(mapping) for mapping in self.file_maps.values()]
        common_keys = set.intersection(*key_sets)
        if not common_keys:
            raise ValueError(f"no aligned samples found in {self.split_root}")

        missing = {name: sorted(set.intersection(*key_sets) ^ set(mapping)) for name, mapping in self.file_maps.items() if set(mapping) != common_keys}
        if missing:
            detail = "; ".join(f"{name}: {len(keys)} misaligned files" for name, keys in missing.items())
            raise ValueError(f"split alignment error in {self.split_root}: {detail}")

        self.keys = sorted(common_keys)

    def __len__(self) -> int:
        return len(self.keys)

    def _load_rgb_tensor(self, path: Path) -> torch.Tensor:
        image = Image.open(path).convert("RGB")
        image = _resize_preserve_aspect(image, self.load_size)
        return image_to_tensor(np.asarray(image)).squeeze(0)

    def _load_label(self, path: Path) -> torch.Tensor:
        value = float(np.load(path).reshape(-1)[0])
        return torch.tensor(value, dtype=torch.float32).view(1, 1, 1)

    def __getitem__(self, index: int):
        key = self.keys[index]
        item = {
            "p0": self._load_rgb_tensor(self.file_maps["p0"][key]),
            "p1": self._load_rgb_tensor(self.file_maps["p1"][key]),
            "p0_path": str(self.file_maps["p0"][key]),
            "p1_path": str(self.file_maps["p1"][key]),
        }
        if self.dataset_mode == "2afc":
            item["ref"] = self._load_rgb_tensor(self.file_maps["ref"][key])
            item["judge"] = self._load_label(self.file_maps["judge"][key])
            item["ref_path"] = str(self.file_maps["ref"][key])
            item["judge_path"] = str(self.file_maps["judge"][key])
        else:
            item["same"] = self._load_label(self.file_maps["same"][key])
            item["same_path"] = str(self.file_maps["same"][key])
        return item


def load_bapps_dataset(
    dataset_root: str | Path,
    dataset_mode: str,
    datasets: Sequence[str | Path],
    *,
    load_size: int | None = 64,
) -> Dataset:
    """Load one or more BAPPS splits and concatenate them if needed."""

    split_datasets = []
    for dataset_name in datasets:
        split_root = resolve_split_root(dataset_root, dataset_mode, dataset_name)
        split_datasets.append(AlignedBAPPSDataset(split_root, dataset_mode=dataset_mode, load_size=load_size))
    if len(split_datasets) == 1:
        return split_datasets[0]
    return ConcatDataset(split_datasets)


def make_loader(dataset: Dataset, *, batch_size: int = 1, shuffle: bool = False, num_workers: int = 0) -> DataLoader:
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle, num_workers=num_workers, drop_last=False)


def accuracy_2afc(d0s: np.ndarray, d1s: np.ndarray, judges: np.ndarray) -> tuple[float, np.ndarray]:
    judges = np.asarray(judges, dtype=float).reshape(-1)
    d0s = np.asarray(d0s, dtype=float).reshape(-1)
    d1s = np.asarray(d1s, dtype=float).reshape(-1)
    scores = (d0s < d1s) * (1.0 - judges) + (d1s < d0s) * judges + (d1s == d0s) * 0.5
    return float(np.mean(scores)), scores


def voc_ap(rec: np.ndarray, prec: np.ndarray) -> float:
    rec = np.asarray(rec, dtype=float)
    prec = np.asarray(prec, dtype=float)
    mrec = np.concatenate(([0.0], rec, [1.0]))
    mpre = np.concatenate(([0.0], prec, [0.0]))
    for i in range(mpre.size - 1, 0, -1):
        mpre[i - 1] = np.maximum(mpre[i - 1], mpre[i])
    i = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[i + 1] - mrec[i]) * mpre[i + 1]))


def ap_jnd(distances: np.ndarray, same: np.ndarray) -> tuple[float, np.ndarray]:
    distances = np.asarray(distances, dtype=float).reshape(-1)
    same = np.asarray(same, dtype=float).reshape(-1)
    order = np.argsort(distances)
    sorted_same = same[order]
    tp = np.cumsum(sorted_same)
    fp = np.cumsum(1.0 - sorted_same)
    fn = np.sum(sorted_same) - tp
    prec = tp / np.maximum(tp + fp, 1e-12)
    rec = tp / np.maximum(tp + fn, 1e-12)
    return voc_ap(rec, prec), order
