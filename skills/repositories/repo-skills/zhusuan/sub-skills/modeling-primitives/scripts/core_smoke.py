"""Core modeling smoke check for ZhuSuan.

This script exercises the core Bayesian-network surface and a minimal ELBO
call without touching repo-local examples or datasets.
"""

from __future__ import absolute_import
from __future__ import division

import tensorflow as tf
import zhusuan as zs


@zs.meta_bayesian_net(scope='modeling_primitives_smoke')
def build_model():
    bn = zs.BayesianNet()
    z = bn.normal('z', tf.zeros([2]), std=1., group_ndims=1)
    bn.normal('x', z, std=1., group_ndims=1)
    return bn


@zs.reuse_variables(scope='modeling_primitives_q')
def build_variational():
    bn = zs.BayesianNet()
    bn.normal('z', tf.zeros([2]), std=1., group_ndims=1, n_samples=2)
    return bn


if __name__ == '__main__':
    model = build_model()
    conditioned = model.observe(x=tf.zeros([2]))
    variational = build_variational()
    lower_bound = zs.variational.elbo(
        model, {'x': tf.zeros([2])}, variational=variational, axis=0)

    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        cond_log_prob, log_joint, elbo_val = sess.run([
            conditioned.cond_log_prob('x'),
            conditioned.log_joint(),
            tf.reduce_mean(lower_bound),
        ])
        print('cond_log_prob', float(cond_log_prob))
        print('log_joint', float(log_joint))
        print('elbo', float(elbo_val))
