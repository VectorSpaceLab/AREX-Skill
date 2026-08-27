# PyMJCF Reference

This reference covers programmatic MJCF construction, parsing, composition, validation, and export with the installed `dm_control` package.

## Core object model

Import PyMJCF through the top-level package:

```python
from dm_control import mjcf
```

A valid PyMJCF model starts with one root `<mujoco>` element:

```python
model = mjcf.RootElement(model="demo", model_dir="", assets=None)
```

`RootElement(model=None, model_dir='', assets=None)` creates an empty model. If `model` is omitted, PyMJCF uses an internal default name; set a meaningful model name before export because export helpers derive filenames from it.

`mjcf.Element` instances are created by adding children; user code should not instantiate a generic `Element` directly.

```python
world = model.worldbody
floor = world.add("geom", name="floor", type="plane", size=[1, 1, 0.05])
body = world.add("body", name="box", pos=[0, 0, 0.3])
slide = body.add("joint", name="slide_z", type="slide", axis=[0, 0, 1])
box = body.add("geom", name="box_geom", type="box", size=[0.05, 0.05, 0.05])
```

### Child and attribute access patterns

- Non-repeated children are exposed as attributes: `model.worldbody`, `model.asset`, `model.actuator`.
- Repeated children return a list/dict-like view: `body.geom[0]`, `body.geom['box_geom']`, `for geom in body.geom: ...`.
- Deep search is available with `find(namespace, identifier)` and `find_all(namespace)`.
- `find('joint', name)` includes specialized joint tags such as `<freejoint>`; `find('actuator', name)` includes actuator subtypes such as `<motor>`, `<position>`, and `<velocity>`.
- `find_all(namespace, immediate_children_only=True)` restricts to direct children. `find_all(namespace, exclude_attachments=True)` ignores attached child models.

Example:

```python
same_box = model.find("geom", "box_geom")
all_geoms = model.find_all("geom")
assert same_box is box
```

### XML keywords and keyword-like element names

Some MJCF names collide with Python syntax or keywords.

| XML concept | PyMJCF access |
|---|---|
| attribute `class="..."` | `element.dclass = "..."`; reading `element.dclass` |
| pass XML `class` in `add` | `parent.add("geom", dclass="red", ...)` |
| child element `<global>` under `<visual>` | `getattr(model.visual, "global")` |
| MuJoCo compiled visual global fields | `physics.model.vis.global_` |
| attributes `type` and `range` | normal Python attributes: `geom.type`, `joint.range` |

Do not write `element.class` or `model.visual.global`; those are Python syntax errors.

## Creating and modifying models

Attributes can be set during `add`, updated later, or removed with `del` when the schema allows removal.

```python
box.pos = [0.1, 0.0, 0.3]
box.rgba = [0.2, 0.4, 1.0, 1.0]
del box.rgba
```

PyMJCF validates against the MJCF schema:

- Unknown children or attributes raise `AttributeError`.
- Wrong vector lengths, invalid scalar types, invalid enum values, or deleting required attributes raise `ValueError`.
- Validation errors usually include the element and attribute involved; inspect the operation that most recently changed the model.

Defaults are represented explicitly in the object model. Default values do not appear as concrete attributes on elements unless those attributes were assigned on that element.

```python
red = model.default.add("default", dclass="red")
red.geom.rgba = [1, 0, 0, 1]
geom = model.worldbody.add("geom", name="g", type="sphere", size=[0.05], dclass="red")
assert geom.rgba is None  # default applies at compile/XML interpretation time
```

## Reference attributes

Reference attributes can be assigned either as strings or direct `mjcf.Element` objects. Prefer direct element references:

```python
joint = body.add("joint", name="hinge", type="hinge", axis=[0, 0, 1])
model.actuator.add("motor", name="hinge_motor", joint=joint, gear=[1])
```

Direct references are safer because they survive renames and are required for cross-model references after attachment. String references are not fully verified by PyMJCF at assignment time and cannot contain `/` for attached-model scoped names.

## Parsing existing MJCF

PyMJCF provides four public parser helpers:

```python
model = mjcf.from_xml_string(xml_string, model_dir="", resolve_references=True, assets=None)

with open("model.xml", "r", encoding="utf-8") as f:
    model = mjcf.from_file(f, model_dir="", resolve_references=True, assets=None)

model = mjcf.from_path("model.xml", resolve_references=True, assets=None)
model = mjcf.from_zip("model.zip", model_file="model.xml", resolve_references=True)
```

Parser options:

- `model_dir` prefixes relative asset filenames when parsing from a string or file handle.
- `assets` is a `{filename: bytes}` mapping searched before the filesystem. Use it for in-memory textures, meshes, includes, or exported assets.
- `resolve_references=True` resolves reference attributes to elements when possible.
- `escape_separators=True` can be used for input XML that already contains `/` in identifiers; without it, such identifiers can raise `ValueError` because `/` is PyMJCF's namespacing separator.
- `from_zip` selects the single XML file in a zip, or the `model_file` argument when multiple XML files exist, and loads non-XML entries as assets relative to the model directory in the archive.

