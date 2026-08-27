# Conversion and Quantization

## Verified CLI

`python -m mlx_audio.convert`

## Important Flags

- `--hf-path`: source Hugging Face repo or local path
- `--mlx-path`: destination directory
- `--quantize` / `-q`: enable quantization
- `--q-bits`: quantization bit width
- `--q-group-size`: group size
- `--q-mode`: `affine`, `mxfp4`, `mxfp8`, or `nvfp4`
- `--quant-predicate`: mixed-precision recipe such as `mixed_3_4`
- `--dtype`: convert weights without quantizing
- `--dequantize`: undo a quantized checkpoint
- `--upload-repo`: upload the converted model
- `--revision`: select a source revision
- `--model-domain`: force `tts`, `stt`, `sts`, or `lid`

## Practical Behavior

- The converter auto-detects the model domain when `--model-domain` is omitted.
- `--quantize` and `--dequantize` are mutually exclusive.
- `--dtype` is the non-quantized path.
- `--quant-predicate` is only relevant when quantizing.
- The converter copies supporting files into the output directory and writes a new `config.json`.

## Safe Planning

- Confirm the source repo id and the target output path before starting a long conversion.
- Check the quantization mode and bit width before the run.
- Use the command builder to catch mutually exclusive or missing flags early.
