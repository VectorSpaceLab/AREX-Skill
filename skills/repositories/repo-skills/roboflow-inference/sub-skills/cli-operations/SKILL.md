---
name: cli-operations
description: "Route Roboflow Inference CLI users through server lifecycle,
  one-shot inference, benchmarks, cloud deployment, Roboflow Cloud staging and
  batch-processing, and enterprise compilation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# CLI Operations

Use this sub-skill when the user wants the `inference` CLI itself, or the module form `python -m inference_cli.main`: server lifecycle, `infer`, benchmark runs, cloud deployment, Roboflow Cloud data staging and batch processing, or enterprise model compilation.

## Route here when

- They ask how to start, check, or stop the local inference server.
- They ask how to run `inference infer` on an image, directory, or video.
- They ask about `inference benchmark api-speed`, `python-package-speed`, or the experimental `inference-models-speed` benchmark.
- They ask about `inference cloud ...` deployment commands.
- They ask about `inference rf-cloud data-staging ...` or `batch-processing ...`.
- They ask about `inference enterprise inference-compiler compile-model`.
- They need the exact CLI flags, common invocation patterns, or a CLI-specific error message.

## Do not route here when

- The user is working on `inference workflows process-image`, `process-images-directory`, or `process-video`. Use the workflow-processing sub-skill instead.
- They want SDK/WebRTC client behavior or HTTP request shaping.
- They want model backend selection or runtime/package negotiation.

## First decisions to make

1. Which command family is the user asking about?
2. Is the target local Docker, a hosted Roboflow endpoint, Roboflow Cloud, or the enterprise compiler?
3. Does the command need a Roboflow API key from `--api-key` or `ROBOFLOW_API_KEY`?
4. Will the command write to disk, and if so does the output path need an override flag?
5. Is the user actually asking about workflow image/video processing? If so, hand off to workflow-processing.

## Read these bundled references

- [CLI reference](references/cli-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [CLI smoke helper](scripts/inspect_cli_help.py)

If the user switches to workflow image/video processing, continue in [`../workflow-processing/SKILL.md`](../workflow-processing/SKILL.md) instead of expanding this sub-skill.

## Answer pattern

When answering, give:

1. The exact CLI family and subcommand.
2. The shortest working command that matches the user’s target.
3. Any required dependency, Docker, or API-key precondition.
4. The key flags that change output, networking, or overwrite behavior.
5. A troubleshooting branch if the command can fail for a predictable reason.
