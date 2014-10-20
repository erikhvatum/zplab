import ctypes
import atexit
import sys

_at_err_dict = {
    1: 'NOTINITIALISED',
    2: 'NOTIMPLEMENTED',
    3: 'READONLY',
    4: 'NOTREADABLE',
    5: 'NOTWRITABLE',
    6: 'OUTOFRANGE',
    7: 'INDEXNOTAVAILABLE',
    8: 'INDEXNOTIMPLEMENTED',
    9: 'EXCEEDEDMAXSTRINGLENGTH',
    10: 'CONNECTION',
    11: 'NODATA',
    12: 'INVALIDHANDLE',
    13: 'TIMEDOUT',
    14: 'BUFFERFULL',
    15: 'INVALIDSIZE',
    16: 'INVALIDALIGNMENT',
    17: 'COMM',
    18: 'STRINGNOTAVAILABLE',
    19: 'STRINGNOTIMPLEMENTED',
    20: 'NULL_FEATURE',
    21: 'NULL_HANDLE',
    22: 'NULL_IMPLEMENTED_VAR',
    23: 'NULL_READABLE_VAR',
    24: 'NULL_READONLY_VAR',
    25: 'NULL_WRITABLE_VAR',
    26: 'NULL_MINVALUE',
    27: 'NULL_MAXVALUE',
    28: 'NULL_VALUE',
    29: 'NULL_STRING',
    30: 'NULL_COUNT_VAR',
    31: 'NULL_ISAVAILABLE_VAR',
    32: 'NULL_MAXSTRINGLENGTH',
    33: 'NULL_EVCALLBACK',
    34: 'NULL_QUEUE_PTR',
    35: 'NULL_WAIT_PTR',
    36: 'NULL_PTRSIZE',
    37: 'NOMEMORY',
    38: 'DEVICEINUSE',
    100: 'HARDWARE_OVERFLOW',
    1002: 'AT_ERR_INVALIDOUTPUTPIXELENCODING',
    1003: 'AT_ERR_INVALIDINPUTPIXELENCODING'
}

class AndorError(RuntimeError):
    pass

def _at_errcheck(result, func, args):
    if result != 0:
        raise AndorError(_at_err_dict[result])
    return args

_at_wchar_scratch = ctypes.create_unicode_buffer(255)
_at_camera_handle = None
_at_core_lib = None
_at_util_lib = None

if sys.platform == 'win32':
    _libc = ctypes.libc
elif sys.platform == 'darwin':
    _libc = ctypes.CDLL('libc.dylib')
else:
    _libc = ctypes.CDLL('libc.so.6')

FeatureCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_void_p)

_AT_HANDLE_SYSTEM = 1
ANDOR_INFINITE = 0xFFFFFFFF

def _init_core_lib(corepath):
    global _at_core_lib
    _at_core_lib = ctypes.CDLL(corepath)
    _setup_core_functions(_at_core_lib)
    _at_core_lib.AT_InitialiseLibrary()
    atexit.register(_at_core_lib.AT_FinaliseLibrary)

def _init_util_lib(utilpath):
    global _at_util_lib
    _at_util_lib = ctypes.CDLL(utilpath)
    _setup_util_functions(_at_util_lib)
    _at_util_lib.AT_InitialiseUtilityLibrary()
#    atexit.register(_at_core_lib.AT_FinaliseUtilityLibrary)

