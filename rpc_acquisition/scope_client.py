# The MIT License (MIT)
#
# Copyright (c) 2014 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Zach Pincus

import functools
import zmq
import time
import collections
import numpy
import threading

from .simple_rpc import rpc_client, property_client
from . import scope_configuration as config
from .util import transfer_ism_buffer

def wrap_image_getter(namespace, func_name, get_data):
    function = getattr(namespace, func_name)
    @functools.wraps(function)
    def wrapped():
        return get_data(function())
    setattr(namespace, func_name, wrapped)

def wrap_images_getter(namespace, func_name, get_data):
    function = getattr(namespace, func_name)
    @functools.wraps(function)
    def wrapped():
        return [get_data(name) for name in function()]
    setattr(namespace, func_name, wrapped)

def rpc_client_main(host='127.0.0.1', context=None):
    rpc_addr = config.Server.rpc_addr(host)
    interrupt_addr = config.Server.interrupt_addr(host)

    client = rpc_client.ZMQClient(rpc_addr, interrupt_addr, context)
    scope = client.proxy_namespace()
    is_local, get_data = transfer_ism_buffer.client_get_data_getter(client)
    scope._get_data = get_data
    scope._is_local = is_local
    if not is_local:
        scope.camera.set_network_compression = get_data.set_network_compression
    scope._rpc_client = client
    if hasattr(scope, 'camera'):
        wrap_image_getter(scope.camera, 'acquire_image', get_data)
        wrap_image_getter(scope.camera, 'live_image', get_data)
        wrap_image_getter(scope.camera, 'next_image', get_data)
        if hasattr(scope.camera, 'acquisition_sequencer'):
            wrap_images_getter(scope.camera.acquisition_sequencer, 'run', get_data)
    return scope

def property_client_main(host='127.0.0.1', context=None):
    property_addr = config.Server.property_addr(host)
    scope_properties = property_client.ZMQClient(property_addr, context)
    return scope_properties


def client_main(host='127.0.0.1', context=None, subscribe_all=False):
    if context is None:
        context = zmq.Context()
    scope = rpc_client_main(host, context)
    scope_properties = property_client_main(host, context)
    if subscribe_all:
        # have the property client subscribe to all properties. Even with a no-op callback,
        # this causes the client to keep its internal 'properties' dictionary up-to-date
        scope_properties.subscribe_prefix('', lambda x, y: None)
        scope.rebroadcast_properties()
    return scope, scope_properties

class LiveStreamer:
    def __init__(self, scope, scope_properties, image_ready_callback):
        self.scope = scope
        self.image_ready_callback = image_ready_callback
        self.image_received = threading.Event()
        self.live = scope.camera.live_mode
        self.latest_intervals = collections.deque(maxlen=10)
        self._last_time = time.time()
        scope_properties.subscribe('scope.camera.live_mode', self._live_change, valueonly=True)
        scope_properties.subscribe('scope.camera.live_frame', self._live_update, valueonly=True)

    def get_image(self):
        self.image_received.wait()
        # stash our latest frame number, as self.frame_no could change if further updates occur while processing...
        frame_no = self.frame_no
        # get image before re-enabling image-receiving because if this is over the network, it could take a while
        image = self.scope.camera.live_image()
        t = time.time()
        self.latest_intervals.append(t - self._last_time)
        self._last_time = t
        self.image_received.clear()
        return image, frame_no

    def get_fps(self):
        if not self.live:
            return
        return 1/numpy.mean(self.latest_intervals)

    def _live_change(self, live):
        # called in property_client's thread: note we can't do RPC calls
        self.live = live
        self.latest_intervals.clear()
        self._last_time = time.time()

    def _live_update(self, frame_no):
        # called in property client's thread: note we can't do RPC calls...
        # Note: if we've already received an image, but nobody on the main thread
        # has called get_image() to retrieve it, then just ignore subsequent
        # updates. However, always update the frame number so that get_image()
        # can accurately report what the current frame is (in case the client
        # cares to know if frames were dropped. There's a bit of a race-condition
        # here if the frame is updated while get_image() is in action, but this
        # is a pretty minimal issue and not worth adding locking around.

        self.frame_no = frame_no
        if not self.image_received.is_set():
            self.image_received.set()
            self.image_ready_callback()