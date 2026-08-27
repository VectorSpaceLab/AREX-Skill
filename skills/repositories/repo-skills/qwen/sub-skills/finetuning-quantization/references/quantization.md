# GPTQ Quantization and Post-training Conversion

## When to read

Read this when the user wants to quantize a fine-tuned Qwen checkpoint or reason about Int4/Int8 conversion after training.

## Repository flow

1. Prepare calibration data that follows the same conversation structure as fine-tuning data.
2. Run `run_gptq.py` with the model path, calibration data path, output path, `--bits`, and `--group-size`.
3. Copy the needed checkpoint-side Python and kernel files into the output directory when the downstream inference path requires them.
4. Rename the generated weight file into the final model layout expected by the loader.
5. Validate the resulting checkpoint with the inference sub-skill, not by assuming the quantization step alone proves usability.

## Compatibility cautions

- AutoGPTQ compatibility depends on torch/CUDA/Transformers/Optimum/PEFT versions.
- Some model/torch combinations need a specific wheel rather than a source build.
- Int4/Int8 checkpoint names are not interchangeable with BF16 chat checkpoints.
- Quantized checkpoints may still need checkpoint-side code files for special inference features.

## Failure signals

- `auto_gptq` import errors or wheel mismatch: isolate a compatible environment.
- Missing calibration data or wrong schema: run the data validator first.
- Quantization succeeds but inference fails: the output directory may be missing checkpoint-side support files or the final loader is pointing at the wrong model family.
