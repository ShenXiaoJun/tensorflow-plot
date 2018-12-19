'''Unit Test for tfplot.ops'''

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
import types
import sys
import os
import hashlib

import tensorflow as tf
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # filter out INFO and WARN logs
tf.logging.set_verbosity(tf.logging.ERROR)

import matplotlib
matplotlib.rcParams['figure.figsize'] = (2.5, 2.5)

from imgcat import imgcat
from termcolor import cprint
import numpy as np

import tfplot.figure
import skimage.data


# some fixtures as in showcases.ipynb
def fake_attention():
    import scipy.ndimage
    attention = np.zeros([16, 16], dtype=np.float32)
    attention[(12, 8)] = 1.0
    attention[(10, 9)] = 1.0
    attention = scipy.ndimage.filters.gaussian_filter(attention, sigma=1.5)
    return attention


def hash_image(img):
    return hashlib.sha1(img.tobytes()).hexdigest()

# the plot function can have additional kwargs for providing configuration points
def _overlay_attention(attention, image,
                      alpha=0.5, cmap='jet'):
    fig = tfplot.Figure(figsize=(4, 4))
    ax = fig.add_subplot(1, 1, 1)
    ax.axis('off')
    fig.subplots_adjust(0, 0, 1, 1)  # get rid of margins

    H, W = attention.shape
    ax.imshow(image, extent=[0, H, 0, W])
    ax.imshow(attention, cmap=cmap,
                alpha=alpha, extent=[0, H, 0, W])
    return fig



class TestOps(tf.test.TestCase):
    '''
    Tests tfplot.ops
    '''
    def _execute_plot_op(self, op, print_image=False, feed_dict={}):
        '''Execute the op, and get the result (e.g. ndarray) under a test session'''
        with self.test_session() as sess:
            cprint("\n >>> " + str(op), color='cyan')
            self.assertIsInstance(op, tf.Tensor)
            ret = sess.run(op, feed_dict=feed_dict)
            if print_image and sys.platform == 'darwin':
                print(' ', end='')
                sys.stdout.flush()
                imgcat(ret)
                print('SHA1: ' + hash_image(ret))
            return ret

    # ----------------------------------------------------------------------

    def test_plot_basic(self):
        '''1.1 A basic example'''

        def test_figure():
            fig, ax = tfplot.subplots(figsize=(4, 4))
            ax.text(0.5, 0.5, "Hello World!", ha='center', va='center', size=24)
            return fig

        plot_op = tfplot.plot(test_figure, [])
        r = self._execute_plot_op(plot_op, print_image=True)

    def test_plot_with_arguments(self):
        '''1.2 with Arguments that takes a tensor'''

        def figure_attention(attention):
            fig, ax = tfplot.subplots(figsize=(4, 3))
            im = ax.imshow(attention, cmap='jet')
            fig.colorbar(im)
            return fig

        attention_tensor = tf.constant(fake_attention())
        plot_op = tfplot.plot(figure_attention, [attention_tensor])
        r = self._execute_plot_op(plot_op, print_image=True)

        # TODO: how to compare images?

    def test_plot_with_kwargs(self):
        '''1.3 with kwargs'''

        attention_tensor = fake_attention()
        image_tensor = tf.constant(skimage.data.chelsea())

        # (a) default execution
        plot_op = tfplot.plot(_overlay_attention, [attention_tensor, image_tensor])
        r = self._execute_plot_op(plot_op, print_image=True)
        self.assertEquals(hash_image(r), 'da9c77d5a7b2fe38a4e0985c0b5fc4f68cd269c0')

        # (b) override cmap and alpha
        plot_op = tfplot.plot(_overlay_attention, [attention_tensor, image_tensor],
                              cmap='gray', alpha=0.8)
        r = self._execute_plot_op(plot_op, print_image=True)
        self.assertEquals(hash_image(r), 'e49475e0452fd744864b118c0464bdf1e12d678d')


        # TODO: how to compare images?

    def test_plot_many(self):
        '''1.4 plot_many'''
        # make a fake batch
        batch_size = 3
        image_tensor = tf.constant(skimage.data.chelsea())
        attention_batch = tf.random_gamma([batch_size, 7, 7], alpha=0.3, seed=42)
        image_batch = tf.tile(tf.expand_dims(image_tensor, 0),
                              [batch_size, 1, 1, 1], name='image_batch') # copy

        plot_op = tfplot.plot_many(_overlay_attention, [attention_batch, image_batch])
        r = self._execute_plot_op(plot_op)
        #for i in range(3): imgcat(r[i])
        self.assertEquals(r.shape, (3, 400, 400, 4))