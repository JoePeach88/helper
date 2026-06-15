# CLI DOCUMENTATION BLOCK START #
"""
helper version - to view information about helper cli version and it installed modules.
helper debug - to view cli debug information.
helper modules ls - to view all available modules.
helper <module_name> man - to view manual for helper module.
helper <module_name> help - to view help information for module, show all available methods and its aliases.
"""
#  CLI DOCUMENTATION BLOCK END  #

import re
import inspect
import sys
from pathlib import Path
from difflib import get_close_matches
from env import __release__, __version__, __version_name__, __product_name__, IS_ADMIN, SYSTEM_PLATFORM, LESS_LINES, LOGS_LEVELS, LOGS_PATH, PIP_PROXY, DEBUG, EMOJI_ENABLED, UNPACK_FILE_FILTER, HRDRM_ENABLED, PIP_BREAK_SYSTEM_PACKAGES, GC_ENABLED
from helpers import _find_module, _find_settings, _prepare_helper, _find_disabled_module, list_helpers, Helper
from libs.messages import print_message, less, WARNING, ERROR


def _get_attribute(obj, name, helper):
    try:
        return getattr(obj, name)
    except AttributeError:
        print_message(f"Object {obj} has no method like '{name}'.", WARNING, True)
        obj_methods = obj.__dir__()
        closest_matches = get_close_matches(name, [method for method in dir(obj.helper if 'helper' in obj_methods else obj) if not method.startswith('_')], n=3, cutoff=0.6)
        if closest_matches:
            matches = "\n\t".join(closest_matches)
            print(f"Method '{name}' not found, the most similar methods are:\n\t{matches}")
            if 'helper' in dir(obj):
                print("\n\nAvailable manual:")
                _print_help(obj.helper, helper)
            elif 'helper' in dir(helper) or obj.__doc__:
                print("\n\nAvailable manual:")
                _print_help(obj, helper)
        return None


def _print_help(obj, helper = None, full_output: bool = True):
    if obj.__doc__ or isinstance(obj, str):
        doc = None
        if obj.__doc__:
            doc = prepare_doc(obj, helper)
        else:
            doc = obj
        if doc:
            if full_output:
                print(doc)
            else:
                less(doc)
        else:
            print_message(f"Documentation string not found for object {obj} in helper {helper}.", WARNING)


def _has_mandatory_params(function):
    sig = inspect.signature(function)
    return any(
        param.default == inspect.Parameter.empty and param.name not in ['self', 'args', 'kwargs']
        for param in sig.parameters.values()
    )


def _call_function(helper, function_name, function, args_list, aliases):
    if not callable(function) or isinstance(function, type):
        _handle_non_callable(helper, function_name, function, args_list, aliases)
        return

    if function_name in helper.module.__module_disabled_methods__ or function is None or function_name.startswith('_'):
        print_message(f"Helper {helper} has no method like '{function_name}'.", WARNING, True)
        _print_help(helper.helper, helper)
        return

    if 'help' in args_list:
        _print_help(function, helper)
        return

    args, kwargs = prepare_arguments(*args_list)
    has_mandatory = _has_mandatory_params(function)

    full_output = False
    if 'no_less' in kwargs:
        full_output = True
        kwargs.pop('no_less')

    if 'not_pretty' in kwargs:
        kwargs.pop('not_pretty')
        kwargs.update({'pretty': False})

    if not args and not kwargs and has_mandatory:
        _print_help(function, helper, full_output)
        return

    for alias, aliases_list in aliases.items():
        if function_name in aliases_list:
            function_name = alias
            break

    try:
        print_message(f"Executing helper '{helper}' method {function} with args: {args} and kwargs: {kwargs}")
        output = function(*args, **kwargs)
        if output:
            if isinstance(output, str):
                if full_output:
                    print(output)
                else:
                    less(output)
            else:
                print(output)
    except Exception as e:
        print_message(f"An error occurred while calling '{function_name}' in helper '{helper}': {e}", ERROR, True)


def _handle_non_callable(helper, function_name, obj, args_list, aliases):
    if not args_list:
        _print_help(obj, helper)
        return

    nested_name = args_list[0].lower()
    nested_args = args_list[1:]

    for alias, aliases_list in aliases.items():
        if nested_name in aliases_list:
            nested_name = alias
            break

    if nested_name == 'help':
        _print_help(obj, helper)
        return

    nested_object = _get_attribute(helper, function_name, helper)
    if callable(nested_object):
        nested_object = nested_object()
    if not nested_object:
        return
    nested_function = _get_attribute(nested_object, nested_name, helper)

    if nested_function is not None:
        _call_function(helper, nested_name, nested_function, nested_args, aliases)


def prepare_arguments(*args):
    new_args = []
    kwargs = {}
    i = 0
    while i < len(args):
        if args[i].startswith('--'):
            step = 2
            key = args[i].lstrip('--')
            key = key.replace('-', '_')
            value = args[i + 1] if i + 1 < len(args) else None
            if value and value.startswith('--'):
                value = None
                step = 1
            kwargs[key] = True if value is None else value # key-arguments without value (None) stored as True
            i += step
        else:
            if args[i] not in new_args:
                new_args.append(args[i])
            i += 1
    return new_args, kwargs


