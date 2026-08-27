# Training troubleshooting

## Purpose

Use this matrix when `train.py` fails, silently resumes the wrong run, writes no validation logs, or behaves unexpectedly during normal training, fine-tuning, or multi-GPU execution.

## Data and filelists

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` or `No such file or directory` for a wav | A filelist id has no matching `<input_wavs_dir>/<id>.wav`, the first field already included `.wav`, or `--input_wavs_dir` points at the wrong directory. | Check the first pipe-delimited field in both filelists. It must be a basename without extension. Run `scripts/make_ljspeech_fixture.py --include-missing-wav-row` later as a negative usability case to confirm guidance catches this. |
| Training uses unexpected utterances | `--input_training_file` or `--input_validation_file` still points at the default LJSpeech paths. | Pass all three data options together: `--input_wavs_dir`, `--input_training_file`, and `--input_validation_file`. |
| `ValueError: <sr> SR doesn't match target 22050 SR` | A wav's actual sample rate does not match config `sampling_rate`. | Resample every wav to the selected config rate or create a fully consistent custom config. Do not only edit `sampling_rate`; mel settings, hop/upsample relationship, and pretrained checkpoint compatibility may also change. |
| DataLoader has zero batches or appears to do nothing | Training filelist length is smaller than the per-GPU `batch_size`, and `drop_last=True` drops the incomplete batch. | Reduce config `batch_size`, expose fewer GPUs, or add enough training rows. Remember `batch_size` is divided by visible GPU count. |
| Validation crashes with an undefined loop index or no scalar output | Validation filelist is empty or all rows are invalid; validation loader uses `drop_last=True` with `batch_size=1`. | Keep at least one valid validation wav. Validate file paths before a long run. |

## Fine-tuning mel `.npy` failures

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| Missing `.npy` file under `ft_dataset` or custom mels dir | Mel filename does not exactly match wav basename. | For `LJ001-0001.wav`, create `LJ001-0001.npy`; do not add text, speaker ids, or alternate prefixes. Use `scripts/make_ljspeech_fixture.py --with-mels --include-bad-mel-name` later as a negative case. |
| Shape/channel mismatch near the first generator convolution | Mel array does not have 80 mel channels or has axes reversed. | Save mels as `[80, frames]` or `[1, 80, frames]`. The generator's `conv_pre` expects 80 input channels. |
| `empty range for randrange()` or crop failure in fine-tuning mode | Mel frame count is not long enough for `ceil(segment_size / hop_size)` when the audio is at least `segment_size` samples. | Regenerate mels using the same hop/config and ensure enough frames. For debug, use shorter audio or a smaller smoke config. |
| Validation loss size mismatch | External mel frames do not align with the wav length and config hop size. | Regenerate teacher-forced mels with the same sample rate, hop size, window, mel count, `fmin`, and `fmax` used by the selected config. |
| Passing `--fine_tuning False` still enables fine-tuning | `argparse` uses `type=bool`, and `bool("False")` is true. | Omit the flag for normal training. Use `--fine_tuning True` only when mels are present. |

## Checkpoint and resume issues

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| A new run unexpectedly resumes old weights | `--checkpoint_path` contains both `g_????????` and `do_????????`; `scan_checkpoint()` selects the latest of each. | Use a new checkpoint directory for each experiment/config, or intentionally resume and record the starting checkpoint. |
| Training starts from scratch despite checkpoint files | One side is missing (`g_` or `do_`), filenames do not match the eight-digit pattern, or the directory is wrong. | Keep generator and discriminator/optimizer checkpoints together. Use filenames like `g_00005000` and `do_00005000`. |
| Optimizer state or model load error on resume | Config/model topology changed after the checkpoint was created. | Resume only with a compatible config. For architecture changes, start a new directory or write a dedicated migration script. |
| `config.json` in checkpoint dir differs from current launch | `env.build_env()` copied a config from a previous or current launch into a reused directory. | Treat `config.json` as run metadata. Avoid mixing variants in one checkpoint directory. |

