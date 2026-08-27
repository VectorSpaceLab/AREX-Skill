# Extension Notes

## Gradio

Use Gradio only when the user wants a UI. It is an optional wrapper around the same visual generation flow.

## Tool Inference

Tool inference is a text-only extension and should be routed to the inference skill, not to the multimodal skill.

## Long-Context Templates

If the request is really about choosing a chat template for a model family, route it back to the generic template skill unless the prompt itself needs image tokens.
