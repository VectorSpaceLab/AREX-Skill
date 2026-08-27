---
name: "inference-serving"
description: "Run PointLLM point-cloud chat, batched generation, and the Gradio
  demo with the correct model registration, point-token prompt, GPU, input, and
  output contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: CC BY-NC-SA 4.0
---

# PointLLM inference-serving

Use this route when a task loads a trained PointLLM checkpoint, chats about a
colored point cloud, generates Objaverse or ModelNet outputs in batches, or
starts the Gradio point-cloud demo.

## Route boundaries

- Data downloads, annotation layout, and dataset acquisition belong to the
  sibling [data-preparation](../data-preparation/SKILL.md) route.
- GPT/ChatGPT scoring, traditional metrics, and evaluator internals belong to
  the sibling [evaluation](../evaluation/SKILL.md) route.
- This route does cover the inference-side JSON artifact written by the two
  generation launchers, but not how those artifacts are scored.

## Start with the contract

1. Read [workflows](references/workflows.md) for model loading, one-object
   chat, batch generation, and Gradio startup.
2. Read [api-reference](references/api-reference.md) for registration,
   tokenizer/point-token invariants, preprocessing, and JSON output shapes.
3. Read [cli-reference](references/cli-reference.md) before copying a launcher
   command. It records every supported flag and its source default.
4. For a local file, run the dependency-light checker first:

   ```bash
   python scripts/check_pointcloud.py cloud.npy
   ```

   Use `--strict` when a malformed input must fail a CI check. The checker does
   not load a checkpoint, contact the network, or require CUDA.
5. Use [troubleshooting](references/troubleshooting.md) for install/import,
   backend, input, context, CLI, and output failures. Run the bundled scripts
   from this sub-skill directory; use the root skill's
   `scripts/run_installed_cli.py` for historical package launchers.

## Non-negotiable runtime facts

- The inspected target environment was Python 3.10, torch 2.0.1+cu117,
  Transformers 4.28.0.dev0 at commit `cae78c46`, tokenizers 0.12.1, and an
  A100 40 GB (CUDA capability 8.0). The package reports version 0.1.2.
- The launchers call `.cuda()` directly and load full checkpoints. This is a
  CUDA inference workflow; do not promise CPU inference or CPU fallback.
- Load the tokenizer with `AutoTokenizer.from_pretrained(model_name)` and the
  registered model with `PointLLMLlamaForCausalLM.from_pretrained(...)`, then
  call `initialize_tokenizer_point_backbone_config_wo_embedding(tokenizer)`
  before generation.
- Point input is `N x 6`: `xyz` followed by RGB in `[0, 1]`. Normalize XYZ by
  subtracting its centroid and dividing by its maximum radius. The usual
  training/inference size is 8192 points; FPS downsampling is used when an
  uploaded cloud is larger.
- Prompts must contain exactly the model-reported number of point patch tokens
  (`point_token_len`, normally `512 + 1 = 513` with the v1.2 PointBERT config),
  optionally enclosed by the configured start/end tokens. Do not substitute a
  literal number if the checkpoint config reports another value.
- The chat/demo conversation is `vicuna_v1_1`: roles `USER` and `ASSISTANT`,
  two separators (`" "` and `</s>`), and the assistant stop string is `</s>`.
  The model context is 2048 tokens; generation uses `max_length=2048`, which
  is the total input-plus-output length, not 2048 new tokens.

## Safe operating order

1. Confirm the checkpoint, tokenizer, GPU, and dtype budget. Use the full
   checkpoint; do not use a CPU smoke test as evidence of serving readiness.
2. Validate a local PLY/NPY with the bundled checker. Treat an Objaverse ID
   as a networked data path, not a safe smoke test.
3. For a first model-backed run, use one object and one question. Keep the
   conversation short enough that the 513 point tokens plus prompt leave output
   room.
4. For batch generation, leave `--shuffle` at its `False` default. The scripts
   write JSON under `<model_name>/evaluation/` and reuse an existing output
   instead of regenerating it.
5. Start Gradio only after a file-based chat path works. The public server
   posture is not hardened by this research demo; keep `share=False` and use a
   deliberate temporary directory.

## CLI smoke boundary

The four native candidates are `--help` for PointLLM chat, Gradio chat,
Objaverse generation, and ModelNet generation. They import the full package
before argparse runs, so a missing `easydict`, PointBERT/timm, Open3D, or other
package can make `--help` fail without downloading a model. Use
`scripts/inspect_cli.py` for a no-import, help-only contract check, and report
native help failures as environment evidence rather than silently changing the
launcher.

## Handoffs and review checks

- If the request asks how to obtain Objaverse/ModelNet files, hand off to the
  data sibling rather than adding a download recipe here.
- If it asks for accuracy, BLEU/ROUGE/METEOR, or GPT cost, hand off to the
  evaluation sibling.
- Before declaring success, verify the exact output JSON path, `prompt`, result
  count, object IDs, and whether a prior JSON file caused the script to skip
  generation. See the output contract in [api-reference](references/api-reference.md).