After parsing, immediately run a small validation pass:

```python
assert isinstance(model, mjcf.RootElement)
print(len(model.find_all("body")), len(model.find_all("geom")))
physics = mjcf.Physics.from_mjcf_model(model)  # compile check
```

## Attaching and namespacing models

PyMJCF can attach one `RootElement` into another to build larger scenes while automatically namespacing duplicate child identifiers.

```python
parent = mjcf.RootElement(model="scene")
parent.worldbody.add("geom", name="ground", type="plane", size=[2, 2, 0.05])

child = mjcf.RootElement(model="arm")
arm_body = child.worldbody.add("body", name="link", pos=[0, 0, 0.2])
arm_body.add("joint", name="hinge", type="hinge", axis=[0, 1, 0])
arm_body.add("geom", name="link_geom", type="capsule", size=[0.03, 0.2])

frame = parent.attach(child)       # equivalent to parent.worldbody.attach(child)
frame.add("freejoint")             # only joints/inertials should be added to a frame
physics = mjcf.Physics.from_mjcf_model(parent)
```

A model can also be attached to a site; PyMJCF creates an attachment frame at the site's pose.

```python
site = parent.worldbody.add("site", name="mount", pos=[0.2, 0, 0.3], size=[1e-6] * 3)
frame = site.attach(child)
```

Important attachment behavior:

- `attach` returns the transparent attachment frame. Keep this returned object if you need to add a joint or inertial to the frame.
- The generated XML prefixes attached child names with the child model name, for example `arm/link_geom`.
- Elements of child models do not appear during normal traversal through the parent object tree. Use the child model reference, `parent.find('geom', 'arm/link_geom')`, `parent.enter_scope('arm')`, or `mjcf.traversal_utils.get_attachment_frame(child)` when you need attached elements.
- A `RootElement` can only be attached once. Use `copy.copy(child)` or `copy.deepcopy(child)` to create multiple instances.
- Attaching a model to itself, attaching a non-root element, or attaching a model already attached elsewhere raises an error.
- Conflicting explicit global options under `<compiler>`, `<option>`, `<size>`, or `<visual>` prevent attachment. Set shared global options consistently before attaching.
- Default classes are scoped automatically so a parent's defaults do not silently change an attached child.

## Identifier and namescope gotchas

PyMJCF enforces identifier uniqueness within each relevant namespace:

- Two geoms with the same `name` in the same model namespace are invalid.
- A body and a geom may share a name because they are different namespaces.
- Different actuator subtypes share the broader actuator namespace.
- Attached models receive scoped names, but that does not allow reusing the same child `RootElement` object twice.

When diagnosing a duplicate-name failure, inspect both the local repeated child view and global namespace:

```python
local_names = [g.name for g in body.geom]
global_geoms = [g.full_identifier for g in model.find_all("geom")]
```

For cross-model references, assign the target element itself before or after attachment rather than constructing a string with `/`.

## Exporting XML and assets

For in-memory compile or custom storage, combine `to_xml_string()` and `get_assets()`:

```python
xml = model.to_xml_string()
assets = model.get_assets()
from dm_control import mujoco
physics = mujoco.Physics.from_xml_string(xml, assets=assets)
```

For filesystem export, use the bundled helpers:

```python
mjcf.export_with_assets(model, out_dir="exported_model", out_file_name="demo.xml")
zip_path = mjcf.export_with_assets_as_zip(model, out_dir="exported_model", model_name="demo")
roundtrip = mjcf.from_zip(zip_path, model_file="demo.xml")
```

Export notes:

- `export_with_assets` writes an XML file plus every referenced asset into the target directory, creating the directory if needed. `out_file_name` must end in `.xml`; if omitted, it defaults to `<model.model>.xml`.
- `export_with_assets_as_zip` writes `<model_name>.zip` containing a directory named `<model_name>` with `<model_name>.xml` and assets. It returns the zip path.
- Set `model.model` or pass explicit names before export so filenames are deterministic.
- If assets came from memory, verify `model.get_assets()` has the expected keys before export.
- Always compile either the original model or a round-tripped exported model before relying on the exported file.

## Minimum validation checklist

Before handing off a custom model:

1. Check `find`/`find_all` can locate every body, joint, geom, actuator, site, camera, and sensor the downstream task will use.
2. Compile with `mjcf.Physics.from_mjcf_model(model)`.
3. Run `with physics.reset_context(): ...` for any initial state edits, then `physics.step()` at least once.
4. Inspect a named value such as `physics.named.data.geom_xpos['geom_name']` or bind PyMJCF elements with `physics.bind(element)`.
5. If assets are present, test `mujoco.Physics.from_xml_string(model.to_xml_string(), assets=model.get_assets())` or a zipped round trip.
6. Treat render validation separately from model validity; rendering may fail because of optional backend configuration even when the model is valid.
