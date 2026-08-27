# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current repo commit, dirty state, package version, or major evidence paths differ from this snapshot, run `refresh-skill-from-repo`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-06-21T00:00:00Z",
  "repository": {
    "name": "diffusers",
    "remote_url": "https://github.com/huggingface/diffusers.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "2d0110f8182d18834d5039b19232e5761023b5f6",
    "working_tree": "dirty",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "diffusers",
      "version": "0.39.0.dev0",
      "import_names": ["diffusers"]
    }
  ],
  "evidence": {
    "source_roots": ["src/diffusers"],
    "docs": [
      "README.md",
      "docs/source/en/installation.md",
      "docs/source/en/quicktour.md",
      "docs/source/en/using-diffusers",
      "docs/source/en/training",
      "docs/source/en/modular_diffusers",
      "docs/source/en/api"
    ],
    "examples": [
      "examples/inference",
      "examples/server",
      "examples/server-async",
      "examples/dreambooth",
      "examples/text_to_image",
      "examples/textual_inversion",
      "examples/controlnet",
      "examples/t2i_adapter",
      "examples/instruct_pix2pix",
      "examples/flux-control",
      "examples/community"
    ],
    "tests": [
      "tests/pipelines",
      "tests/schedulers",
      "tests/lora",
      "tests/single_file",
      "tests/modular_pipelines",
      "tests/others",
      "examples/*/test_*.py"
    ],
    "scripts": [
      "src/diffusers/commands",
      "scripts/convert_original_stable_diffusion_to_diffusers.py",
      "scripts/convert_lora_safetensor_to_diffusers.py",
      "scripts/extract_lora_from_model.py",
      "scripts/convert_diffusers_to_original_stable_diffusion.py",
      "scripts/convert_diffusers_to_original_sdxl.py",
      "scripts/convert_stable_diffusion_checkpoint_to_onnx.py"
    ],
    "existing_repo_skills": [
      "skills/disco/diffusers/sub-skills/schedulers",
      "skills/disco/diffusers/sub-skills/adapters-and-loaders",
      "skills/disco/diffusers/sub-skills/modular-pipelines"
    ],
    "excluded": [
      "benchmarks",
      "docker",
      ".github",
      "tests/remote",
      "examples/research_projects",
      "skills/tests",
      "build/cache/generated files"
    ]
  }
}
```

## Refresh Check

- If `git rev-parse HEAD` differs from `repository.commit`, treat the skill as potentially stale and run `refresh-skill-from-repo`.
- If the current working tree dirty paths differ materially from `repository.dirty_paths`, run `refresh-skill-from-repo` before relying on this skill for exact repo behavior.
- If package metadata, optional dependency groups, console entry points, public pipeline/scheduler/loader APIs, training examples, conversion scripts, or modular-pipeline APIs changed, refresh the skill even when the commit is unchanged.
- This provenance intentionally omits private inspection environment paths and local checkout paths.
