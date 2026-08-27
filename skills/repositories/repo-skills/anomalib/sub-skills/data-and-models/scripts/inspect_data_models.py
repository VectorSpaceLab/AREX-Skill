#!/usr/bin/env python3
"""Inspect anomalib data/model entry points or validate custom layouts.

This helper stays inside the generated skill tree and only uses the installed
anomalib package. It is intended for quick discovery and sanity checks, not for
full training or export runs.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError as exc:  # pragma: no cover - exercised in misconfigured environments
    raise SystemExit(
        "pandas is required for this helper. Run it inside the anomalib inspection environment or install the repo's data dependencies."
    ) from exc

try:
    from anomalib.data import (
        ADAM3D,
        Avenue,
        Folder,
        Folder3D,
        MVTec3D,
        MVTecAD,
        PredictDataset,
        ShanghaiTech,
        Tabular,
        UCSDped,
        get_datamodule,
    )
    from anomalib.data.datasets.image.folder import FolderDataset
    from anomalib.models import AiVad, EfficientAd, Fuvas, Padim, Patchcore, get_model, list_models
except ImportError as exc:  # pragma: no cover - exercised in misconfigured environments
    raise SystemExit(
        "anomalib is required for this helper. Activate the anomalib inspection environment before running it."
    ) from exc

DATA_ENTRYPOINTS = [
    MVTecAD,
    Folder,
    Tabular,
    PredictDataset,
    Avenue,
    ShanghaiTech,
    UCSDped,
    MVTec3D,
    Folder3D,
    ADAM3D,
]
MODEL_ENTRYPOINTS = [Padim, Patchcore, EfficientAd, AiVad, Fuvas]


def signature_text(obj: object) -> str:
    """Return a stable signature string for a callable or type."""
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError):
        return "(signature unavailable)"


def print_section(title: str) -> None:
    print(f"\n## {title}")


def print_entrypoints(case: str) -> None:
    print_section("Datamodules")
    for entry in DATA_ENTRYPOINTS:
        print(f"{entry.__name__}{signature_text(entry)}")

    print_section("Models")
    for entry in MODEL_ENTRYPOINTS:
        print(f"{entry.__name__}{signature_text(entry)}")

    print_section("Helpers")
    print(f"get_datamodule{signature_text(get_datamodule)}")
    print(f"get_model{signature_text(get_model)}")

    print_section(f"Registry ({case})")
    for name in sorted(list_models(case=case)):
        print(name)


def summarize_dataframe(samples: pd.DataFrame) -> None:
    print(f"rows: {len(samples)}")
    print(f"columns: {', '.join(samples.columns)}")
    if "task" in samples.attrs:
        print(f"task: {samples.attrs['task']}")
    if "split" in samples.columns:
        print("split counts:")
        print(samples["split"].value_counts(dropna=False).to_string())
    if "label_index" in samples.columns:
        print("label counts:")
        print(samples["label_index"].value_counts(dropna=False).to_string())
    if "mask_path" in samples.columns:
        nonempty = int((samples["mask_path"].astype(str) != "").sum())
        print(f"rows with masks: {nonempty}")


def validate_folder(args: argparse.Namespace) -> int:
    extensions = tuple(args.extensions) if args.extensions else None
    try:
        dataset = FolderDataset(
            name=args.name,
            root=args.root,
            normal_dir=args.normal_dir,
            abnormal_dir=args.abnormal_dir,
            normal_test_dir=args.normal_test_dir,
            mask_dir=args.mask_dir,
            split=args.split,
            extensions=extensions,
        )
        samples = dataset.samples
    except Exception as exc:  # pragma: no cover - handled in tool output
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    summarize_dataframe(samples)
    return 0


def read_tabular_file(file_path: Path, file_format: str | None) -> pd.DataFrame:
    inferred_format = file_format or file_path.suffix.lstrip(".")
    if not inferred_format:
        raise ValueError(f"Could not infer a file format from {file_path.name!r}")

    read_func = getattr(pd, f"read_{inferred_format}", None)
    if read_func is None:
        raise ValueError(f"Unsupported file format: {inferred_format!r}")

    return read_func(file_path)


def normalize_tabular_samples(samples: pd.DataFrame, root: str | Path | None = None) -> pd.DataFrame:
    """Normalize a tabular samples table using anomalib-style rules."""
    samples = samples.copy()
    if "image_path" not in samples.columns:
        raise ValueError("The samples table must contain an 'image_path' column.")

    samples = samples.sort_values(by="image_path", ignore_index=True)

    has_label_index = "label_index" in samples.columns
    has_label = "label" in samples.columns
    has_split = "split" in samples.columns

    if not any((has_label_index, has_label, has_split)):
        raise ValueError("The samples table must contain at least one of 'label_index', 'label' or 'split' columns.")

    def normalize_text(value: object) -> str:
        return str(value).strip().lower()

    if has_label_index:
        samples["label_index"] = pd.to_numeric(samples["label_index"], errors="coerce").astype("Int64")

    if not has_label_index and has_label:
        label_to_index = {"abnormal": 1, "normal": 0, "normal_test": 0}
        samples["label_index"] = samples["label"].map(lambda value: label_to_index.get(normalize_text(value), pd.NA)).astype("Int64")
    elif not has_label_index and has_split:
        split_to_index = {"train": 0, "test": 1}
        samples["label_index"] = samples["split"].map(lambda value: split_to_index.get(normalize_text(value), pd.NA)).astype("Int64")

    has_label_index = "label_index" in samples.columns
    has_label = "label" in samples.columns
    has_split = "split" in samples.columns

    if has_label_index and not has_label and not has_split:
        index_to_label = {0: "normal", 1: "abnormal"}
        samples["label"] = samples["label_index"].map(lambda value: index_to_label.get(value, pd.NA))
        has_label = True

    if has_label_index and not has_label and has_split:
        def infer_label(row: pd.Series) -> object:
            split_value = normalize_text(row["split"])
            label_index = row["label_index"]
            if label_index == 0 and split_value == "train":
                return "normal"
            if label_index == 0 and split_value == "test":
                return "normal_test"
            if label_index == 1:
                return "abnormal"
            return pd.NA

        samples["label"] = samples.apply(infer_label, axis=1)
        has_label = True

    if has_label_index and has_label and not has_split:
        label_to_split = {"normal": "train", "abnormal": "test", "normal_test": "test"}
        samples["split"] = samples["label"].map(lambda value: label_to_split.get(normalize_text(value), pd.NA))
        has_split = True

    if "mask_path" not in samples.columns:
        samples["mask_path"] = ""

    samples["mask_path"] = samples["mask_path"].fillna("")

    if root:
        root_path = Path(root)
        samples["image_path"] = samples["image_path"].map(lambda value: str(Path(root_path, value)))
        samples.loc[
            samples["mask_path"] != "",
            "mask_path",
        ] = samples.loc[samples["mask_path"] != "", "mask_path"].map(lambda value: str(Path(root_path, value)))

    samples = samples.astype({"image_path": "string", "mask_path": "string"})
    if "label" in samples.columns:
        samples = samples.astype({"label": "string"})

    if "split" in samples.columns:
        allowed = {"train", "val", "test"}
        observed = {normalize_text(value) for value in samples["split"].dropna().unique()}
        invalid = sorted(observed - allowed)
        if invalid:
            raise ValueError(f"Unexpected split labels: {', '.join(invalid)}")
        samples["split"] = samples["split"].map(normalize_text)

    if samples.isna().any().any():
        raise ValueError("The samples table contains None or NaN values.")

    if ((samples["label_index"] == 1) & (samples["split"] == "train")).any():
        raise ValueError("Training set must not contain anomalous samples.")

    abnormal_samples = samples.loc[samples["label_index"] == 1]
    if not abnormal_samples.empty:
        mismatch_masks = not abnormal_samples.apply(
            lambda row: Path(row["image_path"]).stem in Path(row["mask_path"]).stem,
            axis=1,
        ).all()
        if mismatch_masks:
            raise ValueError(
                "Mismatch between anomalous images and mask images. Make sure the mask files follow the same naming convention as the anomalous images."
            )

    missing_images = [path for path in samples["image_path"] if not Path(path).exists()]
    if missing_images:
        raise FileNotFoundError(f"Missing file path(s) in samples: {missing_images[0]}")

    missing_masks = [path for path in samples["mask_path"] if path and not Path(path).exists()]
    if missing_masks:
        raise FileNotFoundError(f"Missing file path(s) in samples: {missing_masks[0]}")

    samples.attrs["task"] = "classification" if (samples["mask_path"] == "").all() else "segmentation"
    return samples


def validate_tabular(args: argparse.Namespace) -> int:
    file_path = Path(args.file)
    try:
        samples = read_tabular_file(file_path, args.format)
        if "split" in samples.columns:
            allowed = {"train", "val", "test"}
            observed = {str(value).strip().lower() for value in samples["split"].dropna().unique()}
            invalid = sorted(observed - allowed)
            if invalid:
                print(
                    f"WARNING: unexpected split labels before normalization: {', '.join(invalid)}",
                    file=sys.stderr,
                )
        validated = normalize_tabular_samples(samples, root=args.root)
        if args.split:
            validated = validated[validated["split"] == args.split].reset_index(drop=True)
    except Exception as exc:  # pragma: no cover - handled in tool output
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    summarize_dataframe(validated)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list",
        help="List the current data/model entry points and registry names.",
    )
    list_parser.add_argument(
        "--case",
        choices=("snake", "pascal", "title"),
        default="pascal",
        help="Case to use for list_models() output.",
    )
    list_parser.set_defaults(func=lambda args: (print_entrypoints(args.case) or 0))

    folder_parser = subparsers.add_parser(
        "check-folder",
        help="Validate a custom Folder layout by calling anomalib's parser.",
    )
    folder_parser.add_argument("--name", required=True, help="Dataset name used by the datamodule.")
    folder_parser.add_argument("--root", required=True, help="Dataset root directory.")
    folder_parser.add_argument("--normal-dir", required=True, help="Normal image directory.")
    folder_parser.add_argument("--abnormal-dir", help="Abnormal image directory.")
    folder_parser.add_argument("--normal-test-dir", help="Explicit normal test directory.")
    folder_parser.add_argument("--mask-dir", help="Mask directory for segmentation layouts.")
    folder_parser.add_argument("--split", choices=("train", "val", "test"), help="Optional split filter.")
    folder_parser.add_argument(
        "--extensions",
        nargs="*",
        help="Optional allowed extensions such as .png .jpg .bmp.",
    )
    folder_parser.set_defaults(func=validate_folder)

    tabular_parser = subparsers.add_parser(
        "check-tabular",
        help="Validate a tabular layout with anomalib-style rules.",
    )
    tabular_parser.add_argument("--file", required=True, help="Path to a csv/parquet/json table.")
    tabular_parser.add_argument("--root", help="Optional root directory for relative paths.")
    tabular_parser.add_argument(
        "--format",
        help="Explicit pandas reader name such as csv, parquet, or json.",
    )
    tabular_parser.add_argument("--split", choices=("train", "val", "test"), help="Optional split filter.")
    tabular_parser.set_defaults(func=validate_tabular)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = args.func(args)
    return int(result or 0)


if __name__ == "__main__":
    raise SystemExit(main())
