---
name: lightly
description: "Use LightlySSL for self-supervised computer-vision training, model
  components, CLIs, embeddings, data layout, evaluation, and repository
  maintenance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LightlySSL Repo Skill

Use this skill when a task names `lightly`, LightlySSL, self-supervised computer vision, Lightly's CLI commands, SSL transforms/losses/heads, image-folder embeddings, YOLO crop helpers, or maintenance of the LightlySSL repository.

## Quick setup

- Public install: `pip install lightly`
- Optional TIMM/ViT modules: `pip install "lightly[timm]"`
- Optional direct video support: `pip install "lightly[video]"`
- Minimal import check:

```bash
python - <<'PY'
import lightly
from lightly.loss import NTXentLoss
from lightly.transforms import SimCLRTransform
print(lightly.__version__, NTXentLoss, SimCLRTransform)
PY
```

For a richer environment smoke, run the bundled [environment checker](scripts/check_lightly_environment.py). It imports core modules, reports optional TIMM/video availability, and can do a tiny tensor check without downloads.

## Route map

| Need | Read |
|---|---|
| Assemble datasets, collates, transforms, losses, projection heads, memory banks, or method-to-component mappings. | [ssl-building-blocks](sub-skills/ssl-building-blocks/SKILL.md) |
| Adapt a bare PyTorch, PyTorch Lightning, or distributed Lightly SSL training recipe without downloading repo examples. | [training-workflows](sub-skills/training-workflows/SKILL.md) |
| Build or validate `lightly-version`, `lightly-ssl-train`, `lightly-embed`, `lightly-magic`, `lightly-crop`, Hydra overrides, input folders, embeddings CSVs, or YOLO crop labels. | [cli-data-embedding](sub-skills/cli-data-embedding/SKILL.md) |
| Use KNN/linear evaluation utilities or choose repository checks for changes to losses, transforms, examples, docs, notebooks, or distributed tests. | [evaluation-maintenance](sub-skills/evaluation-maintenance/SKILL.md) |

## Shared references

- [Package overview](references/package-overview.md) — public surfaces, optional extras, and workflow boundaries.
- [Troubleshooting](references/troubleshooting.md) — cross-cutting install/import/backend/data/config problems before routing deeper.
- [Repository provenance](references/repo-provenance.md) — source snapshot and refresh triggers.
- [Router metadata](references/repo-routing-metadata.json) — structured scenario placement used by the managed repo-skills router.

## Operating rules

1. Do not run training, embedding, crop, notebook, benchmark, or distributed commands until the user provides data paths, output policy, and runtime budget.
2. Prefer bundled scripts for safe preflight: environment checks, component smoke checks, CLI command construction, folder validation, tiny YOLO fixtures, and synthetic SimCLR steps.
3. Treat GPU, distributed, TIMM, and video support as optional unless the user explicitly asks for them; verify the relevant backend/extra before claiming it works.
4. Keep source-code maintenance guidance separate from package-use guidance. When editing the repository, use the maintenance sub-skill to select focused checks before broad `make all-checks`.
