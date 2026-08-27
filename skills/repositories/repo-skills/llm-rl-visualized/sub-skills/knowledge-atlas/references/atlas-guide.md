# Atlas guide

## What this guide is for
Use the atlas to answer concept-navigation prompts without reopening the source repository. A good answer usually has four parts:

1. Canonical term.
2. Closest family or diagram.
3. Boundary with neighboring families.
4. Limitation or freshness note.

Prefer "where to look" over "how to implement".

## Recommended synthesis workflow
- Detect the user's language first; mirror it when possible and keep the other language as a synonym.
- Normalize the ask into a family: `LLM basics`, `SFT / LoRA`, `DPO`, `Optimization without training`, `RL basics`, `Policy optimization`, `RLHF / RLAIF`, `Reasoning optimization`, `LLM extensions`, `Roadmap`, `Model catalog`, `Citation & license`, `Book snippets`, or `Bilingual terms`.
- Search both acronym and expansion if the first lookup is thin.
- If the user asks for a comparison, compare by axis instead of by historical order.
- If the user asks for a diagram family, name the family and one sibling figure to inspect next.

### Helpful comparison axes
- Training signal: supervised labels, preference pairs, reward model, or search-based reasoning.
- Objective: cross-entropy, preference loss, policy-gradient surrogate, or decoding-side heuristic.
- Reference model: none, frozen reference, or reward-model guidance.
- Update style: weight update, policy update, or no training at all.
- Runtime role: architecture, decoding, retrieval, search, or alignment pipeline.

### Example: PPO vs GRPO vs DPO vs RLHF
- `DPO` is direct preference optimization from chosen/rejected pairs.
- `RLHF` is the broader alignment pipeline that often includes reward modeling and a policy-optimization stage.
- `PPO` is a policy-optimization algorithm commonly used inside RLHF-style pipelines.
- `GRPO` is another policy-optimization family; use the atlas's PPO/GRPO diagram and note that implementation details vary by paper and framework.

## Category map

| Category | Typical prompts | Best bundled reference |
| --- | --- | --- |
| LLM basics | architecture, input/output, decoding, training flow, MLLM/VLM | `references/atlas-index.json` |
| SFT / LoRA | LoRA, Prefix-Tuning, packing, SFT loss, token mapping | `references/book-code-snippets.md` |
| DPO | DPO vs RLHF/PPO, chosen/rejected, beta, implicit reward | `references/book-code-snippets.md`, `references/citation-and-license.md` |
| Optimization without training | CoT, search, RAG, function calling, sampling, decoding-side heuristics | `references/atlas-index.json` |
| RL basics | MDP, return, value, MC, TD, DQN, IL/BC/IRL | `references/atlas-index.json` |
| Policy optimization | Actor-Critic, GAE, TRPO, PPO, GRPO, DPG/DDPG | `references/book-code-snippets.md`, `references/atlas-index.json` |
| RLHF / RLAIF | reward model, KL penalty, rejection sampling, CAI, RBR | `references/atlas-index.json`, `references/citation-and-license.md` |
| Reasoning optimization | CoT distillation, MCTS, BoN, majority vote, ORM/PRM | `references/atlas-index.json` |
| LLM extensions | RoPE, quantization, normalization, attention variants, benchmarks | `references/atlas-index.json` |
| Roadmap | study sequence, math, infra, resource list | `references/atlas-index.json` |
| Model catalog | paper/code/config lookup, LLM/VLM rows, model family orientation | `references/model-catalog-guide.md` |
| Citation & license | reuse, attribution, non-commercial use, BibTeX | `references/citation-and-license.md` |
| Book snippets | educational code orientation | `references/book-code-snippets.md` |
| Bilingual terms | Chinese/English aliases and file-name normalization | `references/atlas-index.json`, `references/troubleshooting.md` |

## Bilingual handling
- Search both the acronym and the expanded English term.
- If the first result is only in one language, surface the alias in the other language on first mention.
- Preserve mixed-script figure titles and full-width punctuation when quoting a file name or diagram title.
- If the query is Chinese but the only strong match is English, answer with both forms and the canonical family.

### Common alias pairs
- `PPO` = Proximal Policy Optimization / 近端策略优化
- `DPO` = Direct Preference Optimization / 直接偏好优化
- `SFT` = Supervised Fine-Tuning / 监督微调
- `RAG` = Retrieval-Augmented Generation / 检索增强生成
- `RLHF` = Reinforcement Learning from Human Feedback / 基于人类反馈的强化学习
- `VLM` = Vision-Language Model / 视觉语言模型
- `RoPE` = Rotary Position Embedding / 旋转位置编码
- `MCTS` = Monte Carlo Tree Search / 蒙特卡洛树搜索

## Diagram-vs-text caveats
- Diagrams are conceptual summaries, not exhaustive implementation specs.
- `src/code_from_book.md` snippets are pedagogical and may omit edge cases, framework-specific masks, batching, or device/dtype handling.
- The model catalog is a snapshot-oriented index; row dates and links can lag the official release state.
- The atlas is self-contained; answer from the bundled references first.

## Suggested answer template
- Canonical term.
- Closest family.
- What it shows.
- What it is not.
- One bundled reference file to inspect next.

## Provenance note
This guide was distilled from `README.md`, `src/README_EN.md`, `AI-Roadmap(AI知识架构).md`, `LLM-VLM-index (汇总).md`, `src/references.md`, `src/code_from_book.md`, and `LICENSE`.
