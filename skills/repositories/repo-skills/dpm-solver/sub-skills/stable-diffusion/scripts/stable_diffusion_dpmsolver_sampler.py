#!/usr/bin/env python3
"""Stable Diffusion DPMSolverSampler adapter template.

Copy this file next to a copied `dpm_solver_pytorch.py` in a latent-diffusion
project that already provides a compatible model object. This template does not
load checkpoints, tokenizers, safety checkers, or images.
"""

from __future__ import annotations

import importlib.util
import pathlib

import torch


def _load_solver_module():
    root_scripts = pathlib.Path(__file__).resolve().parents[3] / "scripts"
    path = root_scripts / "dpm_solver_pytorch.py"
    spec = importlib.util.spec_from_file_location("skill_dpm_solver_pytorch", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import bundled solver from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_solver = _load_solver_module()
DPM_Solver = _solver.DPM_Solver
NoiseScheduleVP = _solver.NoiseScheduleVP
model_wrapper = _solver.model_wrapper


class DPMSolverSampler:
    """DPM-Solver++ sampler adapter for classic latent-diffusion model objects."""

    def __init__(self, model):
        self.model = model
        to_torch = lambda x: x.clone().detach().to(torch.float32).to(model.device)
        self.alphas_cumprod = to_torch(model.alphas_cumprod)
        self.noise_schedule = NoiseScheduleVP("discrete", alphas_cumprod=self.alphas_cumprod)

    @torch.no_grad()
    def sample(
        self,
        S,
        batch_size,
        shape,
        conditioning=None,
        unconditional_guidance_scale=1.0,
        unconditional_conditioning=None,
        skip_type="time_uniform",
        method="multistep",
        order=2,
        lower_order_final=True,
        correcting_xt_fn=None,
        t_start=None,
        t_end=None,
        x_T=None,
        **kwargs,
    ):
        """Sample latents with DPM-Solver++ and classifier-free guidance."""
        if conditioning is not None:
            if isinstance(conditioning, dict):
                first = conditioning[list(conditioning.keys())[0]]
                cbs = first.shape[0]
            else:
                cbs = conditioning.shape[0]
            if cbs != batch_size:
                print(f"Warning: got {cbs} conditionings but batch-size is {batch_size}")

        C, H, W = shape
        size = (batch_size, C, H, W)
        device = self.model.betas.device if hasattr(self.model, "betas") else self.model.device
        img = torch.randn(size, device=device) if x_T is None else x_T

        model_fn = model_wrapper(
            lambda x, t, c: self.model.apply_model(x, t, c),
            self.noise_schedule,
            model_type="noise",
            guidance_type="classifier-free",
            condition=conditioning,
            unconditional_condition=unconditional_conditioning,
            guidance_scale=unconditional_guidance_scale,
        )
        solver = DPM_Solver(
            model_fn,
            self.noise_schedule,
            algorithm_type="dpmsolver++",
            correcting_xt_fn=correcting_xt_fn,
        )
        x, intermediates = solver.sample(
            img,
            t_start=t_start,
            t_end=t_end,
            steps=S,
            skip_type=skip_type,
            method=method,
            order=order,
            lower_order_final=lower_order_final,
            return_intermediate=True,
        )
        return x.to(device), intermediates

    @torch.no_grad()
    def stochastic_encode(self, x0, encode_ratio, noise=None):
        t_end = torch.tensor([self.ratio_to_time(encode_ratio)], device=x0.device, dtype=x0.dtype)
        return DPM_Solver(lambda x, t: torch.zeros_like(x), self.noise_schedule).add_noise(x0, t_end, noise=noise)

    @torch.no_grad()
    def encode(
        self,
        S,
        x,
        encode_ratio,
        conditioning=None,
        unconditional_guidance_scale=1.0,
        unconditional_conditioning=None,
        skip_type="time_uniform",
        method="multistep",
        order=2,
        lower_order_final=False,
        **kwargs,
    ):
        model_fn = model_wrapper(
            lambda x_in, t, c: self.model.apply_model(x_in, t, c),
            self.noise_schedule,
            model_type="noise",
            guidance_type="classifier-free",
            condition=conditioning,
            unconditional_condition=unconditional_conditioning,
            guidance_scale=unconditional_guidance_scale,
        )
        t_end = self.ratio_to_time(encode_ratio)
        solver = DPM_Solver(model_fn, self.noise_schedule, algorithm_type="dpmsolver++")
        return solver.inverse(
            x,
            steps=S,
            t_end=t_end,
            skip_type=skip_type,
            method=method,
            order=order,
            lower_order_final=lower_order_final,
            return_intermediate=True,
        )

    def time_discrete_to_continuous(self, t_discrete):
        return (t_discrete + 1.0) / self.noise_schedule.total_N

    def time_continuous_to_discrete(self, t_continuous):
        return t_continuous * self.noise_schedule.total_N - 1.0

    def ratio_to_time(self, ratio):
        return (1.0 - 1.0 / self.noise_schedule.total_N) * ratio + 1.0 / self.noise_schedule.total_N

    def time_to_ratio(self, t_continuous):
        """Inverse of ratio_to_time; corrected from the source adapter typo."""
        return (t_continuous - 1.0 / self.noise_schedule.total_N) / (1.0 - 1.0 / self.noise_schedule.total_N)
