"""Fast MCMC smoke check for ZhuSuan.

Runs a tiny HMC chain on a Gaussian target and exercises the effective sample
size helper. This is intentionally much smaller than the native tests.
"""

from __future__ import absolute_import
from __future__ import division

import numpy as np
import tensorflow as tf
import zhusuan as zs
from zhusuan.diagnostics import effective_sample_size


def log_joint(observed):
    x = observed['x']
    return -0.5 * tf.reduce_sum(x ** 2, axis=-1)


if __name__ == '__main__':
    x = tf.Variable(tf.zeros([8, 1]), trainable=False, name='x')
    hmc = zs.HMC(step_size=0.1, n_leapfrogs=2, adapt_step_size=None,
                 adapt_mass=None)
    sample_op, info = hmc.sample(log_joint, {}, {'x': x})

    sgld = zs.SGLD(learning_rate=0.01)
    sghmc = zs.SGHMC(learning_rate=0.01, friction=0.3,
                     variance_estimate=0.02, n_iter_resample_v=2,
                     second_order=False)
    sgnht = zs.SGNHT(learning_rate=0.01, variance_extra=0.0,
                     tune_rate=1.0, n_iter_resample_v=2,
                     second_order=False, use_vector_alpha=False)
    print(type(sgld).__name__, type(sghmc).__name__, type(sgnht).__name__)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        samples = []
        for _ in range(4):
            _, x_val, acc = sess.run([sample_op, x, info.acceptance_rate])
            samples.append(x_val.reshape(-1))
            print('acceptance', float(np.mean(acc)))
        samples = np.array(samples)
        print('sample_mean', float(np.mean(samples)))
        print('ess', float(effective_sample_size(samples, burn_in=0)))
