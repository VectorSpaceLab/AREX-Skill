---
name: artwork-generation
description: "Generate Disco Diffusion artwork with DiscoArt Python APIs,
  runtime/model choices, DocArray outputs, recovery, and generation
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Artwork Generation

Use this sub-skill when the user wants to generate or plan Disco Diffusion artwork through the DiscoArt **Python API**. It covers `create(**kwargs)`, `go_big()`, init images/documents, model/backend choices, output artifacts, DocArray recovery, and generation-specific failures.

## Trigger on requests like

- "Generate an artwork with DiscoArt" or "write a `create()` call for this prompt".
- "Choose safe DiscoArt size/steps/CLIP/diffusion settings for my GPU".
- "Where did DiscoArt save my images/protobuf?" or "recover a lost DiscoArt session".
- "Debug CUDA, model cache/download, OOM, W&B, or no-output issues during `create()`".
- "Use an existing DiscoArt `Document`/`DocumentArray` as `init_document`" or "run `go_big()`".

## Route elsewhere

- Prompt schema, prompt scheduling, schedule grammar, `load_config`/`save_config`/`show_config`/`export_python`, and YAML validation: read `../configuration-and-prompts/SKILL.md`.
- `python -m discoart` CLI, Jina service endpoints, Docker, and Jupyter/runtime launch patterns: read `../cli-and-serving/SKILL.md`.
- Cross-cutting install/import and package-level environment failures: read `../../references/troubleshooting.md` when available.
- Maintainer scripts, release automation, CI, and repository development tasks are outside this generated operating skill.

## Read order

1. `references/artwork-api.md` for `create()`/`go_big()` workflows, parameter grouping, output files, DocArray recipes, and safe examples.
2. `references/model-and-runtime.md` for diffusion/CLIP model choices, CUDA/cache/environment/W&B constraints, and memory trade-offs.
3. `references/troubleshooting.md` for CUDA, model download/cache, OOM, missing output/protobuf, DocArray recovery, and runtime symptoms.
4. `scripts/plan_create_request.py` when you need a safe local summary of a config without running generation or downloading models.

## Quick workflow

1. **Confirm the surface.** Use this sub-skill only for Python API generation. If the user asks for CLI/service execution, route to `cli-and-serving`; if they ask for prompt-schema or schedule syntax, route to `configuration-and-prompts`.
2. **Plan without side effects.** Normalize proposed kwargs through `discoart.config.load_config` or the bundled `scripts/plan_create_request.py`; do not call `create()` until the user intends to run generation and the environment is ready.
3. **Choose safe generation defaults.** Prefer an explicit `name_docarray`, explicit `DISCOART_OUTPUT_DIR` and `DISCOART_CACHE_DIR`, `n_batches=1`, `batch_size=1`, a size that is a multiple of 64, bounded `steps`, and a small CLIP model set for first runs.
4. **Check runtime risk.** DiscoArt can run on CPU but is practically CUDA-oriented. First `create()` calls may download diffusion, secondary, and CLIP weights unless caches are already populated.
5. **Run and preserve artifacts.** `create()` returns a DocArray `DocumentArray`; final/intermediate images and `da.protobuf.lz4` are saved under `<DISCOART_OUTPUT_DIR or .>/<name_docarray>/`.
6. **Recover or debug by name.** For interrupted/lost sessions, use the known `name_docarray`, local `da.protobuf.lz4`, or `DocumentArray.pull(name_docarray)` when cloud backup was enabled and reachable.

## Guardrails

- Never treat config planning as proof that generation will succeed; model downloads, CUDA memory, and cache contents are runtime gates.
- Do not run full native generation tests from this sub-skill draft. Later verification may use the `tiny-create-smoke` and `readme-api-workflows` candidates only when CUDA/cache/time limits make them bounded.
- Keep examples self-contained: import from the installed `discoart` package and do not require opening the original repository checkout.

## Version facts distilled for this skill

- Package version target: DiscoArt `0.12.2`.
- `create` runtime signature: `create(**kwargs) -> Optional[DocumentArray]`, backed by 49 default arguments.
- `go_big` signature: `go_big(doc, window_size=256, upscale_factor=2, skip_rate=0.8, stride_size=None, **kwargs) -> Document`.
- A CUDA smoke check passed during skill construction, but every user runtime must still check its own `torch.cuda.is_available()` and model cache state.
