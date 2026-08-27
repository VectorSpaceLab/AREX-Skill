# Serialization and advanced troubleshooting

Use the error class and the failing boundary to avoid treating an optional
integration problem as a core GemPy failure.

## Failure matrix

| Symptom | Likely boundary | Check / recovery |
|---|---|---|
| `ValueError: Invalid file extension` | `.gempy` path contract | Use a path ending in `.gempy`; a suffix-less save path is auto-appended, load is not |
| `FileNotFoundError` on load | local artifact | Check the caller-owned path and preserve the original file; no network fetch is implicit |
| development warning from save/load | current implementation status | Continue only after the built-in validation and an explicit post-load comparison pass |
| archive validation assertion | native round-trip | Compare table bytes, group order, fault matrix, and grid; do not publish the archive |
| `json.JSONDecodeError` | malformed JSON text | Parse the file, report line/column, repair a copy; do not execute content |
| `Missing required key: ...` | `JsonIO` top-level schema | Add `surface_points`, `orientations`, or `grid_settings` as indicated |
| `Missing required key in surface point/orientation` | `JsonIO` row schema | Add required coordinates/gradients; preserve numeric types |
| `Invalid polarity in orientation` | `JsonIO` row semantics | Use integer `1` or `-1`; polarity -1 flips loaded gradients |
| `Grid settings ...` / interpolation type `ValueError` | `JsonIO` schema | Check resolution/extent containers and numeric kernel options |
| Pydantic `ValidationError` | model header/type schema | Inspect `loc`, enum names, and field types; this is distinct from `ModelValidationError` |
| `ModelValidationError: empty_model` | semantic validation | Add surface points/orientations before compute |
| `empty_fault_group` or `empty_non_fault_group` | semantic structural frame | Remove empty group or add its elements; do not bypass casually |
| `underdetermined_input` | insufficient data | Add more than one point or at least one orientation, then recompute |
| `basement_relation_on_non_last_group` | group order | Move the `BASEMENT` group to the final position |
| compute after load fails but load succeeds | restored model state | Call `.validate()`, inspect active grid, structural relations, interpolation options, then compute |
| `Model solutions must contain dense grid data` | mesh precondition | Recompute with a dense regular grid and verify solution block type |
| `No interpolation outputs available for mesh extraction` | mesh precondition | Ensure compute produced interpolation outputs; reduce grid size while debugging |
| `No module named skimage` | optional mesh dependency | Install a compatible `scikit-image` in the environment; do not edit the archive |
| `No module named gempy_plugins` | optional plugin | Install/version-match the separate plugin only if topology/property is required |
| GSTools import/configuration failure | optional property path | Test plugin and GSTools independently; record seed/configuration |
| `The subsurface package is required ...` | optional Subsurface | Install/verify `subsurface`; core model and persistence remain independent |
| PyVista/display failure | optional visualization | Run headless/no-display core checks and route plots to viewer/environment diagnostics |
| `gempy_legacy` import failure | optional migration | Install a compatible legacy package or omit migration; do not label core failure |
| Torch/CUDA backend failure | optional accelerator | Reproduce with NumPy CPU first; inspect torch/device/dtype under environment route |
| gravity shape/numeric failure | centered geophysics | Verify centers `N x 3`, resolution/radius, `tz`, density order/length, and units |
| process is slow or memory-heavy | expensive grid/plugin | Use one center, small dense resolution, no plotting, and a fixed seed; record limitation |

## Minimal diagnostics

Run the bundled helper first for core persistence:

From the generated GemPy skill root, run:

```bash
python sub-skills/serialization-and-advanced/scripts/json_roundtrip_smoke.py
```

Then use a caller-provided model, not source checkout data:

```python
import importlib.util
import numpy as np
import gempy as gp

print("GemPy:", gp.__version__)
print("points/orientations:",
      len(model.surface_points_copy.xyz), len(model.orientations_copy.xyz))
print("groups:", [g.name for g in model.structural_frame.structural_groups])
print("fault matrix:", np.asarray(model.structural_frame.fault_relations).shape)
model.validate()
for name in ("gempy_plugins", "subsurface", "torch", "pyvista", "skimage", "gempy_legacy"):
    print(name, bool(importlib.util.find_spec(name)))
```

Do not import optional modules merely to decide that a core `.gempy` archive is
invalid. Probe the optional module only when that capability is requested.

## Cross-skill handoff

- If the model cannot be built or mapped, return to
  [modeling](../../modeling/SKILL.md).
- If the failure is a point/orientation/table or structural-frame mutation,
  return to [data-and-structure](../../data-and-structure/SKILL.md).
- If it is an ordinary active-grid, section, topography, or plotting issue,
  return to [grids-and-visualization](../../grids-and-visualization/SKILL.md).
- If it is package installation, import, backend, GPU, or viewer setup, use
  [environment-and-troubleshooting](../../environment-and-troubleshooting/SKILL.md).

Keep these boundaries in the incident record: requested capability, core/optional
classification, exact exception, model artifact status, and next safe action.
