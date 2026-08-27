---
name: "robomind-conversion"
description: "Guides RoboMIND benchmark and embodiment HDF5 trees into LeRobot
  datasets, including language annotations, image/depth decoding, configuration
  mapping, safe execution choices, and recovery of conversion failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# RoboMIND conversion

Use this route when a user needs to convert RoboMIND benchmark data stored as
per-embodiment HDF5 episode trees into local LeRobot datasets. It covers the
RoboMIND-specific directory contract, task language, state/action features,
RGB/depth decoding, embodiment selection, and safe execution planning.

This route does **not** run a conversion, create a Ray cluster, download data,
push to a Hub, or render simulation data while drafting or validating a plan.
It also does not cover AgiBot, LIBERO, RoboCasa, generic adapter execution, or
LeRobot version migration; route those requests to their owning sub-skills.

## Read before planning

- [Workflow and execution choices](references/workflows.md)
- [Input and output data formats](references/data-formats.md)
- [Embodiment and feature catalog](references/embodiments.md)
- [Troubleshooting and recovery](references/troubleshooting.md)

## Safety and applicability

- Accept a local, readable RoboMIND release root and a distinct local output
  root. Treat both paths as user data, not as disposable test fixtures.
- Require one of the three supported benchmark names and one or more of the
  eight physical embodiment names. The simulation labels in the configuration
  registry are intentionally not a supported CLI route.
- Validate the complete hierarchy, HDF5 keys, frame counts, image byte sizes,
  and language annotation coverage before scheduling any episode work.
- Prefer a single-task `--debug` smoke plan. The normal path initializes Ray and
  can schedule many tasks concurrently; never select it accidentally merely
  because Ray is installed.
- The converter removes an existing per-task output directory before writing.
  Require an explicit output inventory and approval before replacing anything.
- Keep depth optional and verify the installed LeRobot image-stat behavior for
  one-channel depth before a real run. Do not silently drop depth or reshape
  incompatible images to satisfy a declared feature shape.

## Route checklist

1. Freeze source root, benchmark, embodiment list, output root, depth choice,
   and desired split policy. Record the RoboMIND/LeRobot compatibility versions.
2. Check the release tree and the CSV/JSON annotation files described in
   [data formats](references/data-formats.md). Reject ambiguous task names
   instead of guessing an instruction.
3. Select the exact config for every embodiment and validate that all configured
   `puppet/*`, `master/*`, RGB, and optional depth datasets exist with aligned
   lengths. Use [embodiments](references/embodiments.md) for widths and shapes.
4. Decide debug versus Ray. Debug processes only the first discovered task for
   the first selected embodiment and avoids Ray; it is the baseline smoke path.
   Ray is an approved throughput option only after resource and cluster
   ownership are explicit.
5. Plan output and error logging. The implementation writes each task under
   `output/benchmark/embodiment/task` and appends Ray failures to `output.txt`
   in the process working directory; make that location intentional.
6. Convert only after a preflight report records skipped episodes, dirty-task
   decisions, annotation fallbacks, image decoding decisions, and output
   replacement approval.
7. Inspect `meta/info.json`, episode metadata, train/validation ranges, feature
   shapes, action metadata, frame counts, and logs before any downstream use or
   publication.

## RoboMIND-specific behavior

The resulting dataset uses v3-style metadata with `fps: 30`, a `robot_type`
matching the embodiment, dictionary-like `observation.states.*` and
`actions.*` features, and video/image features generated from the selected
config. Natural-language task text is attached to every frame. Episode-level
JSON responses are stored as `action_config` metadata when a matching
annotation exists; missing matches use a null-valued fallback and must be
reported.

RGB streams for `franka_1rgb`, `franka_3rgb`, `franka_fr3_dual`, and `ur_1rgb`
are decoded as BGR by the evidence workflow and must be converted to RGB. Other
embodiments are not given that conversion. A failed decode may use only the
known raw byte-size shape fallbacks; any other shape is a data error. The
published implementation also has a mutable top-camera 720x1280 ↔ 480x640
retry; treat that as a bounded, explicitly recorded fallback, not a general
repair mechanism. See [troubleshooting](references/troubleshooting.md).

## Verification boundary and handoff

Safe verification is limited to static link/config checks, CLI parser/help
inspection when imports are available, and a tiny synthetic directory/config
model that does not open real HDF5, encode video, write LeRobot data, start Ray,
or allocate large arrays. A difficult case must cover `franka_3rgb` BGR input,
malformed image shape, and the explicit shape fallback without launching Ray.

Handoff should include the selected benchmark and embodiments, source/output
roots, split and depth decisions, config and annotation validation, debug or
Ray mode, CPU/memory budget, skipped/dirty episodes, output replacement status,
metadata checks, log locations, and unresolved compatibility issues.

Evidence basis: the RoboMIND README, `robomind_h5.py`,
`robomind_uitls.py`, `lerobot_uitls.py`, and the eight embodiment configuration
modules. These artifacts are provenance only; this skill contains the distilled
contract and has no runtime dependency on the source checkout.
