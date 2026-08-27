#!/usr/bin/env python
"""Safe CPU smoke checks for conditioning wrappers.

This helper validates tiny upsampler, vocoder, and autoencoder paths with local
fixtures only. It avoids downloads, checkpoints, and optional external encoder
packages.
"""

import argparse
import json


def build_parser():
    parser = argparse.ArgumentParser(
        description="Run tiny CPU smoke checks for conditioning wrappers."
    )
    parser.add_argument(
        "--skip-vocoder",
        action="store_true",
        help="Skip the vocoder check.",
    )
    return parser


def load_runtime_modules():
    """Import the installed package from the active Python environment."""
    import torch
    from audio_diffusion_pytorch import (
        DiffusionAE,
        DiffusionUpsampler,
        DiffusionVocoder,
        UNetV0,
        VDiffusion,
        VSampler,
    )
    from audio_diffusion_pytorch.models import AdapterBase, EncoderBase

    return (
        torch,
        DiffusionAE,
        DiffusionUpsampler,
        DiffusionVocoder,
        UNetV0,
        VDiffusion,
        VSampler,
        AdapterBase,
        EncoderBase,
    )


def make_generator(torch, seed):
    generator = torch.Generator()
    generator.manual_seed(seed)
    return generator


def run_smoke(args):
    (
        torch,
        DiffusionAE,
        DiffusionUpsampler,
        DiffusionVocoder,
        UNetV0,
        VDiffusion,
        VSampler,
        AdapterBase,
        EncoderBase,
    ) = load_runtime_modules()

    torch.manual_seed(0)

    class TinyEncoder(EncoderBase):
        def __init__(self):
            super(TinyEncoder, self).__init__()
            self.out_channels = 2
            self.downsample_factor = 2

        def forward(self, x, with_info=False):
            latent = torch.cat([x[..., ::2], x[..., 1::2]], dim=1)
            info = {
                "input_shape": list(x.shape),
                "latent_shape": list(latent.shape),
                "downsample_factor": self.downsample_factor,
            }
            return (latent, info) if with_info else latent

    class IdentityAdapter(AdapterBase):
        def encode(self, x):
            return x

        def decode(self, x):
            return x

    wrapper_channels = [4, 4]
    model_kwargs = dict(
        net_t=UNetV0,
        factors=[1, 2],
        items=[1, 1],
        attentions=[0, 0],
        resnet_groups=1,
        diffusion_t=VDiffusion,
        sampler_t=VSampler,
    )

    results = {
        "status": "ok",
        "device": "cpu",
        "seed": 0,
    }

    with torch.no_grad():
        wave = torch.randn(1, 1, 16)

        upsampler = DiffusionUpsampler(
            in_channels=1,
            upsample_factor=2,
            channels=wrapper_channels,
            **model_kwargs
        )
        upsampler.eval()
        up_loss = upsampler(wave)
        up_sample = upsampler.sample(
            torch.randn(1, 1, 8),
            num_steps=2,
            generator=make_generator(torch, 11),
        )
        results["upsampler"] = {
            "loss_ndim": int(up_loss.ndim),
            "input_shape": list(wave.shape),
            "sample_input_shape": [1, 1, 8],
            "sample_shape": list(up_sample.shape),
            "upsample_factor": 2,
        }

        if args.skip_vocoder:
            results["vocoder"] = {"skipped": True}
        else:
            vocoder = DiffusionVocoder(
                mel_channels=2,
                mel_n_fft=8,
                mel_hop_length=2,
                mel_win_length=8,
                mel_sample_rate=16000,
                channels=wrapper_channels,
                **model_kwargs
            )
            vocoder.eval()
            voc_loss = vocoder(wave)
            mel = torch.randn(1, 1, 2, 8)
            voc_sample = vocoder.sample(
                mel,
                num_steps=2,
                generator=make_generator(torch, 12),
            )
            results["vocoder"] = {
                "loss_ndim": int(voc_loss.ndim),
                "wave_shape": list(wave.shape),
                "mel_shape": list(mel.shape),
                "sample_shape": list(voc_sample.shape),
                "mel_sample_rate": 16000,
            }

        autoencoder = DiffusionAE(
            in_channels=1,
            channels=wrapper_channels,
            encoder=TinyEncoder(),
            inject_depth=1,
            latent_factor=2,
            adapter=IdentityAdapter(),
            **model_kwargs
        )
        autoencoder.eval()
        ae_loss, ae_info = autoencoder(wave, with_info=True)
        latent = autoencoder.encode(wave)
        decoded = autoencoder.decode(
            latent,
            num_steps=2,
            generator=make_generator(torch, 13),
        )
        results["autoencoder"] = {
            "loss_ndim": int(ae_loss.ndim),
            "wave_shape": list(wave.shape),
            "latent_shape": list(latent.shape),
            "decoded_shape": list(decoded.shape),
            "info": ae_info,
            "inject_depth": 1,
            "latent_factor": 2,
            "adapter": "identity",
        }

    return results


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        results = run_smoke(args)
    except Exception as exc:  # pragma: no cover - defensive smoke output
        print(
            json.dumps(
                {
                    "status": "error",
                    "error_type": exc.__class__.__name__,
                    "error": str(exc),
                },
                sort_keys=True,
            )
        )
        return 1

    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
