import yaml
from pathlib import Path
from utils import get_caller_module_name


class lang:
    def __init__(self, lang_code: str, debug: bool = False, colored_output: bool = False):
        self.lang = lang_code
        self.debug = debug
        self.colored_output = colored_output
        if self.debug:
            import inspect
            from datetime import datetime
            from colorama import Fore
            timestamp = datetime.now()
            if self.colored_output:
                BLUE = Fore.BLUE
                RESET = Fore.RESET
            else:
                BLUE = Fore.RESET
                RESET = Fore.RESET
            formatted_message = f"{BLUE}[{timestamp}] [{Path(__file__).relative_to(Path(__file__).parent).as_posix()}] [{inspect.currentframe().f_code.co_name}] [INFO] - Localization lib initialized in debug mode.{RESET}"
            print(formatted_message)
            timestamp = datetime.now()
            formatted_message = f"{BLUE}[{timestamp}] [{Path(__file__).relative_to(Path(__file__).parent).as_posix()}] [{inspect.currentframe().f_code.co_name}] [INFO] - Current language is: {self.lang}.{RESET}"
            print(formatted_message)

    def get(self, caller: str = None, function: str = None, key: str = None, return_description: bool = False, return_metadata: bool = False, **kwargs):
        caller_info = get_caller_module_name()
        if caller is None:
            caller = caller or caller_info[0]
        
        if function is None:
            function = function or caller_info[1]

        if function == "<module>":
            function = "__main__"
        self.caller = Path(caller).relative_to(Path(__file__).parent)
        self.function = function
        self.lang_path = self._find_language_file()
        self.lang_data = self._load_language_data()
        self.metadata = self.lang_data.get('metadata', {})
        if return_metadata:
            return self.metadata
        function_data = (self.lang_data.get(str(self.caller), {}).get(function, {}))

        if not isinstance(function_data, dict):
            return function_data

        if "items" not in function_data and "description" not in function_data:
            return function_data

        description = function_data.get("description")

        if return_description and isinstance(description, str):
            return description

        items = function_data.get("items")

        if key is None:
            value = items
        elif isinstance(items, dict):
            value = items.get(key)
        else:
            value = None

        if isinstance(value, str):
            value = value.format(**kwargs).strip()
        return value


    def _find_language_file(self):
        language_directory = self.caller.parent / "lang"
        language_path = language_directory / f"{self.lang}.lng"
        language_file = None

        if language_path.exists():
            language_file = language_path.absolute()

        fallback_files = sorted(language_directory.glob("*.lng"))
        language_file = fallback_files[0].absolute() if fallback_files and not language_file else language_file

        if not language_file:
            return None
        if self.debug:
            import inspect
            from datetime import datetime
            from colorama import Fore
            timestamp = datetime.now()
            if self.colored_output:
                BLUE = Fore.BLUE
                RESET = Fore.RESET
            else:
                BLUE = Fore.RESET
                RESET = Fore.RESET
            formatted_message = f"{BLUE}[{timestamp}] [{Path(__file__).relative_to(Path(__file__).parent).as_posix()}] [{inspect.currentframe().f_code.co_name}] [INFO] - Found language file '{language_file}' for caller: '{self.caller.as_posix()}' and function: '{self.function}'.{RESET}"
            print(formatted_message)
        return language_file.absolute()


    def _load_language_data(self):
        if not self.lang_path:
            return {}
        if not self.lang_path.exists():
            return {}

        with self.lang_path.open(encoding="utf-8") as lang_file:
            if self.debug:
                import inspect
                from datetime import datetime
                from colorama import Fore
                timestamp = datetime.now()
                if self.colored_output:
                    BLUE = Fore.BLUE
                    RESET = Fore.RESET
                else:
                    BLUE = Fore.RESET
                    RESET = Fore.RESET
                formatted_message = f"""{BLUE}[{timestamp}] [{Path(__file__).relative_to(Path(__file__).parent).as_posix()}] [{inspect.currentframe().f_code.co_name}] [INFO] - Loading data of language file '{self.lang_path}' for caller: '{self.caller.as_posix()}' and function: '{self.function}'.{RESET}"""
                print(formatted_message)
            return yaml.safe_load(lang_file) or {}
