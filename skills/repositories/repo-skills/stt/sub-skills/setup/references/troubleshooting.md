# Troubleshooting

Use the bundled checks in this order when setup or launch fails:

1. `python ../../../scripts/check-runtime.py --repo-root <checkout>`
2. `python ../scripts/check-cuda.py` if `devtype=cuda`
3. `python ../scripts/launch-server.py --repo-root <checkout>`

If the app launcher exits immediately, inspect the console output and the runtime log file in the checkout.

## Python version or import failures

**Symptoms**
- the app will not start
- imports fail during the runtime check
- torch, flask, gevent, or faster-whisper cannot load

**Likely causes**
- Python outside the supported 3.9-3.11 range
- a broken or mixed virtual environment
- a failed dependency install
- a NumPy 2 / torch compatibility issue in a fresh environment

**Fix**
- use a clean virtual environment with Python 3.11 when possible
- reinstall `requirements.txt`
- if the resolver complains, retry with `--no-deps`
- if torch import warnings mention NumPy 2, pin `numpy<2` and retry the runtime check

## Missing ffmpeg or ffprobe

**Symptoms**
- upload conversion fails
- the runtime check says `ffmpeg` or `ffprobe` is missing
- API requests return a conversion error before transcription begins

**Likely causes**
- the binaries are not installed
- the binaries are not on `PATH`
- the local copy is missing from the project root or `ffmpeg/` directory

**Fix**
- install ffmpeg system-wide, or
- place both binaries beside the project files, or
- place both binaries in a local `ffmpeg/` directory

The app expects both commands to resolve before file conversion can work.

## Missing models or first-run download failures

**Symptoms**
- the selected model does not load
- the app reports that a model file is missing
- the first transcription attempt hangs or fails while trying to download a model

**Likely causes**
- `models/` is empty
- the chosen model folder was not copied into place
- the host cannot reach Hugging Face or the mirror endpoint

**Fix**
- copy the required model folder into `models/`
- use a smaller model for the first launch if disk or network is limited
- allow outbound network access for the first download, or pre-stage the model offline

## CUDA or cuDNN mismatch

**Symptoms**
- `devtype=cuda` launches but transcription fails
- the CUDA probe says CUDA is available but cuDNN is not
- the probe reports an unacceptable CUDA / cuDNN combination
- the app crashes on launch or on the first GPU inference

**Likely causes**
- the torch wheel does not match the installed CUDA stack
- the CUDA toolkit and driver are mismatched
- the cuDNN version does not match the installed CUDA version
- `devtype=cuda` was selected before the GPU stack was ready

**Fix**
- run `python ../scripts/check-cuda.py --strict` when CUDA is required
- reinstall the CUDA torch wheel
- install the matching cuDNN release for your CUDA major version
- if you do not need GPU acceleration, switch back to `devtype=cpu`

## Windows `cublasxx.dll` errors

**Symptoms**
- Windows reports that `cublasxx.dll` is missing
- startup fails immediately on an NVIDIA machine

**Likely causes**
- the CUDA DLL set is incomplete on Windows
- the required cuBLAS files were not copied into the system path

**Fix**
- install the correct cuBLAS / CUDA support files for the host
- copy the required DLLs into the Windows system directory if that is the deployment pattern you are using
- fall back to `devtype=cpu` if the machine is only intended for CPU inference

## Large-model memory exhaustion

**Symptoms**
- `large` or `large-v3` crashes the process
- the GPU runs out of memory
- the machine becomes unstable on the first transcription

**Likely causes**
- the model is too large for the available VRAM or RAM
- VAD, beam search, and previous-text conditioning are using extra memory

**Fix**
- switch to `medium` or a smaller model
- keep `beam_size` and `best_of` conservative
- keep `condition_on_previous_text=false`
- disable `vad` if you need to reduce pressure further
- stay on CPU mode if the GPU is not large enough for the chosen model

## Update-check noise

**Symptoms**
- startup prints an update-related message or nothing at all from the update thread
- the host is offline and you see no update result

**Likely cause**
- the background update check cannot reach the remote version file

**Fix**
- none required for normal operation
- this is a background convenience check and does not block launch

## CPU mode on a CUDA-ready host

If the machine has a working NVIDIA stack but you still want CPU execution, keep `devtype=cpu`. The launcher will not force CUDA just because the hardware can use it.

## When to stop troubleshooting and switch skills

If the server launches successfully and the browser opens, switch to [`transcription`](../../transcription/SKILL.md) for upload flow, `/api`, and client usage.
