# BAText / ABCNet text spotting workflows

AdelaiDet's text spotting support is centered around BAText/ABCNet configs, Bezier annotations, BezierAlign pooling, and text-specific evaluation.

## Config selection

Start under `configs/BAText/`. Inspect the family README and YAML for:

- `MODEL.META_ARCHITECTURE`
- `MODEL.BATEXT.*`
- `MODEL.ROI_HEADS` / text head settings
- Dataset names in `DATASETS.TRAIN` and `DATASETS.TEST`
- `MODEL.WEIGHTS` and output directory
- Dictionary or lexicon paths, especially `MODEL.BATEXT.CUSTOM_DICT`

## Training/evaluation launch

Use the train-eval wrapper, then add text-specific overrides after `--opts`:

```bash
python ../train-eval/scripts/run_train_eval.py --repo-root /path/to/AdelaiDet \
  --config configs/BAText/attn_R_50.yaml \
  --num-gpus 4 \
  --opts OUTPUT_DIR output/batext MODEL.BATEXT.CUSTOM_DICT /path/to/dict.txt
```

Evaluation-only is the same route with `--eval-only --model-weights /path/to/model.pth`.

## Demo visualization

Use `demo-visualize` for rendering:

```bash
python ../demo-visualize/scripts/run_demo.py --repo-root /path/to/AdelaiDet \
  --config configs/BAText/attn_R_50.yaml \
  --weights /path/to/model.pth \
  --input sample.jpg --output output/text-demo \
  --opts MODEL.BATEXT.CUSTOM_DICT /path/to/dict.txt
```

If detections appear but recognized strings are wrong, stay in this text route and inspect dictionaries, lexicons, transcription normalization, and benchmark protocol.

## BezierAlign setup dependency

Text pooling uses `adet.layers.BezierAlign`, backed by `adet._C.bezier_align_forward/backward`. Before text training/demo, run:

```bash
python ../../scripts/check_install.py --cuda-ops
```

A failure in BezierAlign or `adet._C` is a setup-build blocker.

## Evaluation protocol cautions

Text spotting numbers can vary based on:

- Generic/weak/strong lexicon selection.
- Dictionary file contents and casing.
- Whether illegible/do-not-care words are filtered.
- Transcription normalization.
- Exact benchmark split and annotation format.

Record these choices whenever reporting or comparing results.
