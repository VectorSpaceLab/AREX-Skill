#!/usr/bin/env python3
"""Validate DeepMedic-style per-channel NIFTI manifests without importing DeepMedic."""
from __future__ import print_function

import argparse
import os
import sys
from pathlib import Path

import numpy as np


class ValidationError(Exception):
    """An input manifest or NIFTI failed a validation check."""


def _manifest_path(value):
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValidationError("manifest does not exist: {}".format(path))
    return path.resolve()


def read_manifest(value, allow_dash=False):
    """Read one list file; data paths are relative to that list file."""
    path = _manifest_path(value)
    entries = []
    with path.open("r") as handle:
        for line_number, raw in enumerate(handle, 1):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped == "-":
                if not allow_dash:
                    raise ValidationError(
                        "{}:{}: '-' is only allowed in channel manifests".format(path, line_number)
                    )
                entries.append(None)
                continue
            entry = Path(stripped).expanduser()
            if not entry.is_absolute():
                entry = path.parent / entry
            entries.append(entry.resolve())
    if not entries:
        raise ValidationError("manifest is empty: {}".format(path))
    return path, entries


def _deepmedic_shape(image):
    """Return the 3-D shape accepted by dataManagement.io.load_volume."""
    shape = tuple(int(dim) for dim in image.shape)
    if len(shape) == 2:
        return shape + (1,)
    if len(shape) == 3:
        return shape
    if len(shape) == 4 and shape[3] == 1:
        return shape[:3]
    raise ValidationError(
        "NIFTI has unsupported shape {}; expected 2-D, 3-D, or 4-D with fourth dimension 1".format(shape)
    )


def _deepmedic_zooms(image):
    shape = _deepmedic_shape(image)
    zooms = tuple(float(value) for value in image.header.get_zooms()[: len(image.shape)])
    if len(zooms) < len(shape):
        zooms = zooms + (1.0,) * (len(shape) - len(zooms))
    return zooms[:3]


def load_header(path, role, read_data=False):
    if path is None:
        return None
    if not path.is_file():
        raise ValidationError("{} file does not exist: {}".format(role, path))
    try:
        import nibabel as nib
        image = nib.load(str(path))
        shape = _deepmedic_shape(image)
        zooms = _deepmedic_zooms(image)
        data = None
        if read_data:
            data = np.asanyarray(image.dataobj)
            # Force the same dimensional interpretation as load_volume().
            if data.ndim == 2:
                data = np.expand_dims(data, axis=2)
            elif data.ndim == 4:
                data = data[:, :, :, 0]
            if tuple(data.shape) != shape:
                raise ValidationError(
                    "{} data shape {} differs from header shape {}".format(path, data.shape, shape)
                )
        return {
            "path": path,
            "role": role,
            "shape": shape,
            "zooms": zooms,
            "affine": np.asarray(image.affine),
            "data": data,
        }
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("cannot load {} NIFTI {}: {}".format(role, path, exc))


def _same_tuple(left, right, tolerance):
    return len(left) == len(right) and all(abs(a - b) <= tolerance for a, b in zip(left, right))


def _validate_labels(info, num_classes, labels_seen):
    try:
        import nibabel as nib
        image = nib.load(str(info["path"]))
        data = np.asanyarray(image.dataobj)
        if data.ndim == 2:
            data = np.expand_dims(data, axis=2)
        elif data.ndim == 4:
            data = data[:, :, :, 0]
        if tuple(data.shape) != info["shape"]:
            raise ValidationError(
                "label data shape {} differs from header shape {}: {}".format(
                    data.shape, info["shape"], info["path"]
                )
            )
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("cannot read label data {}: {}".format(info["path"], exc))
    if not np.all(np.isfinite(data)):
        raise ValidationError("label volume contains non-finite values: {}".format(info["path"]))
    if not np.all(data == np.rint(data)):
        raise ValidationError(
            "label volume contains non-integer values (DeepMedic would round them): {}".format(info["path"])
        )
    integer_data = np.rint(data).astype(np.int64, copy=False)
    if integer_data.size:
        low = int(integer_data.min())
        high = int(integer_data.max())
        if low < 0:
            raise ValidationError("label values must start at 0 or above; {} has minimum {}".format(info["path"], low))
        if num_classes is not None and high >= num_classes:
            raise ValidationError(
                "label values in {} reach {}, outside [0, {})".format(info["path"], high, num_classes)
            )
        labels_seen.update(int(value) for value in np.unique(integer_data))
    return integer_data


