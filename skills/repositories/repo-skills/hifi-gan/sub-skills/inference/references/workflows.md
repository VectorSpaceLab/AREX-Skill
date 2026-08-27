# Inference workflows

## Wav-to-wav inference

1. Put mono 16-bit PCM wav files in `test_files/` or another directory you control.
2. Make sure the checkpoint directory contains the matching `config.json`.
3. Run:

   ```bash
   python scripts/infer_hifigan.py --mode wav --checkpoint_file cp_hifigan/g_00050000 \
     --input_wavs_dir test_files \
     --output_dir generated_files
   ```

4. Outputs are named `<stem>_generated.wav` and use the config sample rate in the WAV header.

Notes:

- The bundled entrypoint does not resample or validate the input sample rate. Use a source wav whose sample rate matches the paired config.
- The bundled entrypoint ultimately iterates `os.listdir(...)`; keep the directory free of subdirectories and stray files.
- If you need CPU-only execution, the script will fall back automatically when CUDA is not available.

## Mel-to-wav inference

1. Put mel `.npy` files in `test_mel_files/` or another directory you control.
2. The safest shape is `float32` with 80 mel bins, either `(80, T)` or `(1, 80, T)`.
3. Run:

   ```bash
   python scripts/infer_hifigan.py --mode mel --checkpoint_file cp_hifigan/g_00050000 \
     --input_mels_dir test_mel_files \
     --output_dir generated_files_from_mel
   ```

4. Outputs are named `<stem>_generated_e2e.wav` and use the config sample rate in the WAV header.

Notes:

- Mel mode does not generate mels; it only consumes the `.npy` files.
- Rank-1 arrays, ragged arrays, or non-80-channel arrays should be treated as input errors.
- If your upstream text-to-mel model produces a batch dimension, keep it only if the array still represents one mel sample. The helper accepts the common 2-D single-sample layout by default.

## Synthetic smoke

1. Create a synthetic checkpoint and config pair:

   ```bash
   python scripts/make_dummy_checkpoint.py --output-dir ./scratch/hifigan-smoke/cp
   ```

2. Create tiny wav and mel fixtures:

   ```bash
   python scripts/make_tiny_inference_fixtures.py --output-root ./scratch/hifigan-smoke/fixtures
   ```

3. Run both inference modes. The smoke helper uses the bundled runtime source and applies local modern torch/librosa compatibility shims; it does not require an external checkout.

   ```bash
   python scripts/run_inference_smoke.py --work-dir ./scratch/hifigan-smoke
   ```

## Intentional negative cases

Use these when you want to verify error recovery guidance rather than happy-path synthesis.

- Checkpoint/config mismatch:

  ```bash
  python scripts/make_dummy_checkpoint.py \
    --output-dir ./scratch/hifigan-mismatch/cp \
    --state-config config_v1.json \
    --config-file config_v2.json
  ```

  Then run `scripts/infer_hifigan.py --mode wav` or `--mode mel` against that checkpoint directory.

- Unsupported wav sample rate:

  ```bash
  python scripts/make_tiny_inference_fixtures.py --output-root ./scratch/hifigan-bad-wav --sample-rate 16000
  ```

- Wrong-rank mel input:

  ```bash
  python scripts/make_tiny_inference_fixtures.py --output-root ./scratch/hifigan-bad-mel --mel-rank 1
  ```
