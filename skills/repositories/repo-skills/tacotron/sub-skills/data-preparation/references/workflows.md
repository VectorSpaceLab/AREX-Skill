# Data workflows

## Safe command sequence

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/data-preparation/scripts/build_preprocess_command.py --checkout-root "$CHECKOUT_ROOT" --base-dir /data/tacotron --dataset ljspeech --output training --num-workers 4
# Review the printed dry-run command, then intentionally execute it from the checkout cwd.
cd "$SKILL_ROOT" && python sub-skills/data-preparation/scripts/validate_training_metadata.py --data-dir /data/tacotron/training
```

The builder never reads a dataset or writes files; it preserves the source CLI
flags for an intentional execution step. Use an absolute or deliberately chosen
base directory and keep the generated training directory separate from raw
audio. `--num_workers` is an optimization; reduce it when debugging file or
decoder failures. Full preprocessing still needs external audio and the pinned
audio decoder stack.

## Custom corpus

Start from a tiny set of WAV/text pairs. Ensure each source audio file is
readable, has a nonzero frame count, and produces both arrays with matching
first dimensions. Write metadata only after all workers complete. Add a new
`--dataset` choice and dispatch branch only when its input layout is stable.

## Preflight checks

Check raw file names, metadata delimiters, UTF-8 text, sample-rate handling,
write permissions, free disk, and the output row count. The data feeder later
loads `linear_filename` and `mel_filename` relative to the directory containing
`train.txt`, so moving only `train.txt` breaks training.
