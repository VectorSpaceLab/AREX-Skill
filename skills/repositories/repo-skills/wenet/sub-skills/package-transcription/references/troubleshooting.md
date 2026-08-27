# Package Transcription Troubleshooting

## Import fails before any model is loaded

Symptoms:

- `ImportError` while importing `wenet`
- PyTorch internal import errors
- NumPy ABI warnings such as modules compiled for NumPy 1.x

Likely causes and recovery:

1. Use a Python version supported by the package and its ML dependencies.
2. Prefer the WeNet-documented PyTorch/Torchaudio pairing (`torch==2.2.2`,
   `torchaudio==2.2.2`) when a newer PyTorch changes internal APIs.
3. If PyTorch reports a NumPy ABI warning, pin `numpy<2` unless the full stack
   is known to support NumPy 2.x.
4. Run the bundled checker with no model directory to verify imports:

   ```bash
   python sub-skills/package-transcription/scripts/check_wenet_package.py
   ```

## Local model directory is incomplete

Symptoms:

- `FileNotFoundError: Required file train.yaml/final.pt/units.txt not found`
- model loads from the wrong directory
- tokenizer or feature setup fails

Recovery:

```bash
python sub-skills/package-transcription/scripts/check_wenet_package.py \
  --model-dir /path/to/model_dir
```

Add or locate the missing `train.yaml`, `final.pt`, and `units.txt` files. A
`global_cmvn` file is optional, but if present it is used by `load_model()`.

## Built-in model loading stalls or fails

Symptoms:

- network timeouts
- download starts unexpectedly
- unsupported model key exits the process

Built-in keys go through WeNet's model hub and can download archives. If the
environment has no network or model-cache permission, use a local model
directory instead. Check the intended key spelling; prefer `whisper-*` keys over
legacy `whiper-*` names unless matching an existing asset.

## CUDA or NPU device fails

Symptoms:

- `--device cuda` accepted by the parser but PyTorch says CUDA is unavailable
- CUDA library/driver errors
- `npu` selected but `torch_npu` is missing

Recovery:

1. Validate backend availability before loading the model:

   ```bash
   python sub-skills/package-transcription/scripts/check_wenet_package.py \
     --device cuda
   ```

2. Use `--device cpu` if GPU/NPU is not required.
3. For CUDA, install a PyTorch build compatible with the driver and GPU.
4. For Ascend NPU, install the CANN toolkit and the matching `torch-npu` extra;
   do not assume ordinary PyTorch CUDA wheels can run NPU paths.

## Audio, alignment, context, or punctuation options fail

- Confirm the `audio_file` positional argument exists and is readable.
- Forced alignment requires both `--align` and `--label`.
- Context biasing requires a readable context list and a suitable model path;
  tune `--context_score` instead of raising it blindly.
- Punctuation requires a punctuation model. Use `--punc_model_dir` when not
  relying on the built-in punctuation asset.
- Token timing/confidence output from `--show_tokens_info` depends on model
  support; if the result object lacks token details, fall back to text-only
  transcription.

## Sox and audio backend issues

Training docs mention sox compatibility problems for feature extraction. If
PyTorch/Torchaudio reports that the sox extension or audio backend is missing,
install sox/libsox through the target platform package manager or Conda and
retry the package check before debugging model code.
