import pandas as pd
import glob
import os
from pathlib import Path
from env import __version__, LOGS_PATH
from helpers import print_message, print_choices, print_choice, render_code, INFO, WARNING, ERROR, loader, SYSTEM_PLATFORM, get_system_based_value
from helpers.core.utils import install_update, retrieve_json
from helpers.modules.utils import github_url_to_releases_api


# Module global settings
__module_disabled_methods__ = []
__module_name__ = 'coreHelper'
__module_author__ = 'JoePeach88'
__module_version__ = __version__
__module_link__ = None
__module_category__ = ['builtin', 'core']
__module_compatibility__ = ['all']
__module_dependencies__ = []
__module_status__ = 'stable'
__methods_static_aliases__ = {}


class coreHelper:
    """
    **Module to work with helper core.**
    """
    def __init__(self, settings: dict):
        self.settings = settings.get('core')

        # Subclasses
        self.config = self.config(dict(loader.config), settings.get('core:config', {}))
        self.update = self.update(settings.get('core:update', {}))
        self.logs = self.logs(settings.get('core:logging', {}))

    class config:
        """
        **Module to manipulate helper config parameters.**
        """
        def __init__(self, global_settings: dict, settings: dict):
            self.global_settings = global_settings
            self.settings = settings

        def get(self, section: str, option: str):
            """
            **Method retrieves config data.**
            ```
            Usage:
                core config get <section> <option>
            ```
            """
            return f"Config data is:\n  Section: {section}\n  Option: {option}\n  Value: {loader.get(section, option)}"
        
        def set(self, section: str, option: str, value: str, system_based: bool = False):
            """
            **Method sets config data.**
            ```
            Usage:
                1. Simple value set:
                    core config set <section> <option> <value>
                2. Value set based on current system:
                    core config set <section> <option> <value> --system-based
            ```
            """
            if system_based:
                current_value = loader.get(section, option)
                value = f'{SYSTEM_PLATFORM}({value})'
                if current_value:
                    current_value_splitted = [val.strip() for val in current_value.split(',')]
                    for splitted_value in current_value_splitted:
                        if splitted_value == value or get_system_based_value(splitted_value, return_default=True):
                            current_value_splitted.remove(splitted_value)
                    if value not in current_value_splitted:
                        value = f"{', '.join(current_value_splitted)}, {value}"
                    else:
                        value = current_value
            loader.set(section, option, value)
            return f"The following values ​​are set:\n  Section: {section}\n  Option: {option}\n  Value: {value}"

        def ls(self, pretty: bool = True):
            """
            **Method displays all config data.**
            ```
            Usage:
                core config ls
            ```
            """
            if pretty:
                for section_name, section_proxy in self.global_settings.items():
                    if section_name != 'DEFAULT':
                        print(f"[{section_name}]")
                        for key, value in section_proxy.items():
                            print(f"  {key} = {value}")
            else:
                return {s:dict(self.global_settings.items(s)) for s in self.global_settings.sections()}

    class update:
        """
        **Module updates helper core.**
        """
        def __init__(self, settings: dict):
            self.settings = settings
            self.core_url = github_url_to_releases_api('https://github.com/JoePeach88/helper')

        def check(self, pretty: bool = True, dev: bool = False):
            """
            **Method checks updates for helper core.**
            ```
            Usage:
                core update check
            ```
            """
            dev = self.settings.get('enable_dev_updates', 'False') == 'True' or dev
            if not self.core_url:
                return [] if not pretty else "Failed to retrieve core updates."

            release_data = retrieve_json(self.core_url)
            if not isinstance(release_data, list) or not release_data:
                print_message("Failed to retrieve core updates.", WARNING)
                return "Failed to retrieve core updates." if pretty else []

            core_for_update = []
            core_remote_download_link, core_remote_version, core_remote_changelog = None, None, None

            for core_last_release in release_data:
                is_dev_release = 'dev' in core_last_release['tag_name']
                if (is_dev_release and dev) or (not is_dev_release and not dev):
                    core_remote_download_link = core_last_release.get('tarball_url')
                    core_remote_version = core_last_release['tag_name'].split('-')[0]
                    core_remote_changelog = core_last_release.get('body')
                    break

            if core_remote_version and (__version__ < core_remote_version or (__version__ < core_remote_version and 'dev' in core_last_release['tag_name'])):
                update_data = {
                    'name': 'core',
                    'current_version': __version__,
                    'remote_version': core_remote_version + ' (dev)' if is_dev_release else '',
                }
                if not pretty:
                    update_data.update({
                        'remote_download_link': core_remote_download_link,
                        'changelog': core_remote_changelog,
                    })
                core_for_update.append(update_data)

            if pretty:
                return pd.DataFrame(core_for_update).to_string(index=False, justify='left') if core_for_update else "All modules are up-to-date."
            return core_for_update if core_for_update else []

        def install(self, dev: bool = False):
            """
            **Method updates helper core.**
            ```
            Usage:
                core update install
            ```
            """
            core_for_update = self.check(pretty=False, dev=dev)
            if not core_for_update:
                return "Nothing to install."
            if core_for_update:
                core_for_update = core_for_update[0]
                return install_update(core_for_update['remote_version'], core_for_update['remote_download_link'])

    class logs:
        """
        **Module to manipulate with logs.**
        """
        def __init__(self, settings: dict):
            self.settings = settings

        def ls(self, pretty: bool = True):
            """
            **Method displays logs.**
            ```
            Usage:
                core logs ls
            ```
            """
            logs = []
            refactored_logs = []
            logs.extend(glob.glob(os.path.join(Path(LOGS_PATH), "*.log")))
            for log in logs:
                refactored_logs.append(Path(log).stem)
            return f'Available logs ({len(refactored_logs)}):\n' + '\n'.join(refactored_logs) if pretty else refactored_logs

        def view(self, log: str = None):
            """
            **Method displays log content.**
            ```
            Usage:
                core logs view <log>
            ```
            """
            if not log:
                logs_list = self.ls(pretty=False)
                log = print_choices(logs_list, exit_btn=True)
                if log:
                    log = f"{LOGS_PATH}/{log}.log"
            else:
                if not Path(log).exists():
                    log = f"{LOGS_PATH}/{log}.log"
                    if not Path(log).exists():
                        log = None
            if log:
                with open(log, 'r', encoding='utf-8') as log_file:
                    return render_code(log_file.read(), 'python')


        def rm(self, log: str = None):
            """
            **Method removes log file.**
            ```
            Usage:
                core logs rm
            ```
            """
            if not log:
                logs_list = self.ls(pretty=False)
                log = print_choices(logs_list, exit_btn=True)
                if log:
                    log = f"{LOGS_PATH}/{log}.log"
            else:
                if not Path(log).exists():
                    log = f"{LOGS_PATH}/{log}.log"
                    if not Path(log).exists():
                        log = None
            if log:
                os.remove(log)
                return f"Log file '{Path(log).as_posix()}' removed."

        def flush(self):
            """
            **Method removes all log files.**
            ```
            Usage:
                core logs flush
            ```
            """
            logs_list = self.ls(pretty=False)
            if logs_list:
                for log in logs_list:
                    log = f"{LOGS_PATH}/{log}.log"
                    os.remove(log)
                return 'All logs removed.'
