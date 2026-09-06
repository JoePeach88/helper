import inspect


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
