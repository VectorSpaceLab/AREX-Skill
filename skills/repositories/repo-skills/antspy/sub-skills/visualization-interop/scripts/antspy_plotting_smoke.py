#!/usr/bin/env python3
"""Tiny ANTsPy visualization/interop smoke check.

Usage:
    python antspy_plotting_smoke.py
    python antspy_plotting_smoke.py --output-dir antspy-plot-smoke-output
    python antspy_plotting_smoke.py --keep-output --verbose

The script sets Matplotlib's Agg backend, creates tiny in-memory images, saves
PNG plots to a temporary directory by default, checks channel/RGB/vector round
trips, and verifies image-matrix mask ordering without GUI access or source
repository data.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny headless ANTsPy plotting and interop smoke check."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory for generated PNG files. Defaults to a temporary directory.",
    )
    parser.add_argument(
        "--keep-output",
        action="store_true",
        help="Keep the temporary output directory and print its path.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print generated files and selected image properties.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_output_dir(requested: Path | None) -> tuple[Path, bool]:
    if requested is None:
        return Path(tempfile.mkdtemp(prefix="antspy-plot-smoke-")), True
    requested.mkdir(parents=True, exist_ok=True)
    return requested, False


def assert_png(path: Path) -> None:
    require(path.exists(), f"missing output file: {path.name}")
    require(path.stat().st_size > 0, f"empty output file: {path.name}")


def main() -> int:
    args = parse_args()
    output_dir, is_temporary = make_output_dir(args.output_dir)

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
        import ants
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"Failed to import required plotting dependencies: {exc}", file=sys.stderr)
        if is_temporary and not args.keep_output:
            shutil.rmtree(output_dir, ignore_errors=True)
        return 2

    try:
        base_array = np.arange(64, dtype="float32").reshape(8, 8)
        base = ants.from_numpy(base_array, origin=(1.0, 2.0), spacing=(0.5, 0.75))
        overlay = ants.from_numpy(
            (base_array > base_array.mean()).astype("float32"),
            origin=base.origin,
            spacing=base.spacing,
            direction=base.direction,
        )
        require(
            ants.image_physical_space_consistency(base, overlay),
            "base and overlay should share physical space",
        )

        plot_path = output_dir / "plot.png"
        ants.plot(base, overlay=overlay, filename=str(plot_path), title="smoke", dpi=80)
        assert_png(plot_path)

        grid_path = output_dir / "grid.png"
        ants.plot_grid([[base, base + 1]], slices=None, filename=str(grid_path), colorbar=False, dpi=80)
        assert_png(grid_path)

        hist_path = output_dir / "hist.png"
        ants.plot_hist(base, title="histogram", threshold=0.0)
        plt.savefig(hist_path, dpi=80, bbox_inches="tight")
        plt.close()
        assert_png(hist_path)

        volume_array = np.stack([base_array, base_array + 1, base_array + 2], axis=-1)
        volume = ants.from_numpy(volume_array.astype("float32"), spacing=(0.5, 0.75, 1.25))
        ortho_path = output_dir / "ortho.png"
        ants.plot_ortho(volume, filename=str(ortho_path), xyz=(4, 4, 1), dpi=80, figsize=0.5)
        assert_png(ortho_path)

        red = ants.from_numpy(np.full((4, 5), 10, dtype="uint8"))
        green = ants.from_numpy(np.full((4, 5), 20, dtype="uint8"))
        blue = ants.from_numpy(np.full((4, 5), 30, dtype="uint8"))
        merged = ants.merge_channels([red, green, blue])
        split = ants.split_channels(merged)
        require(len(split) == 3, "split channel count mismatch")
        require(np.allclose(split[1].numpy(), green.numpy()), "split channel values changed")

        rgb_array = np.zeros((4, 5, 3), dtype="uint8")
        rgb_array[..., 0] = 255
        rgb = ants.from_numpy(rgb_array, is_rgb=True)
        vector = ants.rgb_to_vector(rgb)
        rgb_again = ants.vector_to_rgb(vector)
        require(rgb.components == 3, "RGB component count mismatch")
        require(vector.components == 3, "vector component count mismatch")
        require(rgb_again.is_rgb, "vector_to_rgb did not return RGB image")

        mask = ants.from_numpy(
            (base_array >= 20).astype("float32"),
            origin=base.origin,
            spacing=base.spacing,
            direction=base.direction,
        )
        matrix = ants.images_to_matrix([base, base + 2], mask=mask, epsilon=0.5)
        expected_voxels = int((mask.numpy() >= 0.5).sum())
        require(matrix.shape == (2, expected_voxels), f"unexpected matrix shape: {matrix.shape}")
        restored = ants.matrix_to_images(matrix, mask)
        require(len(restored) == 2, "matrix_to_images row count mismatch")
        require(
            ants.image_physical_space_consistency(restored[0], mask),
            "restored image does not match mask physical space",
        )
        require(
            np.allclose(restored[1][mask >= 0.5], (base + 2)[mask >= 0.5]),
            "matrix round trip did not preserve masked values",
        )

        sections = ants.ndimage_to_list(volume)
        require(len(sections) == volume.shape[-1], "ndimage_to_list section count mismatch")
        rebuilt = ants.list_to_ndimage(volume, sections)
        require(rebuilt.dimension == volume.dimension, "list_to_ndimage dimension mismatch")
        require(rebuilt.shape == volume.shape, "list_to_ndimage shape mismatch")

        generated = sorted(path.name for path in output_dir.glob("*.png"))
        if args.verbose:
            print(f"base: shape={base.shape} spacing={base.spacing} components={base.components}")
            print(f"volume: shape={volume.shape} spacing={volume.spacing}")
            print(f"matrix_shape={matrix.shape} generated={generated}")

        print(f"ANTsPy visualization smoke passed: {', '.join(generated)}")
        if args.keep_output or not is_temporary:
            print(f"output_dir={output_dir}")
        return 0
    except Exception as exc:
        print(f"ANTsPy visualization smoke failed: {exc}", file=sys.stderr)
        if args.keep_output or not is_temporary:
            print(f"output_dir={output_dir}", file=sys.stderr)
        return 1
    finally:
        if is_temporary and not args.keep_output:
            shutil.rmtree(output_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
