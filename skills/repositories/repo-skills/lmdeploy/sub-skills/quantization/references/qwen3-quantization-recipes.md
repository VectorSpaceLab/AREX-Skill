# Qwen3 Quantization Recipes

These recipes summarize the bundled Qwen3 `llm-compressor` examples as reference-only patterns. They are not required for ordinary `lmdeploy lite` AWQ/GPTQ flows, and they should be copied or adapted into the user's project only when the user intentionally wants the `llm-compressor` path.

## When To Use These Recipes

Use these patterns when:

- The target is Qwen3 or Qwen3 MoE and the user asks for `llm-compressor` rather than LMDeploy Lite.
- The user wants a compressed-tensors-style artifact that LMDeploy TurboMind can deploy.
- The user has already approved installing `llmcompressor`, `datasets`, and compatible `transformers`/`torch` dependencies.

Use `lmdeploy lite auto_awq` or `lmdeploy lite auto_gptq` instead when the user simply asks for standard LMDeploy Lite quantization.

## Shared Structure

Both Qwen3 reference scripts follow the same high-level structure:

1. Parse `--model-id` and required `--work-dir`.
2. Load `AutoModelForCausalLM.from_pretrained(..., dtype="auto", device_map="auto", trust_remote_code=True)`.
3. Load `AutoTokenizer.from_pretrained(..., trust_remote_code=True)`.
4. Build a calibration dataset from `neuralmagic/calibration`, split `train`, config `LLM`.
5. Use `NUM_CALIBRATION_SAMPLES = 256` and `MAX_SEQUENCE_LENGTH = 512`.
6. Apply the tokenizer chat template to user/assistant messages.
7. Run `llmcompressor.oneshot(...)` with the selected recipe.
8. Save the model and tokenizer to `--work-dir`.

## AWQ Recipe

The AWQ reference uses `AWQModifier`:

```python
AWQModifier(
    ignore=["lm_head", "re:.*mlp.gate$"],
    scheme="W4A16_ASYM",
    targets=["Linear"],
    duo_scaling="both",
)
```

Operational notes:

- The default model ID is `Qwen/Qwen3-30B-A3B`.
- The recipe ignores `lm_head` and MoE gate modules.
- `W4A16_ASYM` is the reference scheme.
- The calibration dataset requires network access unless already cached.
- This path may need substantially more memory than a small LMDeploy Lite run because `device_map="auto"` loads a large model before compression.

Example command after adapting the recipe into the user's own workspace:

```shell
python qwen3_awq_recipe.py --model-id Qwen/Qwen3-30B-A3B --work-dir ./qwen3_30b_a3b_awq
```

Deploy with TurboMind after verifying the saved config is recognized:

```shell
lmdeploy serve api_server ./qwen3_30b_a3b_awq --backend turbomind
```

If auto-detection fails and the artifact is AWQ-style grouped INT4, try `--model-format awq`; if the artifact uses compressed tensors metadata, let LMDeploy auto-detect or use the backend-specific guidance from `backend-extension`.

## GPTQ Recipe

The GPTQ reference uses `GPTQModifier`:

```python
GPTQModifier(
    targets="Linear",
    scheme="W4A16_ASYM",
    ignore=["lm_head", "re:.*mlp.gate$"],
)
```

Operational notes:

- The default model ID is `Qwen/Qwen3-30B-A3B`.
- The recipe has the same calibration dataset and preprocessing as AWQ.
- Use a GPTQ-specific output directory, such as `qwen3_30b_a3b_gptq`, to avoid AWQ/GPTQ loading mistakes.
- Deploy with a GPTQ-aware model format only when LMDeploy does not auto-detect correctly.

Example command after adapting the recipe into the user's own workspace:

```shell
python qwen3_gptq_recipe.py --model-id Qwen/Qwen3-30B-A3B --work-dir ./qwen3_30b_a3b_gptq
```

Deploy with TurboMind:

```shell
lmdeploy serve api_server ./qwen3_30b_a3b_gptq --backend turbomind --model-format gptq
```

## Adaptation Checklist

- Replace hard-coded output directories with user-approved paths.
- Confirm `trust_remote_code=True` is acceptable for the selected Qwen model.
- Confirm remote dataset access to `neuralmagic/calibration` or substitute an approved cached dataset.
- Keep `max_seq_length` and sample count small for first smoke tests; increase only when quality justifies the cost.
- Preserve ignored modules unless the user has validation evidence for changing them.
- Save tokenizer files alongside model weights so LMDeploy can serve the artifact.
- Record whether the result is AWQ, GPTQ, or compressed-tensors style before handing it off to pipeline or serving workflows.

## Accuracy Caveats

The documented Qwen3 evaluation showed that Qwen3-8B asymmetric AWQ can be competitive with BF16 on medium-output tasks, while long-output datasets can show larger drops. Treat long generation, coding, and math tasks as quality-sensitive validation targets rather than assuming a W4A16 artifact is acceptable from a smoke test alone.
