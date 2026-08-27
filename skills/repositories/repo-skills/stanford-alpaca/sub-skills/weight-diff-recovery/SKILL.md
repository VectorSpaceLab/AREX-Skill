---
name: weight-diff-recovery
description: "Guide Alpaca weight-diff creation and recovery, path-role
  validation, tokenizer pad-token resizing, integrity checks, and safe dry-run
  planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Weight Diff Recovery

Use this sub-skill when the task is about Alpaca/LLaMA weight diffs rather than supervised fine-tuning or data generation.

## Route Here For
- Recovering Alpaca weights from the released diff after the raw Meta LLaMA checkpoint has been converted to Hugging Face format.
- Creating a fresh weight diff from a raw/tuned checkpoint pair.
- Checking checkpoint path roles, output locations, device choice, tokenizer pad-token resizing, naive integrity checks, or a short inference smoke run.
- Planning a recovery command without loading checkpoints yet.

## Route Elsewhere
- Supervised fine-tuning, later downstream use of recovered weights, or training recipes: `../fine-tuning/SKILL.md`
- License/intended-use context, prompt provenance, or dataset handling: `../dataset-and-prompts/SKILL.md`
- Prompt synthesis or seed-task generation details: `../instruction-generation/SKILL.md`

## Fast Workflow
1. Confirm the mode:
   - `recover`: `path_raw` + `path_diff` -> optional `path_tuned`
   - `make_diff`: `path_raw` + `path_tuned` -> `path_diff`
2. Verify prerequisites before any live load:
   - `path_raw` points to the Hugging Face-converted LLaMA checkpoint directory.
   - `path_diff` points to the released Alpaca weight-diff directory.
   - `path_tuned` is either the tuned input for `make_diff` or the recovery output directory for `recover`.
   - You have the relevant LLaMA access and non-commercial license context for the diff/artifacts; read the bundled [intended-use and licenses reference](../dataset-and-prompts/references/intended-use-and-licenses.md) before sharing outputs.
3. Run `scripts/build_weight_diff_command.py` to validate the path roles and print a safe dry-run command.
4. If you intend to execute, use `scripts/alpaca_weight_diff.py` with the chosen device.
5. Treat the checksum and smoke inference as sanity checks only.

## Key Rules
- `make_diff` computes `diff-minus-raw`; `recover` computes `diff-plus-raw`.
- When the raw tokenizer has no pad token, resize the tokenizer and both embedding matrices before subtraction/addition.
- `device="cpu"` is the safest inspection default. Switch to `cuda` only if the hardware is available and the checkpoint fits.
- `path_tuned` is optional on `recover`; when omitted, nothing is saved.
- The naive checksum is a heuristic. A matching value is useful, but a mismatch is not a cryptographic proof of failure.
- The inference smoke is qualitative only and can fail for prompt-format, device, or memory reasons unrelated to weight correctness.

## References and scripts

- Read [workflows](references/workflows.md) for recover/make-diff recipes, path roles, and execution gates.
- Read [API reference](references/api-reference.md) for verified function signatures, parameters, and return/save behavior.
- Read [troubleshooting](references/troubleshooting.md) for missing checkpoints, tokenizer mismatches, OOM, device errors, and checksum failures.
- Run [build_weight_diff_command.py](scripts/build_weight_diff_command.py) to validate path roles and print a dry-run command before tensor loads.
- Run [alpaca_weight_diff.py](scripts/alpaca_weight_diff.py) only when you intentionally want the self-contained live/dry-run runner.
