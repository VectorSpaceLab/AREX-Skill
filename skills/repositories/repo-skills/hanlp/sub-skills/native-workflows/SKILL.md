---
name: native-workflows
description: "Guides local HanLP native Python workflows with pretrained model
  loading, pipeline composition, task selection, cache/device controls, and
  no-download smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Native Workflows

Use this sub-skill when a task needs local Python HanLP rather than only a RESTful service: `hanlp.load`, `hanlp.pretrained`, `hanlp.pipeline`, MTL task selection, sentence splitting, device/cache controls, or a safe no-download smoke check.

## Read First

- Read `references/native-api-reference.md` for verified signatures, local inference patterns, pipeline composition, `tasks`, `skip_tasks`, and device arguments.
- Read `references/pretrained-models.md` for model-family routing, identifier names, language/task coverage, and download/cache caveats.
- Read `references/troubleshooting.md` for model download, cache, device, and local input-shape failures.
- Run `scripts/pipeline_smoke.py` to verify no-download `hanlp.pipeline` behavior.
- Run `scripts/split_sentence_smoke.py` for deterministic sentence splitting without loading a pretrained EOS model.

## Minimal Native Check

```bash
python -c "import hanlp; print(hanlp.__version__, len(hanlp.pretrained.ALL))"
```

This confirms import and identifier registration. It does not prove that a pretrained model archive is downloaded or that GPU acceleration works.

## Route by Native Task

| User need | Use |
| --- | --- |
| Load a pretrained MTL or single-task model by identifier or URL | `hanlp.load(identifier, devices=..., verbose=...)` in `references/native-api-reference.md` |
| Pick model families for tokenization, POS, NER, dependency/constituency parsing, SRL, SDP, AMR, classification, STS, or language ID | `references/pretrained-models.md` |
| Run fewer tasks or use pre-tokenized input with an MTL model | `tasks=` and `skip_tasks=` notes in `references/native-api-reference.md` |
| Split a document before local sentence-level models | `scripts/split_sentence_smoke.py` and sentence-splitting notes |
| Compose several single-task components | `hanlp.pipeline().append(..., input_key=..., output_key=...)` |

## Common Decisions

- Native MTL models expect sentence-level inputs. Split raw documents before passing them to local MTL models.
- Loading a model may recursively download dependencies. Make cache and network assumptions explicit before promising offline execution.
- Use `devices=-1` for CPU-oriented checks when the component supports it. Use GPU devices only after verifying a compatible GPU-enabled backend.
- Use `tasks` to limit output work and `skip_tasks='tok*'` when passing pre-tokenized sentences to compatible MTL models.