def initialize(model_name_of_desired_camera='ZYLA-5.5-CL3'):
    if sys.platform == 'win32':
        ldd_ext = '.dll'
    elif sys.platform == 'darwin':
        ldd_ext = '.dylib'
    else:
        ldd_ext = '.so'

    if _at_core_lib is None:
        _init_core_lib('libatcore' + ldd_ext)
    if _at_util_lib is None:
        _init_util_lib('libatutility' + ldd_ext)

    devices_attached = _at_core_lib.AT_GetInt(_AT_HANDLE_SYSTEM, "DeviceCount")
    if devices_attached == 0:
        raise AndorError('No Andor SDK3 devices detected.  Is the camera turned on?')
    # Even on the scope machine, the default Andor configuration includes two
    # virtual cameras, for a total of three camera devices.  A hardware camera
    # will take device index 0, provided you have only one hardware camera, and
    # we are very clearly working under this assumption.  We might then test
    # this assumption by querying the camera's name and ensuring that it matches
    # the name of our hardware camera:
    global _at_camera_handle
    _at_camera_handle = _at_core_lib.AT_Open(0)
    if model_name_of_desired_camera is not None:
        camera_model_name = GetString('CameraModel')
        if camera_model_name != model_name_of_desired_camera:
            _at_core_lib.AT_Close(_at_camera_handle)
            _at_camera_handle = None
            raise AndorError('Model name of Andor device 0, "' + camera_model_name + 
                             '", does not match the desired camera model name, "' +
                             model_name_of_desired_camera + '".')

    atexit.register(_at_core_lib.AT_Close, _at_camera_handle)

def RegisterFeatureCallback(Feature, EvCallback, Context):
    """RegisterFeatureCallback(Feature, EvCallback, Context)
    
    Parameters:
        Feature: str
        EvCallback: FeatureCallback
        Context: ctypes.c_void_p"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_RegisterFeatureCallback(_at_internals._at_camera_handle, Feature, EvCallback, Context)
    else:
        raise RuntimeError('Andor library not initialized')

def UnregisterFeatureCallback(Feature, EvCallback, Context):
    """UnregisterFeatureCallback(Feature, EvCallback, Context)
    
    Parameters:
        Feature: str
        EvCallback: FeatureCallback
        Context: ctypes.c_void_p"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_UnregisterFeatureCallback(_at_internals._at_camera_handle, Feature, EvCallback, Context)
    else:
        raise RuntimeError('Andor library not initialized')

