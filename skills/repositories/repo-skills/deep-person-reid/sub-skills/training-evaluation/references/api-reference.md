# API reference for training/evaluation

This reference lists the Torchreid 1.4.0 API surfaces needed to build data managers, engines, optimizers, schedulers, and evaluation calls. For embedding-only and metric-internal details, route to the feature-extraction sub-skill.

## Data managers

### `torchreid.data.ImageDataManager`

Verified signature:

```python
ImageDataManager(
    root='', sources=None, targets=None, height=256, width=128,
    transforms='random_flip', k_tfm=1, norm_mean=None, norm_std=None,
    use_gpu=True, split_id=0, combineall=False, load_train_targets=False,
    batch_size_train=32, batch_size_test=32, workers=4,
    num_instances=4, num_cams=1, num_datasets=1,
    train_sampler='RandomSampler', train_sampler_t='RandomSampler',
    cuhk03_labeled=False, cuhk03_classic_split=False,
    market1501_500k=False,
)
```

Primary outputs/properties:

- `train_loader`: DataLoader over source train data.
- `train_loader_t`: optional target train DataLoader when `load_train_targets=True`; sources and targets must not overlap.
- `test_loader[name]['query']` and `test_loader[name]['gallery']`: evaluation DataLoaders for each target.
- `test_dataset[name]['query']` and `test_dataset[name]['gallery']`: raw tuple lists used by ranked-result visualization.
- `num_train_pids`, `num_train_cams`: counts used for model classifier construction.
- `preprocess_pil_img(img)`: test transform for one PIL image.

Image batch dicts contain at least `img`, `pid`, `camid`, `impath`, and `dsetid`. `img` has shape `(batch_size, channels, height, width)`.

### `torchreid.data.VideoDataManager`

Verified signature:

```python
VideoDataManager(
    root='', sources=None, targets=None, height=256, width=128,
    transforms='random_flip', norm_mean=None, norm_std=None,
    use_gpu=True, split_id=0, combineall=False,
    batch_size_train=3, batch_size_test=3, workers=4,
    num_instances=4, num_cams=1, num_datasets=1,
    train_sampler='RandomSampler', seq_len=15, sample_method='evenly',
)
```

Video batch dicts contain `img`, `pid`, `camid`, and `dsetid`. `img` has shape `(batch_size, seq_len, channels, height, width)` for evaluation/extraction. During video engine training, the engine flattens `(batch, seq_len, channels, height, width)` into `(batch*seq_len, channels, height, width)` for image-like model forwarding.

Important video constraints:

- `sample_method` choices: `evenly`, `random`, `all`.
- `all` can yield variable tracklet lengths and should use batch size 1.
- Current training transforms are image-like; they are applied independently to frames, not consistently across a whole tracklet.

## Dataset registry APIs

```python
torchreid.data.register_image_dataset(name, dataset_class)
torchreid.data.register_video_dataset(name, dataset_class)
```

Both registries reject duplicate names. Register custom datasets before constructing data managers in the same Python process.

Initializer errors look like:

```text
Invalid dataset name. Received "...", but expected to be one of [...]
```

When a key is invalid, check spelling and whether the dataset is image or video.

## Model construction boundary

Training/evaluation uses:

```python
torchreid.models.build_model(name, num_classes, loss='softmax', pretrained=True, use_gpu=True)
```

- `num_classes` should be `datamanager.num_train_pids`.
- `loss='softmax'` makes ordinary engines expect classifier outputs.
- `loss='triplet'` makes triplet engines expect `(outputs, features)` from the model.
- `pretrained=True` may load or download ImageNet/pretrained weights. Use `pretrained=False` for strict offline smoke checks.
- Detailed model-key catalogs and embedding behavior are owned by the feature-extraction sub-skill.

## Engine selection

The unified workflow chooses engine from `data.type` and `loss.name`:

| `data.type` | `loss.name` | Engine class |
| --- | --- | --- |
| `image` | `softmax` | `torchreid.engine.ImageSoftmaxEngine` |
| `image` | `triplet` | `torchreid.engine.ImageTripletEngine` |
| `video` | `softmax` | `torchreid.engine.VideoSoftmaxEngine` |
| `video` | `triplet` | `torchreid.engine.VideoTripletEngine` |

### Image softmax engine

```python
ImageSoftmaxEngine(datamanager, model, optimizer, scheduler=None, use_gpu=True, label_smooth=True)
```

Computes cross-entropy loss and top-1 accuracy from model outputs.

### Image triplet engine

```python
ImageTripletEngine(
    datamanager, model, optimizer, margin=0.3, weight_t=1,
    weight_x=1, scheduler=None, use_gpu=True, label_smooth=True,
)
```

Computes hard triplet loss on features when `weight_t > 0` and cross-entropy on classifier outputs when `weight_x > 0`. At least one weight must be positive. Use an identity-balanced sampler.

### Video engines

