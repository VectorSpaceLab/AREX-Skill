# InternVideo-Next Troubleshooting

## Weight/config mismatch

Large/Base checkpoints require matching model config and stage. If state-dict keys or tensor shapes fail, confirm whether the checkpoint is Stage2 Large/Base and whether the model constructor matches.

## FlashAttention missing

InternVideo-Next model files use FlashAttention-related modules. Install compatible CUDA/Torch/FlashAttention packages in the target environment before running large jobs.

## Diffusion or JEPA loss confusion

Stage2 code introduces diffusion-loss and JEPA/masking components. Route architecture questions to the workflow reference and inspect the stage-specific model file before changing loss flags.

## Dataset decoding failures

The dataset loaders rely on video decoding and annotation paths. Validate a tiny list and codecs first; missing data should not be debugged as a model issue.

## Memory failures

Reduce frame count, batch size, crop/clip count, or model size for smoke checks. Preserve benchmark/pretraining settings separately from reduced local tests.
