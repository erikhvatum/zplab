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
# Authors: Erik Hvatum

from zacquisition.service import Service
from zacquisition.service_property import ServiceProperty
from zacquisition import service_property_validators as spvs

class Camera(Service):
    exposureTime = ServiceProperty(default=0.01, name='exposureTime', validators=spvs.isFloatLike)

    def __init__(self, pyClassString, zmqContext=None, instanceType=Service.InstanceType.Daemon, parent=None, name='Andor Camera (Zyla 5.5)', \
                 ipcSocketPath='/tmp/zacquisition', eventTcpPortNumber=51500, commandTcpPortNumber=51501, \
                 daemonHostName=None):
        super().__init__('zacquisition.camera.andor.Camera', zmqContext, instanceType, parent, name, \
                         ipcSocketPath, eventTcpPortNumber, commandTcpPortNumber, \
                         daemonHostName)