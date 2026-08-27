# Configuration reference

Torchreid's unified interface uses a YACS-style configuration tree. Command-line overrides are dotted key/value pairs appended after regular arguments. This reference lists the relevant keys and safe editing patterns.

## Dotted override rules

- Use exact dotted names, e.g. `model.name`, `data.save_dir`, `test.evaluate`.
- Values are parsed by YACS from strings. Use `True`/`False` for booleans, numbers for numeric values, and shell-quoted list literals for lists.
- For CLI-style sources, targets, root, and transforms, prefer top-level options when available: `--root`, `--source`, `--target`, `--transforms`. The helper converts these into `data.*` entries.
- Put every override as a pair: `KEY VALUE`. A missing value or misspelled key fails during config merge.
- For list values in a shell, quote the whole literal: `train.stepsize '[60, 120]'`, `train.open_layers "['fc', 'classifier']"`, `test.ranks '[1, 5, 10, 20]'`.

Example evaluation opts that must appear together:

```text
model.load_weights /path/to/model.pth.tar
test.evaluate True
test.visrank True
data.save_dir log/eval_market1501
```

`test.visrank True` without `test.evaluate True` is invalid because `Engine.run` rejects visrank during training.

## Default config tree

| Section | Key | Default | Meaning |
| --- | --- | --- | --- |
| `model` | `name` | `resnet50` | Model architecture key. Common choices here: `osnet_x1_0`, `osnet_x0_75`, `osnet_x0_5`, `osnet_x0_25`, `osnet_ibn_x1_0`, `osnet_ain_x1_0`, `resnet50`, `resnet50_fc512`. |
| `model` | `pretrained` | `True` | Load ImageNet/pretrained weights if available; may trigger a download for some model keys. Set `False` for no-download smoke checks or strict offline runs. |
| `model` | `load_weights` | empty | Path to weights to load before train/eval; used for test-only evaluation and fine-tuning. |
| `model` | `resume` | empty | Path to checkpoint with optimizer/scheduler state for resuming training. |
| `data` | `type` | `image` | `image` uses `ImageDataManager`; `video` uses `VideoDataManager`. |
| `data` | `root` | `reid-data` | Parent directory containing dataset folders. |
| `data` | `sources` | `['market1501']` | Training source dataset key(s). |
| `data` | `targets` | `['market1501']` | Evaluation target dataset key(s). Defaults to sources if omitted in API constructors. |
| `data` | `workers` | `4` | DataLoader workers. Use `0` or `1` when multiprocessing hangs. |
| `data` | `split_id` | `0` | 0-based split index. Fixed-split datasets usually use 0. |
| `data` | `height`, `width` | `256`, `128` | Input image size. |
| `data` | `combineall` | `False` | Adds query/gallery identities into training for supported datasets. |
| `data` | `transforms` | `['random_flip']` | Training augmentation list. Test transform is resize + tensor + normalization. |
| `data` | `k_tfm` | `1` | Number of independent augmentations per image; image train data only. |
| `data` | `norm_mean`, `norm_std` | ImageNet values | Channel normalization. Use bundled mean/std helper for dataset-specific values. |
| `data` | `save_dir` | `log` | Directory for logs, checkpoints, TensorBoard files, and visrank outputs. |
| `data` | `load_train_targets` | `False` | Build target training loader for domain adaptation; sources/targets must not overlap. |
| `market1501` | `use_500k_distractors` | `False` | Add Market1501 500K distractors if locally available. |
| `cuhk03` | `labeled_images` | `False` | Use labeled images instead of detected images. |
| `cuhk03` | `classic_split` | `False` | Use original 20 classic splits instead of new 767/700 split. |
| `cuhk03` | `use_metric_cuhk03` | `False` | Use CUHK03 single-gallery-shot metric; usually pair with `classic_split True`. |
| `sampler` | `train_sampler` | `RandomSampler` | Source train sampler. Triplet workflows usually require `RandomIdentitySampler`. |
| `sampler` | `train_sampler_t` | `RandomSampler` | Target train sampler when `load_train_targets=True`. |
| `sampler` | `num_instances` | `4` | Instances per identity for identity sampler. |
| `sampler` | `num_cams` | `1` | Number of cameras/domains sampled per batch for domain sampler. |
| `sampler` | `num_datasets` | `1` | Number of datasets sampled per batch for dataset sampler. |
| `video` | `seq_len` | `15` | Frames sampled per tracklet. |
| `video` | `sample_method` | `evenly` | `evenly`, `random`, or `all`. `all` requires batch size 1. |
| `video` | `pooling_method` | `avg` | Tracklet feature pooling: `avg` or `max`. |
| `train` | `optim` | `adam` | Optimizer: `adam`, `amsgrad`, `sgd`, `rmsprop`, `radam`. |
| `train` | `lr` | `0.0003` | Base learning rate. |
| `train` | `weight_decay` | `5e-4` | L2 penalty. |
| `train` | `max_epoch` | `60` | Total epochs. |
| `train` | `start_epoch` | `0` | Usually set by resume. |
| `train` | `batch_size` | `32` | Training batch size or tracklet batch size for video. |
| `train` | `fixbase_epoch` | `0` | Two-step transfer fixed-base epochs. |
| `train` | `open_layers` | `['classifier']` | Layers trained during fixed-base stage. |
| `train` | `staged_lr` | `False` | Use lower LR for base layers. |
| `train` | `new_layers` | `['classifier']` | Layers that keep the full LR when staged LR is enabled. |
| `train` | `base_lr_mult` | `0.1` | Multiplier for base-layer LR under staged LR. |
| `train` | `lr_scheduler` | `single_step` | Scheduler: `single_step`, `multi_step`, or `cosine`. |
| `train` | `stepsize` | `[20]` | Step epoch(s). `single_step` accepts the final int if a list is given; `multi_step` requires a list. |
| `train` | `gamma` | `0.1` | Step decay multiplier. |
| `train` | `print_freq` | `20` | Training log frequency. |
| `train` | `seed` | `1` | Random seed. |
| `loss` | `name` | `softmax` | `softmax` or `triplet`. |
| `loss.softmax` | `label_smooth` | `True` | Label smoothing for cross-entropy. |
| `loss.triplet` | `margin` | `0.3` | Triplet loss margin. |
| `loss.triplet` | `weight_t` | `1.0` | Triplet loss weight. |
| `loss.triplet` | `weight_x` | `0.0` | Cross-entropy auxiliary weight. |
| `test` | `batch_size` | `100` | Evaluation batch size. Official OSNet templates often use 300. |
| `test` | `dist_metric` | `euclidean` | `euclidean` or `cosine`. |
| `test` | `normalize_feature` | `False` | L2-normalize features before distance. |
| `test` | `ranks` | `[1, 5, 10, 20]` | CMC ranks to print. |
| `test` | `evaluate` | `False` | Test-only mode when `True`. |
| `test` | `eval_freq` | `-1` | Evaluate only after training if -1; otherwise evaluate every N epochs after `start_eval`. |
| `test` | `start_eval` | `0` | First epoch eligible for periodic evaluation. |
| `test` | `rerank` | `False` | Apply k-reciprocal person re-ranking in test. |
| `test` | `visrank` | `False` | Save ranked result plots; only valid with `evaluate True`. |
| `test` | `visrank_topk` | `10` | Number of gallery images visualized per query. |

