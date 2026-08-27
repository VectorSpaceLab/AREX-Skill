# MJCF / MuJoCo Troubleshooting

Use this reference when model construction, parsing, attachment, export, compile, stepping, named access, or API-level rendering fails. First separate model validity from optional rendering: a model can be valid and step correctly even if the host lacks an OpenGL backend.

## Fast triage

1. Reproduce without rendering: build/parse, compile with `mjcf.Physics.from_mjcf_model` or `mujoco.Physics.from_xml_string`, reset, and step once.
2. Print or save `model.to_xml_string()` for the smallest failing model. Remove unrelated assets, cameras, sensors, and contacts until the failure is isolated.
3. Check schema-level PyMJCF errors before MuJoCo compile errors. PyMJCF catches invalid children/attributes and many invalid values early.
4. Validate names and references after attachment because generated identifiers are namespaced.
5. Only after non-rendering compile/step succeeds, debug `physics.render` backend settings.

## Common failure matrix

| Symptom | Likely cause | What to do |
|---|---|---|
| `AttributeError: '<x> is not a valid child of <y>'` | Adding an element under the wrong parent or using an XML tag not allowed by the MJCF schema. | Move the element to the schema-valid parent: geoms/joints/bodies under `worldbody` or `body`, actuators under `model.actuator`, assets under `model.asset`, contacts under `model.contact`. Use `find_all` to inspect existing structure. |
| `AttributeError: '<attr>' is not a valid attribute for <tag>` | Misspelled attribute, wrong element type, or Python keyword gotcha. | Use `dclass` for XML `class`; use `getattr(model.visual, 'global')` for `<visual><global>`; verify the attribute belongs to that MJCF tag. |
| `ValueError during assignment to attribute ...` | Wrong vector length, wrong dtype, invalid enum, invalid range, or deleting a required attribute. | Replace strings with numeric lists where required, check vector lengths (`pos` length 3, `quat` length 4, `size` depends on geom type), and do not delete required fields such as inertial mass. |
| Duplicate-name or identifier uniqueness error | Two elements share a name in the same namespace, often geoms, joints, actuators, defaults, cameras, or sensors. | Rename within the model before compile. Remember body and geom namespaces differ, but actuator subtypes share an actuator namespace. For repeated model instances, attach deep copies rather than reusing one `RootElement`. |
| `KeyError` from `body.geom['name']` or `physics.named...['name']` | The name does not exist in that local view or compiled namespace; attached names may be scoped. | Use `model.find_all('geom')`, inspect `element.full_identifier`, and after attachment try `parent.find('geom', 'child_model/geom_name')` or `physics.bind(original_element)`. |
| Reference compiles to missing object | A reference attribute was assigned as an unchecked string or points across attached models. | Assign the target `mjcf.Element` object directly: `actuator = model.actuator.add('motor', joint=joint_element)`. Avoid strings containing `/`; use direct references for cross-model references. |
| Parser rejects identifiers containing `/` | `/` is PyMJCF's attachment namespace separator. | Prefer renaming identifiers in the source XML. If preserving input names is required, parse with `escape_separators=True` and validate downstream names explicitly. |
| `from_zip` cannot find XML | Zip has no XML, multiple XML files without the selected `model_file`, or assets placed relative to the wrong model directory. | Pass `model_file='main.xml'` when the archive has multiple XML files. Keep assets relative to that XML's directory. Round-trip with `mjcf.from_zip(zip_path, model_file='...')`. |
| Asset file missing at compile/export | `model_dir` was omitted, assets dict keys do not match XML filenames, or export naming changed asset locations. | For in-memory parse, pass `assets={filename: bytes}`. For strings/file handles with file assets, set `model_dir`. For export, check `model.get_assets().keys()` and compile with `mujoco.Physics.from_xml_string(model.to_xml_string(), assets=model.get_assets())`. |
| Attach fails with “already attached elsewhere” | The same `RootElement` object was attached more than once. | Use `copy.copy(child_model)` or `copy.deepcopy(child_model)` for each instance, or construct a fresh child object. |
| Attach fails with “Cannot merge a model to itself” | Parent and child are the same model object. | Create a distinct child model. Do not attach a model to itself. |
| Attach fails with global option conflict | Child and parent explicitly set incompatible `<compiler>`, `<option>`, `<size>`, or `<visual>` global options. | Set shared global options consistently before attachment. Be especially careful with `compiler.angle` because an implicit default in one model may not flag every semantic mismatch. |
| Attachment frame refuses a child element | Attachment frames only allow joints and inertials as direct children. | Add geoms, sites, cameras, and sensors to the attached child model's `worldbody`; add only frame joints/inertials to the returned attachment frame. |
| MuJoCo compile `ValueError` after PyMJCF succeeds | The XML is schema-formed but physically invalid: missing inertial, invalid contact, bad actuator reference, bad mesh/texture, impossible joint settings, or unsupported compiler option. | Write the generated XML, reduce the model, verify asset keys, and compile the reduced XML. Check the error line/object name and map it back to `find`/`find_all` identifiers. |
| `physics.named.data...` shape surprise | Field dimensionality differs by object type or model dimensions; empty actuators produce shape `(0,)`. | Inspect `physics.model.nq`, `nv`, `nu`, `ngeom`, `nbody`, and the field shape. Guard zero-actuator models before setting controls. |
| `physics.step()` raises a physics/divergence error or produces NaNs | Unstable dynamics: large timestep, unrealistic masses/inertias, invalid initial penetration, excessive actuator gains, or bad controls. | Start from `reset_context`, apply zero control, reduce timestep/gains, add damping, avoid deep penetrations, check finite qpos/qvel after `forward()`, and increase complexity gradually. Do not hide divergence unless the downstream task explicitly tolerates it. |
| `physics.render` fails immediately | Optional rendering backend is missing or mismatched (`MUJOCO_GL`, display, EGL, OSMesa, GLFW). | Confirm non-rendering compile/step first. Then choose a backend and route detailed backend work to the rendering sibling skill. Headless hosts often need `MUJOCO_GL=egl` or `osmesa`; GLFW usually needs a display. |
| Render width/height/camera error | Requested image is larger than the offscreen buffer or the camera id/name is invalid. | In PyMJCF set `getattr(model.visual, 'global').offwidth` and `.offheight` before compile. After compile inspect `physics.model.vis.global_.offwidth`, `.offheight`, and `physics.model.ncam`. Use `camera_id=-1` for the free camera. |
| `depth`, `segmentation`, overlays, or render flags conflict | The render API forbids some option combinations. | Use exactly one of RGB/depth/segmentation. Do not use overlays with depth/segmentation. Do not use `render_flag_overrides` with depth/segmentation. |

