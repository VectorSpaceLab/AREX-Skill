# CLI reference

Run the bundled `validate_inference_inputs.py` preflight first. For actual
execution, set `GEOSEG_CHECKOUT` to the user-supplied GeoSeg checkout and call
the root bundled wrapper. The wrapper changes into that checkout, forwards the
original CLI flags unchanged, and avoids making the current directory an
implicit dependency. The checkout contains no packaging metadata. Use `python`
from the prepared Python 3.8/CUDA environment.

```bash
export GEOSEG_CHECKOUT=/path/to/GeoSeg
export GEOSEG_SKILL=/path/to/this/skill
```

## Benchmark tile evaluators

All three evaluators require `-c/--config_path` and
`-o/--output_path`, accept `-t/--tta` with choices `lr` and `d4` (default is
no TTA when the flag is omitted), and accept `--rgb` for colorized PNG masks.
The source parser exposes `None` as an internal choice, but the shell-safe way
to request it is to omit `-t`, not to pass the string `None`.

```bash
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root "$GEOSEG_CHECKOUT" vaihingen_test.py \
  -c config/vaihingen/dcswin.py \
  -o fig_results/vaihingen/dcswin \
  --rgb -t d4

python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root "$GEOSEG_CHECKOUT" potsdam_test.py \
  -c config/potsdam/dcswin.py \
  -o fig_results/potsdam/dcswin \
  --rgb -t lr

python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root "$GEOSEG_CHECKOUT" loveda_test.py \
  -c config/loveda/dcswin.py \
  -o fig_results/loveda/dcswin_test \
  -t d4
```

`loveda_test.py` additionally exposes `--val`. Without `--val`, it predicts
`config.test_dataset` (LoveDA `Test`) and does not calculate metrics. With
`--val`, it uses `config.val_dataset` (the `Val` Urban/Rural tree), creates
`<output>/Urban` and `<output>/Rural`, and prints per-class F1/IoU plus aggregate
F1, mIoU, and OA. Because `geoseg.datasets.loveda_dataset` constructs
`loveda_val_dataset` at import time, the LoveDA validation directory must exist
for config import even when only test prediction was intended.

Vaihingen and Potsdam always evaluate their configured test dataset and print
per-class F1/IoU plus aggregate F1, mIoU, and OA. Their aggregate means exclude
the final class (`[:-1]` in the scripts); retain that distinction when
comparing numbers with LoveDA.

## UAVid sequence inference

```bash
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root "$GEOSEG_CHECKOUT" inference_uavid.py \
  -i data/uavid/uavid_test \
  -c config/uavid/unetformer.py \
  -o fig_results/uavid/unetformer_r18 \
  -t lr -ph 1152 -pw 1024 -b 2 -d uavid
```

Flags:

| Flag | Default | Meaning |
|---|---:|---|
| `-i`, `--image_path` | `data/uavid/uavid_test` | Sequence root; each sequence must contain `Images/`. |
| `-c`, `--config_path` | required | Python config used to build the model and locate the checkpoint. |
| `-o`, `--output_path` | required | Root under which sequence `Labels/` folders are created. |
| `-t`, `--tta` | `lr` | `lr`, `d4`, or no TTA if omitted/explicit parser default. |
| `-ph`, `--patch-height` | `1152` | Tile height used for padding and inference. |
| `-pw`, `--patch-width` | `1024` | Tile width used for padding and inference. |
| `-b`, `--batch-size` | `2` | Inference batch size; lower it on CUDA OOM. |
| `-d`, `--dataset` | `uavid` | Output mapping choice: `pv`, `landcoverai`, or `uavid`; use `uavid` for UAVid. |

The source calls `model.cuda(config.gpus[0])`, unlike the other inference
script's plain `model.cuda()`. The stock configs document `gpus='auto'` for
Lightning training, so inspect this field before UAVid inference: use a
configuration whose `gpus` is indexable and selects the intended CUDA device
(for example, a single-device list such as `[0]`) if the stock value is not
accepted by the installed runtime.

## Huge-image inference

```bash
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" \
  --repo-root "$GEOSEG_CHECKOUT" inference_huge_image.py \
  -i data/vaihingen/test_images \
  -c config/vaihingen/dcswin.py \
  -o fig_results/vaihingen/dcswin_huge \
  -t lr -ph 512 -pw 512 -b 2 -d pv
```

Flags are the same shape as UAVid, except:

| Flag | Default | Meaning |
|---|---:|---|
| `-i`, `--image_path` | required | Flat folder scanned for `.tif`, `.png`, and `.jpg`. |
| `-t`, `--tta` | no TTA | `lr`, `d4`, or omitted. |
| `-ph`, `--patch-height` | `512` | Tile height. |
| `-pw`, `--patch-width` | `512` | Tile width. |
| `-b`, `--batch-size` | `2` | Inference batch size. |
| `-d`, `--dataset` | `pv` | `pv`, `landcoverai`, `uavid`, or `building`; selects RGB conversion. |

Huge-image output has the same basename as each input in the output root. It
is always color-converted for the supported dataset choices; there is no
`--rgb` switch and no explicit indexed-output switch in this script.

## Help-only smoke checks

These are safe parser/import checks and do not require a dataset or checkpoint
because argparse exits on `--help` before model construction:

```bash
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" --repo-root "$GEOSEG_CHECKOUT" train_supervision.py --help
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" --repo-root "$GEOSEG_CHECKOUT" vaihingen_test.py --help
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" --repo-root "$GEOSEG_CHECKOUT" potsdam_test.py --help
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" --repo-root "$GEOSEG_CHECKOUT" loveda_test.py --help
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" --repo-root "$GEOSEG_CHECKOUT" inference_uavid.py --help
python "$GEOSEG_SKILL/scripts/run_geoseg_entrypoint.py" --repo-root "$GEOSEG_CHECKOUT" inference_huge_image.py --help
```

They do not replace a CUDA run with real data. `PyramidMamba` remains outside
this verified path because `mamba_ssm` is optional and unverified.
