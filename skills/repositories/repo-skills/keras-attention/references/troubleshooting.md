# Troubleshooting guide

## Install and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'attention'` | The `attention` distribution is not installed in the active Python environment. | Run `python -m pip install attention`, then verify `from attention import Attention` from the same Python. |
| `ModuleNotFoundError: No module named 'tensorflow'` | The package requires TensorFlow but the environment lacks it or uses the wrong Python. | Install a TensorFlow 2.x version compatible with the Python version, then run `python scripts/smoke_attention.py --force-cpu`. |
| Import works in the source checkout but fails elsewhere | The checkout directory was shadowing a missing install. | Test from a neutral directory and install the distribution into the target environment. |
| TensorFlow/Keras import errors after an upgrade | Version mismatch, especially around newer TensorFlow/Keras releases. | Prefer the tested TensorFlow 2.x range in `references/compatibility.md`; run the bundled smoke script before continuing. |

## Model-construction errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ValueError: Possible values for score are: [luong] and [bahdanau].` | `score` was not exactly `"luong"` or `"bahdanau"`. | Correct the score string or use `Attention.SCORE_LUONG` / `Attention.SCORE_BAHDANAU`. |
| Shape/rank errors inside `Dot`, `Lambda`, or attention layers | `Attention` received a 2D final state instead of a 3D sequence. | Set `return_sequences=True` on the preceding RNN/LSTM/GRU so the input shape is `(batch, timesteps, input_dim)`. |
| Output feature width is unexpected | `units` controls the final attention vector width. | Set `Attention(units=desired_width)` and update the downstream `Dense`/head layer if needed. |
| Attention does not appear to learn a useful pattern in a tiny demo | Too few samples/epochs or a weak synthetic setup. | First verify construction with the smoke script; then increase data/epochs only for an actual training experiment. |

## Save/load and serialization

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unknown layer: Attention` or custom-object deserialization errors | The model loader does not know the custom layer class. | Import `Attention` and pass `custom_objects={"Attention": Attention}` to `load_model(...)`. |
| HDF5 save emits a legacy-format warning | Modern Keras recommends `.keras` files, but the upstream example uses `.h5`. | Treat the warning as non-fatal. Use `.keras` for new code if desired, but still test loading with custom objects. |
| Predictions differ after load | Different random state, training/evaluation mode differences, or a serialization issue. | Use the bundled smoke script to isolate package serialization, then compare the user's full model with fixed seeds and deterministic preprocessing. |

## Debug mode and attention-weight extraction

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KERAS_ATTENTION_DEBUG=1` seems ignored | The environment variable was set after `attention` was already imported. | Restart the process/kernel and set `KERAS_ATTENTION_DEBUG=1` before importing `attention`. |
| Sequential model fails or treats `Attention` strangely in debug mode | Debug mode makes `Attention` subclass `object`, not Keras `Layer`. | Use debug mode only for introspection. Prefer the Functional API or direct calls in debug experiments; use normal mode for production models. |
| `keract` cannot find `attention_weight` | The model has not been built/called, the layer name changed, or debug mode was not enabled early enough. | Run a forward pass first; confirm `KERAS_ATTENTION_DEBUG=1` was set before import; inspect available activation names if needed. |
| Attention weights are plotted but look noisy | The model may not have trained enough, or the toy task is too small/stochastic. | Verify the data mask, seed the synthetic data, and increase training budget only after the extraction pipeline works. |

## Optional visualization dependencies

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'keract'` | Visualization examples need optional dependencies. | Run `python -m pip install keract matplotlib pydot`, then `python scripts/check_example_dependencies.py`. |
| `ImportError` or `InvocationException` from `plot_model` / pydot | Graphviz `dot` executable is missing or not on `PATH`. | Install Graphviz for the active environment and confirm `dot -V` or the dependency checker reports a path. |
| Matplotlib tries to open a GUI or hangs in CI | Interactive backend selected in a headless process. | Set `MPLBACKEND=Agg` before importing Matplotlib or save figures without displaying windows. |
| Large numbers of plot files are created | Visualization demos save per-epoch images. | Use a temporary/user-approved output directory and lower the epoch count for checks. |

## Dataset and long-running examples

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| IMDB example stalls or fails while loading data | Keras dataset download needs network/cache access. | Do not use IMDB as an install smoke. Prepopulate/cache the dataset or skip unless the task explicitly requires the benchmark. |
| IMDB or visualization demos run very slowly on CPU | They are training demonstrations, not minimal checks. | Use the bundled smoke script for package validation; reserve full demos for explicit experiment requests. |
| Results do not match README accuracy exactly | The comparison is stochastic and depends on TensorFlow, seeds, hardware, and data cache. | Report methodology, seed, versions, and run count rather than promising exact accuracy. |

## TensorFlow backend warnings

TensorFlow may print messages about missing CUDA drivers, failed CUDA init,
cuDNN/cuFFT/cuBLAS factory registration, or missing TensorRT. For CPU-only
Keras Attention tasks, these messages can be ignored if imports and the smoke
script pass. If the user explicitly needs GPU execution, verify TensorFlow sees
the target device before debugging the `Attention` layer itself.

Useful CPU-only smoke:

```bash
CUDA_VISIBLE_DEVICES="" python scripts/smoke_attention.py --score both --force-cpu
```

## Protobuf compatibility

If an older TensorFlow environment reports protobuf implementation errors, try:

```bash
PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python python your_script.py
```

This mirrors the repository's test environment setting. Use it as a targeted
workaround, not as a blanket default.
