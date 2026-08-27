# Troubleshooting

## Wrong language
**Symptom:** the answer only finds the Chinese title or only the English title.

**Likely cause:** the prompt uses a different alias, acronym, or script than the bundled index entry.

**Fix:** search both the acronym and the expansion, then surface both language forms in the reply.

## Missing concept
**Symptom:** the query does not seem to exist in the atlas.

**Likely cause:** the term belongs to a neighboring family or uses a different naming convention.

**Fix:** reclassify by axis:
- architecture / decoding -> `LLM basics`
- weight update / fine-tuning -> `SFT / LoRA` or `DPO`
- alignment pipeline -> `RLHF / RLAIF`
- policy update -> `Policy optimization`
- search / reasoning -> `Reasoning optimization`
- retrieval / function calling / decode-time heuristics -> `Optimization without training`
- catalog / citation / reuse -> `Model catalog` or `Citation & license`

## Stale model catalog
**Symptom:** a row looks out of date or a link no longer matches the latest release.

**Likely cause:** the catalog is snapshot-based and manually maintained.

**Fix:** use the catalog for orientation only, then verify the official model card or project page before making freshness, licensing, or deployment claims.

## Citation or image misuse
**Symptom:** the user wants to reuse diagrams or snippets but does not mention attribution or publication context.

**Likely cause:** the license rules were not checked yet.

**Fix:** follow `citation-and-license.md`:
- keep embedded attribution for online posts or blogs,
- cite formally for papers, books, and reports,
- do not use the materials for direct commercial purposes.

## Confusing algorithm-family boundaries
**Symptom:** the user mixes PPO, GRPO, DPO, RLHF, RAG, and CoT as if they were the same kind of method.

**Likely cause:** the prompt spans multiple axes at once.

**Fix:** explain the axis first:
- `DPO` = preference optimization,
- `RLHF` = alignment pipeline,
- `PPO` / `GRPO` / `TRPO` / `DDPG` = policy-optimization families,
- `RAG` / function calling = training-free augmentation,
- `CoT` / `ToT` / `MCTS` = reasoning/search families.

## Asset mutation boundary
**Symptom:** the user asks to trim image whitespace or rename assets from spreadsheet mappings.

**Likely cause:** the request belongs to asset maintenance, not the knowledge atlas.

**Fix:** route the request to `asset-maintenance`; do not solve it here.
