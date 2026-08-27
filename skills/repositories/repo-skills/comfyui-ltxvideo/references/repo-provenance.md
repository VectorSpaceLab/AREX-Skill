# Repo Provenance

This runtime skill was distilled from the ComfyUI-LTXVideo repository snapshot below.

| Field | Value |
| --- | --- |
| Repository | ComfyUI-LTXVideo |
| Public remote | https://github.com/Lightricks/ComfyUI-LTXVideo.git |
| Commit | `ac4d99839020b983e956a8ab67ec38aec1b6e65a` |
| Branch | `master` |
| Exact tag | none found at HEAD |
| Working tree state at generation | dirty: untracked `skills/` production outputs were present/created during skill construction |
| Package version | not available: repository has no standalone Python package metadata or distribution version |
| Runtime shape | ComfyUI custom-node package loaded by ComfyUI from a folder containing `__init__.py` |
| Generated skill id | `comfyui-ltxvideo` |
| Import policy for this run | not imported, per user request |

## Evidence paths used

Relative source evidence paths inspected or distilled:

- `README.md`
- `requirements.txt`
- `__init__.py`
- `nodes_registry.py`
- Core generation modules: `easy_samplers.py`, `looping_sampler.py`, `looping_sampler.md`, `tiled_sampler.py`, `tiled_vae_decode.py`, `latents.py`, `guide.py`, `low_vram_loaders.py`
- Prompt/conditioning modules: `gemma_encoder.py`, `gemma_api_conditioning.py`, `prompt_enhancer_nodes.py`, `prompt_enhancer_utils.py`, `conditioning_loader.py`, `conditioning_saver.py`, `dynamic_conditioning.py`, `text_embeddings_connectors.py`, `embeddings_connector.py`, `guiders/`, `system_prompts/`, `gemma_configs/`
- Specialized workflow modules: `iclora.py`, `iclora_attention.py`, `audio_only.py`, `hdr.py`, `sparse_tracks.py`, `masks.py`, `vanish_nodes.py`, `pyramid_blending.py`, `web/js/sparse_track_editor.js`
- Advanced/experimental modules: `stg.py`, `q8_nodes.py`, `vae_patcher.py`, `latent_norm.py`, `decoder_noise.py`, `utiltily_nodes.py`, `tricks/`, `presets/stg_advanced_presets.json`
- Workflow evidence: `example_workflows/2.0/`, `example_workflows/2.3/`, `example_workflows/2.5/`, and media fixtures under `example_workflows/assets/` as native-verification candidates only

## Refresh signals

Refresh this skill when:

- `__init__.py` node mappings change;
- ComfyUI core changes the LTX-2 built-in node/API surface used by this custom node package;
- workflow JSON families are added, renamed, or migrate to new model versions;
- `requirements.txt` changes, especially Kornia, transformers, torch, q8, or OpenCV-related behavior;
- README model placement, VRAM, or supported workflow guidance changes;
- new Python-backed nodes are added under `web/js/` frontend behavior or `tricks/`.
