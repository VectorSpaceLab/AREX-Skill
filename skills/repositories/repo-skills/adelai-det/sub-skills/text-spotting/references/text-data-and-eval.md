# Text data and evaluation

## Annotation expectations

Text spotting is not box-only detection. Dataset records need enough information for detection and recognition:

- Image path and size.
- Text region geometry, often Bezier/control-point representation.
- Transcription string.
- Legibility/do-not-care flags according to the benchmark.
- Category/class metadata expected by the config.

`adet.data.datasets.text` and related mappers parse text annotations into structures used by BAText/ABCNet. If a custom dataset starts as COCO boxes only, add text transcriptions and Bezier-compatible geometry before using text configs.

## Dictionary and lexicon inputs

`MODEL.BATEXT.CUSTOM_DICT` can point to a custom dictionary. Benchmark evaluation may also use lexicons external to the config. Keep these explicit:

```bash
--opts MODEL.BATEXT.CUSTOM_DICT /path/to/custom_dict.txt
```

When comparing results, record:

- Dictionary file path/version.
- Lexicon protocol: none/generic/weak/strong or benchmark-specific.
- Whether transcriptions are lowercased/uppercased/filtered.
- Any ignored words/regions.

## TextEvaluator dependencies

The source text evaluator imports `rapidfuzz.string_metric`, which is available in rapidfuzz 2.x but removed in rapidfuzz 3.x. If evaluator import fails, use:

```bash
python -m pip install 'rapidfuzz<3'
```

## Common failure patterns

| Symptom | Likely issue | Fix |
| --- | --- | --- |
| BezierAlign import/op fails | `adet._C` not built with CUDA or wrong PyTorch stack. | Use `setup-build`; rerun `check_install.py --cuda-ops`. |
| Training loads but recognition loss is wrong/NaN | Text labels or dictionary mismatch. | Inspect annotation transcriptions and dictionary coverage. |
| Evaluation import fails at rapidfuzz | rapidfuzz 3.x installed. | Pin `rapidfuzz<3`. |
| Detections draw but text is empty | Recognition branch disabled/misconfigured or missing dictionary. | Inspect `MODEL.BATEXT` keys and weights/config match. |
| Reported numbers differ from paper/model zoo | Different lexicon/protocol/split. | Recreate the benchmark-specific protocol before comparing. |

## Cross-routes

- Use `data-prep` to create or validate text annotations.
- Use `demo-visualize` to render text predictions.
- Use `train-eval` to launch text training/evaluation after text inputs are validated.
