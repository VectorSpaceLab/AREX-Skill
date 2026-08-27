# ImageBind and StableUnCLIP Workflows

## Purpose

Read this when an InternGPT task asks to generate an image from audio, a thermal image, audio plus an image, or audio plus text. The guidance is self-contained and describes the tool contracts that a running InternGPT service expects; it does not require opening repository source files.

## Model relationship

`Anything2Image` is the foundation object. It loads a StableUnCLIP image-to-image diffusion pipeline configured for 512x512 generation and an ImageBind Huge embedding model. It enables CPU offload and VAE slicing for the diffusion pipeline; when energy-saving mode is active, the code moves the ImageBind model and diffusion pipeline onto the requested device only for the call and then offloads them afterward.

`Audio2Image`, `Thermal2Image`, `AudioImage2Image`, and `AudioText2Image` are template wrappers around that foundation object. In the app controller, template wrappers are created only when their required foundation object is already loaded. Loading an individual wrapper name without the foundation is not enough for the normal app startup path.

Practical load implication: for ImageBind generation, plan for `Anything2Image` to be present in the app load string; the wrapper tools are created from it by the controller.

## Tool contracts

| Tool | Natural trigger | Action input string | Internal modalities | Output behavior |
| --- | --- | --- | --- | --- |
| `Audio2Image` | "generate a real image from this audio" | One local audio path. | `AUDIO` embedding from a one-item audio path list. | Saves one 512x512 generated image using an `Audio2Image` suffix based on the audio filename and returns the new image path. |
| `Thermal2Image` | "generate a real image from a thermal image" | One local thermal-image path. | `THERMAL` embedding from a one-item image path list. | Saves one 512x512 generated image using a `Thermal2Image` suffix based on the thermal filename and returns the new image path. |
| `AudioImage2Image` | "generate a new image from above image and audio" | Exactly `image_path,audio_path`. Both sides are stripped after splitting. | `VISION` embedding for the image and `AUDIO` embedding for the audio; the embeddings are averaged. | Saves one 512x512 generated image using an `AudioImage2Image` suffix based on the audio filename and returns the new image path. |
| `AudioText2Image` | "generate a real image from this audio and a prompt" | `audio_path,prompt`. The first comma separates the audio path from the prompt; later commas remain part of the prompt. | `TEXT` embedding for the prompt and `AUDIO` embedding for the audio; the embeddings are mixed with equal weights. | Saves one 512x512 generated image using an `AudioText2Image` suffix based on the audio filename and returns the new image path. |

The wrappers pass only image embeddings to StableUnCLIP; prompt text is converted through ImageBind before generation rather than sent as a normal diffusion prompt.

## Modality preprocessing expectations

InternGPT uses ImageBind modality-specific preprocessing functions before calling the ImageBind model:

- Audio inputs are passed as a list of local audio paths and transformed for the `AUDIO` modality.
- Thermal inputs are passed as a list of local image paths and transformed for the `THERMAL` modality.
- Image inputs in audio+image workflows are passed as a list of local image paths and transformed for the `VISION` modality.
- Text prompts in audio+text workflows are passed as a one-item text list and transformed for the `TEXT` modality.

Sample assets used by the project demonstrate these practical formats: WAV for audio, JPEG/JPG for thermal and ordinary images, and MP4 for video fixtures. Thermal files are still image files; the thermal meaning comes from the model modality and data content, not from a distinct file extension.

Use the bundled validator from the sub-skill root to check local file existence, extension class, and comma grammar before attempting a heavy generation call:

```bash
python scripts/validate_multimodal_assets.py --audio ./sound.wav --image ./reference.jpg
python scripts/validate_multimodal_assets.py --tool AudioText2Image --tool-input "./sound.wav, a rainy city street"
python scripts/validate_multimodal_assets.py --tool AudioImage2Image --tool-input "./reference.jpg,./sound.wav"
```

Run the commands from this sub-skill directory, or provide the script path relative to your current working directory.

## App audio-tab behavior

In the Gradio app, the "Audio (with ImageBind)" tab accepts uploaded audio file paths. Uploading or selecting an audio example calls the controller's audio-upload path, which:

1. rejects a missing path with "No audio input. Please upload audio file";
2. clears non-persistent user state while preserving the agent and memory;
3. copies the audio into the app's working image/output area with an `audio` suffix;
4. stores the copied path as the current `audio_path`; and
5. adds a memory message telling the agent that the user provided an audio file and must use tools rather than imagine from the description.

After the upload, the user can send natural prompts such as:

- `generate a real image from this audio`
- `generate a real image from this audio and a quiet forest at night`
- `generate a new image from above image and audio` after an image has also been uploaded

## Native evidence and verification posture

The repository included CUDA-heavy native smoke intent for audio-to-image and thermal-to-image generation. Treat those as future full-runtime candidates only: they require model weights/downloads, CUDA, and enough VRAM, and they should not be used as lightweight construction checks. For static planning, prefer this reference plus the bundled validator.
