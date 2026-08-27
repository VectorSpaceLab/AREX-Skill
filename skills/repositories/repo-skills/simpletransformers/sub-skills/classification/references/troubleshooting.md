# Classification Troubleshooting

## Transformers compatibility import errors

Symptoms:

- `ImportError: cannot import name 'XLNetSequenceSummary'`
- `ImportError: cannot import name 'XLMSequenceSummary'`
- `ImportError: cannot import name 'FlaubertSequenceSummary'`
- MMBT/deprecated module import failures before `ClassificationModel` is constructed.

Likely cause: Simple Transformers 0.70.8 imports aliases that are missing or moved in modern Hugging Face Transformers versions. The package metadata only declares `transformers>=4.31.0`, so pip can install a version that satisfies metadata but still breaks runtime imports.

Recovery:

1. Confirm the error happens on import before touching the dataset.
2. Check the installed `simpletransformers`, `transformers`, and `torch` versions.
3. Try a package version or repo refresh that has patched these imports. If the current checkout is fixed, refresh this skill.
4. If the user controls the environment and only needs non-XLM/XLNet branches, they may apply a local compatibility patch, but record it as environment-specific and avoid publishing it as general package truth.
5. Do not mark classification verification complete until the target environment imports the selected model class cleanly.

## CUDA surprise or CPU-only execution

Constructors default to `use_cuda=True`. On CPU hosts this can raise CUDA/device errors or run slowly while probing devices.

Use `use_cuda=False` for schema checks, CPU tests, and reproducible minimal examples. Only enable CUDA after verifying a compatible PyTorch CUDA build and available GPU memory.

## Stale cached features

Symptoms: labels or max sequence length changes but training appears to reuse old features.

Set `reprocess_input_data=True`, change/clear `cache_dir` or `dataset_cache_dir`, and use a unique `output_dir` while debugging.

## Output directory overwrite errors

If an output directory already exists, set `overwrite_output_dir=True` only when the user accepts overwriting. For production experiments, choose a new run-specific directory instead.

## Multi-label labels loaded as strings

Symptoms: label vectors look like `'[1, 0, 1]'`, evaluation dimensions mismatch, or thresholds behave strangely.

Parse labels to Python lists before model calls and validate with:

```bash
python scripts/validate_classification_data.py --task multilabel --input data.jsonl --num-labels 3
```

## LayoutLM bounding-box failures

Symptoms: indexing errors, shape mismatch, or poor model behavior with document text.

Check that every row's coordinate lists have the same length as `text.split()`, values are integers in `0..1000`, and `x0 <= x1`, `y0 <= y1`.

## Multimodal image failures

Symptoms: file-not-found, PIL decode errors, or image encoder import issues.

Validate paths with `--check-image-exists`, confirm `image_path` is the directory used by the model call, and test the image reader independently before training. Treat MMBT/deprecated Transformers import errors as dependency/version problems, not missing image files.

## ONNX conversion failures

ONNX export requires optional ONNX/ONNX Runtime dependencies and compatible model/tokenizer types. First verify normal PyTorch prediction, then install export dependencies and rerun export on a small model. If an ONNX runtime provider is requested, check provider availability separately.

## Full native tests are slow

Repo-native classification examples and tests train Hugging Face models and may download checkpoints. Use them only with user-approved network/cache/compute budget. For ordinary skill verification, combine schema validators, import checks, and a single focused native import test when dependencies are compatible.
