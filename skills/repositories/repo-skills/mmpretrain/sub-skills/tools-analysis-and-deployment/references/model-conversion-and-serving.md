# Model Conversion and Serving

This reference covers checkpoint publishing, structural reparameterization, family-specific converters, and TorchServe packaging.

## Publishing checkpoints

| Tool | Input contract | Output contract | Notes |
| --- | --- | --- | --- |
| `scripts/publish_checkpoint.py` | Source checkpoint plus a target file or target directory. Optional dataset type and EMA choice. | A new publish-ready checkpoint artifact. The source file is never mutated. | Safe helper: removes training-only fields, adds metadata, and can merge EMA weights only when requested. |
| `publish_model` | Source checkpoint plus an output path. Optional dataset type and EMA toggle. | A timestamped publish-ready checkpoint name. | Official converter with the same high-level goal; use it when you want the native repository script semantics. |

### Publishing rules
- Drop optimizer state, scheduler state, hook messages, and other training-only fields before distributing a checkpoint.
- Add `mmpretrain_version` to the metadata when publishing.
- If a dataset family is known, attach the dataset metainfo so downstream tools can read class labels.
- Preserve the input file and write a new artifact path.
- Treat EMA carefully: only merge EMA weights when the key layout matches the base state dict.

## Structural reparameterization

| Tool | When to use | Input contract | Output contract | Notes |
| --- | --- | --- | --- | --- |
| `reparameterize_model.py` | A backbone exposes a deploy conversion path such as `switch_to_deploy()`. | Config, checkpoint, and save path. | A deploy-mode checkpoint with the reparameterized weights. | Best for RepVGG-style or other deployable backbones. The model must be buildable as an image classifier. |

## Family-specific converters

Most conversion scripts in this family are one-way format bridges from an external checkpoint layout into an MMPreTrain layout. Choose the script that matches the source checkpoint family as closely as possible.

| Source family | Representative scripts | Typical use | Notes |
| --- | --- | --- | --- |
| Generic torchvision / image-classification weights | `torchvision_to_mmpretrain.py`, `vgg_to_mmpretrain.py`, `mobilenetv2_to_mmpretrain.py`, `efficientnet_to_mmpretrain.py`, `efficientnetv2_to_mmpretrain.py` | Convert common classification checkpoints into MMPreTrain naming and head layout. | Usually needs only the source weights and a matching target config family. |
| Modern convnets and reparameterized backbones | `convnext_to_mmpretrain.py`, `repvgg_to_mmpretrain.py`, `replknet_to_mmpretrain.py`, `van2mmpretrain.py`, `shufflenetv2_to_mmpretrain.py`, `vig_to_mmpretrain.py`, `edgenext_to_mmpretrain.py` | Convert family-specific backbone weights. | Parameter names are architecture-specific; do not reuse across unrelated models. |
| Transformer backbones | `deit3_to_mmpretrain.py`, `tinyvit_to_mmpretrain.py`, `twins2mmpretrain.py`, `revvit_to_mmpretrain.py`, `eva_to_mmpretrain.py`, `eva02_to_mmpretrain.py`, `levit2mmpretrain.py` | Convert transformer checkpoints with patch embeddings, tokens, and stage-specific naming. | Extra tokens, positional embeddings, and classifier heads often need exact matching. |
| Multimodal and open-vocabulary weights | `clip_to_mmpretrain.py`, `openai-clip_to_mmpretrain-clip.py`, `glip_to_mmpretrain.py`, `ram2mmpretrain.py`, `llava-delta2mmpre.py`, `otter2mmpre.py`, `ofa.py` | Convert external multimodal or task-specific weights. | These converters are especially sensitive to tokenizer, vision, and text-encoder settings. |
| Adapter and low-rank merges | `merge_lora_weight.py` | Merge LoRA deltas into a base model. | Use only when the LoRA module layout matches the target model. |

## TorchServe packaging

| Tool | Input contract | Output contract | Notes |
| --- | --- | --- | --- |
| `mmpretrain2torchserve.py` | Config, checkpoint, output folder, and model name. | A TorchServe `.mar` archive in the output folder. | Requires `torchserve` and `torch-model-archiver`. The output folder must be writable, and the handler is bundled with the package. |
| `mmpretrain_handler.py` | Used by the archive produced above. | Inference-time handler logic. | Do not edit the archive by hand unless you are intentionally customizing serving behavior. |
| `test_torchserver.py` | Image, config, checkpoint, model name, and a running inference endpoint. | Comparison output between TorchServe and the local PyTorch path. | Use this only when the service is already running and reachable. |

## TorchServe flow

1. Convert a publish-ready checkpoint into a `.mar` archive.
2. Place the archive in the model store that TorchServe reads.
3. Start TorchServe with the expected inference, management, and metrics ports.
4. Send a prediction request to the model name registered in the archive.
5. Compare the serving result against the local model when you need a sanity check.

## Converter selection hints

- Use the closest family-specific converter when the checkpoint comes from an external repository with a known naming scheme.
- Use the publish helper after training when you only need a clean distributable checkpoint.
- Use reparameterization only when the architecture provides a deploy-time conversion path.
- Use TorchServe packaging only when you need a server artifact, not for ordinary local inference.
