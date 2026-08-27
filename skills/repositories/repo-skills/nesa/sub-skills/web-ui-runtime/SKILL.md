---
name: web-ui-runtime
description: "Install, configure, launch, and troubleshoot Nesa's encrypted AI
  web UI and model-management runtime."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NO_LICENSE
---

# Nesa Web UI Runtime

Use this sub-skill when the user asks about the local browser demo, one-click
installation, model downloads, CPU/GPU flags, web UI settings, or how Nesa plugs
into the text-generation web UI.

Typical triggers:

- "start the Nesa demo UI"
- "why does the one-click installer fail?"
- "switch the demo from CPU to GPU"
- "download or select encrypted models in the UI"
- "what does `equivariant-encrypt` mode do?"

## Decide the runtime target

Ask or infer these before running commands:

1. Operating system: Linux, macOS, or Windows.
2. Backend target: CPU, NVIDIA CUDA, AMD ROCm, Apple M-series/MPS, Intel Arc, or
   unknown.
3. Whether the user permits environment mutation and model downloads.
4. Whether the UI should be local-only or reachable from other hosts.
5. Which model path is needed: encrypted DistilBERT local classification or
   encrypted Llama remote streaming.

If the user only needs the small sentiment demo, route to
[encrypted-distilbert](../encrypted-distilbert/SKILL.md) instead of launching the
full web UI.

## Safe-first workflow

1. Read [references/installation-and-runtime.md](references/installation-and-runtime.md)
   for the platform and backend decision matrix.
2. Validate settings/flags before launch:

   ```bash
   python scripts/validate_runtime_config.py --settings /path/to/settings.yaml --cmd-flags /path/to/CMD_FLAGS.txt
   ```

3. Preview model-download naming before network downloads:

   ```bash
   python scripts/check_hf_model_plan.py nesaorg/distilbert-sentiment-encrypted
   ```

4. Only then run user-approved installer or launch commands.
5. If anything fails, read [references/troubleshooting.md](references/troubleshooting.md)
   before installing broad extras or switching backend variants.

## Important repo-specific behavior

- The checked default command flags include CPU mode.
- The settings template uses `mode: equivariant-encrypt`.
- The UI model menu dispatches selected model names through Nesa's model
  registry rather than ordinary generic loader behavior for the supported Nesa
  models.
- Model download helpers can fetch or checksum Hugging Face model files, but
  that is a network and disk-writing operation.
- Launching the UI can bind to `0.0.0.0`; never expose it without auth unless
  the user explicitly approves that risk.

## References and scripts

- [references/installation-and-runtime.md](references/installation-and-runtime.md):
  platform installer flow, dependency variants, backend choices, and launch
  advice.
- [references/configuration.md](references/configuration.md): settings fields,
  command flags, and `equivariant-encrypt` mode details.
- [references/webui-integration.md](references/webui-integration.md): model menu,
  registry dispatch, download helper, and prompt-flow integration.
- [references/troubleshooting.md](references/troubleshooting.md): install,
  runtime, model-download, and public-serving failure modes.
- [scripts/validate_runtime_config.py](scripts/validate_runtime_config.py):
  read-only settings and command-flag validator.
- [scripts/check_hf_model_plan.py](scripts/check_hf_model_plan.py): safe model id,
  branch, and output-folder preview without downloading files.

## Boundaries

- Do not use this sub-skill for low-level request struct changes; route to
  [backend-protocol](../backend-protocol/SKILL.md).
- Do not use this sub-skill for contest scoring/attack baselines; route to
  [security-contest](../security-contest/SKILL.md).
- Do not run one-click installers, large downloads, or web UI launch commands
  without user approval.
