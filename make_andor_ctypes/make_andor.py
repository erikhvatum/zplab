import output_ctypes

code = """import ctypes
import atexit
import sys

_at_err_dict = {{
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
}}

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

{}

def ConvertBuffer(inputBuffer, outputBuffer, width, height, stride, inputPixelEncoding, outputPixelEncoding):
    '''ConvertBuffer(inputBuffer, outputBuffer, width, height, stride, inputPixelEncoding, outputPixelEncoding)
    
    Parameters:
        inputBuffer: ctypes.POINTER(ctypes.c_uint8)
        outputBuffer: ctypes.POINTER(ctypes.c_uint8)
        width, height, stride: ctypes.c_int64
        inputPixelEncoding, outputPixelEncoding: str'''
    _at_util_lib.AT_ConvertBuffer(inputBuffer, outputBuffer, width, height, stride, inputPixelEncoding, outputPixelEncoding)

def _setup_core_functions(lib):
    {}

def _setup_util_functions(lib):
    {}
"""

core_protos = '''
int [_at_errcheck] AT_InitialiseLibrary();
int [_at_errcheck] AT_FinaliseLibrary();
int [_at_errcheck] AT_Open(int CameraIndex, AT_H* Hndl [output]);
int [_at_errcheck] AT_Close(AT_H Hndl);
int [_at_errcheck] AT_RegisterFeatureCallback(AT_H Hndl, const AT_WC* Feature, FeatureCallback EvCallback, void* Context);
int [_at_errcheck] AT_UnregisterFeatureCallback(AT_H Hndl, const AT_WC* Feature, FeatureCallback EvCallback, void* Context);
int [_at_errcheck] AT_IsImplemented(AT_H Hndl, const AT_WC* Feature, AT_BOOL* Implemented [output]);
int [_at_errcheck] AT_IsReadable(AT_H Hndl, const AT_WC* Feature, AT_BOOL* Readable [output]);
int [_at_errcheck] AT_IsWritable(AT_H Hndl, const AT_WC* Feature, AT_BOOL* Writable [output]);
int [_at_errcheck] AT_IsReadOnly(AT_H Hndl, const AT_WC* Feature, AT_BOOL* ReadOnly [output]);
int [_at_errcheck] AT_SetInt(AT_H Hndl, const AT_WC* Feature, AT_64 Value);
int [_at_errcheck] AT_GetInt(AT_H Hndl, const AT_WC* Feature, AT_64* Value [output]);
int [_at_errcheck] AT_GetIntMax(AT_H Hndl, const AT_WC* Feature, AT_64* MaxValue [output]);
int [_at_errcheck] AT_GetIntMin(AT_H Hndl, const AT_WC* Feature, AT_64* MinValue [output]);
int [_at_errcheck] AT_SetFloat(AT_H Hndl, const AT_WC* Feature, double Value);
int [_at_errcheck] AT_GetFloat(AT_H Hndl, const AT_WC* Feature, double* Value [output]);
int [_at_errcheck] AT_GetFloatMax(AT_H Hndl, const AT_WC* Feature, double* MaxValue [output]);
int [_at_errcheck] AT_GetFloatMin(AT_H Hndl, const AT_WC* Feature, double* MinValue [output]);
int [_at_errcheck] AT_SetBool(AT_H Hndl, const AT_WC* Feature, AT_BOOL Value);
int [_at_errcheck] AT_GetBool(AT_H Hndl, const AT_WC* Feature, AT_BOOL* Value [output]);
int [_at_errcheck] AT_SetEnumIndex(AT_H Hndl, const AT_WC* Feature, int Value);
int [_at_errcheck] AT_SetEnumString(AT_H Hndl, const AT_WC* Feature, const AT_WC* String);
int [_at_errcheck] AT_GetEnumIndex(AT_H Hndl, const AT_WC* Feature, int* Value [output]);
int [_at_errcheck] AT_GetEnumCount(AT_H Hndl, const AT_WC* Feature, int* Count [output]);
int [_at_errcheck] AT_IsEnumIndexAvailable(AT_H Hndl, const AT_WC* Feature, int Index, AT_BOOL* Available [output]);
int [_at_errcheck] AT_IsEnumIndexImplemented(AT_H Hndl, const AT_WC* Feature, int Index, AT_BOOL* Implemented [output]);
int [_at_errcheck] AT_GetEnumStringByIndex(AT_H Hndl, const AT_WC* Feature, int Index, AT_WC* String, int StringLength);
int [_at_errcheck] AT_Command(AT_H Hndl, const AT_WC* Feature);
int [_at_errcheck] AT_SetString(AT_H Hndl, const AT_WC* Feature, const AT_WC* String);
int [_at_errcheck] AT_GetString(AT_H Hndl, const AT_WC* Feature, AT_WC* String, int StringLength);
int [_at_errcheck] AT_GetStringMaxLength(AT_H Hndl, const AT_WC* Feature, int* MaxStringLength [output]);
int [_at_errcheck] AT_QueueBuffer(AT_H Hndl, AT_U8* Ptr, int PtrSize);
int [_at_errcheck] AT_WaitBuffer(AT_H Hndl, AT_U8** Ptr [output], int* PtrSize [output], unsigned int Timeout);
int [_at_errcheck] AT_Flush(AT_H Hndl);'''.strip().split('\n')

