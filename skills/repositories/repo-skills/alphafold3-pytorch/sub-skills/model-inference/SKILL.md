---
name: model-inference
description: "Construct bounded AlphaFold 3 models, choose forward loss or
  sampling modes, load compatible checkpoints, and inspect confidence,
  distogram, and ranking outputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model inference

Use this sub-skill after an input has been converted to model-ready tensors, or
use the tiny smoke helper to validate the model contract before allocating a
large run. Start with [workflows](references/workflows.md), then consult the
[API contract](references/model-and-forward-api.md) for exact shapes and
[troubleshooting](references/troubleshooting.md) for recovery.

## Route by responsibility

- Send proteins, nucleic acids, ligands, metals, atom features, batching,
  masks, representative-atom indices, and output structure conversion to
  [input-representation](../input-representation/SKILL.md).
- Send mmCIF/PDB parsing, MSA and template acquisition or preprocessing to
  [data-pipeline](../data-pipeline/SKILL.md). This model accepts already prepared
  tensors; it does not fetch biological data for you.
- Send `Trainer`, datasets, optimizers, YAML, EMA, and checkpointed training
  loops to [training-configuration](../training-configuration/SKILL.md).
- Send Click command construction, output files, and Gradio operation to
  [cli-serving](../cli-serving/SKILL.md).

## Operating sequence

1. Select CPU for contract checks and reduced tests; select CUDA only after the
   device, dtype, and memory budget are explicit.
2. Construct a deliberately reduced `Alphafold3` with dimensions and depths
   appropriate to the available memory. The constructor's production defaults
   are not a smoke configuration.
3. Validate `atom_inputs`, atom-pair inputs, token counts, molecule lengths,
   masks, and all index offsets before calling `forward`.
4. Choose the return mode deliberately: coordinates for inference, or loss and
   an optional breakdown when ground-truth positions/labels are supplied.
5. Add confidence/distogram logits only when they are needed; rank multiple
   samples/models with the dedicated scoring classes rather than treating raw
   logits as scores.
6. For a checkpoint, prefer `init_and_load` when the file was saved by this
   package, and verify version, constructor dimensions, device, and strictness
   before production inference.

Run the [bundled safe check](scripts/smoke_model.py). The examples assume this
sub-skill directory is the current directory; from any other directory, invoke
the linked script by its resolved path because the helper has no current-directory
assumptions:

```bash
python scripts/smoke_model.py --help
python scripts/smoke_model.py --mode signature --device cpu
# Only for an explicitly bounded tiny forward:
python scripts/smoke_model.py --mode forward --device cpu --num-sample-steps 2
python scripts/smoke_model.py --mode forward --device cpu --num-sample-steps 2 --with-distogram
```

The helper never downloads weights, enables PLM/NLM encoders, trains, starts a
server, or uses production-scale defaults. It is a contract probe, not evidence
of useful structural accuracy or production throughput.
