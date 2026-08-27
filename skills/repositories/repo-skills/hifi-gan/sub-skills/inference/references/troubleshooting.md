# Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| `AssertionError` in `load_checkpoint(...)` or the checkpoint file is missing | The checkpoint path is wrong or the file does not exist | Point `--checkpoint_file` at an actual `g_########` file. The directory beside it must also contain `config.json`. |
| `FileNotFoundError` or `JSONDecodeError` while opening `config.json` | The paired config is missing or malformed | Copy the exact `config.json` that was used for the generator into the checkpoint directory. |
| `RuntimeError` / size mismatch from `load_state_dict` | The checkpoint and config family do not match | Use the same family for both files. If you need to test recovery, generate an intentional mismatch with `scripts/make_dummy_checkpoint.py`. |
| No outputs appear and no error is printed | The input directory is empty | Populate the directory with the intended files only. The scripts iterate `os.listdir(...)` and do not filter the directory entries. |
| `IsADirectoryError`, WAV read errors, or other load failures in the input loop | The input directory contains subdirectories, hidden files, or non-matching files | Keep only the intended `.wav` or `.npy` files in the input folder, or pre-clean it before running. |
| `inference_e2e.py` fails in Conv1d or with a rank error | The mel `.npy` has the wrong rank, wrong channel count, or malformed dtype | Use `float32` arrays with 80 mel bins and rank 2 or 3. For a negative test, use `--mel-rank 1`. |
| Output sounds wrong but the script ran | The input wav sample rate differs from the config or the source wav is stereo / unsupported | Use mono 16-bit PCM wavs that already match the paired config sample rate. The script does not resample or downmix. |
| Output files overwrite earlier runs | The same output directory or filenames were reused | Use a fresh `--output_dir` for each run, or clean it first. The WAV writer overwrites files with the same name. |
| Unexpected output filename | The file stem is derived from `os.path.splitext(...)`, so only the final extension is removed | Rename the input if you need a different stem. `foo.bar.wav` becomes `foo.bar_generated.wav`. |
| `PermissionError` or the output path already exists as a file | The output directory is not writable or collides with a file path | Choose a writable directory path. `os.makedirs(..., exist_ok=True)` only helps when the path is a directory. |
| CUDA is unavailable or a GPU run fails at startup | Driver / CUDA / torch mismatch, or you are on a CPU-only host | The scripts fall back to CPU when `torch.cuda.is_available()` is false. If you expected GPU, verify `torch.cuda.get_device_name(0)` in a clean torch shell and compare it to the verified inspection stack. |
| `ModuleNotFoundError: No module named 'librosa'` during `--help` or launch | The audio stack is incomplete even though torch imports | Install the repo's audio dependencies; the verified inspection stack had `librosa 0.10.2.post1` with `librosa.util.normalize` available. |
| `mel() takes 0 positional arguments` or `stft requires the return_complex parameter` | The copied HiFi-GAN runtime source is running on a newer librosa or PyTorch stack | Use `scripts/infer_hifigan.py` or `scripts/run_inference_smoke.py`, which apply local compatibility shims, or pin/patch the runtime stack deliberately before production inference. |
