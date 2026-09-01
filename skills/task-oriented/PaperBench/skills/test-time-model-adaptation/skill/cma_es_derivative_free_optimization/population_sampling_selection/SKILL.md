---
name: population_sampling_selection
description: Sample and select CMA-ES Gaussian offspring for derivative-free black-box optimization recovery.
---

# Gaussian Population Sampling and Selection

Use this skill when implementing the CMA-ES generation loop: draw normalized Gaussian vectors, transform them with the covariance eigensystem, evaluate a black-box objective, sort by fitness, and compute the weighted selected step.

## Inputs
- Mean vector, step-size, covariance matrix, strategy parameters, objective callable, and random generator.

## Outputs
- Sorted offspring records, weighted normalized step, new mean, selected y vectors, selected z vectors, and best fitness.

## Workflow
1. Symmetrize and factorize the covariance matrix.
2. Draw `lambda` standard normal vectors and transform them into covariance-shaped steps.
3. Evaluate only objective values; do not use gradients or objective internals.
4. Rank offspring by fitness and compute weighted recombination over the top `mu` parents.

## Validation
Run the tests with the Distiller skill-tree validator. The tests use seeded random numbers and a sphere objective.

## Limitations
This skill performs one generation only; path and covariance adaptation are delegated to the adaptation skill.
