# Evaluation workflows

## `val.py` command contract

Run in a user-selected writable workspace where the project's `val.py` entry
point and a CUDA-capable environment are available. The entry point is:

```bash
python val.py [all options below]
```

`val.py` calls `cfg.parse_args()`, so the following are the exact parser flags
and defaults in this snapshot. The `-` spelling is intentional.

| Flag | Type | Default | Evaluation relevance |
|---|---|---:|---|
| `-seed` | int | `24` | Parsed but not used by `val.py` itself. |
| `-net` | str | `sam` | Model registry: `sam`, `efficient_sam`, or `mobile_sam`. |
| `-baseline` | str | `unet` | Parsed compatibility option; not used by `val.py`. |
| `-encoder` | str | `default` | Must be valid for the selected `-net`. |
| `-seg_net` | str | `transunet` | Parsed compatibility option; not used by `val.py`. |
| `-mod` | str | `sam_adpt` | `val.py` only enters its evaluation branch for `sam_adpt`. |
| `-exp_name` | str | `msa_test_isic` | Prefix for a new `logs/` output tree. |
| `-type` | str | `map` | Parsed compatibility option. |
| `-vis` | int | `None` | Required in practice: use a positive interval. |
| `-reverse` | bool | `False` | Parsed compatibility option. |
| `-pretrain` | bool | `False` | Parsed compatibility option. |
| `-val_freq` | int | `5` | Parsed but not used by independent `val.py`. |
| `-gpu` | bool | `True` | Enables CUDA model placement when true. |
| `-gpu_device` | int | `0` | CUDA device index used by model and validation tensors. |
| `-sim_gpu` | int | `0` | Parsed compatibility option. |
| `-epoch_ini` | int | `1` | Parsed compatibility option. |
| `-image_size` | int | `256` | Input resize/model image size. |
| `-out_size` | int | `256` | Prediction and target resize size. |
| `-patch_size` | int | `2` | Parsed model compatibility option. |
| `-dim` | int | `512` | Parsed model compatibility option. |
| `-depth` | int | `1` | Parsed model compatibility option. |
| `-heads` | int | `16` | Parsed model compatibility option. |
| `-mlp_dim` | int | `1024` | Parsed model compatibility option. |
| `-w` | int | `4` | Parsed loader option; dataset factory uses its own worker values for most 2D routes. |
| `-b` | int | `2` | Validation loader batch size for most registered 2D routes. |
| `-s` | bool | `True` | Parsed compatibility option. |
| `-warm` | int | `1` | Parsed compatibility option. |
| `-lr` | float | `0.0001` | Parsed compatibility option; no optimizer is created by `val.py`. |
| `-uinch` | int | `1` | Parsed compatibility option. |
| `-imp_lr` | float | `0.0003` | Parsed compatibility option. |
| `-weights` | str | `0` | **Required in practice**; wrapper checkpoint to evaluate. |
| `-base_weights` | str | `0` | Parsed compatibility option. |
| `-sim_weights` | str | `0` | Parsed compatibility option. |
| `-distributed` | str | `none` | Any value other than `none` wraps the model in `DataParallel` and adds `module.` to checkpoint keys. |
| `-dataset` | str | `isic` | Case-sensitive dataset selector. REFUGE's implemented branch is `REFUGE`. |
| `-sam_ckpt` | value | `None` | Base model checkpoint passed to model construction; provide a local compatible file. |
| `-thd` | bool | `False` | Enable 3D slice/chunk handling. |
| `-chunk` | int | `None` | Training crop depth; not the independent validation split size. |
| `-num_sample` | int | `4` | Parsed loader option for 3D training crops. |
| `-roi_size` | int | `96` | Parsed 3D crop/visualization size. |
| `-evl_chunk` | int | `None` | Independent validation depth chunk; `None` means the full available depth. |
| `-mid_dim` | int | `None` | Parsed model compatibility option. |
| `-multimask_output` | int | `1` | Number configured in the original SAM decoder; use `2` for the documented REFUGE route. |
| `-data_path` | str | `../data` | Dataset root, except `val.py` forcibly changes it to `../dataset` for lowercase `refuge`/`refuge2`. |

The parser uses `type=bool` for several flags. In standard `argparse`, a
non-empty string such as `False` is still truthy. Do not assume
`-thd False` or `-gpu False` disables a feature; omit the flag/use the default
or verify the parsed configuration before a run. Dataset names are also case
sensitive: `REFUGE` reaches the two-channel dataset branch, whereas the
lowercase `refuge` special case only changes `data_path` and then does not
match that branch.

A minimally explicit 2D shape of command (the values are examples, not a
weight or data guarantee) is:

```bash
python val.py -net sam -encoder vit_b -mod sam_adpt \
  -weights /path/to/adapter-wrapper.pth \
  -sam_ckpt /path/to/sam-base.pth \
  -dataset isic -data_path /path/to/data \
  -image_size 256 -out_size 256 -vis 50 -gpu_device 0
```

