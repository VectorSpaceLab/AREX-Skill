import math
import random


def logsumexp(values):
    maximum = max(values)
    return maximum + math.log(sum(math.exp(value - maximum) for value in values))


def squared_distance(left, right):
    return sum((a - b) ** 2 for a, b in zip(left, right))


def normalize_log_weights(log_weights):
    normalizer = logsumexp(log_weights)
    weights = [math.exp(value - normalizer) for value in log_weights]
    return weights


def effective_sample_size(weights):
    return 1.0 / sum(weight * weight for weight in weights)


def entropy(weights):
    return -sum(weight * math.log(max(weight, 1e-300)) for weight in weights)


def gaussian_kde_density(point, particles, weights, bandwidth):
    dimension = len(point)
    coefficient = 1.0 / ((math.sqrt(2.0 * math.pi) * bandwidth) ** dimension)
    total = 0.0
    for particle, weight in zip(particles, weights):
        total += weight * coefficient * math.exp(-0.5 * squared_distance(point, particle) / (bandwidth * bandwidth))
    return total


def weighted_choice_index(rng, weights):
    threshold = rng.random()
    cumulative = 0.0
    for index, weight in enumerate(weights):
        cumulative += weight
        if cumulative >= threshold:
            return index
    return len(weights) - 1


def rejuvenate_particles(rng, particles, weights, bandwidth):
    refreshed = []
    for _ in particles:
        ancestor = particles[weighted_choice_index(rng, weights)]
        refreshed.append([value + rng.gauss(0.0, bandwidth) for value in ancestor])
    return refreshed


def pmd_weight_update(weights, log_factors, gamma):
    log_weights = [math.log(max(weight, 1e-300)) + gamma * factor for weight, factor in zip(weights, log_factors)]
    updated = normalize_log_weights(log_weights)
    return {"weights": updated, "effective_sample_size": effective_sample_size(updated), "entropy": entropy(updated)}


def run_pmd_loop(initial_particles, observations, log_likelihood, log_prior, iterations=20, batch_size=4, gamma=0.05, bandwidth=0.5, seed=0):
    rng = random.Random(seed)
    particles = [list(particle) for particle in initial_particles]
    weights = [1.0 / len(particles)] * len(particles)
    trace = []
    for iteration in range(iterations):
        particles = rejuvenate_particles(rng, particles, weights, bandwidth)
        batch = [observations[rng.randrange(len(observations))] for _ in range(batch_size)]
        scale = len(observations) / batch_size
        log_factors = []
        for particle in particles:
            likelihood_term = scale * sum(log_likelihood(particle, observation) for observation in batch)
            density_term = math.log(max(gaussian_kde_density(particle, particles, weights, bandwidth), 1e-300))
            log_factors.append(likelihood_term + log_prior(particle) - density_term)
        update = pmd_weight_update(weights, log_factors, gamma)
        weights = update["weights"]
        trace.append({"iteration": iteration + 1, "effective_sample_size": update["effective_sample_size"], "entropy": update["entropy"], "weights_sum": sum(weights)})
    return {"particles": particles, "weights": weights, "trace": trace, "bandwidth": bandwidth}
