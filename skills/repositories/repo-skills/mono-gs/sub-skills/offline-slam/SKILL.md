---
name: offline-slam
description: "Run MonoGS offline SLAM on monocular TUM, RGB-D TUM/Replica, and
  stereo EuRoC configs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Offline SLAM

Use this sub-skill to construct and sanity-check MonoGS offline SLAM runs with
`python slam.py --config ...` for:

- monocular TUM RGB-D sequences used as monocular input;
- RGB-D TUM and RGB-D Replica sequences;
- stereo EuRoC MH02-style sequences.

This sub-skill owns command construction, GUI/headless choices, multiprocessing
and `single_thread` behavior, sensor-specific config choice, runtime output
expectations, and the core APIs that drive a SLAM run.

## Route away

- Dataset download, full data-layout validation, or YAML editing beyond picking
  a known offline config: use the sibling `data-and-configs` sub-skill.
- Metric definitions, result aggregation, W&B policy, or rendering/ATE analysis:
  use the sibling `evaluation-and-results` sub-skill.
- Intel RealSense camera, USB/device permissions, or live monocular/RGB-D demo:
  use the sibling `live-demo` sub-skill.

## Fast path

1. Ensure the MonoGS runtime environment has CUDA PyTorch and the two CUDA
   extensions available; offline SLAM has no CPU-only substitute.
2. Choose the offline config family:
   - monocular TUM: `configs/mono/tum/<sequence>.yaml`;
   - RGB-D TUM: `configs/rgbd/tum/<sequence>.yaml`;
   - RGB-D Replica: `configs/rgbd/replica/<scene>.yaml` or `<scene>_sp.yaml`;
   - stereo EuRoC: `configs/stereo/euroc/mh02.yaml`.
3. Decide whether this is an interactive GUI run or a headless/evaluation run.
   The real `slam.py` CLI supports only `--config` and optional `--eval`; there
   is no runtime `--headless` flag.
4. Use `scripts/plan_slam_run.py` to print a safe command and warnings before
   launching a long run:

   ```bash
   python scripts/plan_slam_run.py --repo-root <mono-gs-repo> \
     --config configs/mono/tum/fr3_office.yaml --check-files
   ```

5. Run the suggested command from the MonoGS repository root only after any data,
   display, or backend warnings are resolved.

## Bundled references

- `references/workflows.md` — command matrix, GUI/headless choices,
  multiprocessing/`single_thread` notes, sensor-specific considerations, and
  expected output tree.
- `references/api-reference.md` — distilled CLI, config, class, renderer,
  dataset, and Gaussian-model facts used by offline SLAM.
- `references/troubleshooting.md` — workflow-specific failure modes and safe
  mitigations.
- `scripts/plan_slam_run.py` — read-only planner; it never starts SLAM, downloads
  data, edits configs, or imports repository runtime modules.
