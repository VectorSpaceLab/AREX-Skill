# Align-Anything operating overview

Align-Anything is a multimodal alignment package for supervised fine-tuning, preference/reward/cost modeling, PPO-style RLHF, diffusion alignment, multimodal serving, and several satellite project workflows. Treat it as a GPU-oriented research package: imports and static checks can run on CPU, but most real model, training, vLLM, and multimodal paths need CUDA-class hardware plus model/data assets.

## Main package surfaces

| Surface | What it owns | Use this skill area |
| --- | --- | --- |
| `align_anything.configs` | Training/evaluation/vLLM/DeepSpeed configuration files and chat/data templates. | `sub-skills/training-and-alignment/` for train configs; root environment docs for dependency checks. |
| `align_anything.trainers` | SFT, DPO, PPO, PPO remote RM, RM, cost, safer RLHF, GRPO, KTO, ORPO, SimPO, diffusion, Janus, and VLA/action trainers. | `sub-skills/training-and-alignment/` |
| `align_anything.datasets` | Supervised, preference, prompt-only, diffusion, any-to-any, Janus, VLA/action, and modality-specific dataset wrappers. | `sub-skills/training-and-alignment/references/config-and-data.md` |
| `align_anything.models` | Model registry, pretrained loading, reward/value wrappers, multimodal wrappers, and SPOC/embodied model support. | `sub-skills/multimodal-serving/` for loading/inference and `sub-skills/training-and-alignment/` for training model wiring. |
| `align_anything.serve` | Text, multimodal, and omni-modal Gradio CLI entry points. | `sub-skills/multimodal-serving/` |
| `align_anything.models.remote_rm` | Flask reward server, remote reward client, reward functions, and math verifier. | `sub-skills/remote-reward-models/` |
| `projects/` | Any-to-Text builders, Janus, InterMT, language feedback, Chameleon-style text-image-to-text-image, and Eval-Anything. | `sub-skills/project-workflows/` |

## Decision flow

1. **Is the user trying to train or align?** Load `training-and-alignment` first. It maps algorithm/modality names to trainer modules, config identifiers, dataset contracts, and launcher templates.
2. **Is the user loading a model or launching a CLI?** Load `multimodal-serving` first. It covers `load_pretrained_models`, text/multi/omni CLIs, device/dtype/trust-remote-code, and media preprocessing.
3. **Is there an HTTP reward endpoint or PPO remote reward model?** Load `remote-reward-models` first, then return to `training-and-alignment` for the PPO trainer launch.
4. **Does the request name a project folder or Eval-Anything?** Load `project-workflows` first. Many satellite workflows require optional runtimes and are reference-only until explicitly prepared.

## Construction-time runtime facts

The construction inspection runtime verified the following public facts without preserving private paths in this skill:

- `align_anything` imports.
- `align_anything.models.pretrained_model.load_pretrained_models` imports.
- `align_anything.serve.text_modal_cli`, `multi_modal_cli`, and `omni_modal_cli` import.
- `align_anything.models.remote_rm.run_reward_server`, `reward_server`, and `remote_rm_client` import.
- Representative core trainers import: text-to-text SFT/DPO/PPO/PPO remote RM, text-image-to-text SFT, text-audio-to-text PPO, and any-to-any SFT.
- Janus trainer import requires an optional Janus-compatible package and is not covered as a ready base-runtime capability.
- CUDA PyTorch was available during construction; DeepSpeed emitted custom-op compatibility warnings when no CUDA toolkit path was configured, which is an execution-time troubleshooting item rather than an import failure.

## Safe execution rules

- Never run a model download, benchmark, dataset fetch, `share=True` Gradio server, Slurm submission, or long training job without explicit user intent and resource confirmation.
- Prefer dry-runs and import probes before running launchers.
- Treat `trust_remote_code=True`, vLLM backends, and remote Gradio sharing as security-sensitive.
- Keep model/data/output paths user-provided; do not reuse construction-time local paths.
