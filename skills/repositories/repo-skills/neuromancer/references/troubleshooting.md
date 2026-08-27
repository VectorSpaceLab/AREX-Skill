# Cross-cutting troubleshooting

## Package import and installation

- **`ModuleNotFoundError: neuromancer`:** the active Python is not the one
  where the distribution was installed. Run
  `python -c "from importlib.metadata import version; print(version('neuromancer')); import neuromancer; print(neuromancer.__version__)"`
  from the same isolated environment; do not rely on shell activation state
  alone.
- **`ModuleNotFoundError: requests` while importing `neuromancer.psl`:** PSL
  imports `requests` in this release although the package metadata may omit it.
  Install the missing public dependency into the target environment, then
  rerun the PSL import. This does not authorize a hidden network download.
- **A submodule import fails while core imports pass:** install the dependency
  family owned by that route. ODE/SDE, Lightning, CVXPY/CVXPYLayers, CasADi,
  and plotting imports are not interchangeable; do not mask the error by
  claiming the route is verified.
- **Graph plotting fails:** graph construction and forward execution do not
  require a rendered image. Install the system Graphviz executable only when
  `show()` or file export is actually needed.

## Keys, shapes, and names

- **`KeyError` in `Node`, `Problem`, or `System`:** print the input and output
  key sets before the forward pass. A node receives only the keys listed in
  `input_keys`; a rollout needs rank-3 horizon inputs unless `nsteps` and an
  initializer make the convention explicit.
- **Loss output is missing:** use a collated dataset batch with a string
  `name`; `Problem.forward` prefixes returned keys with that value. Check that
  the selected Trainer metric matches the resulting key.
- **Graph warning or assertion about overwrite/duplicate names:** assign unique
  names to nodes, objectives, and constraints. Recurrent same-key outputs are
  valid only when the overwrite is intentional and documented.
- **Shape mismatch:** write down batch, time, and feature axes for every edge.
  Ordinary blocks and node callables usually consume `(B,F)`, while `System`
  stores `(B,T,F)` and sequence loaders emit `(B,nsteps,F)`.

## Optional backend and runtime limits

- **CUDA import succeeds but execution fails or runs out of memory:** use a tiny
  CPU check and report CUDA as unverified until a real device allocation and the
  selected route pass. A CUDA-enabled PyTorch wheel alone is not evidence.
- **Native Butterfly/factor extension cannot build:** use a pure-Python SLiM
  map or a portable `torch.nn.Linear` fallback. Do not install compilers or
  launch a large native build for a CPU route without explicit authorization.
- **Training hangs, downloads, or writes checkpoints unexpectedly:** reduce to
  a tiny fixture, CPU accelerator, short epoch count, `save_weights=False`, and
  an explicit writable output path. Do not run recursive example sweeps.
- **Optional solver or plotting executable missing:** distinguish package import
  failure, external executable absence, and unsupported problem data. Install
  only the component required by the selected workflow.

For route-specific recovery, use the troubleshooting reference linked from the
relevant sub-skill rather than treating a generic import pass as proof of a
complete scientific workflow.
