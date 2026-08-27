#!/usr/bin/env python3
"""Safe smoke checks for the generated Nitrain skill.

Run this from any working directory. Pass --repo-root if you want to import the
checkout directly instead of relying on the installed package.

Examples
--------
python scripts/check_install.py --mode base
python scripts/check_install.py --mode datasets
python scripts/check_install.py --mode all
"""

from __future__ import annotations

import argparse
import importlib
import sys
import tempfile
from pathlib import Path
from typing import Iterable


def add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def require_module(name: str, purpose: str):
    try:
        return importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - explicit smoke helper
        raise SystemExit(
            f"missing optional dependency for {purpose}: {name} ({exc})"
        ) from exc


def optional_smoke(label: str, fn):
    try:
        return fn()
    except (ImportError, ModuleNotFoundError) as exc:  # pragma: no cover
        raise SystemExit(f"missing optional dependency for {label}: {exc}") from exc


def load_nitrain():
    try:
        import nitrain as nt
    except Exception as exc:  # pragma: no cover - explicit smoke helper
        raise SystemExit(f"failed to import nitrain: {exc}") from exc
    return nt


def check_base() -> None:
    nt = load_nitrain()
    from nitrain import readers, samplers, transforms

    print(f"nitrain={nt.__version__}")
    print(f"ImageReader={readers.ImageReader.__name__}")
    print(f"ColumnReader={readers.ColumnReader.__name__}")
    print(f"RangeNormalize={transforms.RangeNormalize.__name__}")
    print(f"SliceSampler={samplers.SliceSampler.__name__}")


def check_datasets() -> None:
    nt = load_nitrain()
    from nitrain import readers

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(nt.fetch_data("example-01", path=tmpdir, overwrite=True))
        ds = nt.Dataset(
            inputs=readers.ImageReader("*/img3d.nii.gz"),
            outputs=readers.ColumnReader("age", base_file="participants.csv"),
            base_dir=str(base_dir),
        )
        x, y = ds[0]
        assert x.shape == (30, 40, 50), x.shape
        assert y == 50, y
        train, test = ds.split(0.8, random=False)
        assert len(train) == 8, len(train)
        assert len(test) == 2, len(test)
        folder = nt.Dataset(
            inputs=readers.ImageReader("*/img3d.nii.gz"),
            outputs=readers.FolderNameReader("*/img3d_100.nii.gz", format="integer"),
            base_dir=str(base_dir),
        )
        _, label = folder[3]
        assert label == 3, label

    print("datasets smoke ok")


def check_preprocess() -> None:
    nt = load_nitrain()
    from nitrain import readers, samplers, transforms as tx

    def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(nt.fetch_data("example-01", path=tmpdir, overwrite=True))
            ds = nt.Dataset(
                inputs=readers.ImageReader("*/img3d.nii.gz"),
                outputs=readers.ImageReader("*/img3d_seg.nii.gz"),
                transforms={("inputs", "outputs"): tx.Resample((40, 40, 40))},
                base_dir=str(base_dir),
            )
            x, y = ds[0]
            assert x.shape == (40, 40, 40), x.shape
            assert y.shape == (40, 40, 40), y.shape

            loader = nt.Loader(
                ds,
                images_per_batch=1,
                sampler=samplers.SliceSampler(batch_size=12, axis=-1),
            )
            xb, yb = next(iter(loader))
            assert xb.shape == (12, 40, 40, 1), xb.shape
            assert yb.shape == (12, 40, 40, 1), yb.shape

            keras_loader = loader.to_keras()
            kx, ky = next(iter(keras_loader))
            assert tuple(kx.shape) == (12, 40, 40, 1), tuple(kx.shape)
            assert tuple(ky.shape) == (12, 40, 40, 1), tuple(ky.shape)

        print("preprocess smoke ok")

    optional_smoke("preprocess/TensorFlow loader bridge", _run)


def check_models() -> None:
    nt = load_nitrain()

    def _run():
        archs = nt.list_architectures()
        assert len(archs) > 0, "no architectures reported"

        arch_fn = nt.fetch_architecture("vgg", dim=2)
        model = arch_fn((48, 48, 1), number_of_outputs=1, mode="regression")
        trainer = nt.Trainer(model, task="regression")
        assert trainer.framework == "keras", trainer.framework
        print(f"architectures={len(archs)}")
        print(f"trainer={trainer.framework}:{trainer.loss}")

    optional_smoke("models/antspynet-tensorflow stack", _run)


def check_predictor() -> None:
    nt = load_nitrain()
    from nitrain import readers, transforms as tx
    from nitrain.samplers import SliceSampler

    def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(nt.fetch_data("example-01", path=tmpdir, overwrite=True))
            ds = nt.Dataset(
                inputs=readers.ImageReader("*/img3d.nii.gz"),
                outputs=readers.ImageReader("*/img3d_100.nii.gz"),
                transforms={("inputs", "outputs"): tx.Resample((40, 40, 40))},
                base_dir=str(base_dir),
            ).select(1)

            arch_fn = nt.fetch_architecture("unet", dim=2)
            model = arch_fn(
                (40, 40, 1),
                number_of_outputs=1,
                number_of_layers=2,
                number_of_filters_at_base_layer=8,
                mode="regression",
            )
            predictor = nt.Predictor(model, task="regression", sampler=SliceSampler(axis=-1))
            preds = predictor.predict(ds)
            assert len(preds) == 1, len(preds)
            assert preds[0].shape == (40, 40, 40), preds[0].shape

        print("predictor smoke ok")

    optional_smoke("predictor/antspynet-tensorflow stack", _run)


def check_torch() -> None:
    torch = require_module("torch", "TorchTrainer smoke")
    monai_nets = require_module("monai.networks.nets", "TorchTrainer smoke")
    nt = load_nitrain()
    from nitrain.trainers import TorchTrainer

    model = monai_nets.DenseNet121(spatial_dims=2, in_channels=1, out_channels=2)
    model.eval()
    out = model(torch.zeros((1, 1, 64, 64)))
    assert tuple(out.shape) == (1, 2), tuple(out.shape)
    trainer = TorchTrainer(
        model,
        optimizer=torch.optim.Adam(model.parameters(), 1e-3),
        loss=torch.nn.MSELoss(),
        metrics=[],
        device="cpu",
    )
    print(f"torch={torch.__version__}")
    print(f"torch-trainer={trainer.__class__.__name__}:{trainer.device}")


MODES: dict[str, Iterable[str]] = {
    "base": ("check_base",),
    "datasets": ("check_base", "check_datasets"),
    "preprocess": ("check_base", "check_preprocess"),
    "models": ("check_base", "check_models"),
    "predictor": ("check_base", "check_preprocess", "check_predictor"),
    "torch": ("check_base", "check_torch"),
    "all": (
        "check_base",
        "check_datasets",
        "check_preprocess",
        "check_models",
        "check_predictor",
        "check_torch",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=sorted(MODES),
        default="all",
        help="which smoke family to run",
    )
    parser.add_argument(
        "--repo-root",
        help="optional checkout root to add to sys.path before imports",
    )
    args = parser.parse_args()
    add_repo_root(args.repo_root)

    for name in MODES[args.mode]:
        globals()[name]()

    print(f"smoke mode {args.mode} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
