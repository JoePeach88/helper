import os
import importlib.util
import sys
import re
import subprocess
from pathlib import Path
from env import loader, config_file, SYSTEM_PLATFORM, HRDRM_ENABLED, PIP_PROXY, PIP_BREAK_SYSTEM_PACKAGES, get_system_based_value


HELPERS_DIR = Path(__file__).resolve().parent
HELPERS_PARENT_DIR = HELPERS_DIR.parent
if str(HELPERS_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_PARENT_DIR))
from libs.messages import print_message, print_choices, print_choice, render_code, render_md, WARNING, ERROR, SUCCESS, INFO


def install_requirements(module_name: str, requirements_file: str):
    try:
        command = [
            sys.executable,
            '-m',
            'pip',
            'install',
            '-r',
            requirements_file,
        ]
        if PIP_BREAK_SYSTEM_PACKAGES:
            command.extend(['--break-system-packages'])
        if PIP_PROXY:
            command.extend(['--proxy', PIP_PROXY])
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

        for line in process.stdout:
            print_message(line)

        process.wait()
        print_message(f"Successfully installed packages from {requirements_file} for module '{module_name}'.")

    except subprocess.CalledProcessError as e:
        print_message(f"Error during package installation: {e.stderr}", ERROR)
        return
    except FileNotFoundError:
        print_message(f"Error: The file '{requirements_file}' was not found.", ERROR)
        return
    except Exception as e:
        print_message(f"Error during package installation: {e}", ERROR)
        return


def _load_modules_from_directory(directory_path: str, package: str = None, force: bool = True, install_reqs: bool = False):
    module_files = [dir for dir in Path(os.path.join(directory_path)).iterdir() if Path(dir).name != 'helpers' and Path(dir).is_dir()]
    for module in module_files:
        if Path(module).name.startswith('_'):
            module_files.remove(module)

    modules = []
    disabled_modules = []
    settings = []
    for file_path in module_files:
        file_name = os.path.basename(file_path)
        module_name = os.path.splitext(file_name)[0]

        if module_name == "__init__":
            continue

        module_settings = {}

        loader.config.read(config_file)
        for key in loader.config.keys():
            if re.match(f'^{module_name}[:]?.*$', key):
                module_settings = dict(dict(loader.config).get(key, {}).items())
                settings.append({key: module_settings})
        
        module_enabled = 'True'
        for setting in settings:
            module_enabled = setting.get(module_name, {}).get('enabled', 'True')
        try:
            if package:
                full_module_name = f"{package}.{module_name}"
                module = importlib.import_module(full_module_name)
            else:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

            if module_enabled == 'True':
                if 'all' in module.__module_compatibility__ or SYSTEM_PLATFORM in module.__module_compatibility__:
                    if module not in modules:
                        modules.append(module)    
                    if module.__module_status__ in ['development', 'dev', 'testing', 'test']:
                        if force:
                            print_message(f"Module '{module_name}' loaded, but may not work correctly because it is under development.", WARNING)
                    elif module.__module_status__ in ['deprecated', 'unstable', 'unsupported']:
                        if force:
                            print_message(f"Module '{module_name}' loaded, but may not work correctly because it is not supported anymore, better way is delete it via command 'modules rm {module_name}'.", WARNING)
                    elif module.__module_status__ in ['stable', 'supported', 'prod']:
                        if force:
                            print_message(f"Loaded module: '{module_name}'")
                    else:
                        if force:
                            print_message(f"Module '{module_name}' loaded, but have unknown stability status.", WARNING)
                else:
                    if module not in disabled_modules:
                        disabled_modules.append(module)
                    if force:
                        print_message(f"Module '{module_name}' not supported by this platform ({SYSTEM_PLATFORM}), module not loaded.", WARNING)
            else:
                if module not in disabled_modules:
                    disabled_modules.append(module)

        except ModuleNotFoundError:
            reqs_path = Path(file_path) / 'requirements.txt'
            if reqs_path.exists():
                if install_reqs:
                    if force:
                        print_message(f"Module was not loaded correctly, cause some dependencies was not found, installing packages from module`s '{module_name}' requirements.txt...", WARNING)
                    install_requirements(module_name, reqs_path)
                    return _load_modules_from_directory(directory_path, package, install_reqs=install_reqs)
                else:
                    if force:
                        print_message(f"Module '{module_name}' not loaded cause it missing packages from requirements and HRDRM is disabled.", WARNING)
            else:
                if force:
                    print_message(f"Cannot load module '{module_name}' cause it missing some packages and cannot be resolved via `helper requirements dynamic resolve method (HRDRM)`, please generate requirements manually via modules renderreq {module_name} and then execute helper CLI.", WARNING)

        except AttributeError:
            if module in modules:
                modules.remove(module)
            print_message(f"Module '{module_name}' not loaded cause some required helper attributes not found, suggesting it`s not a helper module.", WARNING)

        except Exception as e:
            if force:
                print_message(f"Error loading module '{module_name}': {e}", ERROR)

    return modules, disabled_modules, settings


