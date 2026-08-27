# Troubleshooting

## Purpose

Use this as the cross-cutting troubleshooting entry point for HiFi-GAN. It
covers dependency mismatches, checkpoint/config pairing, and broad layout or
runtime failures that are shared by both sub-skills.

## Environment and dependency issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` for `torch`, `librosa`, `scipy`, `tensorboard`, or `matplotlib` | The environment is missing the audio/training stack | Install the repo's runtime dependencies in a CUDA-capable Python environment before using the skill. |
| `stft requires the return_complex parameter` | A newer PyTorch version is being used with the copied `meldataset.py` code path | Use the bundled `train_hifigan.py`, `infer_hifigan.py`, or smoke helpers, which apply process-local shims, or pin/patch the stack intentionally. |
| `librosa.filters.mel` argument errors | A newer librosa version is being used with copied source that calls `mel` positionally | Use the bundled wrappers/smoke helpers for compatibility checks or patch the call path deliberately. |
| CUDA imports succeed but `torch.cuda.is_available()` is false | CPU-only torch, driver mismatch, or missing GPU passthrough | Re-check the CUDA environment before attempting training. |

## Data and layout issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `FileNotFoundError` for a wav | The training filelist id does not match an existing `<input_wavs_dir>/<id>.wav` file | Keep the first filelist column basename-only; do not add `.wav`. |
| Missing mel `.npy` during fine-tuning | The mel filename does not match the wav basename | Use identical basenames for wav and mel files. |
| Empty input directory for inference | The bundled inference path's `os.listdir(...)` found no usable files | Populate the directory with only the intended wav or mel files. |
| Wrong output filename stem | The scripts strip only the final extension | Rename the source file if a different stem is required. |

## Checkpoint and config issues

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `load_state_dict` size mismatch | The checkpoint and `config.json` do not belong to the same generator family | Keep the checkpoint directory and the paired config together. |
| Training silently resumes the wrong run | An old checkpoint directory still contains both `g_########` and `do_########` files | Use a fresh checkpoint directory per run or deliberately resume the matching one. |
| Inference fails before synthesis starts | The checkpoint directory is missing `config.json` | Copy the exact config used to create the generator into that checkpoint directory. |

## Workflow routing hints

- If the issue is about filelists, validation, checkpoints, or TensorBoard,
  stay in the training sub-skill.
- If the issue is about checkpoint/config pairing, output directories, or mel
  shape errors during synthesis, stay in the inference sub-skill and use
  `scripts/infer_hifigan.py`.
- If the problem is broader than either route, start here and then jump into
  the specific sub-skill reference that matches the failure.
