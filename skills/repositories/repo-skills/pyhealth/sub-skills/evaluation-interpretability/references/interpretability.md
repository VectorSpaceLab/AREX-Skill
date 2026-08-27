# Interpretability workflows

`pyhealth.interpret` exposes an API and methods including baseline, integrated
gradients, basic gradient, DeepLIFT, SHAP/LIME-related methods, attention
rollout, Chefer/GIM variants, and ensemble aggregation. The exact method needs
an appropriate model/input interface; read its constructor and method contract
before use.

A defensible explanation workflow:

1. freeze the model/checkpoint and document preprocessing;
2. select a target sample and output (class, label, or token target);
3. choose a baseline/reference consistent with the modality;
4. compute the explanation without changing model weights;
5. check shape, normalization, and aggregation back to patient/visit fields;
6. compare with a perturbation or sufficiency/comprehensiveness check when
   available; and
7. report that attribution is not causal or clinical evidence by itself.

Text, image, audio, and code explanations inherit processor/tokenization
semantics from [medical-code-text](../../medical-code-text/SKILL.md) and data
routes. Full examples may require trained models or large data; use a tiny
synthetic differentiable model for API checks.
