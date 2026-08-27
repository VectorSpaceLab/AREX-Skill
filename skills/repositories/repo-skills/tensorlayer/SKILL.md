---
name: tensorlayer
description: "Routes TensorLayer model-building, data utilities, vision, text,
  reinforcement learning, and training workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# TensorLayer

Use this repo skill when the user wants to work with the TensorLayer package and does not need to open the original checkout again. TensorLayer is a TensorFlow-based deep learning library, so the normal path is to install TensorFlow 2.x, install TensorLayer, and then route to the sub-skill that matches the workflow.

## Quick install

- Install a TensorFlow 2.x build appropriate for the host.
- Install TensorLayer, usually with editable mode for local inspection: `pip install -e .`.
- If you need the app or vision modules, add `matplotlib` and `opencv-python`.
- If you need `tensorlayer.nlp.process_sentence`, add `nltk`.
- The package's runtime dependencies include `imageio`, `progressbar2`, `scikit-image`, `scipy`, `wrapt`, `h5py`, and `cloudpickle`.

## Minimal import check

Start with:

```bash
python -I -c "import tensorlayer as tl; print(tl.__version__)"
```

If the package import fails because the app/vision modules are missing, install the optional visualization stack and try again. For CLI help, make sure `CUDA_VISIBLE_DEVICES` is not set to an empty string; the current `tl` parser crashes on that case.

## How the skill is organized

- `sub-skills/core-modeling/` — layers, models, save/load, pretrained constructors, activations, costs, initializers, optimizers.
- `sub-skills/data-and-utilities/` — file helpers, dataset loaders, preprocessing, iteration, visualization, TFRecord and tiny data round-trips.
- `sub-skills/training-and-cli/` — `tl.utils.fit/test/predict`, `tl train`, distributed-training setup, and training-loop patterns.
- `sub-skills/vision-and-apps/` — pretrained CNNs, object-detection and pose wrappers, spatial transformer workflows, quantized vision examples.
- `sub-skills/text-and-sequence/` — NLP helpers, word embedding, PTB/text generation, seq2seq workflows.
- `sub-skills/reinforcement-learning/` — reward utilities and RL tutorial patterns.

## Read first

- Read `references/repo-provenance.md` before deciding whether this skill matches the current checkout.
- Read `references/api-overview.md` when you need the package-wide module map or the verified live API notes.
- Read `references/troubleshooting.md` when imports, CLI help, optional dependencies, or backend warnings fail.

## Safe bundled checks

- `scripts/check_import.py` — verify package importability and run a tiny model smoke test.
- `scripts/check_cli_help.py` — verify the `tl` CLI help without triggering the empty-`CUDA_VISIBLE_DEVICES` bug.

## Routing hints

Choose the sub-skill by the user's natural request:

- If the request is about building or saving a model, go to `core-modeling`.
- If the request is about loading data, preprocessing, TFRecords, or utility helpers, go to `data-and-utilities`.
- If the request is about training loops or `tl train`, go to `training-and-cli`.
- If the request is about image models, detection wrappers, or visual output, go to `vision-and-apps`.
- If the request is about text, tokenization, PTB, word embedding, or seq2seq, go to `text-and-sequence`.
- If the request is about rewards, sampling actions, or RL examples, go to `reinforcement-learning`.

When a workflow spans more than one area, start with the most specific sub-skill and use the cross-links in its references.
