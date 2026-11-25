import re
import inspect
import sys
import pyfiglet
import ctypes
import lief
from datetime import datetime
from pathlib import Path
from difflib import get_close_matches
from env import (
    __release__, __version__, __version_name__, __product_name__, IS_ADMIN, SYSTEM_PLATFORM, LESS_LINES, LOGS_LEVELS, LOGS_PATH,
    PIP_PROXY, DEBUG, LOCALE, ENCODING, EMOJI_ENABLED, UNPACK_FILE_FILTER, HRDRM_ENABLED, GC_ENABLED,
    MD_RETURN_OUTPUT, UPDATE_CHECK, lang, MEASURE_TIME, CACHE_ENABLED, CACHE_LOCATION, PIP_PARAMS
)
from helpers import _find_module, _find_settings, _prepare_helper, _find_disabled_module, list_helpers, Helper, HELPERS_DIR, BASE_LIBRARY
from messages import print_message, render_md, less, WARNING, ERROR


def _get_attribute(obj, name, helper, full_output):
    try:
        return getattr(obj, name)
    except AttributeError:
        print_message(f"Object {obj} has no method like '{name}'.", WARNING)
        obj_methods = obj.__dir__()
        closest_matches = get_close_matches(name, [method for method in dir(obj.helper if 'helper' in obj_methods else obj) if not method.startswith('_')], n=3, cutoff=0.6)
        if closest_matches:
            matches = "\n\t".join(closest_matches)
            print(lang.get(key='methods', name=name, matches=matches))
            if 'helper' in dir(obj):
                print(lang.get(key='manual'))
                _print_help(obj.helper, helper, full_output)
            elif 'helper' in dir(helper) or obj.__doc__:
                print(lang.get(key='manual'))
                _print_help(obj, helper, full_output)
        return None


def _print_help(obj, helper = None, full_output: bool = True):
    doc = prepare_doc(obj, helper)
    if doc:
        doc = render_md(doc)
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


def _call_function(helper, function_name, function, args_list, kwargs_list, aliases, full_output):
    if not callable(function) or isinstance(function, type):
        _handle_non_callable(helper, function_name, function, args_list, kwargs_list, aliases)
        return 1

    if function_name in helper.module.__module_disabled_methods__ or function is None or function_name.startswith('_'):
        print_message(f"Helper {helper} has no method like '{function_name}'.", WARNING)
        _print_help(helper.helper, helper, full_output)
        return 1

    if 'help' in args_list or 'help' in kwargs_list:
        _print_help(function, helper, full_output)
        return 1

    args, kwargs = args_list, kwargs_list
    has_mandatory = _has_mandatory_params(function)

    if 'no_less' in kwargs:
        full_output = True
        kwargs.pop('no_less')

    if 'not_pretty' in kwargs:
        kwargs.pop('not_pretty')
        kwargs.update({'pretty': False})

    if not args and not kwargs and has_mandatory:
        _print_help(function, helper, full_output)
        return 1

    for alias, aliases_list in aliases.items():
        if function_name in aliases_list:
            function_name = alias
            break

    try:
        print_message(f"Executing helper '{helper}' method {function} with args: {args} and kwargs: {kwargs}")
        output = function(*args, **kwargs)
        if output:
            if isinstance(output, str):
                if MD_RETURN_OUTPUT:
                    output = render_md(output)
                if full_output:
                    print(output)
                else:
                    less(output)
            else:
                print(output)
    except Exception as e:
        print_message(f"An error occurred while calling '{function_name}' in helper '{helper}': {e}", ERROR, True)
        return 1


