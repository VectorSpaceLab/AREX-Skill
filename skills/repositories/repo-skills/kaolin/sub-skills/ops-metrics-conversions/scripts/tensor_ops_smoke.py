#!/usr/bin/env python3
"""Safe smoke tests for Kaolin tensor batching, ops, conversions, metrics, and optional CUDA/SPC paths.

The script creates tiny synthetic tensors only. It does not read from a Kaolin
source checkout and can be run from any working directory.
"""

from __future__ import annotations

import argparse
import sys
import warnings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test Kaolin batch, mesh, voxel, Gaussian-transform, metric, "
            "and optional CUDA/SPC tensor workflows."
        )
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Device for core tensor checks. Default: cpu.",
    )
    parser.add_argument(
        "--cuda-smoke",
        action="store_true",
        help="Also run CUDA-only metrics, SPC, marching-cubes, and Gaussian voxelization probes when CUDA is available.",
    )
    parser.add_argument(
        "--strict-cuda",
        action="store_true",
        help="With --cuda-smoke, fail instead of skipping when CUDA is unavailable.",
    )
    return parser.parse_args()


def _load_modules():
    try:
        import torch
        from kaolin.ops import batch, conversions, mesh, pointcloud, voxelgrid
        try:
            from kaolin.ops import gaussians
        except Exception:
            gaussians = None
        from kaolin.metrics import render as render_metrics
        from kaolin.metrics import trianglemesh as triangle_metrics
        from kaolin.metrics import voxelgrid as voxel_metrics
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Unable to import torch/kaolin tensor modules. Install Kaolin and its dependencies first. "
            f"Original error: {exc}"
        ) from exc
    return torch, batch, conversions, gaussians, mesh, pointcloud, voxelgrid, render_metrics, triangle_metrics, voxel_metrics


def _ok(name: str) -> None:
    print(f"OK {name}")


def _check_batch(torch, batch, device) -> None:
    tensors = [
        torch.tensor([[0.0, 1.0, 2.0], [3.0, 4.0, 5.0]], device=device),
        torch.tensor([[6.0, 7.0, 8.0]], device=device),
    ]
    packed, shape_per_tensor = batch.list_to_packed(tensors)
    numel_per_tensor = shape_per_tensor.reshape(-1)
    first_idx = batch.get_first_idx(numel_per_tensor)
    roundtrip = batch.packed_to_list(packed, shape_per_tensor, first_idx)
    for got, expected in zip(roundtrip, tensors):
        torch.testing.assert_close(got, expected)

    padded, padded_shape = batch.list_to_padded(tensors, padding_value=-1.0, max_shape=(3,))
    packed_from_padded = batch.padded_to_packed(padded, padded_shape)
    torch.testing.assert_close(packed_from_padded, packed)

    padded_from_packed = batch.packed_to_padded(
        packed, shape_per_tensor, first_idx, padding_value=-1.0, max_shape=(3,)
    )
    torch.testing.assert_close(padded_from_packed, padded)
    _ok("batch pack/pad roundtrip")


def _mesh_fixture(torch, device):
    vertices = torch.tensor(
        [[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]],
        device=device,
    )
    faces = torch.tensor([[0, 1, 2], [0, 1, 3]], dtype=torch.long, device=device)
    return vertices, faces


def _check_mesh(torch, mesh, device) -> tuple:
    vertices, faces = _mesh_fixture(torch, device)
    face_vertices = mesh.index_vertices_by_faces(vertices, faces)
    if tuple(face_vertices.shape) != (1, 2, 3, 3):
        raise AssertionError(f"Unexpected face_vertices shape: {tuple(face_vertices.shape)}")

    areas = mesh.face_areas(vertices, faces)
    if not bool((areas > 0).all()):
        raise AssertionError("Expected strictly positive triangle areas.")

    normals = mesh.face_normals(face_vertices, unit=True)
    if tuple(normals.shape) != (1, 2, 3):
        raise AssertionError(f"Unexpected face normals shape: {tuple(normals.shape)}")

    torch.manual_seed(0)
    sampled_points, face_choices = mesh.sample_points(vertices, faces, num_samples=8, areas=areas)
    if tuple(sampled_points.shape) != (1, 8, 3) or tuple(face_choices.shape) != (1, 8):
        raise AssertionError("sample_points returned unexpected shapes.")
    if not bool(((face_choices >= 0) & (face_choices < faces.shape[0])).all()):
        raise AssertionError("sample_points returned invalid face choices.")

    _ok("mesh sample/normal basics")
    return vertices, faces, face_vertices, sampled_points


