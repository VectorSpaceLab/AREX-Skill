"""Synthetic diagnostics for keras-vis image utility behavior.

The script intentionally uses generated numpy arrays instead of repository sample
images. By default it treats Pillow and imageio as optional: their availability
is reported, but missing optional packages do not fail the check unless
--require-optional is supplied.
"""
from __future__ import print_function

import argparse
import json
import os
import sys
import traceback

# Keep TensorFlow/Keras import noise low when the legacy backend is present.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")


def _find_module(module_name):
    """Return True when a module can be located without importing heavy code."""
    try:
        try:
            from importlib import util as importlib_util
            return importlib_util.find_spec(module_name) is not None
        except ImportError:
            import imp  # pylint: disable=deprecated-module
            imp.find_module(module_name)
            return True
    except Exception:
        return False


def _slice_item_to_text(item):
    """Render slice objects in a compact, deterministic form."""
    if item is Ellipsis:
        return "..."
    if isinstance(item, slice):
        if item.start is None and item.stop is None and item.step is None:
            return ":"
        return "slice({0}, {1}, {2})".format(item.start, item.stop, item.step)
    return repr(item)


def _slice_tuple_to_text(item_tuple):
    return "[" + ", ".join(_slice_item_to_text(item) for item in item_tuple) + "]"


def _ok(name, details):
    return {"name": name, "status": "pass", "details": details}


def _fail(name, message, verbose=False):
    details = {"message": str(message)}
    if verbose:
        details["traceback"] = traceback.format_exc()
    return {"name": name, "status": "fail", "details": details}


def _import_required(verbose=False):
    """Import required runtime modules and return either objects or a failure."""
    try:
        import numpy as np
        from keras import backend as K
        from vis.utils import utils
        from vis.visualization import overlay
        return {"np": np, "K": K, "utils": utils, "overlay": overlay}, None
    except Exception as exc:  # pragma: no cover - diagnostic path
        return None, _fail("required-imports", exc, verbose=verbose)


def _check_normalize(np, utils):
    arr = np.array([-2.0, 0.0, 2.0], dtype="float32")
    scaled = utils.normalize(arr, min_value=-1.0, max_value=1.0)
    if abs(float(np.min(scaled)) + 1.0) > 1e-5:
        raise AssertionError("normalized minimum is not close to -1")
    if abs(float(np.max(scaled)) - 1.0) > 1e-5:
        raise AssertionError("normalized maximum is not close to 1")

    constant = utils.normalize(np.ones((3,), dtype="float32"), min_value=5.0, max_value=9.0)
    if not np.allclose(constant, 5.0):
        raise AssertionError("constant arrays should map to min_value")

    return _ok("normalize", {
        "input": [-2.0, 0.0, 2.0],
        "range": [round(float(np.min(scaled)), 6), round(float(np.max(scaled)), 6)],
        "constant_array_value": round(float(constant[0]), 6),
    })


def _check_overlay(np, overlay):
    first = np.full((2, 2, 3), 200, dtype="uint8")
    second = np.zeros((2, 2, 3), dtype="uint8")
    blended = overlay(first, second, alpha=0.25)
    if blended.shape != first.shape:
        raise AssertionError("overlay changed shape")
    if blended.dtype != first.dtype:
        raise AssertionError("overlay did not preserve first array dtype")
    if int(blended[0, 0, 0]) != 50:
        raise AssertionError("unexpected overlay blend value")

    saw_alpha_error = False
    try:
        overlay(first, second, alpha=1.5)
    except ValueError:
        saw_alpha_error = True
    if not saw_alpha_error:
        raise AssertionError("overlay should reject alpha outside [0, 1]")

    saw_shape_error = False
    try:
        overlay(first, np.zeros((2, 2, 1), dtype="uint8"), alpha=0.5)
    except ValueError:
        saw_shape_error = True
    if not saw_shape_error:
        raise AssertionError("overlay should reject mismatched shapes")

    return _ok("overlay", {
        "shape": list(blended.shape),
        "dtype": str(blended.dtype),
        "sample_value": int(blended[0, 0, 0]),
        "invalid_alpha_rejected": saw_alpha_error,
        "shape_mismatch_rejected": saw_shape_error,
    })


