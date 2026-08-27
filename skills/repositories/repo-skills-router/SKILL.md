---
name: "repo-skills-router"
description: "Routes substantive ML, AI, data, scientific-computing, and software-engineering requests to the smallest useful set of managed repository skills. Invoke proactively when a request names or implies a package, framework, model family, dataset, modality, workflow, backend, deployment target, evaluation method, or implementation approach that may benefit from repository guidance, even if no repository is named. Narrow progressively from area to family to repository root: inspect only the one or two most likely area pages; compare candidates by capability, task surface, model/data format, training versus inference versus evaluation intent, runtime constraints, and root-skill description; then open only the selected root and relevant sub-skills, references, or scripts. Select multiple repositories only when each adds a distinct capability. Do not load the whole collection, treat dependencies or incidental integrations as capabilities, choose by name alone, or force a match when no exact taxonomy family applies."
metadata:
  disco-role: "operating"
---
# Repo Skills Router

Use this router for substantive requests where a managed repository skill may provide implementation guidance. It is a progressive-disclosure index, not a replacement for the selected repository skill.

## Routing procedure

1. Identify the user's dominant capability, workflow, data/model format, and runtime intent.
2. Read only the one or two most likely area pages below.
3. Compare the relevant family pages, especially when training, inference, evaluation, deployment, or similarly named repositories overlap.
4. Open the selected repository root at `../repo-skills/<skill-id>/SKILL.md`, then read only its relevant sub-skills, references, and scripts.
5. If no exact family fits, do not force a repository match; continue with the general task context or report that the managed collection has no exact route.

A repository may appear in several families. Choose the smallest set of repository roots that directly covers the request, and do not load every candidate listed on a family page.

## Area quick map

| Area | Populated families | Repository memberships | Area page |
| --- | ---: | ---: | --- |
| [Computer Vision](references/areas/computer-vision.md) | 21 | 312 |
| [Biomedical AI](references/areas/biomedical-ai.md) | 11 | 50 |
| [Generative Media](references/areas/generative-media.md) | 13 | 192 |
| [Speech and Audio](references/areas/speech-and-audio.md) | 5 | 55 |
| [Natural Language Processing](references/areas/natural-language-processing.md) | 9 | 78 |
| [LLM Applications](references/areas/llm-applications.md) | 16 | 323 |
| [LLM Models, Training, and Alignment](references/areas/llm-models-training-and-alignment.md) | 6 | 149 |
| [Information Retrieval](references/areas/information-retrieval.md) | 4 | 67 |
| [MLOps](references/areas/mlops.md) | 15 | 116 |
| [Model Deployment and Optimization](references/areas/model-deployment-and-optimization.md) | 4 | 114 |
| [Training Infrastructure](references/areas/training-infrastructure.md) | 12 | 135 |
| [Reinforcement Learning](references/areas/reinforcement-learning.md) | 5 | 82 |
| [Robotics and Embodied AI](references/areas/robotics-and-embodied-ai.md) | 7 | 81 |
| [Autonomous Driving](references/areas/autonomous-driving.md) | 3 | 38 |
| [Graph Learning](references/areas/graph-learning.md) | 4 | 42 |
| [Scientific Computing](references/areas/scientific-computing.md) | 16 | 124 |
| [Data Science](references/areas/data-science.md) | 12 | 152 |
| [Time Series Analysis](references/areas/time-series-analysis.md) | 7 | 53 |
| [Probabilistic and Causal Modeling](references/areas/probabilistic-and-causal-modeling.md) | 4 | 20 |
| [Responsible AI](references/areas/responsible-ai.md) | 4 | 21 |

## Maintenance

The machine-readable files under `references/index/` are the generated routing source of truth. Do not hand-edit area or family pages. For import, refresh, extension, or taxonomy changes, read [references/maintenance.md](references/maintenance.md) and use the verified importer/updater transaction.
