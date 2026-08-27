---
name: robot-model-import
description: "Load, inspect, validate, and troubleshoot IKPy robot models from
  URDF, MJCF, or IKPy JSON metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Robot model import

Use this sub-skill when a robot description must become an IKPy `Chain`, when
an imported chain has the wrong path or joint count, or when a URDF/MJCF parser
error needs diagnosis. Start with the smallest model inspection that answers
which links, joints, bodies, and path names are present.

- For loader signatures, path semantics, element-to-`URDFLink` mapping, and
  orientation conventions, read [api-reference.md](references/api-reference.md).
- For self-contained URDF/MJCF examples and smoke fixtures, read
  [workflows.md](references/workflows.md). The bundled
  `scripts/make_tiny_models.py` creates temporary examples without repository
  assets.
- For actionable parser and data failures, read
  [troubleshooting.md](references/troubleshooting.md).
- `python scripts/inspect_model.py --help` provides a no-write model inspection
  command. It reports source names and chain shape, and can optionally run FK.

The central distinction is structural: URDF has root-level `link` and `joint`
records traversed as an alternating path, while MJCF nests `body` records and
follows child bodies. IKPy represents each URDF/MJCF joint (or a fixed
body/explicit tip offset) as a `URDFLink`; the source URDF link records are not
chain links. Keep explicit `False` values in an `active_links_mask` for the
origin and fixed tip entries; do not rely on the constructor's last-entry
warning to repair a NumPy boolean mask. Pass a full joint vector, including
inactive entries.

Use `Chain.from_urdf_file` or `Chain.from_json_file` for URDF-backed models and
`Chain.from_mjcf_file` for MJCF. Use `ikpy.urdf.utils.get_urdf_tree` only for
optional structural inspection, and keep rendering concerns in
`visualization-geometry`. Route FK/IK method selection to `chain-kinematics`
and JAX execution to `jax-backend`.
