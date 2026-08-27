#!/usr/bin/env python3
"""Generate gaussian-splatting depth_params.json for depth regularization.

This is an adapted, self-contained version of the repository's depth-scale
utility. It reads a COLMAP model and monocular inverse-depth PNGs, estimates a
scale/offset per image, and writes <base-dir>/sparse/0/depth_params.json.
It does not download depth models or run COLMAP.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import cv2
import numpy as np
from joblib import Parallel, delayed

from read_write_model import qvec2rotmat, read_model


def get_scales(key, cameras, images, points3d_ordered, depths_dir: Path):
    image_meta = images[key]
    cam_intrinsic = cameras[image_meta.camera_id]
    pts_idx = image_meta.point3D_ids

    mask = pts_idx >= 0
    mask *= pts_idx < len(points3d_ordered)
    pts_idx = pts_idx[mask]
    valid_xys = image_meta.xys[mask]

    if len(pts_idx) > 0:
        pts = points3d_ordered[pts_idx]
    else:
        pts = np.array([0, 0, 0])

    R = qvec2rotmat(image_meta.qvec)
    pts = np.dot(pts, R.T) + image_meta.tvec
    inv_colmap_depth = 1.0 / pts[..., 2]

    n_remove = len(image_meta.name.split(".")[-1]) + 1
    image_stem = image_meta.name[:-n_remove]
    inv_mono = cv2.imread(str(depths_dir / f"{image_stem}.png"), cv2.IMREAD_UNCHANGED)
    if inv_mono is None:
        return None
    if inv_mono.ndim != 2:
        inv_mono = inv_mono[..., 0]
    inv_mono = inv_mono.astype(np.float32) / float(2**16)

    scale_to_depth = inv_mono.shape[0] / cam_intrinsic.height
    maps = (valid_xys * scale_to_depth).astype(np.float32)
    valid = (
        (maps[..., 0] >= 0)
        * (maps[..., 1] >= 0)
        * (maps[..., 0] < cam_intrinsic.width * scale_to_depth)
        * (maps[..., 1] < cam_intrinsic.height * scale_to_depth)
        * (inv_colmap_depth > 0)
    )

    if valid.sum() > 10 and (inv_colmap_depth.max() - inv_colmap_depth.min()) > 1e-3:
        maps = maps[valid, :]
        inv_colmap_depth = inv_colmap_depth[valid]
        inv_mono_depth = cv2.remap(
            inv_mono,
            maps[..., 0],
            maps[..., 1],
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )[..., 0]
        t_colmap = np.median(inv_colmap_depth)
        s_colmap = np.mean(np.abs(inv_colmap_depth - t_colmap))
        t_mono = np.median(inv_mono_depth)
        s_mono = np.mean(np.abs(inv_mono_depth - t_mono))
        scale = float(s_colmap / s_mono) if s_mono != 0 else 0.0
        offset = float(t_colmap - t_mono * scale)
    else:
        scale = 0.0
        offset = 0.0
    return {"image_name": image_stem, "scale": scale, "offset": offset}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create sparse/0/depth_params.json from COLMAP and inverse-depth PNGs")
    parser.add_argument("--base-dir", required=True, type=Path, help="COLMAP scene root containing sparse/0.")
    parser.add_argument("--depths-dir", required=True, type=Path, help="Directory containing per-image inverse-depth PNGs.")
    parser.add_argument("--model-type", default="bin", choices=["bin", "txt"], help="COLMAP model file extension under sparse/0.")
    parser.add_argument("--jobs", type=int, default=-1, help="Parallel jobs for per-image scale fitting (default: all cores).")
    args = parser.parse_args()

    base = args.base_dir.resolve()
    depths = args.depths_dir.resolve()
    model_dir = base / "sparse" / "0"
    if not model_dir.is_dir():
        parser.error(f"missing COLMAP model directory: {model_dir}")
    if not depths.is_dir():
        parser.error(f"missing depths directory: {depths}")

    cam_intrinsics, images_metas, points3d = read_model(str(model_dir), ext=f".{args.model_type}")
    if not images_metas:
        parser.error("COLMAP model contains no images")
    if not points3d:
        parser.error("COLMAP model contains no points3D; cannot estimate scale")

    pts_indices = np.array([points3d[key].id for key in points3d])
    pts_xyzs = np.array([points3d[key].xyz for key in points3d])
    points3d_ordered = np.zeros([pts_indices.max() + 1, 3])
    points3d_ordered[pts_indices] = pts_xyzs

    depth_param_list = Parallel(n_jobs=args.jobs, backend="threading")(
        delayed(get_scales)(key, cam_intrinsics, images_metas, points3d_ordered, depths) for key in images_metas
    )
    depth_params = {
        item["image_name"]: {"scale": item["scale"], "offset": item["offset"]}
        for item in depth_param_list
        if item is not None
    }
    out_path = model_dir / "depth_params.json"
    out_path.write_text(json.dumps(depth_params, indent=2) + "\n")
    print(f"Wrote {out_path} with {len(depth_params)} image entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
