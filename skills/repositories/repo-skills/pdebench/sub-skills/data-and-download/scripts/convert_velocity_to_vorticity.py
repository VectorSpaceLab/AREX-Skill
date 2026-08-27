#!/usr/bin/env python3
"""Safely convert a local 3-D CFD velocity HDF5 file to vorticity."""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import Callable

import h5py
import numpy as np


class ConversionError(ValueError):
    """A user-fixable input, schema, spacing, or output error."""


def _get_dataset(handle: h5py.File, name: str) -> h5py.Dataset:
    if name not in handle or not isinstance(handle[name], h5py.Dataset):
        raise ConversionError(f"required root dataset is missing: {name}")
    return handle[name]


def _coordinate(
    handle: h5py.File, name: str, expected_length: int
) -> tuple[np.ndarray, float]:
    dataset = _get_dataset(handle, name)
    values = np.asarray(dataset[:])
    if not np.issubdtype(values.dtype, np.number):
        raise ConversionError(f"{name} must contain numeric coordinates")
    if values.ndim != 1 or values.shape[0] != expected_length:
        raise ConversionError(
            f"{name} must be 1-D with length {expected_length}; got {values.shape}"
        )
    if not np.all(np.isfinite(values)):
        raise ConversionError(f"{name} contains non-finite values")
    if values.shape[0] < 2:
        raise ConversionError(f"{name} needs at least two coordinates")
    differences = np.diff(values.astype(np.float64))
    if not (np.all(differences > 0) or np.all(differences < 0)):
        raise ConversionError(f"{name} must be strictly monotone")
    spacing_values = np.abs(differences)
    spacing = float(spacing_values.mean())
    tolerance = max(1e-12, spacing * 1e-6)
    if not np.allclose(spacing_values, spacing, rtol=1e-5, atol=tolerance):
        raise ConversionError(
            f"{name} is not uniformly spaced; spectral conversion requires an "
            "equidistant grid"
        )
    if not np.isfinite(spacing) or spacing == 0.0:
        raise ConversionError(f"{name} produced an invalid spacing: {spacing}")
    return values, spacing


def _load_api(backend: str) -> tuple[Callable[..., object], Callable[[np.ndarray], object] | None]:
    """Load a public package API without depending on the source checkout cwd."""
    try:
        from pdebench.data_gen.src.vorticity import compute_spectral_vorticity_np
    except ImportError as exc:  # pragma: no cover - depends on caller environment
        raise ImportError(
            "pdebench is not importable; install pdebench before converting "
            "or use the source package's verified environment"
        ) from exc

    if backend == "numpy":
        return compute_spectral_vorticity_np, None

    try:
        import jax.numpy as jnp
        from pdebench.data_gen.src.vorticity import compute_spectral_vorticity_jnp
    except ImportError as exc:  # pragma: no cover - depends on optional dependency
        raise ImportError(
            "JAX backend requested but JAX or the public JAX vorticity API is "
            "not installed; retry with --backend numpy or install CPU JAX"
        ) from exc
    return compute_spectral_vorticity_jnp, jnp.asarray


def _output_path(input_path: Path, requested: Path | None) -> Path:
    if requested is not None:
        return requested
    return input_path.with_name(f"{input_path.stem}_vorticity.hdf5")


