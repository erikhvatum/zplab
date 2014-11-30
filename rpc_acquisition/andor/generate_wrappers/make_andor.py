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
# Authors: Zach Pincus, Erik Hvatum

try:
    from . import output_ctypes
except SystemError:
    import sys
    es = [
        'This script can not be run from within its own package. Try:',
        '\tcd ..',
        '\tpython3 -m generate_wrappers.make_andor'
    ]
    sys.stderr.write('\n'.join(es) + '\n')
    sys.stderr.flush()
    sys.exit(-1)

code = """
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
# Author: Zach Pincus

# Autogenerated by make_andor.py. All changes made to this file will be lost
# the next time make_andor.py is executed!
import ctypes
from .common import *
from .common import _at_errcheck

_at_core_lib = None
_at_util_lib = None
_at_camera_handle = None

_at_wchar_scratch = ctypes.create_unicode_buffer(255)

{}

def _setup_core_functions():
    {}

def _setup_util_functions():
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
int [_at_errcheck] AT_SetBool(AT_H Hndl, const AT_WC* Feature, AT_BOOL Bool);
int [_at_errcheck] AT_GetBool(AT_H Hndl, const AT_WC* Feature, AT_BOOL* Bool [output]);
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
int [_at_errcheck] AT_FinaliseUtilityLibrary()
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
    if _at_camera_handle is not None:
        return _at_core_lib.{}(_at_camera_handle, {})
    else:
        raise AndorError('Andor library not initialized')
'''

bool_wrapper = '''def {}({}):
    {}
    if _at_camera_handle is not None:
        return _at_core_lib.{}(_at_camera_handle, {}) != AT_FALSE
    else:
        raise AndorError('Andor library not initialized')
'''

string_wrapper = '''def {}({}):
    {}
    if _at_camera_handle is not None:
        _at_core_lib.{}(_at_camera_handle, {}, _at_wchar_scratch, _at_wchar_scratch._length_)
        return _at_wchar_scratch.value
    else:
        raise AndorError('Andor library not initialized')
'''

util_wrapper = '''def {}({}):
    {}
    return _at_util_lib.{}({})
'''

def indent(lines, amount=4, ch=' '):
    padding = amount * ch
    return ('\n'+padding).join(lines.split('\n'))

def generate_code(outfile):
    core_setup = []
    wrapper_funcs = []
    for proto in core_protos:
        function_name, in_args, out_args, func_code = output_ctypes.create_library_prototype(proto, '_at_core_lib', additional_defs)
        core_setup.append(func_code)
        if in_args and in_args[0][0] == 'Hndl' and function_name != 'AT_Close':
            # wrap the function in a helpful wrapper
            in_args = in_args[1:]
            if len(out_args) == 1 and out_args[0][0] in ('Bool', 'Readable', 'Writable', 'ReadOnly', 'Available', 'Implemented'):
                wrapper_text = bool_wrapper
            elif len(in_args) > 1 and in_args[-2][0] == 'String' and in_args[-1][0] == 'StringLength':
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
        function_name, in_args, out_args, func_code = output_ctypes.create_library_prototype(proto, '_at_util_lib', additional_defs)
        util_setup.append(func_code)
        if function_name not in ('AT_InitialiseUtilityLibrary', 'AT_FinaliseUtilityLibrary'):
            wrapper_text = util_wrapper
            wrapper_name = function_name[3:] # strip 'AT_'
            doc = '"""{}"""'.format(output_ctypes.construct_docstring(wrapper_name, in_args, out_args))
            if in_args:
                in_arg_names, in_arg_types = zip(*in_args)
                in_arg_names = ', '.join(in_arg_names)
            else:
                in_arg_names = ''
            wrapper_code = wrapper_text.format(wrapper_name, in_arg_names, indent(doc), function_name, in_arg_names)
            wrapper_funcs.append(wrapper_code)


    core_setup = '\n\n'.join(core_setup)
    wrapper_funcs = '\n'.join(wrapper_funcs)
    util_setup = '\n\n'.join(util_setup)
    output_code = code.format(wrapper_funcs, indent(core_setup), indent(util_setup))

    with open(outfile, 'w') as f:
        f.write(output_code)

if __name__ == '__main__':
    import pathlib
    generate_code(outfile=str(pathlib.Path(__file__).parent.parent / 'wrapper.py'))
