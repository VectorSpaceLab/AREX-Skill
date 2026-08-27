# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the LMOps repository. If the current repo commit, dirty state, source project directories, public command flags, data schemas, or major README workflows differ from this snapshot, run `refresh-repo-skill`.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T04:09:30Z",
  "repository": {
    "name": "LMOps",
    "remote_url": "https://github.com/microsoft/LMOps.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "4f2a9deb5f08e459fd44c2e4792344d78ca89fc3",
    "working_tree": "dirty-after-generation",
    "dirty_paths": ["skills/"],
    "source_evidence_dirty_paths_excluding_generated_skill": []
  },
  "packages": [
    {
      "name": "LMOps-root",
      "version": null,
      "import_names": [],
      "note": "The repository has no root Python package metadata; evidence comes from independent project directories."
    }
  ],
  "evidence": {
    "source_roots": [
      "prompt_optimization",
      "uprise",
      "se2",
      "llm_retriever/src",
      "adaptllm",
      "instruction_pretrain/utils",
      "data_selection",
      "minillm/minillm",
      "dpkd",
      "reslora/myloralib",
      "tuna/src",
      "learning_law/src",
      "oel",
      "opcd",
      "llm-as-a-coach",
      "gad",
      "opo",
      "corag/src",
      "llma/src"
    ],
    "docs": [
      "README.md",
      "prompt_optimization/README.md",
      "promptist/README.md",
      "uprise/README.md",
      "se2/README.md",
      "llm_retriever/README.md",
      "ced_icl/ced_exp/README.md",
      "structured_prompting/fairseq-version/README.md",
      "structured_prompting/hf-version/README.md",
      "understand_icl/README.md",
      "adaptllm/README.md",
      "adaptllm/scripts/README.md",
      "instruction_pretrain/README.md",
      "data_selection/README.md",
      "minillm/README.md",
      "dpkd/README.md",
      "reslora/README.md",
      "tuna/README.md",
      "learning_law/README.md",
      "oel/README.md",
      "opcd/README.md",
      "llm-as-a-coach/README.md",
      "gad/README.md",
      "opo/README.md",
      "corag/README.md",
      "llma/README.md",
      "llma/src/README.md"
    ],
    "examples": [
      "adaptllm/data_samples",
      "prompt_optimization/prompts",
      "reslora/examples",
      "tuna/gpt_data",
      "LLM4Science"
    ],
    "scripts_and_tools": [
      "adaptllm/scripts",
      "uprise/*.py and uprise/*.sh command wrappers",
      "se2/*.py and se2/*.sh command wrappers",
      "llm_retriever/scripts",
      "data_selection/scripts and data_selection/tools",
      "minillm/scripts and minillm/tools",
      "dpkd/scripts and dpkd/tools",
      "tuna/src",
      "oel/scripts and oel/tools",
      "opcd/scripts and opcd/tools",
      "llm-as-a-coach/usage_example.sh and scripts",
      "gad/scripts and gad/tools",
      "corag/scripts"
    ],
    "configs": [
      "adaptllm/configs",
      "uprise/configs",
      "se2/configs",
      "llm_retriever/ds_config.json",
      "data_selection/configs",
      "minillm/configs",
      "dpkd/configs",
      "opcd/system_prompts"
    ],
    "excluded_or_reference_only": [
      "dpkd/transformers",
      "promptist/diffusers",
      "promptist/trlx",
      "structured_prompting/fairseq-version/fairseq",
      "understand_icl/fairseq",
      "uprise/DPR",
      "se2/DPR",
      "oel/verl",
      "opcd/verl",
      "llm-as-a-coach/verl",
      "opo/verl"
    ]
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, treat this skill as potentially stale.
- If source project READMEs, command flags, data schemas, or bundled script decisions changed, refresh even on the same commit.
- The `skills/` dirty path above reflects generated skill artifacts. Source evidence was captured from a clean checkout before the generated files were added.
- If a later task requires actual CUDA/Ray/vLLM/native execution rather than static planning, rerun environment preparation for that narrower execution scope.
