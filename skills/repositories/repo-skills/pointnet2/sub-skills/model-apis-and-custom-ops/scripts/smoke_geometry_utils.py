#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Smoke-test PointNet2 provider.py and pc_util.py on tiny point clouds.

The smoke distinguishes dependency failures (for example missing eulerangles or
plyfile) from real point-cloud data-shape/range failures. It avoids importing
show3d_balls.py because that file opens an OpenCV GUI window and loads a shared
library at import time.

Compatible with Python 2.7 and Python 3.x.
"""
from __future__ import print_function

import argparse
import json
import os
import sys
import tempfile
import traceback

try:
    import __builtin__ as builtins  # Python 2
except ImportError:  # pragma: no cover - Python 3
    import builtins


class SmokeError(Exception):
    def __init__(self, kind, message):
        Exception.__init__(self, message)
        self.kind = kind
        self.message = message


def _parents(path):
    path = os.path.abspath(path)
    while True:
        yield path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent


def find_repo_root(explicit):
    if explicit:
        root = os.path.abspath(os.path.expanduser(explicit))
        if not os.path.exists(root):
            raise SystemExit("repo root does not exist: %s" % root)
        return root
    starts = [os.getcwd(), os.path.abspath(__file__)]
    for start in starts:
        for candidate in _parents(start):
            if os.path.isfile(os.path.join(candidate, "utils", "provider.py")) and os.path.isfile(
                os.path.join(candidate, "utils", "pc_util.py")
            ):
                return candidate
    raise SystemExit("could not infer repo root; pass --repo-root /path/to/pointnet2")


def import_or_error(module_name, kind):
    try:
        __import__(module_name)
        return sys.modules[module_name]
    except BaseException as exc:
        raise SmokeError(kind, "import %s failed: %s: %s" % (module_name, type(exc).__name__, exc))


def assert_shape(name, value, expected):
    got = tuple(value.shape)
    if got != tuple(expected):
        raise SmokeError("shape", "%s shape %s != expected %s" % (name, got, tuple(expected)))


def assert_close(name, actual, expected, np, atol=1e-6):
    if not np.allclose(actual, expected, atol=atol):
        raise SmokeError("shape", "%s values differed; got %s expected %s" % (name, actual, expected))


def run_provider_checks(repo_root, np):
    if not hasattr(builtins, "xrange"):
        setattr(builtins, "xrange", range)
    utils_dir = os.path.join(repo_root, "utils")
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
    try:
        import provider
    except BaseException as exc:
        raise SmokeError("dependency", "import provider failed: %s: %s" % (type(exc).__name__, exc))

    np.random.seed(123)
    batch = np.array(
        [
            [[0.0, 0.0, 0.0], [0.25, 0.0, 0.0], [0.0, 0.25, 0.0], [0.0, 0.0, 0.25]],
            [[0.1, 0.1, 0.1], [0.2, 0.1, 0.1], [0.1, 0.2, 0.1], [0.1, 0.1, 0.2]],
        ],
        dtype=np.float32,
    )
    labels = np.array([0, 1], dtype=np.int32)

    shuffled_data, shuffled_labels, idx = provider.shuffle_data(batch.copy(), labels.copy())
    assert_shape("shuffle_data.data", shuffled_data, batch.shape)
    assert_shape("shuffle_data.labels", shuffled_labels, labels.shape)
    assert_shape("shuffle_data.idx", idx, labels.shape)

    shuffled_points = provider.shuffle_points(batch.copy())
    assert_shape("shuffle_points", shuffled_points, batch.shape)

    rotated = provider.rotate_point_cloud_by_angle(batch.copy(), np.pi / 2.0)
    assert_shape("rotate_point_cloud_by_angle", rotated, batch.shape)
    assert_close("rotation norm preservation", np.linalg.norm(rotated, axis=2), np.linalg.norm(batch, axis=2), np)

    jittered = provider.jitter_point_cloud(batch.copy(), sigma=0.0, clip=0.05)
    assert_shape("jitter_point_cloud", jittered, batch.shape)
    assert_close("zero-sigma jitter", jittered, batch, np)

    shifted = provider.shift_point_cloud(batch.copy(), shift_range=0.0)
    assert_shape("shift_point_cloud", shifted, batch.shape)
    assert_close("zero-range shift", shifted, batch, np)

    scaled = provider.random_scale_point_cloud(batch.copy(), scale_low=1.0, scale_high=1.0)
    assert_shape("random_scale_point_cloud", scaled, batch.shape)
    assert_close("unit scale", scaled, batch, np)

    dropped = provider.random_point_dropout(batch.copy(), max_dropout_ratio=0.0)
    assert_shape("random_point_dropout", dropped, batch.shape)
    assert_close("zero dropout", dropped, batch, np)

    return {
        "provider_import": True,
        "provider_checks": [
            "shuffle_data",
            "shuffle_points",
            "rotate_point_cloud_by_angle",
            "jitter_point_cloud",
            "shift_point_cloud",
            "random_scale_point_cloud",
            "random_point_dropout",
        ],
    }


def dependency_checks(require_sklearn):
    required = ["eulerangles", "plyfile"]
    optional = ["sklearn"] if require_sklearn else []
    results = {}
    missing = []
    for name in required + optional:
        try:
            __import__(name)
            results[name] = "ok"
        except BaseException as exc:
            results[name] = "%s: %s" % (type(exc).__name__, exc)
            if name in required:
                missing.append(name)
    if missing:
        raise SmokeError(
            "dependency",
            "missing or broken pc_util dependency/dependencies: %s. Fix these before treating geometry failures as data-shape errors. Details: %s"
            % (", ".join(missing), results),
        )
    return results


def run_pc_util_checks(repo_root, np, require_sklearn):
    deps = dependency_checks(require_sklearn)
    utils_dir = os.path.join(repo_root, "utils")
    if utils_dir not in sys.path:
        sys.path.insert(0, utils_dir)
    try:
        import pc_util
    except BaseException as exc:
        raise SmokeError("dependency", "import pc_util failed after dependency check: %s: %s" % (type(exc).__name__, exc))

    points = np.array([[-0.5, -0.5, -0.5], [0.0, 0.0, 0.0], [0.5, 0.25, -0.25]], dtype=np.float32)
    vol = pc_util.point_cloud_to_volume(points, vsize=4, radius=1.0)
    assert_shape("point_cloud_to_volume", vol, (4, 4, 4))
    if float(vol.sum()) < 2.0:
        raise SmokeError("shape", "point_cloud_to_volume produced too few occupied voxels: sum=%s" % float(vol.sum()))

    batch_vol = pc_util.point_cloud_to_volume_batch(points.reshape((1, 3, 3)), vsize=4, radius=1.0, flatten=False)
    assert_shape("point_cloud_to_volume_batch", batch_vol, (1, 4, 4, 4, 1))

    recovered = pc_util.volume_to_point_cloud(vol)
    if len(recovered.shape) != 2 or recovered.shape[1] != 3:
        raise SmokeError("shape", "volume_to_point_cloud returned invalid shape %s" % (recovered.shape,))

    image = pc_util.point_cloud_to_image(points, imgsize=4, radius=1.0, num_sample=2)
    assert_shape("point_cloud_to_image", image, (4, 4, 2, 3))

    tmpdir = tempfile.mkdtemp(prefix="pointnet2_pc_util_")
    ply_path = os.path.join(tmpdir, "tiny.ply")
    try:
        pc_util.write_ply(points, ply_path, text=True)
        roundtrip = pc_util.read_ply(ply_path)
        assert_shape("read_ply", roundtrip, points.shape)
    finally:
        try:
            os.remove(ply_path)
            os.rmdir(tmpdir)
        except Exception:
            pass

    return {
        "pc_util_import": True,
        "dependency_checks": deps,
        "pc_util_checks": [
            "point_cloud_to_volume",
            "point_cloud_to_volume_batch",
            "volume_to_point_cloud",
            "point_cloud_to_image",
            "write_ply/read_ply",
        ],
    }


def run_smoke(repo_root, skip_pc_util, require_sklearn):
    try:
        import numpy as np
    except BaseException as exc:
        raise SmokeError("dependency", "import numpy failed: %s: %s" % (type(exc).__name__, exc))

    result = {
        "ok": True,
        "repo_root": repo_root,
        "python": sys.executable,
        "numpy_version": getattr(np, "__version__", "unknown"),
        "show3d_balls_imported": False,
        "notes": ["show3d_balls.py is intentionally not imported because it opens OpenCV GUI state at import time"],
    }
    result.update(run_provider_checks(repo_root, np))
    if skip_pc_util:
        result["pc_util_skipped"] = True
    else:
        result.update(run_pc_util_checks(repo_root, np, require_sklearn))
    return result


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", help="Path to the pointnet2 checkout. If omitted, search upward.")
    parser.add_argument("--skip-pc-util", action="store_true", help="Only run provider.py checks; skip eulerangles/plyfile and pc_util.py.")
    parser.add_argument("--require-sklearn", action="store_true", help="Also report sklearn import state as an optional geometry-stack dependency.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    repo_root = find_repo_root(args.repo_root)
    try:
        result = run_smoke(repo_root, args.skip_pc_util, args.require_sklearn)
    except SmokeError as exc:
        payload = {
            "ok": False,
            "failure_class": exc.kind,
            "message": exc.message,
            "traceback_tail": traceback.format_exc(limit=4).splitlines()[-8:],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("ERROR [%s]: %s" % (exc.kind, exc.message), file=sys.stderr)
        return 2 if exc.kind == "dependency" else 3
    except BaseException as exc:
        payload = {
            "ok": False,
            "failure_class": "unexpected",
            "message": "%s: %s" % (type(exc).__name__, exc),
            "traceback_tail": traceback.format_exc(limit=4).splitlines()[-8:],
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("ERROR [unexpected]: %s" % payload["message"], file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Geometry utility smoke: OK")
        print("  repo_root: %s" % result["repo_root"])
        print("  numpy_version: %s" % result["numpy_version"])
        print("  provider_checks: %s" % ", ".join(result["provider_checks"]))
        if result.get("pc_util_skipped"):
            print("  pc_util_checks: skipped")
        else:
            print("  dependency_checks: %s" % result["dependency_checks"])
            print("  pc_util_checks: %s" % ", ".join(result["pc_util_checks"]))
        print("  show3d_balls_imported: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
