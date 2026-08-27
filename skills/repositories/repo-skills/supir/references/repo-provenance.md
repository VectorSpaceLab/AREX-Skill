# SUPIR Repo Provenance

- skill id: `supir`
- source project: SUPIR (Scaling Up to Excellence: Practicing Model Scaling for Photo-Realistic Image Restoration In the Wild)
- source remote: `https://github.com/Fanghua-Yu/SUPIR.git`
- branch: `master`
- commit: `bda91af2000042f8bedfec8897d92917e67c1d88`
- exact tag: none detected
- package/distribution version: not declared; the repository provides import packages `SUPIR`, `sgm`, and `llava` without Python packaging metadata
- generated skill root: `skills/disco/supir/`
- generated from dirty checkout: yes
- dirty-state summary at generation time: untracked `skills/` production artifacts were present; source directories used as evidence were otherwise read-only during extraction

## Evidence paths

The generated skill distilled these source-relative evidence paths:

- `README.md`
- `requirements.txt`
- `CKPT_PTH.py`
- `options/SUPIR_v0.yaml`
- `options/SUPIR_v0_tiled.yaml`
- `options/SUPIR_v0_Juggernautv9_lightning.yaml`
- `test.py`
- `gradio_demo.py`
- `gradio_demo_tiled.py`
- `gradio_demo_face.py`
- `SUPIR/util.py`
- `SUPIR/models/SUPIR_model.py`
- `SUPIR/modules/SUPIR_v0.py`
- `SUPIR/utils/colorfix.py`
- `SUPIR/utils/tilevae.py`
- `SUPIR/utils/face_restoration_helper.py`
- `llava/llava_agent.py`
- `llava/model/builder.py`
- `llava/model/language_model/llava_llama.py`
- `sgm/util.py`
- `sgm/models/diffusion.py`
- `sgm/modules/diffusionmodules/sampling.py`
- `sgm/modules/encoders/modules.py`

## Refresh triggers

Refresh this skill when any of these change materially:

- SUPIR or SDXL checkpoint variable names or YAML fields change.
- `test.py` or any `gradio_demo*.py` flag surface changes.
- `SUPIR.util`, `SUPIRModel.batchify_sample`, `LLavaAgent`, tiled VAE, or face helper signatures change.
- The repo gains packaging metadata or a new official CLI.
- The documented dependency stack moves away from the Transformers 4.x/LLaVA registration behavior recorded in this skill.
