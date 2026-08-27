# Troubleshooting

## Purpose

Read this when a `textgenrnn` workflow fails before or after import. Cross-cutting install/import/model-load issues live here; training-only and embedding-only issues stay in their sub-skill troubleshooting files.

## Quick triage

Run the bundled environment helper first if you are unsure whether the runtime is compatible:

```bash
python scripts/check_textgenrnn_env.py --generate --n 1 --max-gen-length 20
```

If that helper fails before generation, use the symptoms below.

## Common failures

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pkg_resources'` | The environment has a setuptools build that no longer exposes `pkg_resources`. | Pin or install a compatible setuptools version such as `setuptools<81`, then rerun the import check. |
| `ModuleNotFoundError: No module named 'tensorflow.compat.v1.keras'` | The environment uses a modern TensorFlow/Keras 3 stack that removed the compatibility surface this repository imports. | Downgrade to a pre-Keras-3 TensorFlow stack, such as TensorFlow/Keras 2.15.x, then rerun the import check. |
| Import works, but model construction or generation fails immediately | The runtime is still missing a compatible TensorFlow/Keras pair or the weights/vocab/config triplet does not match. | Verify the installation guide, then retry with the bundled environment helper and the correct weight/config/vocab files. |
| `FileNotFoundError`, `OSError`, or HDF5 load errors for `weights_path`, `vocab_path`, or `config_path` | The custom model files are missing or do not belong to the same training run. | Recreate or copy the matching HDF5/JSON triplet from the same model prefix. |
| TensorFlow prints CUDA library warnings or shows no GPUs | CUDA runtime libraries are unavailable to the TensorFlow build. | Treat this as optional-backend noise unless the user explicitly needs GPU acceleration. The CPU path is valid for the selected workflows. |
| A generated file cannot be written | Destination parent directory does not exist or is not writable. | Create the directory, choose a writable path, or let the helper create the parent directory. |

## Recovery steps

1. Check the verified stack in [`installation-and-compatibility.md`](installation-and-compatibility.md).
2. Re-run the import check with `python -c "from textgenrnn import textgenrnn; print(textgenrnn.__name__)"`.
3. If the import is still broken, repair the TensorFlow/Keras or setuptools layer before touching package code.
4. For model-file problems, confirm that the custom weights, vocab, and config files were produced by the same scratch-training run.
5. For GPU warnings, decide whether the user actually needs CUDA acceleration. If not, continue on CPU.

## Do not overreact to

- `warnings` about `pkg_resources` deprecation under compatible setuptools.
- TensorFlow CPU feature-guard or missing-CUDA noise when the task does not require GPU acceleration.

## Route-specific failures

- Generation-only sampling issues, output-length questions, and interactive controls belong to the generation sub-skill.
- Tiny-corpus, batch-size, or context/CSV issues belong to the training sub-skill.
- PCA/t-SNE sample-size issues belong to the embedding-analysis sub-skill.
