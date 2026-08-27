# VAD CLI reference

The names below are taken from the repository's `tools/train.py` and `tools/test.py` parsers. Module-level imports still require the legacy dependencies and native operators before help can execute.

## `train.py`

```text
CONFIG                         positional config path
--work-dir DIR                 output logs/checkpoints/config dump
--resume-from CHECKPOINT       resume training
--no-validate                  disable validation during training
--gpus N                       non-distributed GPU count
--gpu-ids ID [ID ...]          non-distributed GPU ids; mutually exclusive with --gpus
--seed N                       random seed, default 0
--deterministic                deterministic cuDNN options
--options KEY=VALUE [...]      deprecated alias for --cfg-options
--cfg-options KEY=VALUE [...]  merge config overrides
--launcher {none,pytorch,slurm,mpi}
--local_rank N                 distributed local rank
--autoscale-lr                 scale learning rate by GPU count / 8
```

`--options` and `--cfg-options` cannot be supplied together. Config plugin imports occur before model construction. The work directory receives a dumped config and logs.

## `test.py`

```text
CONFIG CHECKPOINT              positional config and checkpoint
--json_dir DIR                 optional custom metric-record parent in this fork
--out FILE.pkl                 save result pickle; suffix must be .pkl or .pickle
--fuse-conv-bn                 fuse convolution/batch-normalization for inference
--format-only                  format outputs without evaluation
--eval METRIC [METRIC ...]     evaluate selected metrics
--show                         show results
--show-dir DIR                 save shown results
--gpu-collect                  distributed GPU result collection
--tmpdir DIR                   distributed temporary collection directory
--seed N / --deterministic
--cfg-options KEY=VALUE [...]  merge config overrides
--options KEY=VALUE [...]      deprecated alias for --eval-options
--eval-options KEY=VALUE [...] dataset.evaluate keyword options
--launcher {none,pytorch,slurm,mpi}
--local_rank N
```

At least one of `--out`, `--eval`, `--format-only`, `--show`, or `--show-dir` is required. `--eval` and `--format-only` are mutually exclusive. Use `--launcher none` for the recommended one-GPU evaluation route.

## Validation checklist

- Config has the intended model family, plugin, dataset, temporal annotations, and normalization.
- Checkpoint exists and matches tiny/base plus stage.
- Use `--out` when later visualization is needed; inspect it with the visualization helper.
- Use a writable temporary directory for distributed collection only; it does not make distributed evaluation accurate for this project.
