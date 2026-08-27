# Repo Provenance

- source repository identity: `2U1/Qwen-VL-Series-Finetune`
- source commit: `c8f7377b67dc0b7c34c77cc4e7e65698401b3dce`
- branch: `master`
- exact tag at HEAD: none
- working tree state at generation time: dirty, with the repo-local `skills/` tree newly created for this skill production and later repaired to include bundled `src/` runtime entrypoints
- remote URL: omitted-private-or-unknown

## Evidence used

- `README.md`
- `requirements.txt`
- `environment.yaml`
- `LICENSE`
- `scripts/*.sh`
- `scripts/zero*.json`
- `src/` (copied into the generated runtime tree during the repair pass)
- private inspection environment checks recorded in the review artifacts

## Refresh baseline

This skill reflects the repository state at the commit above plus the inspected README, scripts, and source layout. The generated runtime tree also includes a copied `src/` subtree and bundled DeepSpeed configs so the training, merge, and serving workflows are self-contained. If the repository changes, refresh the skill against the newer evidence before relying on it.
