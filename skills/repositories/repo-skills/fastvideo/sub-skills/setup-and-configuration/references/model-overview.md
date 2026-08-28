# Model and backend overview

FastVideo resolves registered Hugging Face IDs through its registry and chooses
model-family pipeline and sampling defaults. Families include Wan, Hunyuan and
HunyuanVideo 1.5, LTX-2, LongCat, Cosmos, Kandinsky 5, LingBot, Matrix-Game,
GEN3C, GameCraft, DreamX-World, MiniMax H3, Stable Audio, MMAudio, Flux,
Stable Diffusion 3.5, Z-Image, and TurboDiffusion.

Use the exact registered ID from current package metadata or the user's model
card. Treat a model absent from the registry as requiring an explicit pipeline
configuration or conversion. A model being registered does not prove that its
remote files are public, that it fits available VRAM, or that every optimization
supports it.

Important distinctions:

- T2V generates video from text; I2V conditions on an image; T2I/I2I are image
  workloads; V2A/T2A produce audio for supported families.
- TurboDiffusion uses an RCM scheduler, one to four steps, SLA attention, and
  guidance scale 1.0.
- Matrix-Game uses image-to-video control inputs such as keyboard/mouse tensors.
- LongCat supports text/image/video-control/refinement variants; refinement
  changes output geometry and has separate conditioning inputs.
- LTX-2 is multimodal and may return audio plus video; continuation state is a
  separate typed envelope.
- Stable Audio and MiniMax H3 have audio-specific output or muxing behavior.

For support decisions, inspect the selected preset and workload first, then
check the attention/quantization compatibility table in
[inference optimizations](../../inference/references/optimizations.md).
