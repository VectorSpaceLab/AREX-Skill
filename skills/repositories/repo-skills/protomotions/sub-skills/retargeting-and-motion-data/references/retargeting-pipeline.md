# Retargeting pipeline

## Conceptual flow

For AMASS/SMPL to robot retargeting, the pipeline is:

```text
Packaged SMPL MotionLib (.pt)
  -> extract keypoints and source contacts
  -> PyRoki trajectory-level retargeting to G1 or H1_2
  -> convert retargeted root/joint trajectories to ProtoMotions .motion
  -> package .motion files into a robot MotionLib .pt
```

PyRoki performs trajectory-level optimization rather than frame-by-frame IK. It balances local/global alignment, root/joint smoothness, joint limits, velocity limits, foot contacts, and foot tilt. The documented pipeline trims/pads trajectories to a fixed horizon for efficient JAX compilation.

## Environments

Use two Python environments:

- ProtoMotions environment: loads MotionLib, extracts keypoints, converts/filters packaged motions, packages output.
- PyRoki environment: runs JAX/PyRoki batch retargeting and source-contact extraction.

Do not merge these environments unless dependency evidence proves compatibility.

## Main arguments to preserve

- `proto_python`: Python interpreter with ProtoMotions installed.
- `pyroki_python`: Python interpreter with PyRoki installed.
- input MotionLib or single `.motion` file.
- output directory.
- robot type: `g1` or `h1_2` for the evidence-backed PyRoki scripts.
- `skip_freq`: process every Nth motion for small smoke subsets.
- `--skip-existing`: resume interrupted retargeting.
- `--save-contacts-only`: generate contact labels from source motions.
- filter thresholds: min height, velocity, DOF velocity, and duration-height filters.

## Single-motion route

For a single SMPL `.motion`, extract keypoints, retarget to robot, extract source contacts, convert to robot `.motion`, then visualize or package. Single-motion retargeting is the safest first debug path before batch AMASS.

## Batch route

For a packaged AMASS MotionLib, first run with a high skip frequency such as 50 for a smoke subset. Once keypoints, PyRoki outputs, contacts, converted `.motion` files, and final MotionLib packaging succeed, rerun with `skip_freq=1` for full scale.

## Output layout

A typical batch output has separate directories for keypoints, PyRoki-retargeted trajectories, contacts, ProtoMotions `.motion` files, and final packaged `.pt` MotionLib. Keep these directories stable so interrupted runs can skip existing files.

## Verification

Before training on retargeted data:

1. summarize the final MotionLib fields and motion counts;
2. inspect a small subset for body-count/contact-length mismatches;
3. run a visualizer or headless simulator check only after the selected backend is verified;
4. use `subset_motion_lib.py` if GPU memory cannot load the full dataset.
