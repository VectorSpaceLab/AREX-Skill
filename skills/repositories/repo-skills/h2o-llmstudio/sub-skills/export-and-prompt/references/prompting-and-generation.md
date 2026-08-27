# Prompting and generation

## Prompt session contract

Use the saved experiment directory with the prompt CLI:

```bash
python llm_studio/prompt.py -e <experiment-dir> -d cuda:0
```

The prompt session reads two core artifacts from the experiment directory:

- `cfg.yaml`
- `checkpoint.pth`

At startup the prompt flow:

- loads the saved configuration,
- forces training to zero epochs,
- pins the requested device and local rank,
- disables gradient checkpointing,
- treats the backbone as non-pretrained for inference setup,
- applies the saved prediction settings to the model's generation config,
- loads the trained checkpoint,
- then enters an interactive chat loop.

Prompting is session-local. The command-line session does not rewrite the saved
experiment configuration.

## Live parameter changes

Inside the prompt loop, a line that starts with `--` is treated as one or more
`name value` pairs. The parser updates the in-memory prediction settings and
rebuilds the generation config immediately.

Example:

```text
--num_beams 4 --top_k 30
```

The values are cast from the current field type, so use exact field names and
simple primitive values.

Common generation fields you can tune at prompt time:

| Field | Effect |
| --- | --- |
| `min_length_inference` | Minimum number of new tokens |
| `max_length_inference` | Maximum number of new tokens |
| `max_time` | Time cap; `0` disables the limit |
| `do_sample` | Enables stochastic generation |
| `num_beams` | Beam-search width |
| `temperature` | Sampling temperature when sampling is enabled |
| `repetition_penalty` | Penalizes repeated tokens |
| `top_k` | Top-k sampling cutoff when sampling is enabled |
| `top_p` | Top-p sampling cutoff when sampling is enabled |

If sampling is off, temperature, top-k, and top-p are cleared from the active
generation config.

## Prompt formatting

The prompt text is still interpreted with the experiment's dataset rules. The
loaded tokenizer and dataset helpers are responsible for prompt parsing,
message cleanup, and the final text the model sees.

Keep the runtime working directory able to resolve the bundled prompt templates
used by configuration loading. If those templates are missing, prompt setup can
fail before the model is loaded.

## Preflight checklist

Before running the prompt CLI, verify:

- the experiment directory exists,
- `cfg.yaml` is readable,
- `checkpoint.pth` is present,
- the selected device is valid for the current hardware,
- the prompt template directory is available in the runtime location.

For generation-style experiments, this is the normal path for chatting with the
trained model. For non-generation problem types, prompt-style output may not be
a good fit even if the files load.

## h2oGPT handoff

After exporting or downloading the model, h2oGPT can load it from either a
Hugging Face repo id or an extracted local folder:

```bash
python generate.py --base_model=<repo-id-or-extracted-folder>
```

If the model arrived as a zip archive, extract the archive first. Use the same
prompt format that the experiment used during training, because the model's
chat behavior depends on that formatting.