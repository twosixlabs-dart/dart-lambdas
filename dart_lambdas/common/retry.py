import collections
import time


def execute_with_arguments(fn_to_execute, args):
    if isinstance(args, collections.abc.Mapping):
        return fn_to_execute(**args)
    if isinstance(args, collections.abc.Iterable):
        return fn_to_execute(*args)
    else:
        raise Exception( "must provide arguments as a dictionary (**kwargs) or list (*args)" )


def retry(retry_fn, args, num_times, fail_check_fn = None, pause = 0):
    if num_times < 1:
        raise Exception( "num_times must be greater than 0" )

    try:
        res = execute_with_arguments(retry_fn, args)
        if fail_check_fn is not None:
            if fail_check_fn( res ):
                if num_times == 1:
                    return res

                time.sleep(pause / 1000)
                return retry(retry_fn, args, num_times - 1, fail_check_fn, pause)

        return res
    except Exception:
        if num_times == 1:
            raise

        time.sleep(pause / 1000)
        return retry(retry_fn, args, num_times - 1, fail_check_fn, pause)

