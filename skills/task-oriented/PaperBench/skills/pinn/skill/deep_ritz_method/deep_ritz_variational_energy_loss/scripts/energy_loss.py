import math


def poisson_10d_exact_python(point):
    total = 0.0
    for index in range(0, min(10, len(point)), 2):
        if index + 1 < len(point):
            total += point[index] * point[index + 1]
    return total


def relative_l2_python(predictions, targets):
    numerator = sum((prediction - target) ** 2 for prediction, target in zip(predictions, targets))
    denominator = sum(target ** 2 for target in targets)
    if denominator == 0.0:
        return math.inf
    return math.sqrt(numerator / denominator)


def poisson_energy_loss_torch(model, interior, boundary, beta=1000.0, exact_boundary_fn=None, forcing_fn=None):
    import torch
    interior = interior.detach().clone().requires_grad_(True)
    interior_values = model(interior)
    gradients = torch.autograd.grad(interior_values.sum(), interior, create_graph=True)[0]
    forcing = torch.zeros_like(interior_values) if forcing_fn is None else forcing_fn(interior).reshape_as(interior_values)
    interior_energy = (0.5 * gradients.pow(2).sum(dim=1, keepdim=True) - forcing * interior_values).mean()
    boundary_values = model(boundary)
    if exact_boundary_fn is None:
        target = torch.zeros_like(boundary_values)
    else:
        target = exact_boundary_fn(boundary).reshape_as(boundary_values)
    boundary_penalty = ((boundary_values - target) ** 2).mean()
    total = interior_energy + beta * boundary_penalty
    return total, {
        "interior_energy": float(interior_energy.detach().cpu()),
        "boundary_penalty": float(boundary_penalty.detach().cpu()),
        "gradient_energy_mean": float((0.5 * gradients.pow(2).sum(dim=1)).mean().detach().cpu()),
    }
