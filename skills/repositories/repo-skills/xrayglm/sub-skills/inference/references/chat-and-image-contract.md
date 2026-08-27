# Chat and image contract

The operating contract below is derived from the checked-in chat helper and
its callers. It is useful when writing a Researcher wrapper or diagnosing a
conversation that appears to ignore an image.

## Public signatures

The verified callable signature is:

```text
chat(image_path, model, tokenizer, query, history=None, image=None,
     max_length=1024, top_p=0.7, top_k=30, temperature=0.95,
     repetition_penalty=1.2, invalid_slices=[], english=False)
```

`image_path` is a local path or URL for a new image, or `None` when the caller
passes a processed `image` tensor. `query` is the current user turn.
`history` is a list of `(old_query, response)` pairs; a falsey history is
replaced with an empty list. The return is `(response, new_history,
processed_image)`. Keep the returned image for later turns if the same study
is intended, and clear it when changing studies.

The helper also exposes:

```text
process_image(text, image=None)
BlipImageEvalProcessor(image_size=384, mean=None, std=None)
```

The actual chat path constructs the image processor with size `224`, despite
the processor's verified default constructor size of `384`. This distinction is
important when reproducing preprocessing: use the runtime chat behavior for
model-compatible inference, and do not assume the public constructor default
is what chat uses.

## Prompt serialization

The helper inserts an image marker at the beginning of every prompt:

```text
<img>IMAGE_REFERENCE</img>
```

For a new image, `IMAGE_REFERENCE` is the entered path or URL. For a cached
image, the marker is empty and the tensor is supplied separately. Chinese
history is appended as:

```text
<img>path-or-empty</img>问：旧问题
答：旧回答
问：当前问题
答：
```

English history is appended as:

```text
<img>path-or-empty</img>Q:old question
A:old answer
Q:current question
A:
```

The final separator is the generation boundary. Keep the exact tags and
separators when implementing an adapter; ordinary prose such as a pasted file
path is not equivalent to the `<img>...</img>` marker. The helper uses the
last `<img>...</img>` match and removes the reference from the text before
tokenization. Do not provide both a non-empty image path tag and an `image`
object: the contract asserts that these are mutually exclusive.

## Local images and URLs

A local reference is opened with PIL. A reference beginning with `http` is
retrieved with `requests` and a 10-second timeout, then decoded from response
bytes with PIL. This accepts HTTP as well as HTTPS, so callers should enforce
HTTPS or an allowlist when handling untrusted input. The helper does not
provide a robust response-size limit, MIME allowlist, redirect policy, or
SSRF protection. Do not pass arbitrary user-controlled URLs to a privileged
host; prefetch through a constrained service if needed.

Before a model call, validate that a local file is readable and is an actual
image, and bound its dimensions/file size in the calling application. Use
`Image.open(...).convert('RGB')`; malformed, truncated, palette, grayscale,
or alpha images should be normalized deliberately rather than allowed to
produce ambiguous errors. Never log the full URL if it may contain secrets.

The WebUI's Gradio image component uses `type="filepath"`; its callback then
opens that path with PIL. It does not accept a URL directly in the image
widget. The CLI is the route for a URL reference, subject to network policy.

## Preprocessing and cache behavior

A PIL image is converted to RGB, resized to a square, converted to a tensor,
and normalized using the BLIP-2 means `(0.48145466, 0.4578275, 0.40821073)` and
standard deviations `(0.26862954, 0.26130258, 0.27577711)`. Chat uses a 224
pixel square and adds a batch dimension. The processed tensor is moved to the
model parameter dtype and device before generation. The visual model replaces
an image placeholder span with learned image embeddings; its configured image
length is normally 32.

After the first CLI call, the path is set to `None` and the returned processed
image is passed back. This is an in-memory reuse of the image tensor, not a
persistent or encrypted cache. `clear` resets it. WebUI history is displayed
as pairs and image upload/clear resets the visible seed, but callers should
still explicitly clear state when a patient or study changes.

A URL may be fetched again if a caller starts a new chat with that URL. A
previous tensor can keep sensitive pixels alive in process memory. The image
may also appear in OS/Python temporary storage or logs outside this route;
apply the host's data-retention policy.

## Language transitions

The model supports Chinese and English branches, but language selection changes
prompt separators and decoding cleanup. A safe transition is: save the
necessary non-sensitive summary, type `clear`, terminate the current loop, and
relaunch with `--english` (or without it). Do not mix Chinese `问：/答：` and
English `Q:/A:` history unless an experiment explicitly tests that behavior.
For a Chinese-to-English experiment with a URL, fetch/validate the URL under
network policy, begin a fresh English session, then record that the image was
reused only if the same processed tensor was intentionally retained.

## Failure interpretation

A successfully parsed `<img>` tag or a successful PIL decode proves only input
parsing. It does not prove that the checkpoint, tokenizer, CUDA kernels,
visual encoder, or generation strategy is ready. Diagnose model readiness
separately before attributing a bad answer to prompt formatting.