def _call_dll_function(method, args, kwargs):
    TYPE_MAP = {
        'int': ctypes.c_int,
        'float': ctypes.c_double,
        'str': ctypes.c_char_p,
        'bytes': ctypes.c_char_p,
        'bool': ctypes.c_bool,
    }

    def _detect_arg_type(arg: str):
        from utils import is_bool, is_bytes, is_float, is_int
        if is_bool(arg)[0]:
            return 'bool', is_bool(arg)[1]
        elif is_bytes(arg)[0]:
            return 'bytes', is_bytes(arg)[1]
        elif is_float(arg)[0]:
            return 'float', is_float(arg)[1]
        elif is_int(arg)[0]:
            return 'int', is_int(arg)[1]
        else:
            return 'str'

    def _prepare_dll_args(args: list):
        inferred_argtypes = []
        c_args = []
        for arg in args:
            arg_type, arg_value = _detect_arg_type(arg)
            inferred_argtypes.append(TYPE_MAP.get(arg_type, ctypes.c_void_p))
            c_args.append(arg_value.encode('utf-8') if arg_type == 'str' else arg_value)
        return c_args, inferred_argtypes

    try:
        dll_path = Path(__file__).parent / f'helpers/dlls/{method}.dll'
        if not dll_path.exists():
            print_message(lang.get(function='detect_handler', key='unknown_method', method=method), WARNING, True)
            return
        print_message('Creating CDLL and parsing functions in dll file...')
        libc = ctypes.CDLL(str(dll_path))
        binary = lief.parse(str(dll_path))
        print_message(f'CDLL: {libc}.')
        print_message(f'Parse object: {binary}.')
        exported_functions = [func.name for func in binary.exported_functions if re.search(r"^[a-zA-Z0-9]\w*", func.name)]
        print_message(f'Parsed functions ({len(exported_functions)}): {exported_functions}.')
        full_output = kwargs.pop('no_less', False)
        return_type = kwargs.pop('return_type', int)

        if not args:
            md = render_md(lang.get(function='detect_handler', key='dll_functions', dll=method, count=len(exported_functions), methods='\n\n* '.join(exported_functions)))
            if full_output:
                print(md)
            else:
                less(md)
            return

        function = args[0]
        raw_args = args[1:]

        if function in exported_functions:
            print_message(f"Function '{function}' found in dll, executing it...")
            c_args, inferred_argtypes = _prepare_dll_args(raw_args)
            function_obj = getattr(libc, function)
            function_obj.restype = TYPE_MAP.get(return_type, ctypes.c_int)
            function_obj.argtypes = inferred_argtypes
            print_message(f"Executing '{function_obj}' with args types: {inferred_argtypes}.")
            print_message(f"Executing '{function_obj}' with args: {c_args}.")
            raw_output = function_obj(*c_args)

            if raw_output is not None:
                print_message(f"Decoding raw output: '{raw_output}'.")
                output = raw_output.decode('utf-8') if isinstance(raw_output, bytes) else raw_output
                if isinstance(output, str):
                    if MD_RETURN_OUTPUT:
                        output = render_md(output)
                    if full_output:
                        print(output)
                    else:
                        less(output)
                else:
                    print(output)
        else:
            print_message(lang.get(function='detect_handler', key='unknown_method', method=function), WARNING, True)

    except Exception as e:
        print_message(f"DLL execution error: {e}.", ERROR, force=True)


def _handle_non_callable(helper, function_name, obj, args_list, kwargs_list, aliases, full_output):
    if not args_list:
        _print_help(obj, helper, full_output)
        return

    nested_name = args_list[0].lower()
    nested_args = args_list[1:]

    for alias, aliases_list in aliases.items():
        if nested_name in aliases_list:
            nested_name = alias
            break

    if nested_name == 'help' or nested_name == '--help':
        _print_help(obj, helper, full_output)
        return

    nested_object = _get_attribute(helper, function_name, helper, full_output)
    if callable(nested_object):
        nested_object = nested_object()
    if not nested_object:
        return
    nested_function = _get_attribute(nested_object, nested_name, helper, full_output)

    if nested_function is not None:
        _call_function(helper, nested_name, nested_function, nested_args, kwargs_list, aliases)


