# Blender MuJoCo exporter reference

The dm_control Blender exporter is an optional Blender add-on workflow, not a normal dm_control runtime dependency. Use this reference only when the user explicitly asks to export Blender-authored assets to MuJoCo/MJCF or to understand exporter limitations.

## What the exporter does

The exporter maps common Blender scene concepts into MuJoCo model concepts:

| Blender concept | MuJoCo/MJCF output idea |
|---|---|
| Armatures or object hierarchies | Kinematic body tree |
| IK constraints and bone limits | MuJoCo joints and joint ranges |
| Meshes | MuJoCo mesh-backed geoms |
| Materials and textures | MuJoCo material/texture definitions where supported |
| Lights | MuJoCo lights |

It was designed so artists can continue using standard Blender modeling workflows while producing a MuJoCo model draft. The resulting MJCF should still be treated as generated model source that needs physics validation.

## Runtime and installation cautions

- Blender is external software; `pip install dm_control` does not install a Blender runtime.
- The exporter is a Blender add-on workflow. It is not required for `physics.render`, Control Suite tasks, or dm_control viewers.
- The exporter README and the add-on preparation script named `install.sh` are reference-only guidance for this skill. The script prepares an add-on folder named like `addons/mujoco_model_exporter` by copying exporter Python files and rewriting imports. Treat this as a mutating build step, not a safe default runtime command.
- Installing a Blender add-on can modify a user's Blender add-on directories and preferences. Only proceed after explicit user consent.
- Work from disposable copies of `.blend` files and exporter output directories; do not run exporter preparation in a directory containing valuable untracked add-on work.
- If the user only needs to render or load an existing MJCF model, do not involve Blender; route to `physics.render` or the MJCF/MuJoCo model skill instead.

## Modeling behavior and limitations

### Kinematic trees and IK

Armatures can become the MuJoCo kinematic tree. IK constraints identify which bones should receive degrees of freedom. A model without IK chains can export as a static model. Bone limits are an important source of joint limit information.

Root armatures may receive a free joint by default. Disable the exporter option for an armature free joint if the root should be fixed.

### Geometry and meshes

The exporter writes mesh geometry for Blender meshes. Historical exporter output may use MuJoCo `.msh` mesh files, while modern MuJoCo also supports `.obj`. Treat any `.msh` output as a compatibility concern and convert or validate it when needed for a modern toolchain.

Meshes with multiple materials may be split into submeshes. This is visually useful but can change convex hulls, mass, and inertia compared with the original mesh.

### Materials and textures

MuJoCo's renderer uses a fixed material model. Blender materials based on simple diffuse/specular/smoothness/reflectance concepts are safer than complex Cycles node graphs. Texture assets may require manual copying or packaging next to the exported model.

### Double-sided materials and scaling

Double-sided materials can duplicate faces with reverse winding. This can affect physical properties such as mass and inertia because geometry changes.

Scaling transforms are especially risky: the exporter may reset scaling transforms on bones and meshes to ensure affine frames. This modifies the Blender scene and is not automatically undone. Use a disposable copy before exporting.

## When to avoid the exporter

Avoid or postpone Blender exporter work when:

- The user does not have Blender installed or cannot run Blender interactively/batch-mode.
- The task is only to render, probe OpenGL backends, use the viewer, or collect pixel observations.
- The model's physical fidelity, mass/inertia, or collision hulls are critical and cannot be manually reviewed.
- The asset uses complex Cycles materials, procedural texture nodes, multi-material meshes where mass/inertia must be exact, or unreviewed scaling transforms.
- The environment is headless/CI and the user has not explicitly approved Blender installation or add-on mutation.

## Safe documentation-only workflow

1. Confirm the user has Blender and accepts add-on installation/mutation risks.
2. Make disposable copies of the `.blend` file and intended export directory.
3. Prepare the add-on outside valuable Blender add-on directories, then install through Blender's add-on UI or an explicit user-approved Blender add-on path.
4. Export a small representative model first.
5. Validate the exported MJCF by loading it with dm_control/MuJoCo, checking model warnings, stepping the physics, and rendering a small offscreen frame if a rendering backend is available.
6. Route model-editing or MJCF validation details to `../mjcf-mujoco-models/SKILL.md`; route backend/render failures back to this sub-skill's troubleshooting reference.

## Minimal validation after export

After the user provides an exported MJCF file in their own workspace, validate with installed dm_control in a normal Python process:

```python
from dm_control import mujoco

physics = mujoco.Physics.from_xml_path("exported_model.xml")
physics.step()
print(physics.model.nbody, physics.model.ngeom)
```

If the model uses external mesh/texture assets, ensure the MJCF and assets are located exactly as referenced by the XML before loading.