def IsImplemented(Feature):
    """IsImplemented(Feature) -> Implemented
    
    Parameters:
        Feature: str
    Return value:
        Implemented: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_IsImplemented(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def IsReadable(Feature):
    """IsReadable(Feature) -> Readable
    
    Parameters:
        Feature: str
    Return value:
        Readable: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_IsReadable(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def IsWritable(Feature):
    """IsWritable(Feature) -> Writable
    
    Parameters:
        Feature: str
    Return value:
        Writable: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_IsWritable(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def IsReadOnly(Feature):
    """IsReadOnly(Feature) -> ReadOnly
    
    Parameters:
        Feature: str
    Return value:
        ReadOnly: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_IsReadOnly(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def SetInt(Feature, Value):
    """SetInt(Feature, Value)
    
    Parameters:
        Feature: str
        Value: ctypes.c_int64"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_SetInt(_at_internals._at_camera_handle, Feature, Value)
    else:
        raise RuntimeError('Andor library not initialized')

def GetInt(Feature):
    """GetInt(Feature) -> Value
    
    Parameters:
        Feature: str
    Return value:
        Value: ctypes.c_int64"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetInt(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def GetIntMax(Feature):
    """GetIntMax(Feature) -> MaxValue
    
    Parameters:
        Feature: str
    Return value:
        MaxValue: ctypes.c_int64"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetIntMax(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def GetIntMin(Feature):
    """GetIntMin(Feature) -> MinValue
    
    Parameters:
        Feature: str
    Return value:
        MinValue: ctypes.c_int64"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetIntMin(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def SetFloat(Feature, Value):
    """SetFloat(Feature, Value)
    
    Parameters:
        Feature: str
        Value: ctypes.c_double"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_SetFloat(_at_internals._at_camera_handle, Feature, Value)
    else:
        raise RuntimeError('Andor library not initialized')

def GetFloat(Feature):
    """GetFloat(Feature) -> Value
    
    Parameters:
        Feature: str
    Return value:
        Value: ctypes.c_double"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetFloat(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def GetFloatMax(Feature):
    """GetFloatMax(Feature) -> MaxValue
    
    Parameters:
        Feature: str
    Return value:
        MaxValue: ctypes.c_double"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetFloatMax(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def GetFloatMin(Feature):
    """GetFloatMin(Feature) -> MinValue
    
    Parameters:
        Feature: str
    Return value:
        MinValue: ctypes.c_double"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetFloatMin(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def SetBool(Feature, Value):
    """SetBool(Feature, Value)
    
    Parameters:
        Feature: str
        Value: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_SetBool(_at_internals._at_camera_handle, Feature, Value)
    else:
        raise RuntimeError('Andor library not initialized')

def GetBool(Feature):
    """GetBool(Feature) -> Value
    
    Parameters:
        Feature: str
    Return value:
        Value: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetBool(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def SetEnumIndex(Feature, Value):
    """SetEnumIndex(Feature, Value)
    
    Parameters:
        Feature: str
        Value: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_SetEnumIndex(_at_internals._at_camera_handle, Feature, Value)
    else:
        raise RuntimeError('Andor library not initialized')

def SetEnumString(Feature, String):
    """SetEnumString(Feature, String)
    
    Parameters:
        Feature: str
        String: str"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_SetEnumString(_at_internals._at_camera_handle, Feature, String)
    else:
        raise RuntimeError('Andor library not initialized')

def GetEnumIndex(Feature):
    """GetEnumIndex(Feature) -> Value
    
    Parameters:
        Feature: str
    Return value:
        Value: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetEnumIndex(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def GetEnumCount(Feature):
    """GetEnumCount(Feature) -> Count
    
    Parameters:
        Feature: str
    Return value:
        Count: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetEnumCount(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def IsEnumIndexAvailable(Feature, Index):
    """IsEnumIndexAvailable(Feature, Index) -> Available
    
    Parameters:
        Feature: str
        Index: ctypes.c_int
    Return value:
        Available: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_IsEnumIndexAvailable(_at_internals._at_camera_handle, Feature, Index)
    else:
        raise RuntimeError('Andor library not initialized')

def IsEnumIndexImplemented(Feature, Index):
    """IsEnumIndexImplemented(Feature, Index) -> Implemented
    
    Parameters:
        Feature: str
        Index: ctypes.c_int
    Return value:
        Implemented: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_IsEnumIndexImplemented(_at_internals._at_camera_handle, Feature, Index)
    else:
        raise RuntimeError('Andor library not initialized')

def GetEnumStringByIndex(Feature, Index):
    """GetEnumStringByIndex(Feature, Index) -> String
    
    Parameters:
        Feature: str
        Index: ctypes.c_int
    Return value:
        String: str"""
    if _at_camera_handle is not None:
        _at_core_lib.AT_GetEnumStringByIndex(_at_camera_handle, Feature, Index, _at_wchar_scratch, _at_wchar_scratch._length_)
        return _at_wchar_scratch[:_libc.wcslen(_at_wchar_scratch)]
    else:
        raise RuntimeError('Andor library not initialized')

def Command(Feature):
    """Command(Feature)
    
    Parameters:
        Feature: str"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_Command(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def SetString(Feature, String):
    """SetString(Feature, String)
    
    Parameters:
        Feature: str
        String: str"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_SetString(_at_internals._at_camera_handle, Feature, String)
    else:
        raise RuntimeError('Andor library not initialized')

def GetString(Feature):
    """GetString(Feature) -> String
    
    Parameters:
        Feature: str
    Return value:
        String: str"""
    if _at_camera_handle is not None:
        _at_core_lib.AT_GetString(_at_camera_handle, Feature, _at_wchar_scratch, _at_wchar_scratch._length_)
        return _at_wchar_scratch[:_libc.wcslen(_at_wchar_scratch)]
    else:
        raise RuntimeError('Andor library not initialized')

def GetStringMaxLength(Feature):
    """GetStringMaxLength(Feature) -> MaxStringLength
    
    Parameters:
        Feature: str
    Return value:
        MaxStringLength: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_GetStringMaxLength(_at_internals._at_camera_handle, Feature)
    else:
        raise RuntimeError('Andor library not initialized')

def QueueBuffer(Ptr, PtrSize):
    """QueueBuffer(Ptr, PtrSize)
    
    Parameters:
        Ptr: ctypes.POINTER(ctypes.c_uint8)
        PtrSize: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_QueueBuffer(_at_internals._at_camera_handle, Ptr, PtrSize)
    else:
        raise RuntimeError('Andor library not initialized')

def WaitBuffer(Timeout):
    """WaitBuffer(Timeout) -> Ptr, PtrSize
    
    Parameters:
        Timeout: ctypes.c_uint
    Return values:
        Ptr: ctypes.POINTER(ctypes.c_uint8)
        PtrSize: ctypes.c_int"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_WaitBuffer(_at_internals._at_camera_handle, Timeout)
    else:
        raise RuntimeError('Andor library not initialized')

def Flush():
    """Flush()"""
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.AT_Flush(_at_internals._at_camera_handle, )
    else:
        raise RuntimeError('Andor library not initialized')


def ConvertBuffer(inputBuffer, outputBuffer, width, height, stride, inputPixelEncoding, outputPixelEncoding):
    '''ConvertBuffer(inputBuffer, outputBuffer, width, height, stride, inputPixelEncoding, outputPixelEncoding)
    
    Parameters:
        inputBuffer: ctypes.POINTER(ctypes.c_uint8)
        outputBuffer: ctypes.POINTER(ctypes.c_uint8)
        width, height, stride: ctypes.c_int64
        inputPixelEncoding, outputPixelEncoding: str'''
    _at_util_lib.AT_ConvertBuffer(inputBuffer, outputBuffer, width, height, stride, inputPixelEncoding, outputPixelEncoding)

def _setup_core_functions(lib):
    _prototype_AT_InitialiseLibrary = ctypes.CFUNCTYPE(ctypes.c_int)
    lib.AT_InitialiseLibrary = _prototype_AT_InitialiseLibrary(("AT_InitialiseLibrary", lib), ())
    lib.AT_InitialiseLibrary.errcheck = _at_errcheck
    
    _prototype_AT_FinaliseLibrary = ctypes.CFUNCTYPE(ctypes.c_int)
    lib.AT_FinaliseLibrary = _prototype_AT_FinaliseLibrary(("AT_FinaliseLibrary", lib), ())
    lib.AT_FinaliseLibrary.errcheck = _at_errcheck
    
    _prototype_AT_Open = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
    lib.AT_Open = _prototype_AT_Open(("AT_Open", lib), ((1, 'CameraIndex'), (2, 'Hndl')))
    lib.AT_Open.errcheck = _at_errcheck
    
    _prototype_AT_Close = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    lib.AT_Close = _prototype_AT_Close(("AT_Close", lib), ((1, 'Hndl'),))
    lib.AT_Close.errcheck = _at_errcheck
    
    _prototype_AT_RegisterFeatureCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, FeatureCallback, ctypes.c_void_p)
    lib.AT_RegisterFeatureCallback = _prototype_AT_RegisterFeatureCallback(("AT_RegisterFeatureCallback", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'EvCallback'), (1, 'Context')))
    lib.AT_RegisterFeatureCallback.errcheck = _at_errcheck
    
    _prototype_AT_UnregisterFeatureCallback = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, FeatureCallback, ctypes.c_void_p)
    lib.AT_UnregisterFeatureCallback = _prototype_AT_UnregisterFeatureCallback(("AT_UnregisterFeatureCallback", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'EvCallback'), (1, 'Context')))
    lib.AT_UnregisterFeatureCallback.errcheck = _at_errcheck
    
    _prototype_AT_IsImplemented = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_IsImplemented = _prototype_AT_IsImplemented(("AT_IsImplemented", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Implemented')))
    lib.AT_IsImplemented.errcheck = _at_errcheck
    
    _prototype_AT_IsReadable = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_IsReadable = _prototype_AT_IsReadable(("AT_IsReadable", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Readable')))
    lib.AT_IsReadable.errcheck = _at_errcheck
    
    _prototype_AT_IsWritable = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_IsWritable = _prototype_AT_IsWritable(("AT_IsWritable", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Writable')))
    lib.AT_IsWritable.errcheck = _at_errcheck
    
    _prototype_AT_IsReadOnly = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_IsReadOnly = _prototype_AT_IsReadOnly(("AT_IsReadOnly", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'ReadOnly')))
    lib.AT_IsReadOnly.errcheck = _at_errcheck
    
    _prototype_AT_SetInt = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int64)
    lib.AT_SetInt = _prototype_AT_SetInt(("AT_SetInt", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Value')))
    lib.AT_SetInt.errcheck = _at_errcheck
    
    _prototype_AT_GetInt = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int64))
    lib.AT_GetInt = _prototype_AT_GetInt(("AT_GetInt", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Value')))
    lib.AT_GetInt.errcheck = _at_errcheck
    
    _prototype_AT_GetIntMax = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int64))
    lib.AT_GetIntMax = _prototype_AT_GetIntMax(("AT_GetIntMax", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'MaxValue')))
    lib.AT_GetIntMax.errcheck = _at_errcheck
    
    _prototype_AT_GetIntMin = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int64))
    lib.AT_GetIntMin = _prototype_AT_GetIntMin(("AT_GetIntMin", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'MinValue')))
    lib.AT_GetIntMin.errcheck = _at_errcheck
    
    _prototype_AT_SetFloat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_double)
    lib.AT_SetFloat = _prototype_AT_SetFloat(("AT_SetFloat", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Value')))
    lib.AT_SetFloat.errcheck = _at_errcheck
    
    _prototype_AT_GetFloat = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_double))
    lib.AT_GetFloat = _prototype_AT_GetFloat(("AT_GetFloat", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Value')))
    lib.AT_GetFloat.errcheck = _at_errcheck
    
    _prototype_AT_GetFloatMax = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_double))
    lib.AT_GetFloatMax = _prototype_AT_GetFloatMax(("AT_GetFloatMax", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'MaxValue')))
    lib.AT_GetFloatMax.errcheck = _at_errcheck
    
    _prototype_AT_GetFloatMin = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_double))
    lib.AT_GetFloatMin = _prototype_AT_GetFloatMin(("AT_GetFloatMin", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'MinValue')))
    lib.AT_GetFloatMin.errcheck = _at_errcheck
    
    _prototype_AT_SetBool = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int)
    lib.AT_SetBool = _prototype_AT_SetBool(("AT_SetBool", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Value')))
    lib.AT_SetBool.errcheck = _at_errcheck
    
    _prototype_AT_GetBool = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_GetBool = _prototype_AT_GetBool(("AT_GetBool", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Value')))
    lib.AT_GetBool.errcheck = _at_errcheck
    
    _prototype_AT_SetEnumIndex = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int)
    lib.AT_SetEnumIndex = _prototype_AT_SetEnumIndex(("AT_SetEnumIndex", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Value')))
    lib.AT_SetEnumIndex.errcheck = _at_errcheck
    
    _prototype_AT_SetEnumString = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_wchar_p)
    lib.AT_SetEnumString = _prototype_AT_SetEnumString(("AT_SetEnumString", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'String')))
    lib.AT_SetEnumString.errcheck = _at_errcheck
    
    _prototype_AT_GetEnumIndex = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_GetEnumIndex = _prototype_AT_GetEnumIndex(("AT_GetEnumIndex", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Value')))
    lib.AT_GetEnumIndex.errcheck = _at_errcheck
    
    _prototype_AT_GetEnumCount = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_GetEnumCount = _prototype_AT_GetEnumCount(("AT_GetEnumCount", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'Count')))
    lib.AT_GetEnumCount.errcheck = _at_errcheck
    
    _prototype_AT_IsEnumIndexAvailable = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
    lib.AT_IsEnumIndexAvailable = _prototype_AT_IsEnumIndexAvailable(("AT_IsEnumIndexAvailable", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Index'), (2, 'Available')))
    lib.AT_IsEnumIndexAvailable.errcheck = _at_errcheck
    
    _prototype_AT_IsEnumIndexImplemented = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int))
    lib.AT_IsEnumIndexImplemented = _prototype_AT_IsEnumIndexImplemented(("AT_IsEnumIndexImplemented", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Index'), (2, 'Implemented')))
    lib.AT_IsEnumIndexImplemented.errcheck = _at_errcheck
    
    _prototype_AT_GetEnumStringByIndex = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int)
    lib.AT_GetEnumStringByIndex = _prototype_AT_GetEnumStringByIndex(("AT_GetEnumStringByIndex", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'Index'), (1, 'String'), (1, 'StringLength')))
    lib.AT_GetEnumStringByIndex.errcheck = _at_errcheck
    
    _prototype_AT_Command = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p)
    lib.AT_Command = _prototype_AT_Command(("AT_Command", lib), ((1, 'Hndl'), (1, 'Feature')))
    lib.AT_Command.errcheck = _at_errcheck
    
    _prototype_AT_SetString = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_wchar_p)
    lib.AT_SetString = _prototype_AT_SetString(("AT_SetString", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'String')))
    lib.AT_SetString.errcheck = _at_errcheck
    
    _prototype_AT_GetString = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_int)
    lib.AT_GetString = _prototype_AT_GetString(("AT_GetString", lib), ((1, 'Hndl'), (1, 'Feature'), (1, 'String'), (1, 'StringLength')))
    lib.AT_GetString.errcheck = _at_errcheck
    
    _prototype_AT_GetStringMaxLength = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int))
    lib.AT_GetStringMaxLength = _prototype_AT_GetStringMaxLength(("AT_GetStringMaxLength", lib), ((1, 'Hndl'), (1, 'Feature'), (2, 'MaxStringLength')))
    lib.AT_GetStringMaxLength.errcheck = _at_errcheck
    
    _prototype_AT_QueueBuffer = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.c_uint8), ctypes.c_int)
    lib.AT_QueueBuffer = _prototype_AT_QueueBuffer(("AT_QueueBuffer", lib), ((1, 'Hndl'), (1, 'Ptr'), (1, 'PtrSize')))
    lib.AT_QueueBuffer.errcheck = _at_errcheck
    
    _prototype_AT_WaitBuffer = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8)), ctypes.POINTER(ctypes.c_int), ctypes.c_uint)
    lib.AT_WaitBuffer = _prototype_AT_WaitBuffer(("AT_WaitBuffer", lib), ((1, 'Hndl'), (2, 'Ptr'), (2, 'PtrSize'), (1, 'Timeout')))
    lib.AT_WaitBuffer.errcheck = _at_errcheck
    
    _prototype_AT_Flush = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int)
    lib.AT_Flush = _prototype_AT_Flush(("AT_Flush", lib), ((1, 'Hndl'),))
    lib.AT_Flush.errcheck = _at_errcheck

def _setup_util_functions(lib):
    _prototype_AT_ConvertBuffer = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_uint8), ctypes.POINTER(ctypes.c_uint8), ctypes.c_int64, ctypes.c_int64, ctypes.c_int64, ctypes.c_wchar_p, ctypes.c_wchar_p)
    lib.AT_ConvertBuffer = _prototype_AT_ConvertBuffer(("AT_ConvertBuffer", lib), ((1, 'inputBuffer'), (1, 'outputBuffer'), (1, 'width'), (1, 'height'), (1, 'stride'), (1, 'inputPixelEncoding'), (1, 'outputPixelEncoding')))
    lib.AT_ConvertBuffer.errcheck = _at_errcheck
    
    _prototype_AT_InitialiseUtilityLibrary = ctypes.CFUNCTYPE(ctypes.c_int)
    lib.AT_InitialiseUtilityLibrary = _prototype_AT_InitialiseUtilityLibrary(("AT_InitialiseUtilityLibrary", lib), ())
    lib.AT_InitialiseUtilityLibrary.errcheck = _at_errcheck
