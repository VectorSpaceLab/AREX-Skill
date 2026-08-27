# Repo provenance

- Source repository: Fengshenbang-LM / `fengshen` package.
- Public remote URL: `https://github.com/IDEA-CCNL/Fengshenbang-LM.git`.
- Commit: `c8fb7b8437843ea13fa9d147ce86c4592fa21237`.
- Branch: `main`.
- Exact tag: none detected at this commit.
- Package distribution name: `fengshen`.
- Package metadata version: `0.0.1`.
- Working tree state at generation: dirty because the generated `skills/` output tree was created in the checkout. No source package files were modified by the generated skill.

## Evidence paths used

- `setup.py`
- `.gitmodules`
- `README.md`
- `README_en.md`
- `fengshen/README.md`
- `fengshen/__init__.py`
- `fengshen/requirement.txt`
- `fengshen/cli/fengshen_pipeline.py`
- `fengshen/pipelines/`
- `fengshen/models/`
- `fengshen/data/`
- `fengshen/metric/`
- `fengshen/strategies/`
- `fengshen/tokenizer/`
- `fengshen/utils/`
- `fengshen/examples/` representative README, Python, and shell recipe files
- `fengshen/models/megatron/fused_kernels/tests/test_fused_kernels.py`
- `fengshen/pipelines/test.py`
- `fengshen/pipelines/test_tagging.py`

## Verification baseline

The generated skill was built from source evidence plus a private installed-package inspection environment. Public runtime files intentionally omit local environment paths. Construction-time inspection verified package import, top-level config imports, `TextClassificationPipeline` and `SequenceTaggingPipeline` parser construction, `fengshen-pipeline text_classification predict --help`, `get_entities` tiny behavior, and selected script help/tiny checks. CUDA/Deepspeed/Megatron/stable-diffusion/Ziya native execution was classified optional/unverified for this portable scope.

Refresh this skill if the repo changes package metadata, dependency compatibility, pipeline APIs, examples, or model-family implementations.
