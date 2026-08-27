# FEDformer Model Overview

This subrepo bundles FEDformer together with the Autoformer, Informer, and Transformer baselines used in the same comparison scripts. Use this page when you need to decide which model branch or ablation knob to touch.

## Model family map

| Branch | Core blocks | Key flags | Best for | Notes |
| --- | --- | --- | --- | --- |
| FEDformer-Fourier | `FourierBlock`, `FourierCrossAttention` | `--version Fourier`, `--mode_select`, `--modes` | Frequency-mode selection experiments and Fourier ablations | `mode_select` matters here; the code clips `modes` to the available frequency span. |
| FEDformer-Wavelets | `MultiWaveletTransform`, `MultiWaveletCross` | `--version Wavelets`, `--L`, `--base`, `--cross_activation`, `--modes` | Multiresolution experiments and wavelet ablations | `L`, `base`, and `cross_activation` are the meaningful FEDformer-specific knobs here. |
| Autoformer | decomposition + autocorrelation encoder/decoder | `--model Autoformer` | Baseline comparison inside this subrepo | Uses the same entry point but ignores the FEDformer-only flags. |
| Informer | ProbSparse attention | `--model Informer` | Baseline comparison inside this subrepo | Useful when the task is “compare FEDformer with the Transformer baselines.” |
| Transformer | full attention encoder/decoder | `--model Transformer` | Vanilla baseline comparison | The simplest local baseline in this route. |

## Fourier branch details

- The Fourier path selects frequency bins with `mode_select=random` or `mode_select=low`.
- `random` shuffles the candidate bins before truncation.
- `low` keeps the lowest-frequency bins.
- `modes` is a cap, not a promise; the helper trims it to the available bins.
- The Fourier path is the right choice when the user asks about frequency mode selection, a `modes` sweep, or a direct Fourier comparison.
- `cross_activation` is not the main tuning knob for the Fourier branch in this fork.

## Wavelets branch details

- The Wavelets path uses the multiresolution decomposition blocks instead of the frequency-bin selection blocks.
- `L` controls how many lower levels are ignored.
- `base` selects the polynomial family used to build the filters.
- `cross_activation` chooses the nonlinear function used in the wavelet cross-attention helper.
- `modes` still matters because the cross-attention helper keeps only the first frequency bins it needs.
- The Wavelets path is the right choice when the user asks about `base`, `L`, or `cross_activation`.

## Embedding choices

`run.py` exposes `--embed_type`, which maps to the embedding modules in `FEDformer/layers/Embed.py`.

| `embed_type` | Embedding module | What it keeps | What it drops |
| --- | --- | --- | --- |
| `0` | `DataEmbedding_wo_pos` | value + time features | positional embedding |
| `1` | `DataEmbedding` | value + position + time features | nothing |
| `2` | `DataEmbedding_wo_pos_temp` | value only | position and time features |
| `3` | `DataEmbedding_wo_temp` | value + position | time features |

The parser default is `0`.

## Data and shape alignment

The FEDformer loaders expect the input shapes to line up with the dataset and the chosen `--features` mode.

- `M`: multivariate input and multivariate output.
- `S`: univariate input and univariate output.
- `MS`: multivariate input and single-target output.

When you change datasets, keep these values aligned:

- `--root_path`
- `--data_path`
- `--features`
- `--target`
- `--enc_in`
- `--dec_in`
- `--c_out`

## Comparison guidance

When the task is “compare FEDformer with Autoformer, Informer, or Transformer,” keep the dataset and horizon constant and change only the model family or the FEDformer-specific ablation knob.

Good comparison controls:

- same `data`
- same `root_path` and `data_path`
- same `seq_len`, `label_len`, and `pred_len`
- same `features` and channel counts
- same random seed and training schedule when possible

Compare the saved metrics under `results/<setting>/metrics.npy` and the visualized outputs under `test_results/<setting>/`.

## Route boundary reminder

The local transformer baselines in this subrepo are in scope here.
The repo-wide Linear, DLinear, and NLinear benchmark families are not; send those to the sibling long-forecasting route instead.
