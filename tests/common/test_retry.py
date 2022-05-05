import pytest
from dart_lambdas.common.retry import retry

counter = 3

def test_retry_retries_function_using_exception():

    global counter

    def retry_function( arg1, arg2 ):
        global counter

        if counter > 1:
            counter -= 1
            raise Exception( f"failed on time {counter + 1}")

        return arg1 + arg2

    assert retry(retry_function, [7,10], 5) == 17

    assert counter == 1

    counter = 5

    with pytest.raises(Exception) as excinfo:
        retry(retry_function, [2,3], 3)

    assert "failed on time 3" in str(excinfo.value)
    assert counter == 2

def test_retry_retries_function_using_fail_check():
    global counter

    counter = 3

    def retry_function( arg1, arg2, arg3 ):
        global counter

        if counter > 1:
            counter -= 1
            return arg1 + arg2 + arg3

        return arg1 * arg2 * arg3

    def check_retry( res ):
        if res == 9:
            return True
        elif res == 24:
            return False
        else:
            raise Exception( "impossible value" )

    assert retry(retry_function, [2,3,4], 5, check_retry) == 24
    assert counter == 1
    counter = 5
    assert retry(retry_function, [2,3,4], 3, check_retry) == 9
    assert counter == 2

def test_retry_can_accept_args_as_dict_or_list():

    def retry_function( arg_one = 1, arg_two = 2, arg_three = 3 ):
        return arg_one, arg_two, arg_three

    assert retry(retry_function, {'arg_one':10}, 1) == (10, 2, 3)
    assert retry(retry_function, {'arg_three': 6, 'arg_one': 5}, 1) == (5,2,6)
    assert retry(retry_function, [9,8,7], 1) == (9,8,7)

    with pytest.raises(Exception) as excinfo:
        retry(retry_function, 5, 1)

    assert "must provide arguments as a dictionary (**kwargs) or list (*args)" in str(excinfo.value)

def test_retry_pauses_between_tries():
    global counter
    counter = 4

    def retry_function(arg1, arg2):
        global counter

        if counter > 0:
            counter -= 1
            raise Exception(f"failed on time {counter + 1}")

        return arg1 + arg2

    assert retry(retry_function, [0,1], 5, None, 1000) == 1