```python
VideoSoftmaxEngine(datamanager, model, optimizer, scheduler=None, use_gpu=True, label_smooth=True, pooling_method='avg')
VideoTripletEngine(datamanager, model, optimizer, margin=0.3, weight_t=1, weight_x=1, scheduler=None, use_gpu=True, label_smooth=True, pooling_method='avg')
```

`pooling_method` is `avg` or `max` over sequence features.

## `Engine.run`

Verified signature:

```python
Engine.run(
    save_dir='log', max_epoch=0, start_epoch=0, print_freq=10,
    fixbase_epoch=0, open_layers=None, start_eval=0, eval_freq=-1,
    test_only=False, dist_metric='euclidean', normalize_feature=False,
    visrank=False, visrank_topk=10, use_metric_cuhk03=False,
    ranks=[1, 5, 10, 20], rerank=False,
)
```

Behavior:

- If `test_only=True`, `run` calls `test(...)` and returns without training.
- If `visrank=True` and `test_only=False`, `run` raises `ValueError`; use `test.evaluate True` in config mode.
- Training writes TensorBoard summaries under `save_dir` and runs final test when `max_epoch > 0`.
- Periodic evaluation during training occurs when `(epoch+1) >= start_eval`, `eval_freq > 0`, and the epoch matches the frequency.
- Evaluation extracts query/gallery features, optionally L2-normalizes them, computes euclidean/cosine distance, optionally reranks, then prints `mAP` and requested CMC ranks.
- Visrank outputs are saved under `save_dir/visrank_<dataset>`.

## Optimizer builder

Verified signature:

```python
build_optimizer(
    model, optim='adam', lr=0.0003, weight_decay=0.0005,
    momentum=0.9, sgd_dampening=0, sgd_nesterov=False,
    rmsprop_alpha=0.99, adam_beta1=0.9, adam_beta2=0.99,
    staged_lr=False, new_layers='', base_lr_mult=0.1,
)
```

Supported `optim`: `adam`, `amsgrad`, `sgd`, `rmsprop`, `radam`.

`staged_lr=True` splits direct child modules by name. Names in `new_layers` get the full learning rate; all other child modules get `lr * base_lr_mult`. If the model is wrapped in `nn.DataParallel`, the builder unwraps it for child-module grouping.

## LR scheduler builder

Verified signature:

```python
build_lr_scheduler(optimizer, lr_scheduler='single_step', stepsize=1, gamma=0.1, max_epoch=1)
```

Supported `lr_scheduler`:

- `single_step`: `stepsize` must be an int; if a list is passed, Torchreid uses the last element.
- `multi_step`: `stepsize` must be a list.
- `cosine`: uses cosine annealing over `max_epoch`.

## Unified config-to-API mapping

The unified flow maps config sections to these function calls:

```python
# Data
ImageDataManager(**imagedata_kwargs(cfg))
VideoDataManager(**videodata_kwargs(cfg))

# Model
models.build_model(
    name=cfg.model.name,
    num_classes=datamanager.num_train_pids,
    loss=cfg.loss.name,
    pretrained=cfg.model.pretrained,
    use_gpu=cfg.use_gpu,
)

# Weights/resume
if cfg.model.load_weights: load_pretrained_weights(model, cfg.model.load_weights)
if cfg.model.resume: start_epoch = resume_from_checkpoint(cfg.model.resume, model, optimizer, scheduler)

# Optim/schedule
optim.build_optimizer(model, **optimizer_kwargs(cfg))
optim.build_lr_scheduler(optimizer, **lr_scheduler_kwargs(cfg))

# Engine.run
engine.run(**engine_run_kwargs(cfg))
```

Relevant `engine_run_kwargs` mapping:

| Config key | `Engine.run` arg |
| --- | --- |
| `data.save_dir` | `save_dir` |
| `train.max_epoch` | `max_epoch` |
| `train.start_epoch` | `start_epoch` |
| `train.fixbase_epoch` | `fixbase_epoch` |
| `train.open_layers` | `open_layers` |
| `test.start_eval` | `start_eval` |
| `test.eval_freq` | `eval_freq` |
| `test.evaluate` | `test_only` |
| `train.print_freq` | `print_freq` |
| `test.dist_metric` | `dist_metric` |
| `test.normalize_feature` | `normalize_feature` |
| `test.visrank` | `visrank` |
| `test.visrank_topk` | `visrank_topk` |
| `cuhk03.use_metric_cuhk03` | `use_metric_cuhk03` |
| `test.ranks` | `ranks` |
| `test.rerank` | `rerank` |

## Return/log structures to expect

- Training logs include epoch, batch, time, data time, ETA, loss meters, and learning rate.
- Evaluation logs include `mAP: NN.N%` and CMC lines such as `Rank-1  : NN.N%`.
- `Engine.test` returns the final target's rank-1 value. For multiple targets, inspect logs for each dataset section instead of relying only on the return value.
- Checkpoints are saved under `save_dir`, commonly as `model.pth.tar-<epoch>` with a best-model marker when applicable.
