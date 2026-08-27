# Training Configuration Reference

## Hydra structure

Training/evaluation use Hydra config groups. The default train stack selects:

```text
datamodule: multi_datamodules.yaml
model: multi_model.yaml
callbacks: default.yaml
logger: null
trainer: default.yaml
paths: default.yaml
extras: default.yaml
hydra: default.yaml
experiment: null
hparams_search: null
debug: null
```

Experiments override task-specific datamodule/model/trainer choices.

## Common experiment names

| Experiment | Intended task |
| --- | --- |
| `cws` | Chinese word segmentation |
| `pos` | POS tagging |
| `ner` | Named entity recognition |
| `srl` | Semantic role labeling |
| `dep` | Dependency parsing |
| `sdp` | Semantic dependency parsing |
| `multi`, `multi_bi` | Multi-task models |
| `cls` | Sentence classification code path |

## Trainer choices

Common trainer config families include CPU, GPU, MPS, default, and distributed variants. Use CPU for validation and small checks. Use GPU/distributed only after verifying hardware and approving long-running training.

## Useful overrides

```text
seed=123
train=True
test=True
ckpt_path=/path/to/checkpoint.ckpt
tags='[experiment-name]'
trainer=cpu
experiment=cws
logger=null
```

For eval, `ckpt_path` is required.

## Model/config gotchas

- Model components use custom `_ltp_target_` keys in parts of the model config, not only Hydra's `_target_`.
- `transformers.AutoModel.from_pretrained` may download a backbone unless the environment/cache is prepared.
- Tokenization uses a maximum length (commonly 512 in adapters/pipeline code); long examples need splitting or explicit truncation decisions.
- Multi-task configs share a backbone and task heads. Keep task vocab files synchronized with the config.

## Debug and logging

- Use debug configs to limit data or overfit a tiny batch before full training.
- Avoid online loggers unless credentials and network are intentionally available.
- Capture the resolved Hydra config for any run you need to reproduce.
