# DART-Lambdas

"Lambda Lambda Lambda"

This repository is the home of DART's AWS Lambda functions

## Development environment

To run tests locally on dart-lambdas without having to reinstall the entire package each time you will 
need to run

```bash
source scripts/set_env.sh
```

This will create a virtual environment with the project root on `PYTHONPATH`, allowing python to resolve 
all the imports in both tests and in the `dart_lambdas` package. It will also install all the required modules

To run tests, use the following:

```bash
pytest
```

## Deploying lambdas to AWS

All lambdas are defined in subpackages within `dart_lambdas`. Currently the only one is `ladleSink`. The actual 
lambda function for all lambdas should be exposed in the lambda package as a function `lambda_handler`. (See how 
this is done in `dart_lambdas/ladleSink/__init__.py`.)

To upload the lambda to AWS, the dart_lamdbas package must be zipped up along with a single script called 
`lambda_function.py` that imports the appropriate lambda handler. For `ladleSink`, `lamdba_function.py` will 
look like this:

```python
from dart_lambdas.ladleSink import lambda_handler
```

Once `lambda_function.py` is zipped up along with the dart_lambdas package, it can be deployed to AWS using the  
`awscli lambda` command.

This can be done automatically by running a script for this purpose:

```bash
./scripts/deploy.sh ladleSink
```

## Testing

This project is configured to use pytest for all testing. Testing with pytest is pretty simple. Each test module
(python file) should be prefixed with `test_`, and each test within that module is a method prefixed with `test_`.
Pytest will discover all relevant files and run all tests within them. Gitlab-ci will not publish any function
without all passing tests, and requires at least one test. Make sure that you include an `__init__.py` file within the
tests directory if you want to be able to import between test modules in that directory. Imports should then have
the form: 
```
from .test_module import some_object
```

### Environment Variables

Since configuration data for your lambda function is best parameterized via environment variables that can be set
through the online dashboard, the `aws lambda` command line tool, or AWS CDK, you will need to set these for your
tests. The best way to do this is to create fixtures in `conftest.py` that use `os.environ` or `monkeypatch.setenv`.
These fixtures can be passed to all your test methods without having to use `import conftest.py`.

### Mocking AWS Services
To test your lambda function's interaction with other AWS services you can use the `moto` library to mock AWS. This
can be done very easily using few simple fixtures which you should define in a `conftest.py` file in your tests
directory. You can then use these as a context for each test by including them as parameters of your test methods.
Basically these fixtures are `boto3` instances (`boto3` is a library to interact with AWS services) in one of the
`moto` mocked AWS service contexts. These instances can then be used to set up AWS services just as they would outside
the mocked context, and they can be used to investigate how those services have been effected by your lambda function.
See the ladleSink tests directory for an example of how this works.

### Mocking other API Calls
To mock API calls, use the `mock` library to mock any function you choose. The best way to do this with pytest is to 
write the content of your relevant test within the context:

```python
with mock.patch('dart_lambdas.lambdaFunction.module.function') as function_mocker:
```

This makes an object `function_mocker` available which can be used to configure how that function will behave whenever
it is called within that context. You can define a function `mock_function()` both to define mocked results and
to include `assert` statements on the parameters passed to it. To configure this function as a mock, you call:

```python
function_mocker.side_effect = mock_function
```

inside of the `mock.patch` context.

NB: the string passed to `mock.patch` should point to the function where it is called, not where it is defined.
For instance, if you are mocking the `post` function in the `requests` library, and if the module that calls it
has `import requests` and calls `post` via `requests.post`, you would use:

```python
with mock.patch('dart_lambdas.lambdaFunction.some_module.requests.post') as post_mocker:
```

For the `requests` library (recommended for any REST service calls), you should use the `requests_mock` library.
This library allows you to easily build responses from either dict, json, or raw data. It is easy to incorporate
into any test: just include `import requests_mock` in the test module and pass `requests_mock` as a fixture to any
test. You can create an "adapter" that matches mocked responses to a request in the following way:

```python
import requests_mock

ANY = requests_mock.ANY

def test_some_method(requests_mock):
    adaptor = requests_mock.get(ANY, json={'data': 'some data'})
    data = method_that_uses_requests_get_method_to_retrieve_data(url='http://test-url.com:8080/some/endpoint')
    assert adaptor.called
    assert adaptor.last_request.hostname == 'test-url.com'
    assert data == 'some data'
```
