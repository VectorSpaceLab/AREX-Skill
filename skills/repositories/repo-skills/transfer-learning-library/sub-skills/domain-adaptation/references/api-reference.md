# Domain Adaptation API Reference

This reference maps the public TLLib APIs most useful when wiring domain-adaptation losses or explaining which module belongs to which adaptation family. Use it with `domain-adaptation-workflows.md` for benchmark-style recipes.

## Shared building blocks

| Need | Public API | Input / output contract | Notes |
| --- | --- | --- | --- |
| Binary domain discriminator | `tllib.modules.domain_discriminator.DomainDiscriminator(in_feature, hidden_size, batch_norm=True, sigmoid=True)` | `(N, F) -> (N, 1)` with sigmoid, or `(N, 2)` with `sigmoid=False`. | Used by DANN, CDAN, IWAN-style weights, and many custom adversarial loops. |
| Gradient reversal | `tllib.modules.grl.WarmStartGradientReverseLayer`, `tllib.modules.grl.GradientReverseLayer` | Returns the same tensor in forward; reverses/scales gradients in backward. | DANN/CDAN instantiate warm-start GRL internally unless you pass a custom one. MDD/OSBP wrappers expose explicit `step()` or `grad_reverse` behavior. |
| Kernels | `tllib.modules.kernels.GaussianKernel(sigma=None, track_running_stats=True, alpha=1.0)` | Kernel matrix over a batch of features. | Combine several kernels for MK-MMD/JMMD. Running-stat sigma estimation is useful for small synthetic checks and normal training. |
| Generic classifier | `tllib.modules.classifier.Classifier` / `ImageClassifier` | In train mode returns `(predictions, features)`; in eval returns predictions. | Backbones should expose `out_features`; route model factory choices to `../vision-data-models/SKILL.md`. |
| Generic regressor | `tllib.modules.regressor.Regressor` | In train mode returns `(predictions, features)`; in eval returns predictions. | Used by regression DA variants; labels are usually normalized by workflow code. |

## Core feature-alignment families

| Family | Key APIs | Inputs | Output and integration notes |
| --- | --- | --- | --- |
| DANN | `tllib.alignment.dann.DomainAdversarialLoss(domain_discriminator, reduction='mean', grl=None, sigmoid=True)` | Source and target features `f_s`, `f_t` shaped `(N, F)`; optional instance weights `w_s`, `w_t`. | Returns a scalar by default and records `domain_discriminator_accuracy`. Discriminator input dimension must match `F`. |
| ADDA | `tllib.alignment.adda.DomainAdversarialLoss()` | Domain discriminator probabilities and `domain_label='source'` or `'target'`. | Source loss pushes predictions to one; target loss pushes to zero. Use it in the ADDA two-stage pretrain/adapt loop. |
| CDAN | `tllib.alignment.cdan.ConditionalDomainAdversarialLoss(domain_discriminator, entropy_conditioning=False, randomized=False, num_classes=-1, features_dim=-1, randomized_dim=1024, reduction='mean', sigmoid=True)` plus `MultiLinearMap` / `RandomizedMultiLinearMap`. | Raw logits `g_s`, `g_t` shaped `(N, C)` and features `f_s`, `f_t` shaped `(N, F)`. | CDAN softmaxes logits internally before the multilinear map. With `randomized=False`, discriminator input is `F*C`; with `randomized=True`, it is `randomized_dim`. |
| DAN / MK-MMD | `tllib.alignment.dan.MultipleKernelMaximumMeanDiscrepancy(kernels, linear=False)` | Source and target activations with matching feature shape. | Use one or more `GaussianKernel` modules. Example recipes use matched mini-batch sizes. |
| JAN / JMMD | `tllib.alignment.jan.JointMultipleKernelMaximumMeanDiscrepancy(kernels, linear=True, thetas=None)` and optional `Theta(dim)` | Tuples of source layer activations and target layer activations. | `kernels` is a sequence per layer; `thetas` enables adversarial JAN-style transforms. |
| CORAL | `tllib.alignment.coral.CorrelationAlignmentLoss()` | Source and target features `(N, d)`. | Computes mean and covariance mismatch. Needs at least two examples per batch because covariance divides by `N-1`. |
| BSP | `tllib.alignment.bsp.BatchSpectralPenalizationLoss()` | Source and target features `(N, F)`. | Penalizes the largest singular value from each domain; commonly added to an adversarial DA objective. |

## Hypothesis-adversarial and classifier-discrepancy APIs

| Family | Key APIs | Inputs | Notes |
| --- | --- | --- | --- |
| MCD | `tllib.alignment.mcd.classifier_discrepancy`, `tllib.alignment.mcd.entropy`, `tllib.alignment.mcd.ImageClassifierHead` | Two classifier probability tensors `(N, C)` for discrepancy; a stack of probabilities for entropy. | Use two heads over the same features. Do not pass class indices to discrepancy helpers. |
| MDD classification | `tllib.alignment.mdd.ClassificationMarginDisparityDiscrepancy(margin=4, reduction='mean')`, `tllib.alignment.mdd.ImageClassifier` | Main and adversarial logits for source and target: `y_s`, `y_s_adv`, `y_t`, `y_t_adv`. | `ImageClassifier` returns `(outputs, outputs_adv)` in train mode; call `step()` after each training forward to update the warm-start GRL. |
| MDD regression / DD | `tllib.alignment.mdd.RegressionMarginDisparityDiscrepancy(margin=1, loss_function=F.l1_loss, reduction='mean')`, `tllib.alignment.mdd.ImageRegressor` | Main and adversarial regression outputs with the same shape. | Regression labels in the benchmark workflows are normalized to `[0, 1]`; keep that normalization explicit. |
| OSBP | `tllib.alignment.osbp.UnknownClassBinaryCrossEntropy(t=0.5)`, `tllib.alignment.osbp.ImageClassifier` | Classifier logits shaped `(N, C+1)` where the final column is the unknown class. | `ImageClassifier(...).forward(x, grad_reverse=True)` reverses gradients through the bottleneck during adversarial unknown-boundary training. |

