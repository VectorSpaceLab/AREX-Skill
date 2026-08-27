#!/usr/bin/env python3
"""CPU-safe Kaolin camera, ray, and lighting smoke check.

Example:
  python camera_smoke.py --json
"""

from __future__ import annotations

import argparse
import json


def run() -> dict:
    import torch
    from kaolin.render.easy_render import default_camera, default_lighting
    from kaolin.render.camera.raygen import generate_pinhole_rays

    camera = default_camera(resolution=8)
    lighting = default_lighting()
    rays_o, rays_d = generate_pinhole_rays(camera)
    return {
        "ok": bool(rays_o.shape[-1] == 3 and rays_d.shape[-1] == 3),
        "camera_device": str(camera.device),
        "rays_origin_shape": list(rays_o.shape),
        "rays_direction_shape": list(rays_d.shape),
        "lighting_type": type(lighting).__name__,
        "direction_norm_mean": float(torch.linalg.norm(rays_d.reshape(-1, 3), dim=-1).mean().item()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a CPU-safe Kaolin camera/ray smoke check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()
    try:
        report = run()
    except Exception as exc:  # pragma: no cover
        report = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report)
    return 0 if report.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
