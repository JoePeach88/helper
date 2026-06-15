import pandas as pd
import os
import re
import yaml
from rich.console import Console
from rich.markdown import Markdown
from pipreqs import pipreqs
from helpers.modules.utils import github_url_to_releases_api, retrieve_json, install_module, uninstall_module, determine_type, pack_module, get_file_sha256, get_dir_size, format_bytes
from helpers import print_message, print_choices, _load_modules_from_directory, HELPERS_DIR, INFO, WARNING, ERROR, SYSTEM_PLATFORM
from env import loader, PIP_PROXY
from pathlib import Path


# Module global settings
__module_disabled_methods__ = []
__module_name__ = 'ModulesHelper'
__module_author__ = 'JoePeach88'
__module_version__ = '1.0.0'
__module_link__ = None
__module_category__ = ['builtin', 'core']
__module_compatibility__ = ['all']
__module_dependencies__ = [{}]
__module_status__ = 'stable'
__methods_static_aliases__ = {
    'ls': ['ll', 'list'],
    'info': ['nfo'],
    'update': ['upgrade'],
    'check': ['chk'],
    'enable': ['on'],
    'disable': ['off'],
    'install': ['add'],
    'uninstall': ['rm', 'remove', 'delete'],
    'create': ['new'],
    'rendermd': ['md', 'markdown'],
    'renderreq': ['reqs', 'req'],
    'renderhash': ['hash'],
    'pack': ['zip']
}


