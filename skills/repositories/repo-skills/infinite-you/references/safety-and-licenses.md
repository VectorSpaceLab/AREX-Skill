# Safety and Licenses

## Purpose

Read this before downloading models, using identity images, exposing a demo, or publishing results. InfiniteYou is an identity-preserving image-generation system; responsible use and license boundaries are part of the operating workflow.

## Repository and model licenses

- The repository code is released under Apache License 2.0 in this snapshot.
- The released InfiniteYou model is described by the project as Creative Commons Attribution-NonCommercial 4.0 International for academic research purposes.
- The FLUX.1-dev base model has its own gated access and license terms.
- InsightFace face models and any optional LoRA files have their own upstream licenses.

Always apply the most restrictive relevant license across code, InfiniteYou weights, base model, face models, LoRAs, generated images, and deployment environment.

## Identity-image safety

- Use images from consented subjects or images the user is authorized to process.
- Avoid impersonation, deception, harassment, or privacy-invasive uses.
- If multiple faces are present, the pipeline selects the largest detected face; crop to the intended consenting subject before generation.
- Do not preserve or publish sensitive identity images longer than necessary for the task.

## Download and credential policy

- Do not automatically download gated or non-commercial-use models unless the user has approved the download and license/access constraints.
- Do not store Hugging Face tokens or other credentials in generated scripts, prompts, logs, or committed files.
- Prefer local model paths on shared systems when repeated downloads would waste bandwidth or risk leaking credentials.

## Demo exposure

- The local demo binds to localhost by default. Keep it local unless the user intentionally wants external access.
- When exposing a demo, consider authentication, logging, content moderation, rate limits, and who can upload identity images.
- Do not expose a server from a shared machine without confirming policy and port/bind choices.

## Output review

Before sharing generated images, confirm:

- The subject and intended use are authorized.
- The result does not imply endorsement, identity misuse, or deceptive context.
- Any required attribution or non-commercial restriction is followed.
- Optional LoRAs or base models used in the generation permit the intended use.
