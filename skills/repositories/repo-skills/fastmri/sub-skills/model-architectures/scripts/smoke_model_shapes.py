#!/usr/bin/env python
"""CPU-safe fastMRI model architecture smoke checks."""

import argparse
import json
import sys


def import_runtime():
    try:
        import torch
        import fastmri
        from fastmri.models import AdaptiveVarNet, NormUnet, Unet, VarNet
        from fastmri.models.policy import LOUPEPolicy
    except ModuleNotFoundError as error:
        missing_name = getattr(error, "name", None) or str(error)
        print(
            "Missing runtime dependency: "
            f"{missing_name}. Install fastmri with its PyTorch dependencies; "
            "if the missing module is requests, install requests because "
            "fastmri.data imports it in this checkout.",
            file=sys.stderr,
        )
        raise SystemExit(2) from error

    return {
        "torch": torch,
        "fastmri": fastmri,
        "AdaptiveVarNet": AdaptiveVarNet,
        "NormUnet": NormUnet,
        "Unet": Unet,
        "VarNet": VarNet,
        "LOUPEPolicy": LOUPEPolicy,
    }


def build_center_mask(torch_module, batch_size, width, num_low_frequencies, device):
    center = width // 2
    start = center - num_low_frequencies // 2
    stop = start + num_low_frequencies
    mask = torch_module.zeros(batch_size, 1, 1, width, 1, dtype=torch_module.bool, device=device)
    mask[..., start:stop, :] = True
    return mask


def random_kspace(torch_module, batch_size, num_coils, height, width, device):
    return torch_module.randn(batch_size, num_coils, height, width, 2, device=device)


def check_unet(runtime, args, device):
    torch_module = runtime["torch"]
    model_class = runtime["Unet"]
    model = model_class(
        in_chans=1,
        out_chans=1,
        chans=args.unet_chans,
        num_pool_layers=args.pools,
        drop_prob=0.0,
    ).to(device).eval()
    image = torch_module.zeros(args.batch_size, 1, args.height, args.width, device=device)
    with torch_module.no_grad():
        output = model(image)
    expected_shape = (args.batch_size, 1, args.height, args.width)
    assert tuple(output.shape) == expected_shape, tuple(output.shape)
    return {"output_shape": list(output.shape)}


def check_normunet(runtime, args, device):
    torch_module = runtime["torch"]
    model_class = runtime["NormUnet"]
    model = model_class(
        chans=args.varnet_chans,
        num_pools=args.pools,
        in_chans=2,
        out_chans=2,
        drop_prob=0.0,
    ).to(device).eval()
    complex_image = torch_module.randn(
        args.batch_size, 1, args.height, args.width, 2, device=device
    )
    with torch_module.no_grad():
        output = model(complex_image)
    assert tuple(output.shape) == tuple(complex_image.shape), tuple(output.shape)
    return {"output_shape": list(output.shape)}


def check_varnet(runtime, args, device):
    torch_module = runtime["torch"]
    model_class = runtime["VarNet"]
    model = model_class(
        num_cascades=args.cascades,
        sens_chans=args.sens_chans,
        sens_pools=args.pools,
        chans=args.varnet_chans,
        pools=args.pools,
        mask_center=True,
    ).to(device).eval()
    mask = build_center_mask(
        torch_module, args.batch_size, args.width, args.num_low_frequencies, device
    )
    kspace = random_kspace(
        torch_module, args.batch_size, args.coils, args.height, args.width, device
    )
    masked_kspace = kspace * mask
    with torch_module.no_grad():
        output = model(masked_kspace, mask, num_low_frequencies=args.num_low_frequencies)
    expected_shape = (args.batch_size, args.height, args.width)
    assert tuple(output.shape) == expected_shape, tuple(output.shape)
    return {"output_shape": list(output.shape), "mask_shape": list(mask.shape)}


