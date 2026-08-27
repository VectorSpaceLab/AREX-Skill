# Encrypted DistilBERT Troubleshooting

## Model loading

| Symptom | Likely cause | Fix |
|---|---|---|
| `OSError: Can't load tokenizer` | Missing tokenizer files or wrong directory. | Run `scripts/validate_model_dir.py`; provide a directory with tokenizer config and tokenizer artifacts. |
| `OSError: Error no file named model.safetensors...` | Model weights are absent. | Download or point to a complete model directory; do not expect the generated skill to include weights. |
| Model loads from the network unexpectedly | A model id was passed instead of a local path, or files are not cached. | Ask whether network/cache use is allowed; otherwise provide a local model path. |
| Output labels are numeric or unexpected | Config lacks the expected `id2label` mapping. | Inspect `model.config.id2label` and report the actual mapping. |

## Dependency failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: torch` | PyTorch is not installed. | Install a CPU or GPU torch build suitable for the user's machine. |
| `ImportError` from Transformers about missing backends | `transformers` is installed without PyTorch. | Install PyTorch first, then rerun the import check. |
| NumPy ABI warning from torch | NumPy 2.x with an older torch build. | Use `numpy==1.26.*` for the repo-tested stack, or align torch/NumPy versions together. |

## Runtime behavior

| Symptom | Likely cause | Fix |
|---|---|---|
| CPU run is slow | CPU-only PyTorch and model load overhead. | For this small demo, wait or use GPU if already verified; do not install GPU stacks just for one tiny run unless requested. |
| Scores differ from plaintext DistilBERT | The public encrypted model is approximate and tokenization differs. | Report the comparison setup and do not treat small score changes as a script error. |
| Prompt with unusual characters behaves oddly | Tokenizer normalization and encrypted vocabulary mapping. | Test with a short ASCII prompt first, then isolate the character that changes behavior. |

## Reporting checklist

When a user asks for help, include:

- model source: local path or HF id;
- whether network access was used;
- installed versions of `torch` and `transformers`;
- tokenizer files found by the validator;
- raw exception text if loading failed; and
- actual `id2label` mapping if inference ran.
