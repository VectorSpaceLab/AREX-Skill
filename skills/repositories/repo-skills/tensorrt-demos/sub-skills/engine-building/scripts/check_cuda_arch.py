#!/usr/bin/env python3
"""Read-only CUDA compute-capability probe for plugin build planning.

It uses ctypes against the CUDA Driver API when available. It never compiles,
loads a repository plugin, changes environment state, or writes files.
"""

from __future__ import print_function

import argparse
import ctypes
import sys


CUDA_SUCCESS = 0
CUDA_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR = 75
CUDA_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR = 76


def load_cuda():
    names = ("libcuda.so.1", "libcuda.so", "libcuda.dylib", "nvcuda.dll")
    for name in names:
        try:
            return ctypes.CDLL(name), name
        except OSError:
            pass
    return None, None


def error_text(cuda, code):
    getter = getattr(cuda, "cuGetErrorString", None)
    if getter is None:
        return "CUDA error code %d" % code
    text = ctypes.c_char_p()
    if getter(code, ctypes.byref(text)) == CUDA_SUCCESS and text.value:
        return text.value.decode("utf-8", "replace")
    return "CUDA error code %d" % code


def main():
    parser = argparse.ArgumentParser(
        description="Report visible CUDA device compute capabilities without mutation."
    )
    parser.add_argument(
        "--require",
        help="require one architecture string, such as 80; exit 1 if absent",
    )
    args = parser.parse_args()

    cuda, library = load_cuda()
    if cuda is None:
        print("WARN: CUDA Driver API library not found", file=sys.stderr)
        return 1 if args.require else 0

    # Declare only the API calls used here. CUDA Driver functions return CUresult.
    cuda.cuInit.argtypes = [ctypes.c_uint]
    cuda.cuInit.restype = ctypes.c_int
    cuda.cuDeviceGetCount.argtypes = [ctypes.POINTER(ctypes.c_int)]
    cuda.cuDeviceGetCount.restype = ctypes.c_int
    cuda.cuDeviceGet.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.c_int]
    cuda.cuDeviceGet.restype = ctypes.c_int
    cuda.cuDeviceGetAttribute.argtypes = [
        ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.c_int
    ]
    cuda.cuDeviceGetAttribute.restype = ctypes.c_int

    result = cuda.cuInit(0)
    if result != CUDA_SUCCESS:
        print("WARN: cuInit failed: %s" % error_text(cuda, result), file=sys.stderr)
        return 1 if args.require else 0
    count = ctypes.c_int()
    result = cuda.cuDeviceGetCount(ctypes.byref(count))
    if result != CUDA_SUCCESS:
        print("WARN: cuDeviceGetCount failed: %s" % error_text(cuda, result), file=sys.stderr)
        return 1 if args.require else 0

    architectures = []
    print("CUDA driver library: %s" % library)
    print("CUDA devices: %d" % count.value)
    for ordinal in range(count.value):
        device = ctypes.c_int()
        result = cuda.cuDeviceGet(ctypes.byref(device), ordinal)
        if result != CUDA_SUCCESS:
            print("WARN: device %d lookup failed: %s" % (ordinal, error_text(cuda, result)), file=sys.stderr)
            continue
        major = ctypes.c_int()
        minor = ctypes.c_int()
        major_result = cuda.cuDeviceGetAttribute(
            ctypes.byref(major), CUDA_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MAJOR, device
        )
        minor_result = cuda.cuDeviceGetAttribute(
            ctypes.byref(minor), CUDA_DEVICE_ATTRIBUTE_COMPUTE_CAPABILITY_MINOR, device
        )
        if major_result != CUDA_SUCCESS or minor_result != CUDA_SUCCESS:
            print("WARN: device %d compute capability lookup failed" % ordinal, file=sys.stderr)
            continue
        arch = "%d%d" % (major.value, minor.value)
        architectures.append(arch)
        print("device %d: compute_%s (sm_%s)" % (ordinal, arch, arch))

    unique = sorted(set(architectures))
    print("architectures: %s" % (" ".join(unique) if unique else "none"))
    if args.require and args.require not in unique:
        print("ERROR: required architecture %s is not visible" % args.require, file=sys.stderr)
        return 1
    return 0 if architectures or not args.require else 1


if __name__ == "__main__":
    raise SystemExit(main())