## Debugging snippets

### Print model inventory

```python
for namespace in ["body", "joint", "geom", "actuator", "site", "camera"]:
    print(namespace, [e.full_identifier for e in model.find_all(namespace)])
```

### Compile from PyMJCF and from generated XML

```python
from dm_control import mjcf, mujoco

physics_a = mjcf.Physics.from_mjcf_model(model)
xml = model.to_xml_string()
assets = model.get_assets()
physics_b = mujoco.Physics.from_xml_string(xml, assets=assets)
```

If `physics_a` succeeds and `physics_b` fails, check that the XML string and asset mapping are the ones produced by the same `model` object.

### Validate finite state after reset/step

```python
import numpy as np

with physics.reset_context():
    pass
physics.step()
state = physics.get_state()
assert np.all(np.isfinite(state)), "MuJoCo state contains non-finite values"
```

### Safe control initialization

```python
from dm_control import mujoco
import numpy as np

spec = mujoco.action_spec(physics)
action = np.zeros(spec.shape, dtype=float)
if action.size:
    lo = np.where(np.isfinite(spec.minimum), spec.minimum, -1.0)
    hi = np.where(np.isfinite(spec.maximum), spec.maximum, 1.0)
    action = np.clip(action, lo, hi)
physics.set_control(action)
```

## When to route away

- If the user wants a reusable task/entity architecture, route to Composer rather than building a large ad hoc PyMJCF environment.
- If the user wants Control Suite domains, benchmarking, wrappers, or episode loops, route to the suite sub-skill.
- If the user is blocked by display servers, EGL/OSMesa/GLFW, pixel observations, viewer launchers, or Blender export, keep the model compile/step result here and route backend diagnosis to the rendering sub-skill.
