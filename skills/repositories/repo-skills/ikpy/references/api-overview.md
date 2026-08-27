# IKPy API Overview

Read this reference when a task spans multiple sub-skills or needs a quick
verified map of the package surface. The generated graph targets IKPy 4.0.0
and Python >=3.10.

## Installation and imports

Base installation provides `numpy`, `scipy`, and `sympy`:

```bash
python -m pip install ikpy
python -c "import ikpy; print(ikpy.__version__, ikpy.JAX_AVAILABLE)"
```

Optional extras are independent:

```bash
python -m pip install 'ikpy[plot]'  # matplotlib and graphviz Python package
python -m pip install 'ikpy[jax]'   # jax and jaxlib
```

The package has no console entry point. Use Python APIs or the bundled helpers
linked from the sub-skills.

## Public surface

| Area | Main symbols | Read next |
|---|---|---|
| Chain execution | `ikpy.chain.Chain`, `forward_kinematics`, `inverse_kinematics`, `inverse_kinematics_frame` | `sub-skills/chain-kinematics/references/api-reference.md` |
| Links | `Link`, `OriginLink`, `URDFLink`, `DHLink` | `sub-skills/chain-kinematics/references/api-reference.md` |
| URDF | `Chain.from_urdf_file`, `Chain.from_json_file`, `ikpy.urdf.URDF`, `get_chain_from_joints`, `get_urdf_tree` | `sub-skills/robot-model-import/references/api-reference.md` |
| MJCF | `Chain.from_mjcf_file`, `ikpy.mjcf.MJCF`, orientation helpers | `sub-skills/robot-model-import/references/api-reference.md` |
| NumPy geometry | `ikpy.utils.geometry` | `sub-skills/visualization-geometry/references/api-reference.md` |
| Plotting | `ikpy.utils.plot`, `Chain.plot` | `sub-skills/visualization-geometry/references/workflows.md` |
| JAX | `Chain` with `backend="jax"`, `JaxKinematicsCache`, `ikpy.jax_backend` | `sub-skills/jax-backend/references/api-reference.md` |

## Cross-cutting invariants

1. A chain's joint vector has length `len(chain.links)`. Inactive entries are
   still required in FK and are preserved in the returned IK solution.
2. `active_links_mask` controls optimization variables, not the FK vector.
   The constructor forces the final mask entry false when it is the Python
   singleton `True`; set it explicitly to `False` rather than relying on the
   warning path.
3. `forward_kinematics` returns a 4x4 homogeneous matrix, or a list of one
   4x4 frame per link with `full_kinematics=True`.
4. `inverse_kinematics` returns a full joint vector. Position targets are
   length-3; orientation targets are a length-3 axis for `X`, `Y`, or `Z`, or
   a 3x3 matrix for `all`.
5. Angles and translations use the model's units; URDF/MJCF parsers convert
   the model's documented angular representation to IKPy's internal radians.
6. A numerical IK result must be validated by rerunning FK and measuring target
   error. Solver termination alone is not a physical-safety guarantee.

## Environment smoke

Use the bundled helper before a larger task:

```bash
python scripts/check_env.py
python scripts/check_env.py --require-jax
python scripts/check_env.py --require-plot
```

The helper checks importability and optional modules only. It does not install
packages, select a backend, load external files, or connect to hardware.
