# Optimizer API

## Purpose

Use this reference to choose the right `bitsandbytes.optim` class and verify constructor defaults before writing training-loop code. Signatures are based on installed API inspection plus optimizer source files.

## Family Map

| Family | 32-bit/default classes | 8-bit classes | Paged classes | Typical use |
| --- | --- | --- | --- | --- |
| Adam | `Adam`, `Adam32bit` | `Adam8bit` | `PagedAdam`, `PagedAdam8bit`, `PagedAdam32bit` | General drop-in replacement for `torch.optim.Adam`. |
| AdamW | `AdamW`, `AdamW32bit` | `AdamW8bit` | `PagedAdamW`, `PagedAdamW8bit`, `PagedAdamW32bit` | Decoupled weight decay, common for Transformers and finetuning loops. |
| Lion | `Lion`, `Lion32bit` | `Lion8bit` | `PagedLion`, `PagedLion8bit`, `PagedLion32bit` | Lion optimizer workflows with 8-bit or paged state. |
| AdEMAMix | `AdEMAMix`, `AdEMAMix32bit` | `AdEMAMix8bit` | `PagedAdEMAMix`, `PagedAdEMAMix8bit`, `PagedAdEMAMix32bit` | AdEMAMix with three beta values and optional schedule parameters. |
| Other optimizers | `SGD`, `RMSprop`, `Adagrad`, `LAMB`, `LARS` and 32-bit variants | matching `*8bit` variants where exported | no paged variants for every family | Use when the training recipe already depends on that optimizer family. |

## Verified Constructor Signatures

| API | Signature and defaults | Notes |
| --- | --- | --- |
| `bnb.optim.Adam` | `Adam(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False, optim_bits=32, args=None, min_8bit_size=4096, is_paged=False)` | Set `optim_bits=8` to request 8-bit states through the generic class. |
| `bnb.optim.Adam8bit` | `Adam8bit(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False, optim_bits=32, args=None, min_8bit_size=4096, is_paged=False)` | Despite the compatibility parameter, this class always uses 8-bit optimization; source rejects `amsgrad=True` and non-default `optim_bits`. |
| `bnb.optim.Adam32bit` | `Adam32bit(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False, optim_bits=32, args=None, min_8bit_size=4096, is_paged=False)` | Explicit 32-bit bitsandbytes Adam. |
| `bnb.optim.AdamW` | `AdamW(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0.01, amsgrad=False, optim_bits=32, args=None, min_8bit_size=4096, is_paged=False)` | Weight decay default differs from Adam. |
| `bnb.optim.AdamW8bit` | `AdamW8bit(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0.01, amsgrad=False, optim_bits=32, args=None, min_8bit_size=4096, is_paged=False)` | Always 8-bit; source rejects unsupported `amsgrad=True` and non-default `optim_bits`. |
| `bnb.optim.PagedAdamW8bit` | `PagedAdamW8bit(params, lr=0.001, betas=(0.9, 0.999), eps=1e-08, weight_decay=0.01, amsgrad=False, optim_bits=32, args=None, min_8bit_size=4096)` | Paged and 8-bit; intended for accelerator memory pressure, not CPU memory savings. |
| `bnb.optim.Lion8bit` | `Lion8bit(params, lr=0.0001, betas=(0.9, 0.99), weight_decay=0, args=None, min_8bit_size=4096, is_paged=False)` | No `eps`; defaults follow Lion source. |
| `bnb.optim.PagedLion8bit` | `PagedLion8bit(params, lr=0.0001, betas=(0.9, 0.99), weight_decay=0, args=None, min_8bit_size=4096)` | Paged Lion variant. |
| `bnb.optim.AdEMAMix8bit` | `AdEMAMix8bit(params, lr=0.001, betas=(0.9, 0.999, 0.9999), alpha=5.0, t_alpha=None, t_beta3=None, eps=1e-08, weight_decay=0.01, min_8bit_size=4096, is_paged=False)` | Supports optional `t_alpha` and `t_beta3` scheduling parameters. |
| `bnb.optim.PagedAdEMAMix8bit` | `PagedAdEMAMix8bit(params, lr=0.001, betas=(0.9, 0.999, 0.9999), alpha=5.0, t_alpha=None, t_beta3=None, eps=1e-08, weight_decay=0.01, min_8bit_size=4096)` | Paged AdEMAMix 8-bit variant. |
| `bnb.optim.GlobalOptimManager` | `GlobalOptimManager()`; usually accessed as `GlobalOptimManager.get_instance()` | Global registry for per-parameter overrides such as `optim_bits`, `lr`, `betas`, or sparse flags. |
| `bnb.nn.StableEmbedding` | `StableEmbedding(num_embeddings, embedding_dim, padding_idx=None, max_norm=None, norm_type=2.0, scale_grad_by_freq=False, sparse=False, _weight=None, device=None, dtype=None)` | Embedding layer intended to improve NLP stability and keep optimizer states for the layer in 32-bit. |

## State Configuration Knobs

| Knob | Where it appears | Meaning |
| --- | --- | --- |
| `optim_bits` | Generic optimizer constructors and `GlobalOptimManager` overrides | `32` means full-precision optimizer states; `8` means 8-bit optimizer states. Dedicated `*8bit` classes may keep `optim_bits=32` only as a compatibility argument while internally forcing 8-bit. |
| `min_8bit_size` | Most bitsandbytes optimizers | Parameters with fewer elements than this threshold stay 32-bit. Default is `4096`; use multiples of `4096` when changing it. |
| `is_paged` | Generic classes and non-paged class constructors | Enables paged state allocation when supported; dedicated `Paged*` classes set this internally. |
| `amsgrad` | Adam/AdamW classes | Not supported by dedicated 8-bit Adam/AdamW classes in current source. |

## State Validation Hints

After one optimizer step, inspect `optimizer.state[param]` for tensor states. For large parameters using 8-bit states, expect quantized state tensors and associated scaling/metadata entries rather than only full-precision Adam moments. For tensors below `min_8bit_size`, seeing 32-bit state tensors is expected, not a failed quantization.

Use `state_dict()` and `load_state_dict()` through normal PyTorch optimizer APIs. Validate after loading by running one small forward/backward/step and checking that the state keys and tensor devices match the active model parameters.
