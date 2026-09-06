import configparser
import os
import platform
import ctypes
import re
import locale
from pathlib import Path
from colorama import Fore
from typing import Any, Optional
from localization import lang


__version__ = '1.3.0'
__version_name__ = 'autumn'
__release__ = 'dev'
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

    def remove(self, section: str, option: str = None):
        if self.config.has_section(section) and not option:
            self.config.remove_section(section)
        elif self.config.has_section(section) and option:
            self.config.remove_option(option)
        with open(self.config_path, 'w+', encoding='utf-8') as configfile: 
            self.config.write(configfile)

HELPER_HOME = Path.home() / '.helper'
os.makedirs(HELPER_HOME, mode=0o755, exist_ok=True)
config_file = Path(f'{Path(__file__).parent}/{__product_name__}.cfg').absolute()
if not config_file.exists():
    config_file = HELPER_HOME / 'config'
    if not config_file.exists():
        with open(config_file, 'x', encoding='utf-8') as config:
            default_config = f"""[core:ui]
language = en_US

[core:remote]
gh_api_token = 
pip_proxy = 
pip_break_system_packages = False
update_check = False

[core:optimization]
less_lines = 20
modules_filter = ^.*.$
hrdrm_enabled = False
gc_enabled = True
md_return_output = False

[core:logging]
logs_path = {Path(Path(__file__).parent / 'logs').as_posix()}
logs_levels = ERROR
debug = False
emoji_enabled = True
colored_output = True
measure_time = False
"""
            config.write(default_config)
loader = ConfigLoader(config_file)

# Core #
LOCALE, ENCODING = locale.getdefaultlocale()
IS_ADMIN = is_admin()
SYSTEM_PLATFORM = platform.system()
LANGUAGE = get_system_based_value(loader.get('core:ui', 'language', LOCALE))
INPUT_STYLE = get_system_based_value(loader.get('core:ui', 'input', '-->'))
MORE_STYLE = get_system_based_value(loader.get('core:ui', 'more', '---MORE---'))

# Remote
GITHUB_TOKEN = get_system_based_value(loader.get('core:remote', 'gh_api_token', ''))
PIP_PROXY = get_system_based_value(loader.get('core:remote', 'pip_proxy', ''))
PIP_BREAK_SYSTEM_PACKAGES = get_system_based_value(loader.get('core:remote', 'pip_break_system_packages', 'False')) == 'True'
UPDATE_CHECK = get_system_based_value(loader.get('core:remote', 'update_check', 'False')) == 'True'

# Optimization
LESS_LINES = int(get_system_based_value(loader.get('core:optimization', 'less_lines', '20')))
UNPACK_FILE_FILTER = get_system_based_value(loader.get('core:optimization', 'modules_filter', r'^.*.$'))
HRDRM_ENABLED = get_system_based_value(loader.get('core:optimization', 'hrdrm_enabled', 'False')) == 'True'
GC_ENABLED = get_system_based_value(loader.get('core:optimization', 'gc_enabled', 'True')) == 'True'
MD_RETURN_OUTPUT = get_system_based_value(loader.get('core:optimization', 'md_return_output', 'False')) == 'True'

# Logging
LOGS_PATH = Path(get_system_based_value(loader.get('core:logging', 'logs_path', f'{Path(__file__).parent}/logs'))).absolute()
LOGS_LEVELS = loader.get('core:logging', 'logs_levels', 'ERROR', split=True)
DEBUG = get_system_based_value(loader.get('core:logging', 'debug', 'False')) == 'True'
EMOJI_ENABLED = get_system_based_value(loader.get('core:logging', 'emoji_enabled', 'True')) == 'True'
COLORED_OUTPUT = get_system_based_value(loader.get('core:logging', 'colored_output', 'True')) == 'True'
MEASURE_TIME = get_system_based_value(loader.get('core:logging', 'measure_time', 'False')) == 'True'
# End Core #

# Colors
if COLORED_OUTPUT:
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    BLUE = Fore.BLUE
    RESET = Fore.RESET
else:
    GREEN = Fore.RESET
    YELLOW = Fore.RESET
    RED = Fore.RESET
    BLUE = Fore.RESET
    RESET = Fore.RESET

# Localization
lang = lang(LANGUAGE, DEBUG, COLORED_OUTPUT)
