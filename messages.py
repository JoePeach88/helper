import os
import traceback
import sys
import time
import re
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from datetime import datetime
from pathlib import Path
from utils import get_caller_module_name
from env import BLUE, YELLOW, RED, GREEN, RESET, LOGS_PATH, LOGS_LEVELS, DEBUG, LESS_LINES, SYSTEM_PLATFORM, EMOJI_ENABLED, INPUT_STYLE, MORE_STYLE, lang

if SYSTEM_PLATFORM == 'Windows':
    import msvcrt as userinpurt
else:
    import getch as userinpurt

INFO = 'INFO'
WARNING = 'WARNING'
ERROR = 'ERROR'
SUCCESS = 'SUCCESS'
BASE_LIBRARY = lang.get(key='base_library')
VALID_LEVELS = {INFO, WARNING, ERROR, SUCCESS}
EMOJI_MAP = {
    INFO: '🔵',
    WARNING: '🟡',
    ERROR: '🔴',
    SUCCESS: '🟢'
}
COLOR_MAP = {
    INFO: BLUE,
    WARNING: YELLOW,
    ERROR: RED,
    SUCCESS: GREEN
}


def render_code(content: str, lexer: str):
    console = Console(record=True, highlight=True, soft_wrap=True)
    with console.capture() as capture:
        console.print(Syntax(content, lexer))
    return capture.get()


def render_md(content: str):
    console = Console(record=True, highlight=True, soft_wrap=True)
    with console.capture() as capture:
        console.print(Markdown(content))
    return capture.get()


def mask(d: dict):
    masked_dict = {}
    pattern = re.compile(r'.*(token|secret|password).*', re.IGNORECASE)
    for key, value in d.items():
        if isinstance(value, dict):
            masked_dict[key] = mask(value)
        elif pattern.search(key):
            masked_dict[key] = '**CONTENT_MASKED**'
        else:
            masked_dict[key] = value
    return masked_dict


def print_message(message: str, message_level: str = INFO, force: bool = False, debug: bool = False):
    """
    This function used for debug message with various log levels.

    Args:
        message (str): Message which will be displayed in terminal output if debug mod and message level for display is enabled and set in cli settings.
        message_level (str): Message level (INFO, SUCCESS, WARNING or ERROR constant variables).
        force (bool): Force display message.
    """
    module, function = get_caller_module_name()
    if function == '<module>':
        function = '__main__'
    module = Path(module).relative_to(Path(__file__).parent).as_posix()

    if message_level not in VALID_LEVELS:
        raise ValueError(lang.get(message_level=message_level))

    color = COLOR_MAP.get(message_level, RESET)
    emoji = EMOJI_MAP.get(message_level, None)
    timestamp = datetime.now()
    formatted_message = f'[{timestamp}] [{module}] [{function}] [{message_level}] - {message}'
    if EMOJI_ENABLED:
        formatted_message = f'{emoji} {formatted_message}'
    if message_level == ERROR:
        if traceback.format_exc().split() != ['NoneType:', 'None']:
            formatted_message += f"\n{traceback.format_exc()}"

    if message_level in LOGS_LEVELS:
        os.makedirs(LOGS_PATH, mode=0o755, exist_ok=True)
        log_file_path = Path(LOGS_PATH) / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        with open(log_file_path.absolute(), 'a+', encoding='utf-8') as log_file:
            # if emojis enabled, remove it before writing to log file
            log_message = formatted_message.replace(f'{emoji} ', '') if EMOJI_ENABLED else formatted_message
            log_file.write(f'{log_message}\n')
    
    if not debug:
        if DEBUG:
            print(f'{color}{formatted_message}{RESET}')
        elif force:
            if EMOJI_ENABLED:
                print(f'{color}{emoji} [{message_level}] {message}{RESET}')
            else:
                print(f'{color}[{message_level}] {message}{RESET}')
    else:
        print(f'{color}{formatted_message}{RESET}')


def spinning_loader(stop_event = None, message: str = "Loading, please wait..."):
    if not DEBUG:
        symbols = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        while not stop_event.is_set():
            for symbol in symbols:
                if stop_event.is_set():
                    break
                sys.stdout.write(f"\r{message} {symbol} ")
                sys.stdout.flush()
                time.sleep(0.08)
        sys.stdout.write('\x1b[1A')
        sys.stdout.write('\x1b[2K')
        sys.stdout.write('\r')
        sys.stdout.flush()


def less(string: str):
    """
    Such as less on unix systems, but more simplier :).
    """
    def wait_for_user_input():
        input_char = userinpurt.getch().lower()
        if input_char in [b':', ':']:
            second_char = userinpurt.getch().lower()
            full_chars = input_char + second_char
        else:
            full_chars = input_char
            
        return full_chars in [b'\r', '\n'], full_chars == b':e'

    # Check if the string is a file path and read its content
    if Path(string).exists():
        with open(string, 'r', encoding='utf-8') as file:
            string = file.read()

    string_lines = string.split('\n')
    count = 0
    max_lines = LESS_LINES

    for line in string_lines:
        print(line)
        count += 1
        
        if count >= max_lines:
            print(MORE_STYLE)
            skip_line, scroll_end = wait_for_user_input()
            
            if not skip_line:
                exit(0)
            elif scroll_end:
                max_lines = len(string_lines)
            
            # Clear the last printed line
            sys.stdout.write('\x1b[1A')
            sys.stdout.write('\x1b[2K')
            sys.stdout.flush()


def print_choice(message: str):
    positive_answers = ['y', 'yes', 'Y']
    answer = input(f'{message} (y/N): ')
    return True if answer in positive_answers else False


def print_choices(choices: list, multiple_choice: bool = False, all_btn: bool = False, previous_btn: bool = False, next_btn: bool = False, back_btn: bool = False, exit_btn: bool = False):
    btn_index = len(choices) + 1
    output = ''
    for i, category in enumerate(choices, start=1):
        output += f'{i}. {category}\n'

    if all_btn:
        output += lang.get(key='all', btn_index = btn_index)
        btn_index += 1
        choices.append('all')

    if previous_btn:
        output += lang.get(key='previous', btn_index = btn_index)
        btn_index += 1

    if next_btn:
        output += lang.get(key='next', btn_index = btn_index)
        btn_index += 1

    if back_btn:
        output += lang.get(key='back', btn_index = btn_index)
        btn_index += 1

    if exit_btn:
        output += lang.get(key='exit', btn_index = btn_index)
        btn_index += 1

    print(output)
    try:
        user_choice = input(f'{INPUT_STYLE} ')
        if multiple_choice:
            selected_indexes = [int(choice.strip()) - 1 for choice in user_choice.split(',')]
        else:
            selected_index = int(user_choice.strip()) - 1
    except KeyboardInterrupt:
        exit(0)
    except ValueError:
        return None

    try:
        if multiple_choice:
            return [choices[i] for i in selected_indexes]
        else:
            return choices[selected_index]
    except IndexError:
        return None