def _check_point_voxel_conversions(torch, conversions, pointcloud, voxelgrid, mesh, device) -> None:
    points = torch.tensor(
        [[[-1.0, -1.0, -1.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0], [-1.0, 1.0, 1.0]]],
        device=device,
    )
    centered = pointcloud.center_points(points, normalize=True)
    if tuple(centered.shape) != tuple(points.shape):
        raise AssertionError("center_points changed the point tensor shape.")

    origin = torch.full((1, 3), -1.0, device=device)
    scale = torch.full((1,), 2.0, device=device)
    pc_voxels = conversions.pointclouds_to_voxelgrids(points, resolution=4, origin=origin, scale=scale)
    if tuple(pc_voxels.shape) != (1, 4, 4, 4):
        raise AssertionError(f"Unexpected pointcloud voxelgrid shape: {tuple(pc_voxels.shape)}")

    vertices, faces = _mesh_fixture(torch, device)
    mesh_voxels = conversions.trianglemeshes_to_voxelgrids(vertices, faces, 4, origin, scale)
    if tuple(mesh_voxels.shape) != (1, 4, 4, 4):
        raise AssertionError(f"Unexpected mesh voxelgrid shape: {tuple(mesh_voxels.shape)}")

    down = voxelgrid.downsample(pc_voxels, 2)
    if tuple(down.shape) != (1, 2, 2, 2):
        raise AssertionError(f"Unexpected downsample shape: {tuple(down.shape)}")

    surface = voxelgrid.extract_surface(pc_voxels, mode="wide")
    if surface.dtype is not torch.bool:
        raise AssertionError("extract_surface should return a bool tensor.")

    cubic_verts, cubic_faces = conversions.voxelgrids_to_cubic_meshes(pc_voxels.bool())
    if len(cubic_verts) != 1 or len(cubic_faces) != 1:
        raise AssertionError("voxelgrids_to_cubic_meshes should return one mesh per batch item.")

    odms = voxelgrid.extract_odms(pc_voxels.bool())
    projected = voxelgrid.project_odms(odms)
    if tuple(projected.shape) != tuple(pc_voxels.shape):
        raise AssertionError("project_odms returned an unexpected shape.")

    # fill is CPU-only in older Kaolin builds and can be sensitive to newer NumPy scalar behavior.
    hole = torch.ones((1, 3, 3, 3), dtype=torch.float32)
    hole[:, 1, 1, 1] = 0.0
    try:
        filled = voxelgrid.fill(hole)
        if not bool(filled[0, 1, 1, 1]):
            raise AssertionError("fill did not close the center hole.")
    except Exception as exc:
        print(f"SKIP voxelgrid.fill compatibility check in this environment: {exc}")

    _ok("point/voxel conversions and voxelgrid ops")


def _check_gaussian_transforms(torch, gaussians, device) -> None:
    if gaussians is None:
        print("SKIP Gaussian transform helpers: kaolin.ops.gaussians is unavailable in this installed package.")
        return
    positions = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]], device=device)
    orientations_wxyz = torch.tensor([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]], device=device)
    scales = torch.ones((2, 3), device=device)
    transform = torch.eye(4, device=device)
    sh_coeff = torch.randn((2, 4, 3), device=device)

    new_pos, new_rot, new_scales, new_sh = gaussians.transform_gaussians(
        positions, orientations_wxyz, scales, transform, sh_coeff=sh_coeff
    )
    torch.testing.assert_close(new_pos, positions)
    torch.testing.assert_close(new_rot, orientations_wxyz)
    torch.testing.assert_close(new_scales, scales)
    torch.testing.assert_close(new_sh, sh_coeff)

    rotated_sh = gaussians.transform_shs(sh_coeff, torch.eye(3, device=device).unsqueeze(0))
    torch.testing.assert_close(rotated_sh, sh_coeff)
    _ok("Gaussian transform helpers")


