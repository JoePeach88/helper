import sys


class HelperCLI:
    def __init__(self, arguments: list):
        """Function initiates CLI."""
        self.method = None
        self.args = None
        self.kwargs = None
        METHOD = None
        ARGUMENTS = None
        if len(arguments) >= 1:
            METHOD = arguments[0]
            ARGUMENTS = arguments[1:]
            self.method = METHOD.lower()
            self.args, self.kwargs = self.prepare_arguments(ARGUMENTS)
        try:
            import env
            from env import GC_ENABLED, __product_name__, __required_python__, lang, CACHE_ENABLED, CACHE_LOCATION
            if self.kwargs and 'debug' in self.kwargs:
                env.DEBUG = True
                lang.debug = True
                self.kwargs.pop('debug')
            sys.dont_write_bytecode = CACHE_ENABLED == False
            sys.pycache_prefix = CACHE_LOCATION


            from messages import print_message
            from handler import detect_handler
            from pathlib import Path
            if CACHE_ENABLED and CACHE_LOCATION not in ['./', Path('./').as_posix(), Path(__file__).parent.as_posix()]:
                import shutil
                shutil.rmtree(Path(Path(__file__).parent / '__pycache__'))
            if sys.version_info <= __required_python__:
                required_python = []
                for num in __required_python__:
                    required_python.append(str(num))
                print_message(lang.get(py_version=sys.version, product_name=__product_name__, required_version = '.'.join(required_python)), 'ERROR', True)
            else:
                if ARGUMENTS:
                    print_message(f"Arguments {ARGUMENTS} converted to args and kwargs.")
                print_message(f"Method: '{self.method if self.method else ''}'")
                print_message(f"Arguments: '{self.args if self.args else []}'")
                print_message(f"Key-arguments: '{self.kwargs if self.kwargs else {}}'")
                exit_code = detect_handler(self.method, self.args, self.kwargs)
                if GC_ENABLED:
                    import gc
                    gc.set_debug(0)
                    gc.set_threshold(700, 10, 10)
                    gc.collect(0)
                    gc_stats = gc.get_stats()
                    total_collected = 0
                    for gc_stat in gc_stats:
                        total_collected += gc_stat['collected']
                    print_message(f"Total collected garbage: {total_collected}.")
                self.ret_code = 0 if exit_code is None else exit_code
        except KeyboardInterrupt:
            self.ret_code = 130

    def prepare_arguments(self, args: list):
        positional = []
        keyword = {}
        index = 0

        while index < len(args):
            argument = args[index]

            if not argument.startswith("-"):
                if argument not in positional:
                    positional.append(argument)
                index += 1
                continue

            key = argument.removeprefix("--").removeprefix("-").replace("-", "_")
            value = args[index + 1] if index + 1 < len(args) else None

            if value is not None and (value.startswith("--") or value.startswith("-")):
                value = None
                index += 1
            else:
                index += 2

            if value is not None and value.isdigit():
                value = int(value)

            keyword[key] = True if value is None else value

        return positional, keyword


if __name__ == '__main__':
    cli = HelperCLI(sys.argv[1:])
    SystemExit(cli.ret_code)
