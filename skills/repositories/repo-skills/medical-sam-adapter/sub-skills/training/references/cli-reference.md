# Training CLI reference

`train.py` and `val.py` both call `cfg.parse_args()`. The table below is the
complete option set in `cfg.py` for this source snapshot. Flags use one dash,
and option names are case-sensitive. The defaults are parser defaults, not a
promise that the resulting run is safe.

## Exact parser options

| Flag | `type` in `cfg.py` | Default | Source meaning / operational note |
|---|---|---:|---|
| `-seed` | `int` | `24` | Random seed. |
| `-net` | `str` | `sam` | Network family passed to `get_network`: `sam`, `efficient_sam`, or `mobile_sam`. |
| `-baseline` | `str` | `unet` | Legacy baseline label; it does not select the SAM registry. |
| `-encoder` | `str` | `default` | Case-sensitive registry key; valid values depend on `-net`. |
| `-seg_net` | `str` | `transunet` | Legacy segmentation label; not the SAM registry selector. |
| `-mod` | `str` | `sam_adpt` | Mode string. The documented modes are `sam_adpt`, `sam_lora`, and `sam_adalora`; other strings use a full-image-encoder fallback. |
| `-exp_name` | `str` | `msa_test_isic` | Experiment name used to create a timestamped directory below `logs/`. |
| `-type` | `str` | `map` | Legacy condition type; help text mentions `ave`, `rand`, and `rand_map`. |
| `-vis` | `int` | `None` | Visualization interval in batches. `None` is unsafe once validation evaluates `ind % args.vis`; pass a positive integer. |
| `-reverse` | `bool` | `False` | Legacy adversary-reverse switch. It is parsed with Python `bool`. |
| `-pretrain` | `bool` | `False` | Declared as bool but passed to `torch.load` as though it were a path when truthy; this is not a usable path interface. |
| `-val_freq` | `int` | `5` | Post-training validation interval in epochs. Use a positive value. |
| `-gpu` | `bool` | `True` | Whether `get_network` performs GPU placement. False does not make the loop CPU-safe. |
| `-gpu_device` | `int` | `0` | CUDA device index used for model/data/checkpoint placement. |
| `-sim_gpu` | `int` | `0` | Legacy similarity GPU selector; not the main training device. |
| `-epoch_ini` | `int` | `1` | Start-epoch field; the shown training loop does not use it to restore state. |
| `-image_size` | `int` | `256` | Square model input size. SAM-style builders derive the embedding grid from this value. |
| `-out_size` | `int` | `256` | Square target/prediction resize used before the loss and metrics. |
| `-patch_size` | `int` | `2` | Legacy model setting; SAM builders use their own patch size. |
| `-dim` | `int` | `512` | Legacy transformer dimension. |
| `-depth` | `int` | `1` | Legacy transformer depth. |
| `-heads` | `int` | `16` | Legacy transformer head count. |
| `-mlp_dim` | `int` | `1024` | Legacy transformer MLP width. |
| `-w` | `int` | `4` | Dataloader worker count supplied by the parser; built-in loaders may set their own values. |
| `-b` | `int` | `2` | Dataloader batch size. In 3D this is the loader batch before slices are flattened. |
| `-s` | `bool` | `True` | Dataset shuffle switch; parsed with Python `bool`, so text `False` is truthy. |
| `-warm` | `int` | `1` | Legacy warm-up setting; not used by the main SAM loop. |
| `-lr` | `float` | `1e-4` | Adam learning rate. |
| `-uinch` | `int` | `1` | Legacy U-Net input-channel setting. |
| `-imp_lr` | `float` | `3e-4` | Legacy implicit-model learning rate. |
| `-weights` | `str` | `0` (integer object when omitted) | Existing training-wrapper checkpoint for warm start/resume. The value is a string only when supplied. |
| `-base_weights` | `str` | `0` | Legacy baseline weights. |
| `-sim_weights` | `str` | `0` | Legacy similarity weights. |
| `-distributed` | `str` | `none` | Comma-separated CUDA IDs for `torch.nn.DataParallel`; `none` uses the single-device path. |
| `-dataset` | `str` | `isic` | Case-sensitive dataset dispatcher key. Confirm the exact key with data preparation. |
| `-sam_ckpt` | implicit string | `None` | Local base-model checkpoint passed to the selected model builder. It has no explicit `type`, so supplied values are argparse strings. |
| `-thd` | `bool` | `False` | 3D mode. Parsed with Python `bool`; omit it for 2D rather than writing `-thd False`. |
| `-chunk` | `int` | `None` | 3D training crop depth; required in practice by the MONAI crop transform. |
| `-num_sample` | `int` | `4` | Number of positive/negative MONAI crops per source volume. |
| `-roi_size` | `int` | `96` | 3D in-plane crop size; the crop is `(roi_size, roi_size, chunk)`. |
| `-evl_chunk` | `int` | `None` | 3D validation depth window. None means the source volume depth. |
| `-mid_dim` | `int` | `None` | Adapter bottleneck width or LoRA/AdaLoRA rank, depending on the constructed block. |
| `-multimask_output` | `int` | `1` | Number of masks requested by the original SAM branch; the README uses `2` for REFUGE. |
| `-data_path` | `str` | `../data` | Dataset root passed to the dispatcher. Always make the user-selected root explicit. |

## The `type=bool` trap

`argparse` applies `bool()` to a supplied string. Therefore `bool("False")`
is `True`. In this parser all of the following are truthy when written with a
value of `False`:

```text
-thd False       # can enter the 3D branch
-gpu False       # still does not avoid CUDA operations
-s False         # still enables the truthy shuffle value
-pretrain False  # becomes True, then is used as a torch.load argument
```

For a false value, omit the option when its default is false. For a true value,
use an explicitly recorded command and verify the effective configuration. The
source does not provide a `store_true`/`store_false` alternative. A wrapper may
normalize booleans only if it reports the normalized command and does not claim
that the original parser semantics changed.

## Construction rules

- Keep `-sam_ckpt` and `-weights` separate. The former initializes a selected
  base builder; the latter is a saved experiment wrapper.
- `-image_size` controls model input construction. `-out_size` controls the
  resized prediction/target. Changing either is a memory or shape decision,
  not a label conversion.
- Lower `-b` and `-image_size` for 2D memory pressure. For 3D, lower `-b`,
  `-chunk`, `-num_sample`, `-roi_size`, and independently `-evl_chunk`.
- Set `-vis` to a positive integer. The default `None` can fail in the
  validation path even when training visualization is not desired.
- Training's dispatcher uses exact names such as `isic`, `REFUGE`, `DDTI`,
  `WBC`, `STARE`, `pendal`, `Brat`, `kits`, `atlas`, `lnq`, `segrap`,
  `toothfairy`, and `decathlon`; use the data-preparation route for the full
  case-sensitive registry and layout contract. Evaluation has a separate
  lowercase `refuge`/`refuge2` special case.

## Safe parser check

These checks do not start training and do not download anything:

```bash
python scripts/inspect_model_registry.py --help
python scripts/inspect_model_registry.py --net mobile_sam --encoder tiny_vit --mod sam_lora
python train.py --help
```

`train.py --help` is only a parser check. The imported training stack and actual
loop still require CUDA, optional packages, local data, and compatible local
weights. See [workflows](workflows.md) for commands with no download step.
