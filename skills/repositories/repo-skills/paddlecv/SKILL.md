---
name: "paddlecv"
description: "Use for PaddlePaddle models repo PaddleCV and ppcv inference,
  task-name pipelines, model catalog checks, and custom operator graph
  workflows."
metadata:
  disco-role: "operating"
disable-model-invocation: true
license: Apache 2.0
---

# PaddleCV

Use this skill for PaddlePaddle `paddlecv` / `ppcv` workflows: single-model vision inference, task-name driven system pipelines, and custom operator or DAG extension. It is a router, not a full manual.

## Read first
- `references/task-catalog.md` for the supported task families and config paths.
- `references/api-reference.md` for the public `PaddleCV`, `Pipeline`, registry, and config APIs.
- `references/workflows.md` for the common inference and extension routes.
- `references/troubleshooting.md` when imports, downloads, configs, or runtime checks fail.
- `scripts/smoke_import.py` for a quick package/catalog smoke check.

## Route map

| User intent | Read |
| --- | --- |
| Run a single image model from a config file | `sub-skills/single-model-inference/SKILL.md` |
| Use `PaddleCV(task_name=...)` or OCR / PP-Structure / ShiTu / Human / Vehicle / TinyPose / IE / SA / TTS pipelines | `sub-skills/system-pipelines/SKILL.md` |
| Add, adapt, or debug a custom operator, connector, output, or config graph | `sub-skills/custom-ops/SKILL.md` |
| Check the package import, supported tasks, or catalog without running inference | `scripts/smoke_import.py` and `references/task-catalog.md` |

## Shared runtime facts
- Public import surface: `paddlecv.PaddleCV`, `ppcv.engine.pipeline.Pipeline`, `ppcv.model_zoo.get_config_file`, `ppcv.model_zoo.get_model_file`, `ppcv.model_zoo.list_model`.
- Config-driven inference reads `paddlecv/configs/single_op/*.yml` and `paddlecv/configs/system/*.yml` through `Pipeline(config_path=...)`.
- Task-name inference reads the built-in `TASK_DICT` through `PaddleCV(task_name=...)`.
- Runtime downloads use the `paddlecv://` scheme and cache under `~/.cache/paddlecv/{models,configs,dicts,fonts}`.
- Package import also pulls in `ppcv.ops.models.nlp` and `ppcv.ops.models.speech`, so `paddlenlp` and `paddlespeech` are part of the practical import surface.

## Use these helpers
- Run `scripts/run_predict.py` when you need one bundled entry point for config-based or task-name inference.
- Run `scripts/smoke_import.py` to confirm the package, catalog, and public constructor shape before deeper debugging.

## Install and compatibility notes
- Keep `paddle`, `cv2`, `numpy`, `paddlenlp`, `paddlespeech`, and the package's image/runtime dependencies aligned.
- If `pkg_resources` is missing, install a `setuptools` version that still provides it.
- If `paddlenlp` fails on `aistudio_sdk.hub.download`, use an `aistudio-sdk` release that still exports that helper.
- If OpenCV complains about NumPy ABI mismatches, use a NumPy 1.x build that matches the OpenCV wheel.
- If retrieval or ShiTu-style workflows fail, check `faiss` compatibility for your Python version.

## What not to do here
- Do not treat the root skill as the place for custom-op implementation details or per-model API tables.
- Do not route pure training or tutorial reproduction work here.
- Do not rely on source checkout paths inside runtime instructions; use bundled references and scripts instead.

## If something breaks
Start with `references/troubleshooting.md`, then use the owning sub-skill. Most failures are one of: missing package dependencies, cache/download problems, config graph mismatches, or backend/version incompatibility.