def validate(args):
    channel_manifests = [read_manifest(value, allow_dash=True) for value in args.channel_list]
    channel_lists = [items for _, items in channel_manifests]
    n_cases = len(channel_lists[0])
    if any(len(items) != n_cases for items in channel_lists[1:]):
        lengths = [len(items) for items in channel_lists]
        raise ValidationError("channel manifest lengths disagree: {}".format(lengths))

    labels = read_manifest(args.labels_list)[1] if args.labels_list else None
    rois = read_manifest(args.roi_list)[1] if args.roi_list else None
    if labels is not None and len(labels) != n_cases:
        raise ValidationError("labels contain {} entries but channels contain {} cases".format(len(labels), n_cases))
    if rois is not None and len(rois) != n_cases:
        raise ValidationError("ROI masks contain {} entries but channels contain {} cases".format(len(rois), n_cases))

    database_zooms = None
    for case_index in range(n_cases):
        case_infos = []
        for channel_index, items in enumerate(channel_lists):
            path = items[case_index]
            if path is None:
                continue
            case_infos.append(load_header(path, "channel {}".format(channel_index), args.read_data))
        if not case_infos:
            raise ValidationError("case {} has no actual channel file (all entries are '-')".format(case_index + 1))

        label_info = None
        roi_info = None
        if labels is not None:
            label_info = load_header(labels[case_index], "label", args.read_data)
            case_infos.append(label_info)
        if rois is not None:
            roi_info = load_header(rois[case_index], "ROI", args.read_data)
            case_infos.append(roi_info)

        reference = case_infos[0]
        if database_zooms is None:
            database_zooms = reference["zooms"]
        elif not _same_tuple(reference["zooms"], database_zooms, args.voxel_tolerance):
            raise ValidationError(
                "database voxel-size mismatch at case {}: {} has {}, expected {}".format(
                    case_index + 1, reference["path"], reference["zooms"], database_zooms
                )
            )
        for info in case_infos[1:]:
            if info["shape"] != reference["shape"]:
                raise ValidationError(
                    "case {} shape mismatch: {} has {}, expected {} from {}".format(
                        case_index + 1, info["path"], info["shape"], reference["shape"], reference["path"]
                    )
                )
            if not _same_tuple(info["zooms"], reference["zooms"], args.voxel_tolerance):
                raise ValidationError(
                    "case {} voxel-size mismatch: {} has {}, expected {} from {}".format(
                        case_index + 1, info["path"], info["zooms"], reference["zooms"], reference["path"]
                    )
                )
            if args.check_affine and not np.allclose(
                info["affine"], reference["affine"], rtol=0.0, atol=args.affine_tolerance
            ):
                raise ValidationError(
                    "case {} affine mismatch; files may not be co-registered: {} vs {}".format(
                        case_index + 1, info["path"], reference["path"]
                    )
                )

        if label_info is not None and args.check_labels:
            _validate_labels(label_info, args.num_classes, args.labels_seen)

        print(
            "case {:>4}: shape={} voxel_size={} channels={} labels={} roi={}".format(
                case_index + 1,
                reference["shape"],
                tuple(round(value, 6) for value in reference["zooms"]),
                len(channel_lists),
                "yes" if label_info is not None else "no",
                "yes" if roi_info is not None else "no",
            )
        )

    if args.require_contiguous_labels:
        if labels is None:
            raise ValidationError("--require-contiguous-labels requires --labels-list")
        if not args.labels_seen or args.labels_seen != set(range(max(args.labels_seen) + 1)):
            raise ValidationError(
                "observed labels are not contiguous starting at zero: {}".format(sorted(args.labels_seen))
            )

    print("valid: {} cases, {} channel manifest(s)".format(n_cases, len(channel_lists)))
    if args.labels_seen:
        print("observed labels: {}".format(sorted(args.labels_seen)))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Check explicit DeepMedic-style per-channel NIFTI list files. "
            "Paths in a list are resolved relative to that list file. No input data are modified."
        )
    )
    parser.add_argument(
        "--channel-list",
        action="append",
        required=True,
        metavar="FILE",
        help="one list file per modality; repeat once per channel",
    )
    parser.add_argument("--labels-list", metavar="FILE", help="optional one-label-file-per-case list")
    parser.add_argument("--roi-list", metavar="FILE", help="optional one-ROI-file-per-case list")
    parser.add_argument(
        "--num-classes",
        type=int,
        metavar="N",
        help="optional exclusive upper bound for labels (valid values are 0 through N-1)",
    )
    parser.add_argument(
        "--require-contiguous-labels",
        action="store_true",
        help="require the union of observed labels to be exactly 0,1,...,K",
    )
    parser.add_argument(
        "--check-affine",
        action="store_true",
        help="also require matching affines within each subject (recommended co-registration check)",
    )
    parser.add_argument(
        "--affine-tolerance",
        type=float,
        default=1e-4,
        metavar="T",
        help="absolute affine comparison tolerance (default: 1e-4)",
    )
    parser.add_argument(
        "--voxel-tolerance",
        type=float,
        default=1e-5,
        metavar="T",
        help="voxel-size comparison tolerance in header units (default: 1e-5)",
    )
    parser.add_argument(
        "--read-data",
        action="store_true",
        help="read every image payload, not only its NIFTI header; useful for detecting corrupt compressed data",
    )
    parser.add_argument(
        "--skip-label-checks",
        dest="check_labels",
        action="store_false",
        help="skip reading label values; shape/loadability are still checked",
    )
    parser.set_defaults(check_labels=True, labels_seen=set())
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.num_classes is not None and args.num_classes <= 0:
        parser.error("--num-classes must be positive")
    if args.voxel_tolerance < 0 or args.affine_tolerance < 0:
        parser.error("tolerances must be non-negative")
    try:
        return validate(args)
    except ValidationError as exc:
        print("ERROR: {}".format(exc), file=sys.stderr)
        return 1
    except ImportError:
        print("ERROR: nibabel and numpy are required by this standalone validator", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
