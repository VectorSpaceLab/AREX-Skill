"""Fast variational-inference smoke check for ZhuSuan.

Exercises ELBO, IWAE-style objectives, normalizing flows, and the GP helper
module used by the sparse variational GP example.
"""

from __future__ import absolute_import
from __future__ import division

from pathlib import Path
import sys

import tensorflow as tf
import zhusuan as zs

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gp_helpers import RBFKernel, gp_conditional


@zs.meta_bayesian_net(scope='vi_smoke_model')
def build_model():
    bn = zs.BayesianNet()
    z = bn.normal('z', tf.zeros([2, 1]), std=1., group_ndims=1)
    bn.normal('x', z, std=1., group_ndims=1)
    return bn


@zs.reuse_variables(scope='vi_smoke_q')
def build_q(n_particles):
    bn = zs.BayesianNet()
    bn.normal('z', tf.zeros([2, 1]), std=1., group_ndims=1,
              n_samples=n_particles)
    return bn


if __name__ == '__main__':
    model = build_model()
    q = build_q(2)
    qz, log_qz = q.query('z', outputs=True, local_log_prob=True)
    qz, log_qz = zs.planar_normalizing_flow(qz, log_qz, n_iters=1)

    elbo = zs.variational.elbo(
        model, {'x': tf.zeros([2, 1])}, latent={'z': [qz, log_qz]}, axis=0)
    iw = zs.variational.importance_weighted_objective(
        model, {'x': tf.zeros([2, 1])}, latent={'z': [qz, log_qz]}, axis=0)
    is_ll = zs.is_loglikelihood(
        model, {'x': tf.zeros([2, 1])}, {'z': [qz, log_qz]}, axis=0)

    kernel = RBFKernel(1)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        elbo_val, iw_val, is_val = sess.run([
            tf.reduce_mean(elbo), tf.reduce_mean(iw), tf.reduce_mean(is_ll)])
        gp = gp_conditional(
            tf.constant([[0.0]], dtype=tf.float32),
            tf.zeros([1, 1], dtype=tf.float32),
            tf.constant([[1.0]], dtype=tf.float32),
            full_cov=False,
            kernel=kernel)
        gp_sample = sess.run(gp.sample())
        print('elbo', float(elbo_val))
        print('iwae', float(iw_val))
        print('is_ll', float(is_val))
        print('gp_sample_shape', gp_sample.shape)