For REFUGE, select the implemented spelling and two output channels:

```bash
python val.py -net sam -encoder vit_b -mod sam_adpt \
  -weights /path/to/refuge-wrapper.pth \
  -sam_ckpt /path/to/sam-base.pth \
  -dataset REFUGE -multimask_output 2 -vis 50
```

Do not copy a command without checking model/output compatibility. The source
`get_network` accepts SAM encoders `default`, `vit_b`, `vit_l`, `vit_h`;
EfficientSAM encoders `default`, `vit_s`, `vit_t`; and MobileSAM encoders
`default`, `vit_h`, `vit_l`, `vit_b`, `tiny_vit`, `efficientvit_l2`,
`PromptGuidedDecoder`, `sam_vit_h`. Actual checkpoint format and required
weights vary by registry.

## What `validation_sam` does

1. Calls `net.eval()`, allocates the CUDA device, and sets the fixed threshold
   tuple `(0.1, 0.3, 0.5, 0.7, 0.9)`.
2. Reads `pack['image']` and `pack['label']`, and uses the supplied `pt` and
   `p_label` unless the sample is 3D or has no point. For 3D it regenerates
   click prompts from the volume and assigns positive point labels.
3. Runs preprocessing, image encoder, prompt encoder, and mask decoder under
   `torch.no_grad()`. Original SAM requests multiple decoder masks when
   `-multimask_output > 1`; EfficientSAM and MobileSAM explicitly request
   `multimask_output=False` in this validation loop.
4. Interpolates predictions to `-out_size`, accumulates the loss, calls
   `eval_seg`, and optionally calls `vis_image`.
5. Returns `(loss_total / dataset_size, metric_tuple_normalized_by_dataset_size)`.
   The first value is a loss-like total, not the IoU or Dice score. For REFUGE,
   `val.py` prints the four metric values with cup/disc labels; see
   [metrics](metrics.md) for channel order and threshold behavior.

Training validation is not an independent reproducibility check: it shares the
in-memory network and loader produced by `train.py`, occurs at configured
points, and uses the current training process. Independent `val.py` makes a
fresh network and loads a saved wrapper, but it still relies on the same
registered dataset factory and preprocessing conventions.

## 3D and chunk controls

The repository's 3D path expects images and labels shaped as `[B,C,H,W,D]`.
For each validation chunk, `validation_sam` slices the last dimension, then
rearranges to `(B*D,C,H,W)`, repeats a single-channel input to three channels,
resizes images to `image_size` and masks to `out_size`, evaluates 2D slices,
and accumulates the results. `-thd True` therefore means slice-wise model
execution, not a native 3D SAM decoder.

- `-chunk` is consumed by the MONAI Decathlon/BTCV **training** random crop
  spatial size `(roi_size, roi_size, chunk)`. It does not set independent
  validation chunking.
- `-evl_chunk N` sets the last-dimension validation slice block to `N`.
  Without it, one block spans the available depth.
- The loop condition is `while buoy + evl_ch <= depth`; a trailing partial
  block is not evaluated. Choose a divisor of the volume depth or record this
  limitation before comparing results.
- The source multiplies each chunk's metrics by the current batch size and
  divides the accumulated result by `dataset_size`. It does not perform a
  separate average over slices/chunks. Chunked and unchunked scores should not
  be assumed mathematically identical.
- `-roi_size` also affects point visualization scaling in 3D; changing it
  without matching the data/crop contract can make overlays misleading.

The registered non-Decathlon 3D classes use external NIfTI, NRRD, or NumPy
volume readers and dataset-specific conventions. Route file names, orientation,
labels, and sample validation to [data preparation](../../data-preparation/).

## Logs and visualizations

After loading the checkpoint, `val.py` calls `set_log_dir('logs', exp_name)`
and creates a fresh timestamped tree relative to the working directory:

```text
logs/<exp_name>_<YYYY_MM_DD_HH_MM_SS>/
├── Model/
├── Log/
└── Samples/
```

The independent evaluator writes a timestamped log file beneath `Log/` via
`create_logger` and sends the metric summary to that logger/console. It does
not reuse the checkpoint's stored `path_helper` (the corresponding assignment
is commented out in `val.py`). Visualization files are written beneath
`Samples/` with names beginning `Test`, a small set of sample names, and
`epoch+<epoch>.jpg`.

`vis_image` shows at most four items per row. For one channel it composes input,
prediction, and ground truth. For two channels it composes input, both channel
predictions, and both channel targets. For more than two channels it composes
input, every channel prediction, then every channel target. Predictions are
sigmoided for display when outside `[0,1]`. Visualization requires the
project's torchvision image utilities and compatible optional plotting/image
packages; absent dependencies should be diagnosed rather than silently treated
as a metric failure. This route does not provide a visualization-free wrapper
around `val.py`; use the helper only for checkpoint inspection.
