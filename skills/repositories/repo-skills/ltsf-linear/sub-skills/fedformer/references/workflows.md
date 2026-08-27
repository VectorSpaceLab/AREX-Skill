# FEDformer Workflows

Use these recipes when you need a single FEDformer run, a controlled comparison against the local Transformer baselines, or a reproducible sweep over prediction length or look-back window.

## 1) Single run

1. Make sure the checkout contains a `FEDformer/` subtree and that the dataset CSVs are available under the chosen `root_path`.
2. Pick the model family:
   - `--model FEDformer` for the FEDformer branches.
   - `--model Autoformer`, `Informer`, or `Transformer` for a comparison run inside this subrepo.
3. Pick the FEDformer branch:
   - `--version Fourier` for frequency-mode selection.
   - `--version Wavelets` for multiresolution experiments.
4. Keep `seq_len`, `label_len`, `pred_len`, and the feature layout fixed while you change one ablation knob at a time.

Example using the bundled wrapper:

```bash
python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
  --is_training 1 \
  --model FEDformer \
  --version Fourier \
  --mode_select low \
  --modes 64 \
  --data ETTh1 \
  --data_path ETTh1.csv \
  --root_path <dataset-root> \
  --features S \
  --seq_len 96 \
  --label_len 48 \
  --pred_len 96 \
  --enc_in 7 \
  --dec_in 7 \
  --c_out 7
```

The native source entry point is the same command run from `<repo-root>/FEDformer/` with `python -u run.py`.

## 2) Compare FEDformer with the local baselines

The supported comparison family in this subrepo is:

- `FEDformer`
- `Autoformer`
- `Informer`
- `Transformer`

For a fair comparison:

- keep the dataset and horizon fixed;
- keep `seq_len`, `label_len`, and the feature mode fixed;
- keep `enc_in`, `dec_in`, and `c_out` fixed;
- compare the metrics saved under `results/<setting>/metrics.npy`.

Example comparison loop:

```bash
for model in FEDformer Autoformer Informer Transformer; do
  python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
    --is_training 1 \
    --model "$model" \
    --data ETTh1 \
    --data_path ETTh1.csv \
    --root_path <dataset-root> \
    --features S \
    --seq_len 96 \
    --label_len 48 \
    --pred_len 96 \
    --enc_in 7 \
    --dec_in 7 \
    --c_out 7
 done
```

## 3) FEDformer ablations

Use the following knobs when the question is specifically about FEDformer internals:

- Fourier: sweep `--mode_select` and `--modes`.
- Wavelets: sweep `--L`, `--base`, and `--cross_activation`.
- Embeddings: sweep `--embed_type`.
- Input smoothing: keep `--moving_avg` at the parser default unless you are setting a real Python list in code.

A practical ablation run keeps the dataset fixed and changes exactly one of those knobs at a time.

## 4) Reproduce the long-forecasting sweeps

The native shell scripts in `FEDformer/scripts/LongForecasting.sh` encode the large prediction-length sweep that covers ETT, Electricity, Exchange, Traffic, Weather, and ILI presets.

Treat that script as reference-only because it launches many long jobs and hardcodes log redirection.

You can reproduce the pattern with a loop over `pred_len` values:

```bash
for pred_len in 96 192 336 720; do
  python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
    --is_training 1 \
    --model FEDformer \
    --version Fourier \
    --data ETTh1 \
    --data_path ETTh1.csv \
    --root_path <dataset-root> \
    --features S \
    --seq_len 96 \
    --label_len 48 \
    --pred_len "$pred_len" \
    --enc_in 7 \
    --dec_in 7 \
    --c_out 7
 done
```

Swap in the dataset-specific `data`, `data_path`, `features`, and channel counts from the source sweep when needed.

## 5) Reproduce the look-back-window sweeps

`FEDformer/scripts/LookBackWindow.sh` is also reference-only. It varies `seq_len` and `pred_len` across a large matrix of runs.

Use the same command structure and change the look-back length:

```bash
for seq_len in 36 48 60 72 144 288; do
  python scripts/run_fedformer.py --repo-root <repo-root> --run -- \
    --is_training 1 \
    --model FEDformer \
    --version Wavelets \
    --data ETTm1 \
    --data_path ETTm1.csv \
    --root_path <dataset-root> \
    --features M \
    --seq_len "$seq_len" \
    --label_len 48 \
    --pred_len 24 \
    --enc_in 7 \
    --dec_in 7 \
    --c_out 7
 done
```

## 6) Smoke and post-run checks

After a run finishes, look for:

- `checkpoints/<setting>/checkpoint.pth`
- `results/<setting>/metrics.npy`
- `results/<setting>/pred.npy`
- `results/<setting>/true.npy`
- `test_results/<setting>/`

For a quick GPU sanity check without data, use:

```bash
python scripts/smoke_fedformer.py --repo-root <repo-root> --version Wavelets
```

## Source script provenance

| Source repo artifact | Bundled skill helper | Why the helper exists |
| --- | --- | --- |
| `FEDformer/run.py` | `scripts/run_fedformer.py` | Safe wrapper that resolves the FEDformer working directory and avoids hardcoding a checkout path. |
| `FEDformer/scripts/LongForecasting.sh` | `references/workflows.md` plus `scripts/run_fedformer.py` | Large multi-dataset sweep with long jobs and log redirection; better kept as a recipe than copied verbatim. |
| `FEDformer/scripts/LookBackWindow.sh` | `references/workflows.md` plus `scripts/run_fedformer.py` | Large look-back sweep with repeated jobs and repo-local logging assumptions. |
