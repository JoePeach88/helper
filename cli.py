import sys
import gc
sys.dont_write_bytecode = True
gc.set_debug(0)
gc.set_threshold(700, 10, 10)


from env import GC_ENABLED, __product_name__, __required_python__
from libs.handler import detect_handler, print_message


def __init__():
    """Function initiates CLI."""
    if len(sys.argv) > 1:
        METHOD = sys.argv[1]
        ARGUMENTS = sys.argv[2:]
        method = METHOD.lower()
        arguments = ARGUMENTS
        detect_handler(method, arguments)
    else:
        detect_handler(None, None)
    if GC_ENABLED:
        gc.collect(0)
        gc_stats = gc.get_stats()
        total_collected = 0
        for gc_stat in gc_stats:
            total_collected += gc_stat['collected']
        print_message(f"Total collected garbage: {total_collected}.")

if __name__ == '__main__':
    if sys.version_info < __required_python__:
        print_message(f"Python version ({sys.version}) not compatible with {__product_name__} CLI.", 'ERROR', True)
    else:
        __init__()
