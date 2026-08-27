# StarVLA model families and registry names

Evidence basis: `README.md`, `docs/VM4A.md`, `docs/WM4A.md`, `docs/model_zoo.md`, `docs/faq.md`, registry decorators under `starVLA/model/framework/{VLM4A,VM4A,WM4A}/`, and model/action module dispatch code.

## Mental model

StarVLA organizes model construction around a single framework registry. A training/evaluation config selects a framework by `framework.name`; `build_framework(cfg)` auto-discovers framework modules, resolves that registered key, and constructs the model. All registered families are expected to implement the shared `baseframework` interface: training `forward(...)` returns an `action_loss`, and inference `predict_action(...)` returns `normalized_actions` for later unnormalization/deployment.

The three high-level families are:

| Family | Use it for | Typical backbone | Typical output style |
| --- | --- | --- | --- |
| VLM4A | vision-language-action models where a VLM supplies image/language features | Qwen2.5/3/3.5-VL, MiniCPM-V, Gemma 4, Cosmos-Reason2, Florence, EgoVLA/VILA, Molmo2 | action tokens, MLP actions, flow/diffusion action chunks |
| VM4A | lightweight visuomotor baselines without a large VLM/world model | ResNet-18 visual encoders inside ACT or Diffusion Policy | normalized action chunks |
| WM4A | world-model-for-action variants using video-generation DiT features | Cosmos-Predict2 or Wan2.2 | MLP, flow-matching, or layer-wise action chunks |

## Registry keys in this checkout

Run `scripts/inspect_framework_registry.py` against an installed StarVLA environment for the final source-of-truth list. Source decorators in this checkout show these public keys.

### VLM4A core and related VLM swaps

| Registry key | Common label | Backbone/action idea | Selection notes |
| --- | --- | --- | --- |
| `QwenFast` | StarVLA-FAST / QwenFAST | Qwen-VL with FAST action tokenizer and autoregressive action-token prediction | Requires an action-token-capable VLM/tokenizer. Good when you want discrete action-token modeling rather than a separate continuous action head. |
| `QwenOFT` | StarVLA-OFT | Qwen-VL plus MLP/L1 continuous action head over action special-token hidden states | Fast continuous baseline; action head hidden dim is aligned from the loaded VLM. |
| `QwenPI`, `QwenFM` | StarVLA-PI | Qwen-VL plus layer-wise flow-matching cross-DiT action head | Uses multiple VLM layers. The framework populates DiT shape fields from the loaded VLM hidden size/layer count. |
| `QwenPI_v3` | QwenPI_v3 | Qwen-VL plus per-layer projectors into an action DiT hidden space | Useful when compressing VL hidden states with `action_dit_hidden_dim`. Be careful with legacy-vs-canonical forward semantics for old checkpoints. |
| `QwenGR00T` | StarVLA-GR00T | Qwen-VL as System-2, single-layer/last-hidden-state flow-matching DiT as System-1 | Good default for GR00T-style continuous action chunks; `cross_attention_dim` is overwritten from the actual VLM hidden size. |
| `MiniCPMPI`, `MiniCPMGR00T` | MiniCPM-V PI/GR00T | Direct ports of QwenPI/QwenGR00T to MiniCPM-V 4.6 | VLM dispatch is selected by `framework.qwenvl.base_vlm` containing MiniCPM-V. Source asserts the expected 1024 hidden size. |
| `Gemma4PI`, `Gemma4GR00T` | Gemma 4 PI/GR00T | Direct ports of QwenPI/QwenGR00T to Gemma 4 | VLM dispatch is selected by `framework.qwenvl.base_vlm` containing Gemma 4. Hidden-size alignment is asserted. |
| `CosmosGR00T` | Cosmos-Reason2 GR00T | Cosmos-Reason2 VLM with GR00T flow-matching head | This is VLM4A using a physical-reasoning VLM, distinct from WM4A Cosmos-Predict2 world-model variants. |
| `QwenDiscreteDiffusion` | discrete diffusion | Qwen-VL plus MaskGIT-style layer-wise discrete diffusion action head | Use when exploring discrete diffusion action generation, not the standard FAST tokenizer path. |
| `QwenDual` | dual Qwen/action setup | Qwen-VL with dual action path | Specialized; inspect config before assuming compatibility with released checkpoints. |
| `QwenAdapter` | adapter action head | Qwen-VL with VLA adapter/proprio projector | Specialized adapter route with a different state/proprio contract. |
| `ABot_M0` | ABot-M0 | Qwen-style VLM with high-dimensional flow-matching action variant | Source notes it targets larger action-dimensional chunks than vanilla GR00T. |
| `InternVLA-M1`, `LangForce`, `EgoVLA`, `PI0`, `Pi0`, `PI05`, `Pi05` | additional experimental/framework ports | Framework-specific VLM/action-head compositions | Treat as source-backed but less central; verify registry presence and required pretrained components before recommending. |

