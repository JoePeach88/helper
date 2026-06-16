import configparser
import os
import platform
import ctypes
import re
import locale
import yaml
from pathlib import Path
from colorama import Fore
from typing import Any, Optional


__version__ = '1.1.0'
__version_name__ = 'summer'
__release__ = 'stable'
__product_name__ = 'helper'
__required_python__ = (3, 7)


def get_system_based_value(string: str, default: str = None, return_default: bool = False):
    """
    Method parses value based on OS.
    For example:
        Linux(some_value) -> some_value  if script runs on Linux
        Windows(some_value) -> some_value  if script runs on Windows
        Windows|Linux(some_value) -> some_value  if script runs on both Linux and Windows
    """
    pattern = r'{platform}\((.*?)\)'.format(platform=SYSTEM_PLATFORM)
    match = re.search(pattern, string)
    if match:
        return match.group(1)
    elif return_default:
        return default
    else:
        return string
    

def get_localization(locale_code: str, locales_path: str):
    locale_full_path = Path(f'{locales_path}/{locale_code}.yml')
    if locale_full_path.exists():
        with open(locale_full_path, 'r', encoding='utf-8') as locale_file:
            return yaml.safe_load(locale_file.read())


def is_admin():
    try:
        return os.getuid() == 0
    except AttributeError:
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except AttributeError:
            return False


class ConfigLoader:
    def __init__(self, config_file):
        self.config_path = Path(config_file)
        self.config = configparser.ConfigParser(empty_lines_in_values=True)
        self.config_exists = self.config_path.exists()
        if self.config_exists:
            self.config.read(self.config_path, encoding='utf-8')

    def get(self, section: str, option: str, default: Optional[Any] = None, split: bool = False, split_char: str = ','):
        env_key = f"{section.upper()}_{option.upper()}"
        env_val = os.getenv(env_key)
        if env_val is not None:
            env_val = env_val.strip()

        if env_val is not None and env_val != '':
            val = env_val
        elif self.config_exists and self.config.has_option(section, option):
            val = self.config.get(section, option, raw=True).strip()
            if val == '':
                val = default
        else:
            val = default

        if split:
            if not isinstance(val, str) or not val:
                return []
            items = [
                item.strip().strip('\'\"')
                for item in val.split(split_char)
                if item.strip()
            ]
            return items

        return val
    
    def set(self, section: str, option: str, value: str):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)
        with open(self.config_path, 'w+', encoding='utf-8') as configfile: 
            self.config.write(configfile)

config_file = Path(f'{Path(__file__).parent}/{__product_name__}.cfg').absolute()
loader = ConfigLoader(config_file)

# Colors
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
RED = Fore.RED
BLUE = Fore.BLUE
RESET = Fore.RESET

# Core #
LOCALE, ENCODING = locale.getdefaultlocale()
LOCALIZATION_DATA = get_localization(LOCALE, './locales')
IS_ADMIN = is_admin()
SYSTEM_PLATFORM = platform.system()
GITHUB_TOKEN = get_system_based_value(loader.get('core:remote', 'gh_api_token', ''))
PIP_PROXY = get_system_based_value(loader.get('core:remote', 'pip_proxy', ''))
PIP_BREAK_SYSTEM_PACKAGES = get_system_based_value(loader.get('core:remote', 'pip_break_system_packages', 'False')) == 'True'
DEBUG = get_system_based_value(loader.get('core:logging', 'debug', 'False'))
EMOJI_ENABLED = get_system_based_value(loader.get('core:logging', 'emoji_enabled', 'True')) == 'True'
LESS_LINES = int(get_system_based_value(loader.get('core:optimization', 'less_lines', '20')))
UNPACK_FILE_FILTER = get_system_based_value(loader.get('core:optimization', 'modules_filter', r'^.*.$'))
HRDRM_ENABLED = get_system_based_value(loader.get('core:optimization', 'hrdrm_enabled', 'True')) == 'True'
GC_ENABLED = get_system_based_value(loader.get('core:optimization', 'gc_enabled', 'True')) == 'True'

# Logging
LOGS_PATH = Path(get_system_based_value(loader.get('core:logging', 'logs_path', f'{Path(__file__).parent}/logs'))).absolute()
LOGS_LEVELS = loader.get('core:logging', 'logs_levels', 'ERROR', split=True)
# End Core #
