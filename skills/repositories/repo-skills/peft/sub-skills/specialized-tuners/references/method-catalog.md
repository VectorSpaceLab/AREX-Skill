# Specialized Tuner Method Catalog

This catalog is for selecting PEFT tuners outside ordinary LoRA and prompt/soft-prompt methods. Most entries are injected with `get_peft_model(base_model, Config(...))`; exact support still depends on the target layer classes present in the base model.

## Selection map

| Need | Prefer | Why | Watch for |
| --- | --- | --- | --- |
| Very small multiplicative adapters for transformer projections | `IA3Config` | Learns vectors on attention and feed-forward modules; supports mixed-adapter registration. | `feedforward_modules` must be a subset of `target_modules` when both are lists/sets. |
| Orthogonal or rotation-style updates | `OFTConfig`, `BOFTConfig`, `HRAConfig`, `PsoftConfig`, `RoadConfig` | Preserves geometric structure and can be attractive when low-rank additive updates are unstable. | Supported layer types vary; RoAd is linear-layer focused and typically uses higher learning rates. |
| LyCORIS-style non-LoRA decomposition | `LoHaConfig`, `LoKrConfig` | LoHa uses Hadamard-product decomposition; LoKr uses Kronecker-product decomposition. | These are close LoRA alternatives but owned here for non-standard tuners; avoid using them for quantization-specific LoRA routing. |
| Extreme checkpoint-size reduction with shared projections | `VeraConfig`, `PveraConfig`, `RandLoraConfig`, `TinyLoraConfig` | Share or regenerate projection matrices and train small scaling vectors. | If reproducibility matters, keep projection matrices in the checkpoint; random regeneration can vary across devices or future PyTorch versions. |
| Full-rank or high-rank alternatives to LoRA | `RandLoraConfig`, `ShiraConfig`, `HiraConfig`, `C3AConfig`, `FrodConfig`, `WaveFTConfig`, `DeloraConfig`, `MissConfig`, `PeanutConfig` | Target cases where rank deficiency is suspected or the task needs more expressive updates. | Many are newer and more method-specific; verify layer support and default initialization before large runs. |
| Multi-adapter or expert routing | `XLoraConfig`, `PolyConfig`, `RoadConfig`, `IA3Config` | XLora gates existing LoRA experts; Poly learns adapter routing; RoAd and IA3 have mixed-compatible registrations. | XLora depends on LoRA experts and is not a generic replacement for `LoraConfig`. |
| Continual learning with subspace preservation | `OSFConfig` | Uses SVD-style preserved/adapted subspaces to reduce forgetting across tasks. | Recompute/wrap for sequential tasks so preserved directions reflect the latest weights. |
| Bias-only or LayerNorm-focused adaptation | `BeftConfig`, `LNTuningConfig` | Very small parameter budget and simple target surfaces. | Defaults may target LayerNorm/bias-like modules; use explicit `target_modules` for custom architectures. |
| Adaptive subspace allocation | `AdamssConfig` | Segments SVD subspaces and supports Adaptive Subspace Allocation behavior. | Subspace parameters must be consistent with target modules and rank choices. |
| Vector-bank sharing | `VBLoRAConfig` | Shares a vector bank and learns top-k composition, reducing stored parameters. | `save_only_topk_weights=True` is intended for merge/inference and not resume-training workflows. |

## Method notes

### IA3

IA3 applies learned multiplicative vectors. The key configuration distinction is `feedforward_modules`: feed-forward targets multiply inputs, while other targets multiply outputs. For list/set targets, PEFT validates `feedforward_modules` is a subset of `target_modules`. Use explicit targets such as `q_proj`, `v_proj`, and an MLP module (`fc2`, `w0`, or architecture-specific equivalent).

### BOFT and OFT

BOFT and OFT are orthogonal fine-tuning methods. They are good candidates when preserving geometry matters or when additive low-rank updates are not the right inductive bias. `BOFTConfig` exposes butterfly-factor style controls; `OFTConfig` exposes OFT block/rank controls and has optional backend-specific classes in the package for some quantized linear implementations.

### LoHa and LoKr

LoHa and LoKr are LyCORIS-style tuners. They share common target-module concepts with LoRA but use different decompositions. They are useful when users want a LoRA-family alternative without entering LoRA initialization or quantization workflows.

### VeRA, PVeRA, RandLoRA, and TinyLoRA

These methods reduce stored/trainable parameters by sharing or regenerating random projections and learning small scaling vectors. PEFT configs typically expose projection seed/key and `save_projection` style options. Use `save_projection=True` when exact checkpoint reproducibility matters; use projection regeneration only when the storage tradeoff is worth potential cross-version/device variation.

### VBLoRA

VBLoRA uses a vector bank plus top-k sharing. Saving only top-k weights drastically reduces checkpoint size, but those checkpoints are meant for merging or inference rather than resuming training. If the workflow requires continuing training, save all trainable logits.

### XLora

XLora is a router over existing LoRA adapters. It should be selected when the user has multiple LoRA experts and wants token/layer-wise gating, not when the user simply needs a single non-LoRA adapter. Validate expert adapters, task type, and LoRA target compatibility before configuring `XLoraConfig`.

### LN tuning and BEFT

`LNTuningConfig` trains LayerNorm parameters by default and can target other module names explicitly. `BeftConfig` focuses on bias-efficient fine-tuning, especially low-data regimes. These are good first checks for ultra-low-parameter adaptation before reaching for more complex decompositions.

### FourierFT, FRoD, HRA, HiRA, SHiRA, C3A, WaveFT, DeLoRA, MiSS, PEANuT

These are expressive non-LoRA alternatives with method-specific initialization and target-layer constraints. Treat them as deliberate choices: name the intended advantage (spectral compression, full-rank diagonalization, Householder reflections, Hadamard/high-rank update, sparse high-rank update, circular convolution, wavelet/spectral update, decoupled robust low-rank update, shard sharing, or neural tweakers) and then verify target module support on a small model before a large run.

### OSF

OSF is specifically useful for continual learning. Choose `effective_rank` as an integer, fraction, or `None` for defaults. For a sequence of tasks, re-wrap or recompute after each task so the preserved subspace reflects the current model, not only the original checkpoint.

## Mixed-adapter guidance

PEFT registration marks only some methods as mixed-compatible. Evidence in this checkout shows `IA3Config`, `LoHaConfig`, `LoKrConfig`, `RoadConfig`, `HiraConfig`, and `BeftConfig` registered with mixed compatibility. Other specialized tuners may still support multiple named adapters through normal PEFT lifecycle operations, but do not promise per-sample mixed adapter batches or weighted composition unless the method is registered and tested for it.

For mixed requests:

1. Prefer a known mixed-compatible method if per-sample `adapter_names` routing is required.
2. Keep target-module types consistent across adapters; IA3 also requires target/feedforward module types to match for weighted adapters.
3. Avoid combining adapters that save the same `modules_to_save` target unless the method explicitly supports it.
4. For XLora, treat the LoRA experts as prerequisites and route LoRA-specific questions to the LoRA sub-skill.
