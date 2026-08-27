# Datasets, losses, and metrics

## Dataset loaders exposed by `asteroid.data`

Asteroid exposes dataset classes for several speech, music, and audio-visual corpora.

| Dataset class | Typical task | Notes |
| --- | --- | --- |
| `WhamDataset` | speech separation / enhancement | WHAM tasks: `enh_single`, `enh_both`, `sep_clean`, `sep_noisy` |
| `WhamRDataset` | reverberant speech separation | WHAMR recipe family |
| `LibriMix` | speech separation / enhancement | Supports clean and noisy separation variants |
| `Wsj0mixDataset` | speech separation | Classic WSJ0-mix recipe surface |
| `DNSDataset` | speech enhancement | Deep Noise Suppression challenge data |
| `MUSDB18Dataset` | music source separation | Often paired with music models and X-UMX-style recipes |
| `FUSSDataset` | arbitrary sound separation | Foreground/background manifest format |
| `AVSpeechDataset` | audio-visual separation | Uses video embeddings and `librosa` at import time |
| `SmsWsjDataset` | multichannel separation | May require `sms_wsj` and `lazy_dataset` helpers |
| `KinectWsjMixDataset` | multichannel separation | Uses Kinect-WSJ data layout |
| `DAMPVSEPSinglesDataset` | vocal separation | Uses `librosa` for loading |
| `LibriVADDataset` | voice activity detection | Returns waveform and label pairs |

## Loss helpers used by recipes

### PIT / MixIT / SinkPIT

- `PITLossWrapper`
- `MixITLossWrapper`
- `SinkPITLossWrapper`
- `SinkPITBetaScheduler`

### Separation and enhancement losses

- `pairwise_neg_sisdr`, `pairwise_neg_sdsdr`, `pairwise_neg_snr`
- `singlesrc_neg_sisdr`, `singlesrc_neg_sdsdr`, `singlesrc_neg_snr`
- `multisrc_neg_sisdr`, `multisrc_neg_sdsdr`, `multisrc_neg_snr`
- `pairwise_mse`, `singlesrc_mse`, `multisrc_mse`
- `SingleSrcPMSQE`
- `SingleSrcNegSTOI`
- `SingleSrcMultiScaleSpectral`
- `deep_clustering_loss`

## Metrics and evaluation

- `get_metrics(...)` computes SI-SDR, SDR, SIR, SAR, STOI, and PESQ-style metrics.
- `MetricTracker` stores utterance-level metrics and produces summary reports.

## External dependency reminders

- `pb_bss_eval` powers the main metric helper.
- `torch_stoi` is needed for STOI-style losses/metrics.
- `librosa` is needed for several dataset imports and audio fallbacks.
- Some recipe families require optional external helpers such as `espnet_model_zoo`, `jiwer`, `sms_wsj`, or `lazy_dataset`.

## Good smoke cases

- `tests/losses/pit_wrapper_test.py`
- `tests/losses/loss_functions_test.py`
- `tests/losses/sinkpit_wrapper_test.py`
- `tests/metrics_test.py`
- `tests/engine/system_test.py`