## Official template summaries

Use these embedded template names with `../scripts/torchreid_train_eval.py --template NAME`.

| Template | Model | Sources/targets | Transforms | Train | Test |
| --- | --- | --- | --- | --- | --- |
| `im_osnet_x1_0_softmax_256x128_amsgrad_cosine` | `osnet_x1_0` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.0015`, 250 epochs, batch 64, `fixbase_epoch 10`, cosine LR | batch 300, euclidean |
| `im_osnet_x1_0_softmax_256x128_amsgrad` | `osnet_x1_0` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.0015`, 150 epochs, batch 64, step `[60]` | batch 300, euclidean |
| `im_osnet_x0_75_softmax_256x128_amsgrad` | `osnet_x0_75` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.0015`, 150 epochs, batch 64, step `[60]` | batch 300, euclidean |
| `im_osnet_x0_5_softmax_256x128_amsgrad` | `osnet_x0_5` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.003`, 180 epochs, batch 128, step `[80]` | batch 300, euclidean |
| `im_osnet_x0_25_softmax_256x128_amsgrad` | `osnet_x0_25` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.003`, 180 epochs, batch 128, step `[80]` | batch 300, euclidean |
| `im_osnet_ibn_x1_0_softmax_256x128_amsgrad` | `osnet_ibn_x1_0` | Market1501 → DukeMTMC-reID | `random_flip`, `color_jitter` | `amsgrad`, lr `0.0015`, 150 epochs, batch 64, step `[60]` | batch 300, euclidean |
| `im_osnet_ain_x1_0_softmax_256x128_amsgrad_cosine` | `osnet_ain_x1_0` | Market1501 → Market1501 and DukeMTMC-reID | `random_flip`, `color_jitter` | `amsgrad`, lr `0.0015`, 100 epochs, batch 64, cosine LR | batch 300, cosine |
| `im_r50_softmax_256x128_amsgrad` | `resnet50_fc512` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.0003`, 60 epochs, batch 32, `fixbase_epoch 5`, step `[20]` | batch 100, euclidean |
| `im_r50fc512_softmax_256x128_amsgrad` | `resnet50_fc512` | Market1501 → Market1501 | `random_flip` | `amsgrad`, lr `0.0003`, 60 epochs, batch 32, `open_layers ['fc','classifier']`, step `[20]` | batch 100, euclidean |

