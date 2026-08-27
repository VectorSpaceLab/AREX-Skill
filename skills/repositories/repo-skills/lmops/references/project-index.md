# LMOps project index

Use this reference when a user names an LMOps paper/project acronym or asks which part of the repository applies to a task. Directory labels below are source-project identifiers from LMOps; they are not runtime links. Use the generated sub-skills and bundled scripts for operating guidance.

## Prompt optimization and rewriting

| Project label | Main task | Use |
| --- | --- | --- |
| `prompt_optimization` | ProTeGi automatic prompt optimization with gradient-style feedback and beam search for binary classification tasks. | `../sub-skills/prompt-optimization/SKILL.md` |
| `promptist` | Promptist text-to-image prompt rewriting, pretrained prompter demo, and RL training planning. | `../sub-skills/prompt-optimization/SKILL.md` |

## In-context example retrieval and ICL analysis

| Project label | Main task | Use |
| --- | --- | --- |
| `uprise` | Universal prompt retrieval for zero-shot or few-shot task prompting; command generation, prompt-pool encoding, retriever training, HF/OpenAI inference. | `../sub-skills/example-retrieval/SKILL.md` |
| `se2` | Sequential example selection with score, train, and infer stages. | `../sub-skills/example-retrieval/SKILL.md` |
| `llm_retriever` | Reward-model and KD bi-encoder training for in-context example retrieval. | `../sub-skills/example-retrieval/SKILL.md` |
| `ced_icl` | Cross-entropy-difference demonstration selection with T-Few dependency. | `../sub-skills/example-retrieval/SKILL.md` |
| `structured_prompting` | Many-shot structured prompting with Fairseq and HF variants. | `../sub-skills/example-retrieval/SKILL.md` |
| `understand_icl` | ICL-as-meta-optimizer analysis, recording, and result computation. | `../sub-skills/example-retrieval/SKILL.md` |

## Adaptation, data selection, and training support

| Project label | Main task | Use |
| --- | --- | --- |
| `adaptllm` | Convert raw domain corpora into reading-comprehension style pretraining text and plan domain benchmark inference. | `../sub-skills/adaptation-and-training/SKILL.md` |
| `instruction_pretrain` | Synthesize instruction-augmented corpora with an instruction synthesizer and vLLM. | `../sub-skills/adaptation-and-training/SKILL.md` |
| `data_selection` | Optimal-control data selection pipeline: proxy data, PMP solver, data scorer, data filtering, pretraining, and evaluation. | `../sub-skills/adaptation-and-training/SKILL.md` |
| `reslora` | ResLoRA adapter wrapper configuration and experiment flag planning. | `../sub-skills/adaptation-and-training/SKILL.md` |
| `learning_law` | Optimize and evaluate learning policies for perceptron and transformer settings. | `../sub-skills/adaptation-and-training/SKILL.md` |

## Distillation and ranking finetuning

| Project label | Main task | Use |
| --- | --- | --- |
| `minillm` | SFT, KD, SeqKD, MiniLLM on-policy distillation, evaluation, model-parallel conversion. | `../sub-skills/distillation-and-post-training/SKILL.md` |
| `dpkd` | Direct Preference Knowledge Distillation train/evaluate workflows. | `../sub-skills/distillation-and-post-training/SKILL.md` |
| `tuna` | Probabilistic and contextual ranking data for instruction tuning. | `../sub-skills/distillation-and-post-training/SKILL.md` |

## VeRL/Ray experiential learning and RL post-training

| Project label | Main task | Use |
| --- | --- | --- |
| `oel` | Online Experiential Learning round loop for text games and evaluation. | `../sub-skills/rl-experiential-learning/SKILL.md` |
| `opcd` | On-Policy Context Distillation for math, text games, and system prompts. | `../sub-skills/rl-experiential-learning/SKILL.md` |
| `llm-as-a-coach` | Experiential learning for non-verifiable tasks with train/eval/score aliases. | `../sub-skills/rl-experiential-learning/SKILL.md` |
| `gad` | Black-box generative adversarial distillation with SeqKD, warmup, adversarial, and eval stages. | `../sub-skills/rl-experiential-learning/SKILL.md` |
| `opo` | Exact on-policy RL and optimal reward baseline configuration guidance for VeRL-style PPO/GRPO. | `../sub-skills/rl-experiential-learning/SKILL.md` |

## RAG and acceleration

| Project label | Main task | Use |
| --- | --- | --- |
| `corag` | Chain-of-retrieval augmented generation with E5 search server, vLLM server, and multihop QA evaluation. | `../sub-skills/rag-and-acceleration/SKILL.md` |
| `llma` | Lossless reference-based decoding acceleration for overlapping references. | `../sub-skills/rag-and-acceleration/SKILL.md` |

## Low-priority or evidence-only areas

| Project label | Treatment |
| --- | --- |
| `LLM4Science` | Notebook evidence only. No generated execution workflow is provided because the checkout exposes no shared package/test harness for the notebooks. |
| Vendored/forked dependencies such as Transformers, Diffusers, TRLX, DPR, Fairseq, and VeRL copies | Use only for compatibility context and project-specific entry-point notes. Do not extract or treat them as the primary LMOps package surface. |
