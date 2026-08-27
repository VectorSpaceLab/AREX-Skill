# Workflows

## 1. No-download validation
Use the safe recipe first when you only need to confirm that the task, model, and input mode are compatible.

- List supported models without loading weights.
- Dry-run a task/model pair before any checkpoint download.
- Confirm whether your input path is a file, directory, or `.scp` list.
- Check whether FFmpeg is needed before you try to process non-WAV audio or video.

Example commands:

```bash
python scripts/clearvoice_inference_recipe.py --list-models
python scripts/clearvoice_inference_recipe.py --task speech_enhancement --model-name MossFormer2_SE_48K --input-path noisy.mp3 --dry-run
```

## 2. File, directory, and `.scp` inference
Use the file-mode recipe for audio files, audio directories, or `.scp` lists.

- Choose the matching `task` and one or more compatible `model-name` values.
- Use `--online-write` when you want the model to save outputs as it processes them.
- Use `--output-path` as a file path for a single offline result, or as a directory for batch outputs.
- When several models are active, expect per-model subdirectories or grouped outputs.

Example commands:

```bash
python scripts/clearvoice_inference_recipe.py --task speech_enhancement --model-name FRCRN_SE_16K --input-path noisy.wav --output-path enhanced.wav
python scripts/clearvoice_inference_recipe.py --task speech_separation --model-name MossFormer2_SS_16K --input-path mix.scp --online-write --output-path separated/
```

## 3. NumPy/Tensor inference
Use the tensor recipe when you already have an in-memory batch.

- Provide exactly one model name.
- Use audio-only tasks only.
- Shape your input as `[batch, length]`.
- Use `--input-path` to load a `.npy` array, or omit it and let the helper build a synthetic validation batch.
- Add `--run` only when dependencies are present and you really want to load the model.

Example command:

```bash
python scripts/clearvoice_numpy_recipe.py --task speech_enhancement --model-name MossFormer2_SE_48K --input-path batch.npy --run --output-path enhanced.npy
```

## 4. AV target speaker extraction
Use the file-mode recipe for the AV model.

- Provide video input, not audio-only input.
- Set `--online-write` because the runtime asserts it for this task.
- Expect per-video output folders and FFmpeg-driven media reconstruction.
- Use `--dry-run` first if you are unsure about codec availability.

Example command:

```bash
python scripts/clearvoice_inference_recipe.py --task target_speaker_extraction --model-name AV_MossFormer2_TSE_16K --input-path video.mp4 --online-write --output-path tse_outputs/
```

## 5. Checkpoint downloads
ClearVoice fetches missing checkpoints on first use.

- Treat the first real run as a networked step unless the checkpoint directory is already staged.
- If you need offline validation only, stay in dry-run mode.
- If a download fails, verify the checkpoint directory, network access, and model family before retrying.
