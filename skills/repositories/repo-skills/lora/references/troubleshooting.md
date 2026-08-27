# Cross-cutting troubleshooting

Read this when a LoRA import, checkpoint load, command, or example run fails
before changing model code.

## Install and import

**Symptom:** `ModuleNotFoundError: No module named 'torch'` or
`No module named 'loralib'`.

**Recovery:** install a PyTorch build first, then `python -m pip install
loralib`. Confirm the interpreter used to run the model is the same one used by
`python -c "import torch, loralib; print(torch.__version__)"`. The package does
not select a CUDA wheel for you.

**Symptom:** a modern PyTorch/Transformers environment imports the package but
the example fails during argument parsing or model loading.

**Recovery:** keep standalone `loralib` use separate from the archived example
forks. The NLU scripts were written for an older Transformers API and the NLG
scripts pin older Torch/Transformers assumptions. Use the focused sub-skill
references to port the LoRA insertion and flags into the versions you actually
run; do not mix an old example launcher with a newer `run_glue.py` blindly.

## Adapter state and trainability

**Symptom:** the optimizer updates the full base model or a saved checkpoint is
nearly as large as the base model.

**Recovery:** call `mark_only_lora_as_trainable(model)` after constructing or
loading the adapterized model, inspect the names with `requires_grad=True`, and
save `lora_state_dict(model)` rather than `model.state_dict()`. If training
biases, use the same `bias=` value for both helper calls.

**Symptom:** `load_state_dict` reports many missing or unexpected keys.

**Recovery:** load the original base checkpoint into the same architecture
first, construct the LoRA layers with the same rank and target modules, then
load the adapter state with `strict=False`. Compare the remaining keys; a
missing `lora_A`/`lora_B` key usually means the target layer was not created or
its module path changed. A classifier-head mismatch in a GLUE task is expected
when the task has a different label count; do not silently ignore adapter-key
mismatches.

## Merge and backend behavior

**Symptom:** outputs change after `eval()` or a second call to `train()`.

**Recovery:** LoRA layers with `merge_weights=True` merge the low-rank update
into the base weight on `eval()` and subtract it again on `train()`. Do not
manually add the update while the layer is already merged. Set
`merge_weights=False` when the surrounding model needs an always-unmerged
forward path, as the archived DeBERTa-v2 example does.

**Symptom:** a command works on CPU but the documented benchmark launcher fails.

**Recovery:** distinguish a CPU import/smoke check from full reproduction. The
archived NLU/NLG recipes use CUDA, distributed launchers, model/data downloads,
and sometimes external metric tools. Check device count, CUDA/Torch wheel
compatibility, per-device batch size, and checkpoint availability before
changing LoRA hyperparameters.

## Data and external tools

**Symptom:** NLG decode or evaluation creates empty files, mismatched line
counts, or missing references.

**Recovery:** validate the context/completion JSONL and prediction JSONL with
the bundled NLG validator. Keep the same dataset ordering through conversion,
encoding, beam search, and decode; pass the correct number of references for
WebNLG/DART. External E2E/GenerationEval tooling is not bundled and may need
network access, Java, Perl, NLTK data, or metric-specific packages.

## Staleness

If source revision, package version, LoRA-specific flags, or model insertion
points differ from [provenance](repo-provenance.md), stop and refresh the skill
instead of patching around stale instructions.
