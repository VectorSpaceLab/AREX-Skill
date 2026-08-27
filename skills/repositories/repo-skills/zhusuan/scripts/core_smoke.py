"""Quick core smoke check for the installed ZhuSuan package.

This script exercises the core Bayesian modeling surface without depending on
repo-local examples or datasets.
"""

from __future__ import absolute_import
from __future__ import division

import tensorflow as tf
import zhusuan as zs


@zs.meta_bayesian_net(scope='core_smoke_model')
def build_model():
    bn = zs.BayesianNet()
    z = bn.normal('z', tf.zeros([2]), std=1.)
    bn.normal('x', z, std=1.)
    return bn


@zs.reuse_variables(scope='core_smoke_q')
def build_variational():
    bn = zs.BayesianNet()
    bn.normal('z', tf.zeros([2]), std=1.)
    return bn


if __name__ == '__main__':
    print('zhusuan', zs.__version__)
    model = build_model()
    variational = build_variational()
    lower_bound = zs.variational.elbo(
        model, {'x': tf.zeros([2])}, variational=variational, axis=0)
    cost = lower_bound.sgvb()
    hmc = zs.HMC(step_size=0.1, n_leapfrogs=1, adapt_step_size=None,
                 adapt_mass=None)
    print('sampler', type(hmc).__name__)
    with tf.Session() as sess:
        sess.run(tf.global_variables_initializer())
        lb_val, cost_val = sess.run([lower_bound, cost])
        print('elbo', float(lb_val))
        print('sgvb_cost', float(cost_val))
