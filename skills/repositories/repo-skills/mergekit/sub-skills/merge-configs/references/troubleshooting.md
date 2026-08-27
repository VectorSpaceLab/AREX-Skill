# Troubleshooting core YAML merges

Classify the first actionable error before editing a working configuration.
Run the parser helper from any directory; it performs no model or Hub access:

```text
python scripts/validate_merge_config.py CONFIG.yml  # from this sub-skill directory
# or: python sub-skills/merge-configs/scripts/validate_merge_config.py CONFIG.yml  # from skill root
```

## Install and import

**Symptom:** `mergekit-yaml: command not found`, `No module named mergekit`, or
an import fails before the config is read.

**Recovery:** activate the environment intended for the merge, verify
`python -m pip show mergekit torch transformers pydantic click`, and run
`mergekit-yaml --help`. Install the package and its normal dependencies in the
active environment rather than patching the configuration. Keep optional
workflow dependencies out of the core route; raw PyTorch, MoE, multi-stage,
LoRA, tokensurgeon, layer-shuffle, and evolution may have distinct extras and
belong to the specialty siblings.

**Symptom:** import succeeds but the helper reports a package version different
from the run environment.

**Recovery:** compare `python -c 'import mergekit; print(mergekit.__file__)'`
with the executable used for `mergekit-yaml`; remove stale editable installs or
invoke both through the same environment. Do not mix a checkout import with a
published package when validating a reproducible run.

## Optional dependencies and backend

**Symptom:** a specialty command fails on an absent package such as an
accelerator, evaluation, Ray, or PEFT dependency.

**Recovery:** do not add that dependency to a core YAML merge by guesswork.
Route the named workflow to `specialized-workflows` or
`extension-and-evolution`, install only its documented extra, and rerun its own
help/probe. A normal core merge requires the installed torch, Transformers,
Pydantic, Click, YAML, tokenizer, and safe-serialization dependencies.

**Symptom:** `--cuda` or `--device cuda` fails with “CUDA not available”, device
ordinal errors, or an unsupported kernel/dtype error.

**Recovery:** run `python -c 'import torch; print(torch.version.cuda, torch.cuda.is_available(), torch.cuda.device_count())'`.
Remove `--cuda`, set `--device cpu`, and disable accelerator-only memory flags
for a CPU fallback. If CUDA is available, check visible devices and use a
supported dtype; do not assume a CUDA-enabled torch build means a visible GPU.

## YAML schema and exclusivity

**Symptom:** validation reports `Exactly one of 'models', 'slices', or
'modules' must be present`.

**Recovery:** keep exactly one of those top-level keys. Do not leave an empty
list beside the populated key; empty lists still alter the validator/planner
path. Put `models` or `slices` inside each `modules` entry, never both.

**Symptom:** `Must specify either output slices or models to merge`.

**Recovery:** every module definition must choose one non-empty `models` or
`slices` list. Check YAML indentation and list nesting.

**Symptom:** `Cannot specify both tokenizer_source and tokenizer`.

**Recovery:** select modern `tokenizer` for per-token controls, or legacy
`tokenizer_source` for simple compatibility selection. Remove the other field;
do not try to merge their settings.

**Symptom:** the helper accepts YAML but the run fails with an unknown module,
unequal slice lengths, or an architecture-specific config key error.

**Recovery:** use `modules` for multi-module architectures, make all sources in
an output slice have equal `(end - start)` lengths, and route architecture
inference/conversion to `model-io-and-architecture`. Parsing cannot prove layer
ranges or architecture compatibility.

## Model references and files

**Symptom:** `Unable to find local path`, repository not found, revision not
found, missing config, missing tokenizer, or an authentication error.

**Recovery:** test each local path independently and confirm it contains the
expected model config and checkpoint index/shards. For Hub references verify
repository id, revision, network/authentication, and cache permissions. Keep
one `@revision` suffix only; malformed strings with multiple `@` are invalid.
Use `--transformers-cache` for a writable cache and record the exact revision.
Do not enable `--trust-remote-code` merely to hide a missing standard
architecture; use it only when the model intentionally requires remote code
and the trust boundary permits it.

**Symptom:** `Base model not in input tensors` or a task-vector method cannot
find its base tensor.

**Recovery:** use byte-for-byte equivalent model references in `base_model` and
its input entry, or allow whole-model normalization to add the declared base.
For slices, set a slice-level `base_model` only when that base is valid for the
slice. A base not contributing the needed tensor cannot be repaired by changing
`weight`.

**Symptom:** shape mismatch, missing required tensor, or incompatible layer
architecture after references resolve.

**Recovery:** stop changing method parameters. Compare architecture, tensor
names, layer counts, and checkpoint conversion requirements; route to
`model-io-and-architecture`. Use `--allow-crimes` only as an explicit,
reviewed decision to mix architectures, not as a default fix.

## Method and parameter failures

**Symptom:** `Unimplemented merge method`.

**Recovery:** use one of the exact registered names in `merge-methods.md`.
A method from another version is not available merely because a document or
model card mentions it.

**Symptom:** `expects exactly two models`, `requires at least 3 models`, or
`Passthrough merge expects exactly one tensor`.

**Recovery:** count effective tensors after base insertion and slice expansion.
Use `slerp`, `nearswap`, and `arcee_fusion` only for their two-model shapes;
use `model_stock` for base plus two variants; use `passthrough` with one source
per output tensor. Remove accidental duplicate/distinct base references.