## Sampler choices and constraints

| Sampler | Use when | Constraints |
| --- | --- | --- |
| `RandomSampler` | Standard softmax training | No identity balancing; default. |
| `SequentialSampler` | Deterministic passes such as mean/std helper | Do not use for ordinary stochastic training unless deliberate. |
| `RandomIdentitySampler` | Triplet/hard-mining style training | `batch_size_train // num_instances` identities are sampled; the number of available pids must be at least this value. If an identity has fewer images/tracklets than `num_instances`, sampling uses replacement. |
| `RandomDomainSampler` | Camera-domain-balanced training | Batch size must be divisible by `sampler.num_cams`; enough samples per selected camera are required. |
| `RandomDatasetSampler` | Multi-source dataset-balanced training | Batch size must be divisible by `sampler.num_datasets`; enough samples per selected dataset are required. |

## Optimizer and LR scheduler choices

`torchreid.optim.build_optimizer` supports:

- `adam` and `amsgrad` with `adam.beta1`, `adam.beta2`.
- `sgd` with `sgd.momentum`, `sgd.dampening`, `sgd.nesterov`.
- `rmsprop` with `rmsprop.alpha` and SGD-style momentum.
- `radam` for RAdam.
- `staged_lr True` with `new_layers` and `base_lr_mult` for fine-tuning.

`torchreid.optim.build_lr_scheduler` supports:

- `single_step`: one step epoch. If `train.stepsize` is a list, the implementation uses the last value.
- `multi_step`: requires `train.stepsize` to be a list.
- `cosine`: cosine annealing over `train.max_epoch`.

## Configuration validation checklist

Before running an expensive command:

1. `data.type` matches dataset key family: image keys with `image`, video keys with `video`.
2. `data.root` points to a parent folder containing the dataset folder expected in [data-formats.md](data-formats.md).
3. `model.name` is a verified Torchreid model key.
4. `loss.name triplet` uses an identity-balanced sampler and a model built with `loss='triplet'`.
5. `test.visrank True` appears only with `test.evaluate True`.
6. `model.load_weights` and `model.resume` paths are local files before runtime.
7. CUHK03 classic split uses `cuhk03.classic_split True`; use `cuhk03.use_metric_cuhk03 True` only when matching the old single-gallery-shot protocol.
8. `data.workers` is conservative for the host; reduce to `0` or `1` when workers hang.
9. CUDA is treated as optional/unverified unless the current environment has passed a CUDA check.
