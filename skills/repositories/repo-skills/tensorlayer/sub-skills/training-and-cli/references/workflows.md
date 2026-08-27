# Workflows

## Tiny synthetic fit/test/predict loop

1. Build a small classifier with `Input` and `Dense` layers.
2. Generate a tiny linearly separable NumPy dataset.
3. Train with `tl.utils.fit` for a small number of epochs.
4. Evaluate with `tl.utils.test`.
5. Predict class logits with `tl.utils.predict` and check the argmax labels.

The bundled `scripts/smoke_fit.py` follows this exact pattern.

## CLI help

1. Leave `CUDA_VISIBLE_DEVICES` unset.
2. Run `python -m tensorlayer.cli --help` or the bundled root helper.
3. Confirm the `train` subcommand is visible and no parser error occurs.

## Distributed trainer guidance

The `Trainer` API belongs here, but the bundled skill keeps distributed jobs help-only. Only launch a real distributed run when the user has explicitly provided the extra runtime requirements.
