# MOSS inference troubleshooting

## Prompt marker mistakes

**Symptoms**: model echoes role markers, never stops, or treats the user turn as
assistant output.

**Recovery**

- Start the generation point with `<|MOSS|>:`.
- End human turns with `<eoh>` and previous assistant turns with `<eom>`.
- Do not add plugin sections unless the model/task expects plugin formatting.
- Use `scripts/build_moss_prompt.py --query ... --json` to inspect exact prompt
  text before running a model.

## Quantized model with multiple GPUs

**Symptom**: `ValueError: Quantized models do not support model parallel`.

**Recovery**

- Use `OpenMOSS-Team/moss-moon-003-sft-int4` or `*-int8` on a single GPU.
- Use `OpenMOSS-Team/moss-moon-003-sft` for multi-GPU model parallelism.
- Validate with `scripts/inspect_cli_flags.py --model-name ... --gpu ...`.

## Missing checkpoints or network stalls

**Symptoms**: Hugging Face snapshot download fails, model path not found, loading
hangs before generation.

**Recovery**

- Decide whether `--model_name` is a Hugging Face id or a complete local
  checkpoint directory.
- Pre-download large checkpoints when network is unreliable.
- Keep tokenizer/config/model shards from the same checkpoint family.
- Do not run demo scripts just for flag validation; use bundled helpers first.

## CUDA out of memory

**Symptoms**: OOM during `from_pretrained`, Accelerate dispatch, or generation;
OOM appears after several turns.

**Recovery**

- Compare precision against the memory table in the root model overview.
- Reduce history length and `max_length`/`max_iterations`.
- Use INT4 for single-GPU low-memory inference.
- Use FP16 model parallelism for multi-GPU only.
- Clear old model processes before retrying.

## Missing Jittor

**Symptom**: `ModuleNotFoundError: No module named 'jittor'` from the Jittor CLI.

**Recovery**

- Treat Jittor as optional; the default requirements do not install it.
- Use the PyTorch CLI unless a task specifically requires Jittor.
- If Jittor is required, install it intentionally for the host and verify a
  minimal Jittor import before running checkpoint conversion/loading.

## Stop-token and length issues

**Symptoms**: generation continues too long, stops too early, or includes raw
`<eom>`/special tokens in output.

**Recovery**

- The demos use EOS token id 106068, corresponding to `<eom>`.
- Preserve history only up to the 2048 context budget.
- Decode only new tokens after the input prompt when using `model.generate`.
- Use `skip_special_tokens=True` when presenting generated text.

## Tool/plugin confusion

Plugin data demonstrates commands such as `Search(...)`, `Calculate(...)`,
`Solve(...)`, and `Text2Image(...)`, but the source demo does not bundle live
external tools. If a task asks for real tool execution, ensure the surrounding
system provides those tools; otherwise explain that the prompt can be formatted
for a plugin-trained model but cannot execute tools by itself.