## Partial DA, AFN, MCC, and RegDA APIs

| Need | Public API | Inputs / shape | Notes |
| --- | --- | --- | --- |
| PADA class weights | `tllib.reweight.pada.ClassWeightModule(temperature=0.1)` | Classifier logits `(N, C)` from target or unlabeled data. | Returns class weights `(C,)` normalized by their maximum. Pass class-index weights to source CE and source/target instance weights to adversarial loss. |
| PADA automatic updates | `tllib.reweight.pada.AutomaticUpdateClassWeightModule(update_steps, data_loader, classifier, num_classes, device, temperature=0.1, partial_classes_index=None)` | A loader yielding images and labels, plus a classifier. | `partial_classes_index` is for debugging; real partial DA should not assume target class membership is known. |
| IWAN instance weights | `tllib.reweight.iwan.ImportanceWeightModule(discriminator, partial_classes_index=None)` | Source features `(N, F)` passed through a domain discriminator. | `get_importance_weight(feature)` returns detached weights `(N, 1)` normalized by their mean. |
| AFN in DA workflows | `tllib.normalization.afn.AdaptiveFeatureNorm(delta)` and `tllib.normalization.afn.ImageClassifier` | Feature tensor `(N, F)`. | AFN increases feature norms stepwise; for non-DA normalization/fine-tuning questions route to `../task-generalization/SKILL.md`. |
| MCC in DA workflows | `tllib.self_training.mcc.MinimumClassConfusionLoss(temperature)` | Target logits `(N, C)`. | Often added as a target regularizer to DANN/CDAN-style loops. For standalone SSL use route to `../self-training/SKILL.md`. |
| RegDA keypoint pseudo labels | `tllib.alignment.regda.PseudoLabelGenerator2d(num_keypoints, height=64, width=64, sigma=2)` or `FastPseudoLabelGenerator2d(sigma=2)` | Predicted heatmaps `(B, K, H, W)`. | Produces ground-truth and ground-false heatmaps for keypoint adaptation. Legacy NumPy aliases may affect the slower documented generator. |
| RegDA disparity | `tllib.alignment.regda.RegressionDisparity(pseudo_label_generator, criterion)` | Main and adversarial heatmaps `(B, K, H, W)`, optional visibility weights, `mode='min'` or `'max'`. | Use a keypoint criterion such as `tllib.vision.models.keypoint_detection.loss.JointsKLLoss`. |
| RegDA model wrapper | `tllib.alignment.regda.PoseResNet2d(backbone, upsampling, feature_dim, num_keypoints, gl=None, finetune=True, num_head_layers=2)` | Image input to backbone; train mode returns `(outputs, outputs_adv)`. | Call `step()` after each training forward. Route keypoint model construction to `../vision-data-models/SKILL.md`. |

## D-adapt object-detection APIs

All D-adapt APIs require a Detectron2-compatible runtime and should be treated as optional-stack APIs.

- Proposal and feedback data: `tllib.alignment.d_adapt.proposal.Proposal`, `PersistentProposalList`, `ProposalDataset`, `ProposalMapper`, `ProposalGenerator`, `ExpandCrop`.
- Feedback loading and mapping: `tllib.alignment.d_adapt.feedback.load_feedbacks_into_dataset`, `get_detection_dataset_dicts`, `transform_feedbacks`, and `DatasetMapper`.
- Detectron2 registry classes: `tllib.alignment.d_adapt.modeling.meta_arch.DecoupledGeneralizedRCNN`, `DecoupledRetinaNet`; ROI heads such as `DecoupledRes5ROIHeads` and `DecoupledStandardROIHeads`; output layer `DecoupledFastRCNNOutputLayers`.
- The D-adapt models extend TLLib object-detection base meta-architectures and return foreground/background proposal outputs during inference.

See `object-detection-adaptation.md` for the workflow and dependency guardrails.

## Shape rules that prevent most failures

- Keep features 2-D for feature losses unless a wrapper explicitly pools spatial maps for you.
- Keep logits raw for CDAN, MDD, MCC, OSBP, CE, and target regularizers. Only use probabilities where the MCD helpers or a discriminator API says probabilities are expected.
- Match source and target feature dimensions exactly. For MK-MMD/JMMD/CORAL/BSP, also keep mini-batch sizes matched unless you have checked the implementation path.
- Make every adversarial discriminator input dimension explicit: `F` for DANN, `F*C` or `randomized_dim` for CDAN, proposal feature dimensions for D-adapt adaptors.
- For wrappers with warm-start GRL/GL layers (`mdd.ImageClassifier`, `mdd.ImageRegressor`, `regda.PoseResNet2d`), call `step()` after each training forward.
