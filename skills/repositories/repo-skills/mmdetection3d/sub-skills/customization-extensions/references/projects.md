# Project Extensions

`projects/` is the escape hatch for optional code that is useful to the ecosystem but not ready to
move into the core package. This sub-skill should keep project guidance separate from core-package
customization so that a user can choose the lightest viable path.

## 1) When to use a project package

Use a project package when:

- the module is specific to one paper or one model family;
- the code needs extra dependencies or optional compilation steps;
- the extension should stay isolated from the core package;
- the config should import the package rather than move the file into `mmdet3d`.

Keep the module in the project package and register it into the normal MMDetection3D registries.
That keeps the runtime behavior consistent while avoiding unnecessary core changes.

## 2) Typical project layout

A project usually contains:

- a `README.md` with usage and dependency notes;
- a `configs/` directory with project configs;
- a Python package with the actual registrable classes;
- optional `setup.py` or extension build helpers when custom ops are needed.

Example shape:

```text
projects/MyProject/
  README.md
  configs/
  my_project/
    __init__.py
    model.py
    transforms.py
    losses.py
```

The package root should import the public symbols that the configs need.

## 3) Import pattern

Project configs commonly use `custom_imports`:

```python
custom_imports = dict(imports=['projects.my_project'], allow_failed_imports=False)
```

That pattern is enough when the project package is already on the Python path.
The important part is that the imported module actually defines the registered classes and exposes
those classes through the package import tree.

The small example project in this repository follows this pattern: a minimal wrapper class is
registered, then the config swaps the backbone type and imports the project package.

## 4) Project families in this repository

| Project | Common extension style | Extra considerations |
| --- | --- | --- |
| `example_project` | Minimal wrapper and config override demo | Useful as a pattern for custom imports and registry exposure |
| `BEVFusion` | Multi-sensor model, custom loaders, transforms, fusion modules, and custom setup | Has an optional compile path for the original voxelization op |
| `DSVT` | Sparse voxel transformer, custom filters, heads, utilities, and setup build | Uses extra runtime deps such as `torch_scatter` and a compiled CUDA op |
| `DETR3D` | Multi-view image detector pieces, transformer and coder modules | The project README calls out a tighter external dependency window |
| `CENet` | Range-view transforms, backbone, and losses | Shows how project-local transforms stay registrable |
| `CenterFormer` | Project-specific backbone, head, and loss code | Good example of custom `MODELS` usage |
| `NeRF-Det` | Multiview pipelines, loaders, data preprocessors, and heads | Demonstrates how a project can own both transforms and model code |
| `PETR` | Transformer blocks, positional encoding, data transforms, and heads | Mixes `MODELS` and `TRANSFORMS` registrations |
| `TPVFormer` | Project-specific encoders, heads, datasets, and preprocessors | Good example of using multiple registries in one project |
| `TR3D` | Sparse backbones, heads, coders, and losses | Another example of keeping task utilities inside a project package |

## 5) Optional dependency cues

Project code may require one or more of these:

- a project-local `setup.py` build step;
- a CUDA extension compiled in-place;
- an extra Python package such as `torch_scatter`;
- a specific upstream dependency window.

Do not assume that every project extension is installed.
If the user only wants to use a single project family, keep the guidance scoped to that package and do
not suggest installing unrelated project extras.

### Examples of project-specific build notes

- Some BEVFusion setups need the project build step when the original voxelization op is desired.
- DSVT commonly needs its custom compiled op and the extra sparse-operator dependency.
- DETR3D-style projects may depend on a specific external package version range.

These are project-specific, not core-package requirements.

## 6) What to tell the user

When a request touches a project package, answer these questions first:

1. Does the user want the project to stay external or move into the core package?
2. Does the project need custom Python-only code or compiled extras?
3. Can the extension be imported via `custom_imports` without changing the core package?
4. Is the current environment ready for the project's optional dependencies?

If the answer to any of those is uncertain, keep the project guidance reference-only and route the
implementation to the safest minimal scaffold.

## 7) Safety boundary

This sub-skill should not silently expand into a full project installation plan.
If the project needs GPU-only compilation, special libraries, or external checkpoints, document that
as a project requirement and stop at the project-package boundary.
