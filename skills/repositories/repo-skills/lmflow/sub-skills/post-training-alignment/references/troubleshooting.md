# Alignment Troubleshooting

## Missing `trl`

**Symptom**: DPO or DPOv2 imports fail.

**Likely cause**: the `trl` extra is not installed.

**Recovery**: install the `trl` extra in the alignment environment.

## Missing Ray or Engine Extras

**Symptom**: iterative DPO or reward-model inference fails because an engine module cannot be imported.

**Likely cause**: the environment is missing Ray, vLLM, or SGLang.

**Recovery**: install the exact optional extra and keep vLLM and SGLang in separate environments.

## Bad Preference Data

**Symptom**: the aligner complains about `chosen`, `rejected`, `prompt`, or `margin`.

**Likely cause**: the dataset type does not match the expected alignment shape.

**Recovery**: validate the dataset with the data-and-templates helper and convert to the required preference layout.

## RAFT Output Noise

**Symptom**: generated text contains noisy markers such as stray `#` tokens.

**Likely cause**: the workflow is collecting low-quality generations or the cleanup rule is too permissive.

**Recovery**: adjust the RAFT cleanup logic and inspect collected samples before another iteration.

## Merge-LoRA Confusion

**Symptom**: merging fails or the output model is not usable.

**Likely cause**: the base path, adapter path, or output path is wrong.

**Recovery**: confirm the paths and use the CPU merge route by default.
