---
name: components-metrics
description: "Guides SpeechBrain model components, decoders, losses, metric
  statistics, WER scoring, checkpoints, Pretrainer, streaming helpers, and
  component-level troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SpeechBrain components and metrics

Use this sub-skill when the task is to choose, wire, debug, or test SpeechBrain neural components, decoders, metrics, checkpoints, pretrained-weight loading, streaming helpers, or scoring utilities.

## Route map

| Task | Read/run |
| --- | --- |
| Select neural modules, lobes, feature wrappers, decoders, or losses. | `references/components-and-decoders.md` |
| Save/recover checkpoints or load pretrained weights into modules. | `references/checkpoints-and-pretraining.md` |
| Compute WER/PER/CER, metric stats, classification/binary metrics, or scoring summaries. | `references/metrics-and-scoring.md`; run `scripts/compute_wer_cli.py`. |
| Work on streaming/chunked ASR or streaming feature wrappers. | `references/streaming.md` |
| Diagnose shape, checkpoint, metric, decoder, or streaming failures. | `references/troubleshooting.md` |

## Common component workflow

1. Keep model/module construction in HyperPyYAML when possible.
2. Use recipe `Brain` hooks to wire forward/objective/metric behavior.
3. Validate tensor shapes and relative lengths before decoder or metric calls.
4. Use `Checkpointer` for local experiment state and `Pretrainer` for fetching/loading pretrained model files.
5. Use metric stats classes inside `on_stage_start` / `compute_objectives` / `on_stage_end` patterns.

## Useful bundled script

```bash
python scripts/compute_wer_cli.py ref.txt hyp.txt --mode strict
```

The script is adapted from SpeechBrain's WER utility pattern and uses the installed package only.
