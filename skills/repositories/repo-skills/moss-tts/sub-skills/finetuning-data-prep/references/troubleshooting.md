# Fine-tuning troubleshooting

Use this reference when JSONL validation, preprocessing, distributed launch, or the first checkpoint smoke test fails.

## Missing audio files or wrong base path

Symptoms:

- The validator reports missing `audio`, `ref_audio`, `reference`, `ref_wav`, or conversation `wav` paths.
- `prepare_data.py` fails while loading an audio file.
- The same manifest works from one directory but not another.

Actions:

1. Identify which helper will run. Local v1.5 resolves relative audio paths from the JSONL file's parent; Delay, Local legacy, and Realtime helpers read paths as written from the process context.
2. Re-run validation with the base directory that matches the intended launch:

   ```bash
   # From this sub-skill directory, or replace <this sub-skill> with its installed path.
   python scripts/validate_training_jsonl.py \
     train_raw.jsonl --task moss-tts --mode raw --base-dir data-root
   ```

3. If paths are URI-like or produced by a remote dataset loader, use `--no-exists-check` for syntax validation, then validate the dataset loader separately.
4. Avoid mixing relative path conventions in one JSONL. Pick one base and regenerate the manifest if necessary.

## `reference`, `ref_audio`, and `reference_audio` confusion

Symptoms:

- `ref_audio only supports a single path`.
- A TTSD row loses the intended speaker-to-reference alignment.
- Reference audio is encoded but training behaves like it has no reference.

Rules and fixes:

- `ref_audio`: single reference path. Use it for ordinary TTS voice cloning and Local v1.5 single-reference rows.
- `reference_audio`: accepted alias; use when converting data that already uses that field, but keep it string/list of strings without `null` unless the trainer path supports list placeholders through `reference_audio_codes`.
- `reference`: use for TTSD multi-speaker lists. It may contain `null` placeholders, and `prepare_data.py` preserves those positions when creating `reference_audio_codes`.
- Do not place a TTSD speaker list in `ref_audio`; it is checked as a single-reference field.
- If both code fields and path fields exist, training prefers precomputed code fields. Regenerate or remove stale code fields when changing reference paths.

## Pre-encoded `audio_codes` versus raw audio

Symptoms:

- `Each record must contain audio_codes. Run prepare_data.py first.`
- `Record ... is missing audio_codes`.
- A prepared manifest is accidentally re-encoded or overwritten.
- Training tries to encode reference paths on the fly and fails because no codec is loaded.

Actions:

1. Use `--mode raw` validation before preprocessing and `--mode prepared` validation before SFT.
2. If every row already has valid `audio_codes` and the needed reference code fields, launch training with the equivalent of `SKIP_PREPARE=1` or call the SFT entry point for the user's training checkout.
3. Do not run a raw-audio preprocessing entry point on a prepared manifest just to validate it; those programs expect `audio` and may re-encode targets.
4. Local v1.5-style preprocessing can preserve existing `audio_codes` while filling missing reference codes, but only use that behavior deliberately.
5. If reference paths remain without `ref_audio_codes` or `reference_audio_codes`, either rerun preprocessing with reference encoding enabled or keep the codec available during training.

## Sharded output names, rank assignment, and globs

Symptoms:

- Training reports no shard assigned for a rank.
- Some ranks have zero local records.
- Distributed training hangs near an allreduce.
- `--train-jsonl` seems to load only one shard.

Rules and fixes:

- Multi-rank preprocessing writes `name.rank00000-of-00016.jsonl` style files.
- Train with a quoted glob, directory, single JSONL, or comma-separated list. Prefer:

  ```bash
  --train-jsonl 'prepared/train_with_codes.rank*.jsonl'
  ```

- The suffix world size must be consistent across all matched shard files. Do not mix `.rank*-of-00008.jsonl` with `.rank*-of-00016.jsonl` in the same run.
- The training world size should not exceed the number of available shard ranks unless the modulo assignment is intentional and each process receives records.
- In pre-sharded mode, legacy trainers drop incomplete final batches; Local v1.5 aligns all ranks to the shortest shard. If too many records are dropped, create more balanced shards or reduce `gradient_accumulation_steps`.
- If a shell expands the glob too early, quote it or pass a comma-separated list explicitly.

## FSDP, ZeRO-3, and DeepSpeed extras

Symptoms:

- `deepspeed` import errors.
- ZeRO-3 initialization hangs or fails during model loading.
- FSDP complains about transformer layer wrapping.
- Checkpoint save/load fails under a sharded strategy.

