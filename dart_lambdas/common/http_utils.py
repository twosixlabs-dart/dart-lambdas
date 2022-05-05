from time import sleep
import requests

from dart_lambdas.common.custom_logging import LOG


# Send a multipart POST request to "url" at "endpoint" on "port" with a file stream "file_data" and
# form data "post_data", trying "num_times" times, and sleeping for "sleep_time" seconds
# between each request.
#
# @returns (success: Boolean, response: Any) where "success" says whether it was successful, and
# "response" is either the content of the response, or the status or exception of failure
def try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, numtimes):
    times_left = numtimes - 1

    LOG(f"Attempt #{numtimes}: {url}:{port}{endpoint}")

    try:
        response = requests.post(f"{url}:{port}{endpoint}", files=post_files, data=post_data, auth=basic_auth)

        if response.status_code == 200:
            return [True, response.text]
        else:
            if times_left == 0:
                return [False, f"FAILED TO POST. Response status-code: {response.status_code}"]
            else:
                sleep(sleep_time)
                return try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, times_left)
    except Exception as e:
        LOG(f"Exception: {e}")
        if times_left == 0:
            return [False, f"FAILED TO POST. Exception: {str(e)}"]
        else:
            sleep(sleep_time)
            return try_post(url, port, endpoint, post_files, post_data, basic_auth, sleep_time, times_left)


# send GET request to "url" at "endpoint" on "port". tries "num_times" times, and sleeps for "sleep_time" seconds
# between each request. Each request will fail after timeout of "time_out" seconds
#
# @returns (success: Boolean, response: Any) where "success" says whether it was successful, and
# "response" is either the content of the response, or the status or exception of failure
def try_get(url, port, endpoint, params, sleep_time, num_times):
    times_left = num_times - 1
    LOG(f"Attempt #{num_times}: {url}:{port}{endpoint}")

    try:
        response = requests.get(f"{url}:{port}{endpoint}", params=params)

        if response.status_code == 200:
            return (True, response.content)
        else:
            LOG(f"Response status-code {response.status_code}")

            if times_left == 0:
                return (False, f"Response status-code: {response.status_code}")
            else:
                sleep(sleep_time)
                return try_get(url, port, endpoint, params, sleep_time, times_left)
    except Exception as e:
        LOG(f"Exception: {e}")

        if times_left == 0:
            return (False, f"Exception: {str(e)}")
        else:
            sleep(sleep_time)
            return try_get(url, port, endpoint, params, sleep_time, times_left)
