#!/usr/bin/env python3
"""Synthetic smoke checks for loader dispatch and manifest-backed datasets.

The fixtures are written into a temporary directory tree so this script does not
require any real medical dataset.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import sys

import nibabel as nib
import numpy as np
import torch
from PIL import Image


def ensure_repo_on_path() -> None:
    try:
        import lib.medloaders  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "medloaders" / "__init__.py").is_file():
            sys.path.insert(0, str(parent))
            return

    raise RuntimeError(
        "Could not import MedicalZooPytorch dataloaders. Run from a checkout that contains the repo root, or make the package importable first."
    )


ensure_repo_on_path()

import lib.medloaders as medical_loaders
from lib.medloaders import medical_loader_utils as mlu
from lib.medloaders.covid_ct_dataset import CovidCTDataset
from lib.medloaders import COVIDxdataset as covidx_mod


def save_nifti(path: Path, data: np.ndarray) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = nib.Nifti1Image(np.asarray(data, dtype=np.float32), np.eye(4, dtype=np.float32))
    nib.save(img, str(path))
    return path


def save_png(path: Path, rgb_value: tuple[int, int, int]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (64, 64), rgb_value)
    image.save(str(path))
    return path


def parse_covidx_manifest(path: Path) -> tuple[list[str], list[str]]:
    paths: list[str] = []
    labels: list[str] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        if "/ c o" in line:
            break
        _, rel_path, label = line.split(" ")
        paths.append(rel_path)
        labels.append(label)
    return paths, labels


def assert_shape(name: str, actual, expected) -> None:
    if tuple(actual) != tuple(expected):
        raise AssertionError(f"{name} shape mismatch: expected {expected}, got {tuple(actual)}")


def exercise_brats_subvolumes(root: Path) -> None:
    arrays = {
        "t1": np.full((8, 8, 8), 1, dtype=np.float32),
        "t1ce": np.full((8, 8, 8), 2, dtype=np.float32),
        "t2": np.full((8, 8, 8), 3, dtype=np.float32),
        "flair": np.full((8, 8, 8), 4, dtype=np.float32),
        "seg": np.ones((8, 8, 8), dtype=np.float32),
    }
    paths = [save_nifti(root / f"{name}.nii.gz", data) for name, data in arrays.items()]
    out_dir = root / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    samples = mlu.create_sub_volumes(
        *[[str(p)] for p in paths],
        dataset_name="brats2018",
        mode="train",
        samples=1,
        full_vol_dim=(8, 8, 8),
        crop_size=(4, 4, 4),
        sub_vol_path=str(out_dir) + "/",
        normalization="max_min",
        th_percent=0.1,
    )

    if len(samples) != 1:
        raise AssertionError(f"Expected one synthetic subvolume, got {len(samples)}")

    for saved_path in samples[0]:
        if not Path(saved_path).exists():
            raise AssertionError(f"Missing generated patch file: {saved_path}")
        loaded = np.load(saved_path)
        if loaded.ndim != 3:
            raise AssertionError(f"Generated patch should be 3D, got shape {loaded.shape}")


def exercise_ixi_dispatch(root: Path) -> None:
    (root / "ixi" / "T1").mkdir(parents=True, exist_ok=True)
    (root / "ixi" / "T2").mkdir(parents=True, exist_ok=True)

    t1_path = save_nifti(root / "ixi" / "T1" / "subject01_T1.nii.gz", np.arange(64, dtype=np.float32).reshape(4, 4, 4))
    t2_path = save_nifti(root / "ixi" / "T2" / "subject01_T2.nii.gz", np.arange(64, dtype=np.float32).reshape(4, 4, 4) + 10)

    class SyntheticIXI:
        def __init__(self, args, dataset_path="./data", voxels_space=(2, 2, 2), modalities=2, to_canonical=False, save=True):
            self.samples = [(str(t1_path), str(t2_path))]
            self.affine = nib.load(str(t1_path)).affine
            self.full_volume = None

        def __len__(self):
            return len(self.samples)

        def __getitem__(self, index):
            t1_file, t2_file = self.samples[index]
            t1 = torch.from_numpy(np.asarray(nib.load(t1_file).get_fdata(dtype=np.float32)))
            t2 = torch.from_numpy(np.asarray(nib.load(t2_file).get_fdata(dtype=np.float32)))
            return t1, t2

    original_ixi = medical_loaders.IXIMRIdataset
    medical_loaders.IXIMRIdataset = SyntheticIXI
    args = SimpleNamespace(
        batchSz=1,
        dataset_name="ixi",
        dim=(4, 4, 4),
        nEpochs=1,
        inChannels=2,
        inModalities=2,
        samples_train=1,
        samples_val=1,
        classes=4,
        split=0.5,
        threshold=0.1,
        normalization="max_min",
        augmentation=False,
        loadData=False,
        cuda=False,
    )
    try:
        generator, affine = medical_loaders.generate_datasets(args, path=str(root))
        batch = next(iter(generator))
    finally:
        medical_loaders.IXIMRIdataset = original_ixi

    if len(batch) != 2:
        raise AssertionError(f"Expected two tensors from the IXI generator, got {len(batch)}")
    assert_shape("ixi batch t1", batch[0].shape, (1, 4, 4, 4))
    assert_shape("ixi batch t2", batch[1].shape, (1, 4, 4, 4))
    assert_shape("ixi affine", affine.shape, (4, 4))


def exercise_covid_ct(root: Path) -> None:
    covid_dir = root / "CT_COVID"
    non_dir = root / "CT_NonCOVID"
    covid_dir.mkdir(parents=True, exist_ok=True)
    non_dir.mkdir(parents=True, exist_ok=True)

    save_png(covid_dir / "covid_01.png", (255, 0, 0))
    save_png(non_dir / "normal_01.png", (0, 255, 0))

    covid_txt = root / "trainCT_COVID.txt"
    non_txt = root / "trainCT_NonCOVID.txt"
    covid_txt.write_text("covid_01.png\n", encoding="utf-8")
    non_txt.write_text("normal_01.png\n", encoding="utf-8")

    ds = CovidCTDataset(mode="train", root_dir=str(root), txt_COVID=str(covid_txt), txt_NonCOVID=str(non_txt))
    if len(ds) != 2:
        raise AssertionError(f"Expected two COVID CT samples, got {len(ds)}")
    image, label = ds[0]
    assert_shape("COVID_CT image", image.shape, (3, 224, 224))
    if int(label) not in (0, 1):
        raise AssertionError(f"Unexpected COVID CT label: {label}")


def exercise_covidx(root: Path) -> None:
    train_dir = root / "train"
    val_dir = root / "val"
    (train_dir / "normal").mkdir(parents=True, exist_ok=True)
    (train_dir / "COVID-19").mkdir(parents=True, exist_ok=True)
    (val_dir / "normal").mkdir(parents=True, exist_ok=True)
    (val_dir / "COVID-19").mkdir(parents=True, exist_ok=True)

    save_png(train_dir / "normal" / "normal_train.png", (0, 0, 255))
    save_png(train_dir / "COVID-19" / "covid_train.png", (255, 255, 0))
    save_png(val_dir / "normal" / "normal_val.png", (0, 128, 255))
    save_png(val_dir / "COVID-19" / "covid_val.png", (255, 128, 0))

    manifest_dir = root / "covidx_manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    train_manifest = manifest_dir / "train_split_v2.txt"
    test_manifest = manifest_dir / "test_split_v2.txt"
    train_manifest.write_text(
        "0 normal/normal_train.png normal\n"
        "1 COVID-19/covid_train.png COVID-19\n",
        encoding="utf-8",
    )
    test_manifest.write_text(
        "2 normal/normal_val.png normal\n"
        "3 COVID-19/covid_val.png COVID-19\n",
        encoding="utf-8",
    )

    original_read_filepaths = covidx_mod.read_filepaths

    def fake_read_filepaths(file: str):
        if "train_split_v2" in file:
            return parse_covidx_manifest(train_manifest)
        return parse_covidx_manifest(test_manifest)

    covidx_mod.read_filepaths = fake_read_filepaths
    original_load_image = covidx_mod.COVIDxDataset.load_image

    def safe_load_image(self, img_path, resize_dim, **kwargs):
        image = covidx_mod.img_loader.load_2d_image(img_path, resize_dim)
        t = covidx_mod.transforms.ToTensor()
        norm = covidx_mod.transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[1, 1, 1])
        return norm(t(image))

    covidx_mod.COVIDxDataset.load_image = safe_load_image
    try:
        train_ds = covidx_mod.COVIDxDataset(mode="train", n_classes=3, dataset_path=str(root), dim=(32, 32))
        val_ds = covidx_mod.COVIDxDataset(mode="val", n_classes=3, dataset_path=str(root), dim=(32, 32))
        image, label = train_ds[0]
    finally:
        covidx_mod.COVIDxDataset.load_image = original_load_image
        covidx_mod.read_filepaths = original_read_filepaths

    if len(train_ds) != 2 or len(val_ds) != 2:
        raise AssertionError(f"Expected two synthetic COVIDx samples per split, got {len(train_ds)} and {len(val_ds)}")

    assert_shape("COVIDx image", image.shape, (3, 32, 32))
    if int(label) not in (0, 1, 2):
        raise AssertionError(f"Unexpected COVIDx label: {label}")


def main() -> int:
    np.random.seed(0)
    torch.manual_seed(0)

    with TemporaryDirectory(prefix="medicalzoo-dataloaders-") as tmpdir:
        root = Path(tmpdir)
        exercise_brats_subvolumes(root / "brats_fixture")
        exercise_ixi_dispatch(root / "ixi_fixture")
        exercise_covid_ct(root / "covid_ct_fixture")
        exercise_covidx(root / "covidx_fixture")

    print("dataloader smoke ok")
    print("checked: brats subvolumes, ixi dispatcher, covid ct, covidx")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
