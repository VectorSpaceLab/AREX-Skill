#!/usr/bin/env python3
"""Run deterministic, local smoke checks for pykitti.raw.

The script creates a three-position raw KITTI tree in a temporary directory,
selects positions [2, 0], and checks metadata plus all four camera/Velodyne
streams. It never downloads, displays, or modifies data outside the temporary
fixture. The fixture is removed unless --keep-temp is supplied.
"""

from __future__ import print_function

import argparse
import datetime as datetime_module
import shutil
import sys
import tempfile
from pathlib import Path


DATE = "2011_09_26"
DRIVE = "0019"
FRAME_NAMES = ("0000000000", "0000000002", "0000000007")
SELECTED_POSITIONS = (2, 0)


def check(condition, message):
    """Raise an assertion with a useful deterministic message."""
    if not condition:
        raise AssertionError(message)


def write_calibration(date_dir):
    rigid = "R: 1 0 0 0 1 0 0 0 1\nT: 0 0 0\n"
    (date_dir / "calib_imu_to_velo.txt").write_text(rigid)
    (date_dir / "calib_velo_to_cam.txt").write_text(rigid)

    projections = {
        "00": (0.0, 0.0),
        "01": (-10.0, 0.0),
        "02": (-20.0, 0.0),
        "03": (-30.0, 0.0),
    }
    lines = []
    for camera, (tx, _unused) in projections.items():
        values = (100.0, 0.0, 2.0, tx,
                  0.0, 100.0, 1.0, 0.0,
                  0.0, 0.0, 1.0, 0.0)
        lines.append("P_rect_{}: {}".format(
            camera, " ".join(str(value) for value in values)))
    for camera in ("00", "01", "02", "03"):
        lines.append("R_rect_{}: {}".format(
            camera, "1 0 0 0 1 0 0 0 1"))
    (date_dir / "calib_cam_to_cam.txt").write_text("\n".join(lines) + "\n")


def write_raw_tree(base_dir):
    """Create a tiny but parser-compatible raw KITTI tree."""
    # Imports stay here so --help works even in an unprepared environment.
    import numpy as np
    from PIL import Image

    date_dir = base_dir / DATE
    date_dir.mkdir(parents=True, exist_ok=True)
    drive_dir = date_dir / (DATE + "_drive_" + DRIVE + "_sync")
    write_calibration(date_dir)

    for camera in range(4):
        (drive_dir / "image_{:02d}".format(camera) / "data").mkdir(
            parents=True, exist_ok=True)
    velo_dir = drive_dir / "velodyne_points" / "data"
    oxts_dir = drive_dir / "oxts" / "data"
    velo_dir.mkdir(parents=True)
    oxts_dir.mkdir(parents=True)

    timestamps = []
    timestamp_fractions = (123456789, 987654321, 555555999)
    for position, frame_name in enumerate(FRAME_NAMES):
        for camera in (0, 1):
            image = Image.new("L", (4, 3), color=20 + position + camera)
            image.save(drive_dir / "image_{:02d}".format(camera) / "data"
                       / (frame_name + ".png"))
        for camera in (2, 3):
            image = Image.new(
                "RGB", (4, 3),
                color=(20 + position, 40 + camera, 60 + position + camera),
            )
            image.save(drive_dir / "image_{:02d}".format(camera) / "data"
                       / (frame_name + ".png"))

        points = np.array([
            [position + 1.0, 0.0, 10.0, 0.25],
            [position + 2.0, 1.0, 11.0, 0.50],
        ], dtype=np.float32)
        points.tofile(velo_dir / (frame_name + ".bin"))

        # OXTS has 25 floating fields followed by five integer flags/counts.
        lat = 49.0 + position * 0.000001
        lon = 8.0 + position * 0.000001
        row = [lat, lon, 100.0 + position * 0.5] + [0.0] * 22
        row += [3, 10, 6, 6, 6]
        check(len(row) == 30, "fixture OXTS row must contain 30 fields")
        (oxts_dir / (frame_name + ".txt")).write_text(
            " ".join(str(value) for value in row) + "\n")
        timestamps.append(
            "2011-09-26 11:00:00.{:09d}\n".format(
                timestamp_fractions[position]))

    (drive_dir / "oxts" / "timestamps.txt").write_text("".join(timestamps))
    return date_dir, drive_dir


