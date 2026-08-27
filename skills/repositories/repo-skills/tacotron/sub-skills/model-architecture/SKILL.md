---
name: model-architecture
description: "Guides inspection and adaptation of the legacy Tacotron TensorFlow
  1.x graph, including input shapes, CBHG blocks, attention, decoder outputs,
  and audio reconstruction settings."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model architecture

Use this route when a task concerns graph construction, tensor shapes, model
components, hparams that alter dimensions, or why a checkpoint cannot be used
with a new configuration. This is the original Tacotron implementation using
TensorFlow 1.x graph APIs and `tf.contrib`; it is not a TensorFlow 2 migration
recipe.

## Workflow

1. Start with the hparams that define input/output dimensions: `num_mels`,
   `num_freq`, `outputs_per_step`, `embed_depth`, encoder/attention/decoder
   depths, and `max_iters`.
2. Build the model through `models.create_model('tacotron', hparams)` and call
   `Tacotron.initialize(inputs, input_lengths, mel_targets, linear_targets)`.
   Omit targets for inference; provide both for training.
3. Treat `mel_outputs`, `linear_outputs`, and `alignments` as the public graph
   outputs. Add loss and optimizer only in training graphs.
4. Use the bundled shape inspector for graph/API checks, and read the detailed
   architecture reference before changing dimensions or restoring a checkpoint.
## Command roots and verification boundary

The inspector is a skill asset, while source imports must use the checkout root:

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/model-architecture/scripts/inspect_model_shapes.py --repo-root "$CHECKOUT_ROOT"
cd "$SKILL_ROOT" && python sub-skills/model-architecture/scripts/inspect_model_shapes.py --repo-root "$CHECKOUT_ROOT" --build-graph
```

The graph smoke requires a compatible TensorFlow 1.x runtime and checks graph
construction only. It loads no checkpoint and does not validate real audio,
Griffin-Lim quality, vocoder output, training convergence, or GPU behavior.

Read [`references/architecture.md`](references/architecture.md) for the graph
flow, [`references/api-reference.md`](references/api-reference.md) for shape
contracts, and [`references/troubleshooting.md`](references/troubleshooting.md)
for TensorFlow-version and checkpoint mismatch guidance. The bundled
[`scripts/inspect_model_shapes.py`](scripts/inspect_model_shapes.py) is safe by
default and only builds a tiny graph when `--build-graph` is explicitly used.
