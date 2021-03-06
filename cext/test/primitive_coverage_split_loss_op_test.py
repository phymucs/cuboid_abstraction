import os
import sys
import numpy as np

import tensorflow as tf
from tensorflow.python.framework import constant_op
from tensorflow.python.platform import test
from tensorflow.python.ops import gradient_checker

sys.path.append('../..')
from cext import primitive_coverage_split_loss

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['CUDA_VISIBLE_DEVICES'] = '0'


class PrimitiveCoverageLossTest(test.TestCase):

  def _VerifyValuesNew(self, in_z, in_q, in_t, in_pos, expected):
    with self.test_session() as sess:
      z = constant_op.constant(in_z)
      q = constant_op.constant(in_q)
      t = constant_op.constant(in_t)
      pos = constant_op.constant(in_pos)
      data_out = primitive_coverage_split_loss(z, q, t, pos)
      actual = sess.run(data_out)
    self.assertAllClose(expected[0], actual[0], atol=1e-8)
    self.assertAllEqual(expected[1], actual[1])

  def _VerifyGradientsNew(self, in_z, in_q, in_t, in_pos, n_cube, batch_size):
    with self.test_session():
      z = constant_op.constant(in_z, shape=[batch_size, 3*n_cube])
      q = constant_op.constant(in_q, shape=[batch_size, 4*n_cube])
      t = constant_op.constant(in_t, shape=[batch_size, 3*n_cube])
      pos = constant_op.constant(in_pos)
      data_out = primitive_coverage_split_loss(z, q, t, pos)
      ret = gradient_checker.compute_gradient(
          [z, q, t],
          [[batch_size, 3*n_cube], [batch_size, 4*n_cube], [batch_size, 3*n_cube]],
          data_out[0],
          [batch_size, n_cube],
          x_init_value=[np.asfarray(in_z).reshape([batch_size, 3*n_cube]),
                        np.asfarray(in_q).reshape([batch_size, 4*n_cube]),
                        np.asfarray(in_t).reshape([batch_size, 3*n_cube])]
          )
      # print(ret)
      self.assertAllClose(ret[0][0], ret[0][1], atol=1e-4)
      self.assertAllClose(ret[1][0], ret[1][1], atol=1e-4)
      self.assertAllClose(ret[2][0], ret[2][1], atol=1e-4)


  def testForward_0(self):
    # point outside one cube
    in_z = [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]
    in_q = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
    in_t = [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]
    in_pos = [[0.5, 0.7, 0.5, 0.7],
              [0.5, 0.8, 0.5, 0.8],
              [0.5, 0.9, 0.5, 0.9],
              [0.0, 0.0, 1.0, 1.0]]
    loss = [[1.37], [1.37]]
    count = [[2], [2]]
    expected = [loss, count]
    self._VerifyValuesNew(in_z, in_q, in_t, in_pos, expected)

  def testForward_1(self):
    # point inside one cube
    in_z = [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]
    in_q = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
    in_t = [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]
    in_pos = [[0.2, 0.2],
              [0.2, 0.2],
              [0.2, 0.2],
              [0.0, 1.0]]
    loss = [[0.0], [0.0]]
    count = [[1], [1]]
    expected = [loss, count]
    self._VerifyValuesNew(in_z, in_q, in_t, in_pos, expected)

  def testForward_2(self):
    # two cube
    in_z = [[0.1, 0.1, 0.1, 0.2, 0.3, 0.4], [0.1, 0.1, 0.1, 0.2, 0.3, 0.4]]
    in_q = [[1.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.5], [1.0, 0.0, 0.0, 0.0, 0.5, 0.5, 0.5, 0.5]]
    in_t = [[0.1, 0.1, 0.1, 0.2, 0.3, 0.4], [0.1, 0.1, 0.1, 0.2, 0.3, 0.4]]
    in_pos = [[0.2, 0.3, 0.7, 0.2, 0.3, 0.7],
              [0.2, 0.3, 0.8, 0.2, 0.3, 0.8],
              [0.2, 0.3, 0.9, 0.2, 0.3, 0.9],
              [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]]
    loss = [[0, 0.14], [0, 0.14]]
    count = [[1, 2], [1, 2]]
    expected = [loss, count]
    self._VerifyValuesNew(in_z, in_q, in_t, in_pos, expected)

  def testBackward_0(self):
    # one cube, one point, test q
    in_z = [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]
    in_q = [[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]]
    in_t = [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1]]
    batch_size = 2
    n_cube = 1
    in_pos = [[0.5, 0.7, 0.5, 0.7],
              [0.5, 0.8, 0.5, 0.8],
              [0.5, 0.9, 0.5, 0.9],
              [0.0, 0.0, 1.0, 1.0]]
    self._VerifyGradientsNew(in_z, in_q, in_t, in_pos, n_cube, batch_size)

  def testBackward_1(self):
    # two point to two cube
    in_z = [[0.1, 0.1, 0.1, 0.1, 0.1, 0.1], [0.1, 0.1, 0.1, 0.1, 0.1, 0.1]]
    in_q = [[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0]]
    in_t = [[0.1, 0.1, 0.1, 0.8, 0.8, 0.8], [0.1, 0.1, 0.1, 0.8, 0.8, 0.8]]
    batch_size = 2
    n_cube = 2
    in_pos = [[0.3, 0.6, 0.3, 0.6],
              [0.3, 0.6, 0.3, 0.6],
              [0.3, 0.6, 0.3, 0.6],
              [0.0, 0.0, 1.0, 1.0]]
    self._VerifyGradientsNew(in_z, in_q, in_t, in_pos, n_cube, batch_size)


if __name__ == '__main__':
  test.main()
