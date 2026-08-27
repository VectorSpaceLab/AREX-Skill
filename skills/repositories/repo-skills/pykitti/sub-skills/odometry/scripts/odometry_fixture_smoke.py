#!/usr/bin/env python3
"""Run a deterministic, local-only smoke test for ``pykitti.odometry``.

The fixture is intentionally small and is deleted after the test by default.
Use ``--keep`` when inspecting the generated tree after a run.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import tempfile
from pathlib import Path
from typing import Optional


SEQUENCE = "00"
FRAME_COUNT = 4
SELECTED_FRAMES = [3, 1]


def _check(condition: bool, message: str) -> None:
    """Raise an assertion error even when Python is run with ``-O``."""
    if not condition:
        raise AssertionError(message)


def _write_calibration(path: Path) -> None:
    matrices = {
        "P0": [100, 0, 32, 0, 0, 100, 24, 0, 0, 0, 1, 0],
        "P1": [100, 0, 32, -10, 0, 100, 24, 0, 0, 0, 1, 0],
        "P2": [100, 0, 32, -20, 0, 100, 24, 0, 0, 0, 1, 0],
        "P3": [100, 0, 32, -30, 0, 100, 24, 0, 0, 0, 1, 0],
        "Tr": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    }
    path.write_text(
        "".join(
            "{}: {}\n".format(key, " ".join(str(value) for value in values))
            for key, values in matrices.items()
        ),
        encoding="ascii",
    )


def _write_pose_file(path: Path) -> None:
    lines = []
    for frame in range(FRAME_COUNT):
        # Identity rotation and a frame-specific translation make selection
        # order observable without requiring any external ground truth.
        lines.append(
            "1 0 0 {x} 0 1 0 {y} 0 0 1 {z}\n".format(
                x=frame, y=frame + 0.5, z=frame + 1.0
            )
        )
    path.write_text("".join(lines), encoding="ascii")


def _write_sensor_files(sequence_path: Path) -> None:
    import numpy as np
    from PIL import Image

    for camera in range(4):
        (sequence_path / "image_{}".format(camera)).mkdir()
    (sequence_path / "velodyne").mkdir()

    for frame in range(FRAME_COUNT):
        size = (4 + frame, 3 + frame)
        Image.new("L", size, color=10 + frame).save(
            sequence_path / "image_0" / "{:06d}.png".format(frame)
        )
        Image.new("L", size, color=20 + frame).save(
            sequence_path / "image_1" / "{:06d}.png".format(frame)
        )
        Image.new("RGB", size, color=(30 + frame, 40 + frame, 50 + frame)).save(
            sequence_path / "image_2" / "{:06d}.png".format(frame)
        )
        Image.new("RGB", size, color=(60 + frame, 70 + frame, 80 + frame)).save(
            sequence_path / "image_3" / "{:06d}.png".format(frame)
        )

        points = np.arange((frame + 2) * 4, dtype=np.float32).reshape(-1, 4)
        points[:, 0] += frame
        points.tofile(sequence_path / "velodyne" / "{:06d}.bin".format(frame))


def _build_fixture(root: Path) -> None:
    sequence_path = root / "sequences" / SEQUENCE
    sequence_path.mkdir(parents=True)
    (root / "poses").mkdir()
    _write_calibration(sequence_path / "calib.txt")
    (sequence_path / "times.txt").write_text(
        "".join("{:.1f}\n".format(frame / 10.0) for frame in range(FRAME_COUNT)),
        encoding="ascii",
    )
    _write_pose_file(root / "poses" / "{}.txt".format(SEQUENCE))
    _write_sensor_files(sequence_path)


def _run_assertions(root: Path) -> None:
    import numpy as np
    import pykitti

    data = pykitti.odometry(str(root), SEQUENCE, frames=SELECTED_FRAMES)
    _check(len(data) == len(SELECTED_FRAMES), "selected timestamp length mismatch")
    _check(data.frames == SELECTED_FRAMES, "selected frame order was not retained")

    expected_times = [dt.timedelta(microseconds=100000 * frame) for frame in SELECTED_FRAMES]
    _check(data.timestamps == expected_times, "timestamp selection/order mismatch")

    _check(len(data.poses) == len(SELECTED_FRAMES), "pose selection length mismatch")
    for selected_position, original_frame in enumerate(SELECTED_FRAMES):
        pose = data.poses[selected_position]
        _check(pose.shape == (4, 4), "pose shape mismatch")
        _check(
            np.allclose(
                pose[:3, 3],
                [original_frame, original_frame + 0.5, original_frame + 1.0],
            ),
            "pose selection/order mismatch",
        )
        _check(np.allclose(pose[3], [0, 0, 0, 1]), "pose homogeneous row mismatch")

    calib = data.calib
    for field in ("P_rect_00", "P_rect_10", "P_rect_20", "P_rect_30"):
        _check(getattr(calib, field).shape == (3, 4), field + " shape mismatch")
    for field in ("K_cam0", "K_cam1", "K_cam2", "K_cam3"):
        _check(getattr(calib, field).shape == (3, 3), field + " shape mismatch")
    for field in ("T_cam0_velo", "T_cam1_velo", "T_cam2_velo", "T_cam3_velo"):
        _check(getattr(calib, field).shape == (4, 4), field + " shape mismatch")
    _check(np.allclose(calib.K_cam0, [[100, 0, 32], [0, 100, 24], [0, 0, 1]]), "intrinsic mismatch")
    _check(np.isclose(calib.T_cam1_velo[0, 3], -0.1), "gray transform mismatch")
    _check(np.isclose(calib.T_cam3_velo[0, 3], -0.3), "RGB transform mismatch")
    _check(np.isclose(calib.b_gray, 0.1), "gray baseline mismatch")
    _check(np.isclose(calib.b_rgb, 0.1), "RGB baseline mismatch")

    expected_sizes = [(4 + frame, 3 + frame) for frame in SELECTED_FRAMES]
    cam0 = list(data.cam0)
    cam1 = list(data.cam1)
    cam2 = list(data.cam2)
    cam3 = list(data.cam3)
    expected_pixels = {
        "cam0": [10 + frame for frame in SELECTED_FRAMES],
        "cam1": [20 + frame for frame in SELECTED_FRAMES],
        "cam2": [(30 + frame, 40 + frame, 50 + frame) for frame in SELECTED_FRAMES],
        "cam3": [(60 + frame, 70 + frame, 80 + frame) for frame in SELECTED_FRAMES],
    }
    for name, images, mode in (
        ("cam0", cam0, "L"),
        ("cam1", cam1, "L"),
        ("cam2", cam2, "RGB"),
        ("cam3", cam3, "RGB"),
    ):
        _check(len(images) == len(SELECTED_FRAMES), name + " generator length mismatch")
        _check([image.size for image in images] == expected_sizes, name + " size/order mismatch")
        _check(all(image.mode == mode for image in images), name + " mode mismatch")
        _check(
            [image.getpixel((0, 0)) for image in images] == expected_pixels[name],
            name + " content/order mismatch",
        )

    gray = list(data.gray)
    rgb = list(data.rgb)
    _check(len(gray) == len(SELECTED_FRAMES), "gray stereo length mismatch")
    _check(len(rgb) == len(SELECTED_FRAMES), "RGB stereo length mismatch")
    _check(all(left.mode == right.mode == "L" for left, right in gray), "gray stereo mode mismatch")
    _check(all(left.mode == right.mode == "RGB" for left, right in rgb), "RGB stereo mode mismatch")
    _check(data.get_gray(1)[0].size == expected_sizes[1], "indexed gray size mismatch")
    _check(data.get_rgb(1)[1].size == expected_sizes[1], "indexed RGB size mismatch")

    scans = list(data.velo)
    expected_shapes = [(frame + 2, 4) for frame in SELECTED_FRAMES]
    _check([scan.shape for scan in scans] == expected_shapes, "scan generator shape/order mismatch")
    _check(all(scan.dtype == np.float32 for scan in scans), "scan dtype mismatch")
    _check(data.get_velo(0).shape == expected_shapes[0], "indexed scan shape mismatch")

    pose_file = root / "poses" / "{}.txt".format(SEQUENCE)
    pose_file.unlink()
    # Missing poses are a supported no-ground-truth case.  Ignore the expected
    # warning text and assert the public state instead of matching stdout.
    with contextlib.redirect_stdout(io.StringIO()):
        no_poses = pykitti.odometry(str(root), SEQUENCE, frames=[0, 2])
    _check(no_poses.poses == [], "missing pose file did not produce empty poses")
    _write_pose_file(pose_file)


def run_smoke(keep: bool) -> Optional[Path]:
    if keep:
        root = Path(tempfile.mkdtemp(prefix="pykitti-odometry-fixture-"))
        try:
            _build_fixture(root)
            _run_assertions(root)
        except Exception:
            print("fixture retained at: {}".format(root))
            raise
        print("fixture retained at: {}".format(root))
        return root

    with tempfile.TemporaryDirectory(prefix="pykitti-odometry-fixture-") as directory:
        root = Path(directory)
        _build_fixture(root)
        _run_assertions(root)
    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a local-only pykitti.odometry fixture smoke test."
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="retain the temporary fixture instead of cleaning it up",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    run_smoke(keep=args.keep)
    print("odometry fixture smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
