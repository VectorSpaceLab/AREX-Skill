# Example and workflow guide

The upstream project contains one safe basic example and several longer
demonstrations. This generated skill distills those workflows so future agents
can use the package without opening the original checkout.

## Safe basic workflow

Use this pattern for a quick package validation or as the starting point for a
user's own sequence model:

1. Create dummy or task-specific sequence data with shape
   `(samples, timesteps, input_dim)`.
2. Build a Keras Functional model.
3. Put an RNN layer before attention with `return_sequences=True`.
4. Add `Attention(units=..., score="luong" or "bahdanau")`.
5. Add the task head, compile/train as needed, then validate save/load with
   `custom_objects={"Attention": Attention}`.

Bundled replacement for a safe smoke run:

```bash
python scripts/smoke_attention.py --score both --save-format h5 --force-cpu
```

Use `--score luong` or `--score bahdanau` when you only need one branch. Use
`--skip-save-load` when filesystem writes are not allowed. This script does not
train on large data; it only checks model construction, prediction, config, and
serialization behavior.

## Debug and visualization workflows

The repository's visualization demos use `KERAS_ATTENTION_DEBUG=1` plus
`keract` and plotting libraries to inspect the internal `attention_weight`
softmax layer. Distill the pattern as follows:

1. Set `KERAS_ATTENTION_DEBUG=1` before importing `attention`.
2. Build a small Functional model, not a Sequential model, when debug mode is
   active.
3. Run one forward pass or a small training loop so the attention internals are
   built.
4. Use `keract.get_activations(model, sample_batch,
   layer_names="attention_weight")` to obtain the attention weights.
5. Plot or compare the attention matrix against a task-specific mask.

For a dependency-only check before attempting visualization:

```bash
python scripts/check_example_dependencies.py
```

If running in a headless terminal or CI job, set a noninteractive Matplotlib
backend before importing `matplotlib`:

```bash
MPLBACKEND=Agg python your_visualization_script.py
```

### Add-two-numbers-style demo

The delimiter-sum demo trains on synthetic sequences where two delimiter
positions indicate which subsequent values should be averaged/summed. The
attention map should become largest around the useful positions. Use this demo
only when the user specifically asks for interpretability or attention-map
visualization, because the original training scale is large and writes many
plot images.

Safe adaptation tips:

- Reduce samples and epochs first; confirm the pipeline and attention-weight
  extraction before attempting the full visualization.
- Keep fixed delimiter positions for tiny tests when you need deterministic
  assertions.
- Save plots to a temporary or user-approved output directory.
- Prefer `score="bahdanau"` when matching the repository's delimiter demo.

### Find-max-style demo

The max-of-sequence demo trains the model to identify the maximum value in each
sequence and visualizes whether attention concentrates on that timestep. It is
useful for explaining attention maps but is not a default installation smoke.

Safe adaptation tips:

- Start with a tiny sample count and very few epochs.
- Use `MPLBACKEND=Agg` in noninteractive environments.
- Treat lack of convergence in a tiny run as a training-budget issue, not a
  package import failure, unless model construction or `attention_weight`
  extraction fails.

## IMDB comparison workflow

The IMDB demo compares a baseline LSTM classifier against a similarly sized
LSTM-plus-`Attention` classifier and reports maximum/mean validation accuracy.
It is benchmark-like, not a quick smoke test.

Operational cautions:

- It may download the IMDB dataset through Keras/TensorFlow dataset utilities.
- It trains two models for multiple epochs and can be slow on CPU.
- GPU acceleration is useful for runtime but not required by the package API.
- Accuracy differences are stochastic; preserve seeds and run counts when a
  user asks for a faithful comparison.

Do not run this workflow during ordinary package validation. Use it only when
the task explicitly asks for the comparison experiment or a benchmark-style
reproduction.

## Optional dependency matrix

| Need | Package/tool | Check |
| --- | --- | --- |
| Core `Attention` layer | `attention`, `tensorflow`, `numpy` | `python scripts/smoke_attention.py --score both --force-cpu` |
| Save/load HDF5 example | `h5py` via TensorFlow dependency | bundled smoke script with `--save-format h5` |
| Attention activation extraction | `keract` | `python scripts/check_example_dependencies.py` |
| Plot images/heatmaps | `matplotlib` | dependency checker; set `MPLBACKEND=Agg` if headless |
| Model diagram generation | `pydot` plus Graphviz `dot` executable | dependency checker reports both Python package and `dot` path |
| IMDB dataset demo | network access to Keras dataset cache | do not run unless explicitly selected |

## Translating examples to user code

When adapting these workflows for a user's project:

- Replace synthetic arrays with the user's sequence tensor but preserve the 3D
  input contract.
- Keep `return_sequences=True` immediately before `Attention`.
- Select the attention `units` to match the downstream feature width; it is not
  required to equal the RNN hidden size.
- Use `score="luong"` unless the user requests Bahdanau or is matching a known
  additive-attention experiment.
- Validate with a tiny batch before starting a long training run.
- Keep debug mode and visualization code out of production training/inference
  unless the user explicitly needs interpretability artifacts.
