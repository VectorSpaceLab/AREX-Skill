# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of PPO-PyTorch. If the current commit, dirty state, package versions, or evidence paths differ from this snapshot, refresh the skill.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-18T23:15:33Z",
  "repository": {
    "name": "PPO-PyTorch",
    "remote_url": "https://github.com/nikhilbarhate99/PPO-PyTorch.git",
    "vcs": "git",
    "branch": "master",
    "tag": null,
    "commit": "728cce83d7ab628fe2634eabcdf3239997eb81dd",
    "working_tree": "dirty-generated-skill-only",
    "dirty_paths": ["skills/"]
  },
  "packages": [
    {
      "name": "torch",
      "version": "2.13.0+cu130",
      "import_names": ["torch"]
    },
    {
      "name": "numpy",
      "version": "2.5.1",
      "import_names": ["numpy"]
    },
    {
      "name": "pandas",
      "version": "3.0.5",
      "import_names": ["pandas"]
    },
    {
      "name": "matplotlib",
      "version": "3.11.1",
      "import_names": ["matplotlib"]
    },
    {
      "name": "Pillow",
      "version": "11.3.0",
      "import_names": ["PIL"]
    }
  ],
  "evidence": {
    "source_roots": ["PPO.py", "train.py", "test.py", "plot_graph.py", "make_gif.py"],
    "docs": ["README.md", "PPO_preTrained/README.md", "PPO_colab.ipynb"],
    "examples": ["PPO_logs/", "PPO_figs/", "PPO_gifs/"],
    "tests": [],
    "configs": []
  }
}
```

## Refresh check

- If `git rev-parse HEAD` changes, refresh the skill.
- If the dirty paths outside `skills/` change, refresh the skill.
- If the public workflow shape changes, especially the training/evaluation/visualization scripts or checkpoint layout, refresh the skill.
