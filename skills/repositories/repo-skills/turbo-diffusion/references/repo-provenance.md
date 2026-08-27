# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of TurboDiffusion. If the current repo commit, dirty state, package version, source-layout import behavior, public CLI flags, or major evidence paths differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T19:20:16Z",
  "repository": {
    "name": "TurboDiffusion",
    "remote_url": "https://github.com/thu-ml/TurboDiffusion.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "73df7e1c60cd3647518ad77b76dc09a927cf9930",
    "working_tree": "dirty",
    "dirty_paths": [
      "skills/"
    ],
    "submodules": [
      {
        "path": "turbodiffusion/ops/cutlass",
        "commit": "e67e63c331d6e4b729047c95cf6b92c8454cba89"
      }
    ]
  },
  "packages": [
    {
      "name": "turbodiffusion",
      "version": "1.0.0",
      "import_names": [
        "turbodiffusion",
        "turbo_diffusion_ops"
      ],
      "console_scripts": [
        "turbodiffusion-serve"
      ]
    }
  ],
  "evidence": {
    "metadata": [
      "pyproject.toml",
      "setup.py",
      "MANIFEST.in"
    ],
    "source_roots": [
      "turbodiffusion/",
      "turbodiffusion/inference/",
      "turbodiffusion/serve/",
      "turbodiffusion/SLA/",
      "turbodiffusion/ops/",
      "turbodiffusion/rcm/",
      "turbodiffusion/scripts/"
    ],
    "docs": [
      "README.md",
      "turbodiffusion/serve/README.md",
      "turbot2va/README.md",
      "turbot2va/docs/acceleration.md"
    ],
    "examples_and_scripts": [
      "scripts/inference_wan2.1_t2v.sh",
      "scripts/inference_wan2.2_i2v.sh",
      "scripts/quantize.sh",
      "turbodiffusion/scripts/train.py",
      "turbodiffusion/scripts/merge_models.py",
      "turbodiffusion/scripts/safetensors_to_pth.py",
      "turbodiffusion/scripts/dcp_to_pth.py"
    ],
    "tests_or_native_candidates": [
      "turbodiffusion/rcm/networks/wan2pt1_jvp_test.py",
      "turbot2va/LTX-2/packages/ltx-core/tests/test_transformer_fusion_helpers.py",
      "turbot2va/LTX-2/packages/ltx-distillation/tests/test_acceleration_config.py",
      "turbot2va/LTX-2/packages/ltx-distillation/tests/test_inference_prompt_loading.py"
    ],
    "assets_sampled": [
      "assets/t2v_inputs/prompts.txt",
      "assets/i2v_inputs/prompts.txt",
      "assets/i2v_inputs/i2v_input_0.jpg"
    ]
  }
}
```

## Verified preparation baseline

The construction run verified a private CUDA inspection environment with Python 3.12, `torch==2.8.0+cu128`, compiled `turbo_diffusion_ops`, `flash-attn`, CUDA allocation, INT8/FastNorm custom-op smoke checks, and parser/help checks for the T2V, I2V, serve, installed serve entry point, and checkpoint modification CLIs. Full generation, full training, SpargeAttn/SageSLA runtime, and TurboT2AV Pixi execution were not run because they require external checkpoints, optional dependency stacks, credentials, or expensive GPU/model execution.

## Refresh check

- If `git rev-parse HEAD` differs from the recorded commit, treat the skill as potentially stale.
- If public README commands, `pyproject.toml`, `setup.py`, `turbodiffusion/inference/`, `turbodiffusion/serve/`, `turbodiffusion/SLA/`, `turbodiffusion/ops/`, `turbodiffusion/scripts/`, or TurboT2AV docs change, refresh the skill.
- If the package fixes source-layout imports or changes console entry points, refresh the root install and troubleshooting guidance.
- If new checkpoints, resolutions, model families, or TurboT2AV commands are released, refresh `references/model-and-asset-catalog.md` and affected sub-skills.
