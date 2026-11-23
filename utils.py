import inspect
import math
import hashlib
from pathlib import Path


def get_caller_module_name():
    stack = inspect.stack()
    if len(stack) < 3:
        return None, None
    try:
        caller_info = stack[2]
        caller_frame = caller_info.frame
        module = inspect.getmodule(caller_frame)
        if module is None:
            return None, None
        qualname = getattr(
            caller_frame.f_code,
            "co_qualname",
            caller_info.function,
        )
        return getattr(module, "__file__", None), qualname

    finally:
        del stack


def format_bytes(size_bytes):
    if size_bytes == 0:
        return "0B"
    from messages import BASE_LIBRARY
    units = BASE_LIBRARY['units']
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {units[i]}"


def get_dir_size(path='.'):
    root_directory = Path(path)
    return sum(f.stat().st_size for f in root_directory.rglob('*') if f.is_file())


def get_file_sha256(file: str):
    sha256_hash = hashlib.sha256()
    with open(file, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