def convert(
    input_path: Path,
    output_path: Path,
    backend: str,
    overwrite: bool,
) -> tuple[Path, tuple[float, float, float]]:
    if not input_path.is_file():
        raise FileNotFoundError(f"input HDF5 file does not exist: {input_path}")
    input_resolved = input_path.resolve()
    output_resolved = output_path.resolve()
    if input_resolved == output_resolved:
        raise ConversionError("input and output must be different files")
    if output_path.exists() and not overwrite:
        raise FileExistsError(
            f"output already exists: {output_path}; choose another --output or add --overwrite"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    vorticity_function, to_backend = _load_api(backend)
    temporary_name: str | None = None
    try:
        with h5py.File(input_path, "r") as source:
            vx = _get_dataset(source, "Vx")
            vy = _get_dataset(source, "Vy")
            vz = _get_dataset(source, "Vz")
            if vx.shape != vy.shape or vx.shape != vz.shape:
                raise ConversionError(
                    f"Vx, Vy, and Vz must have equal shapes; got {vx.shape}, "
                    f"{vy.shape}, and {vz.shape}"
                )
            if len(vx.shape) != 5:
                raise ConversionError(
                    "Vx, Vy, and Vz must have shape [trial,time,x,y,z]; "
                    f"got rank {len(vx.shape)} and shape {vx.shape}"
                )
            trials, time, nx, ny, nz = vx.shape
            if not all(np.issubdtype(dataset.dtype, np.number) for dataset in (vx, vy, vz)):
                raise ConversionError("Vx, Vy, and Vz must contain numeric data")
            t_coordinate = _get_dataset(source, "t-coordinate")
            t_values = np.asarray(t_coordinate[:])
            if not np.issubdtype(t_values.dtype, np.number):
                raise ConversionError("t-coordinate must contain numeric values")
            if t_coordinate.ndim != 1 or t_coordinate.shape[0] != time:
                raise ConversionError(
                    f"t-coordinate must have shape ({time},); got {t_coordinate.shape}"
                )
            if not np.all(np.isfinite(t_values)):
                raise ConversionError("t-coordinate contains non-finite values")
            x_coordinate, dx = _coordinate(source, "x-coordinate", nx)
            y_coordinate, dy = _coordinate(source, "y-coordinate", ny)
            z_coordinate, dz = _coordinate(source, "z-coordinate", nz)

            output_dtype = np.result_type(vx.dtype, vy.dtype, vz.dtype, np.float32)
            with tempfile.NamedTemporaryFile(
                prefix=f".{output_path.name}.",
                suffix=".partial",
                dir=output_path.parent,
                delete=False,
            ) as temporary:
                temporary_name = temporary.name

            with h5py.File(temporary_name, "w") as destination:
                for component in ("omega_x", "omega_y", "omega_z"):
                    destination.create_dataset(
                        component, shape=vx.shape, dtype=output_dtype
                    )
                destination.create_dataset("t-coordinate", data=t_coordinate[:])
                destination.create_dataset("x-coordinate", data=x_coordinate)
                destination.create_dataset("y-coordinate", data=y_coordinate)
                destination.create_dataset("z-coordinate", data=z_coordinate)
                destination.attrs["source_file"] = input_path.name
                destination.attrs["backend"] = backend
                destination.attrs["dx"] = dx
                destination.attrs["dy"] = dy
                destination.attrs["dz"] = dz
                destination.attrs["vorticity_convention"] = (
                    "omega_x=dVz/dy-dVy/dz; omega_y=dVx/dz-dVz/dx; "
                    "omega_z=dVy/dx-dVx/dy"
                )

                for trial in range(trials):
                    velocity = np.stack(
                        [vx[trial, :], vy[trial, :], vz[trial, :]], axis=-1
                    )
                    if to_backend is not None:
                        velocity_for_api = to_backend(velocity)
                    else:
                        velocity_for_api = velocity
                    result = np.asarray(
                        vorticity_function(velocity_for_api, dx, dy, dz)
                    )
                    if result.shape != (time, nx, ny, nz, 3):
                        raise ConversionError(
                            "vorticity API returned an unexpected shape: "
                            f"{result.shape}; expected {(time, nx, ny, nz, 3)}"
                        )
                    destination["omega_x"][trial, :] = result[..., 0]
                    destination["omega_y"][trial, :] = result[..., 1]
                    destination["omega_z"][trial, :] = result[..., 2]

        os.replace(temporary_name, output_path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except FileNotFoundError:
                pass
    return output_path, (dx, dy, dz)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert local PDEBench 3-D CFD Vx/Vy/Vz fields to omega_x/omega_y/omega_z. "
            "No download or upload is performed."
        )
    )
    parser.add_argument("--input", "-d", required=True, type=Path, help="input HDF5 file")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="output HDF5 path (default: <input-stem>_vorticity.hdf5)",
    )
    parser.add_argument(
        "--backend",
        choices=("numpy", "jax"),
        default="numpy",
        help="spectral API backend; NumPy/CPU is the safe default",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="replace an existing output after explicit confirmation by this flag",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        output, spacing = convert(
            args.input,
            _output_path(args.input, args.output),
            args.backend,
            args.overwrite,
        )
    except (
        ConversionError,
        FileExistsError,
        FileNotFoundError,
        ImportError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        f"CONVERTED: {output} backend={args.backend} "
        f"dx={spacing[0]:.12g} dy={spacing[1]:.12g} dz={spacing[2]:.12g}"
    )
    print("OUTPUT DATASETS: omega_x, omega_y, omega_z, t-coordinate, x-coordinate, y-coordinate, z-coordinate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
