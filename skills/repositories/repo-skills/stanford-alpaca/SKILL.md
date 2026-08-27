---
name: stanford-alpaca
description: "Routes Stanford Alpaca instruction-data, Self-Instruct generation,
  supervised fine-tuning, and LLaMA weight-diff recovery workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Stanford Alpaca

Use this root skill to route research tasks involving Stanford Alpaca's released instruction-following data, its historical Self-Instruct-style generator, Hugging Face supervised fine-tuning flow, or Alpaca/LLaMA weight-diff recovery. It is a self-contained operational guide: use its bundled references and helpers rather than reopening a source checkout.

## Start with the right route

| User need or signal | Read or run |
| --- | --- |
| Alpaca JSON/JSONL schema, prompt text, label masking, datasheet/model-card questions, data validation | [dataset-and-prompts](sub-skills/dataset-and-prompts/SKILL.md) |
| Seed tasks, prompt rendering, saved completion parsing, OpenAI completion API, `regen.json`, filtering, ROUGE-L deduplication | [instruction-generation](sub-skills/instruction-generation/SKILL.md) |
| `Trainer`, `torchrun`, FSDP, DeepSpeed, LLaMA/OPT SFT, OOM, batch-size planning, tokenizer/model preparation | [fine-tuning](sub-skills/fine-tuning/SKILL.md) |
| `path_raw`, `path_diff`, `path_tuned`, recovering or creating model weight differences, checksum, recovery inference | [weight-diff-recovery](sub-skills/weight-diff-recovery/SKILL.md) |

## Safe starting sequence

1. For any new or generated corpus, run the offline validator in `dataset-and-prompts` first. It accepts JSON arrays or JSONL, checks the `instruction`/`input`/`output` contract, and can show prompt previews.
2. For instruction synthesis, debug the bundled prompt renderer and saved-response parser before using a live API. Live completion calls require credentials, network access, and a legacy completion-compatible OpenAI client.
3. For SFT, build a launch command before launching it. The bundled command builder only prints text; full LLaMA/OPT jobs require an appropriate model checkpoint, CUDA environment, and enough memory.
4. For weight recovery, use the bundled dry-run command builder to distinguish raw, diff, and output checkpoint paths before loading any tensors.

## Runtime dependencies and capability gates

This is a script-oriented project rather than an installable Python distribution. To use every bundled helper, install a Python environment with PyTorch, Transformers, Fire, NumPy, rouge-score, sentencepiece, tokenizers, and an OpenAI client compatible with `openai.Completion.create`. A historically compatible baseline is `transformers==4.28.1`, `tokenizers==0.13.3`, `openai==0.27.8`, and `numpy<2` with older PyTorch builds.

Run the bundled cross-skill probe after installation:

```bash
python scripts/check_stanford_alpaca_env.py
```

- Use `--require-cuda` only when a CUDA workflow is actually required; CPU imports do not validate multi-GPU FSDP, DeepSpeed, or large-checkpoint recovery.
- Add DeepSpeed only for the optional ZeRO-3 offload path. Add experiment tracking integrations only if you explicitly enable them in Transformers.
- Keep OpenAI API keys in the process environment, never in scripts, datasets, prompts, or skill files.

## Boundaries and safety

- The released data and weight-diff artifacts carry non-commercial/research-use restrictions. Read [dataset intended use and licenses](sub-skills/dataset-and-prompts/references/intended-use-and-licenses.md) before using or distributing derived data, models, or recovered weights.
- This skill provides documentation and safe planning helpers; it does not claim that a live OpenAI call, a full GPU fine-tune, or real LLaMA checkpoint recovery has run in a later user's environment.
- Do not treat the historical training hyperparameters as universally optimal. Validate data, model compatibility, hardware, and evaluation goals for the current experiment.

## Shared references

- [Cross-cutting troubleshooting](references/troubleshooting.md): install/import compatibility, credentials, CUDA, data paths, artifacts, and licensing failures.
- [Repository provenance](references/repo-provenance.md): source commit and evidence baseline; read it before deciding whether a refresh is needed.
- [Environment probe](scripts/check_stanford_alpaca_env.py): inspect dependencies and optional CUDA availability without loading a model or calling a network service.

## Common multi-step routes

- **Generate then train:** `instruction-generation` -> `dataset-and-prompts` -> `fine-tuning`.
- **Use the released data directly:** `dataset-and-prompts` -> `fine-tuning`.
- **Recover then use a model:** `weight-diff-recovery` -> `fine-tuning` only if additional supervised training is intended.
