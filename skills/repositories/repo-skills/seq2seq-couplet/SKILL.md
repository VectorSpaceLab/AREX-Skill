---
name: seq2seq-couplet
description: "Routes training, inference, and Flask serving workflows for the
  TensorFlow seq2seq couplet project."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# seq2seq-couplet

Use this skill for the TensorFlow seq2seq couplet repository. It covers the
project's two user-facing workflows:

- training or continuing a checkpoint,
- generating couplets from a trained checkpoint or serving the HTTP API.

## Read first

- `references/repo-provenance.md` to check whether this skill still matches the
  current checkout.
- `references/dependencies.md` for the verified runtime dependency set and the
  legacy GPU notes.
- `references/model-overview.md` for the architecture and module map.
- `references/troubleshooting.md` for the common install, data, checkpoint,
  and backend failures.
- `references/licensing.md` before redistributing or modifying the bundled
  runtime copy.

## Install and verify

1. Use Python 3.7 for the verified runtime set.
2. Run `scripts/install_runtime_deps.py` inside the target environment if the
   runtime dependencies are missing.
3. Run `scripts/check_env.py` to verify the bundled runtime copy, TensorFlow
   smoke, and route definitions. Add `--repo-root <checkout>` only when you need
   to compare a live checkout against the bundled copy.

The verified dependency set is CPU-friendly and does not require CUDA for the
bundled workflows. Legacy GPU acceleration needs TensorFlow 1.15 together with
CUDA 10.0 and cuDNN 7, which are not bundled or required here.

## Route map

| If the user wants... | Go here |
| --- | --- |
| Train the couplet model, continue a checkpoint, inspect loss or BLEU, or validate the line/vocab layout | `sub-skills/training/SKILL.md` |
| Generate couplets from a checkpoint, inspect beam scores, or expose the Flask API | `sub-skills/inference/SKILL.md` |
| Diagnose TensorFlow, protobuf, CUDA, checkpoint, or path issues | `references/troubleshooting.md` |

## Shared helpers

- `scripts/couplet_runtime.py` holds the common path handling, tiny-fixture, and
  inference helpers used by the bundled scripts.
- `scripts/install_runtime_deps.py` installs the verified runtime package set
  into the active Python environment.
- `scripts/check_env.py` confirms imports and the TensorFlow smoke without
  importing the legacy long-running server module.

## Working rules

- Prefer the bundled wrappers over the legacy source scripts; they use the
  self-contained runtime copy by default and accept explicit file paths instead
  of hard-coded paths.
- Keep training and inference vocab files aligned. The first two vocabulary
  entries must be `<s>` and `</s>` in that order.
- If a script mentions the legacy source behavior, treat it as evidence, not as
  a runtime dependency.
- Use the sub-skill references for step-by-step workflows; keep this root skill
  as the router.

## Fast orientation

- `reader.py` tokenizes on spaces, appends `</s>` to the input, and prepends
  `<s>` plus `</s>` to the target side.
- `seq2seq.py` builds a bidirectional LSTM encoder, Bahdanau attention decoder,
  and beam-search inference path.
- `model.py` manages the training, evaluation, and inference graphs.
- `server.py` is the legacy Flask surface; the bundled inference scripts provide
  the same behavior with explicit paths and safer startup.

## Common first checks

- If imports fail with protobuf descriptor errors or the beam-search graph
  raises a NumPy symbolic-tensor error, read the troubleshooting reference and
  reinstall the pinned dependency set.
- If TensorFlow prints missing `libcudart` or `libcudnn` warnings, the CPU path
  is still usable; the legacy GPU path is simply unavailable.
- If a checkpoint load fails, make sure the output directory was created by the
  training workflow and that the vocab file has not changed.

For details on the per-workflow commands, continue into the relevant sub-skill.