def detect_handler(method, args, kwargs):
    if UPDATE_CHECK:
        try:
            print_message("Initiating builtin 'core' helper to check core updates.")
            core_prepared = _prepare_helper('core')
            core_module = _find_module('helpers.core')
            core_settings = _find_settings('core')
            core_helper = getattr(core_module, core_prepared)
            core_helper = core_helper(core_settings)
            print_message("Helper 'core' initiated.")
        except Exception as e:
            print_message(f"Helper 'core' cannot be initiated cause something went wrong: {e}.", ERROR)
            return 1
        updates = core_helper.update.check(pretty = False)
        if updates:
            print(render_md(lang.get(key='new_version', version = updates[0]['remote_version'])))
    is_helper = _find_module(f'helpers.{method}')
    is_disabled = _find_disabled_module(f'helpers.{method}')
    full_output = 'no_less' in args or 'no_less' in kwargs
    if is_disabled:
        print_message(lang.get(key='disabled', method = method), WARNING, force=True)
        return 1
    if is_helper:
        print_message(f"Found helper handler at {is_helper}.")
        return helper_handler(method, args, kwargs, full_output)
    elif method in ['howto']:
        with open(HELPERS_DIR / 'README.md', encoding='utf-8') as readme_file:
            readme_content = render_md(readme_file.read())
            if 'no_less' in args or 'no_less' in kwargs:
                print(readme_content)
            else:
                less(readme_content)
    elif method in ['debug', '-d', '--debug']:
        debug_handler()
    elif method in ['version', '-v', '--version']:
        version_handler()
    elif method in ['changelog', 'changes']:
        if len(args) == 1 and not ('dev' in args[0] or 'stable' in args[0]):
            args.append('stable')
        global_version = re.sub(r'\.\d+\.\d+', '.x.x', __version__)
        if args:
            global_version = re.sub(r'\.\d+\.\d+', '.x.x', args[0])
        changelog = Path(__file__).parent / (f"changelogs/{global_version}/{__version__}-{__release__}.md" if not args else f"changelogs/{global_version}/{'-'.join(args)}.md")
        if changelog.exists():
            with open(changelog, encoding='utf-8') as changelog_file:
                changes_content = render_md(changelog_file.read())
                if 'no_less' in args or 'no_less' in kwargs:
                    print(changes_content)
                else:
                    less(changes_content)
    elif method in ['selfcheck']:
        print_message("Initiating builtin 'core' helper to initialize selfcheck.")
        core_prepared = _prepare_helper('core')
        core_module = _find_module('helpers.core')
        core_settings = _find_settings('core')
        core_helper = getattr(core_module, core_prepared)
        core_helper = core_helper(core_settings)
        print_message("Helper 'core' initiated.")
        print(core_helper.selfcheck())
    elif method in ['help', '--help'] or method is None:
        _print_help(lang.get(function='description'), full_output=full_output)
    elif method in ['helpers', 'list', 'ls']:
        try:
            print_message("Initiating builtin 'modules' helper to list all available helpers.")
            modules_prepared = _prepare_helper('modules')
            modules_module = _find_module('helpers.modules')
            modules_settings = _find_settings('modules')
            modules_helper = getattr(modules_module, modules_prepared)
            modules_helper = modules_helper(modules_settings)
            print_message("Helper 'modules' initiated.")
        except Exception as e:
            print_message(f"Helper 'core' cannot be initiated cause something went wrong: {e}.", ERROR)
            return 1
        print(modules_helper.ls(all=True))
    else:
        _call_dll_function(method, args, kwargs)


