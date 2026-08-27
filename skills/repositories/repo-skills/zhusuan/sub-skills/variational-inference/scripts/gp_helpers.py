"""Small Gaussian-process helpers adapted from ZhuSuan examples.

These helpers are useful for sparse variational GP examples and stay self-
contained so they do not depend on the original examples directory.
"""

from __future__ import absolute_import
from __future__ import division

import tensorflow as tf
import zhusuan as zs


class RBFKernel(object):
    def __init__(self, n_covariates, name='rbf_kernel', dtype=tf.float32):
        k_raw_scale = tf.get_variable('k_log_scale_{}'.format(name),
                                      [n_covariates], dtype,
                                      initializer=tf.zeros_initializer())
        self.k_scale = tf.nn.softplus(k_raw_scale)

    def __call__(self, x, y):
        batch_shape = tf.shape(x)[:-2]
        rank = x.shape.ndims
        assert_ops = [
            tf.assert_greater_equal(
                rank, 2,
                message='RBFKernel: rank(x) should be static and >=2'),
            tf.assert_equal(
                rank, tf.rank(y),
                message='RBFKernel: x and y should have the same rank')
        ]
        with tf.control_dependencies(assert_ops):
            x = tf.expand_dims(x, rank - 1)
            y = tf.expand_dims(y, rank - 2)
            k_scale = tf.reshape(self.k_scale, [1] * rank + [-1])
            ret = tf.exp(-tf.reduce_sum(tf.square(x - y) / k_scale, axis=-1) / 2)
        return ret

    def Kdiag(self, x):
        if x.shape.ndims == 2:
            return tf.ones([tf.shape(x)[0]], dtype=x.dtype)
        else:
            return tf.ones([tf.shape(x)[0], tf.shape(x)[1]], dtype=x.dtype)



def gp_conditional(z, fz, x, full_cov, kernel, Kzz_chol=None):
    """Return the GP conditional distribution f(x) | f(z)=fz."""
    n_z = int(z.shape[0])
    n_particles = tf.shape(fz)[0]

    if Kzz_chol is None:
        Kzz_chol = tf.cholesky(kernel(z, z))

    Kzz_chol_inv = tf.matrix_triangular_solve(Kzz_chol, tf.eye(n_z))
    Kzz_inv = tf.matmul(tf.transpose(Kzz_chol_inv), Kzz_chol_inv)
    Kxz = kernel(x, z)
    Kxziz = tf.matmul(Kxz, Kzz_inv)
    mean_fx_given_fz = tf.matmul(fz, tf.matrix_transpose(Kxziz))

    if full_cov:
        cov_fx_given_fz = kernel(x, x) - tf.matmul(Kxziz, tf.transpose(Kxz))
        cov_fx_given_fz = tf.tile(
            tf.expand_dims(tf.cholesky(cov_fx_given_fz), 0),
            [n_particles, 1, 1])
        fx_given_fz = zs.distributions.MultivariateNormalCholesky(
            mean_fx_given_fz, cov_fx_given_fz)
    else:
        var = kernel.Kdiag(x) - tf.reduce_sum(tf.matmul(
            Kxz, tf.matrix_transpose(Kzz_chol_inv)) ** 2, axis=-1)
        std = tf.sqrt(var)
        fx_given_fz = zs.distributions.Normal(
            mean=mean_fx_given_fz, std=std, group_ndims=1)
    return fx_given_fz
