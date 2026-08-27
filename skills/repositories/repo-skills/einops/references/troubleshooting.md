# Cross-Cutting Troubleshooting

## Purpose

Use this root reference for install/import, optional dependency, backend, and
staleness issues that affect several `einops` sub-skills. For operation-specific
pattern failures, continue to the nearest sub-skill troubleshooting file.

## Install or Import Fails

Symptoms:

```text
ModuleNotFoundError: No module named 'einops'
ImportError while importing einops
```

Recovery:

1. Install the public package in the environment that will run the user's code:
   ```bash
   pip install einops
   ```
2. Verify the interpreter and package version without relying on a source tree:
   ```bash
   python - <<'PY'
   import einops
   print(einops.__version__)
   from einops import rearrange, reduce, repeat, pack, unpack, einsum
   print('core imports ok')
   PY
   ```
3. If editing a checkout, use editable install only for maintainer work:
   ```bash
   pip install -e .
   ```
4. If the user's code runs in notebooks, services, or distributed jobs, check
   that the kernel/worker interpreter is the same interpreter where `einops` was
   installed.

## Optional Tensor Framework Missing

`einops` itself has no runtime dependencies. PyTorch, TensorFlow, JAX, CuPy,
Paddle, OneFlow, PyTensor, MLX, and other tensor libraries must be installed by
the user's project.

Symptoms:

```text
ModuleNotFoundError: No module named 'torch'
ModuleNotFoundError: No module named 'tensorflow'
RuntimeError: Tensor type unknown to einops
```

Recovery:

- Install only the framework needed by the user's task; do not install every
  optional backend.
- Import the framework before passing its tensors to `einops`.
- Use [`sub-skills/framework-integrations/references/troubleshooting.md`](../sub-skills/framework-integrations/references/troubleshooting.md)
  for backend dispatch and layer-specific recovery.

## Pattern or Shape Error

Common error fragments:

```text
Wrong shape
Shape mismatch
Could not infer sizes
Identifiers only on one side of expression
Specify sizes for new axes in repeat
Invalid axis identifier
```

Recovery:

- Use [`sub-skills/tensor-operations/references/troubleshooting.md`](../sub-skills/tensor-operations/references/troubleshooting.md)
  for `rearrange`, `reduce`, `repeat`, and `parse_shape` failures.
- Use [`sub-skills/named-einsum-and-packing/references/troubleshooting.md`](../sub-skills/named-einsum-and-packing/references/troubleshooting.md)
  for `einsum`, `pack`, `unpack`, `PS`, and `-1` inference failures.
- Reproduce with the nearest bundled smoke script and then adapt the tiny array
  shapes to the user's case.

## Accelerator or Device Confusion

`einops` operations run through the backend tensor library. They do not create
CUDA, ROCm, MPS, or vendor accelerator support independently.

Safe statement pattern:

- Verified: "The pattern works on a NumPy/CPU tensor."
- Not verified unless tested: "The same operation works on CUDA/ROCm/MPS."

To verify a device path, create a tiny tensor on the target device with the
framework itself, run one `einops` operation, and assert the output remains on
that device. See `framework-integrations` for concrete examples.

## Maintainer Command Mutates State

Some repository commands mutate the working tree or current Python environment:

- Native test runner with `--pip-install` installs packages into the active
  environment.
- Hatch `check` runs `ruff format` and `ruff check --fix` before mypy.
- Docs build/serve scripts convert README content into docs before building.
- Docs deploy and PyPI publish workflows require credentials and should not be
  run as ordinary diagnostics.

Use [`sub-skills/repo-development`](../sub-skills/repo-development/SKILL.md)
for dry-run wrappers and maintainer boundaries.

## Skill Staleness

Read [`repo-provenance.md`](repo-provenance.md). Refresh this skill if:

- The current checkout commit or dirty paths differ from the recorded snapshot.
- Public exports in `einops/__init__.py` changed.
- Function signatures or pattern grammar changed.
- Backend classes, layer modules, Array API support, or torch compile helpers
  changed.
- Native test runner, docs scripts, CI matrices, or package metadata changed.
