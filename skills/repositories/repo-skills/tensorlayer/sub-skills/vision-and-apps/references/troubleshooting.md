# Troubleshooting

## Missing visualization dependencies

### `matplotlib` or `opencv-python` is missing

TensorLayer imports its app/vision stack during top-level import, so the vision route depends on both packages in practice. Install them before debugging image workflows.

## Pretrained-weight issues

### A constructor tries to download or load external weights

Use `pretrained=False` for bundled checks. The public tutorials that mention Baidu links, class-name files, or local model weights are reference-only unless those files are provided.

### Object-detection and pose examples fail on their input files

Those examples expect local images and model assets. Keep the smoke script on synthetic or constructor-only checks.

## Headless display issues

### `image.show()` or GUI calls fail on the host

Avoid interactive display in the skill helpers. Use array-shape checks or save images to disk instead of opening windows.

## Shape and input-size issues

### Forward passes fail because the input shape is wrong

Use a 224x224x3 synthetic tensor for the common image constructors. For YOLOv4, the source implementation expects 416x416 inputs.