### VM4A

| Registry key | Policy | Backbone/action idea | Selection notes |
| --- | --- | --- | --- |
| `ACT` | LeRobot ACTPolicy wrapper | ResNet-18 image encoder, state input, transformer action chunk | Use as a compact visuomotor baseline. Optional `lerobot` dependency is guarded at import; missing dependency fails only at instantiation. |
| `DiffusionPolicy` | Diffusion Policy image-policy subset | ResNet-18 multi-image encoder, DDPM/1D U-Net action generation | Uses a vendored non-hybrid image-policy subset and persists EMA weights under `ema_averaged.*`. Public checkpoints are not promised in docs. |

### WM4A

| Registry key | Backbone | Action head | Selection notes |
| --- | --- | --- | --- |
| `CosmoPredict2OFT` | Cosmos-Predict2-2B video DiT | MLP/L1 (OFT-style) | Fastest WM4A head; simplest for LIBERO-style WM4A experiments. |
| `CosmoPredict2GR00T` | Cosmos-Predict2-2B video DiT | flow-matching GR00T-style | Medium-speed diffusion/flow action head over world-model features. |
| `CosmoPredict2PI` | Cosmos-Predict2-2B video DiT | layer-wise PI/cross-DiT | Slower but uses all selected transformer layers. |
| `WanOFT` | Wan2.2-TI2V-5B Diffusers | MLP/L1 (OFT-style) | Wan alternative to Cosmos; hidden size is larger than Cosmos. |
| `WanGR00T` | Wan2.2-TI2V-5B Diffusers | flow-matching GR00T-style | Wan backbone with flow action head. |
| `WanPI` | Wan2.2-TI2V-5B Diffusers | layer-wise PI/cross-DiT | Wan backbone with layer-wise action head. |

The WM4A documentation mentions a generic `WM4A_OFT`, but source decorators in this checkout register the six concrete Cosmos/Wan keys above. Do not assume `WM4A_OFT` is valid unless the registry script reports it in the target environment.

## Choosing a family

- Choose `QwenFast` when the checkpoint/tokenizer is explicitly an Action-token VLM and the user wants autoregressive discrete action-token prediction.
- Choose `QwenOFT` or `CosmoPredict2OFT`/`WanOFT` when the user wants the simplest continuous-action MLP head and fastest iteration.
- Choose `QwenPI`, `QwenPI_v3`, `MiniCPMPI`, or `Gemma4PI` when the user needs layer-wise VLM conditioning through a flow-matching action DiT.
- Choose `QwenGR00T`, `MiniCPMGR00T`, `Gemma4GR00T`, or `CosmosGR00T` when the task calls for GR00T-style VLM-as-System-2 plus flow-matching System-1 action generation.
- Choose `ACT` or `DiffusionPolicy` when the research question is a compact visuomotor baseline/control that should share StarVLA data, normalization, training, and deployment surfaces without a large VLM.
- Choose WM4A (`CosmoPredict2*`, `Wan*`) when the user explicitly wants video/world-model representations rather than VLM representations.

## Released model/checkpoint facts

The model-zoo evidence lists modified action-token VLMs for Qwen2.5-VL-3B and Qwen3-VL-4B, several Qwen Bridge/Fractal finetuning checkpoints for FAST/OFT/PI/GR00T/PI_v3, and a Calvin QwenGR00T checkpoint. VM4A docs describe ACT and Diffusion Policy as real-robot validated but public checkpoints as TBD. WM4A docs point to pretrained world-model-to-VLA checkpoints, but exact reproduction still depends on matching the checkpoint-time config/code and locally available backbone weights.
