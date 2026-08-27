# Config reference

## Loader behavior

- YAML files are parsed with `yaml.SafeLoader`.
- Scalar strings are converted with literal parsing when possible.
- The bundled runner applies overrides as literal values, not arbitrary Python expressions.
- Override paths use dots for nested dicts and numeric segments for list indices.
- Override targets must already exist in the loaded config.

## Top-level runtime keys

| Key | Meaning | Trainer effect |
| --- | --- | --- |
| `epochs` | Epoch-based training length | Enables epoch mode; the trainer derives `total_iters` from `epochs * iters_per_epoch`. |
| `total_iters` | Iteration-based training length | Used when `epochs` is absent. |
| `output_dir` | Output root | The runner appends `<config-stem>-<timestamp>` under this path. |
| `snapshot_config.interval` | Checkpoint cadence | In epoch mode, the trainer multiplies it by `iters_per_epoch`; otherwise it is iteration-based. |
| `log_config.interval` | Log cadence | Iteration-based. |
| `log_config.visiual_interval` | Image cadence | Iteration-based; keep the repo spelling. |
| `validate.interval` | Validation cadence | Iteration-based. |
| `validate.save_img` | Save validation images | Controls `visual_test/` writes. |
| `validate.metrics` | Validation metrics | Built by the metric registry. |
| `enable_visualdl` | VisualDL toggle | Enables a writer under the output directory. |
| `find_unused_parameters` | Distributed wrapping hint | Passed to `paddle.DataParallel`. |
| `model.max_eval_steps` | Validation cap | Limits the number of steps in `test()`. |

## Registry-backed blocks

| Config block | Registry | How it resolves |
| --- | --- | --- |
| `model.name` | `MODELS` | `ppgan.models.builder.build_model` looks up the class by name and passes the remaining keys into the constructor. |
| `dataset.*.name` | `DATASETS` | `ppgan.datasets.builder.build_dataset` resolves the class name, except for `RepeatDataset`, which wraps a nested `dataset` block. |
| `validate.metrics.*.name` | `METRICS` | `ppgan.models.BaseModel.setup_metrics` builds each metric from its `name`. |
| `optimizer.*.name` | `OPTIMIZERS` | `ppgan.solver.builder.build_optimizer` resolves the optimizer class. |
| `lr_scheduler.name` | `LRSCHEDULERS` | `ppgan.solver.builder.build_lr_scheduler` resolves the scheduler class. |

If a `name` is not registered, the trainer raises a registry lookup error before any training work starts.

## Representative names from inspected configs

| Config | `model.name` | `dataset.train.name` | `dataset.test.name` | Metric examples |
| --- | --- | --- | --- | --- |
| `configs/cyclegan_cityscapes.yaml` | `CycleGANModel` | `UnpairedDataset` | `UnpairedDataset` | none in the sample config |
| `configs/pix2pix_cityscapes.yaml` | `Pix2PixModel` | `PairedDataset` | `PairedDataset` | `FID` |
| `configs/basicvsr_reds.yaml` | `BasicVSRModel` | `RepeatDataset` wrapping `VSRREDSMultipleGTDataset` | `VSRREDSMultipleGTDataset` | `PSNR`, `SSIM` |
| `configs/stylegan_v2_256_ffhq.yaml` | `StyleGAN2Model` | `SingleDataset` | `SingleDataset` | `FID` |
| `configs/wav2lip.yaml` | `Wav2LipModel` | `Wav2LipDataset` | `Wav2LipDataset` | no validation metric block in the sample config |

## Registry name examples

### Models
`CycleGANModel`, `Pix2PixModel`, `BasicVSRModel`, `StyleGAN2Model`, `Wav2LipModel`, `ESRGAN`, `EDVRModel`, `RCANModel`, `PReNetModel`, `SwinIRModel`, `InvDNModel`, `NAFNetModel`, `GFPGANModel`, `GPENModel`, `AOTGANModel`.

### Datasets
`UnpairedDataset`, `PairedDataset`, `SingleDataset`, `RepeatDataset`, `VSRREDSMultipleGTDataset`, `VSRVimeo90KDataset`, `Wav2LipDataset`, `GPENDataset`, `FFHQDegradationDataset`, `AOTGANDataset`, `NAFNetTrain` / `NAFNetVal` / `NAFNetTest`.

### Metrics
`FID`, `PSNR`, `SSIM`, `LPIPSMetric`.

### Optimizers and schedulers
`Adam`, `SGD`, `Momentum`, `RMSProp`, `AdamW`, `MultiStepDecay`, `LinearDecay`, `NonLinearDecay`, `CosineAnnealingRestartLR`.

## Override syntax

Dotted paths always start from the loaded config root.
Examples:

```bash
-o dataset.train.dataroot_a=/data/trainA dataset.train.dataroot_b=/data/trainB
-o dataset.train.batch_size=4 dataset.test.batch_size=4
-o model.max_eval_steps=1000
-o validate.metrics.fid.batch_size=16
-o optimizer.optimG.beta1=0.0 optimizer.optimD.beta1=0.0
```

List indices are zero-based:

```bash
-o dataset.train.preprocess.2.pipeline.0.size='[286, 286]'
```

## Special patterns

- `RepeatDataset` wraps another dataset block and repeats it `times` times.
- Multi-optimizer configs use nested blocks such as `optimG` and `optimD`; each sub-block needs a `name` and `net_names` list.
- `validate.metrics` can be a single metric dict or a mapping of named metric dicts.
- `FID` may fetch the InceptionV3 weights the first time it runs unless `premodel_path` is already set.
- `checkpoints_dir` appears in some YAML files, but the generic training runner reads `output_dir` for its own artifacts.