# To bypass double load through dynamic module loader
if __name__ == HELPERS_DIR.name:
    MODULES, DISABLED_MODULES, SETTINGS = _load_modules_from_directory(HELPERS_DIR, package=HELPERS_DIR.name, install_reqs=HRDRM_ENABLED)


def _find_module(module_name: str):
    for module in MODULES:
        if module.__name__ == module_name:
            return module
        
def _find_disabled_module(module_name: str):
    for module in DISABLED_MODULES:
        if module.__name__ == module_name:
            return module


def _find_settings(module_name: str):
    settings = {}
    for module_settings in SETTINGS:
        if re.match(f'^{module_name}[:]?.*$', list(dict(module_settings).keys())[0]):
            print_message(f"Found user defined settings for '{module_name}'.")
            settings.update({list(dict(module_settings).keys())[0]: module_settings.get(list(dict(module_settings).keys())[0], {})})
    return settings


def _find_aliases(module_name: str):
    for module_settings in SETTINGS:
        if module_settings.get(f'{module_name}:aliases'):
            print_message(f"Found user defined aliases for '{module_name}'.")
            aliases = {}
            for key, value in module_settings.get(f'{module_name}:aliases', {}).items():
                aliases[key] = eval(value)
            return aliases


def _prepare_helper(helper: str):
    helper = re.sub(r'[^a-zA-Z0-9]', '', helper)
    return '{helper}Helper'.format(helper=helper)


def list_helpers():
    modules_list = []
    for module in MODULES:
        modules_list.append({'module': module.__name__, 'name': module.__module_name__, 'author': module.__module_author__, 'version': module.__module_version__, 
                             'link': module.__module_link__, 'file': module.__file__, 'builtin': ('core' in module.__module_category__ or 'builtin' in module.__module_category__) and module.__module_link__ is None, 'dev': 'dev' == module.__module_status__})
    return modules_list


class Helper:
    """
    Module to work with Helpers.
    """
    def __init__(self, helper: str):
        self.helper = None
        self.module = None
        self.aliases = None
        try:
            helper_init = _prepare_helper(helper)
            helper_mod = _find_module(f'helpers.{helper}')
            if helper_mod:
                helper_settings = _find_settings(helper)
                self.module = helper_mod
                self.aliases = _find_aliases(helper)
                self.helper = getattr(helper_mod, helper_init)
                self.helper = self.helper(helper_settings)
                print_message(f"Helper '{helper}' initialized with settings '{helper_settings}'.")
            else:
                print_message(f"Specified helper '{helper}' not found.", ERROR)
        except Exception as e:
            print_message(f"Failed to initialize helper '{helper}': {e}", ERROR)

    def version(self):
        return f"{self.module.__module_name__}: {self.module.__module_version__}"

    def man(self):
        readme = Path(self.module.__file__).parent / 'README.md'
        helper_name = Path(self.module.__file__).parent.stem
        if readme.exists():
            with open(readme, encoding='utf-8') as readme_file:
                return render_md(readme_file.read())
        return f"Module '{helper_name}' has no available manual."

    def requirements(self):
        reqs = Path(self.module.__file__).parent / 'requirements.txt'
        helper_name = Path(self.module.__file__).parent.stem
        if reqs.exists():
            with open(reqs, encoding='utf-8') as reqs_file:
                return f"Module '{helper_name}' requirements:\n{reqs_file.read().strip()}"
        return f"Module '{helper_name}' has no available requirements."

    def __getattr__(self, name):
        return getattr(self.helper, name)
