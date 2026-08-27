# Asteroid recipe pattern

Asteroid recipes are stage-based training and evaluation flows organized around a `run.sh` master script plus `train.py` / `eval.py` helpers.

If the original recipe tree is not available, use the generated skill's self-contained training entry point instead:

```bash
python scripts/smoke_training.py --device cpu
```

That smoke uses synthetic data and the installed runtime package, so it can run from the skill output.

## Common flow

1. Set `storage_dir`, `python_path`, and a `tag` or experiment name.
2. Choose the dataset/task and sample rate.
3. Prepare or locate the dataset artifacts.
4. Build train/validation/test splits.
5. When working inside a user-provided recipe checkout, run that recipe's `train.py` with the parsed config.
6. Save the best checkpoint and a publishable model dict.
7. When working inside a user-provided recipe checkout, run that recipe's `eval.py` on the test split.

## Common stage variables

- `stage`: where to begin the recipe
- `tag`: stable experiment suffix
- `id`: visible GPU IDs passed through `CUDA_VISIBLE_DEVICES`
- `sample_rate`: dataset and model sample rate
- `task`: enhancement or separation task name
- `n_src`: number of output sources
- `segment`: training clip length in seconds
- `batch_size`, `num_workers`, `epochs`, `lr`, `weight_decay`
- `eval_use_gpu`: whether evaluation uses CUDA when the recipe supports it

## Configuration flow

Many recipes read a YAML config, convert it into grouped CLI arguments, and then write the final config back into the experiment directory.

That pattern makes it easy to:

- restart from a later stage
- compare experiments by tag
- reconstruct a run from a saved `conf.yml`

## Representative recipe families

| Family | Typical signals | Notes |
| --- | --- | --- |
| WHAM / WHAMR / LibriMix / WSJ0-mix | speech separation, noisy separation, enhancement | Usually the clearest examples of Asteroid's stage-based recipe structure |
| DNS Challenge | speech enhancement, noise suppression | Often includes extra evaluation or download steps |
| MUSDB18 / X-UMX | music source separation | Memory heavy; often use `--no-cuda` for evaluation when needed |
| FUSS | arbitrary sound separation | Data and manifest heavy |
| AVSpeech | audio-visual speech separation | Requires extra video and embedding tooling |
| SMS-WSJ / Kinect-WSJ | multi-channel separation | May need extra external packages or helper datasets |
| TAC / DeMask / LibriVAD | speaker extraction, enhancement, VAD | Useful for custom-system examples and dataset wiring |
| Deep Clustering / MixIT / TwoStep | algorithmic recipe variants | Good references for custom loss or architecture wiring |

## What to expect in `train.py`

Typical recipe `train.py` files:

- parse grouped config dictionaries
- build dataloaders from dataset classes
- instantiate a model from `asteroid.models`
- create an optimizer with `asteroid.engine.optimizers.make_optimizer`
- optionally create a scheduler
- wrap everything in `asteroid.engine.system.System`
- call Lightning `Trainer.fit`

## What to expect in `eval.py`

Typical evaluation scripts:

- load `best_model.pth` or another publishable checkpoint
- run the model on the test split
- reorder or compare outputs with a PIT loss helper if needed
- compute separation metrics with `asteroid.metrics.get_metrics`
- write summary metrics and example audio files

## Why recipes are often reference-only

The repository's recipe directories are excellent evidence for workflow shape, but they are often:

- data heavy
- networked
- dataset-specific
- GPU-oriented or memory heavy
- dependent on external helper packages

Because of that, the generated skill usually turns the recipe pattern into concise instructions and small smoke scripts rather than copying the original scripts verbatim.
