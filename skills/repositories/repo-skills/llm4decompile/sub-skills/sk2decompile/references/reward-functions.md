# SK²Decompile Reward Functions

The repo's RL examples ship four reward modules under `verl/SK2DECOMPILE/reward_functions/`.

## Structure recovery rewards

### `exe_type.py`

- **Reward shape**: compilability gate + placeholder-identifier Jaccard similarity.
- **Use case**: skeleton/structure recovery.
- **Behavior**: returns `0.0` if the generated code does not compile with `gcc -c`; otherwise returns the type score plus a compile score.

### `sim_exe.py`

- **Reward shape**: compilability gate + word-level Jaccard similarity.
- **Use case**: alternate structure recovery signal.
- **Behavior**: only rewards outputs that cross the similarity threshold and compile successfully.

## Identifier naming rewards

### `embedding_gte.py`

- **Reward shape**: cosine similarity of GTE embeddings squared.
- **Use case**: identifier naming / skin stage.
- **Requires**: an OpenAI-compatible embedding server, `tree_sitter`, and `tree_sitter_c`.
- **Environment vars**:
  - `GTE_EMBEDDING_MODEL_PATH`
  - `GTE_EMBEDDING_API_KEY` or `OPENAI_API_KEY`
  - `GTE_EMBEDDING_API_BASE`

### `embedding_qwen3.py`

- **Reward shape**: cosine similarity of Qwen3 embeddings squared.
- **Use case**: alternate identifier naming signal.
- **Requires**: an OpenAI-compatible embedding server, `tree_sitter`, and `tree_sitter_c`.
- **Environment vars**:
  - `QWEN3_EMBEDDING_MODEL_PATH`
  - `QWEN3_EMBEDDING_API_KEY` or `OPENAI_API_KEY`
  - `QWEN3_EMBEDDING_API_BASE`

## Practical guidance

- Use the compilability-gated reward functions when the user wants the structure-recovery stage.
- Use the embedding-based reward functions when the user wants identifier naming or semantic recovery.
- If the embedding server is unavailable, keep the reward modules as reference material and do not claim the identifier reward was fully verified.