def _check_data_formats(np, K, utils):
    old_format = K.image_data_format()
    report = {}
    try:
        cases = [
            ("channels_first", (2, 3, 5, 7), (2, 3, 5, 7), (2, 3, 4, 5, 6), (2, 3, 4, 5, 6), "[:, 1, :, :]"),
            ("channels_last", (2, 5, 7, 3), (2, 3, 5, 7), (2, 4, 5, 6, 3), (2, 3, 4, 5, 6), "[:, :, :, 1]"),
        ]
        item = (slice(None), 1, slice(None), slice(None))
        ellipsis_item = (slice(None), 1, Ellipsis)
        for fmt, shape2, expected2, shape3, expected3, expected_slice_text in cases:
            K.set_image_data_format(fmt)
            got2 = utils.get_img_shape(np.zeros(shape2, dtype="float32"))
            got3 = utils.get_img_shape(np.zeros(shape3, dtype="float32"))
            transformed = utils.slicer[item]
            ellipsis_transformed = utils.slicer[ellipsis_item]
            if tuple(got2) != expected2:
                raise AssertionError("{0} 2D image shape report mismatch: {1}".format(fmt, got2))
            if tuple(got3) != expected3:
                raise AssertionError("{0} 3D image shape report mismatch: {1}".format(fmt, got3))
            if _slice_tuple_to_text(transformed) != expected_slice_text:
                raise AssertionError("{0} slice transform mismatch: {1}".format(fmt, transformed))
            report[fmt] = {
                "input_2d": list(shape2),
                "reported_2d": list(got2),
                "input_3d": list(shape3),
                "reported_3d": list(got3),
                "slice_from_canonical": _slice_tuple_to_text(transformed),
                "ellipsis_slice_from_canonical": _slice_tuple_to_text(ellipsis_transformed),
            }
    finally:
        K.set_image_data_format(old_format)
    return _ok("data-format-shapes", report)


def _check_small_helpers(np, utils):
    if utils.listify("abc") != ["abc"]:
        raise AssertionError("listify should wrap strings as one item")
    if utils.listify([1, 2]) != [1, 2]:
        raise AssertionError("listify should leave lists unchanged")
    merged = utils.add_defaults_to_kwargs({"a": 1, "b": 2}, b=3, c=4)
    if merged != {"a": 1, "b": 3, "c": 4}:
        raise AssertionError("add_defaults_to_kwargs merge behavior changed")
    rgb = np.array([[[1, 2, 3]]], dtype="uint8")
    bgr = utils.bgr2rgb(rgb)
    if bgr.tolist() != [[[3, 2, 1]]]:
        raise AssertionError("bgr2rgb should reverse the last axis")
    labels = utils.lookup_imagenet_labels([0, 20, 999])
    if labels != ["tench", "water_ouzel", "toilet_tissue"]:
        raise AssertionError("ImageNet package labels are not available or changed")
    stitched = utils.stitch_images([np.zeros((2, 3, 1), dtype="uint8"), np.ones((2, 3, 1), dtype="uint8")], margin=1, cols=2)
    if stitched.shape != (2, 7, 1):
        raise AssertionError("stitch_images output shape mismatch")
    return _ok("small-helpers", {
        "listify_string": ["abc"],
        "merged_kwargs": merged,
        "bgr2rgb_sample": bgr.tolist(),
        "imagenet_labels": labels,
        "stitched_shape": list(stitched.shape),
    })


def _optional_report(require_optional):
    optional = {
        "Pillow(PIL)": _find_module("PIL"),
        "imageio": _find_module("imageio"),
    }
    missing = [name for name, available in optional.items() if not available]
    status = "pass"
    details = {"available": optional, "required": bool(require_optional)}
    if require_optional and missing:
        status = "fail"
        details["missing"] = missing
        details["message"] = "missing optional image utilities requested by --require-optional"
    return {"name": "optional-dependencies", "status": status, "details": details}


def _run_checks(args):
    report = {
        "status": "pass",
        "checks": [],
    }
    report["checks"].append(_optional_report(args.require_optional))

    imports, import_failure = _import_required(verbose=args.verbose)
    if import_failure is not None:
        report["checks"].append(import_failure)
    else:
        check_specs = [
            ("normalize", lambda: _check_normalize(imports["np"], imports["utils"])),
            ("overlay", lambda: _check_overlay(imports["np"], imports["overlay"])),
            ("data-format-shapes", lambda: _check_data_formats(imports["np"], imports["K"], imports["utils"])),
            ("small-helpers", lambda: _check_small_helpers(imports["np"], imports["utils"])),
        ]
        for name, run_check in check_specs:
            try:
                report["checks"].append(run_check())
            except Exception as exc:  # pragma: no cover - diagnostic path
                report["checks"].append(_fail(name, exc, verbose=args.verbose))

    if any(check["status"] != "pass" for check in report["checks"]):
        report["status"] = "fail"
    return report


def _print_text(report):
    print("keras-vis image utilities diagnostic: {0}".format(report["status"].upper()))
    for check in report["checks"]:
        print("- {0}: {1}".format(check["name"], check["status"]))
        details = check.get("details", {})
        if check["name"] == "optional-dependencies":
            available = details.get("available", {})
            for dep_name in sorted(available):
                state = "available" if available[dep_name] else "missing (optional)"
                if details.get("required") and not available[dep_name]:
                    state = "missing (required by flag)"
                print("  - {0}: {1}".format(dep_name, state))
        elif check["status"] == "fail":
            print("  - message: {0}".format(details.get("message", "unknown failure")))
        else:
            summary = json.dumps(details, sort_keys=True)
            print("  - details: {0}".format(summary))


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run deterministic synthetic checks for keras-vis image utilities."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the diagnostic report as JSON instead of human-readable text",
    )
    parser.add_argument(
        "--require-optional",
        action="store_true",
        help="fail when optional Pillow or imageio support is missing",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="include tracebacks for failed diagnostic steps",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    report = _run_checks(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text(report)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
