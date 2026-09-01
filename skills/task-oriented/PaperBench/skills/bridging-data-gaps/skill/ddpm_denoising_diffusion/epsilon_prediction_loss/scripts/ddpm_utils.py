
import math

def linear_beta_schedule(beta_start, beta_end, num_timesteps):
    if num_timesteps <= 0:
        raise ValueError('num_timesteps must be positive')
    if not (0 < beta_start <= beta_end <= 1):
        raise ValueError('betas must satisfy 0 < beta_start <= beta_end <= 1')
    if num_timesteps == 1:
        return [float(beta_end)]
    step = (beta_end - beta_start) / (num_timesteps - 1)
    return [float(beta_start + step * i) for i in range(num_timesteps)]

def coefficients(betas):
    alpha_prod = 1.0
    rows=[]
    prev=1.0
    for i,b in enumerate(betas):
        a=1.0-b
        alpha_prod*=a
        rows.append({'t':i,'beta':b,'alpha':a,'alpha_cumprod':alpha_prod,'alpha_cumprod_prev':prev,'sqrt_alpha_cumprod':math.sqrt(alpha_prod),'sqrt_one_minus_alpha_cumprod':math.sqrt(1-alpha_prod),'sqrt_recip_alpha_cumprod':math.sqrt(1/alpha_prod),'sqrt_recipm1_alpha_cumprod':math.sqrt(1/alpha_prod-1)})
        prev=alpha_prod
    return rows

def q_sample_scalar(x_start, eps, row):
    return row['sqrt_alpha_cumprod'] * x_start + row['sqrt_one_minus_alpha_cumprod'] * eps

def predict_epsilon(theta, x_t, t_scaled):
    return theta[0] * x_t + theta[1] * t_scaled + theta[2]

def mse_loss(samples, theta):
    losses=[]
    for s in samples:
        pred=predict_epsilon(theta, s['x_t'], s['t_scaled'])
        losses.append((s['epsilon']-pred)**2)
    return sum(losses)/len(losses)

def gradient_step(samples, theta, lr):
    grads=[0.0,0.0,0.0]
    for s in samples:
        pred=predict_epsilon(theta, s['x_t'], s['t_scaled'])
        err=pred-s['epsilon']
        feats=[s['x_t'],s['t_scaled'],1.0]
        for i,f in enumerate(feats):
            grads[i]+=2*err*f/len(samples)
    return [theta[i]-lr*grads[i] for i in range(3)]
