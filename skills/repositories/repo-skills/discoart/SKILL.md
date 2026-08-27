---
name: discoart
description: "Use this repo skill for DiscoArt image generation,
  configuration/prompt scheduling, CLI, Jina serving, Docker runtime planning,
  and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DiscoArt Repo Skill

Use this skill when the task involves **DiscoArt**, the Python package for creating Disco Diffusion artworks through a one-line API, YAML/CLI workflows, and optional Jina service deployment.

DiscoArt is CUDA-oriented: config and CLI planning can be checked safely, but actual `create()` runs may download large diffusion/CLIP/secondary-model weights and need GPU memory. Do not start generation, model downloads, Docker builds, or persistent servers unless the user explicitly wants that runtime action.

## Start here

1. **Install/import check.** Use `scripts/check_discoart_environment.py --check-cuda` to verify package imports, version, default config access, and CUDA visibility without loading models.
2. **Pick the right route.** Use the sub-skill map below; most tasks should immediately move to a focused sub-skill.
3. **Normalize before running.** Validate YAML/kwargs through `discoart.config.load_config` or the bundled validators before calling `create()` or starting a service.
4. **Preserve names and paths.** Prefer explicit `name_docarray`, `DISCOART_OUTPUT_DIR`, and `DISCOART_CACHE_DIR` so outputs and cache behavior are predictable.
5. **Check provenance if stale.** Read `references/repo-provenance.md` before refreshing this skill or comparing it with a newer checkout.

## Sub-skill routes

| If the user asks to... | Read |
| --- | --- |
| Generate or plan artwork with Python `create()`, choose model/runtime settings, handle `DocumentArray` outputs, recover local/cloud results, or use `go_big()` | `sub-skills/artwork-generation/SKILL.md` |
| Write, validate, repair, or explain configs, prompt schema v1, legacy prompt weights, schedule strings, CLIP guidance routing, cut schedule groups, cheatsheets, or config import/export helpers | `sub-skills/configuration-and-prompts/SKILL.md` |
| Use `python -m discoart`, export/run YAML from CLI, serve through Jina Flow, call `/create`/`/result`/`/skip`/`/stop`, or plan Docker/Jupyter GPU execution | `sub-skills/cli-and-serving/SKILL.md` |
| Debug package-wide install/import, CUDA/model-cache, network/version-check, output/cache, or optional dependency issues before choosing a workflow | `references/troubleshooting.md` |

## Minimal safe environment check

```bash
python scripts/check_discoart_environment.py --check-cuda
```

This helper imports DiscoArt with remote model lookup disabled, checks the default configuration can be loaded, prints key dependency versions, and optionally probes `torch.cuda` without running diffusion.

## Public install and runtime facts

```bash
pip install discoart
```

For local development against a checkout, use an editable install only in a disposable environment:

```bash
python -m pip install -e .
```

- Package/distribution/import name: `discoart`.
- Skill baseline package version: `0.12.2`.
- Public import examples: `from discoart import create, cheatsheet, load_config, save_config, show_config, go_big` and `from discoart.config import save_config_svg, export_python`.
- The primary API is `create(**kwargs) -> Optional[DocumentArray]`; static overload/docstring facts are generated from the packaged YAML resources.
- Python 3.7+ is declared by the package, but older ML dependencies often require conservative Python and PyTorch choices. For new environments, prefer a supported Python version with compatible CUDA PyTorch rather than the newest Python available.
- Primary generation is practical only with CUDA-enabled PyTorch and enough VRAM. CPU can import and validate configs but is not a practical generation backend.

For a concise package overview, outputs, environment variables, and evidence-backed constraints, read `references/package-overview.md`.

## Guardrails

- Do not depend on opening this repository's original README, notebook, tests, resources, or scripts at runtime. This generated skill is self-contained.
- Do not run repository-native tests or examples until after task-specific planning; full generation may download large models and take minutes even on GPU.
- Do not run `python -m discoart serve` as a default check; it blocks as a persistent service.
- Do not expose local environment paths, cache paths, or private construction reports in user-facing answers.
- Maintainer release automation, CI linting, and packaging publication workflows are outside this operating skill.

## References

- `references/package-overview.md` — package purpose, APIs, outputs, runtime prerequisites, and environment variables.
- `references/troubleshooting.md` — cross-cutting install/import, CUDA/cache, network, DocArray, and service setup failures.
- `references/repo-provenance.md` — source repository snapshot and refresh baseline.
- `references/repo-routing-metadata.json` — structured scenario metadata consumed by the repo-skills router importer.