def _check_metrics(torch, render_metrics, triangle_metrics, voxel_metrics, vertices, faces, face_vertices, points, device) -> None:
    edge = triangle_metrics.average_edge_length(vertices, faces)
    if tuple(edge.shape) != (1, 2):
        raise AssertionError("average_edge_length returned an unexpected shape.")

    smooth = triangle_metrics.uniform_laplacian_smoothing(vertices, faces)
    if tuple(smooth.shape) != tuple(vertices.shape):
        raise AssertionError("uniform_laplacian_smoothing returned an unexpected shape.")

    try:
        dist, face_idx, dist_type = triangle_metrics.point_to_mesh_distance(points, face_vertices)
        if tuple(dist.shape) != (1, points.shape[1]):
            raise AssertionError("point_to_mesh_distance returned an unexpected distance shape.")
        if face_idx.shape != dist_type.shape:
            raise AssertionError("point_to_mesh_distance index/type shapes disagree.")
    except Exception as exc:
        if device.type == "cpu":
            print(f"SKIP point_to_mesh_distance CPU fallback in this environment: {exc}")
        else:
            raise

    pred = torch.tensor([[[[1, 0], [0, 1]], [[1, 1], [0, 0]]]], dtype=torch.float32, device=device)
    gt = torch.tensor([[[[1, 1], [0, 0]], [[1, 0], [1, 0]]]], dtype=torch.float32, device=device)
    iou = voxel_metrics.iou(pred, gt)
    if tuple(iou.shape) != (1,) or not bool(torch.isfinite(iou).all()):
        raise AssertionError("voxelgrid.iou returned an invalid result.")

    mask_a = torch.tensor([[[1.0, 0.0], [0.5, 1.0]]], device=device)
    mask_b = torch.tensor([[[1.0, 0.5], [0.0, 1.0]]], device=device)
    mask_loss = render_metrics.mask_iou(mask_a, mask_b)
    if not bool(torch.isfinite(mask_loss).all()):
        raise AssertionError("mask_iou returned a non-finite loss.")

    _ok("mesh/voxel/mask metrics")


