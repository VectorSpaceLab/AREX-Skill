#!/usr/bin/env python3
"""Safe smoke checks for the MedicalZooPytorch COVID 2D branch.

This script avoids real COVID data and avoids any network-backed pretrained
weight download. It verifies:
- core branch imports
- manifest parsing helpers with temporary text files
- CovidCTDataset on tiny synthetic PNG fixtures
- MetricTracker and accuracy behavior
- the train_covid train/validation loop on a toy CPU model
- the known CovidNet constructor typo, if still present
"""

from __future__ import annotations

import importlib
import inspect
import math
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class CaptureWriter:
    def __init__(self) -> None:
        self.scalars: list[tuple[str, float, int]] = []

    def add_scalar(self, tag, value, step):
        self.scalars.append((str(tag), float(value), int(step)))


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def ensure_repo_on_path() -> None:
    search_roots = [Path(__file__).resolve().parent, Path.cwd()]
    for root in search_roots:
        for candidate in [root, *root.parents]:
            if (candidate / "lib").is_dir():
                candidate_str = str(candidate)
                if candidate_str not in sys.path:
                    sys.path.insert(0, candidate_str)
                return


def make_rgb_png(path: Path, color: tuple[int, int, int]) -> None:
    from PIL import Image

    image = Image.new("RGB", (256, 256), color)
    image.save(path)


def check_imports():
    modules = [
        "lib.medloaders",
        "lib.medloaders.COVIDxdataset",
        "lib.medloaders.covid_ct_dataset",
        "lib.medzoo",
        "lib.medzoo.COVIDNet",
        "lib.train.train_covid",
        "lib.utils.covid_utils",
    ]
    loaded = {name: importlib.import_module(name) for name in modules}
    print("[ok] imports:", ", ".join(modules))
    ensure(hasattr(loaded["lib.medzoo"], "create_model"), "lib.medzoo should expose create_model")
    return loaded


def check_manifest_helpers():
    from lib.medloaders.COVIDxdataset import COVIDxDataset, read_filepaths
    from lib.medloaders.covid_ct_dataset import CovidCTDataset
    from lib.utils.covid_utils import read_txt

    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)

        txt = tmpdir / "labels.txt"
        txt.write_text("alpha\nbeta\n", encoding="utf-8")
        ensure(read_txt(str(txt)) == ["alpha", "beta"], "read_txt should strip newlines")

        covidx_manifest = tmpdir / "train_split_v2.txt"
        covidx_manifest.write_text(
            "1 img/a.png pneumonia\n"
            "2 img/b.png normal\n"
            "3 img/c.png COVID-19\n",
            encoding="utf-8",
        )
        paths, labels = read_filepaths(str(covidx_manifest))
        ensure(paths == ["img/a.png", "img/b.png", "img/c.png"], "COVIDx manifest paths parsed incorrectly")
        ensure(labels == ["pneumonia", "normal", "COVID-19"], "COVIDx manifest labels parsed incorrectly")

        # The source loader currently passes an extra augmentation keyword that
        # its load_image method does not accept. Verify the signature mismatch
        # explicitly so the smoke output explains the known issue.
        try:
            getitem_src = inspect.getsource(COVIDxDataset.__getitem__)
        except OSError:
            getitem_src = ""
        load_sig = inspect.signature(COVIDxDataset.load_image)
        if "augmentation=" in getitem_src and "augmentation" not in load_sig.parameters:
            print("[note] COVIDxDataset has the known augmentation/load_image mismatch")
        else:
            print("[info] COVIDxDataset signature mismatch no longer present or source unavailable")

        root = tmpdir / "covid_ct_dataset"
        (root / "CT_COVID").mkdir(parents=True)
        (root / "CT_NonCOVID").mkdir(parents=True)
        make_rgb_png(root / "CT_COVID" / "covid_1.png", (220, 0, 0))
        make_rgb_png(root / "CT_NonCOVID" / "normal_1.png", (0, 180, 0))

        covid_txt = tmpdir / "trainCT_COVID.txt"
        noncovid_txt = tmpdir / "trainCT_NonCOVID.txt"
        covid_txt.write_text("covid_1.png\n", encoding="utf-8")
        noncovid_txt.write_text("normal_1.png\n", encoding="utf-8")

        dataset = CovidCTDataset(
            "train",
            root_dir=str(root),
            txt_COVID=str(covid_txt),
            txt_NonCOVID=str(noncovid_txt),
        )
        ensure(len(dataset) == 2, "CovidCTDataset length should equal the combined manifest count")
        sample_x, sample_y = dataset[0]
        ensure(tuple(sample_x.shape) == (3, 224, 224), "CovidCTDataset sample should be resized to 224x224")
        ensure(int(sample_y) in {0, 1}, "CovidCTDataset label should be an integer class index")

    print("[ok] manifest helpers and CovidCTDataset synthetic sample")


