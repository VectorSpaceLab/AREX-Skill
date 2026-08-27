---
name: textgenrnn
description: "Routes agents through textgenrnn generation, training, and
  embedding-analysis workflows for pretrained samples, custom text generation,
  fine-tuning, context labels, and similarity checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# textgenrnn

Use this skill for the `textgenrnn` Python package itself. It is a small Keras/TensorFlow text-generation library centered on one public class, `textgenrnn`, plus a few helper functions in `textgenrnn.utils`.

If the request is about a different TensorFlow project, a transformer LLM stack, or generic Keras internals, route elsewhere. If the request is about this package, use the route map below.

## Before you begin

1. Read [`references/repo-provenance.md`](references/repo-provenance.md) when you need to check whether this skill still matches the repository checkout.
2. Use a compatible runtime. The verified stack for this repository is Python 3.11 with TensorFlow/Keras 2.15.x, `numpy 1.26.4`, `scikit-learn`, `h5py`, `tqdm`, and a setuptools version that still exposes `pkg_resources`.
3. Install the package with `pip install textgenrnn` for the published distribution, or validate a local checkout with an editable install inside a compatible environment.
4. Run a minimal import check before deeper work:

```bash
python -c "from textgenrnn import textgenrnn; print(textgenrnn.__name__)"
```

5. If import or model-load behavior looks suspicious, run [`scripts/check_textgenrnn_env.py`](scripts/check_textgenrnn_env.py) first.
6. There is no CLI entry point in this repository. Use Python APIs or the bundled helper scripts.

## Route map

### [generation](sub-skills/generation/SKILL.md)
Use this route for pretrained generation, custom weight loading, temperature/prefix control, interactive next-token selection, writing generated text to files, saving/loading weights, and model synthesis across multiple `textgenrnn` instances.

### [training](sub-skills/training/SKILL.md)
Use this route for `train_on_texts`, `train_new_model`, `train_from_file`, `train_from_largetext_file`, context labels, word-level training, scratch-model creation, and tiny smoke-training checks.

### [embedding-analysis](sub-skills/embedding-analysis/SKILL.md)
Use this route for `encode_text_vectors`, PCA/t-SNE coordinates, and `similarity` ranking tasks.

## Shared references

- [`references/installation-and-compatibility.md`](references/installation-and-compatibility.md) explains the verified install stack and the TensorFlow/Keras/setuptools compatibility boundary.
- [`references/model-overview.md`](references/model-overview.md) summarizes the architecture, default config, model artifacts, and raw vector shape.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers cross-cutting import, model-load, output-file, and backend warnings.
- [`scripts/check_textgenrnn_env.py`](scripts/check_textgenrnn_env.py) is a safe environment diagnostic and optional short generation smoke.

## Quick path selection

- Ask for `generation` when the user wants to load a model, complete a prompt, generate samples, or save generated text.
- Ask for `training` when the user wants to feed new data, fine-tune, train from a file, or create a scratch model.
- Ask for `embedding-analysis` when the user wants vectors, similarity scores, or visualization coordinates.

## Minimal package facts

- Public import: `from textgenrnn import textgenrnn`
- Public package version in this repository: `2.0.0`
- Default pretrained assets ship as bundled `textgenrnn_weights.hdf5` and `textgenrnn_vocab.json` files inside the package.
- CPU workflows are valid. CUDA/GPU is optional acceleration for training, not a requirement for the selected workflows.

## When to read the bundled helper script

Use [`scripts/check_textgenrnn_env.py`](scripts/check_textgenrnn_env.py) when the user asks whether the installed package can import, whether the environment exposes the expected TensorFlow backend, or whether a quick generation smoke works before moving on to the route-specific sub-skill.
