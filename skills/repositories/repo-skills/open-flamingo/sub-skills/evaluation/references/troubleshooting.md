# Troubleshooting

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `ModuleNotFoundError: sklearn` or an import failure around `roc_auc_score` | `evaluate.py` imports `sklearn.metrics`, but the package metadata's eval extra omits `scikit-learn`. | Install `requirements-eval.txt` or add `scikit-learn` explicitly before running `evaluate.py`. |
| `LookupError` for `wordnet`, `punkt`, or `averaged_perceptron_tagger` | NLTK corpora for OK-VQA postprocessing are missing. | Download the NLTK resources used by `WordNetLemmatizer`, tokenization, and POS tagging. |
| `ModuleNotFoundError: pycocoevalcap` | Caption metrics are missing. | Install the caption-evaluation dependencies before evaluating COCO or Flickr30K. |
| `ModuleNotFoundError: open_clip` | RICES caching needs the OpenCLIP package. | Install `open_clip_torch` before running the cache script. |
| `ModuleNotFoundError: utils` from cache-RICES | The packaged RICES module imports `utils` without a package prefix. | Use this sub-skill's bundled `scripts/run_cache_rices_entrypoint.py` wrapper or the command builder; the wrapper fixes the evaluation import path before execution. |
| `evaluate.py --help` fails before showing arguments | The module imports metric and dataset helpers at import time, so missing eval dependencies stop help generation. | Fix the missing dependencies first, then rerun the help command. |
| `401` or `403` from Hugging Face checkpoint download | Missing or invalid Hugging Face token, or an inaccessible checkpoint repo. | Set a valid token and pre-download the checkpoint locally before evaluation. |
| DDP hangs, times out, or picks the wrong GPU | Launcher env vars are missing or the backend does not match the launch method. | Set `MASTER_ADDR`, `MASTER_PORT`, `WORLD_SIZE`, `RANK`, and `LOCAL_RANK`, or launch with `torchrun`. Use `--no-set-device-rank` when device assignment is already pinned. |
| VQAv2 / VizWiz test-dev cannot be scored locally | Those splits may not have local annotations. | Run the fill workflow to expand the partial results JSON into a submission-ready file. |
| `FileNotFoundError` for `coco.pkl`, `vqav2.pkl`, or other RICES caches | The cached demonstration feature directory is missing or incomplete. | Re-run the cache script for the missing implemented dataset or omit `--cached_demonstration_features` to recompute features on the fly. |
| ImageNet cache command is rejected or `imagenet.pkl` is absent | The cache script parses ImageNet flags but does not implement an ImageNet save branch. | Use evaluation-time RICES recomputation for ImageNet or provide a compatible `imagenet.pkl` by another verified process. |
| `transformers` refuses the installed torch version or numpy errors appear | Version pin drift. | Use the known-compatible window: `torch==2.0.1`, `transformers==4.31.0`, and `numpy<2`. |
| Path errors for VQAv2 / OK-VQA images | The image directory does not end in the expected COCO split name. | Use `train2014`, `val2014`, or `test2015` directories so the filename formatter resolves correctly. |

## Quick recovery checklist

1. Verify the eval dependencies listed above.
2. Confirm the dataset-specific path bundle.
3. Confirm the checkpoint and tokenizer paths.
4. Check the distributed launcher environment.
5. If using RICES, confirm the dataset-specific pickle names in the cache directory.