def run_smoke(keep_temp=False):
    """Create the fixture, run checks, and return a process status."""
    try:
        import numpy as np
        import pykitti
    except ModuleNotFoundError as exc:
        print(
            "raw fixture smoke: missing import {}. Install pykitti's runtime "
            "dependencies; top-level pykitti==0.3.1 also needs compatible "
            "OpenCV (cv2).".format(exc.name),
            file=sys.stderr,
        )
        return 2

    temp_dir = Path(tempfile.mkdtemp(prefix="pykitti-raw-fixture-"))
    try:
        _date_dir, drive_dir = write_raw_tree(temp_dir)
        data = pykitti.raw(
            str(temp_dir), DATE, DRIVE,
            dataset="sync", frames=list(SELECTED_POSITIONS), imtype="png",
        )

        check(len(data) == 2, "selected timestamp count")
        check(data.frames == list(SELECTED_POSITIONS), "selected frame positions")
        check([Path(path).stem for path in data.cam0_files] ==
              [FRAME_NAMES[2], FRAME_NAMES[0]], "non-contiguous cam0 order")
        check([Path(path).stem for path in data.velo_files] ==
              [FRAME_NAMES[2], FRAME_NAMES[0]], "non-contiguous velo order")
        for name in ("cam0_files", "cam1_files", "cam2_files", "cam3_files",
                     "velo_files", "oxts_files"):
            check(len(getattr(data, name)) == 2, name + " selection count")

        expected_stamps = [
            datetime_module.datetime(2011, 9, 26, 11, 0, 0, 555555),
            datetime_module.datetime(2011, 9, 26, 11, 0, 0, 123456),
        ]
        check(data.timestamps == expected_stamps,
              "nanosecond timestamps must truncate to microseconds")
        check(len(data.oxts) == 2, "selected OXTS count")
        check(np.isclose(data.oxts[0].packet.lat, 49.000002),
              "OXTS follows selected position order")
        check(data.oxts[0].T_w_imu.shape == (4, 4), "OXTS pose shape")
        check(np.allclose(data.oxts[0].T_w_imu[:3, 3], 0.0),
              "first selected OXTS pose is the local origin")
        check(np.isfinite(data.oxts[1].T_w_imu).all(),
              "OXTS pose contains finite values")

        calib = data.calib
        check(calib.P_rect_20.shape == (3, 4), "P_rect_20 shape")
        check(calib.K_cam2.shape == (3, 3), "K_cam2 shape")
        check(calib.T_velo_imu.shape == (4, 4), "T_velo_imu shape")
        check(calib.T_cam2_velo.shape == (4, 4), "T_cam2_velo shape")
        check(np.allclose(calib.T_velo_imu, np.eye(4)),
              "identity IMU-to-Velodyne fixture calibration")
        check(np.isclose(calib.b_gray, 0.1), "gray baseline")
        check(np.isclose(calib.b_rgb, 0.1), "RGB baseline")

        gray_left, gray_right = data.get_gray(0)
        check(gray_left.mode == "L" and gray_right.mode == "L",
              "gray image modes")
        check(np.asarray(gray_left).shape == (3, 4), "gray left image shape")
        check(np.asarray(gray_right).shape == (3, 4), "gray right image shape")

        rgb_left, rgb_right = data.get_rgb(0)
        check(rgb_left.mode == "RGB" and rgb_right.mode == "RGB",
              "RGB image modes")
        check(np.asarray(rgb_left).shape == (3, 4, 3), "RGB left image shape")
        check(np.asarray(rgb_right).shape == (3, 4, 3), "RGB right image shape")
        check(len(list(data.gray)) == 2, "gray stereo generator length")
        check(len(list(data.rgb)) == 2, "RGB stereo generator length")

        scan = data.get_velo(0)
        check(scan.dtype == np.float32, "Velodyne dtype")
        check(scan.shape == (2, 4), "Velodyne shape")
        check(np.allclose(scan[0], [3.0, 0.0, 10.0, 0.25]),
              "selected Velodyne values")
        streamed_scans = list(data.velo)
        check(len(streamed_scans) == 2, "Velodyne generator length")
        check(all(item.shape == (2, 4) for item in streamed_scans),
              "streamed Velodyne shapes")

        print("raw fixture smoke: PASS")
        print("checked temporary tree: {}".format(drive_dir))
        return 0
    except Exception as exc:  # make fixture failures visible in CI logs
        print("raw fixture smoke: FAIL: {}: {}".format(
            type(exc).__name__, exc), file=sys.stderr)
        return 1
    finally:
        if keep_temp:
            print("kept temporary fixture: {}".format(temp_dir))
        else:
            shutil.rmtree(str(temp_dir), ignore_errors=False)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Smoke-test pykitti.raw with a local temporary KITTI fixture.")
    parser.add_argument(
        "--keep-temp", action="store_true",
        help="retain the temporary fixture for manual inspection (default: clean up)",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    return run_smoke(keep_temp=args.keep_temp)


if __name__ == "__main__":
    sys.exit(main())