def check_metric_helpers():
    from lib.utils.covid_utils import MetricTracker, accuracy

    logits = torch.tensor(
        [
            [0.1, 0.9],
            [2.0, 1.0],
            [0.8, 0.2],
        ],
        dtype=torch.float32,
    )
    targets = torch.tensor([1, 0, 1], dtype=torch.long)
    correct, total, acc = accuracy(logits, targets)
    ensure((correct, total) == (2, 3), "accuracy should report correct and total counts")
    ensure(abs(acc - (2 / 3)) < 1e-12, "accuracy should report the expected ratio")

    writer = CaptureWriter()
    tracker = MetricTracker("loss", "accuracy", writer=writer, mode="train")
    tracker.update_all_metrics(1, {"loss": 2.0, "accuracy": 0.5}, writer_step=7)
    tracker.update_all_metrics(2, {"loss": 4.0, "accuracy": 0.0}, writer_step=8)
    ensure(tracker.data["count"] == 2, "MetricTracker should store the latest iteration count")
    ensure(abs(tracker.data["loss"] - 6.0) < 1e-12, "MetricTracker should accumulate raw metric sums")
    ensure(abs(tracker.data["accuracy"] - 0.5) < 1e-12, "MetricTracker should accumulate accuracy sums")
    report = tracker.print_all_metrics()
    ensure("loss 3.0000" in report, "MetricTracker should report iteration means")
    ensure("accuracy 0.2500" in report, "MetricTracker should report iteration means")
    ensure(writer.scalars, "MetricTracker should emit scalar logs when a writer is attached")
    print("[info] sample TensorBoard tags:", [tag for tag, _, _ in writer.scalars[:4]])
    print("[ok] accuracy and MetricTracker synthetic behavior")


class TinyClassifier(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.flatten = nn.Flatten()
        self.fc = nn.Linear(3 * 8 * 8, 2)
        nn.init.zeros_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)

    def forward(self, x):
        return self.fc(self.flatten(x))


def check_train_validation_loop():
    from lib.train.train_covid import train, validation

    args = SimpleNamespace(cuda=False, batchSz=2, classes=2, log_interval=1)
    inputs = torch.zeros(4, 3, 8, 8, dtype=torch.float32)
    targets = torch.tensor([0, 1, 1, 1], dtype=torch.long)
    loader = DataLoader(TensorDataset(inputs, targets), batch_size=2, shuffle=False)

    model = TinyClassifier()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.0)
    writer = CaptureWriter()

    train_metrics = train(args, model, loader, optimizer, epoch=1, writer=writer)
    ensure(train_metrics.data["count"] == 2, "train() should update MetricTracker once per batch")
    ensure(abs(train_metrics.data["loss"] / train_metrics.data["count"] - math.log(2.0)) < 1e-4,
           "train() should average the expected cross-entropy loss for zero logits")
    ensure(abs(train_metrics.data["accuracy"] / train_metrics.data["count"] - 0.25) < 1e-12,
           "train() should average the expected batch accuracies")

    val_metrics, confusion_matrix = validation(args, model, loader, epoch=1, writer=writer)
    ensure(val_metrics.data["count"] == 2, "validation() should update MetricTracker once per batch")
    ensure(confusion_matrix.shape == (2, 2), "validation() should build a 2x2 confusion matrix")
    ensure(int(confusion_matrix.sum().item()) == 4, "validation() should count all synthetic samples")
    ensure(abs(val_metrics.data["accuracy"] / val_metrics.data["count"] - 0.25) < 1e-12,
           "validation() should average the expected batch accuracies")
    ensure(writer.scalars, "train/validation should emit scalar logs")
    print("[ok] synthetic train/validation loop")


def check_covidnet_caveat():
    from lib.medzoo.COVIDNet import CNN, CovidNet

    try:
        source = inspect.getsource(CNN.__init__)
    except OSError:
        source = ""
    if "pretrained=True" in source:
        print("[note] CNN still requests torchvision pretrained weights; not instantiating it here")
    else:
        print("[info] CNN pretrained-weight request no longer visible in source")

    try:
        _ = CovidNet("small", 3)
    except NameError as exc:
        if "pepx" in str(exc):
            print("[note] CovidNet constructor still fails on the pepx/PEPX typo")
        else:
            raise
    else:
        print("[info] CovidNet constructor succeeded; the pepx typo may be fixed")


def main() -> None:
    ensure_repo_on_path()
    check_imports()
    check_manifest_helpers()
    check_metric_helpers()
    check_train_validation_loop()
    check_covidnet_caveat()
    print("[done] covid-2d-classification smoke checks passed")


if __name__ == "__main__":
    main()
