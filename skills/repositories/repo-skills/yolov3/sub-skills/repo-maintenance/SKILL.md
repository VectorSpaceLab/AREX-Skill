---
name: repo-maintenance
description: "Maintain the YOLOv3 repository under its CI, style, compatibility,
  dependency, docs, packaging, and PR policies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Repo Maintenance Sub-skill

Read this before modifying YOLOv3 source files, CI, dependencies, documentation, packaging metadata, or release/PR behavior.

## Use

- Read `references/maintenance.md` for repo policy, CI smoke commands, branch/PR workflow, style, and dependency floors.
- Read `references/troubleshooting.md` for packaging, CI, and contribution pitfalls.

## Important facts

- The default branch is `master`, not `main`.
- Core policy: less is more; Delete > Replace > Add; solve behavior in the owning code path.
- Keep Python >=3.8 and PyTorch >=1.8 compatibility.
- CI smoke tests use training, validation, detection, export, and PyTorch Hub paths, including network downloads for official weights and coco128.
- Do not rewrite intentional upstream YOLOv5 provenance links when they refer to issue/discussion numbers.
