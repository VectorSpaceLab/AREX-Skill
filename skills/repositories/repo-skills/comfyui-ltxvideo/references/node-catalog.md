# Node Catalog

Source and live import inspection found 78 custom node class mappings and 79 display-name mappings. This catalog groups the node surface by task route. Use it when a user gives a node name and you need to choose the owning sub-skill.

## Core generation and latent routing

| Node family | Representative nodes | Owner | Use |
| --- | --- | --- | --- |
| Core samplers | `LTXVBaseSampler`, `LTXVInContextSampler`, `LTXVExtendSampler`, `LTXVNormalizingSampler` | `core-generation` | T2V/I2V, latent-guided generation, extension, and normalization-aware sampling. |
| Long/tiled samplers | `LTXVLoopingSampler`, `MultiPromptProvider`, `LTXVTiledSampler` | `core-generation` | Temporal chunks, spatial tiles, evolving prompts, long-form or high-resolution videos. |
| VAE decode helpers | `LTXVTiledVAEDecode`, `LTXVSpatioTemporalTiledVAEDecode` | `core-generation` | Decode large spatial/temporal latent videos with lower peak memory. |
| Latent utilities | `LTXVSelectLatents`, `LTXVAddLatents`, `LTXVDilateLatent`, `LTXVSetVideoLatentNoiseMasks`, `LTXVSetAudioVideoMaskByTime` | `core-generation` | Frame selection, concatenation, mask injection, and video/audio latent manipulation. |
| Guide/keyframe basics | `LTXVAddGuideAdvanced`, `LTXVAddGuideAdvancedAttention`, `LTXVImgToVideoAdvanced`, `LTXVImgToVideoConditionOnly` | `core-generation` | First-frame, image/video guide, keyframe, crop/blur/CRF conditioning before sampling. |
| Low-VRAM loaders | `LowVRAMCheckpointLoader`, `LowVRAMAudioVAELoader`, `LowVRAMLatentUpscaleModelLoader` | `core-generation` | Sequential model loading with dependency inputs to reduce load-time VRAM peaks. |

## Prompt and conditioning

| Node family | Representative nodes | Owner | Use |
| --- | --- | --- | --- |
| Local Gemma encoder | `LTXVGemmaCLIPModelLoader`, `LTXVGemmaEnhancePrompt` | `prompt-conditioning` | Load a local Gemma encoder and use Gemma/processor files for prompt rewrite. |
| API conditioning | `GemmaAPITextEncode` | `prompt-conditioning` | Produce conditioning via LTX Video API instead of local Gemma model loading. |
| Generic prompt enhancer | `LTXVPromptEnhancerLoader`, `LTXVPromptEnhancer` | `prompt-conditioning` | Load Hugging Face LLM/captioner prompt enhancer and apply optional image prompt. |
| Conditioning files | `LTXVSaveConditioning`, `LTXVLoadConditioning` | `prompt-conditioning` | Save/reload `CONDITIONING` safetensors artifacts under ComfyUI embeddings. |
| Dynamic/multimodal guidance | `DynamicConditioning`, `GuiderParameters`, `MultimodalGuider` | `prompt-conditioning` | Denoise-mask modulation and separate video/audio guider parameter controls. |
| Text embedding internals | `FeatureExtractorV1`, `FeatureExtractorV2`, `VideoEmbeddingsProcessor`, `AVEmbeddingsProcessor` | `prompt-conditioning` reference only | Source implementation details behind Gemma connector behavior. |

## Specialized workflows and media utilities

| Node family | Representative nodes | Owner | Use |
| --- | --- | --- | --- |
| IC-LoRA guide path | `LTXICLoRALoaderModelOnly`, `LTXAddVideoICLoRAGuide`, `LTXAddVideoICLoRAGuideAdvanced` | `specialized-workflows` | Load IC-LoRA metadata, add reference/control video or image guides, and tune per-guide attention. |
| Audio/video utilities | `LTXVSetAudioRefTokens`, `LTXVAudioOnlyModel`, `LTXVAudioOnlyEmptyVideoLatent` | `specialized-workflows` | DubIt/audio reference flows and text-to-audio with a dummy video latent. |
| HDR | `LTXVHDRDecodePostprocess` | `specialized-workflows` | Decode LogC3 HDR output, tonemap preview, and optionally write EXR. |
| Sparse motion tracks | `LTXVSparseTrackEditor`, `LTXVDrawTracks` | `specialized-workflows` | Draw/edit sparse track control points and render motion-track guide images. |
| Masks and in/outpaint | `LTXVPreprocessMasks`, `LTXVDilateVideoMask`, `LTXVInpaintPreprocess`, `LTXVLaplacianPyramidBlend` | `specialized-workflows` | Temporal mask preprocessing, video-mask dilation, green inpaint composites, and outpaint blending. |

## Advanced and experimental control

| Node family | Representative nodes | Owner | Use |
| --- | --- | --- | --- |
| STG/APG | `LTXVApplySTG`, `STGGuider`, `STGGuiderAdvanced`, `STGAdvancedPresets`, `APGGuider` | `advanced-control` | Expert classifier-free/STG/APG guidance, block skipping, rescale, and presets. |
| Q8 and VAE patches | `LTXQ8Patch`, `LTXVQ8LoraModelLoader`, `LTXVPatcherVAE` | `advanced-control` | Optional q8 kernels, Q8 LoRA loading order, and VAE patching. |
| Latent/stat normalization | `LTXVAdainLatent`, `LTXVStatNormLatent`, `LTXVPerStepAdainPatcher`, `LTXVPerStepStatNormPatcher` | `advanced-control` | Style/statistic normalization and per-step model patching. |
| Decoder/utility nodes | `Set VAE Decoder Noise`, `ImageToCPU`, `LTXFloatToInt` | `advanced-control` | Decode-noise injection and small helper conversions. |
| Tricks package | `ModifyLTXModel`, `AddLatentGuide`, `LTXAttentionBank`, `LTXPrepareAttnInjections`, `LTXAttnOverride`, `LTXPerturbedAttention`, `LTXFlowEditCFGGuider`, `LTXFlowEditSampler`, `LTXFetaEnhance`, `LTXRFForwardODESampler`, `LTXRFReverseODESampler`, `LTXForwardModelSamplingPred`, `LTXReverseModelSamplingPred` | `advanced-control` | Experimental attention, flow-edit, PAG/FETA, RF, and inverse-prediction controls. |

## Routing caveats

- Some workflow exports, especially newer ones, may contain UUID-like node types from ComfyUI subgraph/template exports. Use `../scripts/summarize_workflow_json.py` to inspect such graphs, then route by surrounding semantic node families and workflow intent.
- Some frontend behavior lives under `WEB_DIRECTORY = "./web"`; `LTXVSparseTrackEditor` is the active Python-backed sparse-track UI surface. Frontend-only references without matching Python node mappings should not be treated as guaranteed node routes.
- Q8 and OpenEXR support are optional; their missing dependencies should route to sub-skill preflight/troubleshooting rather than blocking unrelated workflows.
