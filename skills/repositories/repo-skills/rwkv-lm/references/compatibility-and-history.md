# RWKV-LM compatibility and history map

RWKV-LM contains multiple historical implementation directories. Future agents
should not treat them as interchangeable.

| Area | Use today | Notes |
| --- | --- | --- |
| `RWKV-v1`, `RWKV-v2-RNN`, `RWKV-v3` | Historical reference only | Useful for architecture history, not current training guidance. |
| `RWKV-v4`, `RWKV-v4neo` | Legacy v4/v4neo training/inference and image/chat experiments | Good for migration questions; do not mix with RWKV-7 flags. |
| `RWKV-v5` | RWKV-5 and RWKV-6 training/data compatibility | RWKV-6 uses `--my_testing x060` in this tree. |
| `RWKV-v6` | Pointer to RWKV-v5 | The README says to use `RWKV-v5` with the v6 selector. |
| `RWKV-v7` | Current RWKV-7 demos and reference training path | `train_temp` is the recommended training implementation. |
| `RWKV-v8` | Experimental ROSA/Heron prototypes | Research scripts, mostly GPU/checkpoint-heavy. |

When a user asks for "latest" RWKV training, start with RWKV-7 `train_temp`.
When they ask for ROSA or Heron, use the RWKV-8 route and preserve the
experimental status. When they mention ChatRWKV, RWKV Runner, Ai00, or the
`rwkv` pip package, distinguish those external runtimes from this repository's
training/demo scripts.
