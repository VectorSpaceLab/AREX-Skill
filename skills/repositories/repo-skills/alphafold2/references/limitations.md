# Scope and limitations

Read this when a request expands beyond the verified tiny-tensor operating
surface.

## Current package status

This skill describes the unofficial `alphafold2-pytorch` 0.4.32 package. It is
not a reproduction of the official DeepMind JAX AlphaFold2 system, and its
untrained model outputs should not be presented as validated biological
structures or benchmark results.

The README contains experimental or later-intended options that are absent from
the inspected constructor and forward signatures at this snapshot. The owning
sub-skills call out the most important drift, including atom-expanded outputs,
selectable SE3/EN/EGNN structure modules, real-valued distance predictions, and
several sparse/linear/convolutional attention flags.

## Deliberately bounded workflows

- **Large MSA/database acquisition:** the README describes multi-terabyte data
  and external hosting. This skill does not download, validate, or cache that
  data.
- **Pretrained wrappers:** ESM, MSA Transformer, and ProtTrans construction may
  download model code/weights, require model caches or network access, and may
  use Apex/fused operations. Use precomputed representations when those
  prerequisites are not approved.
- **Training:** the repository includes training helpers and DeepSpeed/
  Lightning-related files, but this graph does not provide a long-running
  training recipe or claim training reproducibility.
- **Refinement and relaxation:** external refinement, PyRosetta, OpenMM
  relaxation, PDB production, and notebook-scale end-to-end runs need separate
  data, model, and system validation.
- **CUDA:** a CUDA-enabled PyTorch installation and visible device are not a
  successful GPU verification. Check allocation and a tiny forward on the
  target host; fall back to CPU for API/shape inspection when GPU memory is
  unavailable.

For these workflows, preserve the explicit prerequisite and stop condition
rather than silently substituting a tiny synthetic CPU run for a scientific
claim.