def check_policy(runtime, args, device):
    torch_module = runtime["torch"]
    policy_class = runtime["LOUPEPolicy"]
    policy = policy_class(
        num_actions=args.width,
        budget=0,
        use_softplus=True,
        slope=10,
    ).to(device).eval()
    mask = build_center_mask(
        torch_module, args.batch_size, args.width, args.num_low_frequencies, device
    ).to(dtype=torch_module.float32)
    kspace = random_kspace(
        torch_module, args.batch_size, args.coils, args.height, args.width, device
    )
    with torch_module.no_grad():
        new_mask, masked_kspace, probability_mask = policy(mask, kspace)
    assert tuple(new_mask.shape) == tuple(mask.shape), tuple(new_mask.shape)
    assert tuple(masked_kspace.shape) == tuple(kspace.shape), tuple(masked_kspace.shape)
    assert tuple(probability_mask.shape) == tuple(mask.shape), tuple(probability_mask.shape)
    return {
        "mask_shape": list(new_mask.shape),
        "masked_kspace_shape": list(masked_kspace.shape),
        "probability_mask_shape": list(probability_mask.shape),
    }


def check_adaptive_varnet(runtime, args, device):
    torch_module = runtime["torch"]
    model_class = runtime["AdaptiveVarNet"]
    model = model_class(
        budget=0,
        num_cascades=1,
        sens_chans=args.sens_chans,
        sens_pools=args.pools,
        chans=args.varnet_chans,
        pools=args.pools,
        cascades_per_policy=1,
        loupe_mask=False,
        crop_size=(args.height, args.width),
        num_sense_lines=None,
        sparse_dc_gradients=False,
    ).to(device).eval()
    mask = build_center_mask(
        torch_module, args.batch_size, args.width, args.num_low_frequencies, device
    ).to(dtype=torch_module.float32)
    kspace = random_kspace(
        torch_module, args.batch_size, args.coils, args.height, args.width, device
    )
    masked_kspace = kspace * mask
    with torch_module.no_grad():
        output, extra_outputs = model(kspace, masked_kspace, mask)
    expected_shape = (args.batch_size, args.height, args.width)
    assert tuple(output.shape) == expected_shape, tuple(output.shape)
    return {
        "output_shape": list(output.shape),
        "extra_output_keys": sorted(extra_outputs.keys()),
    }


def selected_models(model_name):
    if model_name == "all":
        return ["unet", "normunet", "varnet", "policy", "adaptive"]
    return [model_name]


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run tiny fastMRI model architecture shape checks."
    )
    parser.add_argument(
        "--model",
        choices=("all", "unet", "normunet", "varnet", "policy", "adaptive"),
        default="all",
    )
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"))
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--coils", type=int, default=4)
    parser.add_argument("--height", type=int, default=32)
    parser.add_argument("--width", type=int, default=32)
    parser.add_argument("--pools", type=int, default=2)
    parser.add_argument("--cascades", type=int, default=2)
    parser.add_argument("--unet-chans", type=int, default=8)
    parser.add_argument("--varnet-chans", type=int, default=4)
    parser.add_argument("--sens-chans", type=int, default=4)
    parser.add_argument("--num-low-frequencies", type=int, default=4)
    parser.add_argument("--seed", type=int, default=0)
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    runtime = import_runtime()
    torch_module = runtime["torch"]

    if args.device == "cuda" and not torch_module.cuda.is_available():
        print("CUDA was requested but torch.cuda.is_available() is false.", file=sys.stderr)
        return 2

    if args.height < 2 ** args.pools or args.width < 2 ** args.pools:
        print("height and width must be large enough for the requested pooling depth.", file=sys.stderr)
        return 2

    if args.num_low_frequencies <= 0 or args.num_low_frequencies > args.width:
        print("num-low-frequencies must be in the range [1, width].", file=sys.stderr)
        return 2

    torch_module.manual_seed(args.seed)
    device = torch_module.device(args.device)
    checks = {
        "unet": check_unet,
        "normunet": check_normunet,
        "varnet": check_varnet,
        "policy": check_policy,
        "adaptive": check_adaptive_varnet,
    }
    summary = {
        "fastmri_version": getattr(runtime["fastmri"], "__version__", "unknown"),
        "device": str(device),
        "checks": {},
    }

    for model_name in selected_models(args.model):
        summary["checks"][model_name] = checks[model_name](runtime, args, device)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