## CUDA and library compatibility

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Torch not compiled with CUDA enabled`, `CUDA driver version is insufficient`, or device init failures | `train.py` is GPU-only as written and constructs `cuda:<rank>` even when no CPU fallback is available. | Use a CUDA-capable PyTorch build and driver. Confirm `python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"`. |
| Out-of-memory during model/discriminator step | V1 is large, batch size too high, or too many GPUs/jobs share one device. | Try V2/V3, reduce config `batch_size`, expose one GPU with `CUDA_VISIBLE_DEVICES=0`, or lower segment size only for debugging/custom training. |
| `stft requires the return_complex parameter` | Modern PyTorch requires an explicit `return_complex`; source code was written for older PyTorch. | For smoke checks, use `scripts/smoke_train_tiny.py`, which shims `torch.stft`. For production, either run an older compatible stack or patch `meldataset.mel_spectrogram` deliberately. |
| `mel() takes 0 positional arguments` or similar librosa filter error | Modern librosa makes `librosa.filters.mel` keyword-only; source code calls it positionally. | Use the smoke launcher's librosa shim for wiring checks. For long training, pin librosa compatible with the repo or patch the call to use keywords. |
| Import error for `tensorboard` | `torch.utils.tensorboard.SummaryWriter` import fails before training starts. | Install TensorBoard in the active environment and re-run a short smoke. The inspection environment already verified this import once. |
| Import error for `librosa.util.normalize` | Missing/incompatible librosa. | Install a librosa version exposing `librosa.util.normalize` or use a dependency set compatible with the repository. |

## TensorBoard and validation logs

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| No event files under expected run | Logs are written to `<checkpoint_path>/logs`, not a separate default run directory. | Point TensorBoard at the exact checkpoint path: `tensorboard --logdir <checkpoint_path>/logs`. |
| Validation is unexpectedly slow at step 0 | The code validates whenever `steps % validation_interval == 0`; step 0 always qualifies. | Keep a small validation subset for debug/smoke runs. For production, expect first-step validation and account for audio/figure logging. |
| Scalar `mel_error` looks stale after custom interval edits | `mel_error` is freshly computed in the `stdout_interval` block and then used by the `summary_interval` block. | Keep `summary_interval` aligned with `stdout_interval` for precise scalar timing; defaults are aligned (`100` is divisible by `5`). |
| TensorBoard audio/figure logging fails | Bad validation audio, incompatible sample rate, matplotlib backend issues, or generated output/mel mismatch. | Confirm validation wavs load, sample rates match, and the environment can import matplotlib in non-interactive mode. |

## Distributed / `num_gpus > 1` mistakes

| Symptom / error fragment | Likely cause | Recovery |
| --- | --- | --- |
| NCCL rendezvous timeout or address-in-use error | `dist_url` port in the config is already used by another job. | Edit the config's `dist_config.dist_url` to a free local port for each concurrent multi-GPU job. |
| Batch size becomes zero or too small | `h.batch_size = int(h.batch_size / torch.cuda.device_count())`. | Set global `batch_size` at least equal to the number of visible GPUs and preferably divisible by it. |
| Expected single-GPU run spawned multiple workers | All visible GPUs are counted; JSON `num_gpus` is overwritten when CUDA is available. | Set `CUDA_VISIBLE_DEVICES=0` before running if you want one GPU. |
| Multi-node DDP hangs or rank mismatch | The code uses local rank from `mp.spawn()` and does not add a node-rank offset. | Treat upstream `train.py` as single-node DDP. Multi-node training requires an explicit code change/launcher design. |
| Multiple ranks write conflicting outputs | Only rank 0 should write checkpoints/logs in the source code; conflicts usually mean separate jobs reused one checkpoint path. | Give each job a unique `--checkpoint_path` and `dist_url`. |

## When to stop instead of retrying

Stop and ask for a new environment or narrowed scope when:

- No CUDA-capable device is available and the user requires actual training.
- The user wants CPU-only training; that is outside the upstream `train.py` behavior without code changes.
- A production fine-tuning run lacks teacher-forced mel `.npy` files or a tool/model to create them.
- Long training would require downloading a large private dataset or pretrained checkpoint not already available.
