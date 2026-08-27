---
name: alae
description: "Use the ALAE repository for Adversarial Latent Autoencoder data
  preparation, CUDA training, checkpoint-backed generation, latent editing, and
  legacy metrics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# ALAE repo skill

Use this skill when the user names ALAE, StyleALAE, adversarial latent autoencoders, the `podgorskiy/ALAE` repository, `train_alae.py`, `interactive_demo.py`, `style_mixing/stylemix.py`, ALAE TFRecords, principal directions, or ALAE FID/PPL/LPIPS metrics.

ALAE is an older, un-packaged script repository. Future agents normally need a local ALAE checkout, must run native scripts from that checkout root, and should set `PYTHONPATH` to the checkout root for subdirectory scripts.

## First reads

- Read [repository provenance](references/repo-provenance.md) before trusting version-sensitive guidance or deciding whether to refresh this skill.
- Read [setup and environment](references/setup-and-environment.md) before installing dependencies, choosing CUDA/TensorFlow variants, or launching native scripts.
- Read [configuration](references/configuration.md) before choosing a config, overriding YACS options, or diagnosing path/checkpoint mismatches.
- Read [cross-cutting troubleshooting](references/troubleshooting.md) when import, CUDA, TensorFlow, checkpoint, data path, or stale README issues appear.
- Router metadata for import tooling lives in [repo-routing-metadata.json](references/repo-routing-metadata.json).

## Safe root helpers

Run these generated helpers from this skill directory, or use their full paths, while pointing `--repo-root` at the user's ALAE checkout:

```bash
python scripts/check_alae_environment.py --repo-root <ALAE-checkout>
python scripts/download_alae_artifacts.py --dataset all
```

`check_alae_environment.py` imports safe dependencies/source modules and checks PyTorch CUDA with a tiny tensor by default. It does not download models, import metric scripts, run training, or open a GUI.

`download_alae_artifacts.py` lists pretrained model IDs/URLs by default. It downloads only when both `--download` and `--yes` are supplied.

## Route by task

| User intent | Read |
| --- | --- |
| Prepare TFRecords, validate data/sample/style paths, align faces, or adapt dataset paths away from `/data/datasets` | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Train or resume ALAE/StyleALAE, build a `train_alae.py` command, inspect configs, debug DDP/NCCL/dareblopy/checkpoints | [training](sub-skills/training/SKILL.md) |
| Run pretrained demo, generate images, make reconstruction/style-mixing/interpolation/traversal figures, check principal directions | [generation](sub-skills/generation/SKILL.md) |
| Prepare or troubleshoot FID, reconstruction FID, PPL, or LPIPS legacy metric scripts | [metrics](sub-skills/metrics/SKILL.md) |

## Operating sequence for most tasks

1. Confirm the user has or can create a local ALAE checkout; do not rely on the checkout used to build this skill.
2. Read provenance if the checkout differs from the recorded commit or contains new/removed scripts.
3. Run or adapt the root environment checker. Core training/generation requires CUDA-visible PyTorch; CPU-only import is not enough.
4. Use the configuration reference and sub-skill-specific checkers before launching any long GPU, GUI, data conversion, metric, or network operation.
5. For native ALAE commands, run from the checkout root:

   ```bash
   cd <ALAE-checkout>
   export PYTHONPATH="$PYTHONPATH:$(pwd)"
   python train_alae.py -c ffhq
   ```

6. Ask for explicit approval before large downloads, raw dataset conversion, full training, GUI launch, or 10k-50k sample metric runs.

## Important constraints

- The README's ablation/separate-model routes are stale in this checkout: `train_alae_separate.py`, `model_separate.py`, and `celeba_ablation_*.yaml` were not present. Do not route users to them unless a newer checkout actually contains them.
- `metrics/fid_sep.py` imports absent separate-model code and is not an executable route for this skill.
- Many original scripts have hard-coded assumptions (`/data/datasets`, `training_artifacts/<dataset>/last_checkpoint`, fixed sample filenames, FFHQ-specific direction vectors). Prefer generated checkers before native execution.
- TensorFlow/dnnlib metric workflows are optional legacy routes; they may import in a TF1 environment while still lacking a compatible TensorFlow GPU CUDA/cuDNN stack.
