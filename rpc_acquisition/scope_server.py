import zmq
import platform

from . import simple_rpc
from . import scope
from . import scope_configuration as config
from . import ism_buffer_utils

def server_main(rpc_port=None, rpc_interrupt_port=None, property_port=None, verbose=False, context=None):
    if rpc_port is None:
        rpc_port = config.Server.RPC_PORT
    if rpc_interrupt_port is None:
        rpc_interrupt_port = config.Server.RPC_INTERRUPT_PORT
    if property_port is None:
        property_port = config.Server.PROPERTY_PORT

    if context is None:
        context = zmq.Context()

    property_server = simple_rpc.property_server.ZMQServer(property_port, context=context, verbose=verbose)

    scope_controller = scope.Scope(property_server, verbose=verbose)
    # add ism_buffer_utils as hidden elements of the namespace, which RPC clients can use for seamless buffer sharing
    scope_controller._ism_buffer_utils = ism_buffer_utils

    interrupter = simple_rpc.rpc_server.ZMQInterrupter(rpc_interrupt_port, context=context)
    rpc_server = simple_rpc.rpc_server.ZMQServer(scope_controller, interrupter, rpc_port, context=context, verbose=verbose)

    rpc_server.run()