Actions:

1. Install the DeepSpeed extra only for ZeRO-3 runs. DDP and FSDP do not require `deepspeed`.
2. Use the family-matched Accelerate config; do not use an 8B Delay config for Local v1.5 or Realtime.
3. For FSDP configs, keep the transformer layer class wrap target matching the Qwen3 decoder layer used by these models.
4. For multi-node configs, update `num_machines`, `num_processes`, `machine_rank`, `main_process_ip`, and `main_process_port` before launch.
5. Keep trainer-side `--gradient-accumulation-steps` explicit even when the DeepSpeed config also has a gradient accumulation field.
6. If a sharded checkpoint is incomplete or cannot be loaded for smoke inference, retry with the provided full-state-save settings or use DDP for the first small proof run.

## `n_vq` mismatch

Symptoms:

- Dataset errors such as expected `n_vq` but got another code depth.
- `reference_audio_codes n_vq=... does not match target n_vq=...`.
- Local v1.5 reports that the record does not match the fixed model `n_vq`.
- Channelwise loss weight length errors.

Actions:

1. Inspect a prepared row's `audio_codes` shape with the validator. For Local v1.5, the expected depth is normally 12. For TTSD v1.0-style runs, use 16.
2. Pass the same `--n-vq` to preprocessing and training when overriding the default.
3. Regenerate both target and reference codes when changing `n_vq`; do not mix old reference codes with new target codes.
4. Match `--channelwise-loss-weight` to the final `n_vq`: either two values (`text,total_audio`) or `n_vq + 1` explicit values.
5. For Realtime, prefer 16-channel turn codes. The dataset can pad/trim in some shapes, but relying on that can hide manifest mistakes.

## TTSD gibberish after apparently normal training

Symptoms:

- Training loss decreases normally.
- Inference produces gibberish, wrong speaker turns, or unstable continuation.
- Prompt/template behavior differs between preprocessing/training and inference.

Likely causes and fixes:

- TTSD v1.0 expects `n_vq=16`; use `--n-vq 16` in both preprocessing and training.
- Keep the TTSD-compatible support code, processor prompt template, model config, prepared JSONL, checkpoint, and inference loader in agreement. Do not mix a default Delay implementation with a TTSD checkpoint that uses a different template.
- Preserve `reference` list order and `null` placeholders. Speaker `[S1]`, `[S2]`, etc. in `text` must correspond to the intended reference slots.
- Smoke-test with one short dialogue and the exact inference path before scaling training.

## OOM and stability failures

Symptoms:

- CUDA OOM during codec preprocessing or SFT.
- Non-finite losses or gradient norms.
- Throughput is much lower than expected.

Actions:

- Lower `--per-device-batch-size` first, then use `--gradient-accumulation-steps` to recover the global batch size.
- Enable `--gradient-checkpointing` on supported trainers.
- For Local v1.5, try `--gradient-checkpointing-scope global` first; use `all` if the local decoder is also too large.
- Use `--mixed-precision bf16` on supported GPUs; use `fp16` only if BF16 is unavailable and numerics are acceptable.
- Reduce `--num-workers` if dataloader workers compete with codec/model memory.
- Use DDP for the first proof run; move to FSDP/ZeRO-3 only when needed for memory.
- For Local v1.5, `--skip-nonfinite-batches` can keep a long run alive while you investigate, but it should not hide persistent data/model instability.

## Quick inference smoke after a checkpoint

Symptoms:

- Training completes, but it is unclear whether the checkpoint is loadable.
- A checkpoint directory is missing processor/tokenizer/runtime files.
- Local v1.5 saves mono-looking output or wrong sample rate.

Smoke procedure:

1. Pick the latest complete checkpoint, commonly `checkpoint-epoch-N` or `checkpoint-last`.
2. Use the inference sub-skill for the selected model family to load the checkpoint with `trust_remote_code=True` where required.
3. Generate one very short sample with one known-good prompt and one known-good reference audio when the task is reference-conditioned.
4. Save a WAV and confirm it exists and has nonzero duration.
5. Confirm family-specific semantics: Local v1.5 should produce 48 kHz stereo; Realtime conversation generation should preserve user/assistant turn semantics; TTSD should preserve speaker/reference mapping.
6. If smoke passes, route deeper inference, batch generation, quality analysis, or llama.cpp work to the owning inference/backend sub-skill.

A smoke WAV is only a loadability and gross-integrity check. It does not replace task-quality evaluation.
