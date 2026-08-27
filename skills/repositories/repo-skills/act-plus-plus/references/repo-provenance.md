# Repository Provenance

## Purpose

Read this before deciding whether this skill is current for a checkout of the repository. If the current checkout differs in commit, dirty state, package metadata, or major evidence paths, refresh the repo skill before relying on it for operational decisions.

## Snapshot

```json
{
  "schema": "disco.repo-provenance.v1",
  "generated_at_utc": "2026-08-16T17:11:58Z",
  "repository": {
    "name": "act-plus-plus",
    "remote_url": "https://github.com/MarkFzp/act-plus-plus.git",
    "vcs": "git",
    "branch": "main",
    "tag": null,
    "commit": "26bab0789d05b7496bacef04f5c6b2541a4403b5",
    "working_tree": "clean",
    "dirty_paths": []
  },
  "packages": [
    {
      "name": "act",
      "version": "0.0.0",
      "import_names": ["constants", "sim_env", "ee_sim_env", "policy", "imitate_episodes", "detr"]
    },
    {
      "name": "detr",
      "version": "0.0.0",
      "import_names": ["detr", "models", "util"]
    }
  ],
  "evidence": {
    "source_roots": ["*.py", "detr/"],
    "docs": ["README.md", "detr/README.md", "commands.txt"],
    "assets": ["assets/"],
    "examples_or_scripts": [
      "record_sim_episodes.py",
      "replay_episodes.py",
      "visualize_episodes.py",
      "postprocess_episodes.py",
      "compress_data.py",
      "truncate_data.py",
      "imitate_episodes.py",
      "train_latent_model.py",
      "vinn_cache_feature.py",
      "vinn_select_k.py",
      "vinn_eval.py"
    ],
    "excluded_or_reference_only": [
      "align.py",
      "dxl_test.py",
      "dynamixel_client.py",
      "train_actuator_network.py",
      "byol_pytorch"
    ],
    "tests": []
  },
  "external_evidence_notes": {
    "byol_pytorch_gitlink": "bcd1b066c3915745db720175905c1ffcc364f621; empty in inspected checkout",
    "mobile_aloha_runtime": "external dependency for real robot branches, not included in this skill"
  }
}
```

## Refresh check

- If `git rev-parse HEAD` differs from the snapshot commit, refresh this skill.
- If the current working tree is dirty but this snapshot is clean, refresh before trusting CLI/API details.
- Refresh if task names, camera names, HDF5 schema, `policy.py` imports, or CLI flags change.
- Refresh if the external Mobile ALOHA, BYOL, robomimic, or DM Control dependency assumptions become first-class verified scope.
