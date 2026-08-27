---
name: datasets
description: "Validate and troubleshoot InternVideo dataset layouts, annotation
  schemas, and data-readiness across generations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# InternVideo datasets operating skill

Use this sub-skill when the task is about InternVid, instruction data, InternVideo2/3/Next dataset preparation, annotation JSON/JSONL/list schemas, path readiness, benchmark data caveats, or safe preflight validation before training/evaluation.

## Read order

1. `references/data-formats.md` to identify the expected format for the target generation and workflow.
2. Run `scripts/validate_internvideo_annotations.py --help` and then validate the user's annotation file(s) with the closest format mode.
3. `references/troubleshooting.md` when a loader reports missing files, empty datasets, placeholder/token-count assertions, shared-memory/cache failures, or benchmark-data gaps.

## Safe validation workflow

1. Identify workflow: InternVid search metadata, InternVideo2 single-modality list, InternVideo2 multi-modality JSON, InternVideo3 SFT meta/JSONL, InternVideo-Next pretraining list, or benchmark/evaluation data.
2. Validate syntax and schema first with the bundled script. Use `--check-paths` only when the user wants local path existence checks and has provided the relevant `--media-root`.
3. Report counts, errors, warnings, and any assumptions. Do not download datasets or touch object storage without approval.
4. Hand off validated data facts to the requesting sub-skill (`video-mllm`, `next-pretraining`, `single-modality`, or `multi-modality`).

## Bundled validator examples

```bash
python scripts/validate_internvideo_annotations.py \
  --format internvideo3-meta <annotation-meta.json> --follow-meta --max-records 100
```

```bash
python scripts/validate_internvideo_annotations.py \
  --format internvideo2-json <annotations.json> --expect-media-type video --media-root <media-root> --check-paths
```

```bash
python scripts/validate_internvideo_annotations.py \
  --format pretrain-list <pretraining-list.txt> --media-root <media-root> --check-paths
```

Resolve `scripts/validate_internvideo_annotations.py` relative to this `datasets` sub-skill directory when copying the generated skill into another environment. The script itself has no dependency on the original repository checkout.

## Guardrails

- Treat public dataset names as identifiers, not proof that data are present locally.
- YouTube-derived datasets can have dead/missing videos; validation should distinguish annotation syntax from media availability.
- Do not assume JSON and JSONL are interchangeable: InternVideo2 loaders commonly use JSON arrays, while InternVideo3 SFT uses JSONL.
- Do not classify full benchmark acquisition, checkpoint download, or video decoding of large corpora as required static verification.