**Symptom:** `Missing required parameter weight`, `t`, or another method value.

**Recovery:** inspect the effective topology and put the value at the correct
scope. Per-input `weight` belongs under each model/source; global `t`,
`normalize`, `lambda`, or method controls belong under top-level or module/
slice `parameters`. Add an unfiltered fallback after conditional entries.
Remember that a filter is a substring of the actual tensor name and unmatched
conditional lists fall through to lower precedence/defaults.

**Symptom:** merge result changes unexpectedly by layer or only some tensors are
zeroed.

**Recovery:** check gradient endpoints and normalized layer `t`; check filter
order and spelling. A numeric list interpolates from first to last over the
output slice, while an ordered conditional list chooses the first matching
filter. Use `-v` or a small local fixture to inspect the effective plan.

**Symptom:** DARE result is not repeatable, or DELLA raises a probability/
NaN error.

**Recovery:** set `--random-seed INTEGER` for randomized DARE. For DELLA choose
`epsilon` so `density - epsilon > 0` and `density + epsilon < 1`; verify density
is in the intended `(0, 1]` range. For spherical methods, avoid zero or exactly
balanced weights that produce a zero weighted sum.

## Tokenizer and chat conflicts

**Symptom:** modern and legacy tokenizer fields fail validation.

**Recovery:** keep exactly one. Use modern `tokenizer` when union, per-token
embedding, forced donor, zero embedding, model-token remapping, or padding is
needed.

**Symptom:** union output misses a special token, warns that a token is unused,
or embedding dimensions do not match.

**Recovery:** confirm the token exists in the donor tokenizer and below that
model's configured vocabulary size; add it under modern `tokens` when it is a
new output token; ensure all embedding widths match. A token index beyond
`vocab_size` is intentionally ignored. A tokenizer load warning for an input
model means fallback assumptions were made and should be reviewed.

**Symptom:** `Token ... not found`, source model assertion, or forced embedding
has no effect.

**Recovery:** make the donor model an actual merge reference, use exactly one of
`token`/`token_id`, verify the token id is in range, and set `force: true` when
existing donor embeddings must be replaced in every input. Without `force`, an
existing input embedding remains its own value.

**Symptom:** padded embedding rows/config size disagree with tokenizer length.

**Recovery:** expect the tokenizer's real vocabulary length to remain smaller
than the padded model config. Check that embedding row count and config
`vocab_size` equal the requested multiple and that new rows are finite.

**Symptom:** `Invalid chat template`, template not saved, or `auto` selects an
unexpected format.

**Recovery:** use an exact built-in name or a literal Jinja string with braces
and at least 20 characters. `auto` chooses the plurality of non-empty input
templates; explicitly set a built-in/literal when models disagree. Ensure a
built or copied tokenizer exists; with `--no-copy-tokenizer` and no tokenizer
source, a chat template cannot be persisted.

## Dtype and serialization

**Symptom:** output config reports an unexpected dtype or saved tensors have the
wrong type.

**Recovery:** remember `dtype` controls input loading and is the output-config
fallback, while `out_dtype` controls save-time conversion and takes precedence
in the output config. Check architecture force-dtype behavior. Use a torch dtype
name supported by the active package and validate one output tensor after the
run.

**Symptom:** safe serialization fails, output shards are absent/incomplete, or
an output directory contains stale shards.

**Recovery:** use the default `--safe-serialization`, choose a writable empty
output directory, and rerun after removing only the failed output. Reduce
`--out-shard-size` if individual shard handling is a constraint. Use
`--no-safe-serialization` only when a downstream consumer explicitly requires
pickle and the risk is accepted. Inspect the writer/finalization error rather
than claiming success from a partially populated directory.

**Symptom:** tokenizer/model card is missing although tensors completed.

**Recovery:** check `--copy-tokenizer` and `--write-model-card` were not
negated. A failed donor-tokenizer copy can leave the merge successful but
without tokenizer files; supply a tokenizer configuration or copy it manually
from a verified donor. The model card and `mergekit_config.yml` are controlled
by `--write-model-card`.

## Memory and device flags

**Symptom:** host RAM exhaustion with CPU execution.

**Recovery:** use `--low-cpu-memory` only when accelerator storage is available;
otherwise it does not solve a CPU-only RAM limit. Reduce concurrency/thread
pressure, choose a smaller `--out-shard-size`, use `--lazy-unpickle` only for
legacy pickle inputs, and route detailed checkpoint/memory planning to
`model-io-and-architecture`.

**Symptom:** GPU out-of-memory with a CUDA merge.

**Recovery:** remove `--read-to-gpu` so weights are staged through host memory,
avoid `--low-cpu-memory` unless VRAM is known to exceed RAM, use a single
`--device cuda` before trying `--multi-gpu`, and disable `--async-write` if
write buffers add pressure. `--gpu-rich` is an alias for `--cuda`,
`--low-cpu-memory`, `--read-to-gpu`, and `--multi-gpu`; use it only when all
four choices are appropriate.

**Symptom:** multi-GPU execution hangs, selects the wrong device, or gives an
ordinal error.

**Recovery:** prove a single-GPU `--device cuda` run first, inspect visible
accelerators, then add `--multi-gpu`. Do not combine `--gpu-rich` with an
unverified device layout. Fall back to CPU or single-GPU and route graph/device
placement diagnosis to `model-io-and-architecture`.