def prepare_doc(obj, helper = None):
    documentation = re.sub(
        r" \s+",
        "",
        obj if isinstance(obj, str)
        else (re.sub(r"\n\n", "\n", obj.__doc__) if obj.__doc__ else '')
    )
    documentation = documentation.strip()
    if (not callable(obj) or isinstance(obj, type)) and not isinstance(obj, str):
        module_name = obj.__module__.split('.')[-1]
        documentation = (lang.get(inspect.getfile(obj.__class__), obj.__class__.__qualname__) or documentation) + '\n'
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
                from types import MethodType
                if isinstance(method_object, MethodType):
                    formatted_methods.append(lang.get(key='aliases', method = method, alias = ', '.join(alias)))
                else:
                    formatted_methods.append(lang.get(key='aliases_module', method = method, alias = ', '.join(alias)))
        if not has_public_methods:
            return
        documentation += lang.get(key='doc', module_name = module_name, module_formatted_methods = f'\n{module_name} '.join(formatted_methods))
    else:
        if not isinstance(obj, str) and obj:
            doc = lang.get(helper.module.__file__, obj.__qualname__, return_description=True) or obj.__doc__
            if doc:
                documentation = re.sub(r" \s+", "", doc).strip()
            else:
                return None
        else:
            documentation = obj
    return documentation if documentation else None


def helper_handler(helper_name, args, kwargs, full_output):
    helper = Helper(helper_name)
    aliases = helper.module.__methods_static_aliases__
    defined_aliases = helper.aliases
    if defined_aliases:
        aliases.update(defined_aliases)

    if not args or args[0] in ('help', '__init__', None, '--help'):
        _print_help(helper.helper, helper, full_output)
        return 0

    function_name = args[0].lower()
    function_args = args[1:]
    function_kwargs = kwargs

    for alias, aliases_list in aliases.items():
        if function_name in aliases_list:
            function_name = alias
            break

    function = _get_attribute(helper, function_name, helper, full_output)
    if not function:
        return 1

    start_time = datetime.now()
    exit_code = _call_function(helper, function_name, function, function_args, function_kwargs, aliases, full_output)
    end_time = datetime.now()
    if MEASURE_TIME:
        print(lang.get(measure_time=end_time - start_time))
    return exit_code


def version_handler():
    version = __version__
    version_name = __version_name__
    release = __release__
    helpers = list_helpers()
    print(pyfiglet.figlet_format(f"{__product_name__} CLI"))
    print(lang.get(version = version, version_name = version_name, release = release))
    for helper in helpers:
        print(f"{helper['name']}: {helper['version']} --- ({Path(helper['file']).parent.as_posix()}) {'[builtin] 'if helper['builtin'] else ''}{'--- (dev) 'if helper['dev'] else ''}")


def debug_handler():
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
        sys.exit(1)
        return

    selfcheck = core_helper.selfcheck()

    print('--------------------------\n')
    print(lang.get(key='before_selfcheck', platform=SYSTEM_PLATFORM, locale=LOCALE, encoding=ENCODING, version=sys.version, executable=Path(sys.executable).as_posix(), cache_enabled=BASE_LIBRARY['yes' if CACHE_ENABLED else 'no'], cache_location=CACHE_LOCATION))
    print(selfcheck)
    print(lang.get(key='after_selfcheck', 
                   is_admin=BASE_LIBRARY['yes' if IS_ADMIN else 'no'], less_lines=LESS_LINES, logs_levels=LOGS_LEVELS, logs_path=LOGS_PATH, pip_proxy=PIP_PROXY, pip_params=PIP_PARAMS,
                   debug=BASE_LIBRARY['yes' if DEBUG else 'no'], emoji_enabled=BASE_LIBRARY['yes' if EMOJI_ENABLED else 'no'], unpack_file_filter=UNPACK_FILE_FILTER, 
                   hrdrm_enabled=BASE_LIBRARY['yes' if HRDRM_ENABLED else 'no'], gc_enabled=BASE_LIBRARY['yes' if GC_ENABLED else 'no']), '\n')

    print('--------------------------\n')
    print(lang.get(key='modules_settings'))
    core_helper.config.ls()

    print('\n--------------------------\n')
    print(lang.get(key='cli_info'))
    version_handler()
    print('\n--------------------------\n')
