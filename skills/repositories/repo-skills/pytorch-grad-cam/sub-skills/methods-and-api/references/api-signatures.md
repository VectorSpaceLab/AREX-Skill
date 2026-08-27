# Installed API Signatures

The following signatures were inspected from the installed `grad-cam==1.5.5`
package during generation.

```text
GradCAM(model, target_layers, reshape_transform=None)
ScoreCAM(model, target_layers, reshape_transform=None)
GradCAMPlusPlus(model, target_layers, reshape_transform=None)
AblationCAM(model, target_layers, reshape_transform=None, ablation_layer=AblationLayer(), batch_size=32, ratio_channels_to_ablate=1.0)
XGradCAM(model, target_layers, reshape_transform=None)
EigenCAM(model, target_layers, reshape_transform=None)
EigenGradCAM(model, target_layers, reshape_transform=None)
LayerCAM(model, target_layers, reshape_transform=None)
FullGrad(model, target_layers, reshape_transform=None)
GradCAMElementWise(model, target_layers, reshape_transform=None)
KPCA_CAM(model, target_layers, reshape_transform=None, kernel='sigmoid', gamma=None)
ShapleyCAM(model, target_layers, reshape_transform=None)
FinerCAM(model, target_layers, reshape_transform=None, base_method=GradCAM)
SegEigenCAM(model, target_layers, reshape_transform=None)
GuidedBackpropReLUModel(model, device=None)
RefineCAM(model, target_layers, reshape_transform=None, base_method=GradCAMPlusPlus, **kwargs)
ClassifierOutputTarget(category)
ClassifierOutputSoftmaxTarget(category)
ClassifierOutputReST(category)
FasterRCNNBoxScoreTarget(labels, bounding_boxes, iou_threshold=0.5)
SemanticSegmentationTarget(category, mask)
FinerWeightedTarget(main_category, comparison_categories, alpha)
DeepFeatureFactorization(model, target_layer, reshape_transform=None, computation_on_concepts=None)
run_dff_on_image(model, target_layer, classifier, img_pil, img_tensor, reshape_transform, n_components=5, top_k=2)
```

## Notes

- `BaseCAM` stores `model`, `target_layers`, `device`, `outputs`,
  `compute_input_gradient`, `uses_gradients`, `tta_transforms`, `detach`, and
  an `activations_and_grads` hook manager.
- `BaseCAM.__call__(input_tensor, targets, aug_smooth=False, eigen_smooth=False)`
  dispatches to normal forward or augmentation smoothing.
- `RefineCAM` accepts extra kwargs passed to the chosen `base_method`.
- `FinerCAM` delegates most behavior to an internal base CAM instance and adds
  a context-manager-friendly teardown.
