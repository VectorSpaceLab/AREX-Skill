#!/usr/bin/env python3
"""Check expected DeepMedic inference output names without changing data."""
from __future__ import print_function

import argparse
import glob
import os
import shutil
import sys
import tempfile


def case_stem(name):
    """Return the basename used by DeepMedic before adding an output suffix."""
    name = os.path.basename(name)
    if name.endswith(".nii.gz"):
        return name[:-7]
    if name.endswith(".nii"):
        return name[:-4]
    return name


def expected_prediction_path(prediction_dir, case_name, suffix):
    return os.path.join(prediction_dir, case_stem(case_name) + "_" + suffix + ".nii.gz")


def feature_glob(feature_dir, case_name, pattern):
    stem = case_stem(case_name)
    return os.path.join(feature_dir, pattern.format(case=stem))


def check_outputs(prediction_dir, case_names, prob_classes=0,
                  require_features=False, feature_dir=None,
                  seg_suffix="Segm", prob_suffix="ProbMapClass",
                  feature_pattern="{case}_pathway*_layer*_fm*.nii.gz",
                  verbose=True):
    """Return (report_lines, missing_count); perform no writes."""
    prediction_dir = os.path.abspath(prediction_dir)
    feature_dir = (os.path.abspath(feature_dir) if feature_dir else
                   os.path.join(os.path.dirname(prediction_dir), "features"))
    lines = ["prediction directory: {}".format(prediction_dir),
             "feature directory: {}{}".format(
                 feature_dir, " (required)" if require_features else " (not required)")]
    missing_count = 0

    if not os.path.isdir(prediction_dir):
        lines.append("ERROR: prediction directory does not exist or is not a directory")
        return lines, max(1, len(case_names))
    if not case_names:
        lines.append("ERROR: no expected case names were supplied")
        return lines, 1
    if prob_classes < 0:
        lines.append("ERROR: --prob-classes must be non-negative")
        return lines, 1

    for case_name in case_names:
        stem = case_stem(case_name)
        lines.append("CASE {} (stem {})".format(case_name, stem))
        seg_path = expected_prediction_path(prediction_dir, case_name, seg_suffix)
        if os.path.isfile(seg_path):
            lines.append("  segmentation: OK {}".format(os.path.basename(seg_path)))
        else:
            lines.append("  segmentation: MISSING {}".format(os.path.basename(seg_path)))
            missing_count += 1

        for class_index in range(prob_classes):
            prob_path = expected_prediction_path(
                prediction_dir, case_name, prob_suffix + str(class_index))
            if os.path.isfile(prob_path):
                lines.append("  probability class {}: OK {}".format(
                    class_index, os.path.basename(prob_path)))
            else:
                lines.append("  probability class {}: MISSING {}".format(
                    class_index, os.path.basename(prob_path)))
                missing_count += 1

        if require_features:
            matches = sorted(glob.glob(feature_glob(feature_dir, case_name, feature_pattern)))
            if matches:
                lines.append("  feature maps: OK ({} files)".format(len(matches)))
            else:
                lines.append("  feature maps: MISSING (pattern {})".format(
                    feature_pattern.format(case=stem)))
                missing_count += 1
        else:
            lines.append("  feature maps: not requested")

    lines.append("summary: {} case(s), {} missing requested output(s)".format(
        len(case_names), missing_count))
    return lines, missing_count


def run_self_test():
    """Exercise complete and incomplete synthetic layouts in a temp directory."""
    root = tempfile.mkdtemp(prefix="deepmedic-inference-check-")
    try:
        predictions = os.path.join(root, "predictions")
        features = os.path.join(root, "features")
        os.makedirs(predictions)
        os.makedirs(features)
        for filename in (
                "caseA_Segm.nii.gz",
                "caseA_ProbMapClass0.nii.gz",
                "caseA_ProbMapClass1.nii.gz",
                "caseA_pathway0_layer0_fm0.nii.gz"):
            open(os.path.join(predictions if "pathway" not in filename else features,
                              filename), "w").close()
        lines, missing = check_outputs(
            predictions, ["caseA.nii.gz"], prob_classes=2,
            require_features=True, feature_dir=features)
        if missing:
            print("self-test complete-layout failure")
            print("\n".join(lines))
            return 1
        os.remove(os.path.join(predictions, "caseA_ProbMapClass1.nii.gz"))
        _, missing = check_outputs(
            predictions, ["caseA"], prob_classes=2,
            require_features=True, feature_dir=features, verbose=False)
        if missing != 1:
            print("self-test missing-file detection failure")
            return 1
        print("self-test: PASS (complete layout and one missing probability detected)")
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)


def build_parser():
    parser = argparse.ArgumentParser(
        description=("Report missing DeepMedic segmentation, class-probability, "
                     "and optionally feature-map files. The normal check is read-only."))
    parser.add_argument(
        "prediction_dir", nargs="?",
        help="directory containing saved *_Segm.nii.gz and *_ProbMapClassN.nii.gz files")
    parser.add_argument(
        "case_names", nargs="*",
        help="expected case names as passed to namesForPredictionsPerCase (extensions optional)")
    parser.add_argument(
        "--prob-classes", type=int, default=0, metavar="N",
        help="number of class probability files required per case (default: 0)")
    parser.add_argument(
        "--require-features", action="store_true",
        help="require at least one matching feature-map file per case")
    parser.add_argument(
        "--feature-dir", default=None,
        help="feature directory; default is prediction_dir/../features")
    parser.add_argument(
        "--feature-pattern", default="{case}_pathway*_layer*_fm*.nii.gz",
        help="glob pattern; use {case} for the case stem")
    parser.add_argument(
        "--seg-suffix", default="Segm",
        help="segmentation suffix from suffixForSegmAndProbsDict (default: Segm)")
    parser.add_argument(
        "--prob-suffix", default="ProbMapClass",
        help="probability suffix from suffixForSegmAndProbsDict (default: ProbMapClass)")
    parser.add_argument(
        "--self-test", action="store_true",
        help="run a safe synthetic layout check in a temporary directory")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if not args.prediction_dir or not args.case_names:
        parser.error("prediction_dir and at least one case name are required")
    lines, missing = check_outputs(
        args.prediction_dir, args.case_names, args.prob_classes,
        args.require_features, args.feature_dir, args.seg_suffix,
        args.prob_suffix, args.feature_pattern)
    print("\n".join(lines))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
