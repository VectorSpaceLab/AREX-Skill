---
name: detectors-and-explainers
description: "Use AIF360 MDSS and FACTS subgroup detectors plus metric text and
  JSON explainers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# AIF360 Detectors and Explainers

Use this sub-skill when a task asks for subgroup bias scanning, MDSS/FACTS
detectors, or text/JSON explanations of AIF360 metric objects.

## Start here

1. Read [mdss-workflow.md](references/mdss-workflow.md) for legacy and sklearn
   `bias_scan` signatures, inputs, modes, scoring choices, and output handling.
2. Read [facts-workflow.md](references/facts-workflow.md) for optional FACTS
   counterfactual subgroup-recourse workflows and dependency requirements.
3. Read [explainer-reference.md](references/explainer-reference.md) for
   `MetricTextExplainer` and `MetricJSONExplainer` usage with metric objects.
4. Read [troubleshooting.md](references/troubleshooting.md) when labels,
   probabilities, indexes, optional extras, or metric objects do not match.
5. Use [mdss_smoke.py](scripts/mdss_smoke.py) or
   [explainer_smoke.py](scripts/explainer_smoke.py) for no-download base smoke
   checks.

## Route by user intent

| User asks for... | Use this route |
| --- | --- |
| "Find a subgroup with unusually high error or bias" | Use MDSS `bias_scan`; read [mdss-workflow.md](references/mdss-workflow.md). |
| "Score a known subgroup with MDSS inside classification metrics" | Use `MDSSClassificationMetric` via [datasets-and-metrics](../datasets-and-metrics/SKILL.md), then return here for scan interpretation if needed. |
| "Find subgroups that have worse recourse/counterfactual action costs" | Use optional FACTS; read [facts-workflow.md](references/facts-workflow.md). |
| "Explain what this metric means in text or JSON" | Use [explainer-reference.md](references/explainer-reference.md). |
| "Compute fairness metrics before scanning" | Route to [../datasets-and-metrics/SKILL.md](../datasets-and-metrics/SKILL.md) for legacy metrics or [../sklearn-interface/SKILL.md](../sklearn-interface/SKILL.md) for pandas metrics. |
| "Mitigate bias after detecting a problem" | Route to [../mitigation-algorithms/SKILL.md](../mitigation-algorithms/SKILL.md). |

## Detector/explainer distinction

- **MDSS detectors** search for subgroups whose observed outcomes differ from
  expectations under a scoring function.
- **FACTS** searches for subgroups with unequal counterfactual recourse cost or
  effectiveness; it is optional-extra gated.
- **Metric explainers** wrap an existing AIF360 metric object and render method
  outputs in human-readable text or structured JSON; they do not compute new
  metrics independently.

## Safe smoke checks

```bash
python sub-skills/detectors-and-explainers/scripts/mdss_smoke.py --json
python sub-skills/detectors-and-explainers/scripts/explainer_smoke.py --json
```

Both scripts use synthetic in-memory data and require only the base package
surface that was verified for this skill construction run.
