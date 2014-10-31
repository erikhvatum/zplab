from rpc_acquisition import message_device
from rpc_acquisition import message_manager
from rpc_acquisition.dm6000b import illumination_axes
from rpc_acquisition.dm6000b import objective_turret
from rpc_acquisition.dm6000b import stand
from rpc_acquisition.dm6000b import stage
from rpc_acquisition.andor import (andor, camera)


SCOPE_PORT = '/dev/ttyScope'
SCOPE_BAUD = 115200
SCOPE_CAMERA = 'ZYLA-5.5-CL3'

class Scope(message_device.AsyncDeviceNamespace):
    def __init__(self, property_server, verbose=False):
        super().__init__()
        self._message_manager = message_manager.LeicaMessageManager(SCOPE_PORT, SCOPE_BAUD, verbose=verbose)

        self.il = illumination_axes.IL(self._message_manager)
        self.tl = illumination_axes.TL(self._message_manager)
        self.nosepiece = objective_turret.ObjectiveTurret(self._message_manager)
        self.stage = stage.Stage(self._message_manager)
        self.stand = stand.Stand(self._message_manager)

        # TODO: add camera object (non-async) and whatever else we have 
        # plugged into the scope. IOTool box, maybe.
        # The lumencor and LED controls will be stuffed into IL and TL.
        
        andor.initialize(SCOPE_CAMERA)
        self.camera = camera.Camera(property_server)