def detect_handler(method, arguments):
    is_helper = _find_module(f'helpers.{method}')
    is_disabled = _find_disabled_module(f'helpers.{method}')
    if is_disabled:
        print_message(f"Module '{method}' is disabled.", WARNING, force=True)
        return
    if is_helper:
        print_message(f"Found helper handler at {is_helper}.")
        helper_handler(method, arguments)
    elif method in ['debug', '-d', '--debug']:
        debug_handler()
    elif method in ['version', '-v', '--version']:
        version_handler()
    elif method in ['help'] or method is None:
        if __doc__:
            _print_help(__doc__)
    else:
        print_message(f"Unknown keyword '{method}'.", WARNING, True)


def prepare_doc(obj, helper = None):
    documentation = re.sub(r" \s+", "", obj if isinstance(obj, str) else re.sub('\n\n', '\n', obj.__doc__))
    documentation = documentation.strip()
    if (not callable(obj) or isinstance(obj, type)) and not isinstance(obj, str):
        module_name = obj.__module__.split('.')[-1]
        methods = sorted(dir(obj))
        subclasses = []
        if isinstance(obj, object) and obj.__class__.__name__ != f"{module_name}Helper":
            if hasattr(obj, "__mro__"):
                for base in obj.__mro__:
                    base_splitted = base.__qualname__.split('.')[1::] # Unset module name from qualname string, for example 'passvaultHelper.hash.sha256' -> ['hash', 'sha256']
                    if base.__name__ != 'object':
                        subclasses.extend(base_splitted)
            if hasattr(obj, "__name__"):
                if obj.__name__ in subclasses:
                    subclasses.remove(obj.__name__)
                module_name = f"{module_name} {' '.join(subclasses)} {obj.__name__}" if subclasses else f"{module_name} {obj.__name__}"
            else:
                if obj.__class__.__name__ in subclasses:
                    subclasses.remove(obj.__class__.__name__)
                module_name = f"{module_name} {' '.join(subclasses)} {obj.__class__.__name__}" if subclasses else f"{module_name} {obj.__class__.__name__}"
        formatted_methods = []
        if helper:
            aliases = helper.module.__methods_static_aliases__
        else:
            aliases = {}

        has_public_methods = False
        for method in methods:
            method_object = getattr(obj, method)
            if not method.startswith('_') and not method in helper.module.__module_disabled_methods__ and (callable(method_object) or not isinstance(method_object, (list, str, dict, int, float, bool, tuple, set, type(helper.helper), type(None)))):
                has_public_methods = True
                alias = aliases.get(method, [])
                formatted_methods.append(f"{method}\nAliases: {', '.join(alias)}\n")
        if not has_public_methods:
            return
        documentation += f'\nAvailable methods:\n\n{module_name} ' + f'\n{module_name} '.join(formatted_methods)
    return documentation if documentation else None


def helper_handler(helper_name, arguments):
    helper = Helper(helper_name)
    aliases = helper.module.__methods_static_aliases__
    defined_aliases = helper.aliases
    if defined_aliases:
        aliases.update(defined_aliases)

    if not arguments or arguments[0] in ('help', '__init__', None):
        _print_help(helper.helper, helper)
        return

    function_name = arguments[0].lower()
    function_args = arguments[1:]

    for alias, aliases_list in aliases.items():
        if function_name in aliases_list:
            function_name = alias
            break

    function = _get_attribute(helper, function_name, helper)
    if not function:
        return

    _call_function(helper, function_name, function, function_args, aliases)


def version_handler():
    version = __version__
    version_name = __version_name__
    release = __release__
    helpers = list_helpers()
    print(f'{__product_name__} INFO')
    print(f'CLI Version: {version} [{version_name}] ({release})')
    print(f'\nHelpers Modules:')
    for helper in helpers:
        print(f"{helper['name']}: {helper['version']} --- ({Path(helper['file']).parent}) {'[builtin] 'if helper['builtin'] else ''}{'--- (dev) 'if helper['dev'] else ''}")


def debug_handler():
    EMOJI_ENABLED = False
    try:
        print_message("Initiating builtin 'core' helper to retrieve modules settings.")
        core_prepared = _prepare_helper('core')
        core_module = _find_module('helpers.core')
        core_settings = _find_settings('core')
        core_helper = getattr(core_module, core_prepared)
        core_helper = core_helper(core_settings)
        print_message("Helper 'core' initiated.")
    except Exception as e:
        print_message(f"Helper 'core' cannot be initiated cause something went wrong: {e}.", ERROR)
        return

    print('--------------------------\n')
    print('System Information:\n')
    print(f'System: {SYSTEM_PLATFORM}')
    print("Python Version:", sys.version)
    print("Python Executable Path:", sys.executable)
    print(f'Is admin: {IS_ADMIN}')
    print(f'Less lines: {LESS_LINES}')
    print(f'Log file logs levels: {LOGS_LEVELS}')
    print(f'Logs path: {LOGS_PATH}')
    print(f'Pip proxy: {PIP_PROXY}')
    print(f'Pip break_system_packages option: {PIP_BREAK_SYSTEM_PACKAGES}')
    print(f'Debug mode: {DEBUG}')
    print(f'Emoji enabled: {EMOJI_ENABLED}')
    print(f'Unpack file filter: {UNPACK_FILE_FILTER}')
    print(f'HRDRM enabled: {HRDRM_ENABLED}')
    print(f'GC enabled: {GC_ENABLED}\n')

    print('--------------------------\n')
    print('Modules settings:\n')
    core_helper.config.ls()

    print('\n--------------------------\n')
    print('CLI Information:\n')
    version_handler()
    print('\n--------------------------\n')