class modulesHelper:
    """
    Module to work with helper modules.
    """
    def __init__(self, settings: dict):
        self.settings = settings
        not_silent = True
        self.templates = {
            'documentation': Path(__file__).parent / 'templates/documentation.tmpl',
            'module': Path(__file__).parent / 'templates/module.tmpl',
            'scenario': Path(__file__).parent / 'templates/scenario.tmpl'
        }
        if self.settings.get('modules:module', {}).get('silent_load', 'True') == 'True':
            not_silent = False
            print_message("Loading modules silently to retrieve it information.")
        else:
            not_silent = True
            print_message("Loading modules to retrieve it information.")
        all_helpers = _load_modules_from_directory(HELPERS_DIR, package=HELPERS_DIR.name, force=not_silent)
        self.helpers = all_helpers[0]
        self.disabled_helpers = all_helpers[1]

        # Subclasses
        self.update = self.update(settings.get('modules:update', {}), self.helpers)

    def ls(self, all: bool = False, pretty: bool = True):
        """
        Method displays all available modules.
        Usage:
            modules ls
        """
        helpers_list = []
        helpers = self.helpers
        if all:
            helpers.extend(self.disabled_helpers)
        for module in helpers:
            helpers_list.append(module.__name__.split('.')[-1])
        return f'Available modules ({len(helpers_list)}):\n' + '\n'.join(helpers_list) if pretty else helpers_list

    def info(self, module: str = None, pretty: bool = True):
        """
        Method displays information about installed module.
        Usage:
            modules info --module <module_name>
        """
        all_helpers = self.helpers
        all_helpers.extend(self.disabled_helpers)
        if not module:
            module = print_choices([helper.__name__.split('.')[-1] for helper in self.helpers], exit_btn=True)
        if module:
            for helper in all_helpers:
                if helper.__name__.split('.')[-1] == module:
                    name = helper.__module_name__
                    author = helper.__module_author__
                    version = helper.__module_version__
                    link = helper.__module_link__
                    compatibility = 'all' in helper.__module_compatibility__ or SYSTEM_PLATFORM in helper.__module_compatibility__
                    size = get_dir_size(Path(helper.__file__).parent)
                    return f"Name: {name}\nAuthor: {author}\nVersion: {version}\nLink: {link}\nPath: {Path(helper.__file__).parent}\nCompatible: {'Yes' if compatibility else 'No'}\nSize: {format_bytes(size)}" if pretty else {'name': name, 'author': author, 'version': version, 'link': link, 'path': Path(helper.__file__).parent, 'compatibility': compatibility, 'size': size}
            return f"Module with name '{module}' not found." if pretty else {}

    def disable(self, module: str):
        """
        Method disables module.
        Usage:
            modules disable --module <module_name>
        """
        all_helpers = self.helpers
        all_helpers.extend(self.disabled_helpers)
        for helper in all_helpers:
            if helper.__name__.split('.')[-1] == module:
                loader.set(module, 'enabled', 'False')
                return f"Module '{module}' disabled."
        return f"Module '{module}' not found."

    def enable(self, module: str):
        """
        Method enables module.
        Usage:
            modules enable --module <module_name>
        """
        all_helpers = self.helpers
        all_helpers.extend(self.disabled_helpers)
        for helper in all_helpers:
            if helper.__name__.split('.')[-1] == module:
                loader.set(module, 'enabled', 'True')
                return f"Module '{module}' enabled."
        return f"Module '{module}' not found."

    def install(self, module: str, location: str, version: str = None, force: bool = False, skip_check: bool = False):
        """
        Method installs specified module from link or from path.
        Usage:
            modules install <module_name> --location <link or path>
        """
        link_type = determine_type(location)
        return install_module(module, location, version, link_type, force=force, skip_check=skip_check)

    def uninstall(self, module: str, yes: bool = False):
        """
        Method uninstalls specified module.
        Usage:
            modules uninstall <module_name>
        """
        return uninstall_module(module, force=yes)

    def create(self, module: str, name: str = None, author: str = None, version: str = None, systems: str = None, force: bool = False):
        """
        Method creates empty module from template for development.
        Usage:
            modules create <module_name> --name ModuleName --author Author --version 1.0.0 --systems Linux,Windows,Darwin
        """
        module_template = ""
        install_scenario_template = ""
        with open(self.templates.get('module'), 'r', newline="\n", encoding='utf-8') as module_template_file:
            module_template = module_template_file.read()
        with open(self.templates.get('scenario'), 'r', newline="\n", encoding='utf-8') as install_scenario_template_file:
            install_scenario_template = install_scenario_template_file.read()
        with open(self.templates.get('scenario'), 'r', newline="\n", encoding='utf-8') as uninstall_scenario_template_file:
            uninstall_scenario_template = uninstall_scenario_template_file.read()
        if module_template:
            module_template = module_template.format(module = module, name = name, author = author, version = version, systems = ", ".join(f"'{system}'" for system in systems.split(",")))
        module_path = Path(f"{HELPERS_DIR}/{module}").absolute()
        init_path= Path(f"{module_path}/__init__.py").absolute()
        install_scenario_path = Path(f"{module_path}/INSTALL.sc").absolute()
        uninstall_scenario_path = Path(f"{module_path}/UNINSTALL.sc").absolute()
        os.makedirs(module_path, mode=0o750, exist_ok=True)
        if (init_path.exists() or install_scenario_path.exists() or uninstall_scenario_path.exists()) and force:
            os.remove(init_path)
            os.remove(install_scenario_path)
            os.remove(uninstall_scenario_path)

        if not install_scenario_path.exists():
            with open(install_scenario_path, 'x', newline="\n", encoding='utf-8') as install_scenario_file:
                install_scenario_file.write(install_scenario_template)
        if not uninstall_scenario_path.exists():
            with open(uninstall_scenario_path, 'x', newline="\n", encoding='utf-8') as uninstall_scenario_file:
                uninstall_scenario_file.write(uninstall_scenario_template)
        if not init_path.exists():
            with open(init_path, 'x', newline="\n", encoding='utf-8') as module_file:
                module_file.write(module_template)
            return f"Module '{module}' created."
        else:
            return f"Module '{module}' already exists."

    def rendermd(self, module: str):
        """
        Module renders README.md.
        Usage:
            modules rendermd <module_name>
        """
        all_helpers = self.helpers
        all_helpers.extend(self.disabled_helpers)
        if module:
            for helper in all_helpers:
                if helper.__name__.split('.')[-1] == module:
                    obj = getattr(helper, f"{module}Helper")
                    author = helper.__module_author__
                    version = helper.__module_version__
                    link = helper.__module_link__
                    platforms = '\n'.join(helper.__module_compatibility__)
                    disabled_methods = helper.__module_disabled_methods__
                    description = obj.__doc__
                    if description:
                        description = re.sub(r" \s+", "", description).strip()
                    methods = dir(obj)

                    # Creating methods list
                    methods_list = []
                    for method in methods:
                        if method in disabled_methods:
                            continue
                        method_object = getattr(obj, method)
                        if not method.startswith('_') and (callable(method_object) or not isinstance(method_object, (list, str, dict, int, float, bool, tuple, set, type(helper.helper), type(None)))):
                            # determine class method
                            if (not callable(method_object) or isinstance(method_object, type)) and not isinstance(method_object, str):
                                methods_list.append(f"- [**{method}**](#{method}) [module]")
                                class_methods = dir(method_object)
                                for class_method in class_methods:
                                    class_method_object = getattr(method_object, class_method)
                                    if not class_method.startswith('_') and (callable(class_method_object) or not isinstance(method_object, (list, str, dict, int, float, bool, tuple, set, type(helper.helper), type(None)))):
                                        methods_list.append(f"- [{class_method}](#{class_method})")
                            else:
                                methods_list.append(f"- [{method}](#{method})")
                    methods_list = '\n'.join(methods_list)

                    # Creating methods descriptions and usage
                    methods_description = []
                    for method in methods:
                        if method in disabled_methods:
                            continue
                        method_object = getattr(obj, method)
                        if not method.startswith('_') and (callable(method_object) or not isinstance(method_object, (list, str, dict, int, float, bool, tuple, set, type(helper.helper), type(None)))):
                            # determine class method
                            if (not callable(method_object) or isinstance(method_object, type)) and not isinstance(method_object, str):
                                methods_description.append(f"## {method}\n")
                                method_doc = method_object.__doc__
                                if method_doc:
                                    method_doc = re.sub(r" \s+", "", method_doc).strip()
                                methods_description.append(f"```\n{method_doc}\n```\n")
                                class_methods = dir(method_object)
                                for class_method in class_methods:
                                    class_method_object = getattr(method_object, class_method)
                                    if not class_method.startswith('_') and (callable(class_method_object) or not isinstance(method_object, (list, str, dict, int, float, bool, tuple, set, type(helper.helper), type(None)))):
                                        methods_description.append(f"### {class_method}\n")
                                        class_method_doc = class_method_object.__doc__
                                        if class_method_doc:
                                            class_method_doc = re.sub(r" \s+", "", class_method_doc).strip()
                                        methods_description.append(f"```\n{class_method_doc}\n```\n")
                            else:
                                methods_description.append(f"### {method}\n")
                                method_doc = method_object.__doc__
                                if method_doc:
                                    method_doc = re.sub(r" \s+", "", method_doc).strip()
                                methods_description.append(f"```\n{method_doc}\n```\n")
                    methods_description = '\n'.join(methods_description)
                    module_readme = Path(helper.__file__).parent / 'README.md'
                    with open(self.templates.get('documentation'), 'r', newline="\n", encoding='utf-8') as documentation_template_file:
                        documentation_template = documentation_template_file.read()
                    if documentation_template:
                        documentation = documentation_template.format(module = module, description = description, methods_list = methods_list, link = link, author = author, 
                                                                      version = version, platforms = platforms, methods_description = methods_description)
                    else:
                        print_message('Documentation template not exists, aborting md creation.', ERROR)
                        return 'Documentation template not exists, aborting md creation.'
                    with open(module_readme, 'w' if module_readme.exists() else 'x', newline="\n", encoding='utf-8') as module_readme_file:
                        module_readme_file.write(documentation)
                    print_message(f"README.md successfully rendered to '{module_readme.absolute()}'.", force=True)

    def renderreq(self, module: str):
        """
        Module renders requirements.txt.
        Usage:
            modules renderreq <module_name>
        """
        all_helpers = self.helpers
        all_helpers.extend(self.disabled_helpers)
        if module:
            for helper in all_helpers:
                if helper.__name__.split('.')[-1] == module:
                    helper_path = Path(helper.__file__).parent
                    pipreqs_args = {'--encoding': 'utf-8', '--ignore': '.venv', '<path>': f'{helper_path}', '--force': True, '--savepath': None, '--print': None, '--pypi-server': None,
                                    '--proxy': PIP_PROXY, '--use-local': None, '--diff': None, '--clean': None, '--mode': None}
                    pipreqs_obj = pipreqs
                    pipreqs_obj.logging.disable()
                    print_message(f"Starting pipreqs with arguments {pipreqs_args}...")
                    pipreqs_obj.init(pipreqs_args)
                    reqs = helper_path / 'requirements.txt'
                    reqs_lines = []
                    with open(reqs, 'r', newline="\n", encoding='utf-8') as reqs_file:
                        reqs_lines = reqs_file.readlines()
                        reqs_lines = [line for line in reqs_lines if not re.match(r'^(helpers|env|libs|handler|messages|utils).*$', line)] # remove basic helper imports
                    with open(reqs, 'w', newline="\n", encoding='utf-8') as reqs_file:
                        reqs_file.writelines(reqs_lines)
                    if not reqs_lines:
                        os.remove(reqs)
                        print_message(f"requirements.txt for module '{module}' not rendered cause output from pipreqs is empty.", force=True)
                    else:
                        print_message(f"requirements.txt successfully rendered for module '{module}' and saved to '{reqs}'.", force=True)

    def renderhash(self, module: str):
        """
        Method renders hash for each module file.
        Usage:
            modules renderhash <module_name>
        """
        all_helpers = self.helpers
        all_helpers.extend(self.disabled_helpers)
        if module:
            hash_list = []
            for helper in all_helpers:
                if helper.__name__.split('.')[-1] == module:
                    helper_path = Path(helper.__file__).parent
                    for file in helper_path.rglob('*'):
                        file_obj= Path(file)
                        file_parent = file_obj.parent.name
                        if file_parent == module:
                            file_parent = '.'
                        else:
                            file_parent = f"./{file_parent}"
                        file_name = file_obj.name
                        if file_name in ['SHA256', 'CHANGELOG.md', 'README.md'] or file_obj.is_dir():
                            continue
                        hash_obj = {f"{file_parent}/{file_name}": get_file_sha256(file)}
                        hash_list.append(hash_obj)
                    hash_list_file = helper_path / 'SHA256'
                    with open(hash_list_file, 'w' if hash_list_file.exists() else 'x', newline="\n", encoding='utf-8') as f:
                        f.write(yaml.dump(hash_list))
                    print_message(f"SHA256 hash table successfully rendered to '{hash_list_file.absolute()}'.", force=True)

    def pack(self, *modules, location: str = None):
        """
        Method prepare module and packs it to tar archive.
        Usage:
            1. To default pack location:
                modules pack <module_name>
            2. To specified pack location:
                modules pack <module_name> --location <location>
            3. To pack few modules:
                modules pack <module1> <module2> --location <location>
        """
        for module in modules:
            module_info = self.info(module, pretty=False)
            if module_info:
                module_version = module_info['version']
            else:
                return f"Module '{module}' not found."
            print_message("Rendering module requirements, please wait...", force=True)
            self.renderreq(module)
            print_message("Rendering module manual, please wait...", force=True)
            self.rendermd(module)
            print_message("Rendering module hash table, please wait...", force=True)
            self.renderhash(module)
            print_message(pack_module(module, module_version, location), force=True)

    class update:
        """
        Module to manipulate and check updates for modules.
        """
        def __init__(self, settings: dict = None, helpers: list = None):
            self.settings = settings
            self.helpers = helpers

        def changes(self, module: str = None):
            """
            Method prints changelog for module.
            Usage:
                1. With prompt to select available modules.
                    modules update changes
                2. With specified module.
                    modules update changes --module <module_name>
            """
            if not module:
                module = print_choices([helper.__name__.split('.')[-1] for helper in self.helpers], exit_btn=True)
            if module:
                changelog_path = Path(f'{HELPERS_DIR}/{module}/CHANGELOG.md').absolute()
                if not changelog_path.exists():
                    module_updated = self.check(module, pretty=False)
                    if not module_updated:
                        print_message("Nothing to install.", force=True)
                        return
                    else:
                        return module_updated[0]['body']
                else:
                    with open(changelog_path, 'r', encoding='utf-8') as changelog_file:
                        console = Console(record=True, highlight=True, soft_wrap=True)
                        with console.capture() as capture:
                            console.print(Markdown(changelog_file.read()))
                        return capture.get()

        def check(self, module: str = None, pretty: bool = True):
            """
            Method checks updates for modules or specified module.
            Usage:
                1. Without specified module name:
                    modules update check
                2. With specified module name:
                    modules update check --module module_name
            """
            helpers = self.helpers.copy()
            helpers_for_update = []
            if module:
                helpers[:] = [
                    helper
                    for helper in helpers
                    if helper.__name__.rsplit(".", 1)[-1] == module
                ]
            for helper in helpers:
                print_message(f"Checking updates of module '{helper.__name__.split('.')[-1]}'.")
                helper_name = helper.__name__.split('.')[-1]
                if helper_name == 'modules':
                    continue
                helper_current_version = helper.__module_version__
                helper_releases = github_url_to_releases_api(helper.__module_link__)
                if not helper_releases:
                    continue
                helper_releases_data = retrieve_json(helper_releases)
                if not isinstance(helper_releases_data, list):
                    print_message(f"Failed to retrieve updates of module '{helper.__name__.split('.')[-1]}'.", WARNING)
                    continue
                helper_last_release = helper_releases_data[0]
                helper_remote_download_link = helper_last_release.get('tarball_url')
                helper_remote_version = helper_remote_download_link.split('/')[-1]
                helper_remote_changelog = helper_last_release.get('body')
                if helper_current_version < helper_remote_version:
                    update_data = {'name': helper_name, 'current_version': helper_current_version, 'remote_version': helper_remote_version} if pretty else {'name': helper_name, 'current_version': helper_current_version, 'remote_version': helper_remote_version, 'remote_download_link': helper_remote_download_link, 'changelog': helper_remote_changelog}
                    helpers_for_update.append(update_data)
            if pretty:
                return pd.DataFrame(helpers_for_update).to_string(index=False, justify='left') if helpers_for_update else "All modules are up-to-date."
            else:
                return helpers_for_update if helpers_for_update else []

        def install(self, module: str = None, skip_check: bool = False):
            """
            Method updates modules or specified module.
            Usage:
                1. Without specified module name:
                    modules update install
                2. With specified module name:
                    modules update install --module module_name
            """
            modules_for_update = self.check(pretty=False)
            if not modules_for_update:
                print_message("Nothing to install.", force=True)
                return
            if not module:
                if modules_for_update:
                    selected_for_install = print_choices([module_data['name'] for module_data in modules_for_update], multiple_choice=True, all_btn=True, exit_btn=True)
                    if selected_for_install:
                        if 'all' in selected_for_install:
                            for module_data in modules_for_update:
                                return install_module(module_data['name'], module_data['remote_download_link'], skip_check=skip_check, force=True)
                        elif selected_for_install:
                            for module_data in modules_for_update:
                                if module_data['name'] in selected_for_install:
                                    return install_module(module_data['name'], module_data['remote_download_link'], skip_check=skip_check, force=True)
                        else:
                            return
            else:
                if modules_for_update:
                    for module_data in modules_for_update:
                        if module == module_data['name']:
                            return install_module(module, module_data['remote_download_link'], skip_check=skip_check)
                    print_message(f"Module '{module}' is up-to-date.", force=True)
                    return
