#!/usr/bin/env python3
"""Write MASt3R-SLAM config templates bundled with the skill.

Default behavior prints templates to stdout. Use --output-dir to write files.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
import textwrap

CONFIGS = {
    "base.yaml": """
use_calib: False
single_thread: False
dataset:
  subsample: 1
  img_downsample: 1
  center_principle_point: True

matching:
  max_iter: 10
  lambda_init: 1e-8
  convergence_thresh: 1e-6
  dist_thresh: 1e-1
  radius: 3
  dilation_max: 5

tracking:
  min_match_frac: 0.05
  max_iters: 50
  C_conf: 0.0
  Q_conf: 1.5
  rel_error: 1e-3
  delta_norm: 1e-3
  huber: 1.345
  match_frac_thresh: 0.333
  sigma_ray: 0.003
  sigma_dist: 1e+1
  sigma_pixel: 1.0
  sigma_depth: 1e+1
  sigma_point: 0.05
  pixel_border: -10
  depth_eps: 1e-6
  filtering_mode: weighted_pointmap
  filtering_score: median

local_opt:
  pin: 1
  window_size: 1e+6
  C_conf: 0.0
  Q_conf: 1.5
  min_match_frac: 0.1
  pixel_border: -10
  depth_eps: 1e-6
  max_iters: 10
  sigma_ray: 0.003
  sigma_dist: 1e+1
  sigma_pixel: 1.0
  sigma_depth: 1e+1
  sigma_point: 0.05
  delta_norm: 1e-8
  use_cuda: True

retrieval:
  k: 3
  min_thresh: 5e-3

reloc:
  min_match_frac: 0.3
  strict: True
""",
    "calib.yaml": """
inherit: "base.yaml"

use_calib: True
dataset:
  subsample: 2
""",
    "eval_calib.yaml": """
inherit: "base.yaml"

use_calib: True
single_thread: True
dataset:
  subsample: 2
""",
    "eval_no_calib.yaml": """
inherit: "base.yaml"

use_calib: False
single_thread: True
dataset:
  subsample: 2
""",
    "eth3d.yaml": """
inherit: "eval_calib.yaml"

dataset:
  subsample: 1
  center_principle_point: False

reloc:
  strict: False
""",
    "intrinsics.yaml": """
width: 640
height: 480
# With distortion (fx, fy, cx, cy, k1, k2, p1, p2, k3)
calibration: [517.3, 516.5, 318.6, 255.3, 0.2624, -0.9531, -0.0054, 0.0026, 1.1633]
# Without distortion, use only [fx, fy, cx, cy]
""",
}
CONFIGS = {name: textwrap.dedent(text).strip() + "\n" for name, text in CONFIGS.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=pathlib.Path, help="Directory to write selected templates.")
    parser.add_argument("--name", action="append", choices=sorted(CONFIGS), help="Template name to write/print; repeatable. Defaults to all.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files when writing to --output-dir.")
    parser.add_argument("--list", action="store_true", help="List bundled template names and exit.")
    args = parser.parse_args()

    if args.list:
        for name in sorted(CONFIGS):
            print(name)
        return 0

    names = args.name or sorted(CONFIGS)
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for name in names:
            target = args.output_dir / name
            if target.exists() and not args.overwrite:
                print(f"refusing to overwrite {target}; add --overwrite", file=sys.stderr)
                return 1
            target.write_text(CONFIGS[name], encoding="utf-8")
            print(f"wrote {target}")
    else:
        for name in names:
            print(f"# --- {name} ---")
            print(CONFIGS[name], end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
