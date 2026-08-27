---
name: encrypted-distilbert
description: "Run and troubleshoot Nesa's encrypted DistilBERT sentiment demo
  and local Hugging Face model workflow."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Encrypted DistilBERT Demo

Use this sub-skill when the user wants to run, adapt, or debug the small Nesa
Equivariant Encryption sentiment-classification demo.

Typical triggers:

- "run the Nesa DistilBERT demo"
- "load `nesaorg/distilbert-sentiment-encrypted`"
- "show encrypted token IDs before sentiment inference"
- "why does the encrypted sentiment demo fail?"
- "compare local model files vs Hugging Face model id"

## What this workflow demonstrates

The demo is a client/server simulation:

1. The client receives plaintext text.
2. The encrypted tokenizer turns text into token IDs.
3. The simulated server sees the token IDs and runs an encrypted DistilBERT
   sequence-classification model.
4. The client receives probabilities/logits and maps labels locally.

The public demo is educational. The model card says the community version is an
approximation of the enterprise implementation and may reproduce the original
model's output only about 92% of the time.

## Choose an execution mode

- **Local model directory:** best when the user has a directory containing
  `config.json`, tokenizer files, and model weights. Validate it with
  [scripts/validate_model_dir.py](scripts/validate_model_dir.py) before loading.
- **Hugging Face model id:** best when the user permits network downloads and
  cache use. Use [scripts/run_local_demo.py](scripts/run_local_demo.py) with a
  model id or local directory.
- **Web UI DistilBERT mode:** route to
  [web-ui-runtime](../web-ui-runtime/SKILL.md) for browser UI startup and model
  selection, then return here for interpreting local classification output.

## Minimal dependency set

For a CPU-only local check:

```bash
python -m pip install torch transformers safetensors
```

Add `accelerate` only if the selected model-loading path or web UI requires it.
Do not install GPU wheels unless the user needs GPU verification.

## Recommended workflow

1. Clarify whether the user has a local model directory or wants a Hugging Face
   model id.
2. If using a local directory, run the bundled validator:

   ```bash
   python scripts/validate_model_dir.py /path/to/model-dir
   ```

3. Run the bundled demo wrapper with a short prompt:

   ```bash
   python scripts/run_local_demo.py --model /path/to/model-dir --prompt "I love private AI"
   ```

   Or, when network access is allowed:

   ```bash
   python scripts/run_local_demo.py --model nesaorg/distilbert-sentiment-encrypted --prompt "I love private AI"
   ```

4. Report the encrypted token IDs, label probabilities, highest label, and any
   assumptions about local vs network model loading.
5. If a load fails, read [references/troubleshooting.md](references/troubleshooting.md)
   before changing dependencies or model paths.

## References and scripts

- [references/workflow.md](references/workflow.md): detailed local and HF demo
  recipes, inputs/outputs, and validation steps.
- [references/model-card.md](references/model-card.md): distilled model metadata,
  limitations, and interpretation notes.
- [references/troubleshooting.md](references/troubleshooting.md): failure modes
  for missing files, dependency errors, tokenizer/model mismatch, and slow CPU.
- [scripts/validate_model_dir.py](scripts/validate_model_dir.py): read-only local
  model-directory validator.
- [scripts/run_local_demo.py](scripts/run_local_demo.py): standalone, promptable
  DistilBERT sentiment demo wrapper.

## Boundaries

- Do not use this sub-skill for full web UI installation or one-click scripts;
  route to `web-ui-runtime`.
- Do not use this sub-skill to send remote encrypted Llama requests; route to
  `backend-protocol`.
- Do not claim the demo proves enterprise-grade security; route contest/security
  reasoning to `security-contest`.
