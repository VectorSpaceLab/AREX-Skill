# Distributed and domain-parallel troubleshooting

## `ShardTensor` dunder error looks unrelated

- Symptom: `TypeError: unsupported operand type(s) for +: 'ShardTensor' and 'ShardTensor'`.
- Likely cause: the real failure was hidden behind `NotImplemented` routing.
- Fix: retry with the equivalent `torch.add(...)` style operation to surface the real traceback.

## `requires_grad_` does not seem to work

- Symptom: setting `requires_grad_` on a ShardTensor appears to do nothing.
- Likely cause: the call acted on a converted temporary.
- Fix: create the ShardTensor with `requires_grad=True` or let autograd flow through the parameter path.

## Mesh or launcher mismatch

- Symptom: DDP reduces on the wrong group or the domain mesh shape is wrong.
- Likely cause: `ddp_size * domain_size != world_size` or the mesh axes were not named explicitly.
- Fix: inspect the launcher context, rebuild the mesh, and verify the group assignments.

## CUDA / backend missing

- Symptom: domain-parallel custom ops or scatter paths fail to initialize.
- Likely cause: the environment is CPU-only or the CUDA backend is not available.
- Fix: record the capability as blocked until a real CUDA environment is available.

## Async collective warnings

- Symptom: exit-time warnings about unwaited collectives.
- Likely cause: a discarded result still had pending communication.
- Fix: explicitly materialize the result or wait on the collective before program exit.

## `torch.compile` surprises

- Symptom: compiled and eager results diverge or a sharded attention path fails.
- Likely cause: the compile region included a collective-heavy or ring-sharded fragment.
- Fix: compile only the safe regions and re-verify eager behavior first.