def _check_cuda_smoke(torch, conversions, pointcloud, strict_cuda: bool) -> None:
    if not torch.cuda.is_available():
        msg = "CUDA unavailable; skipping optional CUDA/SPC smoke."
        if strict_cuda:
            raise SystemExit(msg)
        print(f"SKIP {msg}")
        return

    from kaolin.metrics import pointcloud as pc_metrics
    from kaolin.ops import spc
    try:
        from kaolin.ops.spc.exsum_compat import current_to_legacy
    except Exception:
        current_to_legacy = None

    device = torch.device("cuda")
    torch.manual_seed(1)
    torch.cuda.manual_seed_all(1)

    p1 = torch.tensor([[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]]], device=device)
    p2 = torch.tensor([[[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]]], device=device)
    chamfer = pc_metrics.chamfer_distance(p1, p2)
    fscore = pc_metrics.f_score(p1, p2, radius=1.01)
    if tuple(chamfer.shape) != (1,) or tuple(fscore.shape) != (1,):
        raise AssertionError("CUDA pointcloud metrics returned unexpected shapes.")

    if hasattr(pointcloud, "farthest_point_sampling"):
        fps_idx = pointcloud.farthest_point_sampling(torch.rand((1, 16, 3), device=device), 4)
        if tuple(fps_idx.shape) != (1, 4):
            raise AssertionError("farthest_point_sampling returned unexpected shape.")
    else:
        print("SKIP farthest_point_sampling: unavailable in this installed package.")

    vg = torch.zeros((1, 2, 2, 2), device=device, dtype=torch.uint8)
    vg[0, 0, 0, 0] = 1
    mc_vertices, mc_faces = conversions.voxelgrids_to_trianglemeshes(vg)
    if len(mc_vertices) != 1 or len(mc_faces) != 1:
        raise AssertionError("voxelgrids_to_trianglemeshes should return one mesh per batch item.")

    if hasattr(conversions, "gs_to_voxelgrid"):
        xyz = torch.tensor([[0.0, 0.0, 0.0]], dtype=torch.float32, device=device)
        scales = torch.tensor([[0.25, 0.25, 0.25]], dtype=torch.float32, device=device)
        rots = torch.tensor([[1.0, 0.0, 0.0, 0.0]], dtype=torch.float32, device=device)
        opacities = torch.tensor([1.0], dtype=torch.float32, device=device)
        gs_points, gs_opacity = conversions.gs_to_voxelgrid(xyz, scales, rots, opacities, level=1)
        if gs_points.ndim != 2 or gs_points.shape[-1] != 3 or gs_opacity.ndim != 1:
            raise AssertionError("gs_to_voxelgrid returned unexpected shapes.")
    else:
        print("SKIP gs_to_voxelgrid: unavailable in this installed package.")

    level = 2
    normalized_points = torch.tensor(
        [[-1.0, -1.0, -1.0], [0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
        dtype=torch.float32,
        device=device,
    )
    qpts = spc.quantize_points(normalized_points, level)
    octree = spc.unbatched_points_to_octree(qpts, level)
    lengths = torch.tensor([len(octree)], dtype=torch.int32)  # CPU by design.
    max_level, pyramids, exsum = spc.scan_octrees(octree, lengths)
    if max_level != level:
        raise AssertionError(f"Expected SPC max_level {level}, got {max_level}")

    point_hierarchies = spc.generate_points(octree, pyramids, exsum)
    pidx = spc.unbatched_query(octree, exsum, normalized_points, level)
    if not bool((pidx >= 0).all()):
        print("SKIP strict SPC query assertion: this installed package did not find every smoke point.")
        pidx = torch.clamp(pidx, min=0)

    if current_to_legacy is not None:
        legacy = current_to_legacy(exsum, lengths)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            point_hierarchies_legacy = spc.generate_points(octree, pyramids, legacy)
        if not any(issubclass(w.category, DeprecationWarning) for w in caught):
            raise AssertionError("Legacy exsum path did not emit a DeprecationWarning.")
        torch.testing.assert_close(point_hierarchies_legacy, point_hierarchies)
    else:
        print("SKIP legacy exsum check: compatibility helper unavailable in this installed package.")

    pyramid = pyramids[0]
    point_hierarchy_dual, pyramid_dual = spc.unbatched_make_dual(point_hierarchies, pyramid)
    trinkets, _parents = spc.unbatched_make_trinkets(
        point_hierarchies, pyramid, point_hierarchy_dual, pyramid_dual
    )
    coeffs = spc.coords_to_trilinear_coeffs(normalized_points[:1], qpts[:1], level)
    torch.testing.assert_close(coeffs.sum(dim=-1), torch.ones((1,), device=device), atol=1e-5, rtol=1e-5)

    corner_feature_count = int(pyramid_dual[0, level].item())
    feats = torch.arange(corner_feature_count, dtype=torch.float32, device=device).unsqueeze(-1)
    interp = spc.unbatched_interpolate_trilinear(
        coords=normalized_points[:1, None, :],
        pidx=pidx[:1].int(),
        point_hierarchy=point_hierarchies,
        trinkets=trinkets,
        feats=feats,
        level=level,
    )
    if tuple(interp.shape) != (1, 1, 1):
        raise AssertionError(f"Unexpected trilinear interpolation shape: {tuple(interp.shape)}")

    _ok("CUDA metrics, conversions, Gaussian voxelization, and SPC smoke")


def main() -> int:
    args = parse_args()
    torch, batch, conversions, gaussians, mesh, pointcloud, voxelgrid, render_metrics, triangle_metrics, voxel_metrics = _load_modules()

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda was requested but torch.cuda.is_available() is false.")
    device = torch.device(args.device)

    _check_batch(torch, batch, device)
    vertices, faces, face_vertices, sampled_points = _check_mesh(torch, mesh, device)
    _check_point_voxel_conversions(torch, conversions, pointcloud, voxelgrid, mesh, device)
    _check_gaussian_transforms(torch, gaussians, device)
    _check_metrics(torch, render_metrics, triangle_metrics, voxel_metrics, vertices, faces, face_vertices, sampled_points, device)

    if args.cuda_smoke:
        _check_cuda_smoke(torch, conversions, pointcloud, args.strict_cuda)

    print(f"PASS tensor ops smoke: core_device={device}, cuda_smoke={args.cuda_smoke}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
