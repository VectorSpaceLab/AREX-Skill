---
name: synthesis-serving
description: "Guides Tacotron checkpoint loading, WAV synthesis, batch
  evaluation, and the Falcon demo server with matching hyperparameters and safe
  operational checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Synthesis and serving

Use this route for using a trained checkpoint, generating evaluation WAVs,
starting the browser demo, or diagnosing empty audio and checkpoint errors.
Read [`references/workflows.md`](references/workflows.md) before starting a
server or changing hparams.

## Workflow

1. Identify the exact checkpoint prefix, including its step suffix when using
   `model.ckpt-<step>`. Confirm sidecar checkpoint files and the hparams used to
   train it.
2. Use `eval.py --checkpoint <prefix>` for the built-in sentence batch, or
   `demo_server.py --checkpoint <prefix> --port 9000` for the browser UI.
3. Pass the same relevant `--hparams` string used during training. Cleaner names,
   audio dimensions, `outputs_per_step`, and `max_iters` are not cosmetic.
4. Test the command with the bundled builder first. Keep the server bound and
   exposed deliberately; the original demo listens on `0.0.0.0`.
5. Verify a generated WAV's sample rate and duration, and inspect endpoint
   trimming if output is silent or abruptly cut.
## Command roots and synthesis boundary

Build from the skill root and run native evaluation/serving only from the
checkout root. The checkpoint must be a real compatible prefix; it is not part
of this skill.

```bash
SKILL_ROOT=/path/to/tacotron-skill
CHECKOUT_ROOT=/path/to/tacotron-checkout
cd "$SKILL_ROOT" && python sub-skills/synthesis-serving/scripts/build_synthesis_command.py --checkout-root "$CHECKOUT_ROOT" --mode eval --checkpoint /data/logs-tacotron/model.ckpt-185000
```

This repository reconstructs WAVs with its `librosa`/SciPy Griffin-Lim path; it
does not use or bundle a neural vocoder. Real synthesis additionally requires
the legacy TensorFlow/audio/Falcon dependencies as applicable, checkpoint sidecar
files, writable output space, and matching hparams. The builder checks only
command syntax: it loads no checkpoint, opens no port, and proves no audio
quality, endpoint behavior, or server security. Full eval and server execution
remain unverified without supplied weights and an approved local listener.

Read [`references/api-reference.md`](references/api-reference.md) for
`Synthesizer` lifecycle and endpoints, [`references/cli-reference.md`](references/cli-reference.md)
for exact flags, and [`references/troubleshooting.md`](references/troubleshooting.md)
for checkpoint, hparam, text, and network-boundary failures. Use
[`scripts/build_synthesis_command.py`](scripts/build_synthesis_command.py) to
build eval/server commands without loading a checkpoint or opening a port.
