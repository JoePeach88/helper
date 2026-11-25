import importlib.util
import sys
import re
import subprocess
from pathlib import Path
from env import loader, config_file, SYSTEM_PLATFORM, HRDRM_ENABLED, PIP_PROXY, get_system_based_value, LANGUAGE, lang
from difflib import get_close_matches


HELPERS_DIR = Path(__file__).resolve().parent
HELPERS_PARENT_DIR = HELPERS_DIR.parent
CRASH_COUNTER = 0
if str(HELPERS_PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(HELPERS_PARENT_DIR))
from messages import mask, print_message, print_choices, print_choice, render_code, render_md, spinning_loader, WARNING, ERROR, SUCCESS, INFO, BASE_LIBRARY


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
        if PIP_PROXY:
            command.extend(['--proxy', PIP_PROXY])
        process = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)

        for line in process.stdout:
            print_message(line.strip())

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
    global CRASH_COUNTER

    directory = Path(directory_path)
    module_dirs = sorted(
        path
        for path in directory.iterdir()
        if path.is_dir()
        and path.name != Path(__file__).resolve().parent.name
        and not path.name.startswith("_")
    )

    modules = []
    disabled_modules = []
    settings = []

    loader.config.read(config_file)
    config = loader.config

    for module_dir in module_dirs:
        module_name = module_dir.name

        if module_name == "__init__":
            continue

        matching_sections = [
            section
            for section in config.keys()
            if re.match(rf"^{re.escape(module_name)}:?.*$", section)
        ]

        for section in matching_sections:
            settings.append({section: dict(config[section].items())})

        module_enabled = config.get(module_name, "enabled", fallback="True")

        try:
            if package:
                loaded_module = importlib.import_module(
                    f"{package}.{module_name}"
                )
            else:
                init_file = module_dir / "__init__.py"
                spec = importlib.util.spec_from_file_location(
                    module_name,
                    init_file,
                    submodule_search_locations=[str(module_dir)],
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not create an import spec for {init_file}")

                loaded_module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = loaded_module
                spec.loader.exec_module(loaded_module)

            if module_enabled != "True":
                disabled_modules.append(loaded_module)
                continue

            compatibility = loaded_module.__module_compatibility__
            status = loaded_module.__module_status__

            if "all" not in compatibility and SYSTEM_PLATFORM not in compatibility:
                if force:
                    print_message(
                        f"Module '{module_name}' not supported by this platform "
                        f"({SYSTEM_PLATFORM}), module not loaded.",
                        WARNING,
                    )
                continue

            modules.append(loaded_module)

            if status in {"development", "dev", "testing", "test"}:
                message = (
                    f"Module '{module_name}' loaded, but may not work correctly "
                    "because it is under development."
                )
                level = WARNING
            elif status in {"deprecated", "unstable", "unsupported"}:
                message = (
                    f"Module '{module_name}' loaded, but may not work correctly "
                    "because it is not supported anymore; better way is delete it "
                    f"via command 'modules rm {module_name}'."
                )
                level = WARNING
            elif status in {"stable", "supported", "prod"}:
                message = f"Loaded module: '{module_name}'."
                level = None
            else:
                message = (
                    f"Module '{module_name}' loaded, but has unknown stability status."
                )
                level = WARNING

            if force:
                print_message(message, level) if level else print_message(message)

        except ModuleNotFoundError:
            requirements_file = module_dir / "requirements.txt"

            if requirements_file.exists() and install_reqs and CRASH_COUNTER < 5:
                CRASH_COUNTER += 1
                if force:
                    print_message(
                        f"[Try {CRASH_COUNTER}/5] Module '{module_name}' could not be "
                        "loaded because dependencies are missing. Installing packages "
                        f"from '{requirements_file}'...",
                        WARNING,
                    )

                install_requirements(module_name, requirements_file)
                return _load_modules_from_directory(
                    directory_path,
                    package=package,
                    force=force,
                    install_reqs=install_reqs,
                )

            if force:
                if requirements_file.exists():
                    print_message(
                        f"Module '{module_name}' not loaded because required packages "
                        "are missing and HRDRM is disabled.",
                        WARNING,
                    )
                else:
                    print_message(
                        f"Cannot load module '{module_name}' because packages are "
                        "missing and cannot be resolved via HRDRM. Generate "
                        f"requirements with 'modules renderreq {module_name}' and "
                        "then execute the helper CLI.",
                        ERROR,
                    )

        except AttributeError:
            if force:
                print_message(
                    f"Module '{module_name}' not loaded because required helper "
                    "attributes were not found; it may not be a helper module.",
                    WARNING,
                )

        except Exception as exc:
            if force:
                print_message(
                    f"Error loading module '{module_name}': {exc}",
                    ERROR,
                )

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
                print_message(f"Helper '{helper}' initialized with settings '{mask(helper_settings)}'.")
            else:
                print_message(f"Specified helper '{helper}' not found.", ERROR)
        except Exception as e:
            print_message(f"Failed to initialize helper '{helper}': {e}", ERROR)

    def version(self):
        return f"{self.module.__module_name__}: {self.module.__module_version__} ({self.module.__module_status__})"

    def man(self):
        readme = Path(self.module.__file__).parent / 'README.md'
        helper_name = Path(self.module.__file__).parent.stem
        if readme.exists():
            with open(readme, encoding='utf-8') as readme_file:
                return render_md(readme_file.read())
        return lang.get(Path(__file__).parent.parent / '__init__.py', helper_name = helper_name)

    def requirements(self):
        reqs = Path(self.module.__file__).parent / 'requirements.txt'
        helper_name = Path(self.module.__file__).parent.stem
        if reqs.exists():
            with open(reqs, encoding='utf-8') as reqs_file:
                return lang.get(Path(__file__).parent.parent / '__init__.py', key='reqs', helper_name = helper_name, reqs = reqs_file.read().strip())
        return lang.get(Path(__file__).parent.parent / '__init__.py', key='no_reqs', helper_name = helper_name)

    def changes(self):
        changelog = Path(self.module.__file__).parent / 'CHANGELOG.md'
        helper_name = Path(self.module.__file__).parent.stem
        if changelog.exists():
            with open(changelog, encoding='utf-8') as changelog_file:
                return render_md(changelog_file.read())
        return lang.get(Path(__file__).parent.parent / '__init__.py', helper_name = helper_name)

    def __getattr__(self, name):
        return getattr(self.helper, name)
