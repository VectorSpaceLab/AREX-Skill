# Optional PaddleHub and Gradio Demo

The repository includes a `gradio/demo.py` example that:

- imports OpenCV, PaddleHub, Gradio, and PyTorch;
- downloads two sample images from the network;
- loads `hub.Module(name='U2Net')`;
- launches a Gradio interface that returns foreground and mask outputs.

This demo is not part of the generated skill's minimum core workflow because it requires optional PaddlePaddle/PaddleHub dependencies, network/model-hub access, and a web server launch.

Use this reference only when the user explicitly asks about the web demo or PaddleHub route. For ordinary PyTorch U-2-Net saliency, human segmentation, portrait generation, or training tasks, route to the relevant sub-skill instead.

Before running an equivalent demo, ask for approval for:

1. installing PaddlePaddle/PaddleHub/Gradio if missing;
2. downloading sample images or hub models;
3. launching a local web server.
