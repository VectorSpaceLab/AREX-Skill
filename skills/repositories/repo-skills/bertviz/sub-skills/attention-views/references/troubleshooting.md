# Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError: 'tokens' is required` | Self-attention was called without a token list. | Pass the token strings that match the attention sequence length. |
| Self-attention arguments conflict with encoder-decoder arguments | Mixed modes were passed to the same call. | Choose one mode: either `attention`+`tokens` or the encoder/decoder blocks. |
| `Attention has N positions, while number of tokens is M` | Tokenization and attention tensors do not match. | Align the tokens with the model output, including special tokens and sentence-pair splits. |
| `Layer X is not in include_layers` | The requested default layer was filtered out. | Add the layer to `include_layers` or choose a different `layer`. |
| `html_action parameter must be 'view' or 'return'` | Invalid `html_action` value. | Use exactly `view` or `return`. |
| `The attention tensor does not have the correct number of dimensions... output_attentions=True` | The model did not return Hugging Face-style attention tensors. | Reload the model with `output_attentions=True` and pass the attention tuple/list directly. |
| No interactive rendering in Jupyter/Colab | Notebook prerequisites are missing or `require.js` is unavailable. | Install JupyterLab/ipywidgets for interactive use, or switch to `html_action='return'` and save the HTML. |
| `head_view` does not seem to filter heads | `head_view` only preselects heads; it does not have `include_heads`. | Use `model_view` for head filtering, or pre-slice the tensors before calling `head_view`. |
| Saved HTML is slow or huge | Too many layers, heads, or input tokens are being rendered. | Shorten the input and use `include_layers`/`include_heads` to narrow the view. |
| Encoder-decoder render fails with missing token lists | Attention blocks were supplied without matching encoder/decoder tokens. | Pass both `encoder_tokens` and `decoder_tokens`, and make sure their lengths match the attention dimensions. |
| HTML export fails because JS assets were copied or edited | BertViz should read its bundled `head_view.js` and `model_view.js` from the installed package. | Do not vendor the JS assets into the skill; rely on the installed BertViz package data. |

## Quick checks

- Verify the attention list contains one 4D tensor per layer.
- Verify the last two dimensions match the token lengths after any sentence split.
- Verify `sentence_b_start` points at the first token in sentence B.
- For `model_view`, verify `include_layers` and `include_heads` are zero-indexed lists.
- For saved HTML, always use `html_action='return'` and write the returned `.data`.