util_protos = '''
int [_at_errcheck] AT_ConvertBuffer(AT_U8* inputBuffer, AT_U8* outputBuffer, AT_64 width, AT_64 height, AT_64 stride, const AT_WC* inputPixelEncoding, const AT_WC* outputPixelEncoding);
int [_at_errcheck] AT_InitialiseUtilityLibrary();
'''.strip().split('\n')

additional_defs = {
  'AT_H': 'ctypes.c_int',
  'AT_BOOL': 'ctypes.c_int',
  'AT_WC *': 'ctypes.c_wchar_p',
  'AT_64': 'ctypes.c_int64',
  'AT_U8': 'ctypes.c_uint8',
  'FeatureCallback': 'FeatureCallback'
}

default_wrapper = '''def {}({}):
    {}
    if _at_internals._at_camera_handle is not None:
        return _at_core_lib.{}(_at_internals._at_camera_handle, {})
    else:
        raise RuntimeError('Andor library not initialized')
'''

string_wrapper = '''def {}({}):
    {}
    if _at_camera_handle is not None:
        _at_core_lib.{}(_at_camera_handle, {}, _at_wchar_scratch, _at_wchar_scratch._length_)
        return _at_wchar_scratch[:_libc.wcslen(_at_wchar_scratch)]
    else:
        raise RuntimeError('Andor library not initialized')
'''


def indent(lines, amount=4, ch=' '):
    padding = amount * ch
    return ('\n'+padding).join(lines.split('\n'))

def generate_code(outfile='andor.py'):
    core_setup = []
    wrapper_funcs = []
    for proto in core_protos:
        function_name, in_args, out_args, func_code = output_ctypes.create_library_prototype(proto, 'lib', additional_defs)
        core_setup.append(func_code)
        if in_args and in_args[0][0] == 'Hndl' and function_name != 'AT_Close':
            # wrap the function in a helpful wrapper
            in_args = in_args[1:]
            if len(in_args) > 1 and in_args[-2][0] == 'String' and in_args[-1][0] == 'StringLength':
                wrapper_text = string_wrapper
                in_args = in_args[:-2]
                out_args.append(('String', 'str'))
            else:
                wrapper_text = default_wrapper
            wrapper_name = function_name[3:] # strip 'AT_'
            doc = '"""{}"""'.format(output_ctypes.construct_docstring(wrapper_name, in_args, out_args))
            if in_args:
                in_arg_names, in_arg_types = zip(*in_args)
                in_arg_names = ', '.join(in_arg_names)
            else:
                in_arg_names = ''
            wrapper_code = wrapper_text.format(wrapper_name, in_arg_names, indent(doc), function_name, in_arg_names)
            wrapper_funcs.append(wrapper_code)
                
    util_setup = []
    for proto in util_protos:
        function_name, in_args, out_args, func_code = output_ctypes.create_library_prototype(proto, 'lib', additional_defs)
        util_setup.append(func_code)
    
    core_setup = '\n\n'.join(core_setup)
    wrapper_funcs = '\n'.join(wrapper_funcs)
    util_setup = '\n\n'.join(util_setup)
    output_code = code.format(wrapper_funcs, indent(core_setup), indent(util_setup))
    
    with open(outfile, 'w') as f:
        f.write(output_code)

if __name__ == '__main__':
    generate_code()
